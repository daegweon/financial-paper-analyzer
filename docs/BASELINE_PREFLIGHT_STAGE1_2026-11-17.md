# PaperSignal — Q0 단계별 실행 기록 (2026-11-17)

## Stage 1: locked PDF preflight and fail-closed safeguards

- Frozen model engine SHA: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` (v6.4.2); no changes to production API or Worker.
- Isolated runner branch: `experiment/v642-full-pipeline-baseline-runner-2026-11-17`.
- Latest preflight code SHA: `fc8d95ee95691750bdbe8db4708eaa79391327f3`.
- Reused the old, previously crashed Railway `papersignal-table-benchmark` service; adding a new Railway service was denied by the free-plan resource limit. This service shares the Railway production environment but is **not** the production API/Worker and is not a separately isolated Supabase DB.
- Runtime: PyMuPDF 1.26.3, `finance-structured-v6.4.2`, Gemini configured.
- The preflight downloaded the **existing private Supabase Storage originals** for B01–B10 using read-only requests. All ten passed locked SHA-256, byte-size, and PDF-page-count verification, in ascending B01–B10 order.
- Last verified preflight: `2026-11-17T01:05:28Z`–`2026-11-17T01:05:36Z`. IDs verified: B01, B02, B03, B04, B05, B06, B07, B08, B09, B10.
- H01 publisher URL responded with a non-PDF, so preflight correctly failed at H01. H02 was not attempted. There were **zero Gemini calls** in preflight and no analysis, user or paper record was written.
- Added authenticated `POST /benchmark/heldout/H01` and `POST /benchmark/heldout/H02`: accepts only exact original locked PDF bytes, enforces content type and 30 MB maximum, verifies SHA-256, size and pages with PyMuPDF, retains bytes in RAM only; no Storage write.
- Added explicit `isolated_write_guard`: the `POST /benchmark/run` endpoint refuses writes by default and additionally blocks the actual production Supabase project even if an opt-in flag is set. A separate non-production Supabase host and `BENCHMARK_ENABLE_ISOLATED_WRITES=true` are necessary for future runs. Current service is blocked from creating QA users/jobs in production.
- Local pinned sandbox tests for the new upload/write guard: **4 passed, 0 failed**. Railway Docker build ran **106 passed, 1 skipped**, and the latest runner deployment succeeded. A skip is not a passing live E2E test.
- No baseline result, Gemini latency, billed cost, overall p95 or peak-RSS result was generated. Q0/Q1/Q2/P0 all remain **BLOCKED**.

## Next independent stage (do not silently skip)

1. Deliver the same original H01/H02 uploaded in ChatGPT into the authenticated in-memory runner endpoint; do **not** substitute another publisher download because the hashes are locked. Files are present in the ChatGPT conversation, but the Railway service cannot access ChatGPT attachment bytes by itself.
2. Re-run read-only preflight to obtain all 12 SHA-verified PDFs. Keep Q0 blocked until this is done.
3. Provision/use a truly non-production Supabase database or implement explicitly labeled persistence simulation; never write QA users/jobs in the production Supabase project.
4. Run frozen v6.4.2 12-paper Gemini benchmark in matched conditions; then run the telemetry-only candidate and measure p95, tokens, real cost and RSS.
5. Independent human gold + final release gates remain pending; no production deployment authorized.

**Do not assume an in-memory upload is persisted between service restarts.**
