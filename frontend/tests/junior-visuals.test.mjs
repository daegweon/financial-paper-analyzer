import test from "node:test";
import assert from "node:assert/strict";
import { buildVisualReadingCards } from "../lib/junior-visuals.ts";

const evidence = [{ page: 12, quote: "Table 3 reports coefficient 0.24." }];

test("only explicit references make cards; table and chart are distinguished", () => {
  const cards = buildVisualReadingCards({ findings: [
    { claim: "no reference", evidence },
    { table_reference: "Table 3", evidence },
    { table_reference: "Figure 2", evidence },
    { table_reference: "Fig. 9", evidence },
  ] });
  assert.equal(cards.length, 3);
  assert.equal(cards[0].kind, "table");
  assert.equal(cards[2].kind, "chart");
  assert.equal(cards[1].kind, "chart");
  assert.equal(cards[0].sourcePage, 12);
});

test("extracted fields are preserved without extrapolating values", () => {
  const [c] = buildVisualReadingCards({ findings: [{
    table_reference: "Table 5", model_or_column: "Model (3)", claim: "Association",
    estimate: "0.24", direction: "positive", statistical_significance: "p < 0.05", evidence,
  }] });
  assert.equal(c.column, "Model (3)");
  assert.equal(c.estimate, "0.24");
  assert.equal(c.significance, "p < 0.05");
  assert.equal(c.screening, "review_required");
});

test("automatic pass label requires conservative verification criteria", () => {
  const verification = { status: "screen_passed", numeric_supported: true,
    direction_consistent: true, significance_supported: true, unsupported_numeric_tokens: [] };
  const f = { table_reference: "Table 4", verification, evidence };
  assert.equal(buildVisualReadingCards({ findings: [f] })[0].screening, "screen_passed");
  assert.equal(buildVisualReadingCards({ findings: [{
    ...f, verification: { ...verification, significance_supported: false },
  }] })[0].screening, "review_required");
  assert.equal(buildVisualReadingCards({ findings: [{
    ...f, verification: { ...verification, unsupported_numeric_tokens: ["99"] },
  }] })[0].screening, "review_required");
});

test("only positive cited pages with nonempty quotes are usable", () => {
  const [bad] = buildVisualReadingCards({ findings: [{
    table_reference: "Figure 1", evidence: [{ page: 0, quote: "Invalid" }, { page: 9, quote: " " }],
  }] });
  assert.equal(bad.sourcePage, null);
  const [good] = buildVisualReadingCards({ findings: [{
    table_reference: "Figure 1", evidence: [{ page: -3, quote: "Bad" }, { page: 18, quote: "Source excerpt" }],
  }] });
  assert.equal(good.sourcePage, 18);
  assert.equal(good.sourceQuote, "Source excerpt");
});

test("legend reference cannot replace the main citation", () => {
  const [c] = buildVisualReadingCards({ findings: [{
    table_reference: "Table 6", significance_legend_evidence: [{ page: 20, quote: "* denotes 10%" }],
  }] });
  assert.equal(c.sourcePage, null);
  assert.equal(c.legendPage, 20);
});

test("deduplication only removes identical reference, column and claim", () => {
  const f = { table_reference: "Table 1", model_or_column: "A", claim: "one", evidence };
  assert.equal(buildVisualReadingCards({ findings: [f, f, { ...f, claim: "two" }] }).length, 2);
});

test("missing records do not create images or invented content; maximum count is bounded", () => {
  assert.deepEqual(buildVisualReadingCards(null), []);
  assert.deepEqual(buildVisualReadingCards({ findings: [{ claim: "No table" }] }), []);
  const input = Array.from({ length: 20 }, (_, i) => ({ table_reference: "Table " + i }));
  assert.equal(buildVisualReadingCards({ findings: input }).length, 6);
  assert.equal(buildVisualReadingCards({ findings: input }, 100).length, 10);
  assert.equal(buildVisualReadingCards({ findings: input }, 0).length, 0);
});

test("large and markup-like source values are capped as ordinary text", () => {
  const [c] = buildVisualReadingCards({ findings: [{
    table_reference: "Table 3", claim: "<script>alert(1)</script>" + "x".repeat(800),
    evidence: [{ page: 2, quote: "a".repeat(500) }],
  }] });
  assert.ok(c.claim.length <= 550);
  assert.ok(c.sourceQuote.length <= 300);
  assert.ok(c.claim.includes("<script>"));
});
