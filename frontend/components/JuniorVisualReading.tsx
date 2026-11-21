"use client";

import { useMemo } from "react";
import { buildVisualReadingCards } from "../lib/junior-visuals";
import type { VisualFinding } from "../lib/junior-visuals";
import styles from "./JuniorVisualReading.module.css";
import { EvidencePopover } from "./EvidencePopover";

type Props = {
  result: { findings?: VisualFinding[] };
  sourcePdfReady: boolean;
  onOpenSourcePage?: (page: number) => void;
};

export function JuniorVisualReading({ result, sourcePdfReady, onOpenSourcePage }: Props) {
  const cards = useMemo(() => buildVisualReadingCards(result), [result]);
  return <section className={styles.section} aria-labelledby="junior-visual-heading">
    <header className={styles.header}>
      <div>
        <p className={styles.eyebrow}>VISUAL EVIDENCE LITERACY</p>
        <h3 id="junior-visual-heading">표·그래프, 원문 보면서 읽기</h3>
        <p>논문에서 추출한 표·그림 번호와 결과를 바탕으로 주니어가 확인해야 할 항목을 차근차근 익히세요.</p>
      </div>
      <span className={styles.tag}>주니어 학습</span>
    </header>
    <div className={styles.lesson} aria-label="표와 그래프 읽기 기본 방법">
      <div><strong>표를 볼 때</strong>
        <p>행은 무엇을 비교하고, 열은 어떤 모형·기간을 나타내나요? 계수의 부호뿐 아니라 단위, 표본 수, 기준집단과 표 하단 주석을 확인하세요.</p>
      </div>
      <div><strong>그래프를 볼 때</strong>
        <p>가로·세로축의 이름과 단위, 기간, 범례, 신뢰구간을 확인하세요. 축 범위에 따라 차이가 과장되어 보일 수 있습니다.</p>
      </div>
    </div>
    <p className={styles.educationNote}><b>위 내용은 일반 학습 안내</b>이며, 논문에서 실제 사용한 단위·축·계수값을 대신 설명하는 것이 아닙니다.</p>
    {cards.length === 0 ? <p className={styles.empty} role="status">
      현재 저장된 분석 결과에는 표·그림 번호가 연결된 실증 결과가 없습니다. 시각자료의 내용이나 위치를 추정하지 않습니다. 원본 PDF에서 직접 확인하세요.
    </p> : <>
      <p className={styles.count}>표·그림 참조가 연결된 {cards.length}개 항목입니다. 펼쳐서 원문과 대조하세요.</p>
      <div className={styles.cards}>
        {cards.map((card, index) => <details className={styles.card} key={card.reference + "|" + card.column + "|" + index}>
          <summary className={styles.summary}>
            <span className={styles.summaryTitle}><span className={styles.kind}>{card.kind === "chart" ? "그래프" : "표"}</span><b>{card.reference}</b>{card.column && <small>{card.column}</small>}</span>
            <span className={card.screening === "screen_passed" ? styles.passed : styles.review}>
              {card.screening === "screen_passed" ? "자동 1차 대조 통과" : "추가 원문 확인 필요"}
            </span>
          </summary>
          <div className={styles.body}>
            <p className={styles.factsLabel}>논문 분석 결과에서 추출한 정보 · 원문 대조 필요</p>
            {card.claim && <p className={styles.claim}>{card.claim}</p>}
            <dl className={styles.fields}>
              {card.column && <><dt>모형·열</dt><dd>{card.column}</dd></>}
              {card.estimate && <><dt>보고된 추정치</dt><dd>{card.estimate}</dd></>}
              {card.direction && <><dt>보고된 방향</dt><dd>{card.direction}</dd></>}
              {card.significance && <><dt>보고된 유의성</dt><dd>{card.significance}</dd></>}
            </dl>
            {card.sourceQuote || card.legendQuote
              ? <EvidencePopover items={[
                  ...(card.sourceQuote && card.sourcePage !== null ? [{ page: card.sourcePage, quote: card.sourceQuote }] : []),
                  ...(card.legendQuote && card.legendPage !== null ? [{ page: card.legendPage, quote: card.legendQuote }] : []),
                ]} onOpenSourcePage={sourcePdfReady ? onOpenSourcePage : undefined}/>
              : <p className={styles.warning}>표·그림을 연결할 원문 인용 페이지가 없습니다. 위치를 임의로 지정하지 않습니다.</p>}
            <div className={styles.checks}>
              <strong>원문에서 직접 확인할 질문</strong>
              <ol>{card.kind === "chart" ? <>
                <li>축의 단위·기간·범례가 실제로 무엇을 뜻하나요?</li>
                <li>오차막대·신뢰구간이 있다면 무엇을 의미하나요?</li>
                <li>축 범위와 표본 선택이 인상을 바꾸지는 않나요?</li>
              </> : <>
                <li>이 값은 어느 행·열의 어떤 모형에 해당하나요?</li>
                <li>단위, 기준집단, 통제변수와 표본 수는 무엇인가요?</li>
                <li>별표·괄호·p값의 의미를 표 주석에서 어떻게 정의했나요?</li>
              </>}</ol>
            </div>
            <p className={styles.disclaimer}>통계적 유의성은 효과 크기나 인과관계 입증을 뜻하지 않습니다.
              {card.screening === "screen_passed" ? " 자동 1차 대조 통과도 독립 연구자 검증을 뜻하지 않습니다." : " 이 항목은 검증 정보가 부족하거나 추가 원문 대조가 필요합니다."}
            </p>
          </div>
        </details>)}
      </div>
    </>}
  </section>;
}
