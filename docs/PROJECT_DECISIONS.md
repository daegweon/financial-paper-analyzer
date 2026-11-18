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
