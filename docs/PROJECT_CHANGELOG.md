## 2026-11-17 — Ranked OSS parser replacement trial (checkpoint)
- User asked pypdfium2 -> pdfplumber -> GROBID -> MinerU -> Marker. Isolated original-source B01–B10 replay completed for first two, baseline too.
- PyMuPDF 346/346 citations/54 screened; PDFium 292/346 and 50; pdfplumber 14/346 and 1. All10 PDFs processed per implementation; no parser failures, no provider calls, no SQL writes.
- PDFium faster and lower child RSS but loses 54 exact citations; plumber large quote regression. Neither promoted. GROBID/MinerU not executed under 1GB hard resource gate; Marker one-shot CPU research feasibility separately pending.
- Benchmark source and metrics committed to experiment/ranked-pdf-parser-trial; execution-only runner kept separate. Full production untouched, engine freeze continues.

## 2026-11-16 — Open-source parser evaluation CLOSED, no production adoption
- User directed ending speculative OSS comparisons. Adopt only a independently verified, overall non-regressing option.
- Existing locked-source evidence: four-PDF selected Camelot Stream extraction 20.565219s -> 9.869005s combined, but B01 p18 Table2 five primary cells remain missing in both all/selected outputs. No human gold or whole-engine gain. Reject unrestricted and selected Camelot for production; preserve experimental code and data.
- Docling/MinerU/Unstructured/Science Parse untested and not adopted. No new providers/packages, code, database schema, API, Worker or production deployment changes.
- Current live Railway commit 8cd5e37..., analysis source says finance-structured-v6.4.2; historical scorecard labelled v6.3.9. Do not confuse those.
- Stored detailed decision and machine-readable gates. Next focus: native engine source fidelity, 18 review-required findings, usage/cost telemetry and beta E2E. No global maximum claimed.

## 2026-11-16 — Actual assistant visual audit exposes within-page omission
- Viewed source-derived crops BEFORE parser candidates: B01 PDF p18/Table2 and B10 p12/Table5. Recorded 15 assistant-draft targets /25 numeric cells, source/render hashes, source geometry and expected-text digests. No human reviewer invented; independent human gold remains0.
- Added draft_cell_audit.py/run.py, visual_drafts_20261116.json and37 rejection tests (all passed locally,0.08s). Existing human-review gate and production validators unchanged. Railway mandatory pytest build gate passed; exact terminal count not recovered from log excerpt, so no new total claimed. LiveE2E/frontend not run.
- Audited four frozen output variants per target (all/selected, prior two repeats):60 checks=40agreements+20missing,0unassessed. B10 all10targets match;B01 all5parameter bundles missing in everyvariant. Native source anchors and inspected raster hashes verified.
- B01p18 saved candidate contains Table4 only, not actual Table2. Same-page omission means matrix equivalence and page-caption inclusion do not establish completeness. Do not promote or simply raise page cap.
- Source semantics retained:transposed B01variable columns;Std.Dev. not relabelledstandarderror. B10volatility0.20 andSharpe0.15 atrow3 distinguish same-number/wrong-column errors;not a claim of observed production mislabelling.
- Text-caption scan:86pages,32captioninstances,allin23selectedpages. Captionless/image tables,63excludedpages andnegativecontrols not fullyvisually audited;B02/B09 cellvisualaudit pending.
- New private compactauditartifacts4, total18. Originalpapers14,analyses103,jobs102completed/28failed,PDFobjects14 unchanged. API/Worker unchanged/online;benchmarkzero runningreplicas,no pendingwork. Nomodelcalls/schema/RLS/publicendpoint/cron.
- Implementationda3f12dd108e2f44e53f7fdf55b13a224b7c4fef;runnerfb5895d28336c9ed9da6c4d32f6bb674b5e649fa;deploymentb61322f7-edf3-4d71-a830-a4884c09862e;runvisual-draft-audit-c569a95eb0f44b608a608493de8a9910. Execution-onlyrunnerconfigs mustnotmerge.
- Report:benchmark/results/visual-draft-audit-2026-11-16.md. Next:caption/geometry-bounded table-region recovery with frozen drafts/untouched controls;complete source/human/negative/fullpipeline/heldoutgates. All18historicalreview-required findings remainunapproved.

## 2026-11-16 — Exact-cell review preparation and bounded Stream execution
- Added source-hash/page/row/column/value/companion exact-cell evaluation, conflict abstention, independent-review record checks, negative-control diagnostics and escaped offline source-first HTML review.
- Added private source-render/cell packets and a predeclared caption-only page selector, capped at eight pages; gold annotations intentionally remain empty. No human review or finding approval was fabricated.
- Local new suite: 48 passed. Isolated Railway full backend suite: 193 passed, 1 skipped (opt-in live E2E not enabled), 6 dependency deprecation warnings, 4.00s. Frontend build/user E2E were not run.
- Exact B01/B02/B09/B10 originals: 86 pages, 23 selected; all-page and selected-page Stream each ran twice per paper with alternating order. 16/16 executions completed, no parser/source/artifact errors. Selected-page matrix projections matched 8/8; prior all-page projections matched 4/4.
- Sum of subprocess wall times: 20.565219s versus 9.869005s (52.01% less). Maximum child RSS: 219.316 versus 173.758 MiB. These exclude source transfers, selection, rendering, upload and AI pipeline; no full-engine performance or accuracy gain claimed.
- Four new private JSON packets contain 33 rendered source pages and eight unadjudicated negative-page candidates, 9,915,979 bytes total. Zero independent human-reviewed cells; cell accuracy/recall/negative-page hit rate unavailable; all18 historical review-required findings remain unapproved.
- Existing paper/analysis/job counts and production API/Worker deployments unchanged; benchmark finished with zero running replicas. Existing private artifacts preserved (10 to14 objects); original PDF bucket still14 objects. No public endpoint/cron, provider call or policy/schema change.
- Implementation commit 2eb467bb4692c1e01ceff7f07e3f3862f0cfed07. Execution-only experiment/table-cell-review-runner pinned to 8c87af25652957fdbf868ccd0732c6c6e632ece9; NEVER merge its railway.toml into production.
- Report: benchmark/results/cell-review-preparation-2026-11-16.md. Metrics: cell-review-metrics-2026-11-16.json. Guide: docs/CELL_REVIEW.md. Next: independent source adjudication, omitted-page/legend audit, then full-pipeline and held-out quality/resource/cost gates. No promotion.

## 2026-11-16 — Exact-corpus open-source table shadow evaluation
- Optional Camelot hardening and isolated B01–B10 benchmark implemented; 209 pages, source identity/SHA-256 checks, separate processes, wall/RSS/version diagnostics and private raw artifacts.
- Focused suites: 43 passed locally and 43 passed in Railway BuildKit, including real synthetic-PDF lattice/stream extraction. Full production regression suite was not rerun.
- Two complete 30-execution extraction passes had zero parser failures and matching hashes/candidate counts. First-pass artifact uploads failed with HTTP 400; bucket discovery was fixed, tested and rerun. Final pass saved all ten private JSON artifacts with zero source/artifact errors.
- API/Worker/frontend production paths, dependencies and historical analysis/job data unchanged. New one-shot benchmark service has no public endpoint/cron and zero running replicas after completion. Original PDF bucket remains private/PDF-only.
- Decision: no unrestricted all-page Camelot production adoption. Exact-cell gold and bounded recovery quality/cost gates are next; no overall accuracy gain or global maximum claimed.
- Report: benchmark/results/table-shadow-evaluation-2026-11-16.md. Guide: docs/TABLE_BENCHMARK.md. Experimental and execution-only branches intentionally separate.

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
