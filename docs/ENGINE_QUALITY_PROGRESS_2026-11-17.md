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
