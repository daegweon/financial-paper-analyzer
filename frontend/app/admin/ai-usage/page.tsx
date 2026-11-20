"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { db } from "../../../lib/supabase";
import styles from "./page.module.css";

type ModelUsage = {
  provider: string;
  model: string;
  event_count: number;
  success_events: number;
  failed_events: number;
  total_tokens: number;
  token_usage_incomplete_events: number;
  average_latency_ms: number | null;
  known_cost_events: number;
  unknown_cost_events: number;
  estimated_cost_usd: string;
};
type UserUsage = {
  user_id: string;
  event_count: number;
  success_events: number;
  failed_events: number;
  success_rate_percent: number | null;
  total_tokens: number;
  token_complete_events: number;
  token_incomplete_events: number;
  average_latency_ms: number | null;
  known_cost_events: number;
  unknown_cost_events: number;
  estimated_cost_usd: string;
};
type Summary = {
  month: string;
  currency: string;
  event_count: number;
  known_cost_events: number;
  unknown_cost_events: number;
  estimated_cost_usd: string;
  monthly_budget_usd: string | null;
  budget_status: string;
  cost_coverage_complete: boolean;
  models: ModelUsage[];
  users: UserUsage[];
  truncated: boolean;
  notice: string;
};

function count(value: number) { return new Intl.NumberFormat("ko-KR").format(value); }

function money(value: string | null) {
  return value === null ? "미확정" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 6 }).format(Number(value));
}

function budgetStatusLabel(value: string) {
  const labels: Record<string, string> = {
    not_configured: "예산 미설정",
    within_budget: "예산 범위 내",
    exceeded: "예산 초과",
    exceeded_with_incomplete_data: "예산 초과 · 집계 일부 누락",
    incomplete_unknown_costs: "비용 미확정 이벤트 존재",
    incomplete_truncated: "조회 한도 도달 · 전체 비용 미확인",
  };
  return labels[value] ?? "상태 확인 필요";
}

