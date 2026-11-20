import test from "node:test";
import assert from "node:assert/strict";
import { explainPaperMethods, juniorRoleGuide, roleOptions, composeJuniorBrief, juniorBriefFilename } from "../lib/junior-workflow.ts";

const sourceFinding = (claim, page, quote, status = "screen_passed") => ({
  claim,
  evidence: [{ page, quote }],
  verification: {
    status, numeric_supported: true,
    direction_consistent: true, significance_supported: true,
    unsupported_numeric_tokens: [],
  },
});

test("model education triggers only on extracted methodology, not arbitrary summary", () => {
  const paper = { summary: "GARCH is mentioned in discussion", methodology: { design: "portfolio backtest" } };
  assert.deepEqual(explainPaperMethods(paper), []);
  const actual = { methodology: { design: "Time series", empirical_strategy: "GARCH-MIDAS" } };
  const lessons = explainPaperMethods(actual);
  assert.equal(lessons[0].title, "GARCH-MIDAS");
  assert.ok(!lessons.some((lesson) => lesson.id === "garch"));
  assert.ok(lessons[0].assumption.includes("시간 정렬"));
});

test("explains common market models without reinterpreting a paper's results", () => {
  const result = { methodology: { design: "CAPM and Fama-French 3-factor", empirical_strategy: "OLS regression" } };
  const lessons = explainPaperMethods(result);
  assert.deepEqual(lessons.map((x) => x.id), ["capm", "fama-french", "regression"]);
  assert.ok(lessons.every((lesson) => lesson.why && lesson.assumption && lesson.caution));
});

test("regression and DiD do not generate redundant generic lessons", () => {
  const lessons = explainPaperMethods({
    methodology: { design: "OLS regression", identification_strategy: "difference-in-differences" },
  });
  assert.ok(lessons.some((x) => x.id === "difference-in-differences"));
  assert.ok(!lessons.some((x) => x.id === "regression"));
});

test("returns empty method lessons for absent methodology instead of guessing", () => {
  assert.deepEqual(explainPaperMethods({}), []);
  assert.deepEqual(explainPaperMethods({ summary: "VAR, GARCH and CAPM" }), []);
  assert.deepEqual(explainPaperMethods({ methodology: { design: "qualitative interview" } }), []);
});

test("all five role categories have meaningful distinct learning questions", () => {
  assert.equal(roleOptions.length, 5);
  const guides = roleOptions.map(({ key }) => juniorRoleGuide(key));
  assert.ok(guides.every((guide) => guide.questions.length === 3 && guide.deliverable && guide.focus));
  assert.notDeepEqual(guides[0].questions, guides[1].questions);
  assert.notDeepEqual(guides[1].questions, guides[4].questions);
});

test("briefing preserves original sourced numbers and page quote and never promotes review status", () => {
  const result = {
    research_question: "Do changes in liquidity explain stock returns?",
    methodology: { design: "Panel regression", sample: "150 firms", period: "2015-2022", empirical_strategy: "OLS" },
    findings: [
      sourceFinding("A one-point increase is associated with 0.8% return.", 12, "Estimate 0.8%, p = 0.04"),
      sourceFinding("This result is unverified and should not be reported", 15, "Unmatched reference", "review"),
    ],
    limitations: [{ description: "Only observations from one country" }],
    bibliographic: { doi: "10.1000/test-paper" },
  };
  const brief = composeJuniorBrief(result, "Liquidity paper", "risk");
  assert.match(brief, /A one-point increase is associated with 0.8% return\./);
  assert.match(brief, /PDF p\.12/);
  assert.match(brief, /Estimate 0\.8%, p = 0\.04/);
  assert.doesNotMatch(brief, /This result is unverified and should not be reported/);
  assert.match(brief, /추가 1건은 검토가 필요/);
  assert.match(brief, /Only observations from one country/);
  assert.match(brief, /DOI: 10.1000\/test-paper/);
  assert.match(brief, /리스크관리 업무 검토 질문/);
  assert.doesNotMatch(brief, /확정 수익/);
});

test("no findings, no question, and no methods produces candid missing-data briefing", () => {
  const brief = composeJuniorBrief({}, "Unknown");
  assert.match(brief, /원문 근거가 확인된 연구 질문 없음/);
  assert.match(brief, /검증 가능한 방법론 정보 없음/);
  assert.match(brief, /표시할 근거 대조 통과 결과 없음/);
  assert.match(brief, /한계 정보 미확인/);
  assert.doesNotMatch(brief, /PDF p\.\d/);
});

test("briefing only includes first two screened findings but does not label third as review failure", () => {
  const result = { findings: [
    sourceFinding("One", 1, "Quote one"),
    sourceFinding("Two", 2, "Quote two"),
    sourceFinding("Three", 3, "Quote three"),
  ] };
  const brief = composeJuniorBrief(result, "3 findings", "research");
  assert.match(brief, /One/);
  assert.match(brief, /Two/);
  assert.doesNotMatch(brief, /Quote three/);
  assert.doesNotMatch(brief, /추가 \d+건은 검토가 필요/);
});

test("roles only modify generic study questions, never source findings", () => {
  const result = { findings: [sourceFinding("Market beta is correlated with returns", 6, "The beta relation is significant")] };
  const wm = composeJuniorBrief(result, "Paper", "wealth");
  const engineer = composeJuniorBrief(result, "Paper", "technology");
  assert.match(wm, /Market beta is correlated with returns/);
  assert.match(engineer, /Market beta is correlated with returns/);
  assert.match(wm, /자산관리·WM 업무 검토 질문/);
  assert.match(engineer, /개발·데이터 업무 검토 질문/);
  assert.notEqual(wm, engineer);
});

test("never copies known false direction or significance findings", () => {
  const result = { findings: [
    { ...sourceFinding("Wrong significance", 10, "p = 0.50"), verification: { status: "screen_passed", numeric_supported: true, significance_supported: false } },
    { ...sourceFinding("Wrong sign", 11, "coefficient -0.23"), verification: { status: "screen_passed", numeric_supported: true, direction_consistent: false } },
  ] };
  const brief = composeJuniorBrief(result, "Paper");
  assert.doesNotMatch(brief, /Wrong significance|Wrong sign/);
  assert.match(brief, /검토가 필요/);
});

test("brief does not introduce any financial advice or generated numeric prediction", () => {
  const brief = composeJuniorBrief({
    research_question: "Can forecasting predict stock returns?",
    methodology: { design: "LASSO", empirical_strategy: "Cross-validation" },
  }, "Forecast");
  assert.ok(brief.includes("준법 심사 결과가 아닙니다"));
  assert.ok(brief.includes("미래 수익·투자 성과를 보장하지 않습니다"));
  assert.doesNotMatch(brief, /\d+%/);
});


test("briefing preserves source quote line breaks without rewriting the citation", () => {
  const excerpt = "Regression table:\n0.8% estimate\np = 0.04";
  const brief = composeJuniorBrief({
    findings: [sourceFinding("The estimated relation was 0.8%.", 12, excerpt)],
  }, "Paper");
  assert.ok(brief.includes(excerpt));
});

test("local export filenames reject path and control characters", () => {
  const filename = juniorBriefFilename("../../risky\\name:2026?<>|.pdf");
  assert.ok(filename.endsWith("-papersignal-junior-brief.txt"));
  assert.doesNotMatch(filename, /[\/\\:*?"<>|\u0000-\u001F\u007F]/);
  assert.ok(filename.length < 100);
  assert.equal(juniorBriefFilename("...."), "paper-papersignal-junior-brief.txt");
});
