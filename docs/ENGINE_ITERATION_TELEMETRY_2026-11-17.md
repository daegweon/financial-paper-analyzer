# Iteration — job-correlated Gemini telemetry (2026-11-17)

## Candidate lineage

- Frozen production: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, `finance-structured-v6.4.2`.
- Held-out lock commit: `149311ec2993cac3bd410c10ac7feb202d582fc7`.
- Clean candidate branch: `experiment/engine-quality-v6-4-2-heldout-clean`, based on `325fb7e5bda6dd05cf4888fd658018a2d8e4abbf`, which is a descendant of the held-out lock.
- First candidate code commit: `7dd13343f44702369b8a1415c750d5fdf08371f7`, after the lock commit.
- Previous PR #5 branch was found to be diverged from the lock commit and is superseded; do not merge it.

## Change

- Adds an async context variable set to the analysis job ID for the lifetime of `_process_analysis_job` and always reset in `finally`.
- Assigns a unique `provider_call_id` to each `_generate_gemini` invocation so multiple LLM passes within one analysis job can be distinguished.
- Logs per-model attempt number, model, HTTP status or transport failure, request elapsed milliseconds, finish reason and token usage.
- Logs total provider-call elapsed time, attempt count and final failure summary.
- Per-attempt elapsed time excludes the intentional 1-second inter-model fallback sleep; `total_elapsed_ms` includes it.
- Raw Gemini error response bodies are now excluded from logs for retryable 5xx/429/404, 400, 401 and 403 responses. Only status/model/timing and generic provider-error classification are retained.
- Does not log API keys, prompt text or PDF text.

## Non-change invariants

- `ANALYSIS_VERSION` remains `finance-structured-v6.4.2`.
- Prompt, schema and `extract_pages` logic remain unchanged from frozen production.
- Gemini request body, model ordering, fallback policy, timeouts, output limits, retry statuses and user result schema are unchanged.
- No data migration, provider switch, PDF parser replacement or production deployment.

## Tests and verification

Added two mocked Gemini telemetry tests (503 → fallback success; 503 + 429 → complete failure), an integration assertion that job context is set during analysis and reset afterwards, and a log-body redaction assertion. Added tests for source fingerprint capture, extraction-only preflight and Railway telemetry aggregation.

**Repository CI has not executed these tests.** GitHub Actions still returns `startup_failure` before creating jobs. No full local backend suite result is claimed. No measured runtime overhead, Gemini full-pipeline result, billable cost or peak RSS result is available.

## Log aggregation utility

`benchmark/parse_railway_telemetry.py` turns Railway timestamp/message exports into safe job-level records. Worker claim logs now include `analysis_jobs.created_at`; the parser reports both `job_created_to_terminal_ms` (includes queue wait) and `claim_to_terminal_ms`. The job-created timestamp is recorded after the PDF upload has completed, so neither metric includes file-transfer time. `full_pipeline_latency_ms` deliberately remains null until an actual upload-start timestamp is logged. The parser also joins Gemini `provider_call_id`/attempt logs, counts retries/provider attempts, sums token usage and retains per-model HTTP outcomes. It does not copy raw log messages or response bodies into output. Provider cost remains null until an explicit dated price schedule is supplied; no prices are guessed.

The output fields are `job_created_to_terminal_ms` and `claim_to_terminal_ms`. The former includes queue wait but starts after upload completion; the latter starts at worker claim. `full_pipeline_latency_ms` remains null because upload-start time is not logged. Do not feed either field into the Q2 upload-to-save p95 gate. Missing token fields remain incomplete and are never fabricated as verified zero-token usage. Q0/Q1/Q2/P0 remain BLOCKED. `final_deploy_allowed=false`.
