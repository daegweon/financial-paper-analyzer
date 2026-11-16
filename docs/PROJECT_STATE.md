# PaperSignal — Project State / Session Handoff

## 2026-11-17 NEW USER DECISION — OVERRIDES OLD "ENGINE FROZEN" EXPERIMENT TEXT

**Open-source parser replacement research is OVER. Resume improving the EXISTING PyMuPDF / finance-structured-v6.4.2 analysis engine in a separate, gated development branch.** The engine was frozen during OSS comparisons only; the user has now explicitly authorized resuming its improvement. Hard stop when independently verified quality/resource/production release thresholds are met, followed by final release. Do NOT continue the OSS candidate hunt.

**Canonical cross-session handoff:** `plan/engine-quality-release-handoff` commit `2e71924bf0801bca9798fddeadb9357cf0f5e05a`, `docs/SESSION_HANDOFF_NEXT.md`, `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md`, `benchmark/engine_release_gates_2026-11-17.json`. Read these FIRST; previous "immediate next task" and "frozen forever" text below is superseded. This is a GitHub checkpoint, NOT ChatGPT saved memory (project memory is off). No production branch update or automatic deployment authorized by this pointer.

---


## 2026-11-17 (Asia/Seoul) — Full-model A/B attempted, deterministic ten-paper evidence replay completed

**Production remains FROZEN**, unchanged on commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, API and Worker SUCCESS/online. User authorized full-analysis Docling Parse vs PyMuPDF A/B as an isolated experiment. Source code of downstream `llm_result`, schemas, finding checks and prompts is identical to deployed v6.4.2; only PDF extraction boundary differs in experiment.

**Fresh full Gemini A/B: INCOMPLETE/BLOCKED, not a win for either engine.** Isolated B01 baseline PyMuPDF arm had Gemini 3.5 Flash Lite HTTP 503 and fallback Gemini 3.6 Flash HTTP 503 (deployment `25ec3be7-09c9-48ad-814d-152f984a9380`); identical on B03 (deployment `521aaccd-dbe4-4f82-a9a6-55dfb2e6f98a`). No paired model-backed results, so zero measured full-model precision/cost/latency improvement. Tiny synthetic Gemini primary probe HTTP 200, fallback read timeout, so provider is partially reachable. Do NOT claim root cause proved; no uncontrolled retries. The benchmark rejects extractive fallback and never writes analyses/jobs.

**Deterministic source-evidence replay: 10/10 original B01–B10, 209 pages, COMPLETED**, in isolated Railway deployment `5d169fb9-fbf1-4781-b080-05cb6ba949e5` (SUCCESS; running replicas 0). Reused the same historical v6.3.9 structured findings and page quotes against PyMuPDF and Docling Parse extraction using current v6.4.2 validation. 346/346 prior citations still verifiable on baseline versus **296/346** on Docling (50 lost; 85.55%); directly-evidenced findings **71 vs 65** (6 lost); current-validator screened-pass findings **54 vs 51** (3 lost); B02 worst major regression (48→32 quotes; 8→4 findings). Parser-only wall sums **8.2202s vs 33.9086s** (Docling ~4.13× slower); maximum child RSS **101.25 MiB vs 664.73 MiB**. These are not fresh model quality metrics, nor independently human-verified correctness; source layout changes may explain quote matching, but the existing pipeline would reject those claims.

**Decision: Docling Parse full replacement is NOT approved.** No engine modifications while user freeze applies. Revisit only after independently checking source quotes/layout, repairing parser-only source quote preservation without weakening numeric checks, paired full-model reruns after provider recovers, and complete resource/held-out/human gates. 18 historical review-required findings remain uncertified. Historical v6.3.9 score (53 passed) differs from current v6.4.2 replay validator (54); do not conflate.