export default function AdminAIUsagePage() {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [forbidden, setForbidden] = useState(false);
  const [budgetInput, setBudgetInput] = useState("");
  const [savingBudget, setSavingBudget] = useState(false);
  const [budgetMessage, setBudgetMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setForbidden(false);
    try {
      const { data, error: sessionError } = await db().auth.getSession();
      if (sessionError) throw sessionError;
      if (!data.session) throw new Error("관리자 계정으로 로그인해 주세요.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("API 주소가 설정되지 않았습니다.");
      const response = await fetch(api.replace(/\/$/, "") + "/api/admin/ai-usage/summary?month=" + encodeURIComponent(month), {
        headers: { Authorization: "Bearer " + data.session.access_token },
        cache: "no-store",
      });
      if (response.status === 403) {
        setForbidden(true);
        throw new Error("관리자 권한이 확인되지 않았습니다. 일반 사용자에게는 AI 사용량과 비용 정보가 공개되지 않습니다.");
      }
      if (!response.ok) throw new Error(response.status === 401 ? "로그인 세션이 만료됐습니다." : "관리자 사용량 정보를 불러오지 못했습니다.");
      const payload = await response.json() as Summary;
      setSummary(payload);
      setBudgetInput(payload.monthly_budget_usd ?? "");
    } catch (cause) {
      setSummary(null);
      setError((cause as Error).message || "조회 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => { void load(); }, [load]);

  async function saveBudget(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingBudget(true);
    setBudgetMessage("");
    try {
      const { data, error: sessionError } = await db().auth.getSession();
      if (sessionError) throw sessionError;
      if (!data.session) throw new Error("관리자 로그인이 필요합니다.");
      const api = process.env.NEXT_PUBLIC_API_URL;
      if (!api) throw new Error("API 주소가 설정되지 않았습니다.");
      const response = await fetch(api.replace(/\/$/, "") + "/api/admin/ai-usage/budget", {
        method: "POST",
        headers: { Authorization: "Bearer " + data.session.access_token, "Content-Type": "application/json" },
        body: JSON.stringify({ monthly_budget_usd: budgetInput }),
      });
      if (response.status === 403) throw new Error("관리자 권한이 확인되지 않았습니다.");
      if (!response.ok) throw new Error("월간 전체 예산을 저장하지 못했습니다.");
      setBudgetMessage("월간 전체 AI 예산을 저장했습니다.");
      await load();
    } catch (cause) {
      setBudgetMessage((cause as Error).message || "예산 저장에 실패했습니다.");
    } finally {
      setSavingBudget(false);
    }
  }

  const budgetRatio = summary?.monthly_budget_usd && Number(summary.monthly_budget_usd) > 0
    ? Number(summary.estimated_cost_usd) / Number(summary.monthly_budget_usd) * 100
    : null;
  const budgetProgress = budgetRatio === null ? null : Math.min(100, budgetRatio);

  return (
    <main className={styles.shell}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>PAPERSIGNAL · ADMINISTRATION</p>
          <h1>AI 사용량 및 비용 관리</h1>
          <p>전체 서비스의 모델 호출량, 추정 비용과 월간 예산을 관리합니다.</p>
        </div>
        <Link className={styles.back} href="/">서비스로 돌아가기</Link>
      </header>

      <section className={styles.toolbar} aria-label="조회 조건">
        <label htmlFor="month">조회 월</label>
        <input id="month" type="month" value={month} onChange={event => setMonth(event.target.value)} />
        <button type="button" onClick={() => void load()} disabled={loading}>{loading ? "조회 중…" : "새로고침"}</button>
      </section>

      {error && <div className={forbidden ? styles.notice : styles.error} role="alert">{error}</div>}

      {summary && <>
        <section className={styles.cards} aria-label="전체 사용량 요약">
          <article className={styles.card}><span>월간 추정 비용</span><strong>{money(summary.estimated_cost_usd)}</strong><small>확인된 유료 사용분</small></article>
          <article className={styles.card}><span>월간 전체 예산</span><strong>{money(summary.monthly_budget_usd)}</strong><small>서버 관리자 설정</small></article>
          <article className={styles.card}><span>모델 호출 이벤트</span><strong>{count(summary.event_count)}</strong><small>성공 {count(summary.success_events)} · 실패 {count(summary.failed_events)}</small></article>
          <article className={styles.card}><span>성공률</span><strong>{summary.success_rate_percent === null ? "—" : summary.success_rate_percent.toFixed(1) + "%"}</strong><small>전체 모델 호출 기준</small></article>
          <article className={styles.card}><span>확인된 토큰</span><strong>{count(summary.total_tokens)}</strong><small>미확정 이벤트 {count(summary.token_incomplete_events)}</small></article>
          <article className={styles.card}><span>평균 응답 시간</span><strong>{summary.average_latency_ms === null ? "—" : count(summary.average_latency_ms) + " ms"}</strong><small>기록된 모델 시도 기준</small></article>
          <article className={styles.card}><span>비용 미확정 이벤트</span><strong>{count(summary.unknown_cost_events)}</strong><small>결제 등급·가격·토큰 미확인</small></article>
        </section>

        <section className={styles.panel}>
          <h2>서비스 전체 월간 AI 예산 설정</h2>
          <p className={styles.subtle}>관리자만 변경할 수 있는 전체 서비스 예산입니다. 사용자별·논문별 예산은 설정하지 않습니다.</p>
          <form className={styles.budgetForm} onSubmit={saveBudget}>
            <label htmlFor="admin-monthly-budget">월간 전체 예산 (USD)</label>
            <input id="admin-monthly-budget" type="number" min="0" max="1000000000" step="0.01" required value={budgetInput} onChange={event => setBudgetInput(event.target.value)} />
            <button type="submit" disabled={savingBudget || !budgetInput.trim()}>{savingBudget ? "저장 중…" : "전체 예산 저장"}</button>
          </form>
          {budgetMessage && <p className={styles.subtle} role="status">{budgetMessage}</p>}
        </section>

        <section className={styles.panel}>
          <div className={styles.panelTitle}><h2>월간 예산 상태</h2><strong>{budgetStatusLabel(summary.budget_status)}</strong></div>
          {budgetRatio !== null && <div className={styles.track} role="progressbar" aria-label="확인된 월간 예산 사용률" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(budgetProgress ?? 0)}><span style={{ width: budgetProgress + "%" }} /></div>}
          <p>{summary.monthly_budget_usd === null ? "월간 예산이 서버에 설정되지 않았습니다." : "확인된 비용 기준 " + (budgetRatio ?? 0).toFixed(1) + "% 사용"}</p>
          {!summary.cost_coverage_complete && <p className={styles.notice}>일부 이벤트의 비용이 미확정입니다. 표시된 비용은 전체 청구액이 아니며 예산 사용률도 하한값입니다.</p>}
          {summary.truncated && <p className={styles.notice}>조회 한도에 도달했습니다. 전체 월간 집계를 위해 서버 페이지네이션 한도를 확인해야 합니다.</p>}
        </section>

        <section className={styles.panel}>
          <h2>모델별 사용량 및 비용</h2>
          <div className={styles.tableWrap} tabIndex={0} aria-label="모델별 사용량 표"><table><thead><tr><th>제공사</th><th>모델</th><th>호출</th><th>성공</th><th>실패</th><th>토큰</th><th>평균 응답</th><th>비용 확인</th><th>미확정</th><th>추정 비용</th></tr></thead>
            <tbody>{summary.models.map(item => <tr key={item.provider + "-" + item.model}><th>{item.provider}</th><td>{item.model}</td><td>{count(item.event_count)}</td><td>{count(item.success_events)}</td><td>{count(item.failed_events)}</td><td>{count(item.total_tokens)}{item.token_usage_incomplete_events ? "†" : ""}</td><td>{item.average_latency_ms === null ? "—" : count(item.average_latency_ms) + " ms"}</td><td>{count(item.known_cost_events)}</td><td>{count(item.unknown_cost_events)}</td><td>{money(item.estimated_cost_usd)}</td></tr>)}</tbody>
          </table></div>
        </section>

        <section className={styles.panel}>
          <h2>사용자별 내부 운영 집계</h2>
          <p className={styles.subtle}>관리자 전용 식별자와 사용량입니다. 일반 사용자 화면과 API에는 제공하지 않습니다.</p>
          <div className={styles.tableWrap} tabIndex={0} aria-label="사용자별 내부 운영 집계 표"><table><thead><tr><th>사용자 ID</th><th>호출</th><th>비용 확인</th><th>미확정</th><th>추정 비용</th></tr></thead>
            <tbody>{summary.users.map(item => <tr key={item.user_id}><th><code>{item.user_id}</code></th><td>{item.event_count}</td><td>{item.known_cost_events}</td><td>{item.unknown_cost_events}</td><td>{money(item.estimated_cost_usd)}</td></tr>)}</tbody>
          </table></div>
        </section>
        <p className={styles.disclaimer}>{summary.notice}</p>
      </>}
      {!summary && !loading && !error && <p className={styles.subtle}>관리자 정보를 불러오고 있습니다.</p>}
    </main>
  );
}
