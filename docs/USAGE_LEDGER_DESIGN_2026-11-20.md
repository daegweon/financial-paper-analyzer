# PaperSignal per-job AI usage ledger — implementation-ready design

## Status and safety boundary

Candidate implementation exists: the additive migration `20261120120000_ai_usage_events_ledger.sql`, its disposable-PostgreSQL contract test, API per-attempt dual-write and administrator-only usage endpoints are committed to the beta candidate. Exact-head CI #44677027806 passed, including the ledger migration contract. Production Supabase remains unchanged (nine remote migrations through `20261113234956`; no `ai_usage_events` or `ai_admin_settings` tables), and Production Railway API remains on the older `ace3fbd5` deployment. A human must approve the staged migration/deployment before any Production write.

## Goals

Persist one immutable event for each provider attempt, including successful requests, HTTP failures and transport failures. Keep provider usage separate from estimated billing. Support per-job, per-paper and per-model reporting without storing prompts, extracted PDF text, model output or credentials.

## Proposed tables

### public.ai_usage_events

- id uuid primary key default gen_random_uuid()
- user_id uuid not null references auth.users(id) on delete cascade
- paper_id uuid nullable references public.papers(id) on delete set null
- analysis_job_id uuid nullable references public.analysis_jobs(id) on delete set null
- provider text not null; model text not null; attempt_index integer > 0
- outcome text in success/http_error/transport_error/invalid_response
- http_status integer nullable; error_class text nullable
- prompt_tokens, candidate_tokens, thought_tokens, total_tokens bigint nullable and nonnegative
- latency_ms integer nullable and nonnegative
- created_at timestamptz not null default now()
- idempotency_key text not null unique

Use an opaque event ID and a server-derived idempotency key from job ID + provider + model + attempt index. Never include access tokens or document contents.

### public.ai_model_price_versions

- id uuid primary key; provider/model text not null; currency char(3) not null
- input/output/thought price per million tokens numeric nullable
- effective_from timestamptz not null; effective_until nullable and later than effective_from
- source_url text not null; source_checked_at timestamptz not null; created_at timestamptz not null

Prices are effective-dated, provider/model-specific and backed by an official source. Free-tier quota consumption is not a USD price. If pricing cannot be established, estimated cost stays null. Historical usage is never assigned a price version outside its effective interval.

## Security

- Enable RLS on both tables.
- Revoke all anon/authenticated raw-event read/write privileges.
- Grant writes only to backend service_role; keep service-role key backend-only.
- No public RPC returns raw usage events.
- Index user/time, analysis_job_id, provider/model/time and price effective lookup.
- Derive ownership fields from authenticated, ownership-checked jobs; never trust caller-supplied ownership IDs.
- Do not store prompt, response, PDF text, email or tokens/credentials.

## API integration

1. Capture each provider attempt's provider/model/outcome/status/error class/token metadata/latency.
2. Persist the event with service-role credentials.
3. Persistence failure is non-fatal to analysis; emit a redacted warning.
4. Enforce idempotency so worker retry cannot double-count.
5. Keep missing provider token values null, not estimated.
6. Calculate cost by joining event time to the price version effective then. Unknown/free-tier pricing yields null cost.
7. Report attempts separately from recovered jobs. A successful fallback is an attempt; recovery requires terminal job state completed.

## Migration and rollout

1. Human review of schema, retention, privacy and pricing policy.
2. Apply additive tables, RLS and service-role grants only.
3. Deploy best-effort idempotent API/worker dual-write.
4. Verify ownership, client grants, retry idempotency and totals in staging.
5. Reconcile a controlled sample against Railway logs.
6. Only after separate approval enable aggregate user views; never expose raw events.
7. Roll back by disabling writes first; retain additive tables until separately reviewed cleanup.

## Acceptance tests

