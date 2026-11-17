import test from "node:test";
import assert from "node:assert/strict";
import {
  analysisConnectionError,
  startAnalysisJob,
  waitForAnalysisJob,
} from "../lib/analysis-job.ts";

const response = (payload, status = 200, headers = {}) =>
  new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json", ...headers } });
const noDelay = async () => {};

test("starts exactly one durable job without resubmitting the POST", async () => {
  let calls = 0;
  const id = await startAnalysisJob({
    url: "/api/analyze/paper-a", token: "test-token",
    fetcher: async (_url, init) => {
      calls++;
      assert.equal(init.method, "POST");
      assert.equal(init.headers.Authorization, "Bearer test-token");
      return response({ job_id: "job-1", status: "queued" }, 202);
    },
  });
  assert.equal(id, "job-1");
  assert.equal(calls, 1);
});

test("transient POST failure does not automatically create a duplicate job", async () => {
  let calls = 0;
  await assert.rejects(
    startAnalysisJob({
      url: "/api/analyze/paper-a", token: "test-token",
      fetcher: async () => { calls++; return response({ detail: "temporarily down" }, 503); },
    }),
    /기존 작업이 등록됐을 수 있으니/,
  );
  assert.equal(calls, 1);
});

test("a network failure is explained instead of showing Failed to fetch", async () => {
  await assert.rejects(
    startAnalysisJob({
      url: "/api/analyze/paper-a", token: "test-token",
      fetcher: async () => { throw new TypeError("Failed to fetch"); },
    }),
    /분석 서버에 연결하지 못했습니다/,
  );
  assert.doesNotMatch(analysisConnectionError(), /Failed to fetch/);
});

test("polls through a network interruption and reports completion", async () => {
  let calls = 0;
  const states = [];
  const result = await waitForAnalysisJob({
    url: "/status", token: "test-token",
    onProgress: (value) => states.push(value),
    fetcher: async (_url, init) => {
      calls++;
      assert.equal(init.method, "GET");
      assert.equal(init.cache, "no-store");
      if (calls === 1) throw new TypeError("network offline");
      if (calls === 2) return response({ status: "processing", stage: "gemini_analysis" });
      return response({ status: "completed", stage: "completed" });
    },
    sleep: noDelay,
  });
  assert.equal(result.status, "completed");
  assert.equal(calls, 3);
  assert.ok(states.some((value) => value.includes("끊겼습니다")));
  assert.ok(states.some((value) => value.includes("Gemini AI")));
});

test("retries 429 and 503 with bounded Retry-After, without resubmitting", async () => {
  let calls = 0;
  const waits = [];
  const result = await waitForAnalysisJob({
    url: "/status", token: "test-token", onProgress: () => {},
    fetcher: async () => {
      calls++;
      if (calls === 1) return response({}, 429, { "retry-after": "200" });
      if (calls === 2) return response({}, 503);
      return response({ status: "completed", stage: "completed" });
    },
    sleep: async (ms) => waits.push(ms),
  });
  assert.equal(result.status, "completed");
  assert.equal(calls, 3);
  assert.deepEqual(waits, [15000, 3000]);
});

test("surfaces a failed job without retrying the analysis", async () => {
  await assert.rejects(
    waitForAnalysisJob({
      url: "/status", token: "token", onProgress: () => {},
      fetcher: async () => response({ status: "failed", stage: "failed", error: "모델 응답 불완전" }),
      sleep: noDelay,
    }),
    /모델 응답 불완전/,
  );
});

test("rejects nontransient authentication errors promptly", async () => {
  let calls = 0;
  await assert.rejects(
    waitForAnalysisJob({
      url: "/status", token: "token", onProgress: () => {},
      fetcher: async () => { calls++; return response({}, 401); },
      sleep: noDelay,
    }),
    /로그인 세션/,
  );
  assert.equal(calls, 1);
});

test("gives up after bounded consecutive transport failures", async () => {
  let calls = 0;
  await assert.rejects(
    waitForAnalysisJob({
      url: "/status", token: "token", onProgress: () => {},
      fetcher: async () => { calls++; throw new Error("offline"); },
      sleep: noDelay,
      maxConsecutiveErrors: 3,
      maxPolls: 50,
    }),
    /연결하지 못했습니다/,
  );
  assert.equal(calls, 3);
});

test("does not mistake an empty successful response for completion", async () => {
  await assert.rejects(
    waitForAnalysisJob({
      url: "/status", token: "token", onProgress: () => {},
      fetcher: async () => response(null),
      sleep: noDelay,
      maxPolls: 1,
    }),
    /응답 형식이 올바르지 않습니다/,
  );
});

test("keeps unfinished jobs in a recoverable state after poll timeout", async () => {
  await assert.rejects(
    waitForAnalysisJob({
      url: "/status", token: "token", onProgress: () => {},
      fetcher: async () => response({ status: "processing", stage: "gemini_analysis" }),
      sleep: noDelay,
      maxPolls: 2,
    }),
    /논문을 다시 열어 결과를 확인/,
  );
});
