/**
 * Junior role learning prompts and paper briefing builder.
 *
 * Paper-derived text is copied verbatim from the saved result. Background
 * explanations and role questions are STATIC learning content, not assertions
 * about a paper or a recommendation to trade any security.
 */
import { juniorGuideSummary, screenPassedFindingCandidates } from "./junior-guide.ts";
import type { JuniorGuideResult } from "./junior-guide";

export type JuniorRole = "wealth" | "risk" | "research" | "product" | "technology";

export type MethodLesson = {
  id: string;
  title: string;
  why: string;
  assumption: string;
  caution: string;
};

type MethodRule = MethodLesson & { pattern: RegExp };

export const roleOptions: Array<{ key: JuniorRole; label: string }> = [
  { key: "wealth", label: "자산관리·WM" },
  { key: "risk", label: "리스크관리" },
  { key: "research", label: "리서치·투자전략" },
  { key: "product", label: "상품·기획" },
  { key: "technology", label: "개발·데이터" },
];

const ROLE_QUESTIONS: Record<JuniorRole, { focus: string; questions: string[]; deliverable: string }> = {
  wealth: {
    focus: "고객 설명에 활용할 수 있는지, 원문이 다루는 투자 대상과 투자 기간을 확인합니다.",
    questions: [
      "논문의 시장·자산군·표본이 고객에게 설명하려는 상품과 일치하나요?",
      "추정된 평균 효과를 개별 고객의 미래 성과로 오해할 여지가 있나요?",
      "고객 설명 시 꼭 함께 알려야 할 불확실성·연구 한계는 무엇인가요?",
    ],
    deliverable: "고객 설명 전 확인할 원문 근거와 적용 범위 목록",
  },
  risk: {
    focus: "위험 측정에 필요한 가정과 스트레스 상황에서의 적용 가능성을 확인합니다.",
    questions: [
      "논문이 사용한 위험지표는 변동성·손실·유동성 중 무엇을 측정하나요?",
      "금융위기나 급격한 시장 변화에서도 모형 가정이 유지될까요?",
      "백테스트·표본 외 검증과 모형 한계가 보고되었나요?",
    ],
    deliverable: "위험지표, 가정, 검증방법 및 적용 제외 조건 메모",
  },
  research: {
    focus: "가설·식별 전략·실증 결과의 강도를 구분하고 재현 가능성을 확인합니다.",
    questions: [
      "연구 질문과 귀무가설, 통제 변수와 식별 전략은 무엇인가요?",
      "통계적 유의성과 경제적 중요성을 각각 어떻게 보여주나요?",
      "대체 표본·모형·기간으로 결과가 유지되는지 확인했나요?",
    ],
    deliverable: "주장·추정치·원문 인용·남은 검증 사항 표",
  },
  product: {
    focus: "상품이나 서비스 아이디어와 원문의 증거 사이에 남아 있는 차이를 확인합니다.",
    questions: [
      "논문의 대상 고객·자산·시장 조건이 제품의 이용 상황과 같은가요?",
      "성과 개선 주장은 실증 결과인가요, 해석 또는 후속 아이디어인가요?",
      "상품 설명·규제·적합성 검토 전 어떤 근거가 더 필요한가요?",
    ],
    deliverable: "제품 활용 가설과 검증이 필요한 데이터·조건 목록",
  },
  technology: {
    focus: "데이터 정의, 누수 방지, 구현 가능성과 재현성을 중심으로 읽습니다.",
    questions: [
      "입력 변수·기간·빈도와 학습/검증 데이터 분리가 명확한가요?",
      "미래 정보 누수, 표본 선택 편향, 재현 불가능한 전처리가 있나요?",
      "현재 운영 데이터와 계산 자원으로 같은 평가를 재현할 수 있나요?",
    ],
    deliverable: "데이터 스키마·재현 절차·성능 검증·누수 점검 항목",
  },
};

