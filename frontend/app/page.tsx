"use client";

import { useEffect, useRef, useState } from "react";
import { db } from "../lib/supabase";
import { clampPdfPage, originalPdfPageUrl } from "../lib/pdf-viewer";
import { ResearchLibrary } from "../components/ResearchLibrary";
import { JuniorPaperGuide } from "../components/JuniorPaperGuide";
import { JuniorWorkplaceGuide } from "../components/JuniorWorkplaceGuide";
import { authCallbackError, cleanAuthErrorUrl } from "../lib/auth-feedback";
import { AnalysisWatchStopped, findActiveAnalysisJob, startAnalysisJob, waitForAnalysisJob } from "../lib/analysis-job";
import type { ActiveAnalysisJob } from "../lib/analysis-job";
import type { User } from "@supabase/supabase-js";

type Evidence = { page: number; quote: string };
type Claim = { text: string; evidence: Evidence[] };
type Finding = {
  claim: string;
  direction: string;
  estimate: string;
  statistical_significance: string;
  table_reference?: string;
  model_or_column?: string;
  significance_legend_evidence?: Evidence[];
  evidence: Evidence[];
  verification?: {
    status: string;
    numeric_supported: boolean;
    unsupported_numeric_tokens: string[];
    direction_consistent: boolean | null;
    significance_supported: boolean | null;
    method: string;
  };
};
type Variable = { name: string; role: string; definition: string; evidence: Evidence[] };
type SampleCountReport = {
  metric: string;
  label: string;
  count: number;
  section: string;
  evidence: Evidence[];
};
type SampleCountConflict = {
  metric: string;
  label: string;
  reported_values: number[];
  sections: string[];
  evidence: Evidence[];
};
type PanelDimensions = {
  study_design_type?: string;
  study_design_evidence?: Evidence[];
  panel_balance?: string;
  panel_balance_evidence?: Evidence[];
  cross_sectional_units_count?: number | null;
  time_periods_count?: number | null;
  reported_total_observations_count?: number | null;
  calculated_total_observations_count?: number | null;
  cross_sectional_units: string;
  time_periods: string;
  reported_total_observations: string;
  calculated_total_observations: string;
  observation_frequency: string;
  observation_unit: string;
  sample_count_reports?: SampleCountReport[];
  source_conflicts?: SampleCountConflict[];
  consistency_status: string;
  consistency_note: string;
  evidence: Evidence[];
};
type Methodology = {
  design: string;
  sample: string;
  period: string;
  data_sources: string[];
  variables: Variable[];
  empirical_strategy: string;
  identification_strategy: string;
  equations: string[];
  evidence: Evidence[];
  panel_dimensions?: PanelDimensions;
};
type Bibliographic = {
  title: string;
  authors: string[];
  year: string;
  venue: string;
  doi: string;
  evidence: Evidence[];
};
type AnalysisResult = {
  mode: string;
  analysis_version?: string;
  methodology_verification?: { repair_attempted: boolean; repair_status: string; repair_model?: string | null };
  findings_deduplication?: { duplicates_removed: number };
  findings_coverage?: {
    status: "supported" | "review_required" | "incomplete" | "not_assessable";
    supported_findings_count: number;
    review_findings_count: number;
    empirical_result_signals_detected: boolean;
    method: string;
  };
  findings_verification?: {
    repair_attempted: boolean;
    repair_status: string;
    repair_model?: string | null;
    rescue_attempted?: boolean;
    rescue_status?: string;
    rescue_model?: string | null;
  };
  summary_verification?: { status: string; unsupported_numeric_tokens?: string[] };
  summary_consistency?: { status: string; summary_mentions_results: boolean; findings_count: number; unmatched_numeric_tokens: string[]; reasons: string[]; method: string };
  summary: string;
  bibliographic?: Bibliographic;
  research_question?: string;
  research_question_evidence?: Evidence[];
  hypotheses?: Claim[];
  contributions?: Claim[];
  methodology?: Methodology;
  findings?: Finding[];
  robustness_checks?: { test: string; result: string; evidence: Evidence[] }[];
  limitations?: { description: string; evidence: Evidence[] }[];
  implications?: Claim[];
  keywords: string[];
  evidence: Evidence[];
  warnings?: string[];
  page_count: number;
  pages_analyzed?: number[];
};
type Paper = {
  id: string;
  title: string;
  status: string;
  storage_path: string;
  created_at: string;
  page_count: number | null;
};
type Analysis = { result: AnalysisResult; model: string; created_at?: string };

function authErrorMessage(error: unknown) {
  const authError = error as { code?: string; message?: string };
  const message = authError.message || "";
  const normalized = message.toLowerCase();
  if (authError.code === "email_address_not_authorized") {
    return "현재 Supabase 기본 이메일 발송은 조직 구성원 주소만 허용합니다. 외부 주소 인증에는 Custom SMTP 설정이 필요합니다.";
  }
  if (authError.code === "over_email_send_rate_limit") {
    return "이메일 발송 한도에 도달했습니다. 잠시 후 다시 시도하거나 Custom SMTP를 설정해 주세요.";
  }
  if (normalized.includes("provider is not enabled") || normalized.includes("unsupported provider")) {
    return "Google 로그인이 아직 Supabase에서 활성화되지 않았습니다. Supabase Auth의 Google 공급자에 OAuth Client ID와 Client Secret을 등록해 주세요.";
  }
  if (normalized.includes("redirect") && normalized.includes("url")) {
    return "로그인 복귀 주소가 Supabase Auth의 Redirect URL 허용 목록에 없습니다. 현재 PaperSignal 주소를 허용 목록에 추가해 주세요.";
  }
  return message || "인증 요청을 처리하지 못했습니다.";
}

