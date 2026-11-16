# PaperSignal engine quality iteration — 2026-11-17

**Scope:** Improvement work on frozen production `finance-structured-v6.4.2` PyMuPDF engine; no OSS parser replacement and **no production deployment**.

## Sources and immutable operating reference

- Handoff: `plan/engine-quality-release-handoff/docs/SESSION_HANDOFF_NEXT.md`.
- Thresholds: `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md` and `benchmark/engine_release_gates_2026-11-17.json`.
- Frozen production branch `feat/research-workspace-mvp`, deployed SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, source version `finance-structured-v6.4.2`.
- Live Railway API deployment `17c9134b-f49c-4358-a879-7ca77b55b936` and Worker deployment `dc501061-d434-454a-bc7d-4658b991a2f1`, both SUCCESS / online, both on frozen SHA at inspection time.
- Supabase project `hwmtayrecsfxernhssro` ACTIVE_HEALTHY; no data written/deleted.
- Vercel project `prj_I67LtzvbFdkWFe80T4Lx448MfPBn`: experiment-branch Preview builds observed READY on earlier changes. Production Vercel remains on `main`, separate from backend production branch. No promotion.
- Historical parser experiment service `papersignal-table-benchmark` has a crashed deployment, unrelated to core running API and Worker. Not part of this patch.

## Iteration 1 — focused direct-quote numeric audit hardening

- Created isolated work branch `experiment/engine-quality-v6-4-x` from the handoff branch.
- Narrow change in `backend/app/main.py`: extract spelled numerator and denominator from portfolio fraction descriptions, e.g. 'four out of six portfolios' and 'four of the six portfolios', requiring the direct cited excerpt; does not relax coefficient validation, table/model identifier rules, or the PyMuPDF parser.
- Added `test_written_portfolio_fraction_audits_both_counts_without_relaxing_estimates`. Covers supported evidence, wrong portfolio counts and wrong coefficient.
- **Not yet accepted into production:** no full B01–B10 corpus A/B, independent human gold, or full-pipeline costs available.

## Iteration 2 — predeclared gate evaluator

- Added `benchmark/engine_quality_gate.py` (CLI exit code 1 on incomplete evidence), usage specification and synthetic unit tests.
- Evaluates Q0 original and held-out SHA locks, 18 double-reviewed historical cases, 50+ material reviewed claims, 98% claim precision, zero critical false approvals, historical citation preservation, +4 recoveries or +5pp recall, held-out evidence, full-pipeline p95/cost/memory comparisons over 2+ matched repetitions, and commit-bound P0 checks.
- Guardrails: excludes Boolean false-as-zero and requires recorded resolution of human reviewer disagreements. Synthetic fixtures are expressly **not independent human verification or release evidence**.
- Local **gate-evaluator unit tests 6 passed** with `pytest -q /mnt/data/test_gate_local.py` (separate local reproduction). This is **not** the full backend test suite.
- GitHub Actions on the PR returned `startup_failure` before jobs; therefore no CI backend/frontend success is claimed. Vercel Preview READY is a build status only, not Q1/Q2/P0 evidence.

## Current release decision — BLOCKED

| Gate | Status | Missing independent proof |
| --- | --- | --- |
| Q0 | BLOCKED | Source-hash-locked original/2 held-outs, complete v6.4.2 full baseline, real 2-person review of 18 |
| Q1 | BLOCKED | >=50 actual human-reviewed material claims, >=98% actual precision, no critical errors, 4 recoveries or +5pp recall |
| Q2 | BLOCKED | Completed baseline/candidate Gemini full-pipeline paired A/B; p95, billable cost, peak memory, reliability; full backend & frontend tests |
| P0 | BLOCKED | Real 2-user upload/auth/RLS E2E, external SMTP, provider quota/503 recovery, production/preview release & rollback |

**Decision:** Keep GitHub PR #4 draft and isolated. Do not merge to `feat/research-workspace-mvp`, deploy backend changes, change Supabase or promote the Vercel preview. Existing live services and user paper/analysis data preserved.

