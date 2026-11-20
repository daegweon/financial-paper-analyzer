import test from "node:test";
import assert from "node:assert/strict";
import {
  getAnalysisQuotaUsage,
  DAILY_ANALYSIS_LIMIT,
  ACTIVE_ANALYSIS_LIMIT,
  ANALYSIS_QUOTA_WINDOW_MS,
} from "../lib/analysis-quota.ts";

const now = Date.parse("2026-11-19T12:00:00.000Z");

test("counts only jobs created in the rolling 24-hour window", () => {
  const usage = getAnalysisQuotaUsage([
    {status:"completed",created_at:new Date(now - 1000).toISOString()},
    {status:"failed",created_at:new Date(now - ANALYSIS_QUOTA_WINDOW_MS).toISOString()},
    {status:"completed",created_at:new Date(now - ANALYSIS_QUOTA_WINDOW_MS - 1).toISOString()},
    {status:"queued",created_at:new Date(now + 1000).toISOString()},
    {status:"completed",created_at:"invalid"},
  ], now);
  assert.equal(usage.dailyUsed, 2);
});

test("counts queued and processing as active regardless of creation age", () => {
  const usage = getAnalysisQuotaUsage([
    {status:"queued",created_at:new Date(now - ANALYSIS_QUOTA_WINDOW_MS * 2).toISOString()},
    {status:"processing",created_at:new Date(now - 1000).toISOString()},
    {status:"completed",created_at:new Date(now - 1000).toISOString()},
  ], now);
  assert.equal(usage.activeCount, 2);
});

test("never displays negative remaining quota", () => {
  const usage = getAnalysisQuotaUsage(Array.from({length:9},(_,i)=>({
    status:i<3?"processing":"completed",
    created_at:new Date(now-i*1000).toISOString(),
  })),now);
  assert.equal(usage.dailyUsed,9);
  assert.equal(usage.activeCount,3);
  assert.equal(usage.dailyRemaining,0);
  assert.equal(usage.activeRemaining,0);
});

test("exposes the same policy limits as the server queue RPC", () => {
  assert.equal(DAILY_ANALYSIS_LIMIT,5);
  assert.equal(ACTIVE_ANALYSIS_LIMIT,2);
});
