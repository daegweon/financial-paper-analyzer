/**
 * Junior-first reading aids. The original LLM result remains authoritative for
 * what the paper says; static glossary text is independent educational context.
 * Do NOT treat automated citation screens as human source verification.
 */
export type JuniorEvidence = { page: number; quote: string };

export type JuniorFinding = {
  claim?: string;
  verification?: {
    status?: string;
    numeric_supported?: boolean;
    direction_consistent?: boolean | null;
    significance_supported?: boolean | null;
    unsupported_numeric_tokens?: string[];
  };
  evidence?: JuniorEvidence[];
};

export type JuniorGuideResult = {
  summary?: string;
  research_question?: string;
  methodology?: {
    design?: string;
    sample?: string;
    period?: string;
    empirical_strategy?: string;
    identification_strategy?: string;
    data_sources?: string[];
  };
  findings?: JuniorFinding[];
  limitations?: { description?: string }[];
  findings_coverage?: { status?: string; supported_findings_count?: number; review_findings_count?: number };
};

export type JuniorTerm = {
  label: string;
  meaning: string;
  check: string;
};

type GlossaryRule = JuniorTerm & { pattern: RegExp };

const TERMS: GlossaryRule[] = [
  { label: "회귀분석", meaning: "여러 변수가 함께 움직이는 관계를 수치로 추정하는 통계 방법입니다.", check: "변수 간 관계를 보여주는지, 인과관계까지 입증하는지 구분해 보세요.", pattern: /회귀분석|회귀모형|regression/i },
  { label: "통계적 유의성", meaning: "가정한 통계 모형 아래에서 관측 결과가 우연과 양립하기 얼마나 어려운지 판단하는 기준입니다.", check: "유의하다고 해서 효과가 크거나 실무적으로 중요하다는 뜻은 아닙니다.", pattern: /유의확률|유의성|p[\s-]?value|significan/i },
  { label: "변동성", meaning: "수익률이 시간에 따라 얼마나 크게 흔들리는지 나타내는 위험의 한 측면입니다.", check: "손실 가능성을 모두 설명하는 지표는 아닙니다.", pattern: /변동성|volatilit|garch/i },
  { label: "유동성", meaning: "자산을 원하는 시점에 큰 가격 충격 없이 거래할 수 있는 정도입니다.", check: "시장의 거래량뿐 아니라 매수·매도 호가 차이도 살펴보세요.", pattern: /유동성|liquidity/i },
  { label: "위험 프리미엄", meaning: "위험을 감수한 대가로 기대하는 추가 수익을 뜻합니다.", check: "추정한 과거 프리미엄이 미래 수익을 보장하지는 않습니다.", pattern: /위험\s?프리미엄|risk.premium|liquidity.premium/i },
  { label: "CAPM", meaning: "시장 전체 위험과 자산 기대수익률의 관계를 설명하는 대표적 자산가격결정 모형입니다.", check: "시장 베타 외 다른 요인을 별도로 고려했는지 확인해 보세요.", pattern: /\bCAPM\b|자본자산가격결정/i },
  { label: "Fama–French 요인모형", meaning: "시장 외에 기업 규모·가치 등 여러 요인으로 수익률 차이를 설명하려는 모형입니다.", check: "논문이 3요인, 5요인 또는 다른 확장 모형 중 무엇을 사용했는지 구분해 보세요.", pattern: /fama.{0,3}french|파마.{0,3}프렌치/i },
  { label: "GARCH", meaning: "변동성이 큰 시기와 작은 시기가 모여 나타나는 현상을 반영하는 시계열 모형입니다.", check: "예측 기간과 변동성 측정 방식을 확인해 보세요.", pattern: /\bGARCH\b/i },
  { label: "패널데이터", meaning: "여러 기업·국가·개인 등을 시간에 걸쳐 반복 관측한 자료입니다.", check: "관측 대상 수와 기간 수, 누락 관측치가 있는지 확인해 보세요.", pattern: /패널데이터|패널\s?자료|panel.data|panel model/i },
  { label: "공적분", meaning: "개별 시계열은 움직이더라도 그들 사이에 장기적인 균형 관계가 존재하는지를 다루는 개념입니다.", check: "장기 관계의 존재와 단기 예측 정확도는 다른 문제입니다.", pattern: /공적분|cointegration/i },
  { label: "샤프비율", meaning: "무위험수익률을 초과한 성과를 변동성으로 나누어 평가하는 지표입니다.", check: "수익률 빈도, 위험 측정 및 무위험수익률 가정을 함께 확인해 보세요.", pattern: /샤프\s?비율|sharpe/i },
  { label: "ESG", meaning: "기업의 환경·사회·지배구조 관련 요소를 통칭합니다.", check: "평가 기관·점수 산식·시점이 다르면 해석이 달라질 수 있습니다.", pattern: /\bESG\b|환경.사회.지배구조/i },
  { label: "LASSO", meaning: "회귀계수를 축소하고 일부를 0으로 만들어 변수 선택을 돕는 정규화 방법입니다.", check: "변수 선택의 안정성과 훈련·검증 데이터 분리가 중요합니다.", pattern: /\bLASSO\b/i },
  { label: "인과관계와 상관관계", meaning: "함께 움직인다는 사실만으로 한 변수가 다른 변수의 원인이라고 단정할 수는 없습니다.", check: "식별 전략·통제 변수·실험 또는 준실험 설계를 확인해 보세요.", pattern: /인과관계|상관관계|causal|endogen|identification.strateg/i },
];

