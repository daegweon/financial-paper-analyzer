import test from "node:test";
import assert from "node:assert/strict";
import { validateBrowserQaTarget } from "../lib/browser-qa-target.ts";

test("accepts only this project's feature preview domains", () => {
  const versioned = validateBrowserQaTarget("https://financial-paper-analyzer-2ysr7puck-daegweonai-9583.vercel.app");
  assert.equal(versioned.kind, "preview");
  assert.equal(versioned.hostname, "financial-paper-analyzer-2ysr7puck-daegweonai-9583.vercel.app");
  const alias = validateBrowserQaTarget("https://financial-paper-analyzer-git-feat-junior-abc123-daegweonai-9583.vercel.app");
  assert.equal(alias.kind, "preview");
});

test("allows only explicit localhost dev origin", () => {
  assert.equal(validateBrowserQaTarget("http://localhost:3000").kind, "local");
  assert.equal(validateBrowserQaTarget("http://127.0.0.1:3000").kind, "local");
  assert.throws(() => validateBrowserQaTarget("http://localhost:3100"), /only/);
});

test("refuses production, main aliases and unrelated Preview origins", () => {
  const unsafe = [
    "https://financial-paper-analyzer.vercel.app",
    "https://financial-paper-analyzer-daegweonai-9583.vercel.app",
    "https://financial-paper-analyzer-git-main-daegweonai-9583.vercel.app",
    "https://other-project-2ysr7puck-daegweonai-9583.vercel.app",
    "https://financial-paper-analyzer-2ysr7puck-daegweonai-9583.vercel.app.evil.example",
    "http://financial-paper-analyzer-2ysr7puck-daegweonai-9583.vercel.app",
    "https://localhost:3000",
  ];
  for (const target of unsafe) assert.throws(() => validateBrowserQaTarget(target), /only|never production/);
});

test("never accepts embedded user info, signed queries or storage tokens", () => {
  const origin = "https://financial-paper-analyzer-2ysr7puck-daegweonai-9583.vercel.app";
  for (const target of [origin + "?token=secret", origin + "/private", origin + "#pdf", origin.replace("https://", "https://u:p@")]) {
    assert.throws(() => validateBrowserQaTarget(target), /may not contain/);
  }
});

test("empty or malformed QA configuration fails instead of silently skipping", () => {
  assert.throws(() => validateBrowserQaTarget(""), /must be set/);
  assert.throws(() => validateBrowserQaTarget(undefined), /must be set/);
  assert.throws(() => validateBrowserQaTarget("not-a-url"), /valid URL/);
});
