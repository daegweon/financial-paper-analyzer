# PaperSignal integrated release candidate — 2026-11-20

## Candidate scope

This branch rebuilds PR #18's product functionality on top of the current `main` authentication, mobile logout, CI-cost and live-E2E work. PR #18 remains Draft and is not merged.

Included:
- Original publisher PDF displayed in the browser through the user's private Supabase signed URL; page navigation uses the original PDF rather than reconstructing pages as HTML.
- Research Library, analysis status recovery, active-job discovery and durable queue polling.
- Page-linked evidence navigation, cross-paper comparison and junior-oriented methodology/workplace guides.
- Table and graph reading learning cards.
- Administrator-only, service-wide AI usage and cost console. Ordinary users do not receive individual AI cost budgets or raw usage-ledger access.
- Analysis v6.4.2 API, worker-compatible durable job processing, atomic queue limits and privacy-minimized AI provider-attempt telemetry.
- Mobile-first Google sign-in and tablet/mobile logout. Auth bootstrap uses `getSession()` plus the auth-state subscription to avoid the stale `getUser()`/logout race.

## Production migration baseline

The exact 13 migrations currently recorded by the live Supabase `supabase_migrations.schema_migrations` table have been mirrored into `supabase/migrations` using their recorded version, name and SQL statements. The two old local-only migration filenames that did not match the remote history were removed. See `docs/PRODUCTION_MIGRATION_BASELINE_2026-11-20.md`.

New additive Production migrations applied:
- `20261120122747_server_owned_analysis_quota`: server-only `enqueue_analysis_job(uuid,uuid)` RPC. EXECUTE is denied to PUBLIC/anon/authenticated and granted to service_role.
- `20261120122819_ai_usage_events_ledger`: private, RLS/FORCE-RLS usage ledger and administrator settings table; no browser-role grants.
- `20261120122859_index_ai_usage_ledger_foreign_keys`: indexes for the new ledger/admin foreign keys.

Previously applied and retained:
- `20261120102957_beta_server_owned_result_writes`: client cannot forge analyses/jobs or update trusted status fields; server_role retains worker/API writes.

## Production state and rollout boundary

- Existing API rollback baseline: Railway deployment `0b5716db-b720-49db-b15c-babf77b26e5a`, commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732`.
- Existing Worker: deployment `dc501061-d434-454a-bc7d-4658b991a2f1`, commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`.
- The API/Worker above remain live and were not changed by this branch. The candidate API now calls the server-only quota RPC and writes usage events, so deploy it only after the migration checks below pass.
- Admin UUID allowlist and Gemini billing mode are intentionally unset until the administrator is designated and the Google AI Studio billing tier is confirmed. Cost remains unknown rather than being fabricated as zero.
- The 5-per-24-hour and 2-concurrent-job controls are abuse/queue-rate limits, not user-managed AI budgets. Service-wide AI budget remains an administrator-only setting.
- Do not promote Vercel Production until the integrated Preview and exact-head CI pass. Keep the prior production deployment available for rollback.

## Verification already available

- Actual two-account synthetic production E2E passed: [GitHub Actions #44722388440](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44722388440). It verified PDF upload, real Gemini analysis, cross-user denial and cleanup.
- Existing main mobile auth/session E2E passed in the pre-integration baseline.
- This new integrated branch still requires its own exact-head backend/frontend/Playwright CI and Preview before merge/deployment.
