## 2026-11-17 — pinned-runtime verification and next baseline gate

- Candidate branch: `experiment/engine-quality-v6-4-2-b01-b10-locked`; PR #7 remains draft. Latest candidate head before this handoff update: `e7782e1c1531dcc658a52246bfb61faa94d1d932`.
- Runtime verified: Python 3.12.16 / PyMuPDF 1.26.3, matching production pin.
- Backend tests on this runtime: frozen production 102 passed / 1 skipped / 0 failed; candidate 123 passed / 1 skipped / 0 failed. The skipped test is opt-in live E2E. GitHub Actions still fails `startup_failure` before creating jobs (latest run 43978680210, 0 jobs).
- Source fingerprint file: `benchmark/source_fingerprint_v6.4.2_2026-11-17.json`. Analysis version, prompt, schema, extraction, model config, requirements and Dockerfile hashes match; Gemini transport hash changed as intended. No secrets read or stored.
- B07 exact locked PDF: 23/23 pages extracted, zero empty pages, 69,414 chars, 73,295 prompt chars. Production/candidate text and prompt hashes match. Paired 10-run extraction+prompt A/B: p50 67.226 ms production vs 68.100 ms candidate (1.013 ratio), maxima 69.456 vs 68.968 ms. Extraction-only; not full-pipeline Q2.
- Historical Supabase results are mixed: B03-B08 v6.3.9, B01/B02/B09 v6.4.0, B10 v6.4.2. Only B10 is a historical v6.4.2 result (job-created-to-completed 27.701 s; worker-started-to-completed 26.575 s; two Gemini calls, 39,653 total tokens). Provider cost, per-call elapsed and RSS unavailable. Do not pool these mixed versions.
- Q0 remains BLOCKED: full same-version v6.4.2 baseline for all B01-B10 plus held-out H01/H02 Gemini runs still pending. Q1/Q2/P0 remain blocked. No production deploy or database mutation.
- Next: execute the frozen v6.4.2 end-to-end baseline on all 10 locked regression PDFs and both locked held-out PDFs in an isolated environment with provider usage/cost and peak RSS telemetry; then compare the telemetry-only candidate under matched conditions. Keep PR #7 draft until gates pass.

## 2026-11-17 — New candidate CI status

- New branch workflow run 43969788375 ended `startup_failure` before any job was created (0 jobs). Repository tests were not executed.
- GitHub API rejected retry with HTTP 403 (`This workflow run cannot be retried`). No test pass is claimed. Candidate remains draft and isolated; no production deployment.

## 2026-11-17 — B01-B10 exact SHA lock complete; v6.4.2 baseline pending

- Attached B01-B10 PDFs verified: 10/10 valid, unencrypted, 209 pages, 17,760,530 bytes. Exact SHA-256 hashes are in benchmark/legacy_regression_binary_lock_2026-11-17.json.
- First B01-B10 binary manifest commit: 342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c. Follow-up lock-reference commit: 14ed46fd032b42813dd0ccf372447bd71bd363aa. Candidate branch experiment/engine-quality-v6-4-2-b01-b10-locked starts from that follow-up commit.
- H01/H02 remain locked at 149311ec2993cac3bd410c10ac7feb202d582fc7. Both corpus lock commits are ancestors of the candidate.
- Exact frozen production extract_pages/sanitize_pdf_text logic reproduced locally on B01-B10 using PyMuPDF 1.26.7 (production pins 1.26.3): 209/209 pages with text, 691,985 chars; five-run local extraction-only preflight. Not production baseline/Q2.
- Current v6.4.2 full-pipeline baseline has not run. Q0 remains BLOCKED pending pinned runtime + Gemini baseline; Q1/Q2/P0 also BLOCKED. No production deploy or DB mutation.


- Added benchmark/parse_railway_telemetry.py on the candidate branch to aggregate Worker claims/completion/retry events with Gemini job/call IDs, model attempt outcomes, latency and token counts. Provider cost remains null until a dated price schedule is supplied. Missing token metadata is explicitly marked incomplete, not treated as a verified zero.
- Added four synthetic parser tests; these and the telemetry tests are committed but unexecuted because GitHub Actions startup_failure happens before any job is created.

