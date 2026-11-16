# PDF table shadow benchmark

Optional experiment only; never imported by the production request/worker path. pymupdf-text is a plain-text control, NOT the full analysis engine. Candidate counts and structural parser scores are not precision/recall.

## Local use

Use a disposable Linux Python 3.12+ environment with backend/requirements-tables-experiment.txt, PyMuPDF==1.26.7 and pytest==9.0.2. Production requirements are unchanged.

```bash
PYTHONPATH=backend:. python -m pytest -q backend/tests/test_pdf_table_experiment.py backend/tests/test_table_shadow.py
python -m benchmark.table_shadow --input-dir /private/original-pdfs --corpus benchmark/table_corpus.sha256.json --output /private/results --timeout 90
```

Local PDFs must have the original corpus filenames. Without a locked SHA-256, local identity is explicitly unverified. Never commit raw PDF/page-text/table payloads, owner IDs, credentials or signed URLs.

## Isolated execution

Use only papersignal-table-benchmark, never API/Worker. Dockerfile.tables-benchmark runs focused tests, then uses a non-root one-shot process. The experiment uses 1 vCPU / 1 GB, no public endpoint, no cron, restart NEVER and an explicitly pinned source commit. The execution-only experiment/table-benchmark-runner branch replaces railway.toml with benchmark configuration; NEVER merge it into production.

Credentials are server-side Railway references to existing API variables, never values copied to chat. BENCHMARK_STORAGE_BUCKET=papers selects the original private PDFs. BENCHMARK_UPLOAD_RESULTS=1 enables NEW JSON artifacts in the dedicated private papersignal-benchmark-artifacts bucket, not the PDF-only papers bucket. No SQL analysis/job writes occur.

Artifacts: <owner>/benchmarks/<run_id>/B01.json through B10.json. Full candidates/text are administrative-only; sanitized metrics appear in logs. Each parser receives no Storage/model credentials. Authenticated redirects are refused. Source length/ETag/page count and SHA-256 are recorded; each engine has its own process/time/RSS/version/error record.

An artifact failure does not retroactively mean parsing failed, but does make the whole process exit nonzero. Missing-bucket lookup initially returned HTTP 400, so discovery now lists buckets instead of treating arbitrary 400 errors as permission to create one. Existing public artifact buckets are rejected, not silently changed.

## Adoption gates

No automatic promotion exists; promotion_eligible stays false in this smoke runner. Before production use require visually checked independent exact-cell gold, prose/figure negative controls, complete-pipeline non-regression, predeclared time/memory/failure/cost budgets, and held-out quality repetition. The second_independent_full_benchmark_not_run blocker refers to FULL QUALITY evaluation, not the count of extraction smoke reruns.

Preserve variable/model-column/coefficient/sign/standard-error/significance/page relationships. Never choose conflicting numbers solely by structural parser score. Keep conflicting candidates for adjudication. Only identical matrices at overlapping geometry on the same page can be deduplicated.

The next candidate is bounded page-selected recovery with the current production path retained as fallback. No unrestricted default lattice+stream scan is approved. Stop changes when total-service benefit is not established; do not claim a global maximum from one configuration.
