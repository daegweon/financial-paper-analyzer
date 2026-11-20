# PaperSignal per-job AI usage ledger — implementation-ready design

## Status and safety boundary

Design only. This document does not create a migration, table, secret, deployment or production write. The production Supabase project remains unchanged. A human must review the migration and staged rollout before it is applied.

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

## Current implementation boundary

Current log telemetry and offline reports are available. This design is not implemented in production. Keep manual DB approval and two-user live E2E at the end of the release checklist.