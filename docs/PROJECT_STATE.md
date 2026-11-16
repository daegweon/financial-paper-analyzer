# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-16 (Asia/Seoul), after first actual assistant visual draft audit.
Production source: feat/research-workspace-mvp; Draft PR #2, do not merge without release gates.
Current open-source work: experiment/pdf-table-engines.
Execution-only branches: experiment/table-benchmark-runner, experiment/table-cell-review-runner, experiment/source-visual-audit-runner and experiment/visual-draft-audit-runner. NEVER merge their root railway.toml into production.

## Latest checkpoint — actual source audit found shared missing table

Read benchmark/results/visual-draft-audit-2026-11-16.md and visual-draft-metrics-2026-11-16.json. Implementation da3f12dd108e2f44e53f7fdf55b13a224b7c4fef adds four isolated experimental/test files, no production changes. Local new tests: 37 passed in 0.08s. Railway's mandatory RUN pytest -q build gate succeeded; exact terminal test count not recovered, so do not invent a new count. Live E2E and frontend build not run.

The assistant ACTUALLY VIEWED source raster crops before candidate output: B01 PDF p18/Table2 and B10 PDF p12/Table5. Source PDF hashes, crop hashes and native word anchors are bound to 15 primary draft targets / 25 numeric cells. Drafts are in benchmark/visual_drafts_20261116.json as expected-text digests plus geometry. They are explicitly review_origin=assistant and visual_draft. ZERO independently human-reviewed gold targets. Existing independent-human-review gate is unchanged; no review-required finding was promoted.

Frozen-output checks against all-page/selected-page Stream, two prior repeats each: 60 checks, 40 agreements, 20 missing, zero unassessed. B10's 10 targets agree in all four saved variants. B01's 5 parameter targets (each with Std. Dev. and t-stat companions) are missing in all four. Original B01 p18 candidate payload contains only a Table4 region, not the visually confirmed Table2. This is a WITHIN-PAGE omission in an already selected page, not a page-cap omission. All-vs-selected matrix equality did NOT prove source completeness. These counts are purposive assistant-draft diagnostics, not general accuracy or 60 independent samples/new parser executions.

Source distinctions: B01 variables run across columns; preserve printed Std. Dev. without relabelling as standard error. B10 Table5 return-constraint row3 has volatility0.20 and Sharpe0.15; this is a wrong-column rejection control, not evidence that production made that specific error. No p-values/stars were inferred.

Native-source caption scan across B01/B02/B09/B10 (86 pages) found32 caption instances all within23 previously selected pages. B01/B02/B09/B10 counts11/7/5/9. This is not an independent visual census; captionless/image tables,63 excluded pages and prose/figure negative controls remain unaudited. B02/B09 source cells were NOT visually reviewed in this checkpoint.

## Immediate next task

Do NOT promote page-selected Camelot merely because it is faster. Investigate caption/geometry-bounded TABLE-REGION recovery for pages with multiple tables, starting with the now-proven B01 p18/Table2 omission. Do not use known numeric answers to find regions. Preserve frozen drafts and compare untouched control pages; do not relax numeric, sign, star, source or conflict checks to make results pass.

Complete source-first visual drafts for B02/B09 and remaining B01/B10 tables, then independent human adjudication of all18 historical review-required findings (B03/B05 outside the four-paper priority batch). Draft assistant observations cannot impersonate two human reviewers. Audit continued/captionless tables and negative controls. Source access is already solved server-side; do not request re-upload or retrieve service-role values into chat.

After that, evaluate the COMPLETE pipeline under predeclared quality/time/memory/failure/provider-cost budgets and held-out papers. Stop variants harming supported claims, citation fidelity or total service performance. Docling and other shortlisted parsers have not yet been benchmarked. No broad v6.4 heuristic expansion or global-maximum claim.

## Infrastructure and containment

Railway project c663389c-453c-4645-a83d-299b94089864; environment0b4f06c3-504a-4610-8995-395c2f4d3d1f.
- API81b678e2-7136-436d-9058-7d20647dc1b7: deployment17c9134b-f49c-4358-a879-7ca77b55b936 SUCCESS/online, unchanged.
- Worker238af942-0628-47d5-9280-04a49373423f: deploymentdc501061-d434-454a-bc7d-4658b991a2f1 SUCCESS/online, unchanged.
- Benchmarkc279046d-aedc-43bf-9e25-c09ab59fe38b:1vCPU/1GB,no public listener/domain/cron,restartNEVER. NOW pinned experiment/visual-draft-audit-runner commitfb5895d28336c9ed9da6c4d32f6bb674b5e649fa, Dockerfile.cell-review, python -m benchmark.draft_cell_audit_run.
- Deploymentb61322f7-edf3-4d71-a830-a4884c09862e finished SUCCESS; running replicas0,pending work empty. Do not automatically redeploy: it consumes compute and writes new audit artifacts.
- Runvisual-draft-audit-c569a95eb0f44b608a608493de8a9910 completed four documents with zero errors. No new parser/model call, queue claim or analysis/job write.
- Temporary encrypted-export runner commits13babfa and2aff4ac were execution-only. No raw PDF/image publicly served or committed, no credentials exported; first guessed pages were not labelled, then source-native target location corrected them. Do not merge export runner configuration into production.
- Prior Vercel sandboxsbx_ndWNtbHXF5WtmiZ3mVMq2Y2zIogP remains stopped; no new sandbox or frontend deployment.

