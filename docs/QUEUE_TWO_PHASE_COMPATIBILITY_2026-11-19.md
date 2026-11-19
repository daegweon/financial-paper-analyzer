# PaperSignal — two-phase analysis queue migration compatibility (2026-11-19)

## Production rollout order (not executed by this CI test)

**Phase 1:** Deploy new API with server-owned job creation while old Supabase authenticated client INSERT permissions remain temporarily unchanged. The Worker remains on its existing code/deployment.

**Phase 2:** Verify the new API's `queue_write_mode=service_role` via the strict GET-only probe; then run a separately authorized disposable-account E2E. Only after successful results, apply the single reviewed client-grant revocation migration, with remote migration history reconciliation.

## What the disposable PostgreSQL CI now proves

- First, run real baseline migrations, **without** the new grant revocation. Insert one synthetic owner's paper and perform `analysis_jobs` INSERT as service_role, then ROLLBACK all inserted data. Existing authenticated role grants still exist during this phase.
- Second, run `20261117215315_beta_server_owned_result_writes.sql` and the existing post-migration RLS/integrity suite: browser users retain own reads and upload metadata INSERT, cannot forge analysis result/job state; service-role writes remain permitted.
- All SQL executes only inside disposable postgres:17 GitHub Actions, with no Supabase credentials or customer documents.

Actual Railway server deployment, real API authentication, Gemini usage, remote migration history and live Supabase grant changes remain **PENDING**. CI success is proof of schema compatibility, not a substitute for live two-user verification.

## Confirmed GitHub run 2026-11-19

- https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952 — all automatic jobs PASS. Actual live API queue marker is `legacy_missing_marker`; candidate local ASGI marker is `service_role`; pre/post revocation disposable PostgreSQL compatibility checks both PASS. Live authenticated E2E remains SKIPPED; no Production modification.