function studyDesignLabel(value?: string) {
  const labels: Record<string, string> = {
    balanced_panel: "균형 패널",
    unbalanced_panel: "불균형 패널",
    repeated_cross_section: "반복 횡단면",
    time_series: "시계열",
    cross_sectional: "횡단면",
    portfolio_optimization: "포트폴리오 최적화",
    other: "기타",
    unknown: "확인 불가",
  };
  return value ? labels[value] ?? value : "확인 불가";
}
function panelBalanceLabel(value?: string) {
  const labels: Record<string, string> = {
    balanced: "균형",
    unbalanced: "불균형",
    not_applicable: "해당 없음",
    unknown: "확인 불가",
  };
  return value ? labels[value] ?? value : "확인 불가";
}
function panelStatusLabel(value?: string) {
  const labels: Record<string, string> = {
    consistent: "원문 보고값과 계산값 일치",
    calculated_only: "균형 패널 계산값만 확인",
    mismatch: "균형 패널 관측치 불일치",
    source_conflict: "원문 내 표본 수 보고 불일치",
    design_conflict: "연구 설계 분류 불일치",
    not_applicable_unbalanced: "불균형 패널 — N×T 비교 미적용",
    not_applicable_repeated_cross_section: "반복 횡단면 — N×T 비교 미적용",
    not_applicable_design: "비패널 연구 설계 — N×T 비교 미적용",
    not_assessable: "근거 부족으로 판정 불가",
  };
  return value ? labels[value] ?? value : "확인 불가";
}

function EvidenceList({ items, sourcePdfUrl }: { items?: Evidence[]; sourcePdfUrl?: string }) {
  if (!items?.length) return null;
  return <div className="evidence-list">{items.map((item, index) =>
    <blockquote className="evidence" key={item.page + "-" + index}>
      <b>PAGE {item.page}</b><p>{item.quote}</p>
      {sourcePdfUrl && Number.isInteger(item.page) && item.page > 0 &&
        <a className="evidence-source-link" href={sourcePdfUrl + "#page=" + item.page} target="_blank" rel="noreferrer">
          원문 p.{item.page} 확인 ↗
        </a>}
    </blockquote>
  )}</div>;
}

