## 2026-11-17 — Continued PyMuPDF improvement, source-review preparation and hard release safeguards

- Committed five synthetic review-queue tests and source-linked \`benchmark/human_review_pack.py\` for 18 v6.3.9 review-required findings, with no fabricated reviewer decisions.
- Verified frozen historical review counts in Supabase by read-only SQL, with exact distribution B01 4/B02 6/B03 1/B05 2/B09 3/B10 2.
- Strengthened release gate with PDF SHA + page + source quote cross-checks, disjoint held-out/regression SHA, and separate structural PASS from actual deployment authorization.
- Local reproduced gate test set: 9 PASS. GitHub runner failed \`startup_failure\`; Free Railway plan denied isolated build service. No secret-bearing historic service modified to work around constraints.
- Experiment branch is NOT held-out pre-registered, so not yet a release-eligible candidate. No current Gemini p95/cost or independently reviewed gold accuracy. Full Q0/Q1/Q2/P0 and final deployment remain blocked.
- Kept Railway production \`8cd5e37\` deployed, data and secrets unchanged. PR #4 remains Draft.

## 2026-11-17 — User final product decision: stop OSS, focus on existing engine and quality-gated final deployment
- Closed speculative external parser adoption/complete replacements (0 production adoptions). Preserve PyMuPDF/v6.4.2 with frozen operating SHA 8cd5e37; do not re-run OSS hunt.
- Committed durable cross-session handoff in isolated `plan/engine-quality-release-handoff` branch: `docs/SESSION_HANDOFF_NEXT.md`, `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md`, machine-readable gates JSON, updated state and decisions. No engine code, data, environment or production deployment changes.
- Defined explicit exit gates: two independent human reviewers for all18 legacy review-required, at least50 material claims and ≥98% source-supported precision, zero critical false approvals, verified meaningful recovery (≥4 issues or heldout recall +5pp), legacy source evidence no regression, whole-pipeline p95 ≤1.05×/cost ≤1.05×/RSS ≤1.10× baseline, repeated matched Gemini runs; two-user/RLS/SMTP/Google frontend/backend release checks. All new gates still BLOCKED until evidence.
- Final goal: stop minor tuning immediately when certified gates are met, stage and deploy only the tested commit, verify live and roll back on any regression. Preserve all existing PDF/history. Current prior-provider Gemini503 blocks full model assertions.

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
