/**
 * Durable analysis-job polling. Polling may lose connectivity while the Worker
 * continues on the server; never resubmit POST /api/analyze in this helper.
 */
export type AnalysisJobState = {
  status?: string;
  stage?: string;
  error?: string | null;
  detail?: string;
};

export type ActiveAnalysisJob = {
  id: string;
  paper_id: string;
  status: "queued" | "processing";
  stage?: string | null;
  created_at: string;
};

export function findActiveAnalysisJob(rows: unknown): ActiveAnalysisJob | null {
  if (!Array.isArray(rows)) return null;
  const jobs = rows.filter((row): row is ActiveAnalysisJob =>
    Boolean(row && typeof row === "object" &&
      typeof row.id === "string" && row.id.trim() &&
      typeof row.paper_id === "string" && row.paper_id.trim() &&
      (row.status === "queued" || row.status === "processing") &&
      typeof row.created_at === "string")
  );
  // Supabase usually sorts rows, but select newest defensively.
  return jobs.sort((a, b) => b.created_at.localeCompare(a.created_at))[0] ?? null;
}

/** Stopping the browser watch never cancels the server-side job. */
export class AnalysisWatchStopped extends Error {
  constructor() {
    super("작업 상태 확인을 중단했습니다. 서버 분석은 계속 진행될 수 있습니다.");
    this.name = "AnalysisWatchStopped";
  }
}

type Fetcher = (url: string, init: RequestInit) => Promise<Response>;
type Sleeper = (milliseconds: number) => Promise<void>;

const TRANSIENT_CODES = new Set([408, 429, 500, 502, 503, 504]);
const DEFAULT_INTERVAL_MS = 3000;
const DEFAULT_MAX_POLLS = 120;
const DEFAULT_MAX_CONSECUTIVE_ERRORS = 8;

export const analysisStageLabels: Record<string, string> = {
  queued: "분석 대기열에 등록했습니다...",
  claimed: "분석 Worker가 작업을 시작했습니다...",
  pdf_download: "PDF 다운로드 및 텍스트 추출 중...",
  pdf_extracted: "PDF 원문 추출 완료. 분석을 준비하고 있습니다...",
  gemini_analysis: "Gemini AI가 금융논문을 분석하고 있습니다...",
  completed: "분석 완료. 결과를 불러오고 있습니다...",
  failed: "분석 실패",
};

export function analysisConnectionError() {
  return "분석 서버에 연결하지 못했습니다. 인터넷 연결과 서버 상태를 확인해 주세요. 이미 등록된 분석 작업은 서버에서 계속 진행될 수 있습니다.";
}

function retryDelay(response: Response, defaultDelay: number) {
  const value = response.headers.get("retry-after");
  if (!value || !/^\d+$/.test(value.trim())) return defaultDelay;
  return Math.min(15000, Math.max(defaultDelay, Number(value) * 1000));
}

function readableDetail(value: unknown, fallback: string) {
  if (!value || typeof value !== "object") return fallback;
  const payload = value as Record<string, unknown>;
  const candidate = typeof payload.detail === "string" ? payload.detail : payload.error;
  return typeof candidate === "string" && candidate.trim()
    ? candidate.trim().slice(0, 400) : fallback;
}

export async function startAnalysisJob({
  url,
  token,
  fetcher = fetch,
}: {
  url: string;
  token: string;
  fetcher?: Fetcher;
}): Promise<string> {
  let response: Response;
  try {
    // Do not retry this POST automatically: the server may have committed a job.
    response = await fetcher(url, { method: "POST", headers: { Authorization: "Bearer " + token } });
  } catch {
    throw new Error(analysisConnectionError());
  }

  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    // The queue RPC returns HTTP 429 with an actionable Korean quota detail.
    // Surface that limit immediately instead of misclassifying it as a
    // transient network failure. Never retry this POST automatically.
    if (response.status === 429) {
      const detail = readableDetail(body, "");
      if (detail) throw new Error(detail);
    }
    if (TRANSIENT_CODES.has(response.status)) {
      throw new Error(
        "분석 작업 등록 응답이 일시적으로 실패했습니다. 기존 작업이 등록됐을 수 있으니 연구 라이브러리의 작업 상태를 먼저 확인해 주세요."
      );
    }
    throw new Error(readableDetail(body, "분석 작업을 등록하지 못했습니다."));
  }
  if (!body || typeof body !== "object" || typeof (body as { job_id?: unknown }).job_id !== "string") {
    throw new Error("서버에서 분석 작업 ID를 받지 못했습니다.");
  }
  const id = (body as { job_id: string }).job_id.trim();
  if (!id) throw new Error("서버에서 분석 작업 ID를 받지 못했습니다.");
  return id;
}

export async function waitForAnalysisJob({
  url,
  token,
  onProgress,
  fetcher = fetch,
  sleep = (ms) => new Promise<void>((resolve) => setTimeout(resolve, ms)),
  intervalMs = DEFAULT_INTERVAL_MS,
  maxPolls = DEFAULT_MAX_POLLS,
  maxConsecutiveErrors = DEFAULT_MAX_CONSECUTIVE_ERRORS,
  shouldContinue = () => true,
}: {
  url: string;
  token: string;
  onProgress: (message: string) => void;
  fetcher?: Fetcher;
  sleep?: Sleeper;
  intervalMs?: number;
  maxPolls?: number;
  maxConsecutiveErrors?: number;
  shouldContinue?: () => boolean;
}): Promise<AnalysisJobState> {
  let consecutiveErrors = 0;

  for (let attempt = 0; attempt < maxPolls; attempt++) {
    if (!shouldContinue()) throw new AnalysisWatchStopped();
    let response: Response;
    try {
      response = await fetcher(url, {
        method: "GET",
        headers: { Authorization: "Bearer " + token },
        cache: "no-store",
      });
    } catch {
      consecutiveErrors += 1;
      if (consecutiveErrors >= maxConsecutiveErrors) throw new Error(analysisConnectionError());
      onProgress("일시적으로 서버 연결이 끊겼습니다. 진행 중인 작업을 다시 확인합니다...");
      await sleep(intervalMs);
      continue;
    }

    if (!shouldContinue()) throw new AnalysisWatchStopped();
    const body: unknown = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (TRANSIENT_CODES.has(response.status)) {
        consecutiveErrors += 1;
        if (consecutiveErrors >= maxConsecutiveErrors) {
          throw new Error("분석 서버가 반복적으로 응답하지 않습니다. 진행 중인 작업은 연구 라이브러리에서 다시 확인해 주세요.");
        }
        onProgress("서버가 일시적으로 혼잡합니다. 이미 등록된 분석 작업의 상태를 다시 확인합니다...");
        await sleep(retryDelay(response, intervalMs));
        continue;
      }
      if (response.status === 401 || response.status === 403) {
        throw new Error("로그인 세션 또는 분석 작업 접근 권한을 확인해 주세요.");
      }
      throw new Error(readableDetail(body, "분석 상태를 조회하지 못했습니다."));
    }

    if (!body || typeof body !== "object") {
      throw new Error("분석 상태 응답 형식이 올바르지 않습니다.");
    }
    const state = body as AnalysisJobState;
    consecutiveErrors = 0;
    onProgress(analysisStageLabels[state.stage || ""] || "분석 작업을 처리하고 있습니다...");
    if (state.status === "completed") return state;
    if (state.status === "failed") {
      throw new Error(state.error || "분석에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    }
    await sleep(intervalMs);
  }

  throw new Error("분석이 계속 진행 중입니다. 잠시 후 논문을 다시 열어 결과를 확인해 주세요.");
}
