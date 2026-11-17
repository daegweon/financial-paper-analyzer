"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { db } from "../lib/supabase";
import styles from "./ResearchLibrary.module.css";

type Paper = {
  id: string;
  title: string;
  status: string;
  storage_path: string;
  created_at: string;
  page_count: number | null;
};

type AnalysisResult = {
  analysis_version?: string;
  bibliographic?: {
    title?: string;
    authors?: string[];
    year?: string;
    venue?: string;
    doi?: string;
  };
  research_question?: string;
  methodology?: {
    design?: string;
    sample?: string;
    period?: string;
    data_sources?: string[];
    empirical_strategy?: string;
    identification_strategy?: string;
    variables?: { name?: string; role?: string; definition?: string }[];
  };
  findings?: {
    claim?: string;
    direction?: string;
    estimate?: string;
    statistical_significance?: string;
  }[];
  robustness_checks?: { test?: string; result?: string }[];
  limitations?: { description?: string }[];
  keywords?: string[];
};

type AnalysisRecord = {
  paper_id: string;
  result: AnalysisResult;
  model: string;
  created_at: string;
};

type Job = {
  id: string;
  paper_id: string;
  status: string;
  stage: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
};

type ComparisonEntry = {
  paper: Paper;
  analysis: AnalysisRecord | null;
};

type ComparisonRow = {
  label: string;
  values: string[];
};

function textOrDash(value?: string | null) {
  return value?.trim() || "—";
}

