"use client";

import { useMemo, useState } from "react";
import { composeJuniorBrief, explainPaperMethods, juniorBriefFilename, juniorRoleGuide, roleOptions } from "../lib/junior-workflow";
import type { JuniorBriefSource, JuniorRole } from "../lib/junior-workflow";
import { juniorGuideSummary } from "../lib/junior-guide";
import styles from "./JuniorWorkplaceGuide.module.css";

type Props = {
  result: JuniorBriefSource;
  paperTitle: string;
};

export function JuniorWorkplaceGuide({ result, paperTitle }: Props) {
  const [role, setRole] = useState<JuniorRole>("wealth");
  const [copyStatus, setCopyStatus] = useState("");
  const methods = useMemo(() => explainPaperMethods(result), [result]);
  const paper = useMemo(() => juniorGuideSummary(result), [result]);
  const guide = juniorRoleGuide(role);
  const brief = useMemo(() => composeJuniorBrief(result, paperTitle, role), [result, paperTitle, role]);

  async function copyBriefing() {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(brief);
      setCopyStatus("브리핑 초안을 복사했습니다. 원문 근거를 확인한 뒤 공유해 주세요.");
    } catch {
      setCopyStatus("자동 복사를 사용할 수 없습니다. 아래 텍스트에서 직접 선택해 복사하세요.");
    }
  }

  function saveBriefing() {
    const blob = new Blob([brief], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = juniorBriefFilename(paperTitle);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setCopyStatus("브리핑 초안을 텍스트 파일로 저장했습니다. 공유 전 원문을 다시 확인해 주세요.");
  }

  return <section className={styles.panel} aria-label="주니어를 위한 금융모형과 업무 활용 학습">
    <div className={styles.heading}>
      <p className={styles.eyebrow}>FROM PAPER TO PRACTICE</p>
      <h3>이 논문을 금융 실무에 연결해 보기</h3>
      <p>논문의 결과와 일반 금융 교육 내용을 분리해 학습합니다. 특정 상품이나 투자 결정을 권하지 않습니다.</p>
    </div>

    <div className={styles.methodSection}>
      <h4>이 금융모형은 왜 사용하나요?</h4>
      <p className={styles.label}>검출 기준: 추출된 연구 설계·추정 방법의 명시적 용어. 아래 설명은 논문이 아닌 일반적인 모형 교육 내용입니다.</p>
      {methods.length ? <div className={styles.methodList}>
        {methods.map((method) => <details className={styles.methodCard} key={method.id}>
          <summary>{method.title}<span aria-hidden="true">＋</span></summary>
          <dl>
            <dt>사용 목적</dt><dd>{method.why}</dd>
            <dt>확인할 가정</dt><dd>{method.assumption}</dd>
            <dt>해석 시 주의</dt><dd>{method.caution}</dd>
          </dl>
        </details>)}
      </div> : <p className={styles.missing}>추출된 방법론에서 해설 가능한 모형명을 찾지 못했습니다. 논문이 모형을 사용하지 않았다는 뜻은 아닙니다.</p>}
    </div>

    <div className={styles.roleSection}>
      <div className={styles.roleHeading}>
        <div>
          <h4>내 직무에서는 무엇을 확인할까요?</h4>
          <p className={styles.label}>직무별 질문은 학습용 예시이며 논문의 실증 결론이 아닙니다.</p>
        </div>
        <label className={styles.roleSelector}>
          <span>관심 직무</span>
          <select value={role} onChange={(event) => {
            setRole(event.target.value as JuniorRole);
            setCopyStatus("");
          }}>
            {roleOptions.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
          </select>
        </label>
      </div>
      <p>{guide.focus}</p>
      <ol className={styles.questions}>{guide.questions.map((question) => <li key={question}>{question}</li>)}</ol>
      <p className={styles.deliverable}><b>연습 산출물</b> {guide.deliverable}</p>
    </div>

    <div className={styles.briefSection}>
      <h4>논문 1쪽 공유 브리핑 초안</h4>
      <p className={styles.label}>논문에서 추출한 원문 정보, 자동 1차 대조 통과 인용, 일반 직무 질문을 구분합니다. 길이는 논문 내용에 따라 1쪽을 넘을 수 있습니다.</p>
      <details className={styles.briefDetails}>
        <summary>브리핑 내용 미리보기</summary>
        <textarea readOnly value={brief} rows={13} aria-label="논문 업무 공유 브리핑 초안" />
      </details>
      <div className={styles.briefActions}>
        <button type="button" className={styles.copyButton} onClick={() => void copyBriefing()}>
          브리핑 초안 복사
        </button>
        <button type="button" className={styles.saveButton} onClick={saveBriefing}>
          텍스트 파일 저장
        </button>
      </div>
      {copyStatus && <p role="status" className={styles.copyStatus}>{copyStatus}</p>}
      <p className={styles.label}>복사된 내용에는 원문 페이지 번호와 직접 인용을 넣습니다. 독립 전문가 검증·투자 판단을 대신하지 않습니다.</p>
    </div>

    <details className={styles.selfCheck}>
      <summary>3문항으로 이해 점검하기</summary>
      <ol>
        <li>이 논문의 연구 질문을 원문 내용에 근거해 한 문장으로 설명할 수 있나요?</li>
        <li>사용한 모형과 핵심 가정을 구별할 수 있나요? {methods[0] ? "(" + methods[0].title + "부터 확인)" : "(방법론은 원문에서 다시 확인)"}</li>
        <li>{paper.findings.length
          ? "첫 번째 근거 연결 결과를 PDF " + paper.findings[0].page + "쪽에서 직접 찾아 해석할 수 있나요?"
          : "검증된 실증 결과가 없을 때 무엇을 모른다고 밝혀야 할까요?"}</li>
      </ol>
      <p>정답 자동 채점 기능은 제공하지 않습니다. 논문 원문을 보고 스스로 대조해 주세요.</p>
    </details>
  </section>;
}
