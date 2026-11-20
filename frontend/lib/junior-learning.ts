/**
 * PaperSignal self-directed learning: sourced paper fragments stay distinct from
 * static education. No analysis is recomputed and no paper-specific facts are invented.
 */
import { juniorGuideSummary, screenPassedFindingCandidates } from "./junior-guide.ts";
import type { JuniorEvidence, JuniorGuideResult } from "./junior-guide.ts";
import { juniorRoleGuide } from "./junior-workflow.ts";
import type { JuniorRole } from "./junior-workflow.ts";

export type StudySource = JuniorGuideResult & {
  research_question_evidence?: JuniorEvidence[];
  methodology?: NonNullable<JuniorGuideResult["methodology"]> & { evidence?: JuniorEvidence[] };
};
export type StudyStepId = "question" | "method" | "evidence" | "practice";
export type StudyStep = {
  id: StudyStepId; title: string; task: string; extracted: string;
  sourcePage: number | null; sourceQuote: string; evidenceNeeded: boolean;
};
export type QuizQuestion = {
  id: string; question: string; options: [string, string, string]; correctIndex: number;
  explanation: string;
};
export type StudyProgress = { completed: StudyStepId[]; bestScore: number | null };
export const STUDY_STEP_IDS: StudyStepId[] = ["question", "method", "evidence", "practice"];
export const emptyStudyProgress = (): StudyProgress => ({ completed: [], bestScore: null });

function concise(value: unknown, max = 240) {
  if (typeof value !== "string") return "";
  const content = value.replace(/[\u0000-\u001F\u007F]+/g, " ").trim();
  return content.length > max ? content.slice(0, max - 1) + "…" : content;
}
function cited(list: JuniorEvidence[] | undefined): { page: number; quote: string } | null {
  if (!Array.isArray(list)) return null;
  const candidate = list.find((item) => item && Number.isSafeInteger(item.page) && item.page > 0 && concise(item.quote));
  return candidate ? { page: candidate.page, quote: concise(candidate.quote, 240) } : null;
}

export function buildStudySteps(source: StudySource, role: JuniorRole): StudyStep[] {
  const guide = juniorGuideSummary(source);
  const firstClaim = screenPassedFindingCandidates(source)[0];
  const questionEvidence = cited(source.research_question_evidence);
  const methodEvidence = cited(source.methodology?.evidence);
  const methodExtract = [
    guide.method.design && "연구 설계: " + guide.method.design,
    guide.method.sample && "표본: " + guide.method.sample,
    guide.method.period && "기간: " + guide.method.period,
  ].filter(Boolean).join(" · ");
  const roleGuide = juniorRoleGuide(role);
  return [
    { id: "question", title: "01 · 연구 질문 파악",
      task: "이 논문이 무엇을 검증하는지 한 문장으로 정리하고, 연구 대상을 구별하세요.",
      extracted: concise(guide.question), sourcePage: questionEvidence?.page ?? null,
      sourceQuote: questionEvidence?.quote ?? "", evidenceNeeded: true },
    { id: "method", title: "02 · 표본과 모형 이해",
      task: "사용한 데이터·기간·모형과 주요 가정을 원문에서 확인하세요.",
      extracted: concise(methodExtract), sourcePage: methodEvidence?.page ?? null,
      sourceQuote: methodEvidence?.quote ?? "", evidenceNeeded: true },
    { id: "evidence", title: "03 · 실증 결과 대조",
      task: "결과의 방향과 크기를 읽고, 인용 페이지에서 표 주석·유의성과 연구 한계를 확인하세요.",
      extracted: concise(firstClaim?.claim), sourcePage: firstClaim?.page ?? null,
      sourceQuote: concise(firstClaim?.quote), evidenceNeeded: true },
    { id: "practice", title: "04 · 내 직무에 연결",
      task: roleGuide.focus + " 연습 산출물: " + roleGuide.deliverable,
      extracted: "", sourcePage: null, sourceQuote: "", evidenceNeeded: false },
  ];
}

const ROLE_QUIZ: Record<JuniorRole, {
  question: string; options: [string, string, string]; correct: number; explanation: string;
}> = {
  wealth: {
    question: "자산관리·WM 업무에서 논문 결과를 고객 설명에 연결할 때 무엇을 우선하나요?",
    options: ["과거 평균 추정치를 모든 고객의 수익 전망으로 안내", "표본·상품·기간의 적합성과 연구 한계를 먼저 확인", "통계적으로 유의하면 투자 적합성이 자동 충족"],
    correct: 1, explanation: "고객별 적합성은 논문 평균 효과에서 곧바로 도출되지 않습니다. 대상과 조건을 먼저 검토해야 합니다.",
  },
  risk: {
    question: "리스크관리에서 새로운 위험 모형을 평가할 때 적절한 접근은?",
    options: ["변동성이 작아지면 꼬리위험 검증 생략", "단일 기간 적합도만 보고 운영에 즉시 적용", "스트레스 시나리오·표본 외 검증·가정을 함께 확인"],
    correct: 2, explanation: "모형 가정과 위기 기간의 성능, 표본 외 결과를 함께 점검해야 합니다.",
  },
  research: {
    question: "리서치·투자전략 담당자가 논문의 실증 결과를 검토할 때 우선해야 할 것은?",
    options: ["식별 전략·통제 변수·강건성 검증과 인용 근거 확인", "추정치의 부호만 보면 충분", "높은 상관계수를 인과효과로 단정"],
    correct: 0, explanation: "식별 전략과 원문 근거가 뒷받침하지 않으면 계수만으로 인과적 결론을 낼 수 없습니다.",
  },
  product: {
    question: "상품·기획 업무에서 논문을 서비스 아이디어로 연결할 때 어떤 기준이 맞나요?",
    options: ["유의한 논문이면 준법 심사 생략 가능", "논문 적용 대상과 제품 사용 조건을 비교하고 별도 검증을 설계", "논문 수익률을 확정 상품 성과로 표시"],
    correct: 1, explanation: "연구 결과는 제품 검증 가설로 사용하고, 적합성·규제·실사용 조건은 따로 확인해야 합니다.",
  },
  technology: {
    question: "개발·데이터 업무에서 논문 모형을 재현할 때 먼저 확인해야 할 것은?",
    options: ["입력값에 미래 정보를 포함해도 테스트 성능이 높으면 허용", "학습 자료가 많다면 데이터 정의는 생략", "데이터 빈도·전처리·훈련/검증 분리·정보 누수 여부"],
    correct: 2, explanation: "재현성과 평가 신뢰도는 입력 정의와 시간에 따른 데이터 분리 및 누수 점검에 달려 있습니다.",
  },
};

