# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-16 (Asia/Seoul), after exact-cell review preparation.
Production source: feat/research-workspace-mvp; Draft PR #2, do not merge without release gates.
Current open-source work: experiment/pdf-table-engines.
Execution-only branches: experiment/table-benchmark-runner (prior smoke) and experiment/table-cell-review-runner (current). NEVER merge their root railway.toml into production.

## Latest checkpoint

Read benchmark/results/cell-review-preparation-2026-11-16.md, its metrics JSON, and docs/CELL_REVIEW.md. Implementation commit 2eb467bb4692c1e01ceff7f07e3f3862f0cfed07 added a fail-closed exact-cell evaluator, source-first private review packets/offline viewer and bounded Stream benchmark. Local new tests: 48 passed. Full backend pytest in the isolated image: 193 passed, 1 skipped (live E2E not enabled), 6 dependency deprecation warnings, 4.00s. No frontend build or user E2E was run.

The original B01/B02/B09/B10 PDFs (86 pages) were identity-checked. Caption selection chose 23 pages. All-page versus selected-page Stream ran twice per paper in alternating order: 16 successful executions, zero parser/source/artifact errors. All eight selected-page matrix comparisons matched; fresh all-page projections matched all four prior private artifacts. Total subprocess wall across eight trials per variant: 20.565219s versus 9.869005s (52.01% reduction). Maximum child RSS: 219.316 versus 173.758 MiB. Timing excludes download, page-selection scan, rendering, upload and full AI analysis; this is NOT an overall-engine speedup or accuracy claim. Excluded-page recall remains unknown.

Four NEW private JSON review packets contain 33 source-page renders, cell geometry/matrices, source/image hashes and eight candidate negative-control pages; 9,915,979 bytes total. Every annotation list remains EMPTY. ZERO independently human-reviewed target cells; cell accuracy, table recall and negative-page hit rate unavailable. Generated images are NOT completed visual review. None of the 18 historically review-required findings was certified. Software checks review metadata; it does not authenticate human reviewers or prove they inspected a PDF.

Decision: retain bounded extraction as an experimental cost candidate only. Production path unchanged; no promotion, validator relaxation or global-maximum claim.

## Immediate next task

Use the private source-first packets to visually label and independently adjudicate exact source row/column/value, signs, companion statistics, p-values/stars/legends and page. B01/B02/B09/B10 cover 15 of the 18 historical review-required findings; B03/B05 remain outside this batch. Do NOT fabricate human approval or use parser output as its own gold. Render private packets locally with python -m benchmark.cell_review /private/B01.json --html /private/B01-review.html. Do not host private HTML publicly.

Audit the page-selection omissions, continued/captionless tables and the candidate prose/figure negative controls. No cap overflow occurred in this batch, but that does not prove complete table coverage. Historical numerical hints were for locating review pages, not labels and not selection inputs.

Then evaluate the COMPLETE existing pipeline under predeclared accuracy/time/memory/failure/provider-cost budgets and on held-out papers. Stop variants that harm supported claims or citation fidelity. The two-repeat extraction comparison is not an independent full-quality benchmark. Docling and other shortlisted parsers have not been benchmarked. Do not begin broad v6.4 heuristics merely because extraction executes.

## Infrastructure and containment

Railway project c663389c-453c-4645-a83d-299b94089864; environment 0b4f06c3-504a-4610-8995-395c2f4d3d1f.
- API 81b678e2-7136-436d-9058-7d20647dc1b7, active deployment 17c9134b-f49c-4358-a879-7ca77b55b936: SUCCESS/online, unchanged.
- Worker 238af942-0628-47d5-9280-04a49373423f, active deployment dc501061-d434-454a-bc7d-4658b991a2f1: SUCCESS/online, unchanged.
- Benchmark-only service c279046d-aedc-43bf-9e25-c09ab59fe38b, papersignal-table-benchmark: 1 vCPU / 1 GB, no public listener/domain, no cron, restart NEVER. NOW pinned to experiment/table-cell-review-runner commit 8c87af25652957fdbf868ccd0732c6c6e632ece9, Dockerfile.cell-review, python -m benchmark.cell_review_run.
- Current benchmark deployment 5155bbf1-6cfd-4e96-858a-7148886ce2fc completed. Running replicas=0; pending work empty. Do not redeploy automatically: it creates new review artifacts and uses compute.
- Production API/Worker/frontend code, production dependencies and service configuration were not changed. No model call, queue claim or analysis/job write occurred.
- Prior temporary Vercel sandbox sbx_ndWNtbHXF5WtmiZ3mVMq2Y2zIogP remains stopped; no new sandbox was created.