- GitHub commit metadata independently confirms lock chronology: lock commit 149311ec2993cac3bd410c10ac7feb202d582fc7 at 2026-11-16T21:11:16Z; first commit on the new candidate branch 356b4d688657fc2c55b828d2b12b3062e1c9434b at 2026-11-16T21:15:33Z. The immutable lock preceded the candidate branch's first commit by 4 minutes 17 seconds.
## 2026-11-17 — Candidate-only Gemini telemetry added, not yet validated

- Candidate branch experiment/engine-quality-v6-4-2-heldout-locked adds per-job/per-call Gemini attempt telemetry (status, model, attempt count, elapsed, token usage), without changing prompt/schema/extraction/request body/retry policy/output version.
- Two mocked provider telemetry tests and one job-context integration assertion added. GitHub Actions startup_failure before job creation; no test execution or overhead measurement.
- Candidate main SHA-256 0886879ed41dec90450894cc14963ac7b3fd6daa7a44a631daae57ef48dbd8ed. Prompt/schema/extraction function hashes remain identical to frozen production.
- PR #5 Draft. No production changes. All Q0/Q1/Q2/P0 remain BLOCKED.

## 2026-11-17 — H01/H02 binary lock and new baseline candidate

- Exact user-uploaded H01/H02 PDF bytes locked: H01 40 pages / SHA-256 816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127; H02 30 pages / SHA-256 d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283.
- Lock commit 149311ec2993cac3bd410c10ac7feb202d582fc7; lock-reference commit 59b68fbc902bd17b656d606246d17b19a5614acf.
- Fresh branch experiment/engine-quality-v6-4-2-heldout-locked created from frozen production SHA 8cd5e37ee8eab3bf4b726b75af89e410ab48396e after the lock. PR #5 Draft. No engine code changes.
- Baseline source fingerprints saved in benchmark/baseline_lock_v6.4.2_2026-11-17.json on the candidate branch. Local extraction preflight uses PyMuPDF 1.26.7, not production pin 1.26.3; its timings are not Q2 evidence.
- Added repeatable source fingerprint and locked extraction-only preflight tools/tests. GitHub Actions still startup_failure before job creation; full tests not run.
- Original B01-B10 PDFs are absent from current Project file inventory; hashes missing. H01/H02 full Gemini runs, independent gold, full p95/cost/RSS and P0 remain missing. Q0/Q1/Q2/P0 BLOCKED. Production remains on 8cd5e37.

## 2026-11-17 — Held-out PDF lock utility test correction

- Local reproduction of the exact-byte lock utility tests initially exposed one incorrect expected error-message substring (test-only mismatch; utility correctly rejected the wrong record type).
- Updated the repository test to match the documented exception message. Re-ran the local synthetic reproduction: 7/7 passed.
- This does not constitute a verified run of the connected repository backend suite or GitHub Actions.
- Publisher PDF binary retrieval was unavailable from the isolated runtime. Exact SHA-256 remains null; both held-outs are preselected, not binary locked; Q0 remains blocked.

## 2026-11-17 — Held-out papers preselected; PDF binary lock still pending

- Registered two new open-access CC BY 4.0 finance papers (H01 40 pages, VAR/TVP-VAR + DMA/DMS + genetic algorithm; H02 30 pages, LASSO/Elastic Net/tree ML + FX/global portfolio) in benchmark/heldout_preregistration_2026-11-17.json.
- Exact publisher PDF URLs and DOI/version metadata are recorded. Execution runtime could not download raw PDF bytes, so SHA-256 fields remain null and Q0 is BLOCKED.
- Added benchmark/lock_heldout_pdfs.py and six synthetic tests to hash exact original bytes, check PyMuPDF page counts, and reject duplicates/regression overlap. No PDF files are stored in Git.
- The next release-eligible candidate branch must be created only after PDF bytes are supplied/obtained, the binary hashes are committed, and that Git commit is recorded as the lock commit. Existing experiment branch remains ineligible because tuning predated holdout preselection.
- No production change or user-data write.

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