export function buildStudyQuiz(source: StudySource, role: JuniorRole): QuizQuestion[] {
  const firstClaim = screenPassedFindingCandidates(source)[0];
  const roleQuiz = ROLE_QUIZ[role];
  return [
    { id: "evidence", question: "원문 페이지 근거가 부족한 논문 분석 결과를 발견했다면?",
      options: ["AI 요약에서 반복되므로 사실로 확정", "근거 미확인으로 표시하고 원본 PDF에서 검증", "숫자를 그럴듯하게 보완"],
      correctIndex: 1, explanation: "근거가 없는 내용은 확인되지 않은 상태 그대로 두고, 원본 페이지와 원문 수치를 직접 대조해야 합니다." },
    { id: "significance", question: "논문의 계수가 통계적으로 유의하다고 보고될 때 올바른 해석은?",
      options: ["효과가 크고 경제적으로 중요하다는 뜻", "인과관계와 미래 수익을 보장", "검정 가정하에서 통계적 증거가 있으나 크기·인과는 별도 검토"],
      correctIndex: 2, explanation: "통계적 유의성은 효과의 크기, 경제적 유용성, 인과성 또는 미래 예측력을 보증하지 않습니다." },
    { id: "role", question: roleQuiz.question, options: roleQuiz.options,
      correctIndex: roleQuiz.correct, explanation: roleQuiz.explanation },
    firstClaim
      ? { id: "source", question: "이 논문의 1차 대조 통과 결과는 PDF " + firstClaim.page + "쪽에 연결되어 있습니다. 다음으로 무엇을 해야 하나요?",
        options: ["해당 페이지의 인용·표·모형 열·기간을 직접 대조", "페이지 번호가 있으므로 전문가 사실 검증이 완료된 것으로 판단", "다른 논문의 수치로 빈 내용을 채움"],
        correctIndex: 0, explanation: "인용 페이지 표기와 자동 1차 대조는 출발점입니다. 원본 페이지의 조건·수치·유의성 주석을 다시 읽어야 합니다." }
      : { id: "source", question: "이 논문에 1차 대조를 통과한 결과 근거가 없다면 어떻게 해야 하나요?",
        options: ["자동 분석 결과의 신뢰도를 높게 가정", "비슷한 논문의 수치를 가져와 완성", "검증된 근거가 없음을 밝히고 원문 확인을 요청"],
        correctIndex: 2, explanation: "확인되지 않은 결과를 채우거나 추측해서는 안 됩니다. 검증 가능한 근거가 확보될 때까지 결론을 보류합니다." },
  ];
}

export function gradeStudyQuiz(questions: QuizQuestion[], answers: Record<string, number>) {
  const answered = questions.filter((q) => Number.isInteger(answers[q.id]) && answers[q.id] >= 0 && answers[q.id] < q.options.length).length;
  const correct = questions.filter((q) => answers[q.id] === q.correctIndex).length;
  return { answered, correct, total: questions.length, complete: answered === questions.length };
}

const ROLE_KEYS: JuniorRole[] = ["wealth", "risk", "research", "product", "technology"];
const SAFE_ID = /^[A-Za-z0-9_-]{8,64}$/;

/** Only opaque account/paper identifiers are used. No paper text or private PDF URL is stored. */
export function studyStorageKey(userId: string, paperId: string, role: JuniorRole): string | null {
  if (!SAFE_ID.test(userId) || !SAFE_ID.test(paperId) || !ROLE_KEYS.includes(role)) return null;
  return "papersignal:learning:v1:" + userId + ":" + paperId + ":" + role;
}

export function parseStudyProgress(raw: string | null): StudyProgress {
  if (!raw || raw.length > 2000) return emptyStudyProgress();
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return emptyStudyProgress();
    const record = parsed as { version?: unknown; completed?: unknown; bestScore?: unknown };
    if (record.version !== 1) return emptyStudyProgress();
    const savedSteps: unknown[] = Array.isArray(record.completed) ? record.completed : [];
    const completed = STUDY_STEP_IDS.filter((id) => savedSteps.includes(id));
    const score = record.bestScore;
    return {
      completed,
      bestScore: typeof score === "number" && Number.isInteger(score) && score >= 0 && score <= 4 ? score : null,
    };
  } catch {
    return emptyStudyProgress();
  }
}
export function serializeStudyProgress(progress: StudyProgress): string {
  return JSON.stringify({ version: 1,
    completed: STUDY_STEP_IDS.filter((id) => progress.completed.includes(id)),
    bestScore: progress.bestScore });
}
