## 2026-11-17 — Read-only B01-B10 private-storage hash workflow

- Supabase read-only inventory confirms B01-B10 originals exist in private Storage (10 PDFs, 209 pages, 17,760,530 bytes), but the connected Supabase tools return metadata only.
- Added \`benchmark/lock_legacy_storage_pdfs.py\`: user can run it locally with \`SUPABASE_URL\` and \`SUPABASE_SERVICE_ROLE_KEY\` held only in local environment. It performs GET-only metadata and private-object downloads, checks exact file size/PDF header/PyMuPDF page count, hashes exact bytes, and emits SHA-256 JSON without file bytes, storage paths, user IDs or secrets.
- Added synthetic tests and \`docs/LOCK_LEGACY_STORAGE_PDFS.md\`. Tests have not run in connected CI; GitHub Actions startup_failure persists.
- Once user attaches the generated JSON (not the service-role key or PDFs), commit the B01-B10 binary lock to the handoff branch, then create a new candidate from that lock. Current PR #6 candidate predates the B01-B10 binary lock and must be re-created after it; do not claim Q0 complete yet.

## 2026-11-17 — Legacy regression inventory and job-created timing

- Read-only Supabase inventory confirms B01-B10 still exist in the private papers bucket: 10 PDFs, 209 pages, 17,760,530 bytes. Sanitized sizes/pages/opaque ETags (not treated as hashes) are in benchmark/legacy_regression_storage_inventory_2026-11-17.json. Exact private file bytes are not exposed by the current connector; B01-B10 SHA-256 remains unverified.
- Worker now logs analysis_jobs.created_at on claim. Telemetry parser calculates job_created_to_terminal_ms (includes queue wait) and claim_to_terminal_ms. Both exclude PDF upload transfer; full_pipeline_latency_ms remains null. Added malformed timestamp regression test.
- PR #6 remains the only clean candidate; PR #5 closed for invalid lock ancestry. No production data or deployments changed.

## 2026-11-17 — Latency scope correction and clean PR

- PR #6 is the clean candidate; PR #5 has been closed because its branch lacked the Held-out lock commit in its Git ancestry.
- Worker claim logs now include \`analysis_jobs.created_at\` from the claim RPC result. The telemetry parser reports \`job_created_to_terminal_ms\` (includes queue wait) and \`claim_to_terminal_ms\`.
- Important: \`analysis_jobs.created_at\` is recorded after PDF upload completes. Neither metric is upload-start-to-save latency. \`full_pipeline_latency_ms\` remains null and Q2 p95 cannot use these two proxy durations.
- Synthetic timing arithmetic verified locally (job created 2 seconds before claim; terminal 10 seconds after claim => 12,000 ms job-created-to-terminal and 10,000 ms claim-to-terminal). Repository CI remains unavailable.
- All Q0/Q1/Q2/P0 remain BLOCKED; no Gemini full-pipeline run, billable cost, peak RSS, independent human gold or actual upload-start timestamp. No production deployment or user-data change.

## 2026-11-17 — Corrected Held-out lineage, telemetry and local preflight (latest)

- User-uploaded H01/H02 original PDFs rechecked by SHA-256 and PyMuPDF: H01 40 pages / 2,521,298 bytes / \`816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127\`; H02 30 pages / 5,223,546 bytes / \`d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283\`.
- Held-out lock commit \`149311ec2993cac3bd410c10ac7feb202d582fc7\`.
- **Important correction:** old candidate branch \`experiment/engine-quality-v6-4-2-heldout-locked\` / PR #5 is NOT descended from the lock commit. Git compare says \`diverged\`, 56 ahead / 18 behind, merge base frozen production SHA \`8cd5e37\`. PR #5 is superseded; do not merge.
- Clean branch \`experiment/engine-quality-v6-4-2-heldout-clean\` starts at \`325fb7e5bda6dd05cf4888fd658018a2d8e4abbf\`, a docs-only descendant of the lock commit. First candidate code commit \`7dd13343f44702369b8a1415c750d5fdf08371f7\` has that base as parent, so lock ancestry is valid.
- Telemetry-only patch adds job context + per-Gemini-call IDs, model attempt/status/timing/token logs, and a parser for Railway logs. Raw provider error bodies are now redacted. Prompt/schema/extraction logic, model order, request body and result schema unchanged.
- Local reproduction of the frozen production \`extract_pages\` function on PyMuPDF 1.26.7: H01 40/40 text pages, 111,448 chars, median 212.735 ms; H02 30/30, 62,589 chars, median 84.105 ms. Production pins 1.26.3, so this is extraction-only local preflight, NOT Q2 or production performance evidence.
- GitHub Actions continues \`startup_failure\` before jobs; repository tests remain unexecuted. No measured telemetry overhead, Gemini full-pipeline latency/cost or peak RSS. Q0/Q1/Q2/P0 all remain BLOCKED.
- No production merge/deployment, Supabase write, user-data change or secret exposure. Keep the clean candidate isolated.


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