function listOrDash(values?: string[]) {
  return values?.filter(Boolean).join(" / ") || "—";
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function jobStatusLabel(status?: string, paperStatus?: string) {
  const value = status || paperStatus || "uploaded";
  const labels: Record<string, string> = {
    queued: "분석 대기",
    processing: "분석 중",
    completed: "분석 완료",
    failed: "분석 실패",
    uploaded: "미분석",
  };
  return labels[value] || value;
}

function jobStageLabel(stage?: string) {
  const labels: Record<string, string> = {
    queued: "대기열",
    pdf_download: "PDF 다운로드 및 텍스트 추출",
    gemini_analysis: "AI 분석",
    completed: "완료",
    failed: "실패",
  };
  return stage ? labels[stage] || stage : "—";
}

function buildComparisonRows(entries: ComparisonEntry[]): ComparisonRow[] {
  const values = (getValue: (result: AnalysisResult, entry: ComparisonEntry) => string) =>
    entries.map((entry) => entry.analysis ? getValue(entry.analysis.result || {}, entry) : "—");

  return [
    {
      label: "분석 상태",
      values: entries.map((entry) => entry.analysis ? "분석 결과 있음" : "분석 결과 없음"),
    },
    {
      label: "서지정보",
      values: values((result) => {
        const bib = result.bibliographic;
        if (!bib) return "—";
        return [
          bib.authors?.join(", "),
          bib.year,
          bib.venue,
          bib.doi ? "DOI: " + bib.doi : "",
        ].filter(Boolean).join(" · ") || "—";
      }),
    },
    {
      label: "연구 질문",
      values: values((result) => textOrDash(result.research_question)),
    },
    {
      label: "연구 설계",
      values: values((result) => textOrDash(result.methodology?.design)),
    },
    {
      label: "표본",
      values: values((result) => textOrDash(result.methodology?.sample)),
    },
    {
      label: "연구 기간",
      values: values((result) => textOrDash(result.methodology?.period)),
    },
    {
      label: "데이터 출처",
      values: values((result) => listOrDash(result.methodology?.data_sources)),
    },
    {
      label: "추정 전략",
      values: values((result) => textOrDash(result.methodology?.empirical_strategy)),
    },
    {
      label: "식별 전략",
      values: values((result) => textOrDash(result.methodology?.identification_strategy)),
    },
    {
      label: "주요 변수",
      values: values((result) => result.methodology?.variables?.length
        ? result.methodology.variables.map((item) =>
            [item.name, item.role ? "(" + item.role + ")" : "", item.definition].filter(Boolean).join(" ")
          ).join("\n")
        : "—"),
    },
    {
      label: "주요 실증 결과",
      values: values((result) => result.findings?.length
        ? result.findings.map((item, index) =>
            (index + 1) + ". " + textOrDash(item.claim) +
            "\n방향: " + textOrDash(item.direction) +
            " · 추정치: " + textOrDash(item.estimate) +
            " · 유의성: " + textOrDash(item.statistical_significance)
          ).join("\n\n")
        : "—"),
    },
    {
      label: "강건성 검증",
      values: values((result) => result.robustness_checks?.length
        ? result.robustness_checks.map((item) =>
            textOrDash(item.test) + ": " + textOrDash(item.result)
          ).join("\n")
        : "—"),
    },
    {
      label: "연구 한계",
      values: values((result) => result.limitations?.length
        ? result.limitations.map((item) => textOrDash(item.description)).join("\n")
        : "—"),
    },
    {
      label: "핵심 키워드",
      values: values((result) => listOrDash(result.keywords)),
    },
    {
      label: "분석 버전 및 모델",
      values: entries.map((entry) => entry.analysis
        ? textOrDash(entry.analysis.result?.analysis_version) + " · " + textOrDash(entry.analysis.model)
        : "—"),
    },
  ];
}

export function ResearchLibrary({
  papers,
  busy,
  onOpen,
  onResume,
}: {
  papers: Paper[];
  busy: boolean;
  onOpen: (paper: Paper) => void | Promise<void>;
  onResume: (paper: Paper, jobId: string) => void | Promise<void>;
}) {
  const [activeTab, setActiveTab] = useState<"library" | "jobs">("library");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest" | "title">("newest");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectionNotice, setSelectionNotice] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState("");
  const [comparison, setComparison] = useState<ComparisonEntry[] | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");

  const refreshJobs = useCallback(async () => {
    setJobsLoading(true);
    try {
      const { data, error } = await db()
        .from("analysis_jobs")
        .select("id,paper_id,status,stage,error_message,created_at,updated_at,completed_at")
        .order("created_at", { ascending: false })
        .limit(100);
      if (error) {
        setJobsError(error.message);
      } else {
        setJobs((data ?? []) as Job[]);
        setJobsError("");
      }
    } catch (error) {
      setJobsError((error as Error).message);
    } finally {
      setJobsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshJobs();
  }, [refreshJobs, busy]);

  useEffect(() => {
    const hasActiveJobs = jobs.some((job) => job.status === "queued" || job.status === "processing");
    if (!hasActiveJobs) return;
    const timer = window.setInterval(() => void refreshJobs(), 5000);
    return () => window.clearInterval(timer);
  }, [jobs, refreshJobs]);

  const latestJobByPaper = useMemo(() => {
    const latest = new Map<string, Job>();
    for (const job of jobs) {
      if (!latest.has(job.paper_id)) latest.set(job.paper_id, job);
    }
    return latest;
  }, [jobs]);

  const visiblePapers = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    return papers
      .filter((paper) => {
        if (normalizedQuery && !paper.title.toLocaleLowerCase().includes(normalizedQuery)) return false;
        const latestStatus = latestJobByPaper.get(paper.id)?.status || paper.status;
        if (statusFilter === "completed") return latestStatus === "completed";
        if (statusFilter === "failed") return latestStatus === "failed";
        if (statusFilter === "processing") return latestStatus === "queued" || latestStatus === "processing";
        if (statusFilter === "uploaded") return latestStatus === "uploaded";
        return true;
      })
      .sort((a, b) => {
        if (sortOrder === "title") return a.title.localeCompare(b.title, "ko");
        const difference = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        return sortOrder === "newest" ? -difference : difference;
      });
  }, [papers, query, statusFilter, sortOrder, latestJobByPaper]);

  function toggleSelected(paperId: string) {
    setSelectedIds((current) => {
      if (current.includes(paperId)) return current.filter((id) => id !== paperId);
      if (current.length >= 4) {
        setSelectionNotice("비교는 한 번에 최대 4편까지 가능합니다.");
        return current;
      }
      setSelectionNotice("");
      return [...current, paperId];
    });
  }

  async function openComparison() {
    const selectedPapers = selectedIds
      .map((id) => papers.find((paper) => paper.id === id))
      .filter((paper): paper is Paper => Boolean(paper));
    if (selectedPapers.length < 2) {
      setSelectionNotice("비교할 논문을 2편 이상 선택해 주세요.");
      return;
    }

    setCompareLoading(true);
    setCompareError("");
    try {
      const { data, error } = await db()
        .from("analyses")
        .select("paper_id,result,model,created_at")
        .in("paper_id", selectedPapers.map((paper) => paper.id))
        .order("created_at", { ascending: false })
        .limit(200);
      if (error) throw error;

      const latest = new Map<string, AnalysisRecord>();
      for (const record of (data ?? []) as AnalysisRecord[]) {
        if (!latest.has(record.paper_id)) latest.set(record.paper_id, record);
      }
      setComparison(selectedPapers.map((paper) => ({
        paper,
        analysis: latest.get(paper.id) ?? null,
      })));
    } catch (error) {
      setCompareError((error as Error).message || "논문 비교 데이터를 불러오지 못했습니다.");
    } finally {
      setCompareLoading(false);
    }
  }

  function downloadComparison() {
    if (!comparison?.length) return;
    const rows = [
      ["비교 항목", ...comparison.map((entry) => entry.paper.title)],
      ...buildComparisonRows(comparison).map((row) => [row.label, ...row.values]),
    ];
    const csv = rows
      .map((row) => row.map((cell) => '"' + String(cell ?? "").replace(/"/g, '""') + '"').join(","))
      .join("\r\n");
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "PaperSignal_논문비교_" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  const comparisonRows = comparison ? buildComparisonRows(comparison) : [];

  return (
    <section className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <p className={styles.eyebrow}>RESEARCH LIBRARY</p>
          <h2>논문 라이브러리 <span>{papers.length}</span></h2>
          <p className={styles.subtitle}>논문을 검색하고 분석 이력을 확인하거나 여러 연구를 비교하세요.</p>
        </div>
        <div className={styles.panelStatus}>
          <span className={busy ? styles.statusBusy : styles.statusReady}>● {busy ? "분석 작업 진행 중" : "연구 공간 준비 완료"}</span>
          <span>{papers.length}편 보관 중</span>
        </div>
      </div>

      <div className={styles.tabs} role="tablist" aria-label="연구 공간 보기">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "library"}
          className={activeTab === "library" ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab("library")}
        >
          논문 목록 <span>{papers.length}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "jobs"}
          className={activeTab === "jobs" ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab("jobs")}
        >
          분석 작업 <span>{jobs.length}</span>
        </button>
      </div>

      {activeTab === "library" ? (
        <>
          <div className={styles.controls}>
            <label className={styles.searchBox}>
              <span aria-hidden="true">⌕</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="논문 제목 검색"
                aria-label="논문 제목 검색"
              />
            </label>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} aria-label="분석 상태 필터">
              <option value="all">모든 상태</option>
              <option value="completed">분석 완료</option>
              <option value="processing">분석 중·대기</option>
              <option value="failed">분석 실패</option>
              <option value="uploaded">미분석</option>
            </select>
            <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value as "newest" | "oldest" | "title")} aria-label="논문 정렬">
              <option value="newest">최신순</option>
              <option value="oldest">오래된순</option>
              <option value="title">제목순</option>
            </select>
          </div>

          <div className={styles.selectionBar}>
            <span>{selectedIds.length}편 선택 <small>· 최대 4편 비교</small></span>
            <div>
              {selectedIds.length > 0 && (
                <button type="button" className={styles.clearButton} onClick={() => { setSelectedIds([]); setSelectionNotice(""); }}>
                  선택 해제
                </button>
              )}
              <button type="button" className={styles.compareButton} disabled={selectedIds.length < 2 || compareLoading} onClick={() => void openComparison()}>
                {compareLoading ? "비교 준비 중..." : "선택 논문 비교"}
              </button>
            </div>
          </div>
          {selectionNotice && <p className={styles.notice} role="status">{selectionNotice}</p>}
          {compareError && <p className={styles.error} role="alert">{compareError}</p>}

          <div className={styles.paperList}>
            {visiblePapers.length === 0 ? (
              <div className={styles.empty}>
                <strong>검색 결과가 없습니다.</strong>
                <span>검색어나 상태 필터를 변경해 주세요.</span>
              </div>
            ) : visiblePapers.map((paper) => {
              const job = latestJobByPaper.get(paper.id);
              const status = job?.status || paper.status;
              return (
                <article className={styles.paperRow} key={paper.id}>
                  <label className={styles.checkboxWrap} aria-label={paper.title + " 비교 대상으로 선택"}>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(paper.id)}
                      onChange={() => toggleSelected(paper.id)}
                    />
                  </label>
                  <button type="button" className={styles.paperButton} onClick={() => void onOpen(paper)}>
                    <span className={styles.pdfIcon}>PDF</span>
                    <span className={styles.paperInfo}>
                      <strong>{paper.title}</strong>
                      <small>{formatDate(paper.created_at)} · {paper.page_count ?? "페이지 정보 없음"}</small>
                    </span>
                    <span className={styles.paperStatus} data-status={status}>{jobStatusLabel(status, paper.status)}</span>
                    <span className={styles.openIcon} aria-hidden="true">↗</span>
                  </button>
                  {(job?.status === "queued" || job?.status === "processing") && (
                    <button type="button" className={styles.resumeJobButton} disabled={busy}
                      onClick={() => void onResume(paper, job.id)}>
                      이어 확인 · {jobStageLabel(job.stage)}
                    </button>
                  )}
                  {job?.status === "failed" && job.error_message && (
                    <p className={styles.jobError} title={job.error_message}>{job.error_message}</p>
                  )}
                </article>
              );
            })}
          </div>
          <p className={styles.listFooter}>
            {visiblePapers.length}편 표시
            {jobsLoading ? " · 작업 이력 동기화 중..." : ""}
          </p>
        </>
      ) : (
        <div className={styles.jobPanel}>
          <div className={styles.jobHeading}>
            <div>
              <strong>최근 분석 작업</strong>
              <p>최근 20건의 분석 요청과 처리 결과를 표시합니다.</p>
            </div>
            <button type="button" className={styles.refreshButton} onClick={() => void refreshJobs()} disabled={jobsLoading}>
              {jobsLoading ? "새로고침 중..." : "새로고침"}
            </button>
          </div>
          {jobsError && <p className={styles.error} role="alert">{jobsError}</p>}
          {jobs.length === 0 ? (
            <div className={styles.empty}>
              <strong>분석 작업 이력이 없습니다.</strong>
              <span>논문을 선택하고 분석을 시작하면 이곳에 기록됩니다.</span>
            </div>
          ) : (
            <div className={styles.jobList}>
              {jobs.slice(0, 20).map((job) => {
                const paper = papers.find((item) => item.id === job.paper_id);
                return (
                  <article className={styles.jobRow} key={job.id}>
                    <div className={styles.jobMain}>
                      <span className={styles.jobStatus} data-status={job.status}>{jobStatusLabel(job.status)}</span>
                      <strong>{paper?.title || "논문 정보 없음"}</strong>
                      <small>{formatDate(job.created_at)} · {jobStageLabel(job.stage)}</small>
                      {job.status === "failed" && job.error_message && (
                        <p className={styles.jobError}>{job.error_message}</p>
                      )}
                    </div>
                    {paper && (
                      <button type="button" className={styles.openJobButton} disabled={busy}
                        onClick={() => void ((job.status === "queued" || job.status === "processing")
                          ? onResume(paper, job.id) : onOpen(paper))}>
                        {job.status === "queued" || job.status === "processing" ? "진행 확인" : "논문 열기"}
                      </button>
                    )}
                  </article>
                );
              })}
            </div>
          )}
          <p className={styles.listFooter}>{jobs.length}건의 작업 기록 중 최근 20건 표시</p>
        </div>
      )}

      {comparison && (
        <div className={styles.modalBackdrop} role="presentation" onClick={() => setComparison(null)}>
          <section
            className={styles.modal}
            role="dialog"
            aria-modal="true"
            aria-label="선택한 금융논문 비교"
            onClick={(event) => event.stopPropagation()}
          >
            <div className={styles.modalHeading}>
              <div>
                <p className={styles.eyebrow}>CROSS-PAPER ANALYSIS</p>
                <h3>논문 비교 분석</h3>
                <p>저장된 최신 분석 결과를 기준으로 비교합니다. 결과가 없는 논문은 별도로 표시합니다.</p>
              </div>
              <button type="button" className={styles.closeButton} onClick={() => setComparison(null)} aria-label="비교 창 닫기">×</button>
            </div>
            <div className={styles.modalActions}>
              <span>{comparison.length}편 비교 · 최신 분석 기준</span>
              <button type="button" className={styles.exportButton} onClick={downloadComparison}>CSV 내보내기 ↓</button>
            </div>
            <div className={styles.tableWrap}>
              <table className={styles.compareTable}>
                <thead>
                  <tr>
                    <th scope="col">비교 항목</th>
                    {comparison.map((entry) => <th scope="col" key={entry.paper.id}>{entry.paper.title}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map((row) => (
                    <tr key={row.label}>
                      <th scope="row">{row.label}</th>
                      {row.values.map((value, index) => <td key={comparison[index].paper.id}>{value}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className={styles.modalFootnote}>비교 결과는 논문별 최신 저장 분석을 사용하며, AI 해석의 정확성을 보증하지 않습니다. 중요한 수치와 인용은 원문 PDF에서 확인하세요.</p>
          </section>
        </div>
      )}
    </section>
  );
}
