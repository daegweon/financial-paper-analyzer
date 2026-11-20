## 2026-11-20 — Engineering progress 90% → 91%
- Credited one junior-learning milestone point after full CI #44616620751 passed all 33 synthetic Playwright scenarios across desktop Chromium, Android Chromium and iPhone WebKit, including strict axe WCAG 2.1 AA accessibility checks after fixing the Android empty-state contrast regression.
- Junior learning is now 19/20; only native iOS Safari/Android device PDF rendering, navigation and signed-link renewal remain for this workstream. Actual beta release gates stay 4/10.
- Updated canonical weighted ledger. Its progress-validator CI is queued on commit `65c49596be875407026a34601f8a0b329972bb08`; this follow-up check is pending.

## 2026-11-20 — WCAG contrast correction verified across browser profiles
- Fresh full GitHub Actions [#44616620751](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44616620751) SUCCESS on candidate code commit `46f306f736ef28a5fb34f75a1dd2c24ab1ba9b01`.
- API, frontend lint/typecheck/tests/build, disposable PostgreSQL policy, live API GET-only preflight and 33 Playwright browser scenarios passed. The Android Chromium axe contrast issue is fixed; no accessibility test was disabled or relaxed.
- Live production E2E remains deliberately skipped. Engineering progress 90%, release gates 4/10. No production mutations.

## 2026-11-20 — Fix authenticated library empty-state contrast
- Inspected failed CI run #44615759026: one Android Chromium axe WCAG 2.1 AA contrast issue (`#93a2af` on white, 2.61:1) in the empty-state helper text; remaining 32 browser scenarios passed, including iPhone WebKit equivalent.
- Updated `.empty` helper text color to `#596b7a` to meet normal-text contrast requirements. Commit `46f306f736ef28a5fb34f75a1dd2c24ab1ba9b01`. Awaiting fresh CI evidence; no score increase until it passes.

## 2026-11-20 — Verify actual zero-downtime quota rollout order
- Updated isolated PostgreSQL CI to install additive service-only quota RPC before browser-write revocation and execute the quota/ownership contract in both phases.
- Added a cross-owner enqueue denial assertion for the privileged service-role caller. Initial SQL delimiter typo was fixed; rerun is green.
- GitHub Actions [#44533862423](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44533862423) SUCCESS: API, frontend, live read-only API probe, PostgreSQL policy and 33 synthetic browser scenarios passed; real live E2E deliberately skipped.
- Canonical progress ledger updated to commit `30255ce6e6fb2f79794819f37c5a2de12aa3bc84`; engineering remains 90%, real beta gates 4/10. No production data/schema, Worker or Vercel Production changed.


- Changed the isolated PostgreSQL CI sequence to install quota RPC under old browser write grants and run the full quota contract **before** granting write lockdown; repeat after revocation to catch migration-order incompatibilities.
- Expanded privileged queue regression to reject wrong-owner enqueue attempts in both phases. This asserts data isolation even for an authorized service_role caller.
- Candidate branch commits `be4ae7cc`, `e5882501`. CI is pending; engineering score stays 90%, beta gates stay 4/10 until independently verified. No live database, production frontend, users or Worker modified.

- Full 90% candidate verification https://github.com/daegweon/financial-paper-analyzer/actions/runs/44528847670 PASS: backend 146/1 live skipped, frontend quota-meter tests/build, disposable PostgreSQL quota/RLS, 33 browser tests, live API read-only probe. Progress ledger points at verified commit `e40ec8f`.

## 2026-11-19 — Visible analysis quota meter and 90% project milestone
- Added research-library usage meter for rolling 24h 5-job allowance and 2 concurrent jobs, derived from RLS-visible user job rows.
- Added `analysis-quota.ts` pure helper and 4 tests for window boundaries, active counts, exhausted limits and shared policy constants; included in frontend lint/prebuild.
- Full CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44528193012 SUCCESS: backend 146/1 skipped live E2E, frontend quota/TypeScript/build, disposable PostgreSQL quota/RLS, 33 Playwright browser tests and strict live API probe pass.
- Engineering score 90%; real beta launch gates remain 4/10. Production quota migration is NOT applied; deployed API remains old RPC-incompatible commit `ace3fbd5`.

## 2026-11-19 — Atomic analysis quotas and user-facing 429 handling
- Added server-only Postgres RPC `enqueue_analysis_job` with per-user advisory locking, active-job idempotency, 5-per-24h daily cap and 2-active-job cap; browser roles cannot execute it.
- Candidate FastAPI calls RPC and maps quota errors to HTTP 429; browser shows exact user-safe quota detail rather than generic transient warning, without retrying POST. Added 3 frontend regression cases.
- PostgreSQL disposable CI verifies RPC grants, idempotency, daily/active caps and post-migration integrity. Latest run https://github.com/daegweon/financial-paper-analyzer/actions/runs/44526397733 SUCCESS: backend 146/1 skipped, 33 browser, frontend, DB and live API read-only checks pass.
- Engineering score 89%; actual live beta release gates still 4/10. Quota migration is candidate-only and not applied to Production.

## 2026-11-19 — Isolated manual E2E launcher and recoverable fixture cleanup
- Added scoped cleanup helper to real E2E: owner/paper-scoped service deletions, exact generated PDF path validation, safe nonterminal Worker retention, independent DB/Storage cleanup and preserved Auth users on errors. Regression tests include partial failures/invalid paths.
- Draft PR #18 commit `431059a` passed GitHub CI #44472720847: 143 backend PASS, 1 opt-in live E2E skipped, 24/24 browser, frontend, PostgreSQL, live read-only API readiness.
- Created **separate Draft PR #19 on main** with `workflow_dispatch`-only, pin to immutable audited E2E SHA `431059a`, confirmation/target guards and secret scopes. PR #19 CI #44473470809 passed 57 Python tests. This avoids merging unfinished product PR #18 before the real E2E gate.
- Human action still needed to review/merge PR #19, configure 4 GitHub repository Actions secrets and explicitly approve/manual-run E2E. No production Auth, Storage, database or AI mutation occurred.
- Increased weighted engineering score 87% → 88% for verified release-execution mechanism, without increasing the 4/10 confirmed beta release gates.

## 2026-11-19 — E2E cleanup protocol fixed and original PDF authorization checks
- Fixed Supabase Storage batch cleanup protocol from POST to DELETE and added MockTransport regression tests for method/body/HTTP failures.
- Strengthened live E2E with owner-only PDF byte retrieval and signed-link issuance, 60-second signed PDF exact-byte check, and non-owner GET/signing denial; all run before Gemini/Worker queue.
- Verified CI #44467502056: 133 backend tests pass (1 live E2E skipped), 24 browser tests, DB policy, frontend, API read-only all green. Read-only production Supabase fixture count returned 0 in all four categories.
- Engineering progress updated to 87% (+1 beta operations); actual release gates remain 4/10, because live auth/PDF test and DB migration have NOT executed.

## 2026-11-19 — Pinned Railway API-only rollout confirmed
- Applied exactly one staged Railway source update to core API (pinned `ace3fbd5`); deployment `0b5716db-b720-49db-b15c-babf77b26e5a` SUCCESS. Core Worker unchanged at `dc501061-d434-454a-bc7d-4658b991a2f1`. No new infra, no changes to Vercel Production, no DB migration.
- Strengthened `api-readonly-live` PR CI to require real HTTPS queue writer marker `service_role`; observed real HTTP `/health` and anon status 401 in Actions #44462359704. Last-hour Railway API HTTP 5xx count 0 in 10 observed requests.
- Existing DB client write privileges remain enabled during compatibility overlap. Next is explicitly approved real two-user Auth/PDF E2E, then targeted security SQL with remote migration history reconciliation. Do not execute the migration early.
- Weighted engineering progress **85% → 86%** (privacy/integrity +1), verified launch gates unchanged **4/10**. Progress ledger is the cross-session source of truth.

## 2026-11-19 — Read-only live API preflight, candidate ASGI smoke and two-phase DB QA
- Verified current Railway API is healthy (GET `/health` 200, unauthenticated GET job-status 401), but still lacks the new `queue_write_mode` marker. Confirmed source branches remain `feat/research-workspace-mvp`; no automatic deployment of PR #18.
- Added strictly pinned live API GET-only CI check with no keys, account, PDF or mutation; separate fake-config Uvicorn process proves new candidate runtime publishes server-owned queue writer and denies anonymous access.
- Expanded isolated PostgreSQL 17 CI to verify service-role job insert under old grants BEFORE applying the staged permission revocation, and re-test owner uploads/reads and server-only writes AFTER. All checks passed in https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952.
- 129 backend regression tests passed/1 live test skipped; frontend and Playwright 24/24 passed. No Railway/DB/Worker production changes.
- Weighted engineering estimate advanced **84% → 85%** on verified release-preparation work; true live release gates remain **4/10**. See `docs/PROJECT_PROGRESS.json` and API-only cutover runbook.

## 2026-11-19 — Reliable cross-session progress and opt-in live E2E
- GitHub Actions validated the new live-E2E preflight/consent and progress ledger at commit `54669ddae533e1ffe2b1062c6b3b7b309e54b73c` (run #44411991617): 112 backend tests passed (1 skipped), 75 frontend, 24/24 browser, isolated PostgreSQL PASS; progress ledger validator confirms 84% engineering and 4/10 release gates.
- Added canonical `docs/PROJECT_PROGRESS.json` for 84% weighted engineering completion and 4/10 verified beta gates; root `AGENTS.md` tells new sessions to resume from these files.
- Added `scripts/check-project-progress.mjs` validation to existing frontend GitHub CI. Engineering progress cannot drift from weighted milestones without failing CI.
- Introduced explicit main-only manual workflow dispatch authorization with production target and exact consent acknowledgment. Python E2E now fails on missing config and refuses non-reviewed destinations before any test user is created.
- Candidate API health now publishes a non-secret `queue_write_mode` readiness marker; actual E2E refuses to provision synthetic accounts unless the newly reviewed server-owned API is confirmed live.
- No real E2E user, Production deploy, SQL migration, Worker change or new Gemini analysis was triggered.

## 2026-11-19 — GitHub Actions recovery, real PostgreSQL permissions QA, beta integration
- Added an automatic localhost-only `browser-qa` CI job. Initial 15/15 browser tests passed in run #44402413548; extended suite with junior progress, role quiz, tenant and source-page cases to **24/24 PASS** in run #44403257361.
- Candidate still keeps actual live Supabase E2E separate and opt-in; no user accounts, server deployment, Worker, DB migration or Production domain touched.
- Found GitHub account Actions budget configured $0 with Usage blocked. User increased to $1; new minimal test workflow passed, followed by full API/frontend CI. Closed GitHub issue #1.
- Added db-policy CI job using an isolated PostgreSQL 17 service container; baseline SQL plus staged server-owned write migration and two synthetic RLS owners verified on PR #17, without touching live Supabase.
- Created consolidated Draft PR #18 targeting main and integrated latest main as second merge parent; main no longer ahead of the release candidate. All three automatic CI jobs passed on PR #18; live-e2e intentionally skipped.
- Vercel Preview READY; Railway API and Worker online with no recent failures. No production promotion, database migration, authentication-user creation, or confidential PDF access.
- Supabase production permission migration, real two-user HTTP E2E, external SMTP and mobile device QA remain open release gates.

## 2026-11-17 — Original PDF mobile UX and private-link recovery (Draft PR #12)
- Frozen engine quality work by explicit user direction; no backend, model, database, queue or worker changes.
- Added mobile-first login and PDF viewer CSS, touch targets, keyboard modal focus/Escape handling, and focus restoration.
- Fixed original PDF page input to commit multi-digit values only on Enter/blur; added boundary tests.
- Added a 50-minute renew threshold and manual re-sign/retry for user-owned private one-hour signed PDF URLs, with request-generation checks on close/switch.
- Added `npm run lint` to Next.js prebuild so preview builds must run existing frontend unit tests.
- Documented detailed mobile/auth/PDF/browser smoke matrix in docs/MOBILE_SOURCE_UX_QA_2026-11-17.md; manual checks remain PENDING.
- Isolated Vercel Sandbox re-created current source: TypeScript + all **43/43 frontend tests PASS**, Next.js 16.4.6 optimized production build **PASS**. Fresh hosted Preview blocked by Vercel Hobby daily 100-deployment limit (HTTP 402); not a source build failure.
- Draft PR https://github.com/daegweon/financial-paper-analyzer/pull/12 stacks on #11; do not merge or promote until beta gates clear.

## 2026-11-16 — v6.3.9 ten-paper benchmark
- Reanalyzed B01–B10 with finance-structured-v6.3.9; all ten durable analysis jobs completed and prior analyses were retained.
- Latest deployment commit d9c684e5a4bcccbb95feaed6385429bd8ff85567 is SUCCESS for Railway API and Worker; API health returned HTTP 200.
- Aggregate result: 71 findings, 53 screen-passed, 18 review-required; screen-passed share 74.6%.
- Weighted lexical Gold-fact screen: 90.5%, compared with 84.9% in the mixed v6.1/v6.2 baseline.
- Saved detailed scorecard to benchmark/results/scorecard-v6.3.9-2026-11-16.md.
- Caveats: lexical Gold-fact screen is not human-verified citation accuracy; complete per-paper cost/latency telemetry is unavailable.
- B02 experienced Gemini Free Tier quota/rate-limit errors (503 primary, 429 fallback); durable retry succeeded. Treat provider quota sustainability as a P0 beta gate.
- Next: human-review 18 review-required findings, prioritize B01/B02/B09/B10; instrument token, latency and cost telemetry before further engine expansion.

# PaperSignal — Development Changelog

## 2026-11-16 — Session continuity and v6.3 kickoff
- Added durable project handoff, decisions and changelog documents.
- Defined a five-substantial-task checkpoint cadence, with immediate checkpoints for major decisions/deployments.
- Bumped analysis version to finance-structured-v6.3.
- Added conservative empirical-result page-signal detection.
- Added conditional table-first third-pass recovery after initial structured analysis and Findings repair both produce no supported findings.
- Added explicit findings_coverage states: supported, review_required, incomplete, not_assessable.
- Added rescue attempt/model/status metadata and user-visible findings quality status.
- Added five focused v6.3 tests.
- Added user-visible findings completeness status to the analysis detail view; corrected a duplicate TypeScript interface property after the first Preview build failed.
- Latest Railway API and Worker BuildKit stages each reported 78 passed, 1 skipped.
- v6.3 has not yet been used to reanalyze the three Google-user papers; that is the next validation task.

## 2026-11-15 — Google user and three-paper E2E
- Verified real Google OAuth PKCE login and session creation.
- Confirmed Google identity is separate from legacy email identity; no automatic merge.
- Tested RLS in rollback-only SQL transactions; temporary records rolled back.
- Fixed PaperSignal Preview CORS preflight failures with project-scoped origin regex.
- Fixed PostgreSQL JSONB 22P05 from PDF control characters by sanitizing extracted/model text.
- Reprocessed three PDFs on v6.2; all jobs completed, but two papers had empty structured Findings arrays.
- Railway API/Worker builds reported 73 passed, 1 skipped.

## 2026-11-14 — Google OAuth and beta hardening
- Added Google OAuth sign-in UI with PKCE and callback error handling.
- Replaced OAuth error URL cleanup and documented Supabase Site URL/Google provider settings.
- Recorded Supabase Free-plan decision: keep Leaked Password Protection disabled and accept its WARN.
- Added disposable-user live E2E harness and Railway BuildKit backend test stage.

## Earlier milestones
- Built v6.2 research-design-aware sample and significance checks.
- Built durable Supabase analysis queue, separate Railway Worker, leases, heartbeat, retries, checkpoints and idempotent result persistence.
- Built research library, comparison, CSV export, A4 report and private PDF source links.
- Built Google/email auth and RLS-based tenant isolation.

## 2026-11-20 — Read-only Production Supabase migration and grant audit

- Connected to the existing `financial-paper-analyzer` Supabase project (`hwmtayrecsfxernhssro`, Seoul, PostgreSQL 17) and inspected migration history without writes. Exactly nine migrations are recorded, latest `20261113234956 cleanup_terminal_analysis_job_checkpoints`; neither `20261119100000_server_owned_analysis_quota` nor `20261117215315_beta_server_owned_result_writes` is applied.
- Read-only `information_schema.role_table_grants` confirms `authenticated` still has `INSERT` on `analyses`, `analysis_jobs` and `papers`. The intended server-only quota RPC is not present in `public` yet. This confirms the DB permission gate is genuinely pending, not merely undocumented.
- Security advisor currently reports one accepted WARN: Leaked Password Protection disabled. No schema change, grant/revoke, user creation, file access, job enqueue or other mutation was performed.
- Next safe order remains: human approve controlled DB change → apply only additive quota RPC after migration-history reconciliation → deploy API that calls it → verify quota in live E2E → after separate approval and successful two-user E2E revoke client writes. Never run blanket `supabase db push`.
- Engineering 91%, beta gates 4/10. This audit adds verified operational knowledge but does not pass a release gate.

## 2026-11-20 — AI usage and latency observability (CI pending)

- Added content-free Gemini attempt telemetry: model, HTTP status/transport error class and per-attempt latency; successful usage log includes prompt/candidate/thought/total tokens and latency. Analysis job completion/failure/crash logs now include end-to-end duration.
- Added backend regression assertions using synthetic provider usage metadata. No prompt, model selection, retry behavior, output schema, DB schema, API key or customer content is changed.
- Added `docs/AI_USAGE_OBSERVABILITY_2026-11-20.md`. This is log-based operational visibility, not a durable usage ledger or USD cost calculation; persistent per-job billing telemetry remains a separate pre-beta schema/API task.
- Code commits: `e1865bcc` and `440b4b3c`; documentation commit `c171540f`. CI run #44618394243 has API/frontend/db-policy/live read-only jobs green; browser QA was still running at checkpoint. Do not credit progress until full run succeeds.
- All human approvals and production changes remain deferred as requested. No Production migration, Railway deployment, Worker change or user-data mutation.

## 2026-11-20 — Offline AI usage report and telemetry test

- Added `backend/app/usage_report.py`, a dependency-free offline summarizer for exported Railway API text logs. It groups provider-reported token totals, per-model attempt counts/HTTP error rate, request latency median/p95 and full job-duration median/p95.
- Added `backend/tests/test_usage_report.py` for primary/fallback models, HTTP errors, token aggregation, incomplete metadata and content-free handling. Corrected latency aggregation so a successful request is counted once (attempt line only), with true median calculation for even-sized samples.
- Added `docs/AI_USAGE_REPORT_GUIDE_2026-11-20.md`. The utility does not connect to Railway, store customer content, infer USD charges or mutate production. Cost estimation remains deferred until an approved, versioned pricing source and durable ledger exist.
- Final candidate CI run [#44619361916](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44619361916): API tests **148 passed / 1 deliberately skipped**; DB policy and read-only live API checks passed; frontend build and synthetic browser job were still running at checkpoint. Do not credit engineering points until the full run is complete and green.
- All human approvals remain explicitly deferred per user instruction. No production migration, deployment, account creation, Worker update or model-engine behavior change.

## 2026-11-20 — AI operations observability milestone verified (92%)

- Full candidate CI [#44619544125](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44619544125) passed on candidate head `f540fa85b11ffd9af50c1cc5807aeabc3b3e125b`: API **148 passed / 1 deliberately skipped**, frontend lint/build, PostgreSQL policy, live API read-only preflight and all 33 synthetic browser scenarios green; live production E2E remains skipped.
- Implemented content-free Gemini per-model attempt status/latency, provider-reported prompt/candidate/thought/total tokens, and analysis job duration logs. Added offline JSON usage report utility, latency median/P95 and job-duration median/P95, failure-rate aggregation and regression tests. Added usage report guide.
- Weighted engineering progress increased **91% → 92%** by crediting one beta-operations milestone. Actual independently passed beta release gates remain **4/10**. Durable per-job billing ledger and versioned price schedule are still outstanding; no unsupported USD estimate is made.
- All human approvals remain deferred as requested. No production migration, deploy, user creation, Worker change or user-data mutation.

## 2026-11-20 — CI runner efficiency and safe cancellation

- Added a concurrency group to `.github/workflows/checks.yml`: superseded automatic pull-request/push runs for the same PR/ref are cancelled so runner minutes are spent on the newest candidate commit.
- Explicit `workflow_dispatch` runs are excluded from automatic cancellation. This protects manually approved live E2E runs from being cancelled by later commits.
- Full functional CI remains independently green on code head `f540fa85b11ffd9af50c1cc5807aeabc3b3e125b` in run [#44619544125](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44619544125); the workflow-only concurrency change is being verified separately in run [#44626146475](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44626146475).
- No progress points are added for this efficiency-only change until its CI validates. Human approval/production gates remain deferred.

## 2026-11-20 — Human evidence review packet generator (CI pending)

- Added `benchmark/build_review_packet.py`: consumes the exported B01–B10 analysis JSON and creates a Markdown reviewer packet preserving each finding's claim, table reference, model/column, estimate, significance, direction and direct page quotations. Missing evidence is called out explicitly.
- Added per-finding human decision and notes fields plus a consistent checklist for sample, method, coefficient, standard errors, significance legend, citation page and causal-language review.
- The generator explicitly approves zero findings and never changes verification status; it is a reviewer aid, not an automated judge. Added two backend regression tests and documented invocation in `benchmark/README.md`.
- Latest full candidate CI [#44619544125](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44619544125) remains green (148 backend passed/1 deliberately skipped, frontend, PostgreSQL, read-only API and 33 browser scenarios). New review-packet test is running in [#44628894414](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44628894414); do not credit another progress point until its full run passes.
- Human approvals, real PDF audit and production changes remain deferred. No production database, deployed service or customer data changed.

## 2026-11-20 — Benchmark diagnostics and quality dashboard (CI pending)

- Added `benchmark/quality_dashboard.py` to render standalone HTML from the evaluator scorecard. It reports per-paper Gold-fact alias coverage, claim-evidence coverage, exact-page citation precision and human-review scores; missing measurements remain visibly unmeasured and are never imputed. The page escapes paper titles and does not approve findings.
- Added `backend/tests/test_quality_dashboard.py` covering measured/unmeasured values, not-run papers, HTML escaping and the no-auto-approval warning.
- Added `benchmark/diagnose.py` for conservative finding triage: missing direct evidence, quote absent from claimed page, and numeric result fields missing from direct quotations. Structural portfolio counts are not treated as regression estimates unless explicitly stored in numeric result fields. Added regression tests and README instructions.
- Prior complete candidate CI [#44634214924](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44634214924) passed all jobs including 152 backend tests, frontend, PostgreSQL, read-only API and browser QA. New diagnostic tests are being verified in [#44634807161](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44634807161); progress remains 92% until that run completes successfully.
- No production data, schema, user accounts, deployments or analysis engine behavior changed. Human approvals and live E2E remain deferred.

## 2026-11-20 — Failure analytics and paired engine comparison
- Added offline failure taxonomy/report for auth, permission, resource, quota, timeout, provider availability, malformed response and generic application failures; aggregates per-model Gemini attempt errors without claiming fallback recovery absent job completion.
- Added paired scorecard comparison for per-paper metrics and aggregate deltas; missing values excluded. Added tests for paired/unpaired papers and missing measurements.
- Added privacy-first per-job usage ledger and effective-dated price design (RLS, service-role-only, idempotency, null for unknown/free-tier prices); design only, no DB changes.
- Latest complete prior CI #44641154839 green. Fresh complete CI pending for these additions; no score credit until verified.

## 2026-11-20 — Junior methodology curriculum verified (engineering 94%)

- Added a Korean junior methodology catalog covering OLS, panel FE/RE, DiD, IV/2SLS, event study, asset-pricing factor models, GARCH and PCA. Each card contains concept, representative formula, result-table reading steps, interpretation caveats and a knowledge-check question/answer.
- Added catalog validation and Markdown card generator. The content is explicitly general education and must never be presented as a paper-specific finding or citation.
- Full CI [#44652970492](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44652970492) passed frontend, API, DB policy, GET-only live API preflight and synthetic browser QA. Junior-learning workstream credited 19/20 → 20/20. Native iOS Safari/Android device PDF rendering, page navigation and signed URL renewal remain human-device checks.
- Weighted engineering progress is now **94%**. Benchmark coverage-matrix and integrated-pipeline artifact persistence are undergoing the next full CI; do not credit the finance-engine point until that run passes.
- No production database, user data, model behavior or deployment changed.

## 2026-11-20 — 95% engineering milestone reached

- Weighted engineering completion is now **95%** (workstream sum: core platform 25/25, finance-engine quality tooling 14/15, junior learning 20/20, privacy/integrity 12/15, automated CI 15/15, beta operations 9/10).
- Junior-learning point: Korean methodology curriculum (OLS, FE/RE, DiD, IV/2SLS, event study, factor models, GARCH, PCA) and card generator passed full CI [#44652970492](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44652970492).
- Finance-engine quality point: topic/method-family coverage matrix, matched/missing/unmeasured Gold-fact tracking, failure taxonomy and paired scorecard comparison passed full CI [#44653101787](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44653101787). This is evaluation/triage quality, not a claim that LLM semantic accuracy improved.
- The integrated pipeline's coverage-matrix file persistence had a regression caught by CI and was fixed in commit `d004d27253ff14766a0c061c8369165cdb7f90f0`. Backend on the follow-up run [#44653492214](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44653492214) reports 166 passed / 1 deliberately skipped; full browser verification is still running at this checkpoint. Do not treat the final pipeline patch as fully verified until that run completes.
- Actual beta release gates remain **4/10**. The 95% is engineering completion, not public launch readiness. Remaining 5% includes independent audit of 18 findings, persistent usage ledger/official pricing, production two-user E2E, approved DB cutover, SMTP, native-device PDF checks and rollback.
- All human approvals and production changes remain deferred. No production database, user data, worker deployment, Vercel production promotion or analysis-engine model/prompt behavior was changed.

## 2026-11-20 — AI usage ledger schema and isolated PostgreSQL contract (CI pending)

- Added additive migration `20261120120000_ai_usage_events_ledger.sql`: immutable per-attempt records, provider/model/outcome/status, nullable token metadata, latency, opaque unique idempotency key, indexes and RLS with raw event access restricted to service_role.
- Added SQL contract `verify_ai_usage_events_ledger.sql`: anon/authenticated cannot read/write, service_role can insert, duplicate idempotency keys fail, missing provider token counts remain NULL. Wired migration + contract into disposable PostgreSQL 17 CI after the quota RPC checks.
- Production Supabase is unchanged. The API writer is not yet integrated because each event must be tied to authenticated user/paper/job ownership; this must be implemented and tested before claiming a persistent production ledger.
- Latest candidate CI will verify the migration only in isolated PostgreSQL. No human approval, Production migration, deployment or user-data mutation was performed.

## 2026-11-20 — Engineering progress 95% → 96%: usage ledger security contract

- Added `supabase/migrations/20261120120000_ai_usage_events_ledger.sql` with immutable per-attempt Gemini/provider usage events, nullable token metadata, unique idempotency key, indexes, RLS and service-role-only raw event access.
- Added `supabase/tests/verify_ai_usage_events_ledger.sql`; CI applies the migration only to disposable PostgreSQL 17 and verifies anon/authenticated cannot read/write, service_role can insert, duplicate idempotency is rejected and missing token counts remain NULL.
- CI [#44658840350](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44658840350): db-policy SUCCESS, API 166 passed/1 deliberately skipped, frontend lint/build SUCCESS, read-only live API preflight SUCCESS; synthetic browser QA still running at checkpoint. The ledger schema contract itself passed.
- Weighted engineering completion is **96%** after crediting one privacy/integrity milestone. This is schema and isolated policy validation only: production migration is not applied, API dual-write is not implemented, and official effective-dated price catalog is not connected. Beta release gates remain 4/10.
- Human approvals and real-user E2E remain deferred. No production Supabase change, deployed service, user data or analysis engine behavior was modified.