const METHOD_RULES: MethodRule[] = [
  {
    id: "garch-midas", title: "GARCH-MIDAS",
    why: "단기적인 변동성 움직임과 더 느리게 변하는 장기 성분을 구분해 추정하려고 사용합니다.",
    assumption: "월별·분기별 변수와 일별 수익률의 시간 정렬 및 표본 범위가 적절해야 합니다.",
    caution: "장기 변수와 변동성의 관련성이 확인돼도 인과관계나 향후 예측력을 자동 보장하지 않습니다.",
    pattern: /\bGARCH[\s-]?MIDAS\b/i,
  },
  {
    id: "garch", title: "GARCH",
    why: "수익률의 변동성이 큰 시기와 작은 시기가 연속해서 나타나는 현상을 표현합니다.",
    assumption: "모형 차수와 오차 분포, 시계열의 안정성 등을 확인해야 합니다.",
    caution: "변동성 추정이 모든 꼬리위험 또는 손실 규모를 설명하는 것은 아닙니다.",
    pattern: /\b(?:GARCH|EGARCH|GJR-GARCH)\b/i,
  },
  {
    id: "capm", title: "CAPM",
    why: "시장 위험(베타)을 기준으로 자산 수익률의 일부를 설명하거나 비교하는 기준선을 만듭니다.",
    assumption: "시장 포트폴리오의 대용 지표와 무위험수익률 가정이 적절한지 확인해야 합니다.",
    caution: "베타만으로 모든 수익률 차이를 설명하는 것은 아닙니다.",
    pattern: /\bCAPM\b|자본자산가격결정/i,
  },
  {
    id: "fama-french", title: "Fama–French 요인모형",
    why: "시장·규모·가치 등 요인에 대한 노출로 자산 수익률 차이를 설명해 보려는 방법입니다.",
    assumption: "사용한 요인의 종류와 구성 방법, 표본 시장의 적합성을 확인해야 합니다.",
    caution: "3요인·5요인 등 버전에 따라 해석할 대상이 달라집니다.",
    pattern: /fama[\s–-]*french|파마[\s-]*프렌치/i,
  },
  {
    id: "var", title: "VAR / TVP-VAR",
    why: "여러 시계열 변수가 서로 시간차를 두고 영향을 주고받는 패턴을 분석합니다.",
    assumption: "시차 선택, 시계열 변환, 정상성 또는 안정성 조건을 살펴봐야 합니다.",
    caution: "변수 사이의 예측 관계만으로 구조적 인과관계가 성립하지는 않습니다.",
    pattern: /\b(?:TVP[\s-]?VAR|VAR)\b|벡터자기회귀/i,
  },
  {
    id: "lasso", title: "LASSO",
    why: "변수 계수를 축소해 많은 후보 변수에서 예측에 유용한 일부를 선택하려고 씁니다.",
    assumption: "규제 강도를 선택한 방법, 시간 순서에 맞는 검증 데이터 분리를 확인해야 합니다.",
    caution: "선택된 변수는 상황에 따라 달라지며, 선택 자체가 인과성을 의미하지 않습니다.",
    pattern: /\bLASSO\b/i,
  },
  {
    id: "difference-in-differences", title: "이중차분법(DiD)",
    why: "정책이나 사건 전후의 변화를 비교집단과 나란히 비교해 효과를 추정합니다.",
    assumption: "특히 평행추세 가정과 처치·비교집단의 비교 가능성을 점검해야 합니다.",
    caution: "집단 간 추세가 원래 달랐다면 추정 결과를 정책 효과라고 단정하기 어렵습니다.",
    pattern: /\b(?:difference[\s-]*in[\s-]*differences|diff[\s-]*in[\s-]*diff|DiD)\b|이중차분/i,
  },
  {
    id: "event-study", title: "사건연구(Event study)",
    why: "공시·정책·충격 등 특정 사건 주변에서의 비정상적인 수익률 움직임을 살펴봅니다.",
    assumption: "사건일, 추정창, 시장모형, 동시 발생 사건이 적절히 처리됐는지 확인해야 합니다.",
    caution: "사건 주변의 가격 변화가 전부 해당 사건 때문이라고 확정할 수는 없습니다.",
    pattern: /\b(?:event[\s-]*study|event[\s-]*window|abnormal[\s-]*returns?)\b|사건연구/i,
  },
  {
    id: "optimization", title: "포트폴리오 최적화",
    why: "기대수익률·위험·제약 조건 등을 고려해 자산 비중을 계산합니다.",
    assumption: "입력 수익률·상관관계·거래 비용과 제약 조건에 민감할 수 있습니다.",
    caution: "과거 자료에 최적화된 비중이 미래 투자 성과를 보장하지 않습니다.",
    pattern: /portfolio[\s-]*optimi[sz]ation|mean[\s-]*variance|포트폴리오\s?최적화|마코위츠/i,
  },
  {
    id: "regression", title: "회귀분석",
    why: "관측된 변수들 사이의 통계적 관계 크기와 방향을 추정하기 위해 사용합니다.",
    assumption: "독립변수와 오차의 관계, 누락 변수, 표준오차 처리 방법 등을 확인해야 합니다.",
    caution: "회귀계수와 통계적 유의성만으로 인과관계나 실무적 중요성이 증명되지는 않습니다.",
    pattern: /\b(?:OLS|regression|fixed[\s-]*effects|random[\s-]*effects)\b|회귀분석|고정효과/i,
  },
];

