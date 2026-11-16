# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-16 (Asia/Seoul).
Production source: feat/research-workspace-mvp; Draft PR #2, do not merge without release gates.
Current open-source work: experiment/pdf-table-engines.
Execution-only branch: experiment/table-benchmark-runner. NEVER merge its root railway.toml into production.

## Latest checkpoint

Read benchmark/results/table-shadow-evaluation-2026-11-16.md and docs/TABLE_BENCHMARK.md first. The prior private-PDF access blocker is resolved using server-side Railway variable references. Do not ask for re-upload or retrieve service-role values into chat.

Optional Camelot 1.0.9 adapter hardened; explicit diagnostics, conflict-preserving deduplication and exact-source shadow benchmark implemented. Focused suites: 43 passed locally and 43 passed in final Railway BuildKit, including real synthetic-PDF lattice/stream extraction. Full production regression suite was NOT rerun.

Original B01–B10: 10 PDFs, 209 pages. Byte length, ETag and page count checked; SHA-256 locked in benchmark/table_corpus.sha256.json. Two complete extraction passes, each with 30 control/parser executions, had no extraction failures and matching per-paper hashes/candidate counts. First-pass artifact persistence failed with HTTP 400; bucket discovery was fixed and retested. Final pass had zero source/artifact errors and saved ten private result JSON objects.

Decision: DO NOT enable unrestricted all-page Camelot in production. Final medians: text control 0.716s, lattice 10.039s, stream 2.749s per PDF. Lattice produced 9 candidates from B04/B07 only and peaked at 554.008 MiB; Stream produced 263 candidates across every page and peaked at 268.543 MiB. Counts are NOT true-table recall. Numeric-cell, model-column and citation accuracy remain unverified. No overall engine quality gain or global performance maximum is claimed.

## Next task

Construct visually checked, independently reviewed exact-cell gold, prioritizing B01/B02/B09/B10 and the 18 historically review-required findings. Record variable, model column, coefficient/sign, standard error, stars/p-value/legend and page; include prose/figure negative controls. Use the saved raw private artifacts, not log-count proxies.

Then compare bounded page-selected Stream recovery (Lattice only where warranted) against the COMPLETE existing pipeline under predeclared quality/time/memory/failure/cost budgets. No regression in existing supported claims or citation fidelity is allowed. Stop changes whose gain does not justify total-service overhead. Test held-out papers before promotion. Two extraction smoke passes do not satisfy the independent full-quality-benchmark gate. Docling and other shortlisted parsers have not been benchmarked in this checkpoint.

## Infrastructure and containment

Railway project c663389c-453c-4645-a83d-299b94089864; environment 0b4f06c3-504a-4610-8995-395c2f4d3d1f.
- API service 81b678e2-7136-436d-9058-7d20647dc1b7, active deployment 17c9134b-f49c-4358-a879-7ca77b55b936: SUCCESS/online, unchanged.
- Worker 238af942-0628-47d5-9280-04a49373423f, deployment dc501061-d434-454a-bc7d-4658b991a2f1: SUCCESS/online, unchanged.
- Benchmark-only service c279046d-aedc-43bf-9e25-c09ab59fe38b, papersignal-table-benchmark: 1 vCPU / 1 GB, no public listener/domain, no cron, restart NEVER, pinned runner commit d1a4b4e33ef8e898058cb0ef21b151843f74ea5c. Final deployment 20becdfa-272f-448f-a347-68af3c8f33b3 finished; running replicas=0, pending work empty.
- API/Worker/frontend code, production dependency files and production service configuration were not changed. Historical failed builds in Railway's lookback predate this experiment.
- Temporary Vercel sandbox sbx_ndWNtbHXF5WtmiZ3mVMq2Y2zIogP was stopped; its pre-existing source snapshot was not deleted.

Supabase hwmtayrecsfxernhssro remains Free/Seoul. Original private papers bucket is still PDF-only, 30 MiB/object, 14 objects; papers table 14 rows; jobs completed=102, failed=28. No historical analysis or job was rewritten or deleted. No model/provider call or queue claim occurred.

New papersignal-benchmark-artifacts bucket: private, JSON-only, 30 MiB/object, 10 objects. Existing Storage RLS policies only cover papers; no authenticated/anonymous artifact policy was added. Administrative-only raw artifacts are under <owner>/benchmarks/tables-1503f4d527fa419a9d48d0576c3f616d/Bnn.json. Never commit raw PDF/text payloads, owner identifiers, secrets or signed URLs.

## Product and historical baseline

North star: evidence-first financial research workspace, verifiable methods/findings/significance/page evidence, private library and cross-paper comparison. Prefer verifiable incompleteness over fabricated claims.

Architecture: Next.js/React on Vercel; Supabase Auth/PostgreSQL/private Storage; FastAPI/PyMuPDF API plus independent durable Railway Worker; model credentials server-side. Historical recorded engine benchmark is finance-structured-v6.3.9; verify live versions instead of assuming from notes.

Existing features include library/upload/history/search/sort, up-to-four-paper comparison, CSV/A4 reports, private source links, email/Google PKCE, owner RLS, durable leases/heartbeat/retry/checkpoints/idempotency, narrow Preview CORS and control-character-safe JSON persistence.

Historical v6.3.9 B01–B10 scorecard (NOT rerun here): 71 findings, 53 screen-passed, 18 review-required; 74.6% screen-passed share and 90.5% weighted lexical Gold-fact screen. Mixed v6.1/v6.2 baseline: 24 findings, 15 screen-passed, 9 review-required; 62.5% and 84.9%. Lexical alias presence is NOT human-verified precision/recall or citation fidelity. Overall progress estimate stays approximately 72%, an engineering estimate, not a KPI. Do not increase it because an optional parser executes.

Google PKCE real-user login and three-paper analysis previously succeeded, but two papers had no structured findings. Google and legacy email identities remain separate; no automatic merge. Historical RLS rollback tests were clean; complete current two-user live E2E remains a release gate.

## Retained release gates and decisions

- Audit all 18 review-required findings and material numeric/page-citation claims before broad engine expansion.
- Persist complete model/token/provider-attempt/latency/cost telemetry. B02 previously needed retry after Gemini Free Tier quota errors; sustained public-beta quota sufficiency is not established.
- Complete disposable two-user upload-analysis E2E, custom SMTP/external confirmation, and production-domain sign-in/logout/relogin/upload/analysis verification.
- Resolve historical GitHub Actions runner startup failures. Focused Railway BuildKit tests do not replace the full release suite.
- Keep Supabase Free; no Pro upgrade solely for Leaked Password Protection. Its disabled state/advisor WARN remains an accepted residual risk, not a passed safeguard.
- No automatic account merge/cross-account migration. Preserve PDFs, historical analyses and user data.
- No secrets in browser/GitHub/chat. Public papers only with free-tier model providers; never confidential/company/customer/personal data.
- Distinguish job completion from extraction quality. The user prefers implemented choices and verified results over repeated design questions.
- Remaining broader work: image-only PDF OCR, beyond-50-page coverage, deletion/retention/export, usage/cost/abuse observability; later knowledge graph, grounded assistant, teams and billing.

## Startup and checkpoint cadence

Read this state, docs/PROJECT_DECISIONS.md, changelog and latest evaluation. Inspect actual branch heads, Railway deployments, Vercel Preview and Supabase state. Resolve discrepancies before further edits. Update state/changelog after five substantial tasks, major architecture/provider/schema/deployment decisions and handoff. Save notes in Git; do not claim account memory is enabled. Continue the recorded next task without requiring the user to reconstruct context.
