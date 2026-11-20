"use client";
import { useEffect, useState } from "react";
import { betaGuideStorageKey } from "../lib/beta-ux";
import styles from "./BetaGettingStarted.module.css";

type Props = { userId: string; paperCount: number; readyCount: number; busy: boolean; onChoosePdf: () => void };

export function BetaGettingStarted({ userId, paperCount, readyCount, busy, onChoosePdf }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [ready, setReady] = useState(false);
  const key = betaGuideStorageKey(userId);
  useEffect(() => {
    setReady(false);
    try { setExpanded(!key || window.localStorage.getItem(key) !== "dismissed"); }
    catch { setExpanded(true); }
    setReady(true);
  }, [key]);
  function dismiss() {
    setExpanded(false);
    if (key) try { window.localStorage.setItem(key, "dismissed"); } catch { /* private browsing */ }
  }
  function reopen() {
    setExpanded(true);
    if (key) try { window.localStorage.removeItem(key); } catch { /* private browsing */ }
  }
  return <section className={styles.panel + " no-print"} aria-label="PaperSignal 베타 시작 안내">
    <div className={styles.top}>
      <div><span className={styles.eyebrow}>GETTING STARTED</span><h2>PaperSignal 처음 사용하기</h2></div>
      {ready && <button type="button" aria-controls="papersignal-start-steps" aria-expanded={expanded}
        className={styles.toggle} onClick={expanded ? dismiss : reopen}>
        {expanded ? "안내 접기" : "사용법 보기"}</button>}
    </div>
    {ready && expanded && <div id="papersignal-start-steps">
      <p className={styles.intro}>금융논문을 업로드하고, AI 결과와 실제 원문을 대조한 뒤, 직무별 학습을 진행해 보세요.</p>
      <ol className={styles.steps}>
        <li><b>01 · 논문 PDF 추가</b><p>30MB 이하의 PDF를 업로드합니다. 개인정보나 사내 미공개 자료가 아닌 공개·비기밀 논문을 사용하세요.</p></li>
        <li><b>02 · 분석과 출처 확인</b><p>논문을 열어 분석을 실행하고, 결과에 표시된 인용을 눌러 원본 PDF 페이지에서 확인합니다.</p></li>
        <li><b>03 · 금융 실무에 연결</b><p>표·그래프 학습 카드와 직무별 학습 경로를 따라 읽고, 이해도 점검으로 기본 원칙을 확인합니다.</p></li>
      </ol>
      <div className={styles.actions}>
        {paperCount === 0
          ? <button type="button" disabled={busy} className={styles.primary} onClick={onChoosePdf}>첫 논문 PDF 선택</button>
          : <a className={styles.primary} href="#paper-library-heading">보관된 논문 보기 · {paperCount}편</a>}
        <span className={styles.status}>{readyCount}편 분석 완료 · 결과는 원본과 대조해 주세요.</span>
      </div>
      <p className={styles.caution}>베타 안내: AI 결과는 전문가 검증이나 투자 자문을 대신하지 않습니다. 분석이 중단된 것처럼 보여도 서버 작업이 진행 중일 수 있으니 작업 상태를 먼저 확인하세요.</p>
    </div>}
  </section>;
}