- anon/authenticated cannot read or write raw events.
- service_role writes only valid ownership-checked job context.
- duplicate idempotency key does not double-count.
- cross-user job/paper association is rejected.
- nullable token fields remain null.
- overlapping price versions are rejected and effective dates select one version.
- unknown/free-tier pricing yields null cost.
- telemetry persistence failure does not fail analysis.
- fallback attempts are distinct and recovery requires terminal completion.

## Current implementation boundary (2026-11-20)

The migration, verification SQL, API dual-write and administrator-only cost/budget endpoints are implemented on the beta candidate and covered by passing candidate CI. They are not live in Production: the remote ledger/admin-settings tables are absent and the Railway API remains on the older immutable deployment. No user-facing per-user budget exists; the budget is a single service-wide administrator setting. Keep manual DB approval, current-head Preview, real two-account E2E and rollback at the end of the release checklist.
## 2026-11-20 isolated migration implementation

The additive migration `supabase/migrations/20261120120000_ai_usage_events_ledger.sql` now implements the immutable per-attempt event table, nullable provider token fields, bounded metadata, unique idempotency key, lookup indexes, RLS and service-role-only raw event access. `supabase/tests/verify_ai_usage_events_ledger.sql` verifies role grants, service-role insertion, duplicate idempotency rejection and preservation of unknown token usage as NULL. CI applies and tests this migration only in its disposable PostgreSQL 17 service.

The migration is **not applied to Production**. The API dual-write is implemented on the candidate using verified task-local ownership context (user/paper/job IDs), but it is not deployed to the live Railway API. Do not report a persistent production ledger until the approved migration, API deployment, live writes and reconciliation are complete.

## 2026-11-20 API dual-write implementation (candidate only)

The API now sets an async task-local ownership context from `_process_analysis_job` (verified `user_id`, `paper_id`, `analysis_job_id`) and records each Gemini attempt to `ai_usage_events` using the backend-only service-role key. HTTP failures and transport errors are separate events; successful provider responses include provider-reported token counts and latency. Attempt indices are monotonically incremented within the analysis job, and the unique idempotency key is job/provider/model/attempt.

Writes use `Prefer: resolution=ignore-duplicates` and a short timeout. A missing service key/context skips recording; a ledger HTTP/network failure emits a redacted warning and never fails the analysis. No prompt, extracted PDF text, model response, API key or bearer token is stored. Unit tests cover ownership payload, null token preservation, idempotency header, missing context and non-fatal write failure.

This code is committed to the beta candidate only; no Railway deployment or Production database migration was performed. Exact-head CI #44677027806 passed all checks, including the disposable PostgreSQL ledger contract. Candidate code is tested, but the Production ledger remains unavailable until the human-approved rollout.

## 2026-11-20 effective-dated pricing and cost reporting

- Added `backend/app/model_price_catalog.json` with official Google Gemini API Standard paid rates checked 2026-11-20: Gemini 3.5 Flash-Lite ($0.30 input / $2.50 output per 1M tokens) and Gemini 3.6 Flash ($0.75 / $3.75 through 2026-12-31; $1.50 / $7.50 from 2027-01-01). Source: https://ai.google.dev/gemini-api/docs/pricing.
- Added Decimal-based cost estimator and per-paper/model report. Output pricing includes thinking tokens, so candidate + thought tokens are priced once. Unknown model, unknown billing mode or incomplete token metadata yields null cost. Free tier is zero only when explicitly confirmed.
- Added nullable `billing_mode` to the candidate ledger schema and `GEMINI_BILLING_MODE` configuration. API records only explicit `free` or `paid_standard`; default is unknown/null. Do not set this variable until the Google AI Studio project billing status is checked. No assumption is made from the presence of an API key.
- Integrated optional usage-event JSON into the quality pipeline as `ai-cost-report.json`; all outputs remain offline and read-only.
- Official rates are estimates, not invoices; refresh the versioned catalog when Google changes pricing. No Production migration or deployment has occurred.
