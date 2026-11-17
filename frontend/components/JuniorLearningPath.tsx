"use client";

import { useEffect, useMemo, useState } from "react";
import { buildStudyQuiz, buildStudySteps, emptyStudyProgress, gradeStudyQuiz, parseStudyProgress, serializeStudyProgress, studyStorageKey } from "../lib/junior-learning";
import type { StudyProgress, StudySource, StudyStepId } from "../lib/junior-learning";
import type { JuniorRole } from "../lib/junior-workflow";
import styles from "./JuniorLearningPath.module.css";

type Props = {
  role: JuniorRole;
  userId: string;
  paperId: string;
  result: StudySource;
  sourcePdfReady: boolean;
  onOpenSourcePage?: (page: number) => void;
};

export function JuniorLearningPath({ role, userId, paperId, result, sourcePdfReady, onOpenSourcePage }: Props) {
  const steps = useMemo(() => buildStudySteps(result, role), [result, role]);
  const quiz = useMemo(() => buildStudyQuiz(result, role), [result, role]);
  const key = studyStorageKey(userId, paperId, role);
  const [progress, setProgress] = useState<StudyProgress>(() => emptyStudyProgress());
  const [loaded, setLoaded] = useState(false);
  const [storageAvailable, setStorageAvailable] = useState(true);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [graded, setGraded] = useState(false);
  const [notice, setNotice] = useState("");
  const score = gradeStudyQuiz(quiz, answers);

  useEffect(() => {
    try {
      setProgress(key ? parseStudyProgress(window.localStorage.getItem(key)) : emptyStudyProgress());
      setStorageAvailable(Boolean(key));
    } catch {
      setProgress(emptyStudyProgress());
      setStorageAvailable(false);
    }
    setLoaded(true);
  }, [key]);

  function save(next: StudyProgress) {
    setProgress(next);
    if (!key) return;
    try {
      window.localStorage.setItem(key, serializeStudyProgress(next));
    } catch {
      setStorageAvailable(false);
    }
  }

  function toggleStep(id: StudyStepId, checked: boolean) {
    const completed = checked
      ? [...progress.completed.filter((value) => value !== id), id]
      : progress.completed.filter((value) => value !== id);
    save({ ...progress, completed });
    setNotice("");
  }

  function submitQuiz() {
    if (!score.complete) return;
    save({ ...progress, bestScore: Math.max(progress.bestScore ?? 0, score.correct) });
    setGraded(true);
    setNotice("");
  }

  function reset() {
    setProgress(emptyStudyProgress());
    setAnswers({});
    setGraded(false);
    if (key) {
      try { window.localStorage.removeItem(key); }
      catch { setStorageAvailable(false); }
    }
    setNotice("이 논문과 직무의 학습 기록을 초기화했습니다.");
  }

  return <section className={styles.panel} aria-labelledby="study-route-heading">
    <header className={styles.header}>
      <div>
        <p className={styles.eyebrow}>ROLE-BASED LEARNING PATH</p>
        <h4 id="study-route-heading">직무별 4단계 학습 경로</h4>
        <p>위에서 선택한 관심 직무에 맞춰 읽고, 원문을 대조한 후 완료 표시를 해 보세요.</p>
      </div>
      <span className={styles.progressNumber}>{loaded ? progress.completed.length : "–"} / {steps.length} 단계</span>
    </header>
    <progress className={styles.progress} value={progress.completed.length} max={steps.length} aria-label="직무별 학습 경로 진행률" />
    <div className={styles.steps}>
      {steps.map((step) => <article key={step.id} className={styles.step}>
        <label className={styles.stepHeading}>
          <input type="checkbox" checked={progress.completed.includes(step.id)} disabled={!loaded}
            onChange={(event) => toggleStep(step.id, event.target.checked)}/>
          <span>{step.title}</span>
        </label>
        <p className={styles.task}>{step.task}</p>
        {step.extracted && <div className={styles.extract}>
          <b>저장된 논문 분석 정보 · 원문 확인 필요</b>
          <p>{step.extracted}</p>
        </div>}
        {step.sourcePage !== null && <div className={styles.source}>
          <span>인용 근거: 원본 PDF {step.sourcePage}쪽</span>
          <button type="button" disabled={!sourcePdfReady || !onOpenSourcePage}
            onClick={() => { if (step.sourcePage !== null) onOpenSourcePage?.(step.sourcePage); }}>
            {sourcePdfReady ? "원문 페이지 열기" : "PDF 연결 대기"}
          </button>
        </div>}
        {step.evidenceNeeded && step.sourcePage === null && <p className={styles.missing}>
          직접 연결할 수 있는 페이지 인용이 없습니다. 검증된 근거가 있다고 가정하지 말고 원본 PDF에서 확인하세요.
        </p>}
      </article>)}
    </div>
    <p className={styles.note}>완료 체크는 학습자가 직접 표시한 기록이며, 논문 이해도나 원문 사실 검증을 자동 보증하지 않습니다.
      {storageAvailable ? " 이 기기·브라우저에만 저장되며 다른 기기에 동기화되지 않습니다." : " 이 환경에서는 학습 기록이 영구 저장되지 않을 수 있습니다."}
    </p>

    <div className={styles.quiz} aria-labelledby="study-quiz-heading">
      <header>
        <h4 id="study-quiz-heading">논문 읽기 이해도 점검 · 4문항</h4>
        <p>금융논문을 안전하게 해석하는 기본 원칙을 확인합니다. 실제 논문 전체의 사실 검증을 대신하지 않습니다.</p>
      </header>
      <div className={styles.questions}>
        {quiz.map((question, index) => <fieldset key={question.id} className={styles.question}>
          <legend>{index + 1}. {question.question}</legend>
          {question.options.map((option, optionIndex) =>
            <label key={optionIndex} className={styles.option}>
              <input type="radio" name={"learning-" + paperId + "-" + role + "-" + question.id}
                checked={answers[question.id] === optionIndex}
                onChange={() => { setAnswers((current) => ({ ...current, [question.id]: optionIndex })); setGraded(false); setNotice(""); }}/>
              <span>{option}</span>
            </label>)}
          {graded && <p className={answers[question.id] === question.correctIndex ? styles.correct : styles.incorrect}>
            <b>{answers[question.id] === question.correctIndex ? "정답" : "다시 확인"}</b>
            {" · 정답: " + question.options[question.correctIndex] + " · " + question.explanation}
          </p>}
        </fieldset>)}
      </div>
      <div className={styles.actions}>
        <button type="button" className={styles.submit} disabled={!score.complete || !loaded} onClick={submitQuiz}>채점하고 해설 보기</button>
        <span aria-live="polite">{score.answered} / {score.total}문항 선택</span>
      </div>
      {graded && <div role="status" className={styles.result}>
        <b>이번 점검: {score.correct} / {score.total}점</b>
        <span>최고 기록: {Math.max(progress.bestScore ?? 0, score.correct)} / {score.total}점</span>
        <p>점수는 학습용 참고이며, 논문별 사실 이해·실무 판단 능력을 인증하는 평가가 아닙니다.</p>
      </div>}
      {!graded && progress.bestScore !== null && <p className={styles.previous}>이전 최고 기록: {progress.bestScore} / {quiz.length}점</p>}
    </div>
    <div className={styles.footer}>
      <button className={styles.reset} type="button" onClick={reset} disabled={!loaded}>이 직무의 학습 기록 초기화</button>
      {notice && <p role="status">{notice}</p>}
    </div>
  </section>;
}
