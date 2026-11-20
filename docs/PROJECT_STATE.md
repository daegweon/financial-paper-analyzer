# PaperSignal — Current consolidated checkpoint (2026-11-20)

**Engineering completion: 98%. Independently passed release gates: 4/10.** The 98% score is weighted engineering completion, not launch readiness.

- Candidate branch `release/beta-candidate-20261119`, Draft PR #18, exact HEAD `4228494d5465cb8b61003ec25c8748a27cff7819`.
- Exact-head Checks [#44677027806](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44677027806) passed API, frontend, disposable PostgreSQL 17 (including the AI usage-ledger migration contract), GET-only live API preflight and synthetic browser QA. The live production E2E job was skipped.
- Vercel Preview is READY for current candidate frontend code SHA `0cdf4fed96df40521a99c5969e3d3703bebde8a8`: deployment `dpl_HTsQiR2ykz72x7q6xE7c5Ww3yTht`, [open Preview](https://financial-paper-analyzer-nwik7wcju-daegweonai-9583.vercel.app). Exact-head GitHub Checks [#44683909825](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44683909825) passed API, frontend, disposable PostgreSQL, GET-only live API preflight and synthetic browser QA; live production E2E remains skipped. Release gates are now 4/10.
- Production Railway API: service `81b678e2-7136-436d-9058-7d20647dc1b7`, deployment `0b5716db-b720-49db-b15c-babf77b26e5a`, commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732`, SUCCESS. Current live rollback baseline is that same deployment; previously listed `17c9134b-f49c-4358-a879-7ca77b55b936` is REMOVED and cannot be used.
- Worker remains unchanged: service `238af942-0628-47d5-9280-04a49373423f`, deployment `dc501061-d434-454a-bc7d-4658b991a2f1`, commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, SUCCESS.
- Read-only Production checks: Railway API recorded 446 requests / 0 server errors / 219 client errors / p99 9 ms over 24 hours. Supabase has 9 migrations through `20261113234956`; `ai_usage_events` and `ai_admin_settings` are absent. No Production migration or candidate API rollout was performed.
- Railway currently has no admin UUID allowlist, global monthly AI budget variable or explicit Gemini billing-mode variable. The admin console and persistent ledger remain candidate-only; budgets are administrator-only, service-wide settings.
- Article-level license statements have now been checked in all ten supplied benchmark PDFs: nine MDPI PDFs explicitly state CC BY 4.0 and the PLOS ONE PDF states CC BY. Attribution and third-party-material limitations are documented in `benchmark/results/license-audit-2026-11-20.md`.
- Latest stored B01–B10 analyses are mixed-version (3 × v6.4.0, 1 × v6.4.2, 6 × v6.3.9): 63 findings, 57 `screen_passed`, 6 `review`. The six current review records received an assistant second-pass PDF audit at `benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md`; no database status was changed and human sign-off remains.
- Supabase advisors: no performance findings; one security warning for disabled leaked-password protection. It was not changed because it affects signup policy and requires an administrator decision.
- Human-only steps are listed in `docs/HUMAN_E2E_HANDOFF_2026-11-19.md`. Keep PR #18 Draft and the finance analysis engine frozen.

---


## 2026-11-20 — Automated accessibility milestone credited

- Full cross-browser CI [#44616620751](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44616620751) passed: all 33 Playwright synthetic browser scenarios across desktop Chromium, Android Chromium and iPhone WebKit, alongside API, frontend and PostgreSQL checks. The Android WCAG 2.1 AA contrast regression is fixed with strict axe assertions unchanged.
- Weighted engineering completion is now **91%** (up from 90%) because the automated cross-browser accessibility milestone is independently verified. The junior-learning workstream is 19/20; the remaining point is real iOS Safari/Android device PDF rendering, navigation and signed-link renewal.
- Actual beta release gates remain **4/10**. This engineering score is not live launch approval. Real two-user E2E, production quota migration, SMTP, native devices, rollback and research audit/budget remain outstanding.
- Progress ledger validator CI for updated score is running on commit `65c49596be875407026a34601f8a0b329972bb08`; do not claim that validation run is green until its result is confirmed.

## 2026-11-20 — Cross-browser accessibility fix verified

- Candidate commit `46f306f736ef28a5fb34f75a1dd2c24ab1ba9b01` passed full GitHub Actions [#44616620751](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44616620751): API, frontend lint/typecheck/tests/build, PostgreSQL 17 policy, live API GET-only preflight and all 33 synthetic browser scenarios.
- The prior Android Chromium WCAG 2.1 AA empty-state contrast regression is resolved by changing helper text from `#93a2af` to `#596b7a`; original axe assertions remain strict. Desktop Chromium, Android Chromium and iPhone WebKit suites passed.
- Engineering remains **90%** and actual beta release gates **4/10**. This is automated synthetic-browser verification, not native device or real authenticated production E2E.
- Live E2E remains skipped pending human merge of PR #19, protected repository secrets and explicit dispatch. No production schema/data, Worker or Vercel Production change.

## 2026-11-20 — Accessibility regression fix (verification pending)

- Latest candidate CI run `44615759026` found one reproducible WCAG 2.1 AA contrast failure in the authenticated Research Library empty-state helper text on Android Chromium: `#93a2af` on white, 2.61:1 (required 4.5:1). The same scenario passed on iPhone WebKit; 32/33 browser cases passed on Android profile.
- Corrected `.empty` helper text to `#596b7a` in `frontend/components/ResearchLibrary.module.css` (commit `46f306f736ef28a5fb34f75a1dd2c24ab1ba9b01`). This is a focused accessibility correction, not a waiver or test relaxation. New CI evidence is not yet available; do not credit a gate or raise engineering progress until verified.
- Baseline remains 90% engineering / 4 of 10 release gates. Live E2E remains intentionally gated by PR #19 human approval and secrets.
# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-20 (Asia/Seoul)
Current consolidated candidate: release/beta-candidate-20261119 (Draft PR #18 directly against main; includes earlier stacked feature branches)
Current release candidate PR: https://github.com/daegweon/financial-paper-analyzer/pull/18 (Draft; do not merge without live E2E and production safety gates)

## Product north star

Build an evidence-first financial research workspace that accurately extracts research design, methodology, empirical findings, statistical significance and page-level PDF evidence; supports cross-paper comparison and a durable private research library. Prefer verifiable incompleteness over fabricated claims.

## Product-first priority override — 2026-11-17

**Analysis engine tuning is frozen.** Do not pursue further v6.x quality experiments unless the user explicitly lifts the freeze. Implement in this exact sequence:

1. Usability: real login, open original PDF, jump to source evidence, responsive/mobile and keyboard testing.
2. Junior-friendly interpretation of paper tables and charts, with source-grounded facts separated from generic finance education.
3. Role-specific learning paths and paper comprehension checks.
4. Beta readiness: error recovery, onboarding, accessibility, deployment and rollback.

Existing Draft PRs #8–#11 cover durable job recovery, junior learning guides, role explainers and inline source reading. New Draft PR #12 improves mobile layout, original PDF navigation input, keyboard focus and private signed-link renewal. Its code changes are not equivalent to passing live browser QA.

## Historical progress estimate — 2026-11-17 (not a current release score)

Overall: approximately 74.5% (subjective engineering feature-completion estimate, **not** live-user verification).
- Core service and user workflows: ~94%
- Authentication and tenant isolation: ~80%
- Analysis engine reliability: ~70%
- Real-user workflow verification: ~75%
- Quantitative analysis-quality benchmark: ~55%
- Public beta readiness: ~45%

Do not raise these percentages without new verified evidence. The v6.3.9 benchmark is complete, but page-level citation fidelity and independent human review remain open.

## Architecture

- Frontend: Next.js 16 / React 19 on Vercel.
- Auth, PostgreSQL and private PDF Storage: Supabase project hwmtayrecsfxernhssro, Seoul region.
- API: FastAPI + PyMuPDF on Railway.
- Durable queue/worker: Supabase job tables and independent Railway Worker.
- AI: Gemini primary gemini-3.5-flash-lite, fallback gemini-3.6-flash.
- Analysis version: current production API/Worker commit reports finance-structured-v6.3.9.
- GitHub repository: daegweon/financial-paper-analyzer.

## Verified complete

- Research library, upload, analysis history, search/sort, up-to-four-paper comparison, CSV export and A4 report.
- Private PDF Storage, signed source links, per-user RLS.
- Email/password and Google OAuth UI; a real Google PKCE login succeeded. Supabase logs recorded Google callback, token exchange HTTP 200 and user lookup HTTP 200.
- The Google identity is distinct from the legacy email identity. Legacy account has 11 papers / 44 analyses; Google account has three test papers / three analyses. Do not merge automatically.
- RLS rollback tests showed Google user can access own paper/analysis/job rows and the legacy account cannot read those rows; Google user initially sees none of the legacy account's records. Test rows were rolled back; no leftovers.
- Durable Worker: atomic claim, leases, heartbeat, retries, checkpoint resume, idempotent result persistence and terminal checkpoint cleanup.
- CORS accepts explicit origins plus a narrowly scoped Vercel Preview hostname regex for this Vercel project/team. Unrelated Vercel origins are rejected.
- PDF/model text is sanitized before JSONB persistence to prevent Postgres 22P05 from control characters.
- Three real Google-account PDFs completed v6.2 analysis: Acharya/Pedersen liquidity risk (50 of 60 pages scanned, 21 evidence quotes, 6 findings); Bank funding constraints (17 pages, 26 quotes, 0 structured findings); Monetary policy/funding cost/risk-taking (20 pages, 40 quotes, 0 structured findings). The latter two are known findings-quality gaps.
- Latest observed Railway API and Worker deployments are SUCCESS on branch commit d9c684e5a4bcccbb95feaed6385429bd8ff85567; API health returned HTTP 200.
- Reanalyzed B01–B10 on finance-structured-v6.3.9. All ten durable jobs completed; prior analysis records were retained.
- v6.3.9 ten-paper scorecard: 71 findings, 53 screen-passed, 18 review-required; screen-passed share 74.6%; weighted lexical Gold-fact screen 90.5%.
- Baseline mixed v6.1/v6.2 snapshot: 24 findings, 15 screen-passed, 9 review-required; screen-passed share 62.5%; weighted lexical Gold-fact screen 84.9%.
- Gold-fact metric is a lexical alias-presence screen, not human-verified precision/recall or page-level citation accuracy. Cost/latency comparison is unavailable because complete per-paper usage totals were not persisted.
- Worker logs showed a Gemini Free Tier quota/rate-limit event during B02; durable retry succeeded. Do not claim the Free Tier quota is sufficient for sustained public-beta traffic.

## Current in-progress work

- v6.3.9 ten-paper benchmark completed and recorded at benchmark/results/scorecard-v6.3.9-2026-11-16.md.
- Do not begin v6.4 or add broad new heuristics until the remaining 18 review-required findings receive targeted human audit.
- Prioritize B01, B02, B09 and B10 because they have the largest review-required counts (4, 6, 3 and 2 respectively).
- Validate every material coefficient, direction, p-value/significance legend, table/figure reference and page citation against the exact stored PDF.
- Inspect B02's Gemini quota/retry event and define a sustainable provider quota/cost plan before public beta.
- Capture per-job model, prompt/candidate token counts, provider attempts, wall-clock latency and estimated cost in a durable usage record before claiming cost/latency improvements.
- Preserve all historical analysis versions; do not delete or overwrite prior results.

## Known remaining work

### P0 — before public beta
1. Complete targeted human review of all 18 review-required findings, starting with B01, B02, B09 and B10.
2. Audit all material coefficient, sign, p-value/significance legend and page-citation claims against the exact PDFs; record reviewer decisions and citation-level scorecard.
3. Persist per-job model/token/provider-attempt/latency/cost telemetry and define sustainable quotas; B02 hit Gemini Free Tier quota before succeeding on retry.
4. Complete a live two-user E2E with disposable accounts and real API/Worker upload-analysis.
5. Configure custom SMTP and verify external mailbox signup/confirmation; Supabase Free built-in SMTP is limited to team-member recipients and 2 emails/hour.
6. GitHub Actions runner issue RESOLVED 2026-11-19; keep api, frontend and isolated db-policy CI green on the release candidate.
7. Verify production domain auth, Google sign-in, logout/relogin, PDF upload and analysis.

### P1 — product quality and operations
- OCR for scanned/image-only PDFs.
- Expand beyond 50 scanned pages, especially appendix/table pages.
- Paper deletion, retention and account export lifecycle.
- Usage, token/cost limits, abuse controls and operational observability.
- Model/provider quality and cost comparison.

### P2 — long-term product
- Research knowledge graph and variable/methodology index.
- Cross-paper hypothesis and findings synthesis.
- Library-wide grounded AI research assistant.
- Team workspace, role management, billing and subscription.

## Accepted product decisions

- Keep Supabase on Free. Do not upgrade to Pro solely for Leaked Password Protection.
- Leaked Password Protection stays disabled; its single security-advisor WARN is an accepted residual risk. Do not claim it is enabled.
- No automatic account merging or cross-account data migration.
- No secrets in browser code, GitHub or chat; service-role and AI keys remain server-side.
- Public papers only for Gemini Free Tier testing; never upload confidential/internal/company/customer/personal data to the free tier.
- Preserve existing papers and analyses unless the user explicitly authorizes deletion.
- Prefer user-facing result status that distinguishes job completion from extraction quality.
- The user prefers the assistant to choose the best implementation path and report outcomes rather than repeatedly ask for design opinions.

## Session startup checklist

At the beginning of every new project session:
1. Read this file, docs/PROJECT_DECISIONS.md, and the last 20 entries of docs/PROJECT_CHANGELOG.md.
2. Inspect current Git branch/PR head, Railway active deployments, latest Vercel Preview, and Supabase job/result state before making claims.
3. Compare live code with this handoff. If they differ, update this state document first.
4. Continue the next P0 task unless the user explicitly changes priorities.

## Checkpoint cadence

Update PROJECT_STATE.md and append PROJECT_CHANGELOG.md:
- every five substantial development tasks/conversation turns;
- immediately after architecture/provider/schema decisions;
- after every production deployment, migration, or user-data E2E;
- before a session handoff.

## 2026-11-17 — New session handoff: Draft PR #12

- Branch: `feat/mobile-pdf-reading-recovery`, Draft PR: https://github.com/daegweon/financial-paper-analyzer/pull/12, based on #11.
- Client-only changes: compact mobile login, responsive PDF controls, dialog keyboard focus/close, page-field commit-on-blur, signed-link refresh/retry, stale request guards.
- `frontend/package.json` prebuild executes all TypeScript and frontend unit tests; PDF regression suite now includes multi-digit input and link-expiry cases.
- QA instructions: `docs/MOBILE_SOURCE_UX_QA_2026-11-17.md`. **Real authenticated mobile browser and citation navigation are PENDING**; no production promotion.
- Keep engine frozen and beta release gate 0/4. Preserve the 74.5% feature-completion estimate until real QA validates this milestone.

## 2026-11-17 — Preview availability blocker

The account reached Vercel Hobby's daily 100-deployment API limit (HTTP 402 `api-deployments-free-per-day`). The latest confirmed READY Preview corresponds to an intermediate Draft PR #12 commit `b7b95984`, not the final source. Final branch was copied to an isolated Vercel Sandbox and passed Next.js 16.4.6 production build, TypeScript and **43/43 frontend unit tests** (auth 5, analysis 13, junior 7, workplace 13, PDF 5). **Fresh Vercel Preview and real-browser QA are still pending**; do not claim beta readiness or release. No production deployment was made.

## 2026-11-19 — Current authoritative release candidate checkpoint

- Active integration PR: https://github.com/daegweon/financial-paper-analyzer/pull/18 (Draft, base main). The latest main was integrated with an actual two-parent merge commit fa526369; main...candidate is 0 commits behind. Earlier Draft PRs #10–#17 remain unmerged historical work branches.
- GitHub Actions startup_failure **RESOLVED**: GitHub personal account had Actions budget $0, usage blocked. User changed it to $1. The minimal runner passed (https://github.com/daegweon/financial-paper-analyzer/actions/runs/44368096096) and full GitHub PR Checks passed (https://github.com/daegweon/financial-paper-analyzer/actions/runs/44370323274). The GitHub runner issue #1 is closed.
- CI contains three automatic jobs: api pytest, frontend TypeScript/tests/Next.js build and isolated PostgreSQL 17 db-policy using real baseline SQL+migration and synthetic tenant data. All three passed. Opt-in live-e2e remains SKIPPED on PR runs, not falsely marked PASS.
- Vercel release-candidate Preview READY at commit fa526369 (protected by Vercel SSO). Production/main and the public domain were not changed.
- Railway production API and Worker online; recent 24-hour failures = 0, no staged changes. Core API/Worker deployments remain the previous production versions, not the release-candidate backend code.
- Supabase project hwmtayrecsfxernhssro has security WARN only for Leaked Password Protection disabled (previously accepted Free-plan limitation); health advisor has 0 findings. Production client grants still allow direct analyses/job INSERT and paper status UPDATE: **the staged security migration has NOT been applied**.
- Staged migration supabase/migrations/20261117215315_beta_server_owned_result_writes.sql must be applied ONLY AFTER the new API server-role job creation flow is deployed and verified. Existing live migration history versions do not match the repository's earlier baseline filenames. Never execute a blanket db push.
- Browser QA 15/15 tests passed in local isolated Chromium/WebKit synthetic scenarios, not live OAuth or private PDF. The actual two-user authenticated HTTP E2E, external SMTP signup, Safari/Android devices, source PDF rendering, 50-minute signed-link refresh and rollback rehearsal remain PENDING.
- Keep financial analysis engine improvements frozen. Product completion and evidence-grounded junior learning remain priorities. See docs/RELEASE_CANDIDATE_GATES_2026-11-19.md for current gate matrix; earlier snapshot numbers and references to #12 are historical only.

## 2026-11-19 — Automated beginner study-path browser regression gate

- Release candidate PR #18 automatically executes 24 Playwright UI scenarios as a separate GitHub `browser-qa` job: 8 each on desktop Chromium, Android-emulated Chromium and iPhone-emulated WebKit, using strict localhost-only synthetic Supabase routes.
- Added junior learning-path acceptance tests: four-step progress persists when reopening A's paper, account B remains isolated, role changes preserve independent progress, four-question quiz can grade and reset, and study-path source-page navigation opens the cited original PDF under mock conditions.
- Verified GitHub Actions run https://github.com/daegweon/financial-paper-analyzer/actions/runs/44403257361 : **24/24 PASS**; Python, frontend and isolated PostgreSQL authorization jobs pass; opt-in live E2E skipped. Prior first CI 15/15 pass at run #44402413548.
- Live OAuth/SMTP, signed private PDF content, real mobile devices and service-first security-migration rollout remain **PENDING**. The engine and Production were not modified.

## 2026-11-19 — Verified durable state and safer manual live E2E

- Canonical weighted development estimate is stored in `docs/PROJECT_PROGRESS.json`: **84/100 engineering points** and **4/10 independently verified release gates**. This is not a public beta release sign-off. The score does not increase merely because new code was drafted.
- Root `AGENTS.md` instructs future coding sessions to read this state, decisions, changelog, progress JSON and release gates before working and to report both percentage and gates each time. `scripts/check-project-progress.mjs` checks weight and earned-point sums and refuses unsupported release-gate PASS claims; it now runs in frontend GitHub CI.
- Manual `workflow_dispatch` live E2E is now limited to main, approved target `production`, boolean consent and the exact acknowledgment `RUN_SYNTHETIC_LIVE_E2E`. New Python preflight refuses missing configuration or any unexpected Supabase/Railway URL; before creating test users it demands `/health.queue_write_mode == service_role`.
- Candidate API `/health` includes a non-secret `queue_write_mode` readiness field. **Running production API is not yet confirmed to support this field**, so actual authenticated E2E remains PENDING and the staged database grant change MUST NOT be applied first.
- Rejected automatic account creation, Production deployment, Worker change, real PDF mutation or DB schema/grant changes in this development milestone. See `docs/LIVE_E2E_SAFE_HANDOFF_2026-11-19.md`.

### 2026-11-19 — Green CI proof for the protected live-E2E guard and progress ledger

- Draft PR #18 code commit `54669ddae533e1ffe2b1062c6b3b7b309e54b73c` independently verified in GitHub Actions: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44411991617 . Python **112 passed / 1 skipped** (real live E2E intentionally skipped), frontend **75/75**, browser Playwright **24/24**, isolated PostgreSQL db-policy **PASS**. New progress validator printed **PROJECT_PROGRESS_VALIDATED 84% engineering, 4/10 release gates**.
- Verified Vercel feature Preview READY on this commit; production remains on older main and old Railway API/Worker, so new `/health.queue_write_mode` is NOT yet claimed live. Live Auth/PDF/E2E, SMTP, migration, device and rollback gates remain PENDING.

## 2026-11-19 — Railway API deployment-readiness verification (engineering 85%)

- Canonical engineering estimate **85%** and real beta release gates **4/10 PASSED**. The +1pt in beta operations is for verified old/new API HTTP readiness probes and a two-phase disposable PostgreSQL migration compatibility check. No live production release gate was cleared.
- Confirmed Railway project `c663389c-453c-4645-a83d-299b94089864` currently has ONLY the `production` environment `0b4f06c3-504a-4610-8995-395c2f4d3d1f`. Core API `81b678e2-7136-436d-9058-7d20647dc1b7` and Worker `238af942-0628-47d5-9280-04a49373423f` both source GitHub branch `feat/research-workspace-mvp`; the release candidate branch does NOT deploy automatically. No staged Railway changes; both core services healthy.
- Live GET-only GitHub Actions probe of `https://papersignal-api-production.up.railway.app/health` returned `status=ok`, `analysis_version=finance-structured-v6.4.2`, and `queue_write_mode=legacy_missing_marker`. Unauthenticated GET job status returned HTTP 401. **Old live API is healthy but has not adopted the server-owned queue submission flow**.
- Separate GitHub runner started candidate Uvicorn with only synthetic local env and observed `queue_write_mode=service_role`, anon status HTTP 401 and no key in health response. No external request or user record.
- PostgreSQL 17 CI now checks both transitions: server-role job enqueue **before** grant revocation while legacy client grants remain, then post-migration user upload/read and owner isolation plus denial of client-forged results and jobs. Entire CI `https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952` PASSED: backend 129 tests pass/1 skipped, frontend lint/build, isolated PostgreSQL, 24/24 Playwright, and GET-only live probe. Opt-in live E2E skipped.
- Actionable API-only cutover recipe and rollback constraints saved to `docs/RAILWAY_API_CUTOVER_2026-11-19.md`. No Railway source change, deploy, DB migration, customer PDF access, or analysis-engine modifications occurred.
- Main-only GitHub workflow_dispatch guard is not yet on main (PR #18 is Draft). Real two-user E2E remains explicitly approved/manual after verified API deployment; do not assume it can be dispatched from an unmerged branch.

## 2026-11-19 — API-only production deployment completed (86% engineering, 4/10 release gates)

- Railway **papersignal-api ONLY** deployment `0b5716db-b720-49db-b15c-babf77b26e5a` reached SUCCESS from pinned immutable commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732`, source `release/beta-candidate-20261119`. The service's previous rollback deployment is `17c9134b-f49c-4358-a879-7ca77b55b936` (pre-SQL-revocation only).
- Railway Worker remains `dc501061-d434-454a-bc7d-4658b991a2f1`, source `feat/research-workspace-mvp`, SUCCESS; no deployment or source change. There are no pending Railway staged changes.
- GitHub Actions strict READ-ONLY public API verification `https://github.com/daegweon/financial-paper-analyzer/actions/runs/44462359704`: HTTP `/health` confirms `queue_writer=service_role`, `analysis_version=finance-structured-v6.4.2`, and no-auth job-status returns HTTP 401. The new API boots successfully with existing Railway variables; no keys were printed.
- Railway recent 1-hour API HTTP sample: 10 requests, zero HTTP 5xx; 5 intentional/ordinary 4xx. Runtime logs show GET health 200 and denied anonymous job-status 401. Snapshot only, not continuous uptime guarantee.
- Live Supabase project still allows authenticated INSERT to analyses/jobs and UPDATE of papers.status. Do not apply `20261117215315_beta_server_owned_result_writes.sql` until the **real consented two-user HTTP E2E passes**, and reconcile remote migration history. Never blindly push all historical migrations.
- Canonical progress raised **85% → 86%** because the server-owned queue API was actually deployed and its readiness/authenticated-boundary preflight verified. The combined `api_migration` beta gate remains PENDING until live E2E and DB grant revocation: **4/10 gates still passed**.
- Consolidated PR #18 remains Draft (unmerged); the Railway service is pinned to older reviewed SHA rather than tracking future branch pushes. Do not infer its running code from latest PR head. Vercel Production/main and user source PDF documents were not changed.

## 2026-11-19 — Real E2E Storage cleanup and private-PDF HTTP assertion hardening

- **Engineering 87% / release gates 4/10 passed**. The +1 milestone point is E2E reliability/security readiness; no live Auth/Worker E2E has run, so no new live gate is marked passed.
- Corrected opt-in live E2E fixture `_remove_storage_object` from unsupported `POST /storage/v1/object/papers` to **`DELETE /storage/v1/object/papers`** with exact `prefixes` JSON. Official Supabase Storage batch-delete protocol and `storage-js` remove implementation confirm DELETE is required. Fix prevents test-created PDF objects being orphaned after an otherwise successful test.
- Added actual HTTP-level checks to the live E2E harness *before triggering the model*: owner must GET the exact original private PDF bytes; other user cannot GET; owner must create a 60s signed link and retrieve the exact source bytes; other user must NOT be able to mint their own signed link. Signed URLs are bearer URLs and are never printed in test errors.
- New `httpx.MockTransport` unit tests prove DELETE method/body/headers, failure on cleanup error, PDF bytes, signed URL path validation and other-user read/sign denial; no live requests in those unit tests.
- **GitHub Actions: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44467502056** — backend **133 passed/1 real E2E skipped**, browser 24/24, frontend and PostgreSQL checks all successful; actual live API read-only readiness check successful.
- Read-only Supabase SQL inspection found 0 test-created Auth users, 0 test papers, 0 test Storage objects and 0 active synthetic test jobs. No deletion was performed.
- Existing core API pinned immutable `ace3fbd5` remains SUCCESS; Worker unchanged. Candidate E2E changes are in unmerged PR #18 and are NOT automatically deployed to Railway.
- Real E2E still requires explicit production-test consent, secure GitHub secrets and a safe manual execution path, after which reviewed client write privilege migration can proceed. Keep historic papers/results intact.

## 2026-11-19 — Independent manual production E2E launcher created (88% engineering; 4/10 beta gates)

- **Live E2E is still NOT executed.** Canonical progress raised **87→88%** based on verified QA cleanup robustness and a separate manual-only E2E launch path; independently passed live beta gates remain 4/10.
- Draft PR #18 head `431059a1116a50f39fd56d565c35a1afc081b8fc` passed https://github.com/daegweon/financial-paper-analyzer/actions/runs/44472720847 : backend 143 PASS/1 deliberate opt-in skip, browser 24/24, isolated PostgreSQL, frontend, and live API GET-only preflight PASS.
- Real E2E cleanup now requires valid exact QA-only PDF path and owner UUID, scopes each admin PostgREST deletion to both `user_id` and `paper_id`, refuses to clean a nonterminal Worker job, attempts independent DB and Storage cleanup, and **retains QA Auth users when any DB/Storage cleanup fails** for manual inspection. MockTransport tests cover successful, partial and rejected cleanup with no production mutation.
- **New standalone workflow PR #19**: https://github.com/daegweon/financial-paper-analyzer/pull/19 (Draft, base `main`, head `8019c8b7b3a1c24de6e758fd5e6190b633fead00`). This PR contains `.github/workflows/papersignal-live-e2e.yml`, a human runbook, and an automated safety contract test. GitHub PR CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44473470809 PASS, 57 Python tests.
- Workflow is manual `workflow_dispatch` only and **NOT on main until a human reviews/merges PR #19**. It requires exact target, approval checkbox, immutable audited source SHA `431059a…`, and acknowledgment `RUN_SYNTHETIC_LIVE_E2E`. Secrets are scoped to preflight/actual E2E steps, never dependency installation, with read-only GitHub token. No account, PDF, AI call or SQL migration happens automatically.
- Human action required: review and merge PR #19 ONLY; securely configure four repo Actions secrets; manually dispatch/approve E2E. Keep PR #18 Draft and do NOT apply write-grant revocation until real E2E PASS. See `docs/HUMAN_E2E_HANDOFF_2026-11-19.md`.
- Read-only actual Supabase checks: 0 known QA-created Auth users, 0 papers, 0 Storage objects, 0 active fixture jobs; live `authenticated` `analyses`/`analysis_jobs` INSERT privileges remain enabled. Railway API `0b5716db-…` and Worker `dc501061-…` are Online with 0 recent failed deployments; no pending Railway changes.

## 2026-11-19 — Server-side per-user analysis quotas and user-facing limit feedback (89% engineering)

- Added `supabase/migrations/20261119100000_server_owned_analysis_quota.sql`: service-role-only `SECURITY DEFINER` RPC with empty search_path, per-user transaction advisory lock, same-paper active-job idempotency, maximum 5 jobs in a rolling 24-hour window and maximum 2 active jobs. Browser `anon`/`authenticated` roles cannot execute the RPC.
- Candidate API now calls the queue RPC rather than direct table INSERT; maps daily/active quota errors to user-safe HTTP 429 messages. Frontend `startAnalysisJob` surfaces actionable 429 details immediately and never retries the POST, avoiding duplicate AI jobs.
- Disposable PostgreSQL tests prove execute grants, idempotency, daily and active limits, pre/post migration behavior. Browser suite runs 33 scenarios (11 each desktop Chromium, Android-emulated Chromium, iPhone-emulated WebKit).
- Latest GitHub Actions https://github.com/daegweon/financial-paper-analyzer/actions/runs/44526397733 SUCCESS: backend **146 passed / 1 live E2E skipped**, candidate ASGI HTTP smoke PASS, PostgreSQL queue quota + RLS PASS, frontend lint/build + progress validation, Playwright **33 passed**, strict live API read-only probe PASS. PR #18 still Draft.
- **Production Supabase quota migration is NOT applied.** Current deployed API is pinned to `ace3fbd5` and does not call the new quota RPC. Before rollout, reconcile actual remote migration versions; obtain explicit approval for additive migration, apply only this migration, deploy candidate API, verify quotas, then later perform real 2-user E2E and client-write revocation.
- Weighted engineering estimate **88% → 89%** due verified cost-control implementation and end-to-end CI coverage; actual live beta release gates remain **4/10**. No production DB or Worker changes in this milestone.

## 2026-11-19 — Visible analysis quota meter and complete CI verification (90%)

- Added a research-library usage meter showing **rolling 24-hour analysis usage out of 5** and **active jobs out of 2**. Usage is derived from the signed-in user's own RLS-visible job rows; malformed/future timestamps are ignored and remaining counts never go negative.
- Added a standalone pure helper `frontend/lib/analysis-quota.ts` and four tests covering rolling-window boundary, active queued/processing states, exhausted limits and shared server policy constants. The test is now part of frontend `npm run lint`/prebuild.
- Latest full CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44528193012 SUCCESS: backend **146 passed / 1 live E2E skipped**, frontend TypeScript + quota UX tests/build PASS, PostgreSQL queue RPC quotas and RLS PASS, Playwright **33 passed**, strict live API GET preflight PASS. No live E2E mutations.
- Engineering **89% → 90%**; the core platform/user feedback milestone is now complete. Real beta release gates remain **4/10**.
- **Production quota rollout is still pending:** remote Supabase migration history currently lists only nine versions through `20261113234956`; quota RPC version `20261119100000` and result-write revocation migration are absent. The running Railway API remains pinned to `ace3fbd5` and uses direct service-role INSERT, not the new quota RPC. Do not apply production migration without explicit change approval and remote-history reconciliation.

## 2026-11-19 — Final verification of 90% quota-meter candidate

- Candidate code + visible usage meter commit `e40ec8f62c9dffe12de9adf8ec4ba07e69a9f044` completed full GitHub Actions successfully: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44528847670 . Backend 146 passed/1 live E2E skipped, frontend TypeScript/quota tests/build, PostgreSQL quota and RLS, 33 Playwright tests, strict live API GET preflight all passed. Progress validator 90% / 4 of 10.
- `docs/PROJECT_PROGRESS.json` now points at this exact commit/run. No Production DB migration, real user E2E, Worker update or analysis-engine changes.

## 2026-11-20 — Additive quota rollout parity verified

- Candidate commit `30255ce6e6fb2f79794819f37c5a2de12aa3bc84` passed GitHub Actions run [#44533862423](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44533862423): API, frontend lint/typecheck/tests/build, 33 browser scenarios, read-only live API probe and PostgreSQL 17 db-policy all SUCCESS; live E2E intentionally SKIPPED.
- CI applies the additive quota RPC before client-write revocation, verifies service-only execute, cross-owner rejection, same-paper idempotency and daily/active caps, then applies revocation and repeats the quota contract. This verifies both migration phases in disposable PostgreSQL only.
- Canonical engineering score remains **90%**; actual beta release gates remain **4/10**. This improves deployment confidence but does not satisfy live account/PDF, production quota rollout, SMTP, native device or rollback gates.
- No Production Supabase migration, Vercel Production promotion, user fixture or Worker deployment was performed. PR #19 still requires human review/merge, protected Actions secrets and explicit manual dispatch for live E2E.



- Consolidated Draft PR #18 includes the production-order regression: apply the additive service-only quota RPC **before** removing legacy client grants, check quotas, then revoke grants and check the same contract again. This is an isolated disposable PostgreSQL test; no live Supabase change.
- A wrong-owner paper queue attempt must raise `PAPERSIGNAL_PAPER_NOT_FOUND` in both phases, even when the call originates from service_role. This guards the API's ownership contract.
- Commits `be4ae7c`, `e588250`; CI result must be verified before crediting any additional completion points. Canonical engineering baseline remains **90%**, real beta gates **4/10**.
- Real live E2E remains blocked on human approval/review of PR #19, securely configured secrets, and manual dispatch. No new Production DB migration, Vercel Production promotion or Worker code change is authorized by this CI enhancement.

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

## 2026-11-20 — Failure taxonomy, version comparison and usage-ledger design (CI pending)

- Added offline `benchmark/failure_report.py` and tests: classify failed analysis jobs (authentication, authorization, missing resource, provider quota, timeout, provider unavailable, invalid model response, other HTTP/application) and aggregate Gemini attempts/errors by model. It explicitly does not infer that a fallback HTTP 200 recovered a job without terminal completion correlation.
- Added `benchmark/compare_scorecards.py` and tests: paired per-paper baseline/candidate comparison across Gold-fact coverage, claim-evidence coverage, exact-page citation precision and explicit human score. Missing measurements are excluded, not imputed as zero.
- Added implementation-ready privacy/security design for an immutable per-attempt usage ledger and effective-dated official pricing, including RLS, service-role-only writes, idempotency, nullable usage and no invented free-tier USD cost. Design only; no migration/table/production write.
- The prior complete CI [#44641154839](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44641154839) passed 157 backend tests, frontend, DB policy, read-only API and browser QA. The new diagnostics/comparison tests need a complete fresh CI run; earlier run [#44644913043](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44644913043) was superseded by newer commits and cancelled. No progress point credited yet.
- Human approvals, production DB changes, deployment and real-user E2E remain deferred. No analysis-engine behavior or user data changed.

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

## 2026-11-20 — Best-effort Gemini usage ledger API writer (CI pending)

- `_process_analysis_job` now establishes task-local ownership context from the verified job (`user_id`, `paper_id`, `analysis_job_id`). Each Gemini model attempt receives a monotonically increasing per-job attempt index.
- Added `_persist_ai_usage_event`: backend service-role POST to `ai_usage_events`, opaque idempotency key, provider/model/outcome/status/error class/latency and provider-reported token metadata. HTTP and transport failures are separate events; unknown token values remain NULL.
- Writes use a short timeout and `Prefer: resolution=ignore-duplicates`; missing context/key skips the write. HTTP/network ledger errors are redacted and non-fatal, so analysis result processing continues. No prompts, PDF text, model response, bearer token or API key is stored.
- Added unit tests for verified ownership fields, token NULL handling, idempotency header, missing context and non-fatal ledger failure. API job in [#44662407474](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44662407474) passed **169 tests / 1 deliberately skipped**; disposable DB ledger policy and GET-only API preflight passed. Frontend build and synthetic browser QA are still running. Keep engineering progress at 96% until full CI is green.
- This is candidate code only; no Railway deployment or Production Supabase migration. Real usage persistence will not begin until separately approved rollout.

## 2026-11-20 — Engineering progress 96% → 97%: API usage-ledger writer verified

- Full CI [#44662407474](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44662407474) passed on the usage-ledger API writer: API **169 passed / 1 deliberately skipped**, disposable PostgreSQL policy, frontend lint/build, GET-only live API preflight and all synthetic browser QA passed; real live E2E intentionally skipped.
- API derives task-local ownership context from the authenticated analysis job and performs best-effort service-role writes for Gemini attempts. Short timeout, idempotency, explicit outcome/status, nullable provider token fields and redacted/non-fatal write failures protect analysis execution.
- One privacy/integrity point credited; weighted engineering completion **97%**. This is candidate code verified in CI, not deployed or writing to Production. Production ledger migration and real two-user E2E remain human-gated.
- Current pricing work adds an official source-backed, effective-dated model catalog, Decimal cost estimator, per-paper report and explicit billing-mode configuration. Its latest full CI [#44666072502](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44666072502) has API 178 tests, DB policy, frontend and GET-only live preflight green; browser QA is still running. Do not credit pricing work until full run passes.
- No production Supabase migration, Railway deployment, Vercel promotion or user-data mutation.

## 2026-11-20 — Monthly AI cost and budget diagnostics (CI pending)

- Verified current Gemini Developer API Standard paid rates against Google's official pricing page (checked 2026-11-20): Gemini 3.5 Flash-Lite $0.30 input/$2.50 output per 1M tokens; Gemini 3.6 Flash $0.75/$3.75 through 2026-12-31 and $1.50/$7.50 from 2027-01-01. Thinking tokens are included in output pricing. Source: https://ai.google.dev/gemini-api/docs/pricing.
- Added effective-dated catalog, Decimal-based estimator and per-paper/model/month cost report. Unknown billing mode, model, timestamp or token usage remains unknown; Free is zero only when explicitly verified. Catalog overlap is rejected.
- Added monthly user and paper budget diagnostics. Exact Decimal sums, incomplete coverage is never reported as within budget; these are reporting alerts only, not hard enforcement. Wired optional events and thresholds into integrated quality pipeline.
- API tests in CI [#44666816651](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44666816651): **181 passed / 1 deliberately skipped**; disposable DB policy and GET-only live API preflight passed. Frontend lint/build and synthetic browser QA still running at checkpoint. Keep engineering progress at 97% until full CI is green.
- No Production migration/deployment. Do not set `GEMINI_BILLING_MODE` until billing tier is verified in Google AI Studio. No hard quota is enforced by this report.

## 2026-11-20 — Administrator-only AI budget and usage console (CI pending)

- Corrected the product boundary: AI cost and budget are administrator operations. Removed individual user/paper budget thresholds from `backend/app/cost_report.py` and the integrated quality pipeline. User/paper cost rows remain administrator-only usage breakdowns; only one service-wide monthly budget exists.
- Added `ai_admin_settings` to the additive AI usage ledger migration, RLS/FORCE RLS and service_role-only access; SQL CI verifies browser roles cannot read/write settings and service_role can persist the global budget.
- Added server-authorized endpoints `GET /api/admin/ai-usage/summary` and `POST /api/admin/ai-usage/budget`. Both verify Supabase session then exact `PAPERSIGNAL_ADMIN_USER_IDS` allowlist membership before service-role access. Summary returns month/model/service-wide budget and administrator-only user aggregates, never raw events. Budget update validates finite nonnegative Decimal values and records the verified admin user ID.
- Added `/admin/ai-usage` administrator dashboard with global monthly budget editor, monthly total, model breakdown and internal user usage. Ordinary users receive HTTP 403 from API regardless of frontend route visibility.
- Added backend tests for allowlist, non-admin denial, global budget write, invalid values, settings persistence and admin summary aggregation. Full CI pending; no progress point until all jobs pass.
- No Production Supabase migration, Railway deployment, Vercel Production promotion or customer data mutation. Admin allowlist and budget environment configuration are documented for the final human rollout.

## 2026-11-20 — Admin dashboard QA findings and remediation (CI pending)

- Browser QA caught two test/UI issues: Next.js CSS Modules require all selectors to be locally scoped (fixed table selectors); the admin page's trailing-slash regex typo was fixed after TypeScript caught it.
- Added explicit browser coverage for a non-admin receiving 403 with no cost/ budget content, and for an administrator viewing aggregate costs and editing the single service-wide monthly budget. The first run exposed test locator strictness and numeric input normalization; selectors were made exact and cross-browser tolerant.
- WCAG testing found a real contrast issue: `.panel>p` specificity overrode `.notice` text color, resulting in #627680 on #fff7e8 at 4.45:1. Fixed with `.panel>p.notice { color: #674a16 }`. It also flagged horizontally scrollable tables as not keyboard focusable; both tables now have `tabIndex=0`, accessible labels and visible keyboard focus.
- New full CI is running on commit `ce5eb76b3c689bfc8f2477f259bb65e05715cdd0`; do not credit the admin-console milestone until API, frontend, DB policy and all browser projects pass.
- No Production migration, deployment or user-data mutation.

## 2026-11-20 — Admin AI operations telemetry and cost-coverage hardening (CI pending)

- Extended the administrator-only usage summary with success/failure counts and rate, total token volume, incomplete token metadata count, average model-attempt latency, and provider-separated model rows. The event query now selects the stored `outcome`, `total_tokens`, and `latency_ms` fields; the cost report preserves provider dimension so identical model names from different providers do not merge.
- Fixed a correctness risk in the 20,000-event monthly query cap. The API now fetches one sentinel page (up to 21,000 rows), detects whether more than 20,000 events exist, then aggregates only the first 20,000. A truncated result can never display `within_budget`; it is explicitly incomplete (or over-budget with incomplete data). Exactly 20,000 rows do not falsely trigger truncation.
- Added a global `created_at` index for month-range admin queries, PostgreSQL CI assertion for the index, backend tests for provider-separated model usage, outcome/token/latency metrics, 20,001-event sentinel pagination, incomplete-budget status, and `updated_at` refresh on admin budget writes. Dashboard includes clear token-incomplete marker and Korean budget status labels.
- CI is being rerun on the latest candidate commits. Do not award an engineering point until the exact PR head passes API, frontend build, PostgreSQL policy and browser QA. Production migration and deployments remain untouched.

## 2026-11-20 — Admin AI operations milestone verified (98% engineering)

- Latest candidate CI #44675494781 passed on commit `b0a4261d8f36025b3d8dfec2105b58ebb9f23121`: API 194 passed/1 deliberately skipped; frontend lint/typecheck/build; disposable PostgreSQL 17 migration/RLS/index checks; GET-only live API preflight; 39 synthetic browser scenarios across desktop Chromium, Android Chromium and iPhone WebKit. Live E2E was deliberately skipped.
- Browser coverage confirms ordinary users receive 403 and no AI cost/budget data, administrators can inspect aggregate usage and save only the global monthly budget, incomplete/truncated usage cannot claim within-budget, and admin UI passes automated WCAG checks.
- Admin console now includes provider/model usage, success/failure rate, token volume, incomplete token metadata, average latency, cost estimates, service-wide monthly budget and administrator-only user usage breakdown. Added created_at index, 20,001st-row sentinel pagination, timestamp refresh on budget upsert and provider-safe cost grouping.
- `docs/PROJECT_PROGRESS.json` now records 98% engineering completion and 4/10 independently passed release gates. This is not a launch approval. Production AI ledger/admin-settings migration, API deployment, actual two-account E2E, SMTP, native-device PDF checks and rollback remain pending human approval. No Production migration, deployment or promotion was performed.

## 2026-11-20 — Official pricing provenance verified (98% engineering)

- Candidate head `9b45e5957f9d2bcecf3ca5be64f5f47a192648f7` passed full CI #44676373334: API 195 passed/1 deliberately skipped, frontend lint/typecheck/build, PostgreSQL 17 migration/RLS/index checks, GET-only live API preflight and 39 synthetic browser scenarios across desktop Chromium, Android Chromium and iPhone WebKit all SUCCESS. Live E2E deliberately skipped.
- Administrator model rows now show per-provider/model cost status counts (confirmed free tier, estimated paid standard, unknown billing, missing tokens, missing price), official price source links and effective dates. Added report/helper/UI contracts and tests. The Google pricing catalog URL is shown as provenance; estimates remain estimates, not invoices.
- Progress ledger updated: 98% engineering completion; release gates remain 4/10. No Production migration, Railway deployment or Vercel Production promotion. Next action is human review and approved staged migration/deployment plus real two-account E2E, not more speculative engine tuning.

## 2026-11-20 — Staged beta release runbook

- Added `docs/BETA_RELEASE_RUNBOOK_2026-11-20.md` with explicit human approval checkpoints, current production API/rollback references, protected E2E secrets, ordered quota RPC/API/AI ledger/client-write-revocation steps, two-account isolation tests, admin allowlist/budget configuration, SMTP/mobile validation and rollback precautions.
- No Production action was executed. The runbook is an operational preparation artifact; launch gates remain 4/10 and engineering completion remains 98%.