function ClaimList({ items, sourcePdfUrl }: { items?: Claim[]; sourcePdfUrl?: string }) {
  if (!items?.length) return <p className="muted">원문 근거가 확인된 항목이 없습니다.</p>;
  return <div className="analysis-cards">{items.map((item, index) =>
    <article className="analysis-card" key={index}>
      <p>{item.text}</p><EvidenceList sourcePdfUrl={sourcePdfUrl} items={item.evidence}/>
    </article>
  )}</div>;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [boot, setBoot] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signup, setSignup] = useState(false);
  const [confirmationPending, setConfirmationPending] = useState(false);
  const [resendingConfirmation, setResendingConfirmation] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selected, setSelected] = useState<Paper | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [activeJob, setActiveJob] = useState<ActiveAnalysisJob | null>(null);
  const [jobLookupError, setJobLookupError] = useState("");
  const [sourcePdf, setSourcePdf] = useState<{ paperId: string; url: string } | null>(null);
  const [sourcePdfError, setSourcePdfError] = useState("");
  const [sourceViewerOpen, setSourceViewerOpen] = useState(false);
  const [sourcePage, setSourcePage] = useState(1);
  const sourceViewerRef = useRef<HTMLDivElement | null>(null);
  const openRequestId = useRef(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [engineMode, setEngineMode] = useState<"gemini" | "openai" | "extractive" | "unknown">("unknown");

  useEffect(() => {
    // Failed social OAuth callbacks can carry duplicate, URL-encoded errors.
    // Explain the failure and remove stale error parameters from the address bar.
    const error = authCallbackError(window.location.search, window.location.hash);
    if (error) {
      setMessage(error);
      const clean = cleanAuthErrorUrl(window.location.href);
      if (clean) window.history.replaceState(window.history.state, "", clean);
    }
    const supabase = db();
    void supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setBoot(false);
    }).catch(error => {
      setMessage(String(error));
      setBoot(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setUser(session?.user ?? null));
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    const api = process.env.NEXT_PUBLIC_API_URL;
    if (!api) return;
    void fetch(api.replace(/\/$/, "") + "/health")
      .then(response => response.ok ? response.json() : Promise.reject(new Error("API unavailable")))
      .then(payload => setEngineMode(payload.analysis_mode === "ai" ? (payload.ai_provider === "gemini" ? "gemini" : "openai") : "extractive"))
      .catch(() => setEngineMode("unknown"));
  }, []);

  useEffect(() => {
    if (user) void refresh();
    else {
      openRequestId.current += 1;
      setPapers([]);
      setSelected(null);
      setAnalysis(null);
      setActiveJob(null);
      setJobLookupError("");
      setSourcePdf(null);
      setSourcePdfError("");
    }
  }, [user]);

  async function refresh() {
    const { data, error } = await db().from("papers")
      .select("id,title,status,storage_path,created_at,page_count")
      .order("created_at", { ascending: false });
    if (error) setMessage(error.message);
    else setPapers((data ?? []) as Paper[]);
  }

  async function auth(event: React.FormEvent) {
    event.preventDefault();
    setAuthLoading(true);
    setMessage("");
    try {
      if (signup) {
        const { data, error } = await db().auth.signUp({
          email: email.trim(),
          password,
        });
        if (error) throw error;
        if (data.session) {
          setConfirmationPending(false);
          setMessage("회원가입과 이메일 인증이 완료됐습니다.");
        } else {
          setConfirmationPending(true);
          setMessage("가입 요청을 받았습니다. 받은 편지함에서 인증 메일을 열어 이메일 인증을 완료해 주세요.");
        }
        return;
      }

      const { error } = await db().auth.signInWithPassword({
        email: email.trim(),
        password,
      });
      if (error) {
        if ((error as { code?: string }).code === "email_not_confirmed") {
          setConfirmationPending(true);
          setMessage("이메일 인증이 아직 완료되지 않았습니다. 인증 메일을 다시 보내 주세요.");
          return;
        }
        throw error;
      }
      setConfirmationPending(false);
      setMessage("");
    } catch (error) {
      setMessage(authErrorMessage(error));
    } finally {
      setAuthLoading(false);
    }
  }

  async function googleAuth() {
    setAuthLoading(true);
    setMessage("");
    try {
      const { error } = await db().auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: window.location.origin + "/",
          queryParams: { prompt: "select_account" },
        },
      });
      if (error) throw error;
    } catch (error) {
      setMessage(authErrorMessage(error));
      setAuthLoading(false);
    }
  }

  async function resendConfirmation() {
    if (!email.trim()) {
      setMessage("인증 메일을 받을 이메일 주소를 먼저 입력해 주세요.");
      return;
    }
    setResendingConfirmation(true);
    setMessage("");
    try {
      const { error } = await db().auth.resend({
        type: "signup",
        email: email.trim(),
      });
      if (error) throw error;
      setConfirmationPending(true);
      setMessage("인증 메일 재전송을 요청했습니다. 받은 편지함과 스팸함을 확인해 주세요.");
    } catch (error) {
      setMessage(authErrorMessage(error));
    } finally {
      setResendingConfirmation(false);
    }
  }

  async function upload(file?: File) {
    if (!file || !user) return;
    if (
      file.size > 31457280 || file.size < 1 ||
      !file.name.toLowerCase().endsWith(".pdf") ||
      new TextDecoder().decode(await file.slice(0, 5).arrayBuffer()) !== "%PDF-"
    ) {
      setMessage("30MB 이하의 유효한 PDF만 올려 주세요.");
      return;
    }
    setBusy(true);
    setMessage("");
    const path = user.id + "/" + crypto.randomUUID() + ".pdf";
    try {
      const storage = await db().storage.from("papers").upload(path, file, {
        contentType: "application/pdf", upsert: false,
      });
      if (storage.error) throw storage.error;
      const inserted = await db().from("papers").insert({
        user_id: user.id,
        title: file.name.replace(/\.pdf$/i, "").slice(0, 500),
        original_filename: file.name,
        storage_path: path,
        size_bytes: file.size,
      }).select("id,title,status,storage_path,created_at,page_count").single();
      if (inserted.error) {
        await db().storage.from("papers").remove([path]);
        throw inserted.error;
      }
      await refresh();
      await open(inserted.data as Paper);
      setMessage("논문 업로드 완료. 분석을 시작할 수 있습니다.");
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function getActiveJob(paperId: string): Promise<ActiveAnalysisJob | null> {
    // The authenticated server database is authoritative; browser storage isn't.
    const { data, error } = await db().from("analysis_jobs")
      .select("id,paper_id,status,stage,created_at")
      .eq("paper_id", paperId)
      .in("status", ["queued", "processing"])
      .order("created_at", { ascending: false })
      .limit(1);
    if (error) throw new Error("진행 중인 분석 작업을 확인하지 못했습니다: " + error.message);
    return findActiveAnalysisJob(data);
  }

  async function open(paper: Paper) {
    const requestId = ++openRequestId.current;
    setSelected(paper);
    setAnalysis(null);
    setActiveJob(null);
    setJobLookupError("");
    setSourcePdf(null);
    setSourcePdfError("");
    setSourceViewerOpen(false);
    setSourcePage(1);
    const [result, signedPdf, jobs] = await Promise.all([
      db().from("analyses").select("result,model,created_at")
        .eq("paper_id", paper.id).order("created_at", { ascending: false }).limit(1),
      db().storage.from("papers").createSignedUrl(paper.storage_path, 3600),
      db().from("analysis_jobs").select("id,paper_id,status,stage,created_at")
        .eq("paper_id", paper.id)
        .in("status", ["queued", "processing"])
        .order("created_at", { ascending: false })
        .limit(1),
    ]);
    if (openRequestId.current !== requestId) return;
    if (result.error) setMessage(result.error.message);
    else if (result.data?.[0]) setAnalysis(result.data[0] as Analysis);
    if (jobs.error) {
      setJobLookupError("진행 중인 작업 확인에 실패했습니다. 새 분석을 시작하지 말고 다시 열어 확인해 주세요.");
    } else {
      setActiveJob(findActiveAnalysisJob(jobs.data));
    }
    if (signedPdf.error) setSourcePdfError("원문 PDF 링크를 만들지 못했습니다: " + signedPdf.error.message);
    else if (signedPdf.data?.signedUrl) setSourcePdf({ paperId: paper.id, url: signedPdf.data.signedUrl });
  }

  function showOriginalPdfPage(page: number) {
    if (!selected) return;
    setSourcePage(clampPdfPage(page, selected.page_count));
    setSourceViewerOpen(true);
    window.setTimeout(() => {
      sourceViewerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 0);
  }

  async function monitorJob(paper: Paper, jobId: string, token: string, openedRequestId: number) {
    const api = process.env.NEXT_PUBLIC_API_URL;
    if (!api) throw new Error("분석 API가 아직 연결되지 않았습니다.");
    const base = api.replace(/\/$/, "");
    await waitForAnalysisJob({
      url: base + "/api/analyze/" + paper.id + "/status?job_id=" + encodeURIComponent(jobId),
      token,
      shouldContinue: () => openRequestId.current === openedRequestId,
      onProgress: (progress) => {
        if (openRequestId.current === openedRequestId) setMessage(progress);
      },
    });
    await refresh();
    if (openRequestId.current === openedRequestId) {
      await open({ ...paper, status: "completed" });
      setMessage("Gemini AI 구조화 분석이 완료됐습니다. 원문 페이지 근거를 확인해 주세요.");
    }
  }

  async function resumeAnalysis(paper: Paper, jobId: string) {
    if (busy) return;
    setBusy(true);
    try {
      if (selected?.id !== paper.id) {
        const previousId = openRequestId.current;
        await open(paper);
        if (openRequestId.current !== previousId + 1) return;
      }
      const openedRequestId = openRequestId.current;
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("로그인이 필요합니다.");
      setMessage("기존 분석 작업을 다시 확인하고 있습니다. 새 작업을 등록하지 않습니다...");
      await monitorJob(paper, jobId, data.session.access_token, openedRequestId);
    } catch (error) {
      if (!(error instanceof AnalysisWatchStopped)) setMessage((error as Error).message);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function analyze() {
    if (!selected || busy) return;
    const paper = selected;
    const openedRequestId = openRequestId.current;
    setBusy(true);
    setMessage("이미 진행 중인 분석이 있는지 확인하고 있습니다...");
    try {
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("로그인이 필요합니다.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("분석 API가 아직 연결되지 않았습니다.");
      const base = api.replace(/\/$/, "");
      const token = data.session.access_token;
      // If this lookup fails, do not risk registering a duplicate job.
      const existing = await getActiveJob(paper.id);
      if (openRequestId.current !== openedRequestId) return;
      setJobLookupError("");
      if (existing) setActiveJob(existing);
      const jobId = existing?.id ?? await startAnalysisJob({
        url: base + "/api/analyze/" + paper.id,
        token,
      });
      await monitorJob(paper, jobId, token, openedRequestId);
    } catch (error) {
      if (!(error instanceof AnalysisWatchStopped) && openRequestId.current === openedRequestId) {
        setMessage((error as Error).message);
      }
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  if (boot) return <main className="shell"><p>연구 공간을 불러오는 중...</p></main>;

  if (!user) return <main className="auth">
    <div className="pitch">
      <div className="brand">◈ Paper<span>Signal</span></div>
      <div className="eyebrow">EVIDENCE-FIRST RESEARCH</div>
      <h1>논문을 읽는 시간을<br/><em>인사이트에 집중하는 시간으로.</em></h1>
      <p>금융 연구 논문의 핵심을 구조화하고 모든 해석의 근거를 페이지 단위로 확인하세요.</p>
      <div className="pill">금융 연구 · 비공개 라이브러리 · 출처 기반 분석</div>
    </div>
    <section className="login"><div className="form">
      <p className="eyebrow">YOUR RESEARCH WORKSPACE</p>
      <h2>{signup ? "연구 공간 만들기" : "다시 만나서 반갑습니다."}</h2>
      <p>분석 결과와 논문을 안전하게 보관하세요.</p>
      <form onSubmit={auth}>
        <label>이메일<input type="email" required value={email} onChange={event => { setEmail(event.target.value); setConfirmationPending(false); }} placeholder="name@example.com"/></label>
        <label>비밀번호<input type="password" required minLength={signup ? 8 : 1} value={password} onChange={event => setPassword(event.target.value)} placeholder="8자 이상 입력"/></label>
        <button className="primary" disabled={authLoading}>{authLoading ? "인증 처리 중..." : signup ? "회원가입" : "로그인"} →</button>
      </form>
      <div className="auth-divider"><span>또는</span></div>
      <button type="button" className="google-button" disabled={authLoading} onClick={() => void googleAuth()}>
        <span className="google-mark" aria-hidden="true">G</span>
        {authLoading ? "Google 계정 연결 중..." : "Google로 계속하기"}
      </button>
      <p className="note">{message}</p>
      <p className="toggle"><button type="button" onClick={() => { setSignup(!signup); setConfirmationPending(false); setMessage(""); }}>{signup ? "로그인으로 돌아가기" : "계정이 없나요? 회원가입"}</button></p>
      {confirmationPending && <div className="auth-confirmation" role="status">
        <p>인증 메일 링크를 열면 이메일 확인 후 PaperSignal 연구 공간으로 돌아옵니다.</p>
        <button type="button" className="resend" disabled={resendingConfirmation} onClick={() => void resendConfirmation()}>
          {resendingConfirmation ? "재전송 요청 중..." : "인증 메일 다시 보내기"}
        </button>
      </div>}
    </div></section>
  </main>;

  return <main className="workspace">
    <aside>
      <div className="brand">◈ Paper<span>Signal</span></div>
      <p className="eyebrow">WORKSPACE</p>
      <div className="nav">▤　논문 라이브러리</div>
      <footer><p>{user.email}</p><button onClick={() => void db().auth.signOut()}>로그아웃</button></footer>
    </aside>
    <div className="content">
      <header>Workspace / <b>논문 라이브러리</b>
        <span className={engineMode === "gemini" || engineMode === "openai" ? "engine-ready" : "engine-pending"}>
          ● {engineMode === "gemini" ? "Gemini AI 분석 활성화" : engineMode === "openai" ? "OpenAI 분석 활성화" : engineMode === "extractive" ? "텍스트 추출 모드" : "API 상태 확인 중"}
        </span>
      </header>
      <div className="body">
        {engineMode === "gemini" && <div className="provider-notice"><b>Gemini 무료 티어 데이터 안내</b><p>현재 설정에서는 업로드한 논문에서 추출한 텍스트와 AI 응답이 Google 제품 개선에 사용되거나 사람 검토자가 처리할 수 있습니다. 공개·비기밀 논문만 업로드하고, 사내 미공개 자료나 개인정보가 포함된 문서는 올리지 마세요.</p></div>}
        <div className="heading">
          <div><p className="eyebrow">RESEARCH LIBRARY</p><h1>나의 연구 라이브러리</h1><p>금융 논문을 수집하고 근거 기반 인사이트를 축적하세요.</p></div>
          <label className="upload-button">＋ 논문 추가
            <input type="file" accept=".pdf,application/pdf" hidden disabled={busy} onChange={event => void upload(event.target.files?.[0])}/>
          </label>
        </div>
        <div className="stats">
          <div><p>전체 논문</p><strong>{papers.length.toString().padStart(2, "0")}</strong><small>보관 중인 논문</small></div>
          <div><p>완료된 분석</p><strong>{papers.filter(paper => paper.status === "completed").length.toString().padStart(2, "0")}</strong><small>근거 기반 결과</small></div>
          <div className="highlight"><p>RESEARCH INTELLIGENCE</p><h2>From papers<br/>to perspectives.</h2></div>
        </div>
        <ResearchLibrary papers={papers} busy={busy} onOpen={open} onResume={resumeAnalysis} />
        {message && <div className="message" role="status">{message}</div>}
      </div>
    </div>

    {selected && <div className="overlay" onClick={() => { openRequestId.current += 1; setSelected(null); setSourcePdf(null); setSourcePdfError(""); setSourceViewerOpen(false); }}>
      <section className="details" onClick={event => event.stopPropagation()}>
        <div className="detail-toolbar no-print">
          {sourcePdf?.paperId === selected.id
            ? <div className="source-pdf-actions">
                <button type="button" className="source-pdf-button" aria-expanded={sourceViewerOpen}
                  onClick={() => setSourceViewerOpen((value) => !value)}>
                  {sourceViewerOpen ? "원문 PDF 접기" : "원문 PDF 함께 보기"}
                </button>
                <a className="source-pdf-button source-pdf-external" href={sourcePdf.url} target="_blank" rel="noreferrer">새 탭 ↗</a>
              </div>
            : <span className="source-pdf-status">{sourcePdfError || "원문 PDF 연결 준비 중..."}</span>}
          <button className="close" onClick={() => { openRequestId.current += 1; setSelected(null); setSourcePdf(null); setSourcePdfError(""); setSourceViewerOpen(false); }}>×</button>
        </div>
        <p className="eyebrow">PAPER INTELLIGENCE</p>
        <h2>{selected.title}</h2>
        <p>연구 설계부터 실증 결과까지 원문 페이지 근거와 함께 검토하세요.</p>
        {activeJob && <div className="active-job-banner no-print" role="status">
          <strong>이미 진행 중인 분석이 있습니다.</strong>
          <p>상태: {activeJob.status === "queued" ? "대기 중" : activeJob.stage === "gemini_analysis" ? "Gemini AI 분석 중" : "처리 중"} · 브라우저를 닫아도 서버 작업은 계속됩니다.</p>
          <button type="button" className="primary" disabled={busy} onClick={() => void resumeAnalysis(selected, activeJob.id)}>
            {busy ? "작업 상태 확인 중..." : "진행 중인 분석 이어 확인 →"}
          </button>
        </div>}
        {sourceViewerOpen && sourcePdf?.paperId === selected.id && <section className="inline-pdf-viewer no-print" ref={sourceViewerRef} aria-label="업로드한 원본 PDF">
          <div className="inline-pdf-heading">
            <div><b>원본 PDF</b><span>업로드한 PDF 페이지를 그대로 표시합니다. 요약이나 HTML로 재구성한 화면이 아닙니다.</span></div>
            <div className="inline-pdf-controls">
              <button type="button" disabled={sourcePage <= 1} onClick={() => setSourcePage((value) => clampPdfPage(value - 1, selected.page_count))}>이전</button>
              <label>페이지
                <input type="number" inputMode="numeric" min={1} max={selected.page_count ?? undefined}
                  value={sourcePage}
                  onChange={(event) => {
                    if (event.target.value === "") return;
                    const value = Number(event.target.value);
                    if (Number.isFinite(value)) setSourcePage(clampPdfPage(value, selected.page_count));
                  }}
                  onBlur={() => setSourcePage((value) => clampPdfPage(value, selected.page_count))}
                  aria-label="원문 PDF 페이지 번호"/>
                <span>/ {selected.page_count ?? "?"}</span>
              </label>
              <button type="button" disabled={Boolean(selected.page_count && sourcePage >= selected.page_count)}
                onClick={() => setSourcePage((value) => clampPdfPage(value + 1, selected.page_count))}>다음</button>
            </div>
          </div>
          <iframe
            key={selected.id + "-" + sourcePage}
            className="inline-pdf-frame"
            title={selected.title + " 원본 PDF " + sourcePage + "페이지"}
            src={originalPdfPageUrl(sourcePdf.url, sourcePage, selected.page_count)}
            loading="lazy"
            referrerPolicy="no-referrer"
          />
          <p className="inline-pdf-fallback">PDF가 표시되지 않으면 <a href={originalPdfPageUrl(sourcePdf.url, sourcePage, selected.page_count)} target="_blank" rel="noreferrer">원문 PDF를 새 탭에서 여세요.</a></p>
        </section>}
        {jobLookupError && <p className="warning" role="alert">{jobLookupError}</p>}
        {!analysis
          ? <div className="prompt">
              <div>✧</div><h3>논문 분석 준비 완료</h3>
              <p>{engineMode === "gemini" || engineMode === "openai"
                ? "AI가 연구 질문, 계량 방법론, 실증 결과, 강건성 검증을 구조화하고 페이지별 인용을 확인합니다."
                : "현재는 텍스트 추출 모드입니다. Railway에 선택한 AI 제공자의 API 키를 설정하면 구조화된 금융 연구 분석이 활성화됩니다."}</p>
              {busy && <p className="analysis-progress" aria-live="polite">{message}</p>}
              <button disabled={busy || Boolean(activeJob) || Boolean(jobLookupError)} className="primary" onClick={() => void analyze()}>{busy ? "작업 상태 확인 중..." : activeJob ? "기존 분석 진행 중" : jobLookupError ? "작업 확인 필요" : "분석 시작 →"}</button>
            </div>
          : <div className="result">
              <p className="mode">{analysis.result.mode === "llm"
                ? "AI 구조화 분석 · 인용 근거 검증"
                : "텍스트 추출 분석 · AI 생성 아님"}</p>
              <JuniorPaperGuide
                result={analysis.result}
                sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined}
                onOpenSourcePage={showOriginalPdfPage}
              />
              <JuniorWorkplaceGuide result={analysis.result} paperTitle={selected.title} />
              <div className="report-toolbar no-print">
                <div>
                  <b>연구 분석 보고서</b>
                  <span>인쇄 창에서 PDF로 저장을 선택하면 A4 보고서가 생성됩니다.</span>
                </div>
                <button type="button" className="report-button" onClick={() => window.print()}>
                  PDF 보고서 저장 ↓
                </button>
              </div>
              {analysis.result.bibliographic && (
                <section className="analysis-section">
                  <h3>논문 서지정보</h3>
                  <p><b>{analysis.result.bibliographic.title}</b></p>
                  <p>{analysis.result.bibliographic.authors?.join(", ") || "저자 확인 불가"} · {analysis.result.bibliographic.year} · {analysis.result.bibliographic.venue}</p>
                  <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.bibliographic.evidence}/>
                </section>
              )}
              <section className="analysis-section">
                <h3>핵심 요약</h3><p>{analysis.result.summary}</p>
                {analysis.result.summary_verification && <p className={analysis.result.summary_verification.status === "model_summary" ? "muted" : "verification-note"}>
                  요약 검증: {analysis.result.summary_verification.status === "model_summary" ? "원문 수치 1차 대조 통과" : analysis.result.summary_verification.status.startsWith("reconstructed") ? "검증된 방법론·실증 결과로 재구성" : "원문 근거 확인 필요"}
                </p>}
                {!!analysis.result.summary_verification?.unsupported_numeric_tokens?.length && <p className="warning">요약에서 인용 페이지로 확인되지 않은 숫자: {analysis.result.summary_verification.unsupported_numeric_tokens.join(", ")}</p>}
                {analysis.result.summary_consistency && <p className={analysis.result.summary_consistency.status === "review" ? "warning" : "verification-note"}>
                  요약·실증 결과 일관성: {analysis.result.summary_consistency.status === "review" ? "구조화 결과와 추가 대조 필요" : "1차 일관성 검사 통과"}
                  {!!analysis.result.summary_consistency.unmatched_numeric_tokens.length && <span>{" · 구조화 항목에서 찾지 못한 숫자: " + analysis.result.summary_consistency.unmatched_numeric_tokens.join(", ")}</span>}
                </p>}
              </section>
              <section className="analysis-section">
                <h3>연구 질문</h3><p>{analysis.result.research_question || "확인 불가"}</p>
                <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.research_question_evidence}/>
              </section>
              <section className="analysis-section"><h3>연구 가설</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.hypotheses}/></section>
              <section className="analysis-section"><h3>학술적 기여</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.contributions}/></section>
              {analysis.result.methodology && (
                <section className="analysis-section">
                  <h3>연구 방법론 및 데이터</h3>
                  {analysis.result.methodology_verification?.repair_attempted && <p className="muted">2차 방법론 검증: {analysis.result.methodology_verification.repair_status === "recovered" ? "누락 방법론 복구 완료" : analysis.result.methodology_verification.repair_status === "reviewed" ? "기존 방법론 재검토 완료" : analysis.result.methodology_verification.repair_status === "partial" ? "일부 항목만 복구" : analysis.result.methodology_verification.repair_status === "no_supported_methodology" ? "추가 근거 확인 불가" : "검증 미완료"}</p>}
                  <div className="method-grid">
                    <div><b>연구 설계</b><p>{analysis.result.methodology.design}</p></div>
                    <div><b>표본</b><p>{analysis.result.methodology.sample}</p></div>
                    <div><b>분석 기간</b><p>{analysis.result.methodology.period}</p></div>
                    <div><b>추정 전략</b><p>{analysis.result.methodology.empirical_strategy}</p></div>
                    <div><b>식별 전략</b><p>{analysis.result.methodology.identification_strategy}</p></div>
                  </div>
                  {!!analysis.result.methodology.data_sources?.length && <p><b>데이터 출처:</b> {analysis.result.methodology.data_sources.join(" · ")}</p>}
                  {analysis.result.methodology.panel_dimensions && analysis.result.methodology.panel_dimensions.evidence?.length > 0 && <>
                    <h4>연구 설계 및 표본 구조 검증</h4>
                    <div className="method-grid">
                      <div><b>연구 설계 유형</b><p>{studyDesignLabel(analysis.result.methodology.panel_dimensions.study_design_type)}</p></div>
                      <div><b>패널 균형 여부</b><p>{panelBalanceLabel(analysis.result.methodology.panel_dimensions.panel_balance)}</p></div>
                      <div><b>횡단면 단위 수</b><p>{analysis.result.methodology.panel_dimensions.cross_sectional_units_count || analysis.result.methodology.panel_dimensions.cross_sectional_units}</p></div>
                      <div><b>관측 기간 수</b><p>{analysis.result.methodology.panel_dimensions.time_periods_count || analysis.result.methodology.panel_dimensions.time_periods}</p></div>
                      <div><b>원문 보고 총관측치</b><p>{analysis.result.methodology.panel_dimensions.reported_total_observations_count || analysis.result.methodology.panel_dimensions.reported_total_observations}</p></div>
                      <div><b>계산 총관측치</b><p>{analysis.result.methodology.panel_dimensions.calculated_total_observations_count || analysis.result.methodology.panel_dimensions.calculated_total_observations}</p></div>
                      <div><b>관측 빈도</b><p>{analysis.result.methodology.panel_dimensions.observation_frequency}</p></div>
                      <div><b>관측 단위</b><p>{analysis.result.methodology.panel_dimensions.observation_unit}</p></div>
                    </div>
                    <p className={["mismatch", "source_conflict", "design_conflict"].includes(analysis.result.methodology.panel_dimensions.consistency_status) ? "warning" : "verification-note"}>
                      표본 구조 검사: {panelStatusLabel(analysis.result.methodology.panel_dimensions.consistency_status)}
                      {" · "}{analysis.result.methodology.panel_dimensions.consistency_note}
                    </p>
                    {!!analysis.result.methodology.panel_dimensions.source_conflicts?.length && <>
                      <h4>원문 내 표본 수 불일치</h4>
                      {analysis.result.methodology.panel_dimensions.source_conflicts.map((conflict, index) =>
                        <article className="analysis-card" key={index}>
                          <b>{conflict.label} · {conflict.metric}</b>
                          <p>원문 보고값: {conflict.reported_values.join(" / ")}</p>
                          <p>출처 위치: {conflict.sections.join(" · ")}</p>
                          <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={conflict.evidence}/>
                        </article>
                      )}
                    </>}
                    {!!analysis.result.methodology.panel_dimensions.sample_count_reports?.length && <>
                      <h4>원문 표본 수 기록</h4>
                      {analysis.result.methodology.panel_dimensions.sample_count_reports.map((report, index) =>
                        <article className="analysis-card" key={index}>
                          <b>{report.label} · {report.metric}</b>
                          <p>{report.count.toLocaleString()} · {report.section}</p>
                          <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={report.evidence}/>
                        </article>
                      )}
                    </>}
                    <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.methodology.panel_dimensions.evidence}/>
                    <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.methodology.panel_dimensions.study_design_evidence}/>
                    <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.methodology.panel_dimensions.panel_balance_evidence}/>
                  </>}
                  {!!analysis.result.methodology.variables?.length && <>
                    <h4>주요 변수</h4>
                    {analysis.result.methodology.variables.map((variable, index) =>
                      <article className="analysis-card" key={index}>
                        <b>{variable.name}</b><span className="tag">{variable.role}</span><p>{variable.definition}</p>
                        <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={variable.evidence}/>
                      </article>
                    )}
                  </>}
                  {!!analysis.result.methodology.equations?.length && <>
                    <h4>모형 및 수식</h4>{analysis.result.methodology.equations.map((equation, index) => <pre className="equation" key={index}>{equation}</pre>)}
                  </>}
                  <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.methodology.evidence}/>
                </section>
              )}
              <section className="analysis-section">
                <h3>주요 실증 결과 <small>{analysis.result.findings?.length ?? 0}</small></h3>
                {!!analysis.result.findings_deduplication?.duplicates_removed && <p className="muted">유사·중복 결과 {analysis.result.findings_deduplication.duplicates_removed}개를 통합했습니다.</p>}
                {analysis.result.findings_verification?.repair_attempted && <p className="muted">2차 실증 결과 검증: {analysis.result.findings_verification.repair_status === "recovered" || analysis.result.findings_verification.repair_status === "recovered_by_rescue" ? "누락 결과 복구 완료" : analysis.result.findings_verification.repair_status === "reviewed" ? "기존 결과 재검토 완료" : analysis.result.findings_verification.repair_status === "no_supported_findings" ? "추가 근거 확인 불가" : "검증 미완료"}</p>}
                {analysis.result.findings_verification?.rescue_attempted && <p className="muted">결과표 중심 3차 검증: {analysis.result.findings_verification.rescue_status === "recovered" ? "복구 완료" : analysis.result.findings_verification.rescue_status === "no_supported_findings" ? "근거 있는 결과 미확보" : "검증 미완료"}</p>}
                {analysis.result.findings_coverage && <p className={analysis.result.findings_coverage.status === "incomplete" ? "warning" : analysis.result.findings_coverage.status === "review_required" ? "verification-note" : "muted"}>
                  실증 결과 추출 품질: {analysis.result.findings_coverage.status === "supported" ? "페이지 근거가 확인된 결과 " + analysis.result.findings_coverage.supported_findings_count + "건" : analysis.result.findings_coverage.status === "review_required" ? "연구자 검토가 필요한 결과 " + analysis.result.findings_coverage.review_findings_count + "건" : analysis.result.findings_coverage.status === "incomplete" ? "실증 결과 신호가 있으나 검증된 결과가 없어 불완전" : "실증 결과 추출 가능 여부 확인 불가"}
                </p>}
                {!analysis.result.findings?.length
                  ? <p className="muted">검증된 실증 결과가 없습니다.</p>
                  : analysis.result.findings.map((finding, index) =>
                    <article className="analysis-card" key={index}>
                      <p>{finding.claim}</p>
                      <div className="finding-meta">
                        <span>방향: {finding.direction}</span><span>추정치: {finding.estimate}</span><span>통계적 유의성: {finding.statistical_significance}</span>
                        {finding.table_reference && <span>표: {finding.table_reference}</span>}
                        {finding.model_or_column && <span>모형·열: {finding.model_or_column}</span>}
                        {finding.verification && <span className={finding.verification.status === "screen_passed" ? "verification-ok" : "verification-review"}>
                          수치·표 맥락: {finding.verification.status === "screen_passed" ? "1차 대조 통과" : "연구자 확인 필요"}
                        </span>}
                      </div>
                      {finding.verification?.unsupported_numeric_tokens?.length ? <p className="warning">인용 페이지에서 확인되지 않은 숫자: {finding.verification.unsupported_numeric_tokens.join(", ")}</p> : null}
                      {finding.verification?.direction_consistent === false && <p className="warning">추정치의 부호와 결과 방향이 일치하지 않습니다.</p>}
                      {finding.verification?.significance_supported === false && <p className="warning">통계적 유의성 표기가 인용 페이지에서 확인되지 않습니다.</p>}
                      <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={finding.evidence}/>
                      {!!finding.significance_legend_evidence?.length && <>
                        <p className="muted">통계적 유의성 표 주석</p>
                        <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={finding.significance_legend_evidence}/>
                      </>}
                    </article>
                  )}
              </section>
              <section className="analysis-section">
                <h3>강건성 검증</h3>
                {!analysis.result.robustness_checks?.length ? <p className="muted">본문에서 검증 가능한 강건성 검증을 찾지 못했습니다.</p>
                  : analysis.result.robustness_checks.map((item, index) =>
                    <article className="analysis-card" key={index}><b>{item.test}</b><p>{item.result}</p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={item.evidence}/></article>
                  )}
              </section>
              <section className="analysis-section">
                <h3>연구 한계</h3>
                {!analysis.result.limitations?.length ? <p className="muted">원문 근거가 확인된 한계가 없습니다.</p>
                  : analysis.result.limitations.map((item, index) =>
                    <article className="analysis-card" key={index}><p>{item.description}</p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={item.evidence}/></article>
                  )}
              </section>
              <section className="analysis-section"><h3>금융·경제적 시사점</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.implications}/></section>
              <section className="analysis-section"><h3>핵심 키워드</h3><div className="tags">{(analysis.result.keywords ?? []).map(keyword => <span key={keyword}>{keyword}</span>)}</div></section>
              <section className="analysis-section"><h3>검증된 원문 근거 <small>{analysis.result.evidence?.length ?? 0}</small></h3><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} items={analysis.result.evidence}/></section>
              {(analysis.result.warnings ?? []).map((warning, index) => <p className="warning" key={index}>{warning}</p>)}
              <p className="muted">분석 모델: {analysis.model} · 버전: {analysis.result.analysis_version ?? "legacy"}</p>
              <button disabled={busy} className="primary" onClick={() => void analyze()}>{busy ? "분석 중..." : "다시 분석하기"}</button>
            </div>}
      </section>
    </div>}
  </main>;
}