Supabasehwmtayrecsfxernhssro remains Free/Seoul. Verified counts:papers14,analyses103,jobs completed102/failed28,original private PDF-only bucket14objects. No historical data rewritten/deleted. Private JSON-only papersignal-benchmark-artifacts now18objects (previous14); four append-only draft-audit artifacts, no new public/authenticated/anonymous read policy or schema/RLS change.

Private namespaces under <owner>/benchmarks/:
- tables-1503f4d527fa419a9d48d0576c3f616d/Bnn.json: original ten-paper raw extraction.
- cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c/B01.json,B02.json,B09.json,B10.json: source images/cells,33 source renders,8 candidate negative pages; original annotations still empty.
- visual-draft-audit-c569a95eb0f44b608a608493de8a9910/B01.json,B02.json,B09.json,B10.json: compact audit outcomes/inventories, not human gold.
Never commit raw PDF/text/image payloads,owner IDs,secrets or signed URLs. Draft text digests are not encryption. Credentials stay server-side Railway references. Offline private viewer: python -m benchmark.cell_review /private/B01.json --html /private/review.html; never host publicly.

## Historical extraction experiments (not full-engine performance)

B01–B10:10PDFs/209pages,SHA locked in benchmark/table_corpus.sha256.json. Two smoke passes each30control/parser executions. First artifact uploads failedHTTP400; bucket discovery fixed and full run repeated successfully. Prior medians:PyMuPDF text0.716s,lattice10.039s,stream2.749s/PDF. Lattice9candidates;stream263across everypage; counts are not recall. Prior smoke PyMuPDF1.26.7; later isolated image uses production-pinned1.26.3. See table-shadow-evaluation-2026-11-16.md and docs/TABLE_BENCHMARK.md.

Prior four-paper experiment:86pages,23selected,16successfulextractions,8/8selected-matrix matches,4/4prior-projection matches. Sum wall20.565219s vs9.869005s(52.01%less);maxchildRSS219.316vs173.758MiB. Excludes transfers/selection/render/upload/AI; NOT overall-engine gain. The NEW visual audit demonstrates shared omissions. Prior full pytest193passed/1skipped/6deprecationwarnings(4.00s) was the preparation checkpoint, not a current total. See cell-review-preparation-2026-11-16.md and docs/CELL_REVIEW.md.

## Product, historical results and retained release gates

North star:evidence-first private financial research workspace;verifiable methods/findings/significance/page evidence,cross-paper comparison;prefer verifiable incompleteness over fabrication. Architecture:Next.js/React on Vercel;Supabase Auth/PostgreSQL/private Storage;FastAPI/PyMuPDF API and independent durable RailwayWorker;server-side model credentials.

Existing:library/upload/history/search/sort,up-to-four-paper comparison,CSV/A4reports,private source links,email/GooglePKCE,ownerRLS,durable leases/heartbeats/retry/checkpoints/idempotency,narrow PreviewCORS,JSON-safe control-character handling. Historical enginefinance-structured-v6.3.9;verify live versions before claiming newer.

Historical ten-paper scorecard(not rerun):71findings,53screen-passed,18review-required;74.6%screen-passed share,90.5%lexicalGold screen. Mixedv6.1/v6.2:24/15/9,62.5%/84.9%. Lexical presence is not human precision/recall/citation fidelity. Overall progress~72%,engineeringestimate notKPI,unchanged.

- Audit all18review-required findings/material numeric-pageclaims before broad expansion.
- Persist model/token/attempt/latency/cost telemetry; sustainable quotas unresolved after historicalB02FreeTier retry.
- Disposabletwo-user live upload-analysisE2E,customSMTP/externalconfirmation,production-domainlogin/logout/relogin/upload/analysis,frontendrelease gates remain. HistoricalGooglePKCE/three-paperflow succeeded;two papers lackedfindings. HistoricalRLSrollback not substitute for currentE2E.
- Resolve historicalGitHubActionsstartupfailures;backendbuild alone not all releasegates.
- Supabase staysFree;noProupgrade for LeakedPasswordProtection;disabled/advisorWARN accepted residualrisk,notpassed safeguard.
- No accountauto-merge/cross-accountmigration;preserve papers/history.
- No secrets in browser/GitHub/chat. Publicpapers only on FreeTierproviders;no confidential/company/customer/personaldata.
- Distinguish jobcompletion fromquality. Assistant chooses implementation details;do not repeatedly ask designquestions.
- Remaining:image-onlyOCR,beyond50pages,deletion/retention/export,usage/cost/abuseobservability;later knowledgegraph,groundedassistant,teams/billing.

## Startup and checkpoint cadence

Read this state,PROJECT_DECISIONS.md,changelog,latest evaluation. Inspect actual branch/deployment/Preview/database before claims. Update after five substantialtasks,majorarchitecture/provider/schema/deploymentdecisions and handoff. Persist inGit;do not claim accountmemory enabled.
