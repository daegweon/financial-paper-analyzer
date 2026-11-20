import test from "node:test";
import assert from "node:assert/strict";
import { juniorGuideSummary, screenPassedFindingCandidates, suggestedJuniorTerms } from "../lib/junior-guide.ts";

function finding(claim, status = "screen_passed", evidence = [{ page: 7, quote: "Reported result" }]) {
  return { claim, verification: { status, numeric_supported: true, significance_supported: true, direction_consistent: true }, evidence };
}

test("junior guide keeps actual extracted question and methodology without inventing a conclusion", () => {
  const result = {
    research_question: "Does liquidity explain returns?",
    summary: "The paper studies liquidity risk.",
    methodology: { design: "Panel regression", sample: "100 firms", period: "2010-2020", empirical_strategy: "OLS" },
    findings: [finding("Liquidity is related to returns.")],
  };
  const guide = juniorGuideSummary(result);
  assert.equal(guide.question, result.research_question);
  assert.equal(guide.summary, result.summary);
  assert.equal(guide.method.design, "Panel regression");
  assert.equal(guide.method.sample, "100 firms");
  assert.equal(guide.method.period, "2010-2020");
  assert.equal(guide.findings[0].claim, "Liquidity is related to returns.");
  assert.equal(guide.findings[0].page, 7);
});

test("no paper result yields explicit absence rather than fabricated beginner text", () => {
  const guide = juniorGuideSummary({});
  assert.equal(guide.question, null);
  assert.equal(guide.summary, null);
  assert.deepEqual(guide.findings, []);
  assert.equal(guide.reviewNeededFindingCount, 0);
  assert.deepEqual(guide.limitations, []);
});

test("only automatically screen-passed claims with page-level quoted evidence can appear", () => {
  const result = {
    findings: [
      finding("Supported with citation"),
      finding("Requires researcher review", "review"),
      finding("No source citation", "screen_passed", []),
      { claim: "Unsupported sign", verification: { status: "screen_passed", direction_consistent: false }, evidence: [{ page: 6, quote: "Quote" }] },
      { claim: "Unsupported numeric", verification: { status: "screen_passed", numeric_supported: false }, evidence: [{ page: 6, quote: "Quote" }] },
      { claim: "Suspicious significance", verification: { status: "screen_passed", significance_supported: false }, evidence: [{ page: 6, quote: "Quote" }] },
      { claim: "Unmatched digit", verification: { status: "screen_passed", unsupported_numeric_tokens: ["6.0"] }, evidence: [{ page: 6, quote: "Quote" }] },
    ],
  };
  const guide = juniorGuideSummary(result);
  assert.deepEqual(guide.findings.map((x) => x.claim), ["Supported with citation"]);
  assert.equal(guide.reviewNeededFindingCount, 6);
});

test("does not mistake empty citation or zero page for source evidence", () => {
  const x = { findings: [
    finding("Empty quote", "screen_passed", [{ page: 7, quote: " " }]),
    finding("Invalid page", "screen_passed", [{ page: 0, quote: "A" }]),
    finding("Valid", "screen_passed", [{ page: 3, quote: "yes" }]),
  ] };
  assert.deepEqual(screenPassedFindingCandidates(x).map((v) => v.claim), ["Valid"]);
});

test("first three displayed findings do not inflate needs-review count", () => {
  const result = { findings: Array.from({ length: 5 }, (_, i) => finding("Finding " + i)) };
  const guide = juniorGuideSummary(result);
  assert.equal(guide.findings.length, 3);
  assert.equal(guide.additionalScreenedFindingsCount, 2);
  assert.equal(guide.reviewNeededFindingCount, 0);
});

test("term explanations are generic education, only triggered by existing extracted text", () => {
  const result = { methodology: { design: "CAPM and GARCH regression with ESG scores" } };
  const terms = suggestedJuniorTerms(result);
  assert.ok(terms.some((x) => x.label === "CAPM"));
  assert.ok(terms.some((x) => x.label === "GARCH"));
  assert.ok(terms.some((x) => x.label === "ESG"));
  assert.ok(terms.some((x) => x.label === "회귀분석"));
  assert.ok(terms.every((x) => x.meaning && x.check));
  assert.equal(suggestedJuniorTerms({ research_question: "Unfamiliar unrelated question" }).length, 0);
});

test("paper limitations are extracted verbatim and not replaced by generic risks", () => {
  const result = { limitations: [{ description: "Single-country sample" }, { description: "Short time span" }] };
  assert.deepEqual(juniorGuideSummary(result).limitations, ["Single-country sample", "Short time span"]);
});
