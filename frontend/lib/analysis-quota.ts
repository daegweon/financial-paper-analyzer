export const DAILY_ANALYSIS_LIMIT = 5;
export const ACTIVE_ANALYSIS_LIMIT = 2;
export const ANALYSIS_QUOTA_WINDOW_MS = 24 * 60 * 60 * 1000;

export type AnalysisQuotaJob = {
  status?: string;
  created_at?: string | null;
};

export type AnalysisQuotaUsage = {
  dailyUsed: number;
  activeCount: number;
  dailyRemaining: number;
  activeRemaining: number;
};

export function getAnalysisQuotaUsage(
  jobs: readonly AnalysisQuotaJob[],
  nowMs = Date.now(),
): AnalysisQuotaUsage {
  const cutoff = nowMs - ANALYSIS_QUOTA_WINDOW_MS;
  let dailyUsed = 0;
  let activeCount = 0;
  for (const job of jobs) {
    const created = typeof job.created_at === "string" ? Date.parse(job.created_at) : NaN;
    if (Number.isFinite(created) && created >= cutoff && created <= nowMs) dailyUsed++;
    if (job.status === "queued" || job.status === "processing") activeCount++;
  }
  return {
    dailyUsed,
    activeCount,
    dailyRemaining: Math.max(0, DAILY_ANALYSIS_LIMIT - dailyUsed),
    activeRemaining: Math.max(0, ACTIVE_ANALYSIS_LIMIT - activeCount),
  };
}