**Durable artifacts**
- Source & one-shot runner `experiment/full-analysis-ab-runner`, measured report `benchmark/results/full-analysis-docling-ab-replay-2026-11-17.md`, JSON scorecard same basename `.json`; report commit `d5cefc46737362514ba91b998bf73ecccd99c783`.
- Private Storage run `replay-49dfcc9e5d9b4c0485ff70bcc1f56028`: 10 new JSON-only per-paper artifacts, no public policy. Frozen originals untouched.
- One experimental image initially lacked pdfminer.six; repaired by pinned dependency and 7 passed focused build tests, then exact ten-paper replay. Standard AI A/B failures and provider probe are recorded with only sanitized status/token metadata.
- Database verified unchanged: 14 papers, 103 analyses, 102 historically completed jobs, 28 failed jobs, 14 private PDFs. Private JSON benchmark artifacts 85 including historical experiments. Model-call opt-in on the benchmark service was disabled after the run. All benchmark replicas 0; API/Worker each 1 running, both on existing commit.
- No frontend deployment or user data modification.

**DO NOT run model batches or promote parser variants without a new user request.** Next session must read this checkpoint and benchmark report first. Engine-development freeze remains in effect.

---


## 2026-11-16 — engine FROZEN; full PyMuPDF replacement experiment executed

User explicitly froze further engine development and authorized isolated attempts to replace PyMuPDF in full with Docling or Camelot. **No production code, dependency, provider, analysis/job or deployment changes.** Live Railway API/Worker SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` remains; source version `finance-structured-v6.4.2`. Do not treat historical v6.3.9 benchmark scores as current.

Experimental replacement of `extract_pages` (no PyMuPDF fallback): Camelot+pdfminer 10/10 and Docling Parse 7.26.0 10/10 original PDFs, 209 pages, zero candidate/process errors in successful options. Docling standard 2.150.0 was installed but failed 4/4 runtime conversions (unclassified exit1); docling-slim Native path failed 4/4 (ImportError in isolated follow-up). Full details: `docs/FULL_PDF_PARSER_REPLACEMENT_TRIAL_2026-11-16.md`. On the frozen prior PyMuPDF token proxy, mean per-paper numeric retention 91.20% Camelot composite vs 95.52% Docling Parse, but **no independent source accuracy or full AI pipeline improvement validated**. Docling Parse max child RSS 651.25 MiB vs Camelot 245.45 MiB. Keep both alternatives experimental; no promotion.

Existing 18 historical review-required findings, provider-cost/latency telemetry and human citation audit remain open. Production unchanged; no automatic follow-on engine improvement while freeze stands. Do not merge runner-root railway.toml. Existing changelog below records earlier historical checkpoints.

---


## 2026-11-16 final OSS decision — supersedes the experimental next-task sections below

**CLOSED: no new OSS parser adoption in production.** User direction is to stop broad parser comparisons. Camelot page-selected runs reduced *extraction-only* wall time by 52.01% on four PDFs, but frozen original-source visual drafts show B01 p18 Table 2's five parameter targets missing from BOTH all-page and selected-page Stream. There is no certified cell/whole-engine accuracy gain, and 0 independent human-reviewed cells. Neither Camelot nor other untested parsers are approved. Do not continue caption/geometry recovery experiments as part of the OSS workstream; direct subsequent engineering to the existing production stack and unresolved 18 review-required findings, durable token/cost telemetry and release gates. See docs/OPEN_SOURCE_ADOPTION_DECISION_2026-11-16.md.

**Version correction:** The inspected Railway API/Worker deployment uses Git commit 8cd5e37ee8eab3bf4b726b75af89e410ab48396e, and its source contains `finance-structured-v6.4.2`; prior `v6.3.9` metrics are historical and not a benchmark of that current commit. Historical state text below is preserved for audit but is not a current version assertion.

**No production changes from this closure.** All experimental raw source artifacts stay private. Final experiment-only decision file and machine-readable gate snapshot are in Git. This top section supersedes older "Immediate next task" statements related to parser exploration.

---


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
