import test from "node:test";
import assert from "node:assert/strict";
import { MAX_PDF_BYTES, betaGuideStorageKey, isAcceptedPdf, uploadFailureMessage } from "../lib/beta-ux.ts";

test("accepts PDF only with correct extension, signature and size", () => {
  assert.equal(isAcceptedPdf("Research.PDF", 1000, "%PDF-"), true);
  assert.equal(isAcceptedPdf("a.pdf", MAX_PDF_BYTES, "%PDF-"), true);
  assert.equal(isAcceptedPdf("a.pdf", MAX_PDF_BYTES + 1, "%PDF-"), false);
  assert.equal(isAcceptedPdf("a.pdf", 4, "%PDF-"), false);
  assert.equal(isAcceptedPdf("a.txt", 100, "%PDF-"), false);
  assert.equal(isAcceptedPdf("a.pdf", 200, "<html"), false);
});
test("uncertain metadata registration asks for library check, not blind retry", () => {
  const msg = uploadFailureMessage("metadata", new Error("Failed to fetch https://private?token=secret"));
  assert.match(msg, /목록|새로고침/);
  assert.match(msg, /자동 재시도하지/);
  assert.doesNotMatch(msg, /private|token|secret|Failed to fetch/);
});
test("storage transport error provides actionable guidance without raw exception", () => {
  const msg = uploadFailureMessage("storage", new TypeError("Failed to fetch jwt=secret"));
  assert.match(msg, /로그인|네트워크/);
  assert.doesNotMatch(msg, /jwt=secret|Failed to fetch/);
});
test("authentication and file-size errors are safely mapped", () => {
  assert.match(uploadFailureMessage("storage", { statusCode: 401 }), /다시 로그인/);
  assert.match(uploadFailureMessage("storage", { status: 413 }), /30MB/);
  assert.match(uploadFailureMessage("validation", {}), /다시 선택/);
});
test("provider messages and signed URLs never echo into upload errors", () => {
  const err = { message: "https://x.supabase.co/storage?token=private_access_token", code: "ServerError" };
  for (const stage of ["storage", "metadata", "validation"]) {
    assert.doesNotMatch(uploadFailureMessage(stage, err), /supabase|token|private_access_token|ServerError/);
  }
});
test("welcome state is keyed only by validated opaque account ID", () => {
  const id = "123e4567-e89b-42d3-a456-426614174000";
  assert.equal(betaGuideStorageKey(id), "papersignal:beta-guide:v1:" + id);
  assert.equal(betaGuideStorageKey(""), null);
  assert.equal(betaGuideStorageKey("../secret"), null);
  assert.equal(betaGuideStorageKey("x".repeat(90)), null);
});
