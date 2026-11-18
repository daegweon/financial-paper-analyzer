import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
const progress = JSON.parse(readFileSync(new URL("../docs/PROJECT_PROGRESS.json", import.meta.url), "utf8"));
assert.equal(progress.schema_version, 1);
assert.equal(progress.source_of_truth, "docs/PROJECT_PROGRESS.json");
assert.match(progress.updated_at, /^\d{4}-\d{2}-\d{2}$/);
assert.match(progress.release_candidate.branch, /^release\/beta-candidate-/);
assert.equal(progress.release_candidate.review_state, "draft");
assert.match(progress.release_candidate.last_independently_verified_sha, /^[0-9a-f]{40}$/);
assert.ok(Array.isArray(progress.workstreams) && progress.workstreams.length >= 5);
let weights = 0, earned = 0;
const ids = new Set();
for (const w of progress.workstreams) {
  assert.ok(!ids.has(w.id), "Duplicate workstream");
  ids.add(w.id);
  assert.ok(Number.isInteger(w.weight) && w.weight > 0);
  assert.ok(Number.isInteger(w.earned) && w.earned >= 0 && w.earned <= w.weight);
  assert.ok(Array.isArray(w.evidence) && w.evidence.length);
  assert.ok(typeof w.remaining === "string" && w.remaining.trim());
  weights += w.weight;
  earned += w.earned;
}
assert.equal(weights, 100, "Weights must add to 100");
assert.equal(earned, progress.overall_percent, "Displayed percentage must match earned points");
assert.ok(Array.isArray(progress.release_gates) && progress.release_gates.length >= 8);
let passed = 0;
const gateIds = new Set();
for (const gate of progress.release_gates) {
  assert.ok(!gateIds.has(gate.id), "Duplicate release gate");
  gateIds.add(gate.id);
  assert.ok(["passed", "pending", "blocked"].includes(gate.status));
  if (gate.status === "passed") {
    assert.ok(/^https:\/\/github\.com\/daegweon\/financial-paper-analyzer\//.test(gate.evidence),
      "Passed release gates require a reproducible GitHub evidence URL");
    passed++;
  } else {
    assert.equal(gate.evidence, null, "Unverified gate must not report a PASS link");
  }
}
assert.ok(progress.response_protocol.includes("overall_percent"));
console.log("PROJECT_PROGRESS_VALIDATED " + earned + "% engineering, " +
  passed + "/" + progress.release_gates.length + " release gates");
