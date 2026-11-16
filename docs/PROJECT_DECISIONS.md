# PaperSignal — Project Decisions

## Product and engineering principles

1. Evidence-first: every material research claim needs a verbatim page-level citation.
2. Never fabricate missing findings, coefficients, signs, p-values, significance or sample sizes.
3. Job completion and analysis quality are separate states.
4. Preserve source papers and analysis history by default.
5. Use durable queue/worker processing, resumable checkpoints and idempotent writes.
6. Keep user data isolated by Auth user ID, RLS and private Storage ownership.
7. Keep secrets server-side only.
8. Prefer narrow allow-lists and project-scoped CORS; never allow all Vercel origins.
9. Keep docs synchronized with actual source and deployed behavior.
10. The assistant chooses implementation details and reports results; ask the user only for credentials/consent or unavoidable external setup.

## Explicit user decisions

- Supabase stays on Free. Do not upgrade to Pro for Leaked Password Protection.
- Leaked Password Protection remains disabled; accept one security-advisor WARN as a documented residual risk. Do not claim the setting is enabled.
- Google OAuth is an enabled login method alongside email/password.
- Do not automatically merge Google and email identities or migrate their libraries.
- No Production promotion until required beta gates are verified.
- The user wants periodic durable project progress records so new sessions continue consistently.

## Technical decisions

- Frontend: Next.js/React on Vercel.
- API and worker: FastAPI and separate Railway Worker.
- Database/Auth/Storage/queue: Supabase.
- AI provider: Gemini primary and fallback; provider-neutral normalized schema maintained for future provider comparison.
- New analysis schema version currently finance-structured-v6.3.
- The backend Docker BuildKit test stage is the required release gate while GitHub Actions fails before job creation.
- Vercel Preview origin regex is scoped to the PaperSignal project/team; unrelated Vercel hosts are rejected.
- PDF and model text are sanitized before JSONB persistence; preserve tabs/newlines/carriage returns and remove incompatible control/surrogate characters.
- Findings v6.3 uses a conditional table-first third pass only when the first two passes return no supported findings and empirical-result page signals are detected.
- Findings coverage states: supported, review_required, incomplete, not_assessable.

## Account and data policy

- A Google account with a different email is a separate Auth user; it starts with its own empty library.
- Account migration must prove control of both accounts, require explicit approval, and transactionally move papers, private Storage objects, analyses and jobs with auditability.
- Do not use the service-role key in frontend/browser requests.
- Free Gemini tier may use prompts/responses to improve Google products and may involve human review; use public/synthetic documents only.

## Release policy

- A completed job does not mean all fields were extracted correctly.
- Empty findings on an empirical paper must be flagged as incomplete/review, not silently treated as full success.
- Beta gates include external email confirmation, Google sign-in, live two-user isolation, PDF upload-analysis, backend/frontend build checks, service health and human review of the ten-paper benchmark.

## 2026-11-17 — 최종 사용자 의사결정 (신규, 이전 기술 결정에 우선)

- 파서/오픈소스 도입·완전 교체 계획을 **종료**합니다. PaperSignal의 기존 PyMuPDF 및 finance-structured-v6.4.2 분석 엔진을 유지하고 자체 품질/안정성 개선으로 집중합니다.
- 최대 성능이라는 표현은 임계점을 충분히 달성한 **검증 가능한 제품 기준**으로 정의하며, 무한 미세 최적화를 하지 않습니다. 승인 기준: `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md` (Q0/Q1/Q2/P0, 모두 필수)와 `benchmark/engine_release_gates_2026-11-17.json`.
- 18 review-required를 독립 인간 2인 검수로 모두 판정, 최소 50개 물질적 주장 출처정확도 98% 이상, critical 허위 승인 0, 과거 승인된 인용/Findings 및 현재 엔진의 기능 비퇴행. 4개 이상의 진짜 복구 또는 답변 가능한 사실의 held-out recall +5pp 이상의 의미 있는 품질 개선이 있어야 엔진 개선 종료로 인정. 모델/provider 시간·비용·메모리·실패율이 전체 파이프라인에서 악화되면 기각.
- 결과 기록은 항상 PyMuPDF 기준 인용 호환성 스크린과 독립 진실 정확도를 구별하고, Gemini 503으로 실행 불가한 새 AI 분석을 성공으로 표기하지 않습니다. 모든 게이트 통과 후 안전한 스테이징·최종 배포 및 사후 검증·롤백 원칙. 그 전 운영 브랜치 push/병합 금지.
- 메모리 off: 다음 세션의 지속성은 `plan/engine-quality-release-handoff` 브랜치 `docs/SESSION_HANDOFF_NEXT.md` 및 위 문서에서 이어갑니다. 기존 계정 메모리에 저장되었다고 주장하지 않습니다.
