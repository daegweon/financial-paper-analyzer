"use client";

import { useEffect, useState } from "react";
import { db } from "../lib/supabase";
import type { User } from "@supabase/supabase-js";

type Evidence = { page: number; quote: string };
type Claim = { text: string; evidence: Evidence[] };
type Finding = {
  claim: string;
  direction: string;
  estimate: string;
  statistical_significance: string;
  evidence: Evidence[];
};
type Variable = { name: string; role: string; definition: string; evidence: Evidence[] };
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

function EvidenceList({ items }: { items?: Evidence[] }) {
  if (!items?.length) return null;
  return <div className="evidence-list">{items.map((item, index) =>
    <blockquote className="evidence" key={item.page + "-" + index}>
      <b>PAGE {item.page}</b><p>{item.quote}</p>
    </blockquote>
  )}</div>;
}

function ClaimList({ items }: { items?: Claim[] }) {
  if (!items?.length) return <p className="muted">원문 근거가 확인된 항목이 없습니다.</p>;
  return <div className="analysis-cards">{items.map((item, index) =>
    <article className="analysis-card" key={index}>
      <p>{item.text}</p><EvidenceList items={item.evidence}/>
    </article>
  )}</div>;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [boot, setBoot] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signup, setSignup] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selected, setSelected] = useState<Paper | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [engineMode, setEngineMode] = useState<"gemini" | "openai" | "extractive" | "unknown">("unknown");

  useEffect(() => {
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
      setPapers([]);
      setSelected(null);
      setAnalysis(null);
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
    setMessage("");
    try {
      const result = signup
        ? await db().auth.signUp({ email, password })
        : await db().auth.signInWithPassword({ email, password });
      setMessage(result.error?.message ?? (signup ? "가입 확인 메일을 확인해 주세요." : ""));
    } catch (error) {
      setMessage((error as Error).message);
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

  async function open(paper: Paper) {
    setSelected(paper);
    setAnalysis(null);
    const result = await db().from("analyses").select("result,model,created_at")
      .eq("paper_id", paper.id).order("created_at", { ascending: false }).limit(1);
    if (result.error) setMessage(result.error.message);
    else if (result.data?.[0]) setAnalysis(result.data[0] as Analysis);
  }

  async function analyze() {
    if (!selected) return;
    setBusy(true);
    setMessage("");
    try {
      const { data } = await db().auth.getSession();
      if (!data.session) throw new Error("로그인이 필요합니다.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("분석 API가 아직 연결되지 않았습니다.");
      const response = await fetch(api.replace(/\/$/, "") + "/api/analyze/" + selected.id, {
        method: "POST",
        headers: { Authorization: "Bearer " + data.session.access_token },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail ?? "논문 분석에 실패했습니다.");
      await refresh();
      await open({ ...selected, status: "completed", page_count: payload.page_count });
      setMessage(payload.mode === "llm"
        ? "AI 구조화 분석이 완료됐습니다. 원문 근거를 확인해 주세요."
        : "텍스트 추출 분석이 완료됐습니다. 생성형 AI는 아직 연결되지 않았습니다.");
    } catch (error) {
      setMessage((error as Error).message);
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
        <label>이메일<input type="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="name@example.com"/></label>
        <label>비밀번호<input type="password" required minLength={signup ? 8 : 1} value={password} onChange={event => setPassword(event.target.value)} placeholder="8자 이상 입력"/></label>
        <button className="primary">{signup ? "회원가입" : "로그인"} →</button>
      </form>
      <p className="note">{message}</p>
      <p className="toggle"><button onClick={() => setSignup(!signup)}>{signup ? "로그인으로 돌아가기" : "계정이 없나요? 회원가입"}</button></p>
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
        <section className="library">
          <h2>논문 라이브러리 <small>{papers.length}</small></h2>
          <label className="drop">⇧　 PDF 파일을 선택하거나 여기에 놓으세요
            <small>30 MB 이하 · 암호화된 PDF 제외</small>
            <input type="file" accept=".pdf,application/pdf" disabled={busy} onChange={event => void upload(event.target.files?.[0])}/>
          </label>
          {papers.length === 0
            ? <div className="empty">📄<h3>아직 등록된 논문이 없습니다</h3><p>첫 금융 연구 논문을 업로드해 주세요.</p></div>
            : papers.map(paper =>
              <button className={"paper " + (selected?.id === paper.id ? "active" : "")} key={paper.id} onClick={() => void open(paper)}>
                <span>📕</span><div><b>{paper.title}</b><small>{new Date(paper.created_at).toLocaleDateString("ko-KR")} · {paper.page_count ?? "—"} pages</small></div>
                <em>{paper.status === "completed" ? "분석 완료" : "분석 대기"}</em><span>→</span>
              </button>
            )}
        </section>
        {message && <div className="message" role="status">{message}</div>}
      </div>
    </div>

    {selected && <div className="overlay" onClick={() => setSelected(null)}>
      <section className="details" onClick={event => event.stopPropagation()}>
        <button className="close" onClick={() => setSelected(null)}>×</button>
        <p className="eyebrow">PAPER INTELLIGENCE</p>
        <h2>{selected.title}</h2>
        <p>연구 설계부터 실증 결과까지 원문 페이지 근거와 함께 검토하세요.</p>
        {!analysis
          ? <div className="prompt">
              <div>✧</div><h3>논문 분석 준비 완료</h3>
              <p>{engineMode === "gemini" || engineMode === "openai"
                ? "AI가 연구 질문, 계량 방법론, 실증 결과, 강건성 검증을 구조화하고 페이지별 인용을 확인합니다."
                : "현재는 텍스트 추출 모드입니다. Railway에 선택한 AI 제공자의 API 키를 설정하면 구조화된 금융 연구 분석이 활성화됩니다."}</p>
              <button disabled={busy} className="primary" onClick={() => void analyze()}>{busy ? "분석 중..." : "분석 시작 →"}</button>
            </div>
          : <div className="result">
              <p className="mode">{analysis.result.mode === "llm"
                ? "AI 구조화 분석 · 인용 근거 검증"
                : "텍스트 추출 분석 · AI 생성 아님"}</p>
              {analysis.result.bibliographic && (
                <section className="analysis-section">
                  <h3>논문 서지정보</h3>
                  <p><b>{analysis.result.bibliographic.title}</b></p>
                  <p>{analysis.result.bibliographic.authors?.join(", ") || "저자 확인 불가"} · {analysis.result.bibliographic.year} · {analysis.result.bibliographic.venue}</p>
                  <EvidenceList items={analysis.result.bibliographic.evidence}/>
                </section>
              )}
              <section className="analysis-section"><h3>핵심 요약</h3><p>{analysis.result.summary}</p></section>
              <section className="analysis-section">
                <h3>연구 질문</h3><p>{analysis.result.research_question || "확인 불가"}</p>
                <EvidenceList items={analysis.result.research_question_evidence}/>
              </section>
              <section className="analysis-section"><h3>연구 가설</h3><ClaimList items={analysis.result.hypotheses}/></section>
              <section className="analysis-section"><h3>학술적 기여</h3><ClaimList items={analysis.result.contributions}/></section>
              {analysis.result.methodology && (
                <section className="analysis-section">
                  <h3>연구 방법론 및 데이터</h3>
                  <div className="method-grid">
                    <div><b>연구 설계</b><p>{analysis.result.methodology.design}</p></div>
                    <div><b>표본</b><p>{analysis.result.methodology.sample}</p></div>
                    <div><b>분석 기간</b><p>{analysis.result.methodology.period}</p></div>
                    <div><b>추정 전략</b><p>{analysis.result.methodology.empirical_strategy}</p></div>
                    <div><b>식별 전략</b><p>{analysis.result.methodology.identification_strategy}</p></div>
                  </div>
                  {!!analysis.result.methodology.data_sources?.length && <p><b>데이터 출처:</b> {analysis.result.methodology.data_sources.join(" · ")}</p>}
                  {!!analysis.result.methodology.variables?.length && <>
                    <h4>주요 변수</h4>
                    {analysis.result.methodology.variables.map((variable, index) =>
                      <article className="analysis-card" key={index}>
                        <b>{variable.name}</b><span className="tag">{variable.role}</span><p>{variable.definition}</p>
                        <EvidenceList items={variable.evidence}/>
                      </article>
                    )}
                  </>}
                  {!!analysis.result.methodology.equations?.length && <>
                    <h4>모형 및 수식</h4>{analysis.result.methodology.equations.map((equation, index) => <pre className="equation" key={index}>{equation}</pre>)}
                  </>}
                  <EvidenceList items={analysis.result.methodology.evidence}/>
                </section>
              )}
              <section className="analysis-section">
                <h3>주요 실증 결과 <small>{analysis.result.findings?.length ?? 0}</small></h3>
                {!analysis.result.findings?.length
                  ? <p className="muted">검증된 실증 결과가 없습니다.</p>
                  : analysis.result.findings.map((finding, index) =>
                    <article className="analysis-card" key={index}>
                      <p>{finding.claim}</p>
                      <div className="finding-meta">
                        <span>방향: {finding.direction}</span><span>추정치: {finding.estimate}</span><span>통계적 유의성: {finding.statistical_significance}</span>
                      </div>
                      <EvidenceList items={finding.evidence}/>
                    </article>
                  )}
              </section>
              <section className="analysis-section">
                <h3>강건성 검증</h3>
                {!analysis.result.robustness_checks?.length ? <p className="muted">본문에서 검증 가능한 강건성 검증을 찾지 못했습니다.</p>
                  : analysis.result.robustness_checks.map((item, index) =>
                    <article className="analysis-card" key={index}><b>{item.test}</b><p>{item.result}</p><EvidenceList items={item.evidence}/></article>
                  )}
              </section>
              <section className="analysis-section">
                <h3>연구 한계</h3>
                {!analysis.result.limitations?.length ? <p className="muted">원문 근거가 확인된 한계가 없습니다.</p>
                  : analysis.result.limitations.map((item, index) =>
                    <article className="analysis-card" key={index}><p>{item.description}</p><EvidenceList items={item.evidence}/></article>
                  )}
              </section>
              <section className="analysis-section"><h3>금융·경제적 시사점</h3><ClaimList items={analysis.result.implications}/></section>
              <section className="analysis-section"><h3>핵심 키워드</h3><div className="tags">{(analysis.result.keywords ?? []).map(keyword => <span key={keyword}>{keyword}</span>)}</div></section>
              <section className="analysis-section"><h3>검증된 원문 근거 <small>{analysis.result.evidence?.length ?? 0}</small></h3><EvidenceList items={analysis.result.evidence}/></section>
              {(analysis.result.warnings ?? []).map((warning, index) => <p className="warning" key={index}>{warning}</p>)}
              <p className="muted">분석 모델: {analysis.model} · 버전: {analysis.result.analysis_version ?? "legacy"}</p>
              <button disabled={busy} className="primary" onClick={() => void analyze()}>{busy ? "분석 중..." : "다시 분석하기"}</button>
            </div>}
      </section>
    </div>}
  </main>;
}
