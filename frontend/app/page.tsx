"use client";

import { useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { db } from "../lib/supabase";
import { clampPdfPage, commitPdfPageInput, originalPdfPageUrl, pdfLinkNeedsRefresh } from "../lib/pdf-viewer";
import { ResearchLibrary } from "../components/ResearchLibrary";
import { BetaGettingStarted } from "../components/BetaGettingStarted";
import { isAcceptedPdf, sourcePdfFailureMessage, uploadFailureMessage } from "../lib/beta-ux";
import { JuniorPaperGuide } from "../components/JuniorPaperGuide";
import { JuniorVisualReading } from "../components/JuniorVisualReading";
import { JuniorWorkplaceGuide } from "../components/JuniorWorkplaceGuide";
import { EvidencePopover } from "../components/EvidencePopover";
import { authCallbackError, cleanAuthErrorUrl } from "../lib/auth-feedback";
import { AnalysisWatchStopped, findActiveAnalysisJob, startAnalysisJob, waitForAnalysisJob } from "../lib/analysis-job";
import type { ActiveAnalysisJob } from "../lib/analysis-job";
import type { User } from "@supabase/supabase-js";

type Evidence = { page: number; quote: string; contexts?: string[] };
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
type PublicPaperSort = "relevance" | "citations_desc" | "title_asc" | "author_asc" | "year_desc";
type PublicPaper = {
  id: string; title: string; year: number | null; doi: string;
  authors: string[]; cited_by_count: number; category?: string;
  pdf_url: string | null; landing_url: string;
  license: string; is_open_access: boolean;
};
type PublicSearchResult = {
  query: string; page: number; apiPage: number; total: number;
  has_more: boolean; results: PublicPaper[]; sort: PublicPaperSort;
};

function sortPublicPapers(items: PublicPaper[], sort: PublicPaperSort): PublicPaper[] {
  const collator = new Intl.Collator("ko", { sensitivity: "base", numeric: true });
  if (sort === "relevance") return [...items];
  return [...items].sort((a, b) => {
    if (sort === "citations_desc") {
      return b.cited_by_count - a.cited_by_count || collator.compare(a.title, b.title);
    }
    if (sort === "title_asc") return collator.compare(a.title, b.title);
    if (sort === "author_asc") {
      return collator.compare(a.authors[0] ?? "", b.authors[0] ?? "") || collator.compare(a.title, b.title);
    }
    return (b.year ?? 0) - (a.year ?? 0) || collator.compare(a.title, b.title);
  });
}

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

function EvidenceList({
  items, sourcePdfUrl, onOpenSourcePage, children,
}: {
  items?: Evidence[];
  sourcePdfUrl?: string;
  onOpenSourcePage?: (page: number) => void;
  children?: ReactNode;
}) {
  if (!items?.length) return children ?? null;
  return <EvidencePopover items={items} sourcePdfUrl={sourcePdfUrl} onOpenSourcePage={onOpenSourcePage}>{children}</EvidencePopover>;
}

function groupedVariableEvidence(variables: Variable[]): Evidence[] {
  const grouped = new Map<string, Evidence & { contexts: string[] }>();
  for (const variable of variables) {
    for (const item of variable.evidence ?? []) {
      const normalizedQuote = item.quote.trim().replace(/\s+/g, " ").toLocaleLowerCase();
      const key = `${item.page}::${normalizedQuote}`;
      const existing = grouped.get(key);
      if (existing) {
        if (!existing.contexts.includes(variable.name)) existing.contexts.push(variable.name);
      } else {
        grouped.set(key, { page: item.page, quote: item.quote, contexts: [variable.name] });
      }
    }
  }
  return Array.from(grouped.values());
}

function ClaimList({
  items, sourcePdfUrl, onOpenSourcePage,
}: {
  items?: Claim[];
  sourcePdfUrl?: string;
  onOpenSourcePage?: (page: number) => void;
}) {
  if (!items?.length) return <p className="muted">원문 근거가 확인된 항목이 없습니다.</p>;
  return <div className="analysis-cards">{items.map((item, index) =>
    <article className="analysis-card" key={index}>
      <p><EvidenceList sourcePdfUrl={sourcePdfUrl} onOpenSourcePage={onOpenSourcePage} items={item.evidence}>{item.text}</EvidenceList></p>
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
  const [signOutLoading, setSignOutLoading] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [papersOwnerId, setPapersOwnerId] = useState<string | null>(null);
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | null>(null);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState("");
  const [uploadIssue, setUploadIssue] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const libraryRequestId = useRef(0);
  const previousUserIdRef = useRef<string | null>(null);
  const currentUserIdRef = useRef<string | null>(null);
  currentUserIdRef.current = user?.id ?? null;
  const visiblePapers = papersOwnerId === user?.id ? papers : [];
  const [selected, setSelected] = useState<Paper | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [readingScale, setReadingScale] = useState(90);
  const [readingScaleReady, setReadingScaleReady] = useState(false);
  useEffect(() => {
    try {
      const saved = Number(window.localStorage.getItem("papersignal-reading-scale"));
      if ([80, 90, 100, 110, 120, 130, 140].includes(saved)) {
        // The previous release persisted its 100% default on first load; migrate that default to 90%.
        setReadingScale(saved === 100 ? 90 : saved);
      }
    } catch {
      // Reading remains usable if browser storage is unavailable.
    }
    setReadingScaleReady(true);
  }, []);
  useEffect(() => {
    if (!readingScaleReady) return;
    try {
      window.localStorage.setItem("papersignal-reading-scale", String(readingScale));
    } catch {
      // The selected size remains active for this page even without persistent storage.
    }
  }, [readingScale, readingScaleReady]);
  const [activeJob, setActiveJob] = useState<ActiveAnalysisJob | null>(null);
  const [jobLookupError, setJobLookupError] = useState("");
  const [sourcePdf, setSourcePdf] = useState<{ paperId: string; url: string; issuedAt: number } | null>(null);
  const [sourcePdfError, setSourcePdfError] = useState("");
  const [sourcePdfRefreshing, setSourcePdfRefreshing] = useState(false);
  const [sourceViewerOpen, setSourceViewerOpen] = useState(false);
  const [sourcePage, setSourcePage] = useState(1);
  const [sourcePageInput, setSourcePageInput] = useState("1");
  const detailsRef = useRef<HTMLElement | null>(null);
  const sourceViewerRef = useRef<HTMLDivElement | null>(null);
  const openRequestId = useRef(0);
  const pdfSignRequestId = useRef(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [engineMode, setEngineMode] = useState<"gemini" | "openai" | "extractive" | "unknown">("unknown");
  const [publicPdfUrl, setPublicPdfUrl] = useState("");
  const [publicQuery, setPublicQuery] = useState("");
  const [publicSearch, setPublicSearch] = useState<PublicSearchResult | null>(null);
  const [publicSearchError, setPublicSearchError] = useState("");
  const [publicSearchLoading, setPublicSearchLoading] = useState(false);
  const [publicImporting, setPublicImporting] = useState(false);
  const [publicSort, setPublicSort] = useState<PublicPaperSort>("relevance");
  const [publicRecommendations, setPublicRecommendations] = useState<PublicPaper[]>([]);
  const [publicRecommendationsLoading, setPublicRecommendationsLoading] = useState(false);
  const [publicRecommendationsError, setPublicRecommendationsError] = useState("");

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
    let disposed = false;
    let authEventReceived = false;
    // Subscribe before reading the persisted session to avoid a delayed
    // network getUser() lookup racing with SIGNED_OUT and restoring stale UI.
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      authEventReceived = true;
      if (!disposed) {
        setUser(session?.user ?? null);
        setBoot(false);
      }
    });
    void supabase.auth.getSession().then(({ data: sessionData, error }) => {
      if (error) throw error;
      if (!disposed && !authEventReceived) setUser(sessionData.session?.user ?? null);
      if (!disposed) setBoot(false);
    }).catch(error => {
      if (!disposed) {
        setMessage(String(error));
        setBoot(false);
      }
    });
    return () => {
      disposed = true;
      data.subscription.unsubscribe();
    };
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
    // Invalidate all private UI data whenever auth identity changes, including
    // account-to-account switches without an intervening null session.
    if (previousUserIdRef.current && previousUserIdRef.current !== user?.id) setMessage("");
    previousUserIdRef.current = user?.id ?? null;
    libraryRequestId.current += 1;
    openRequestId.current += 1;
    pdfSignRequestId.current += 1;
    setPapers([]);
    setPapersOwnerId(null);
    setLibraryError("");
    setLibraryLoading(false);
    setUploadIssue(false);
    setSelected(null);
    setSelectedOwnerId(null);
    setAnalysis(null);
    setActiveJob(null);
    setJobLookupError("");
    setSourcePdf(null);
    setSourcePdfError("");
    setSourcePdfRefreshing(false);
    setSourceViewerOpen(false);
    if (user?.id) {
      void refresh();
      void loadPublicRecommendations();
    } else {
      setPublicQuery("");
      setPublicSearch(null);
      setPublicSearchError("");
      setPublicRecommendations([]);
      setPublicRecommendationsError("");
    }
  }, [user?.id]);

  useEffect(() => { setSourcePageInput(String(sourcePage)); }, [sourcePage]);

  // Keep keyboard navigation inside the authenticated paper dialog, including on mobile.
  useEffect(() => {
    if (!selected || selectedOwnerId !== user?.id) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    detailsRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); closeDetails(); return; }
      if (event.key !== "Tab" || !detailsRef.current) return;
      const focusables = Array.from(detailsRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), iframe, [tabindex]:not([tabindex="-1"])',
      )).filter((element) => element.getClientRects().length > 0);
      if (!focusables.length) { event.preventDefault(); detailsRef.current.focus(); return; }
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === detailsRef.current)) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [selected?.id, selectedOwnerId, user?.id]);

  async function refresh() {
    const ownerId = currentUserIdRef.current;
    if (!ownerId) return;
    const requestId = ++libraryRequestId.current;
    setLibraryLoading(true);
    setLibraryError("");
    try {
      const { data, error } = await db().from("papers")
        .select("id,title,status,storage_path,created_at,page_count")
        .eq("user_id", ownerId)
        .order("created_at", { ascending: false });
      if (requestId !== libraryRequestId.current || ownerId !== currentUserIdRef.current) return;
      if (error) throw error;
      setPapers((data ?? []) as Paper[]);
      setPapersOwnerId(ownerId);
    } catch {
      if (requestId === libraryRequestId.current && ownerId === currentUserIdRef.current) {
        setLibraryError("논문 목록을 불러오지 못했습니다. 네트워크와 로그인 상태를 확인하고 다시 시도해 주세요.");
      }
    } finally {
      if (requestId === libraryRequestId.current && ownerId === currentUserIdRef.current) {
        setLibraryLoading(false);
      }
    }
  }

  function choosePdfFile() {
    if (!busy) uploadInputRef.current?.click();
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

  async function signOut() {
    if (signOutLoading) return;
    setSignOutLoading(true);
    setMessage("");
    try {
      const { error } = await db().auth.signOut();
      if (error) throw error;
      setUser(null);
      setPapers([]);
      setPapersOwnerId(null);
      setSelectedOwnerId(null);
      setSelected(null);
      setAnalysis(null);
      setActiveJob(null);
      setSourcePdf(null);
      setSourcePdfError("");
      setSourceViewerOpen(false);
      setLibraryError("");
      setJobLookupError("");
      setBusy(false);
      setMessage("로그아웃되었습니다.");
    } catch (error) {
      setMessage(authErrorMessage(error));
    } finally {
      setSignOutLoading(false);
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

  async function loadPublicRecommendations() {
    const ownerId = currentUserIdRef.current;
    if (!ownerId) return;
    setPublicRecommendationsLoading(true);
    setPublicRecommendationsError("");
    try {
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("추천 논문을 불러오려면 다시 로그인해 주세요.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("논문 추천 API가 연결되지 않았습니다.");
      const response = await fetch(api.replace(/[/]$/, "") + "/api/public-papers/recommendations", {
        headers: { Authorization: "Bearer " + data.session.access_token },
        cache: "no-store",
      });
      const payload = await response.json().catch(() => ({})) as { results?: PublicPaper[]; detail?: string };
      if (!response.ok) throw new Error(payload.detail || "추천 논문을 불러오지 못했습니다.");
      if (currentUserIdRef.current !== ownerId) return;
      setPublicRecommendations(Array.isArray(payload.results) ? payload.results : []);
    } catch (cause) {
      if (currentUserIdRef.current === ownerId) {
        setPublicRecommendationsError((cause as Error).message || "추천 논문을 불러오지 못했습니다.");
      }
    } finally {
      if (currentUserIdRef.current === ownerId) setPublicRecommendationsLoading(false);
    }
  }

  async function searchPublicPapers(
    apiPage = 1,
    queryOverride?: string,
    sortOverride: PublicPaperSort = publicSort,
    append = false,
    targetUiPage = 1,
  ) {
    if (!user || publicSearchLoading) return;
    // Pagination always uses the immutable query stored with the result set.
    // Editing/clearing the input must not invalidate already displayed results.
    const term = (queryOverride ?? publicQuery).trim();
    if (term.length < 2) {
      setPublicSearchError("검색어를 두 글자 이상 입력해 주세요.");
      return;
    }
    const ownerId = user.id;
    setPublicSearchLoading(true);
    setPublicSearchError("");
    try {
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("검색하려면 다시 로그인해 주세요.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("논문 검색 API가 연결되지 않았습니다.");
      const params = new URLSearchParams({
        query: term,
        page: String(apiPage),
        sort: sortOverride,
      });
      const response = await fetch(
        api.replace(/[/]$/, "") + "/api/public-papers/search?" + params.toString(),
        { headers: { Authorization: "Bearer " + data.session.access_token }, cache: "no-store" },
      );
      const payload = await response.json().catch(() => ({})) as {
        query?: string; page?: number; total?: number; has_more?: boolean;
        results?: PublicPaper[]; detail?: string;
      };
      if (!response.ok) throw new Error(payload.detail || "공개 논문 검색에 실패했습니다.");
      if (currentUserIdRef.current !== ownerId) return;
      setPublicSearch(previous => {
        if (append && previous && previous.query === term && previous.sort === sortOverride) {
          const known = new Set(previous.results.map(item => item.id));
          const additional = (payload.results ?? []).filter(item => !known.has(item.id));
          return {
            ...previous,
            results: [...previous.results, ...additional],
            apiPage: payload.page ?? apiPage,
            total: payload.total ?? previous.total,
            has_more: Boolean(payload.has_more),
            page: targetUiPage,
          };
        }
        return {
          query: term,
          page: 1,
          apiPage: payload.page ?? apiPage,
          total: payload.total ?? 0,
          has_more: Boolean(payload.has_more),
          results: Array.isArray(payload.results) ? payload.results : [],
          sort: sortOverride,
        };
      });
    } catch (cause) {
      if (currentUserIdRef.current === ownerId) {
        setPublicSearchError((cause as Error).message || "논문 검색 중 오류가 발생했습니다.");
      }
    } finally {
      setPublicSearchLoading(false);
    }
  }

  function changePublicSearchPage(nextPage: number) {
    if (!publicSearch || publicSearchLoading || nextPage < 1) return;
    const loadedPages = Math.ceil(publicSearch.results.length / 10);
    if (nextPage <= loadedPages) {
      setPublicSearch(previous => previous ? { ...previous, page: nextPage } : previous);
      return;
    }
    if (nextPage === loadedPages + 1 && publicSearch.has_more) {
      void searchPublicPapers(
        publicSearch.apiPage + 1,
        publicSearch.query,
        publicSearch.sort,
        true,
        nextPage,
      );
    }
  }

  function changePublicSort(nextSort: PublicPaperSort) {
    setPublicSort(nextSort);
    if (publicSearch) {
      void searchPublicPapers(1, publicSearch.query, nextSort);
    }
  }

  async function importPublicPdf(url: string, title?: string) {
    if (!user || busy || publicImporting) return;
    const ownerId = user.id;
    setPublicImporting(true);
    setUploadIssue(false);
    setMessage("공개 PDF 원문을 안전하게 가져오고 있습니다...");
    try {
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("가져오려면 다시 로그인해 주세요.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("PDF 가져오기 API가 연결되지 않았습니다.");
      const response = await fetch(api.replace(/[/]$/, "") + "/api/public-papers/download", {
        method: "POST",
        headers: {
          Authorization: "Bearer " + data.session.access_token,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
        cache: "no-store",
      });
      if (!response.ok) {
        const failure = await response.json().catch(() => ({})) as { detail?: string };
        throw new Error(failure.detail || "공개 PDF 다운로드에 실패했습니다.");
      }
      const fileBlob = await response.blob();
      if (currentUserIdRef.current !== ownerId) return;
      const baseName = (title || "공개 금융논문").replace(/[\\/<>|?"*:]/g, "_").trim().slice(0, 150) || "public-finance-paper";
      const file = new File([fileBlob], baseName + ".pdf", { type: "application/pdf" });
      // Reuse the existing user's private Storage upload and owner-scoped
      // metadata INSERT path; no privileged server-side paper write is needed.
      await upload(file);
      setPublicPdfUrl("");
    } catch (cause) {
      if (currentUserIdRef.current === ownerId) {
        setMessage((cause as Error).message || "PDF 가져오기에 실패했습니다.");
        setUploadIssue(true);
      }
    } finally {
      setPublicImporting(false);
    }
  }

  async function upload(file?: File) {
    if (!file || !user) return;
    const ownerId = user.id;
    let stage: "validation" | "storage" | "metadata" = "validation";
    setBusy(true);
    setUploadIssue(false);
    setMessage("");
    try {
      const signature = new TextDecoder().decode(await file.slice(0, 5).arrayBuffer());
      if (!isAcceptedPdf(file.name, file.size, signature)) {
        setMessage("30MB 이하의 유효한 PDF 파일을 선택해 주세요.");
        setUploadIssue(true);
        return;
      }
      const path = ownerId + "/" + crypto.randomUUID() + ".pdf";
      stage = "storage";
      const storage = await db().storage.from("papers").upload(path, file, {
        contentType: "application/pdf", upsert: false,
      });
      if (storage.error) throw storage.error;
      stage = "metadata";
      const inserted = await db().from("papers").insert({
        user_id: ownerId,
        title: file.name.replace(/\.pdf$/i, "").slice(0, 500),
        original_filename: file.name,
        storage_path: path,
        size_bytes: file.size,
      }).select("id,title,status,storage_path,created_at,page_count").single();
      if (inserted.error) {
        // Insert might have committed before a response was lost. Never delete
        // the uploaded source automatically and leave a valid paper without its PDF.
        // Private orphan cleanup requires a separately verified admin procedure.
        throw inserted.error;
      }
      if (currentUserIdRef.current !== ownerId) return;
      await refresh();
      await open(inserted.data as Paper);
      setMessage("논문 업로드 완료. 분석을 시작할 수 있습니다.");
    } catch (error) {
      if (currentUserIdRef.current === ownerId) {
        setMessage(uploadFailureMessage(stage, error));
        setUploadIssue(true);
      }
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

  function closeDetails() {
    openRequestId.current += 1;
    pdfSignRequestId.current += 1;
    setSelected(null);
    setSelectedOwnerId(null);
    setSourcePdf(null);
    setSourcePdfError("");
    setSourcePdfRefreshing(false);
    setSourceViewerOpen(false);
  }

  async function renewPdfLink(paper: Paper) {
    const requestId = openRequestId.current;
    const signRequestId = ++pdfSignRequestId.current;
    setSourcePdfRefreshing(true);
    setSourcePdfError("");
    try {
      const { data, error } = await db().storage.from("papers").createSignedUrl(paper.storage_path, 3600);
      if (openRequestId.current !== requestId || pdfSignRequestId.current !== signRequestId) return;
      if (error || !data?.signedUrl) {
        setSourcePdfError(sourcePdfFailureMessage(error));
      } else {
        setSourcePdf({ paperId: paper.id, url: data.signedUrl, issuedAt: Date.now() });
      }
    } catch {
      if (openRequestId.current === requestId && pdfSignRequestId.current === signRequestId) {
        setSourcePdfError("원문 PDF 연결 중 네트워크 오류가 발생했습니다. 다시 연결을 눌러주세요.");
      }
    } finally {
      if (openRequestId.current === requestId && pdfSignRequestId.current === signRequestId) setSourcePdfRefreshing(false);
    }
  }

  async function open(paper: Paper) {
    const requestId = ++openRequestId.current;
    const signRequestId = ++pdfSignRequestId.current;
    setSelected(paper);
    setSelectedOwnerId(currentUserIdRef.current);
    setAnalysis(null);
    setActiveJob(null);
    setJobLookupError("");
    setSourcePdf(null);
    setSourcePdfError("");
    setSourcePdfRefreshing(false);
    setSourceViewerOpen(false);
    setSourcePage(1);
    setSourcePageInput("1");
    try {
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
    if (pdfSignRequestId.current === signRequestId) {
      if (signedPdf.error || !signedPdf.data?.signedUrl) {
        setSourcePdfError(sourcePdfFailureMessage(signedPdf.error));
      } else {
        setSourcePdf({ paperId: paper.id, url: signedPdf.data.signedUrl, issuedAt: Date.now() });
      }
    }
    } catch {
      if (openRequestId.current !== requestId) return;
      setJobLookupError("네트워크 오류로 분석 작업 상태를 확인하지 못했습니다. 문서를 다시 열어주세요.");
      if (pdfSignRequestId.current === signRequestId) {
        setSourcePdfError("네트워크 오류로 원문 PDF를 연결하지 못했습니다. 다시 연결을 눌러주세요.");
      }
    }
  }

  function maybeRenewSourcePdf() {
    if (selected && sourcePdf?.paperId === selected.id && pdfLinkNeedsRefresh(sourcePdf.issuedAt) && !sourcePdfRefreshing) {
      void renewPdfLink(selected);
    }
  }

  function showOriginalPdfPage(page: number) {
    if (!selected) return;
    maybeRenewSourcePdf();
    setSourcePage(clampPdfPage(page, selected.page_count));
    setSourceViewerOpen(true);
    window.setTimeout(() => {
      sourceViewerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 0);
  }

  function toggleSourceViewer() {
    if (!selected) return;
    if (!sourceViewerOpen) maybeRenewSourcePdf();
    setSourceViewerOpen((value) => !value);
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
        <label>이메일<input type="email" autoComplete="email" required value={email} onChange={event => { setEmail(event.target.value); setConfirmationPending(false); }} placeholder="name@example.com"/></label>
        <label>비밀번호<input type="password" autoComplete={signup ? "new-password" : "current-password"} required minLength={signup ? 8 : 1} value={password} onChange={event => setPassword(event.target.value)} placeholder="8자 이상 입력"/></label>
        <button className="primary" disabled={authLoading}>{authLoading ? "인증 처리 중..." : signup ? "회원가입" : "로그인"} →</button>
      </form>
      <div className="auth-divider"><span>또는</span></div>
      <button type="button" className="google-button" disabled={authLoading} onClick={() => void googleAuth()}>
        <span className="google-mark" aria-hidden="true">G</span>
        {authLoading ? "Google 계정 연결 중..." : "Google로 계속하기"}
      </button>
      <p className="note" role="status" aria-live="polite">{message}</p>
      <p className="toggle"><button type="button" onClick={() => { setSignup(!signup); setConfirmationPending(false); setMessage(""); }}>{signup ? "로그인으로 돌아가기" : "계정이 없나요? 회원가입"}</button></p>
      {confirmationPending && <div className="auth-confirmation" role="status">
        <p>인증 메일 링크를 열면 이메일 확인 후 PaperSignal 연구 공간으로 돌아옵니다.</p>
        <button type="button" className="resend" disabled={resendingConfirmation} onClick={() => void resendConfirmation()}>
          {resendingConfirmation ? "재전송 요청 중..." : "인증 메일 다시 보내기"}
        </button>
      </div>}
    </div></section>
  </main>;

  const sortedSearchResults = publicSearch
    ? sortPublicPapers(publicSearch.results, publicSearch.sort)
    : [];
  const visibleSearchResults = sortedSearchResults.slice(
    (publicSearch?.page ?? 1) * 10 - 10,
    (publicSearch?.page ?? 1) * 10,
  );
  const loadedSearchPages = publicSearch ? Math.ceil(publicSearch.results.length / 10) : 0;

  function renderPublicPaper(item: PublicPaper) {
    return <li key={item.id} className="public-paper-result">
      <div className="public-paper-result-info">
        <strong>{item.title}</strong>
        <span>{[item.year, ...item.authors].filter(Boolean).join(" · ") || "서지정보 확인 필요"}</span>
        <span className="public-paper-citation">OpenAlex 인용 {item.cited_by_count.toLocaleString("ko-KR")}회</span>
        <small>{item.category ? item.category + " · " : ""}원문 이용 허락: {item.license}</small>
      </div>
      <div className="public-paper-result-actions">
        {item.landing_url.startsWith("https://") &&
          <a href={item.landing_url} target="_blank" rel="noopener noreferrer">원문 ↗</a>}
        {item.pdf_url
          ? <button type="button" onClick={() => void importPublicPdf(item.pdf_url!, item.title)}
              disabled={busy || publicImporting}>
              {publicImporting ? "가져오는 중..." : "PDF 가져오기"}
            </button>
          : <span>공개 PDF 링크 없음</span>}
      </div>
    </li>;
  }

  return <main className="workspace">
    <a href="#workspace-content" className="skip-link">연구 공간 본문으로 이동</a>
    <aside>
      <div className="brand">◈ Paper<span>Signal</span></div>
      <p className="eyebrow">WORKSPACE</p>
      <nav aria-label="주요 메뉴"><a className="nav" href="#workspace-content" aria-current="page">▤　논문 라이브러리</a></nav>
    </aside>
    <div className="content">
      <header className="workspace-header">
        <span className="workspace-breadcrumbs">Workspace / <b>논문 라이브러리</b></span>
        <span className={"workspace-engine " + (engineMode === "gemini" || engineMode === "openai" ? "engine-ready" : "engine-pending")}>
          ● {engineMode === "gemini" ? "Gemini AI 분석 활성화" : engineMode === "openai" ? "OpenAI 분석 활성화" : engineMode === "extractive" ? "텍스트 추출 모드" : "API 상태 확인 중"}
        </span>
        <span className="workspace-account" title={user.email ?? ""}>{user.email}</span>
        <button type="button" className="workspace-sign-out" onClick={() => void signOut()} disabled={signOutLoading}>{signOutLoading ? "로그아웃 중..." : "로그아웃"}</button>
      </header>
      <div className="body" id="workspace-content" tabIndex={-1}>
        {engineMode === "gemini" && <div className="provider-notice"><b>Gemini 무료 티어 데이터 안내</b><p>현재 설정에서는 업로드한 논문에서 추출한 텍스트와 AI 응답이 Google 제품 개선에 사용되거나 사람 검토자가 처리할 수 있습니다. 공개·비기밀 논문만 업로드하고, 사내 미공개 자료나 개인정보가 포함된 문서는 올리지 마세요.</p></div>}
        <div className="heading">
          <div><p className="eyebrow">RESEARCH LIBRARY</p><h1 id="paper-library-heading">나의 연구 라이브러리</h1><p>내 논문과 분석 이력을 먼저 확인하고, 새 논문은 아래에서 찾아 추가할 수 있습니다.</p></div>
          <button type="button" className="upload-button" disabled={busy} onClick={choosePdfFile}>＋ 논문 추가</button>
          <input ref={uploadInputRef} type="file" accept=".pdf,application/pdf" hidden
            aria-label="분석할 PDF 파일 선택" disabled={busy}
            onChange={event => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = ""; // allow re-selecting the same PDF
              void upload(file);
            }}/>
        </div>

        <section id="personal-research-workspace" className="personal-research-workspace" aria-label="내 작업 공간">
        <div className="stats">
          <div><p>전체 논문</p><strong>{visiblePapers.length.toString().padStart(2, "0")}</strong><small>보관 중인 논문</small></div>
          <div><p>완료된 분석</p><strong>{visiblePapers.filter(paper => paper.status === "completed").length.toString().padStart(2, "0")}</strong><small>근거 기반 결과</small></div>
          <div className="highlight"><p>RESEARCH INTELLIGENCE</p><h2>From papers<br/>to perspectives.</h2></div>
        </div>
        {libraryLoading && <p role="status" className="library-loading">논문 목록을 불러오는 중입니다...</p>}
        {libraryError && <div className="library-recovery no-print" role="alert">
          <p>{libraryError}</p>
          <button type="button" disabled={libraryLoading} onClick={() => void refresh()}>목록 다시 불러오기</button>
        </div>}
        {message && <div className="message" role="status" aria-live="polite">{message}</div>}
        {uploadIssue && <div className="recovery-actions no-print" aria-label="업로드 오류 복구">
          <button type="button" disabled={libraryLoading} onClick={() => void refresh()}>저장된 논문 목록 확인</button>
          <button type="button" disabled={busy} onClick={choosePdfFile}>PDF 다시 선택</button>
        </div>}
        <ResearchLibrary key={user.id} papers={visiblePapers} busy={busy} onOpen={open} onResume={resumeAnalysis} />
        <BetaGettingStarted userId={user.id} paperCount={visiblePapers.length}
          readyCount={visiblePapers.filter(paper => paper.status === "completed").length}
          busy={busy} onChoosePdf={choosePdfFile}/>
        </section>
        <section className="public-paper-discovery" aria-labelledby="paper-discovery-heading">
          <div className="public-paper-discovery-header">
            <div>
              <p className="eyebrow">DISCOVER & IMPORT</p>
              <h2 id="paper-discovery-heading">공개 금융 논문 찾아보기</h2>
              <p>내 작업 공간을 확인한 뒤 새 논문을 더 분석하고 싶다면, 여기서 공개 논문을 검색하거나 PDF를 가져오세요.</p>
            </div>
          </div>
          <form className="public-paper-url-form" onSubmit={event => {
            event.preventDefault();
            void importPublicPdf(publicPdfUrl.trim());
          }}>
            <label htmlFor="public-pdf-url">공개 PDF 주소로 가져오기</label>
            <div className="public-paper-input-row">
              <input id="public-pdf-url" type="url" required placeholder="https://.../paper.pdf"
                value={publicPdfUrl} onChange={event => setPublicPdfUrl(event.target.value)}
                maxLength={2048} disabled={busy || publicImporting}/>
              <button type="submit" disabled={busy || publicImporting || !publicPdfUrl.trim()}>
                {publicImporting ? "가져오는 중..." : "내 라이브러리에 가져오기"}
              </button>
            </div>
          </form>
          <form className="public-paper-search-form" onSubmit={event => {
            event.preventDefault();
            void searchPublicPapers(1, publicQuery, publicSort);
          }}>
            <label htmlFor="public-paper-search-query">공개 학술 논문 검색 (OpenAlex)</label>
            <div className="public-paper-input-row">
              <input id="public-paper-search-query" type="search" maxLength={200}
                placeholder="예: ETF arbitrage, asset pricing, portfolio risk"
                value={publicQuery} onChange={event => setPublicQuery(event.target.value)}
                disabled={publicSearchLoading}/>
              <button type="submit" disabled={publicSearchLoading || publicQuery.trim().length < 2}>
                {publicSearchLoading ? "검색 중..." : "논문 검색"}
              </button>
            </div>
          </form>
          <p className="public-paper-disclaimer">
            공개 열람 가능한 논문만 검색됩니다. 무료 열람과 재배포 허용은 다르므로 원문 이용 조건을 확인하세요.
            인용 수는 OpenAlex 기준이며 다른 학술 데이터베이스와 차이가 있을 수 있습니다.
          </p>
          <div className="public-paper-list-toolbar">
            <label htmlFor="public-paper-sort">정렬 기준</label>
            <select id="public-paper-sort" aria-label="논문 정렬" value={publicSort}
              onChange={event => changePublicSort(event.target.value as PublicPaperSort)}
              disabled={publicSearchLoading}>
              <option value="relevance">추천순 / 관련도순</option>
              <option value="citations_desc">인용 수 높은 순</option>
              <option value="title_asc">논문 제목 가나다순</option>
              <option value="author_asc">첫 번째 저자 이름순</option>
              <option value="year_desc">최신 발표순</option>
            </select>
          </div>
          {publicSearchError && <p role="alert" className="public-paper-error">{publicSearchError}</p>}
          {publicSearch ? <div className="public-paper-search-results" aria-label="공개 논문 검색 결과">
            <div className="public-paper-results-heading">
              <p className="public-paper-search-count">
                “{publicSearch.query}” 검색 결과 {publicSearch.total.toLocaleString("ko-KR")}편 ·
                {publicSearch.results.length.toLocaleString("ko-KR")}편 불러옴
              </p>
              <button type="button" className="public-paper-reset" disabled={publicSearchLoading}
                onClick={() => {
                  setPublicSearch(null);
                  setPublicQuery("");
                  setPublicSearchError("");
                  setPublicSort("relevance");
                }}>추천 논문 보기</button>
            </div>
            {publicQuery.trim() !== publicSearch.query && <p className="public-paper-query-snapshot">
              현재 목록은 “{publicSearch.query}” 검색 당시의 결과입니다. 검색창을 수정하거나 비워도 이 목록의 페이지 이동은 유지됩니다.
              새 검색어를 적용하려면 검색 버튼을 눌러 주세요.
            </p>}
            {visibleSearchResults.length === 0 && <p>검색 결과가 없습니다. 다른 키워드를 입력해 보세요.</p>}
            <ul className="public-paper-result-list">
              {visibleSearchResults.map(renderPublicPaper)}
            </ul>
            <div className="public-paper-pagination">
              <button type="button" disabled={publicSearchLoading || publicSearch.page <= 1}
                onClick={() => changePublicSearchPage(publicSearch.page - 1)}>이전</button>
              <span>{publicSearch.page}페이지 · {loadedSearchPages}페이지 불러옴</span>
              <button type="button"
                disabled={publicSearchLoading || (publicSearch.page >= loadedSearchPages && !publicSearch.has_more)}
                onClick={() => changePublicSearchPage(publicSearch.page + 1)}>다음</button>
            </div>
          </div> : <div className="public-paper-search-results" aria-label="추천 공개 금융 논문">
            <div className="public-paper-results-heading">
              <div>
                <h3 className="public-paper-recommendation-title">어떤 논문을 읽을지 모르겠다면, 여기서 시작하세요</h3>
                <p className="public-paper-search-count">금융·경제 분야에서 인용이 많은 공개 논문을 분야별로 추천합니다.</p>
              </div>
              <button type="button" className="public-paper-refresh" disabled={publicRecommendationsLoading}
                onClick={() => void loadPublicRecommendations()}>
                {publicRecommendationsLoading ? "불러오는 중..." : "추천 새로고침"}
              </button>
            </div>
            {publicRecommendationsLoading && <p role="status">분야별 추천 논문을 불러오고 있습니다...</p>}
            {publicRecommendationsError && <p role="alert" className="public-paper-error">
              {publicRecommendationsError}
              <button type="button" onClick={() => void loadPublicRecommendations()}>다시 시도</button>
            </p>}
            {!publicRecommendationsLoading && !publicRecommendationsError && publicRecommendations.length === 0 &&
              <p>현재 추천할 수 있는 공개 PDF 논문이 없습니다. 검색어를 입력해 직접 찾아보세요.</p>}
            <ul className="public-paper-result-list">
              {sortPublicPapers(publicRecommendations, publicSort).map(renderPublicPaper)}
            </ul>
          </div>}
        </section>
      </div>
    </div>

    {selected && selectedOwnerId === user.id && <div className="overlay" onClick={closeDetails}>
      <section className="details" role="dialog" aria-modal="true" aria-labelledby="paper-detail-title" tabIndex={-1} ref={detailsRef}
        onClick={event => event.stopPropagation()}>
        <div className="detail-toolbar no-print">
          <div className="detail-toolbar-left">
            <button type="button" className="detail-back" onClick={closeDetails}>← 라이브러리</button>
            <span className="detail-account" title={user.email ?? ""}>{user.email}</span>
          </div>
          <div className="detail-toolbar-actions">
            <div className="reading-size-controls" role="group" aria-label="보고서 글자 크기">
              <span className="reading-size-label">글자 크기</span>
              <button type="button" className="reading-size-button" aria-label="글자 크기 줄이기"
                title="글자 크기 줄이기" disabled={readingScale <= 80}
                onClick={() => setReadingScale(value => Math.max(80, value - 10))}>A−</button>
              <output className="reading-size-value" aria-live="polite">{readingScale}%</output>
              <button type="button" className="reading-size-button" aria-label="글자 크기 키우기"
                title="글자 크기 키우기" disabled={readingScale >= 140}
                onClick={() => setReadingScale(value => Math.min(140, value + 10))}>A+</button>
              <button type="button" className="reading-size-reset" aria-label="글자 크기 기본값으로"
                title="글자 크기 기본값으로" disabled={readingScale === 90}
                onClick={() => setReadingScale(90)}>기본</button>
            </div>
          {sourcePdf?.paperId === selected.id
            ? <div className="source-pdf-actions">
                <button type="button" className="source-pdf-button" aria-controls="paper-original-pdf" aria-expanded={sourceViewerOpen}
                  onClick={toggleSourceViewer}>
                  {sourceViewerOpen ? "원문 PDF 접기" : "원문 PDF 함께 보기"}
                </button>
                <a className="source-pdf-button source-pdf-external" href={originalPdfPageUrl(sourcePdf.url, sourcePage, selected.page_count)}
                  target="_blank" rel="noreferrer" onClick={event => {
                    if (pdfLinkNeedsRefresh(sourcePdf.issuedAt)) {
                      event.preventDefault();
                      if (!sourcePdfRefreshing) void renewPdfLink(selected);
                    }
                  }}>새 탭 ↗</a>
                <button type="button" className="source-pdf-button" disabled={sourcePdfRefreshing}
                  onClick={() => void renewPdfLink(selected)} aria-label="원문 PDF 보안 링크 갱신">
                  {sourcePdfRefreshing ? "갱신 중..." : "링크 갱신"}
                </button>
                {sourcePdfError && <span className="source-pdf-status source-pdf-error" role="alert">{sourcePdfError}</span>}
              </div>
            : <div className="source-pdf-actions">
                <span className="source-pdf-status" role="status">{sourcePdfRefreshing ? "원문 PDF 다시 연결 중..." : sourcePdfError || "원문 PDF 연결 준비 중..."}</span>
                {sourcePdfError && <button type="button" className="source-pdf-button" disabled={sourcePdfRefreshing}
                  onClick={() => void renewPdfLink(selected)}>다시 연결</button>}
              </div>}

            {analysis && <button type="button" className="detail-report-button" onClick={() => window.print()}>보고서 PDF 저장</button>}
            <button type="button" className="detail-sign-out" onClick={() => void signOut()} disabled={signOutLoading}>{signOutLoading ? "로그아웃 중..." : "로그아웃"}</button>
            <button type="button" className="close" aria-label="논문 상세 화면 닫기" onClick={closeDetails}>×</button>
          </div>
        </div>
        <p className="eyebrow">PAPER INTELLIGENCE</p>
        <h2 id="paper-detail-title">{selected.title}</h2>
        <p>연구 설계부터 실증 결과까지 원문 페이지 근거와 함께 검토하세요.</p>
        {activeJob && <div className="active-job-banner no-print" role="status">
          <strong>이미 진행 중인 분석이 있습니다.</strong>
          <p>상태: {activeJob.status === "queued" ? "대기 중" : activeJob.stage === "gemini_analysis" ? "Gemini AI 분석 중" : "처리 중"} · 브라우저를 닫아도 서버 작업은 계속됩니다.</p>
          <button type="button" className="primary" disabled={busy} onClick={() => void resumeAnalysis(selected, activeJob.id)}>
            {busy ? "작업 상태 확인 중..." : "진행 중인 분석 이어 확인 →"}
          </button>
        </div>}
        {sourceViewerOpen && sourcePdf?.paperId === selected.id && <section className="inline-pdf-viewer no-print" id="paper-original-pdf" ref={sourceViewerRef} aria-label="업로드한 원본 PDF">
          <div className="inline-pdf-heading">
            <div><b>원본 PDF</b><span>업로드한 PDF 페이지를 그대로 표시합니다. 요약이나 HTML로 재구성한 화면이 아닙니다.</span></div>
            <div className="inline-pdf-controls">
              <button type="button" disabled={sourcePage <= 1} onClick={() => { maybeRenewSourcePdf(); setSourcePage((value) => clampPdfPage(value - 1, selected.page_count)); }}>이전</button>
              <label>페이지
                <input type="text" inputMode="numeric" pattern="[0-9]*" maxLength={6}
                  value={sourcePageInput}
                  onFocus={event => event.currentTarget.select()}
                  onChange={event => setSourcePageInput(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); }}
                  onBlur={() => {
                    const page = commitPdfPageInput(sourcePageInput, sourcePage, selected.page_count);
                    if (page !== sourcePage) maybeRenewSourcePdf();
                    setSourcePage(page);
                    setSourcePageInput(String(page));
                  }}
                  aria-label="원문 PDF 페이지 번호"/>
                <span>/ {selected.page_count ?? "?"}</span>
              </label>
              <button type="button" disabled={Boolean(selected.page_count && sourcePage >= selected.page_count)}
                onClick={() => { maybeRenewSourcePdf(); setSourcePage((value) => clampPdfPage(value + 1, selected.page_count)); }}>다음</button>
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
          <p className="inline-pdf-fallback">모바일 브라우저에서 PDF가 작게 보이거나 열리지 않으면 위의 <b>새 탭</b>으로 원본을 확인하세요. 링크가 만료되면 <b>링크 갱신</b>을 누르세요.</p>
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
          : <div className="result" data-reading-scale={readingScale} style={{ "--reading-scale": readingScale / 100 } as CSSProperties}>
              <p className="mode">{analysis.result.mode === "llm"
                ? "AI 구조화 분석 · 인용 근거 검증"
                : "텍스트 추출 분석 · AI 생성 아님"}</p>
              {analysis.result.bibliographic && (
                <section id="analysis-bibliography" className="analysis-section">
                  <h3>논문 서지정보</h3>
                  <p><b>{analysis.result.bibliographic.title}</b></p>
                  <p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.bibliographic.evidence}>{analysis.result.bibliographic.authors?.join(", ") || "저자 확인 불가"} · {analysis.result.bibliographic.year} · {analysis.result.bibliographic.venue}</EvidenceList></p>
                </section>
              )}
              <section id="analysis-summary" className="analysis-section">
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

              <section className="analysis-overview" aria-label="논문 핵심 정보">
                <article><span>연구 질문</span><p>{analysis.result.research_question || "확인 불가"}</p></article>
                <article><span>연구 설계</span><p>{analysis.result.methodology?.design || "확인 불가"}</p></article>
                <article><span>표본 · 연구 기간</span><p>{[analysis.result.methodology?.sample, analysis.result.methodology?.period].filter(Boolean).join(" · ") || "확인 불가"}</p></article>
                <article><span>페이지 근거 확인 결과</span><strong>{analysis.result.findings_coverage?.supported_findings_count ?? analysis.result.findings?.length ?? 0}건</strong><small>실증 결과 추출 기준</small></article>
              </section>
              <nav className="analysis-toc no-print" aria-label="분석 보고서 목차">
                {analysis.result.bibliographic && <a href="#analysis-bibliography">서지정보</a>}
                <a href="#analysis-summary">핵심 요약</a>
                <a href="#analysis-junior-guide">3분 논문 읽기</a>
                <a href="#analysis-visual-reading">표·그래프 읽기</a>
                <a href="#analysis-workplace">직무 활용</a>
                <a href="#analysis-research-question">연구 질문</a>
                <a href="#analysis-hypotheses">가설</a>
                <a href="#analysis-contributions">학술적 기여</a>
                {analysis.result.methodology && <a href="#analysis-methodology">방법론</a>}
                <a href="#analysis-findings">실증 결과</a>
                <a href="#analysis-robustness">강건성</a>
                <a href="#analysis-limitations">연구 한계</a>
                <a href="#analysis-implications">시사점</a>
                <a href="#analysis-keywords">키워드</a>
                <a href="#analysis-source-evidence">원문 근거</a>
              </nav>
              <div id="analysis-junior-guide" className="analysis-anchor">
                <JuniorPaperGuide
                  result={analysis.result}
                  sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined}
                  onOpenSourcePage={showOriginalPdfPage}
                />
              </div>
              <div id="analysis-visual-reading" className="analysis-anchor">
                <JuniorVisualReading result={analysis.result}
                  sourcePdfReady={sourcePdf?.paperId === selected.id}
                  onOpenSourcePage={showOriginalPdfPage}
                />
              </div>
              <div id="analysis-workplace" className="analysis-anchor">
                <JuniorWorkplaceGuide result={analysis.result} paperTitle={selected.title}
                  userId={user?.id ?? ""} paperId={selected.id}
                  sourcePdfReady={sourcePdf?.paperId === selected.id}
                  onOpenSourcePage={showOriginalPdfPage}
                />
              </div>

              <section id="analysis-research-question" className="analysis-section">
                <h3>연구 질문</h3><p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.research_question_evidence}>{analysis.result.research_question || "확인 불가"}</EvidenceList></p>
              </section>
              <section id="analysis-hypotheses" className="analysis-section"><h3>연구 가설</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.hypotheses}/></section>
              <section id="analysis-contributions" className="analysis-section"><h3>학술적 기여</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.contributions}/></section>
              {analysis.result.methodology && (
                <section id="analysis-methodology" className="analysis-section">
                  <h3>연구 방법론 및 데이터 <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.methodology.evidence}/></h3>
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
                    <h4>연구 설계 및 표본 구조 검증 <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.methodology.panel_dimensions.evidence}/></h4>
                    <div className="method-grid">
                      <div><b>연구 설계 유형</b><p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.methodology.panel_dimensions.study_design_evidence}>{studyDesignLabel(analysis.result.methodology.panel_dimensions.study_design_type)}</EvidenceList></p></div>
                      <div><b>패널 균형 여부</b><p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.methodology.panel_dimensions.panel_balance_evidence}>{panelBalanceLabel(analysis.result.methodology.panel_dimensions.panel_balance)}</EvidenceList></p></div>
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
                          <p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={conflict.evidence}>원문 보고값: {conflict.reported_values.join(" / ")} · 출처 위치: {conflict.sections.join(" · ")}</EvidenceList></p>
                        </article>
                      )}
                    </>}
                    {!!analysis.result.methodology.panel_dimensions.sample_count_reports?.length && <>
                      <h4>원문 표본 수 기록</h4>
                      {analysis.result.methodology.panel_dimensions.sample_count_reports.map((report, index) =>
                        <article className="analysis-card" key={index}>
                          <b>{report.label} · {report.metric}</b>
                          <p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={report.evidence}>{report.count.toLocaleString()} · {report.section}</EvidenceList></p>
                        </article>
                      )}
                    </>}
                  </>}
                  {!!analysis.result.methodology.variables?.length && <>
                    <h4>주요 변수 <EvidenceList
                      sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined}
                      onOpenSourcePage={showOriginalPdfPage}
                      items={groupedVariableEvidence(analysis.result.methodology.variables)}
                    /></h4>
                    {analysis.result.methodology.variables.map((variable, index) =>
                      <article className="analysis-card" key={index}>
                        <b>{variable.name}</b><span className="tag">{variable.role}</span>
                        <p>{variable.definition}</p>
                      </article>
                    )}
                  </>}
                  {!!analysis.result.methodology.equations?.length && <>
                    <h4>모형 및 수식</h4>
                    <div className="equation-list">
                      {analysis.result.methodology.equations.map((equation, index) =>
                        <pre className="equation" key={index}>{equation}</pre>
                      )}
                    </div>
                  </>}
                </section>
              )}
              <section id="analysis-findings" className="analysis-section">
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
                      <p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={finding.evidence}>{finding.claim}</EvidenceList></p>
                      <div className="finding-meta">
                        <span>방향: {finding.direction}</span><span>추정치: {finding.estimate}</span><span>통계적 유의성: {finding.statistical_significance}</span>
                        {finding.table_reference && (() => {
                          const page = finding.evidence?.find((item) => Number.isInteger(item.page) && item.page > 0)?.page;
                          return page
                            ? <button type="button" className="finding-source-tag"
                                onClick={() => showOriginalPdfPage(page)}>
                                표·그림: {finding.table_reference} · 원문 p.{page} 보기 ↓
                              </button>
                            : <span>표·그림: {finding.table_reference}</span>;
                        })()}
                        {finding.model_or_column && <span>모형·열: {finding.model_or_column}</span>}
                        {finding.verification && <span className={finding.verification.status === "screen_passed" ? "verification-ok" : "verification-review"}>
                          수치·표 맥락: {finding.verification.status === "screen_passed" ? "1차 대조 통과" : "연구자 확인 필요"}
                        </span>}
                      </div>
                      {finding.verification?.unsupported_numeric_tokens?.length ? <p className="warning">인용 페이지에서 확인되지 않은 숫자: {finding.verification.unsupported_numeric_tokens.join(", ")}</p> : null}
                      {finding.verification?.direction_consistent === false && <p className="warning">추정치의 부호와 결과 방향이 일치하지 않습니다.</p>}
                      {finding.verification?.significance_supported === false && <p className="warning">통계적 유의성 표기가 인용 페이지에서 확인되지 않습니다.</p>}
                      {!!finding.significance_legend_evidence?.length && <p className="muted"><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={finding.significance_legend_evidence}>통계적 유의성 표 주석</EvidenceList></p>}
                    </article>
                  )}
              </section>
              <section id="analysis-robustness" className="analysis-section">
                <h3>강건성 검증</h3>
                {!analysis.result.robustness_checks?.length ? <p className="muted">본문에서 검증 가능한 강건성 검증을 찾지 못했습니다.</p>
                  : analysis.result.robustness_checks.map((item, index) =>
                    <article className="analysis-card" key={index}><b>{item.test}</b><p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={item.evidence}>{item.result}</EvidenceList></p></article>
                  )}
              </section>
              <section id="analysis-limitations" className="analysis-section">
                <h3>연구 한계</h3>
                {!analysis.result.limitations?.length ? <p className="muted">원문 근거가 확인된 한계가 없습니다.</p>
                  : analysis.result.limitations.map((item, index) =>
                    <article className="analysis-card" key={index}><p><EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={item.evidence}>{item.description}</EvidenceList></p></article>
                  )}
              </section>
              <section id="analysis-implications" className="analysis-section"><h3>금융·경제적 시사점</h3><ClaimList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.implications}/></section>
              <section id="analysis-keywords" className="analysis-section"><h3>핵심 키워드</h3><div className="tags">{(analysis.result.keywords ?? []).map(keyword => <span key={keyword}>{keyword}</span>)}</div></section>
              <section id="analysis-source-evidence" className="analysis-section"><h3>검증된 원문 근거 <small>{analysis.result.evidence?.length ?? 0}</small> <EvidenceList sourcePdfUrl={sourcePdf?.paperId === selected.id ? sourcePdf.url : undefined} onOpenSourcePage={showOriginalPdfPage} items={analysis.result.evidence}/></h3></section>
              {(analysis.result.warnings ?? []).map((warning, index) => <p className="warning" key={index}>{warning}</p>)}
              <p className="muted">분석 모델: {analysis.model} · 버전: {analysis.result.analysis_version ?? "legacy"}</p>
              <button disabled={busy} className="primary" onClick={() => void analyze()}>{busy ? "분석 중..." : "다시 분석하기"}</button>
            </div>}
      </section>
    </div>}
  </main>;
}