## Precise next work

1. Fix GitHub Actions runner provisioning or run full backend test/build in a hermetic environment; record actual results.
2. Lock original PDFs and 2 new held-outs with SHA and pre-tuning Git chronology, including extraction parameters/AI model identity and prompt hash.
3. Provide a reviewer workflow for the 18 known cases and 50 material claims with **two actual independent human reviewers**, exact PDF page, row, model column and significance legend; never auto-mark human gold.
4. Measure v6.4.2 and candidate full analyses with the same original+held-out corpus, at least 2 repeats each. Preserve error events and provider token/price data; 503/429 is not success.
5. Revert any candidate that regresses factual precision, historical supported quotes or latency/cost/memory limits.
6. Perform two-account RLS/SMTP/auth/upload E2E and production build/rollback checks. Only after **all** gates pass, stop tuning, release an exact verified Git SHA, and observe post-release health.


## Iteration 3 — historical human-audit queue (code, not human gold)

- New \`benchmark/human_review_pack.py\`: deterministic source-oriented records from a **frozen v6.3.9** JSON export of exactly B01–B10. Produces 18 unique case fingerprints and retains exact claim, coefficient, table/model labels, direct evidence and legend excerpt.
- Source PDFs are SHA-256 hashed **only if local actual PDF bytes are available**; absent files remain \`sha256: null\` and all pages remain \`pdf_pages_verified: false\`.
- Human reviewer slots, source adjudication, and evidence fields are null/empty by default; every case remains \`UNREVIEWED\`.
- Added five synthetic tests for fixed counts, missing/duplicated rows, version mismatch, invalid page evidence, source header fingerprinting, and refusal to invent human review.
- Read-only Supabase SQL inspection on 2026-11-17 confirmed current stored frozen v6.3.9 case totals: B01=4, B02=6, B03=1, B05=2, B09=3, B10=2; all 10 original benchmark papers present. **No DB rows or source storage were modified.**
- The actual complete pack could not be generated from the private workspace here: the original PDF bytes and full local analysis export were not available to the isolated test runtime. No false 'source verified' assertions.

## Iteration 4 — gate provenance / release-permission hardening

- \`benchmark/engine_quality_gate.py\` now requires each independently reviewed claim to match the locked source PDF SHA of its paper, plus specific valid source page, source quote and evidence reference.
- Held-out entries require positive page count and a SHA that does not occur in the regression corpus. Distinct reviewer IDs are necessary but not sufficient for human independence; the release owner must verify them.
- Important security correction: even a fully structurally passing synthetic JSON returns \`final_deploy_allowed: false\`; only \`structural_checks_passed\` may become true. CLI exit zero means structural acceptance only, NEVER automatic promotion.
- Nine local reproduction tests of the gate evaluator passed (\`/mnt/data/test_gate_local.py\`). This tests a local reproduction, **not the full connected repository backend test suite**. The new five review-pack synthetic tests were committed but not run by a verified repository CI runner.
- GitHub Actions continues \`startup_failure\` before any job. New isolated Railway build service creation was refused with \`Free plan resource provision limit exceeded\`; no additional service was created. Existing stopped experimental services have server-side credentials and were not repointed to unreviewed branch code.
- Vercel development Preview builds observed \`READY\`, but this is only the frontend build status and no engine A/B verification.

## Independent held-out chronology warning

This experiment branch was created and altered **before** any new 2-paper held-out PDF manifest was source-SHA locked. Under the strict Q0 pre-registration rule, a new release-eligible candidate must be constructed from the frozen baseline AFTER the new holdouts are genuinely locked; do not retroactively select/claim holdouts for this experimental candidate. Open-source paper discovery alone is not a PDF hash lock.

**No production release:** Q0/Q1/Q2/P0 all remain BLOCKED. Real human reviewers = 0 recorded. Source-supported precision, recoveries, full-model p95/cost/RSS are unmeasured. Railway API/Worker still use production SHA \`8cd5e37\`; original papers/analyses preserved. Keep PR #4 in Draft.
