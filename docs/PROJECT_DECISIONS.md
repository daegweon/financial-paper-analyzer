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

## Open-source adoption gate (2026-11-16; final)

- Close PDF/table parser OSS discovery. Do not deploy Camelot globally or page-selected: the observed extraction-only runtime improvement has not produced verified whole-engine benefit and B01 Table 2 is missing even on an included page.
- Preserve the existing PyMuPDF analysis stack; do not introduce another OSS dependency without audited exact-source/column/numeric gain, zero supported-finding regression, and full-pipeline latency/memory/failure/provider-cost acceptance on held-out sources. Require independent human gold; assistant drafts are not independently human-reviewed.
- Previously explored but untested Docling, MinerU, Unstructured and Science Parse are deferred without conclusions about performance. Avoid speculative candidate expansion.
- Experiment code and runners stay outside production. Direct future work to existing-engine evidence fidelity, 18 review findings, operational telemetry and beta reliability.
- See `docs/OPEN_SOURCE_ADOPTION_DECISION_2026-11-16.md` for pre/post extraction measures and qualifications. Do not interpret historical v6.3.9 scores as a fresh evaluation of the currently deployed v6.4.2 source.

## Full-model Docling Parse A/B and source-evidence compatibility gate (2026-11-17)

- Existing PaperSignal production engine remains frozen at `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, analysis source `v6.4.2`. Do not edit deployment or publish unapproved parser changes.
- Fresh full Gemini A/B failed on B01/B03 due primary/fallback HTTP 503. No successful paired new AI analyses. Gemini synthetic probe does not qualify as full end-to-end test.
- An authorized, model-free replay of identical previously saved v6.3.9 claims through the frozen v6.4.2 verifier found Docling Parse citation regression on all ten PDF papers: 296/346 citations vs PyMuPDF 346/346, 6 fewer evidence-qualified findings and 3 fewer current-screen-passed findings. Docling Parse also took 4.125× PDF-parser wall time and greater child RSS in the isolated run. The earlier 95.52% token-recall proxy is not a product quality win.
- **Do not replace PyMuPDF with the current Docling Parse integration.** Any retry requires restored provider reliability, same-model complete paired analysis, independent page/table gold, zero existing-claim/citation regression, and acceptable full-service resource/cost overhead. Assistant drafts and lexical screen checks cannot certify human precision.
- Test code, private source artifacts, and metrics are retained in experimental branches. Benchmark model opt-in is disabled pending new explicit request.
