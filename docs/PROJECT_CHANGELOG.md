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