function cleanLine(value: string | undefined | null) {
  return (value ?? "").replace(/[\u0000-\u001F\u007F]+/g, " ").trim();
}

export function juniorRoleGuide(role: JuniorRole = "wealth") {
  return ROLE_QUESTIONS[role];
}

export function explainPaperMethods(result: JuniorGuideResult): MethodLesson[] {
  const method = result.methodology;
  const text = [
    method?.design, method?.empirical_strategy, method?.identification_strategy,
  ].filter((value): value is string => typeof value === "string").join(" ").slice(0, 30_000);
  if (!text.trim()) return [];
  const matched = METHOD_RULES.filter((rule) => rule.pattern.test(text));
  const hasMidas = matched.some((rule) => rule.id === "garch-midas");
  const hasSpecificRegression = matched.some((rule) => rule.id === "difference-in-differences");
  return matched
    .filter((rule) => !(hasMidas && rule.id === "garch"))
    .filter((rule) => !(hasSpecificRegression && rule.id === "regression"))
    .slice(0, 4)
    .map(({ id, title, why, assumption, caution }) => ({ id, title, why, assumption, caution }));
}

export type JuniorBriefSource = JuniorGuideResult & {
  bibliographic?: { doi?: string };
};

export function composeJuniorBrief(result: JuniorBriefSource, title: string, role: JuniorRole = "wealth") {
  const guide = juniorGuideSummary(result);
  const questions = juniorRoleGuide(role);
  const roleLabel = roleOptions.find((item) => item.key === role)?.label ?? "자산관리·WM";
  const selected = screenPassedFindingCandidates(result).slice(0, 2);
  const methodology = [
    guide.method.design ? "연구 설계: " + cleanLine(guide.method.design) : null,
    guide.method.sample ? "표본: " + cleanLine(guide.method.sample) : null,
    guide.method.period ? "기간: " + cleanLine(guide.method.period) : null,
    guide.method.strategy ? "추정 방법: " + cleanLine(guide.method.strategy) : null,
  ].filter((v): v is string => Boolean(v));
  const sections = [
    "PaperSignal | 금융논문 1쪽 공유 브리핑 초안",
    "논문: " + (cleanLine(title) || "제목 미확인"),
    ...(result.bibliographic?.doi ? ["DOI: " + cleanLine(result.bibliographic.doi)] : []),
    "확인 범위: 자동 추출 및 페이지 인용의 1차 대조. 독립 연구자 검증 전.",
    "",
    "[1] 연구 질문 · 논문에서 추출",
    cleanLine(guide.question) || "원문 근거가 확인된 연구 질문 없음",
    "",
    "[2] 사용한 데이터·방법 · 논문에서 추출",
    ...(methodology.length ? methodology : ["검증 가능한 방법론 정보 없음"]),
    "",
    "[3] 핵심 결과 · 자동 1차 대조 통과(독립 검증 아님)",
    ...(selected.length
      ? selected.flatMap((finding, i) => [
          (i + 1) + ". " + cleanLine(finding.claim),
          "   출처 PDF p." + finding.page + " 원문 인용: “" + finding.quote + "”",
        ])
      : ["표시할 근거 대조 통과 결과 없음. 수치를 추정하지 않음."]),
    ...(guide.reviewNeededFindingCount > 0
      ? ["추가 " + guide.reviewNeededFindingCount + "건은 검토가 필요하여 위 결과에서 제외."]
      : []),
    "",
    "[4] 원문에서 추출한 연구 한계",
    ...(guide.limitations.length ? guide.limitations.map((v) => "- " + cleanLine(v)) : ["원문 근거가 있는 한계 정보 미확인"]),
    "",
    "[5] " + roleLabel + " 업무 검토 질문 · 일반 교육 가이드(논문 주장 아님)",
    ...questions.questions.map((q) => "- " + q),
    "",
    "[전달 전 확인]",
    "논문 원문 페이지·통계적 유의성·표본 조건을 다시 대조하세요.",
    "과거 연구 결과는 미래 수익·투자 성과를 보장하지 않습니다.",
    "이 초안은 투자 권유·상품 적합성 또는 준법 심사 결과가 아닙니다.",
  ];
  return sections.join("\n");
}

/** File names are local export labels only, never untrusted storage paths. */
export function juniorBriefFilename(title: string) {
  const safe = title
    .normalize("NFKC")
    .replace(/[\\/:*?"<>|\u0000-\u001f\u007f]/g, "_")
    .replace(/\s+/g, " ")
    .replace(/^\.+|\.+$/g, "")
    .trim()
    .slice(0, 60);
  return (safe || "paper") + "-papersignal-junior-brief.txt";
}
