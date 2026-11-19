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

- 2026-11-17: Freeze analysis engine performance tuning. Prioritize (1) real login/PDF/source navigation/mobile usability, (2) junior explanations for figures and tables, (3) role-based learning paths and comprehension, (4) beta accessibility/recovery/deployment/rollback. Do not trade several user-facing features for marginal model score gains.

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

## 2026-11-19 — Integrated beta release gate
- Adopt a single consolidated Draft PR #18 against main for beta release readiness; preserve individual stacked feature PRs for history and avoid merging them independently.
- Block final merge and Production promotion on verified real account/PDF two-tenant E2E, custom SMTP, real mobile PDF smoke, and controlled rollback review. CI success alone is not a live QA pass.
- Keep analysis engine frozen; no additional Gemini prompt/model tuning as a prerequisite for beta QA.
- Treat client analysis/job INSERT grants as a material integrity/LLM-spend risk. Deploy and verify new server-only API job creation before restricting production DB privileges; never execute historical migrations blindly against Supabase because remote migration history differs.
- Track isolated postgres DB policy tests as a permanent third CI gate and preserve `live-e2e` as opt-in to avoid unattended production mutations.
- Actions budget is $1 instead of $0, which allows runners to start but could permit billed overages; never automatically increase it.

## 2026-11-19 — Project status source-of-truth and security gate

- Store weighted engineering progress only in `docs/PROJECT_PROGRESS.json`, separate from independently passed beta release gates. Always report both in future user-facing project responses; do not invent a higher score from activity without test/evidence.
- Root `AGENTS.md` directs agents to read the progress JSON, latest `PROJECT_STATE.md` and changelog on a new session. Validate the file in GitHub frontend CI.
- Production-mutating E2E remains an explicit main-branch-only manual opt-in. Refuse target mismatch and absence of non-secret server-owned queue readiness signal before creating disposable Auth users, files or AI work.

## 2026-11-19 — Live API cutover must be service-specific

- Keep the current Railway Worker on its deployed stable image and existing branch. The candidate API/Worker production services both track `feat/research-workspace-mvp`, not the consolidated `release/beta-candidate-20261119`. Any API cutover requires an explicit API-service-only change plan, verified readiness probe, and rollback ID.
- A new GitHub CI job probes the live public API strictly with GET and no credentials; a missing queue-writer marker is expected until new API deploy and must NOT be interpreted as permission to apply DB grant revocation.
- Test candidate API via isolated Uvicorn and synthetic credentials; schema transition checks must cover both pre-revocation (new server queue usable) and post-revocation (browser writes denied).
- Engineering progress +1 to 85% after immutable CI evidence; release gate count still 4/10. No actual user E2E, DB migration or Production deploy.

## 2026-11-19 — Immutable API-only Railway rollout verified

- Railway core API source is pinned to immutable commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732` (deployment `0b5716db-b720-49db-b15c-babf77b26e5a` SUCCESS), rather than auto-following subsequent PR #18 commits. The Worker stays on its earlier stable source and image.
- Require the live HTTP `queue_write_mode=service_role` marker in `api-readonly-live` PR CI. This is a real deployed-code readiness signal, not evidence of a successful authenticated analysis or Storage authorization.
- Retain current client grants until authorized real two-user HTTP E2E passes; only then apply single reviewed SQL migration, never blanket remote db push. Rollback to old API after revocation is incompatible.
- Record progress **86% engineering / 4 of 10 passed beta launch gates**. Do not mark `api_migration` PASSED until both live HTTP E2E and client grant revocation are complete.
