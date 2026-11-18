# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-19 (Asia/Seoul)
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
