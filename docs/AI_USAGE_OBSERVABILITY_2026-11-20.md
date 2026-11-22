# PaperSignal — AI usage and latency observability (2026-11-20)

# Current implementation status — 2026-11-22

The original 2026-11-20 scope below is a historical description of the first log-only telemetry increment. The durable ledger and administrator reporting have since been implemented.

- Migration `20261120122819_ai_usage_events_ledger` creates `public.ai_usage_events` for provider/model/attempt outcome, billing mode, HTTP/error metadata, token counts, latency, idempotency key and timestamp. The table is forced-RLS and browser roles have no privileges; the trusted service role has SELECT/INSERT.
- `public.ai_admin_settings` stores the administrator's global monthly budget. It is forced-RLS and service-role-only; the server has the SELECT/INSERT/UPDATE privileges required for the admin setting.
- Backend modules: `backend/app/cost_estimator.py`, `backend/app/cost_report.py`, and `backend/app/model_price_catalog.json`. The price catalog is date-effective and source-linked.
- The admin reporting path groups usage by paper/provider/model/month and provides administrator-level user/paper/month summaries. Admin UI: `/admin/ai-usage`.
- Cost statuses distinguish confirmed Free tier, estimated Paid Standard, unknown billing mode, incomplete token usage and missing price. Unknown or incomplete data remains null; it is never silently treated as zero.
- The report is an administrator operational estimate, **not an invoice or an automatic hard spending cap**. The actual Gemini billing tier still needs confirmation in Google AI Studio before a billing-mode value is configured.
- Production migration ledger was checked on 2026-11-22: 14 versions applied through `20261121032957`.

---


## Scope

This increment adds operational telemetry to the existing Gemini request path without changing prompts, model selection, output schemas, retry policy, database schema, user-facing paper results, or production configuration.

## Events

The API emits structured, content-free log fields:

- Gemini attempt telemetry: provider, model, HTTP status (or transport error class), per-attempt latency in milliseconds.
- Gemini usage: provider, model, finish reason, prompt tokens, candidate tokens, thought tokens, total tokens, and request latency in milliseconds.
- Analysis job completed: job/paper IDs, provider, model, scanned page count and end-to-end job duration in milliseconds.
- Failed/crashed jobs also record elapsed duration.

No API key, bearer token, prompt, extracted PDF text, model response, or customer document content is included in these telemetry messages.

## How to use

In Railway API logs, filter Gemini usage provider=gemini to inspect successful model token consumption, and Gemini attempt telemetry provider=gemini to compare primary/fallback attempts and latency. Compare the job-level duration_ms with provider attempt latency to estimate non-model overhead.

A completed analysis that resumed from a durable result checkpoint will not incur another Gemini call; its job duration should be interpreted separately from a fresh provider call.

## Limits and next step

- These are operational logs, not yet a durable normalized usage ledger. Log retention and aggregation depend on the Railway plan/configuration.
- Gemini token counts are recorded when the provider supplies usageMetadata; missing counts remain absent rather than being estimated.
- This change does not invent USD costs. A cost ledger requires a versioned, date-effective pricing schedule and model-specific billing semantics; free-tier quota consumption is not equivalent to retail API cost.
- Before public beta, persist per-job usage events (including failed attempts) in a service-role-only table and compute estimated cost from an explicitly maintained pricing schedule. This requires a separately reviewed additive database migration and rollout.
- No production database migration, deployment, user-data change or model-quality change is part of this increment.

## Verification

The backend regression test stubs Gemini usage metadata and asserts prompt/candidate/thought/total token counts and request latency appear in logs. Full CI also validates API, frontend, isolated PostgreSQL, synthetic browser workflows and a read-only live API probe.
