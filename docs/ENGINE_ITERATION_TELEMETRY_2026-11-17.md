# Iteration — job-correlated Gemini telemetry (2026-11-17)

## Change

A narrow telemetry-only candidate change on the fresh branch from frozen v6.4.2:

- Adds an async context variable set to the analysis job ID for the lifetime of _process_analysis_job and always reset in finally.
- Assigns a provider_call_id to each _generate_gemini invocation so multiple LLM passes within one analysis job can be distinguished.
- Logs per-model attempt number, model, HTTP status or transport failure, request elapsed milliseconds, finish reason and usage token counts.
- Logs total provider-call elapsed time, attempt count and final failure summary.
- Per-attempt elapsed time excludes the intentional 1-second inter-model fallback delay; total_elapsed_ms includes it.
- Does not log API keys, prompt text or PDF text.

## Non-change invariants

- ANALYSIS_VERSION remains finance-structured-v6.4.2.
- The prompt SHA-256, schema SHA-256 and extract_pages function SHA-256 match the frozen production source exactly.
- Gemini request body, model ordering, fallback policy, timeouts, output limits, retry statuses and user result schema are unchanged.
- No data migration, provider switch, PDF parser replacement or production deployment.

## Tests

Added two mocked Gemini telemetry tests (503 -> fallback success; 503 + 429 -> complete failure) and an integration assertion that job context is present during analysis and reset after completion. Tests are committed but **not yet executed** because GitHub Actions repeatedly ends in startup_failure before creating any jobs.

## Acceptance status

This is a measurement-enabling candidate only. No measured latency overhead, full suite pass, held-out Gemini run, billable cost or peak memory result is available. Q0/Q1/Q2/P0 remain BLOCKED. Do not merge or deploy until CI is repaired and full paired regression tests establish non-regression.
