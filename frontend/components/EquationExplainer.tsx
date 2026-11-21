"use client";

import { useMemo } from "react";
import { EvidencePopover } from "./EvidencePopover";

type Evidence = { page: number; quote: string };
type Variable = {
  name: string;
  role: string;
  definition: string;
  evidence?: Evidence[];
};

type Props = {
  equations: string[];
  variables?: Variable[];
};

type SymbolExplanation = {
  role: string;
  description: string;
  source: "paper" | "notation";
  variable?: Variable;
};

const TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_]*|[α-ωΑ-Ω]/gu;

function matchesVariableName(name: string, symbol: string) {
  // Latin letter case is significant in equations: C (input) and c (constant) are different symbols.
  const tokens = name.split(/[^A-Za-z0-9_α-ωΑ-Ω]+/u);
  return tokens.includes(symbol);
}

function explainNotation(symbol: string): Omit<SymbolExplanation, "variable"> {
  if (symbol === "L") return {
    role: "함수의 출력 또는 목적함수 기호",
    description: "L(C)는 C를 입력으로 받아 계산한 함수값을 뜻합니다. L이 손실함수인지, 비용인지, 다른 지표인지는 이 표기만으로 확정할 수 없으며 논문의 정의를 확인해야 합니다.",
    source: "notation",
  };
  if (symbol === "C") return {
    role: "함수의 입력 변수",
    description: "이 식에서 C는 함수에 들어가는 변수입니다. 실제로 비용·자본·용량·통제변수 중 무엇을 뜻하는지는 논문의 변수 정의를 우선해야 합니다.",
    source: "notation",
  };
  if (symbol === "a" || symbol === "α") return {
    role: "계수 또는 크기 조정 파라미터",
    description: "함수값의 크기를 조정하는 계수로 쓰였습니다. 양·음의 부호와 추정값, 경제적 의미는 논문이 제시한 정의와 추정 결과를 확인해야 합니다.",
    source: "notation",
  };
  if (symbol === "b" || symbol === "k") return {
    role: "거듭제곱 지수 파라미터",
    description: "C의 거듭제곱에 적용되는 지수입니다. 함수가 C에 따라 얼마나 빠르게 증가·감소하는지와 곡률을 결정합니다. 탄력성 등 구체적인 해석은 모형의 정의를 확인해야 합니다.",
    source: "notation",
  };
  if (symbol === "c" || symbol === "c0") return {
    role: "상수항",
    description: "다른 변수와 무관하게 더해지는 상수항입니다. 모형에 따라 절편 또는 기준 수준을 나타낼 수 있지만, 실제 해석은 논문 정의에 따릅니다.",
    source: "notation",
  };
  if (symbol === "E_P" || symbol === "EP") return {
    role: "확률분포 P 아래의 기댓값 연산자",
    description: "E_P[·]는 P로 표시된 확률분포 또는 확률측도 아래에서 대괄호 안의 값을 평균한 기댓값을 뜻하는 일반적 표기입니다. P가 가리키는 분포·정보집합은 논문에서 확인해야 합니다.",
    source: "notation",
  };
  if (symbol === "log") return {
    role: "로그 함수",
    description: "괄호 안 값에 로그를 취합니다. 로그의 밑이 자연로그인지 다른 밑인지는 논문의 표기 관례나 본문 정의를 확인해야 합니다.",
    source: "notation",
  };
  if (symbol === "pass_rate") return {
    role: "C에 따라 달라지는 비율 함수",
    description: "pass_rate(C)는 C를 입력으로 받는 통과율 또는 성공률 형태의 함수로 읽을 수 있습니다. 분자·분모, 통과의 기준, 관측 단위는 논문 정의가 있어야 확정할 수 있습니다.",
    source: "notation",
  };
  return {
    role: "논문 정의 확인 필요",
    description: "수식에 등장하는 기호이지만, 현재 추출된 변수 정의에서 대응 항목을 찾지 못했습니다. 임의로 의미를 부여하지 않고 논문의 기호 설명을 확인하도록 남겨 둡니다.",
    source: "notation",
  };
}

export function EquationExplainer({ equations, variables = [] }: Props) {
  const symbols = useMemo(() => {
    const seen = new Set<string>();
    const tokens = equations.flatMap((equation) => equation.match(TOKEN_PATTERN) ?? []);
    return tokens.filter((token) => {
      // Preserve case: C and c are different mathematical symbols.
      if (seen.has(token)) return false;
      seen.add(token);
      return true;
    });
  }, [equations]);

  const explanations = useMemo<SymbolExplanation[]>(() => symbols.map((symbol) => {
    const variable = variables.find((candidate) => matchesVariableName(candidate.name, symbol));
    if (variable?.definition?.trim()) {
      return {
        role: variable.role?.trim() || "논문에서 추출한 변수",
        description: variable.definition.trim(),
        source: "paper",
        variable,
      };
    }
    return explainNotation(symbol);
  }), [symbols, variables]);

  if (!equations.length) return null;

  return <section className="equation-explainer" aria-label="모형 및 수식 해설">
    <div className="equation-list">
      {equations.map((equation, index) => <pre className="equation" key={index}>{equation}</pre>)}
    </div>
    {explanations.length > 0 && <div className="equation-symbol-guide">
      <div className="equation-symbol-heading">
        <h5>기호별 설명</h5>
        <p>논문에서 추출한 변수 정의를 우선 표시하고, 정의가 없는 기호는 수식에서의 일반적인 수학적 역할만 설명합니다.</p>
      </div>
      <div className="equation-symbol-grid">
        {explanations.map((item, index) => <article className="equation-symbol-row" key={symbols[index]}>
          <div className="equation-symbol-token">{symbols[index]}</div>
          <div className="equation-symbol-copy">
            <strong>{item.role}</strong>
            <p>{item.description}</p>
            {item.source === "paper"
              ? <div className="equation-symbol-source">
                  <span>논문에서 추출한 변수 정의</span>
                  {item.variable?.evidence?.length
                    ? <EvidencePopover items={item.variable.evidence} label={`${symbols[index]} 변수 정의 원문 근거`}>원문 근거</EvidencePopover>
                    : <span className="equation-source-unavailable">페이지 인용 미연결</span>}
                </div>
              : <span className="equation-symbol-caveat">일반 표기 해설 · 논문 내 구체적 의미는 별도 확인 필요</span>}
          </div>
        </article>)}
      </div>
    </div>}
  </section>;
}