function validEvidence(evidence: unknown): JuniorEvidence[] {
  if (!Array.isArray(evidence)) return [];
  return evidence.filter((e): e is JuniorEvidence =>
    Boolean(e && typeof e === "object" &&
      Number.isInteger(e.page) && e.page > 0 &&
      typeof e.quote === "string" && e.quote.trim().length > 0)
  );
}

export function screenPassedFindingCandidates(result: JuniorGuideResult): Array<{
  claim: string;
  page: number;
  quote: string;
}> {
  return (result.findings ?? []).flatMap((finding) => {
    const check = finding.verification;
    if (
      !check || check.status !== "screen_passed" ||
      check.numeric_supported === false ||
      check.direction_consistent === false ||
      check.significance_supported === false ||
      (check.unsupported_numeric_tokens?.length ?? 0) > 0 ||
      !finding.claim?.trim()
    ) return [];
    const citation = validEvidence(finding.evidence)[0];
    return citation ? [{ claim: finding.claim.trim(), page: citation.page, quote: citation.quote.trim() }] : [];
  });
}

export function suggestedJuniorTerms(result: JuniorGuideResult): JuniorTerm[] {
  const text = [
    result.research_question,
    result.summary,
    result.methodology?.design,
    result.methodology?.empirical_strategy,
    result.methodology?.identification_strategy,
    ...(result.findings ?? []).map((item) => item.claim),
  ].filter(Boolean).join(" ").slice(0, 60_000);
  return TERMS.filter((item) => item.pattern.test(text))
    .slice(0, 6)
    .map(({ label, meaning, check }) => ({ label, meaning, check }));
}

export function juniorGuideSummary(result: JuniorGuideResult) {
  const question = result.research_question?.trim() || "";
  const summary = result.summary?.trim() || "";
  const method = result.methodology;
  const eligibleFindings = screenPassedFindingCandidates(result);
  const findings = eligibleFindings.slice(0, 3);
  const totalFindings = result.findings?.length ?? 0;
  const limitations = (result.limitations ?? [])
    .map((entry) => entry.description?.trim())
    .filter((value): value is string => Boolean(value))
    .slice(0, 2);

  return {
    question: question || null,
    summary: summary || null,
    method: {
      design: method?.design?.trim() || null,
      sample: method?.sample?.trim() || null,
      period: method?.period?.trim() || null,
      strategy: method?.empirical_strategy?.trim() || null,
    },
    findings,
    reviewNeededFindingCount: Math.max(0, totalFindings - eligibleFindings.length),
    additionalScreenedFindingsCount: Math.max(0, eligibleFindings.length - findings.length),
    limitations,
    terms: suggestedJuniorTerms(result),
  };
}
