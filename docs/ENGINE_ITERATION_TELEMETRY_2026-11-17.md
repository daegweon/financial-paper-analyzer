# PaperSignal — candidate telemetry and extraction preflight (2026-11-17)

## Candidate lineage

- Frozen production: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`.
- H01/H02 lock: `149311ec2993cac3bd410c10ac7feb202d582fc7`.
- B01-B10 first SHA manifest: `342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c`.
- B01-B10 lock-reference commit and candidate base: `14ed46fd032b42813dd0ccf372447bd71bd363aa`.
- First candidate code commit: `ef8b941315765ed45b65c8065b2a35a613f4aced`.
- Latest candidate commit: `50d020e6a960086d4de3a12e94744c51083e1c72`.

## Telemetry changes

- Set an async context variable to the analysis job ID for the lifetime of `_process_analysis_job`, reset in `finally`.
- Assign unique `provider_call_id` to each `_generate_gemini` call.
- Log per-model attempt, model, HTTP/transport outcome, elapsed time, finish reason and token usage.
- Log provider-call attempt count, total elapsed time and failure summary.
- Redact raw provider error response bodies from retryable 5xx/429/404, 400, 401 and 403 logs.
- Worker claim event now includes `analysis_jobs.created_at`; parser emits `job_created_to_terminal_ms` and `claim_to_terminal_ms`. These start after upload completion. `full_pipeline_latency_ms` remains null because upload-start time is not logged.
- Prompt, schema, extraction logic, request body, model ordering, retry policy, analysis version and result schema remain unchanged.

## Extraction-only preflight

Exact production extraction logic, local PyMuPDF 1.26.7 (production pin 1.26.3), B01-B10:
- 209 pages scanned, 0 empty-text pages, 691,985 extracted characters.
- Five local runs per PDF; sum of per-paper medians 683.767 ms.
- This is not full-pipeline latency and not Q2 evidence.

## Verification limits

New-branch GitHub Actions run 43969788375 ended with `startup_failure` before creating any jobs (jobs=0). GitHub rejected a retry with HTTP 403 because the run is not retryable. This is an infrastructure/startup failure, not a passing or failing repository test result. No repository test pass, Gemini baseline, measured telemetry overhead, full-pipeline latency, provider cost or peak RSS is claimed. Q0/Q1/Q2/P0 remain blocked. No production deployment or Supabase data mutation.
