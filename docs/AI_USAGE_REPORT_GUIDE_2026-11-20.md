# PaperSignal AI usage report utility

## Run locally

Export the PaperSignal API service logs from Railway as UTF-8 text, then run:

```bash
cd backend
python -m app.usage_report /path/to/railway-api.log
```

The JSON output groups Gemini activity by model and reports:
- attempt count and HTTP error rate;
- provider-reported prompt, candidate, thought and total token sums;
- median and p95 per-request latency;
- median and p95 completed analysis-job duration.

Transport failures are counted as attempts when the structured log contains a model and error type. They are not assigned invented HTTP status codes. A request's latency is counted once from the attempt telemetry line, not again from the usage line. Job duration is separate from model latency.

## Privacy and interpretation

The utility reads only the structured key/value fields emitted by PaperSignal. It does not output prompts, PDF text, model responses, user identifiers or credentials. Review exported logs before sharing them.

Token totals are provider-reported observations, not USD billing estimates. Do not compare free-tier quota usage with paid pricing. Missing provider token fields remain absent/zero in sums and must not be estimated.

This utility is an offline reporting tool. It does not fetch logs, connect to Railway, persist customer usage, or change production settings.
