"use client";

import { useMemo } from "react";
import { juniorGuideSummary } from "../lib/junior-guide";
import type { JuniorGuideResult } from "../lib/junior-guide";
import styles from "./JuniorPaperGuide.module.css";

type Props = {
  result: JuniorGuideResult;
  sourcePdfUrl?: string;
};

export function JuniorPaperGuide({ result, sourcePdfUrl }: Props) {
  const guide = useMemo(() => juniorGuideSummary(result), [result]);
  const hasMethod = Object.values(guide.method).some(Boolean);

  return <section className={styles.guide} aria-labelledby="junior-guide-heading">
    <div className={styles.heading}>
      <div>
        <p className={styles.eyebrow}>JUNIOR RESEARCH GUIDE</p>
        <h3 id="junior-guide-heading">주니어를 위한 3분 논문 읽기</h3>
        <p>낯선 금융 용어부터 연구 방법, 확인할 결과까지 순서대로 살펴보세요.</p>
      </div>
      <span className={styles.contextTag}>기초 해설</span>
    </div>
    <div className={styles.cards}>
      <article className={styles.card}>
        <div className={styles.number}>01</div>
        <h4>이 논문은 무엇을 알아보려 하나요?</h4>
        {guide.question
          ? <p>{guide.question}</p>
          : <p className={styles.unknown}>원문 근거가 확인된 연구 질문이 아직 없습니다.</p>}
        {guide.summary && <>
          <b className={styles.label}>AI 추출 요약 · 반드시 원문 확인</b>
          <p>{guide.summary}</p>
        </>}
      </article>
      <article className={styles.card}>
        <div className={styles.number}>02</div>
        <h4>어떤 데이터와 방법을 썼나요?</h4>
        {hasMethod ? <dl className={styles.method}>
          {guide.method.design && <><dt>연구 설계</dt><dd>{guide.method.design}</dd></>}
          {guide.method.sample && <><dt>표본</dt><dd>{guide.method.sample}</dd></>}
          {guide.method.period && <><dt>기간</dt><dd>{guide.method.period}</dd></>}
          {guide.method.strategy && <><dt>분석 방법</dt><dd>{guide.method.strategy}</dd></>}
        </dl> : <p className={styles.unknown}>원문에서 확인 가능한 방법론을 아직 추출하지 못했습니다.</p>}
        <p className={styles.footnote}>위 내용은 분석 결과에서 가져온 것입니다. 표본·기간·모형은 원문과 대조하세요.</p>
      </article>
      <article className={styles.card}>
        <div className={styles.number}>03</div>
        <h4>어떤 결과를 근거와 함께 확인할 수 있나요?</h4>
        {guide.findings.length ? <ol className={styles.findings}>
          {guide.findings.map((finding, index) => <li key={index}>
            <p>{finding.claim}</p>
            {sourcePdfUrl
              ? <a href={sourcePdfUrl + "#page=" + finding.page} target="_blank" rel="noreferrer">원문 {finding.page}쪽 대조</a>
              : <span>원문 {finding.page}쪽 근거 · PDF 링크 준비 중</span>}
          </li>)}
        </ol> : <p className={styles.unknown}>자동 근거 대조를 통과한 실증 결과가 없습니다. 결과를 임의로 추정하지 않습니다.</p>}
        <p className={styles.footnote}>표시된 결과는 자동 페이지·수치 1차 대조를 통과한 항목입니다. 독립 연구자의 사실 검증을 뜻하지 않습니다.</p>
        {guide.reviewNeededFindingCount > 0 && <p className={styles.caution}>추가로 {guide.reviewNeededFindingCount}건은 자동 대조 기준을 충족하지 않아 연구자 확인이 필요합니다.</p>}
        {guide.additionalScreenedFindingsCount > 0 && <p className={styles.footnote}>나머지 자동 대조 통과 {guide.additionalScreenedFindingsCount}건은 아래 상세 실증 결과에서 확인할 수 있습니다.</p>}
      </article>
    </div>
    <div className={styles.learning}>
      <div className={styles.learningHeader}>
        <h4>처음 보는 금융·계량 용어</h4>
        <p>일반적인 금융 개념을 설명하는 학습 카드입니다. 논문의 주장이나 투자 조언이 아닙니다.</p>
      </div>
      {guide.terms.length
        ? <div className={styles.terms}>{guide.terms.map((term) => <details key={term.label} className={styles.term}>
          <summary>{term.label} <span aria-hidden="true">＋</span></summary>
          <p>{term.meaning}</p>
          <p><b>읽을 때 확인할 점</b> {term.check}</p>
        </details>)}</div>
        : <p className={styles.noTerms}>자동으로 연결할 수 있는 기초 용어가 없습니다. 아래 상세 분석에서 궁금한 표현을 원문과 함께 확인해 보세요.</p>}
    </div>
    <div className={styles.practice}>
      <h4>금융 실무에 연결할 때 확인할 질문</h4>
      <ul>
        <li>연구 대상 시장·자산군·기간이 지금 맡은 업무와 같은가요?</li>
        <li>결과가 통계적으로 유의한 것과 실제 경제적으로 중요한 것을 구분했나요?</li>
        <li>상관관계를 인과관계로 단정하거나 과거 결과를 미래 수익으로 오해하지 않았나요?</li>
      </ul>
      {guide.limitations.length > 0 && <p className={styles.limitations}>
        <b>논문에서 추출한 연구 한계</b> {guide.limitations.join(" · ")}
      </p>}
      <p className={styles.footnote}>이 질문들은 학습용 점검 항목이며, 특정 상품 투자·매매를 권유하지 않습니다.</p>
    </div>
  </section>;
}