Supabase hwmtayrecsfxernhssro remains Free/Seoul. Before/after counts: papers=14, analyses=103, jobs completed=102/failed=28, original private PDF-only bucket objects=14. No historical paper/analysis/job was rewritten or deleted.

Existing papersignal-benchmark-artifacts bucket remains private, JSON-only, 30 MiB/object; object count increased from 10 to 14. No authenticated/anonymous artifact read policy was added. Previous raw extraction run: <owner>/benchmarks/tables-1503f4d527fa419a9d48d0576c3f616d/Bnn.json. NEW review packets: <owner>/benchmarks/cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c/B01.json, B02.json, B09.json, B10.json. Never commit raw PDF/text/images, owner IDs, credentials or signed URLs. Source access is through server-side Railway variable references, not secrets copied to chat; no re-upload needed.

## Prior exact-corpus shadow baseline

B01–B10: 10 PDFs / 209 pages, SHA-256 locked in benchmark/table_corpus.sha256.json. Prior two smoke passes each ran 30 control/parser executions. First-pass artifact uploads failed HTTP 400; fixed bucket discovery and reran. Final pass saved ten raw private artifacts with zero errors. Report: benchmark/results/table-shadow-evaluation-2026-11-16.md; guide: docs/TABLE_BENCHMARK.md.

Prior medians: PyMuPDF text control 0.716s, lattice 10.039s, stream 2.749s/PDF. Lattice9 candidates; stream263 across every page. Counts are NOT recall/precision. Prior smoke used PyMuPDF1.26.7; current isolated full-suite image uses production-pinned1.26.3. Candidate matrices matched in the four-paper comparison; don't silently treat environments as identical.

## Product, historical results and retained gates

North star: evidence-first private financial research workspace; verifiable methods/findings/significance/page evidence, cross-paper comparison; prefer verifiable incompleteness over fabricated claims.

Architecture: Next.js/React on Vercel; Supabase Auth/PostgreSQL/private Storage; FastAPI/PyMuPDF API and independent durable Railway Worker; model credentials server-side. Historical engine benchmark is finance-structured-v6.3.9; verify live versions before claiming newer versions.

Existing features: library/upload/history/search/sort, up-to-four-paper comparison, CSV/A4 reports, private source links, email/Google PKCE, owner RLS, durable leases/heartbeat/retry/checkpoints/idempotency, narrow Preview CORS and JSON-safe control-character handling.

Historical v6.3.9 B01–B10 scorecard (NOT reanalyzed here): 71 findings, 53 screen-passed, 18 review-required; 74.6% screen-passed share and 90.5% lexical Gold-fact screen. Mixed v6.1/v6.2: 24/15/9, 62.5%/84.9%. Lexical alias presence is NOT human precision/recall/citation fidelity. Overall progress estimate stays ~72%, engineering estimate not KPI.

- Audit all18 review-required findings and material numeric/page claims before broad expansion.
- Persist complete model/token/attempt/latency/cost telemetry and sustainable quotas; B02 historically retried after Gemini Free Tier quota errors.
- Complete disposable two-user upload-analysis E2E, custom SMTP/external confirmation, production-domain login/logout/relogin/upload/analysis and frontend release gates. Historical Google PKCE and three-paper flow succeeded, but two papers lacked structured findings. Historical RLS rollback tests were clean, not a substitute for current E2E.
- Resolve historical GitHub Actions startup failures; this isolated backend pytest result does not satisfy all release gates.
- Keep Supabase Free; no Pro upgrade for Leaked Password Protection. Disabled state/advisor WARN is an accepted residual risk, not a passed safeguard.
- No account auto-merge/cross-account migration. Preserve PDFs and history.
- No secrets in browser/GitHub/chat. Public papers only with free-tier model providers; never confidential/company/customer/personal data.
- Distinguish job completion from extraction quality. Choose implementation details and report verified results rather than repeatedly ask for design opinions.
- Broader remaining work: image-only OCR, beyond50-page coverage, deletion/retention/export, usage/cost/abuse observability; later knowledge graph, grounded assistant, teams/billing.

## Startup and checkpoint cadence

Read this state, PROJECT_DECISIONS.md, changelog and latest evaluation. Inspect actual branch heads/deployments/Preview/database state before changes. Update state/changelog after five substantial tasks, architecture/provider/schema/deployment decisions and handoff. Persist notes in Git; do not claim account memory is enabled.
