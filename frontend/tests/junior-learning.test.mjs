import test from "node:test";
import assert from "node:assert/strict";
import { buildStudyQuiz, buildStudySteps, emptyStudyProgress, gradeStudyQuiz, parseStudyProgress, serializeStudyProgress, studyStorageKey } from "../lib/junior-learning.ts";
import { roleOptions } from "../lib/junior-workflow.ts";

const sourced = (claim, page, quote) => ({
  claim,
  evidence: [{ page, quote }],
  verification: {
    status: "screen_passed", numeric_supported: true,
    direction_consistent: true, significance_supported: true,
    unsupported_numeric_tokens: [],
  },
});

test("all five role options produce four distinct study stages and quizzes", () => {
  for (const { key } of roleOptions) {
    const stages = buildStudySteps({}, key);
    assert.deepEqual(stages.map((s) => s.id), ["question", "method", "evidence", "practice"]);
    assert.ok(stages.every((s) => s.title && s.task));
    const quiz = buildStudyQuiz({}, key);
    assert.equal(quiz.length, 4);
    assert.ok(quiz.every((q) => q.options.length === 3 && q.correctIndex >= 0 && q.correctIndex < 3 && q.explanation));
  }
});

test("role changes learning practice and quiz but not paper-derived source", () => {
  const input = { research_question: "Are returns linked to factor exposures?" };
  const wm = buildStudySteps(input, "wealth");
  const tech = buildStudySteps(input, "technology");
  assert.equal(wm[0].extracted, tech[0].extracted);
  assert.notEqual(wm[3].task, tech[3].task);
  assert.notEqual(buildStudyQuiz(input, "wealth")[2].question, buildStudyQuiz(input, "technology")[2].question);
});

test("only valid evidence with a nonblank quoted excerpt yields a source link", () => {
  const src = {
    research_question: "Does market beta matter?",
    research_question_evidence: [{ page: 0, quote: "bad" }, { page: 4, quote: " Market beta is tested " }],
    methodology: { design: "panel regression", evidence: [{ page: 9, quote: " " }] },
    findings: [sourced("Positive relation", 15, " coefficient 0.4 ")],
  };
  const stages = buildStudySteps(src, "research");
  assert.equal(stages[0].sourcePage, 4);
  assert.equal(stages[1].sourcePage, null);
  assert.equal(stages[2].sourcePage, 15);
  assert.equal(stages[3].sourcePage, null);
  assert.match(stages[2].sourceQuote, /coefficient/);
});

test("unverified findings cannot be promoted to a sourced study stage", () => {
  const input = { findings: [
    { ...sourced("Unverified", 99, "guess"), verification: { status: "review_required" } },
  ] };
  assert.equal(buildStudySteps(input, "wealth")[2].extracted, "");
  assert.equal(buildStudySteps(input, "wealth")[2].sourcePage, null);
  assert.match(buildStudyQuiz(input, "wealth")[3].question, /없다면/);
});

test("citation quiz follows existing passed evidence page without inventing numbers", () => {
  const q = buildStudyQuiz({ findings: [sourced("Paper claim", 17, "quote")] }, "risk")[3];
  assert.match(q.question, /17쪽/);
  assert.equal(q.correctIndex, 0);
  assert.doesNotMatch(JSON.stringify(q), /"estimate"/);
});

test("quiz scoring tracks unanswered, wrong and correct values", () => {
  const questions = buildStudyQuiz({}, "wealth");
  assert.deepEqual(gradeStudyQuiz(questions, {}), { answered: 0, correct: 0, total: 4, complete: false });
  const correct = Object.fromEntries(questions.map((q) => [q.id, q.correctIndex]));
  assert.deepEqual(gradeStudyQuiz(questions, correct), { answered: 4, correct: 4, total: 4, complete: true });
  const wrong = { ...correct, role: (correct.role + 1) % 3 };
  assert.equal(gradeStudyQuiz(questions, wrong).correct, 3);
  assert.equal(gradeStudyQuiz(questions, { ...correct, role: 9 }).complete, false);
});

test("progress keys are scoped to account, paper and role; invalid identifiers are rejected", () => {
  const uid = "123e4567-e89b-42d3-a456-426614174000";
  const paper = "123e4567-e89b-42d3-a456-426614174001";
  const a = studyStorageKey(uid, paper, "wealth");
  assert.ok(a?.includes("learning:v1:"));
  assert.notEqual(a, studyStorageKey(uid, paper, "risk"));
  assert.notEqual(a, studyStorageKey(uid, "123e4567-e89b-42d3-a456-426614174002", "wealth"));
  assert.equal(studyStorageKey("../", paper, "wealth"), null);
  assert.equal(studyStorageKey(uid, paper, "made-up"), null);
});

test("serialized progress contains no paper text or auth tokens and round trips", () => {
  const progress = { completed: ["question", "evidence"], bestScore: 3 };
  const raw = serializeStudyProgress(progress);
  assert.deepEqual(parseStudyProgress(raw), progress);
  assert.equal(raw.includes("sourceQuote"), false);
  assert.equal(raw.includes("token"), false);
});

test("malformed or incompatible stored progress fails closed", () => {
  assert.deepEqual(parseStudyProgress(null), emptyStudyProgress());
  assert.deepEqual(parseStudyProgress("{corrupt"), emptyStudyProgress());
  assert.deepEqual(parseStudyProgress(JSON.stringify({ version: 99, completed: ["question"] })), emptyStudyProgress());
  assert.deepEqual(parseStudyProgress("x".repeat(3000)), emptyStudyProgress());
});

test("persisted progress drops unknown and repeated stages or invalid scores", () => {
  const state = parseStudyProgress(JSON.stringify({ version: 1,
    completed: ["method", "hacked", "method", "question"],
    bestScore: 10 }));
  assert.deepEqual(state.completed, ["question", "method"]);
  assert.equal(state.bestScore, null);
});

test("method data is shown as an extract, never filled by a guess", () => {
  const m = buildStudySteps({ methodology: { design: "time series", sample: "300 observations", period: "2010-2020" } }, "risk");
  assert.match(m[1].extracted, /300 observations/);
  assert.equal(m[1].sourcePage, null);
  assert.equal(buildStudySteps({}, "risk")[1].extracted, "");
});

test("user-provided text is bounded; quiz explanations are static guidance", () => {
  const result = { research_question: "x".repeat(800), findings: [sourced("<script>evil</script>", 1, "Q")] };
  const stages = buildStudySteps(result, "wealth");
  assert.ok(stages[0].extracted.length <= 240);
  assert.ok(stages[2].extracted.includes("<script>"));
  assert.ok(buildStudyQuiz(result, "wealth").every((q) => q.explanation.length > 5));
});
