# PaperSignal — API-only Railway cutover plan (2026-11-19)

**Status: REVIEWED AS A PROCEDURE, NOT EXECUTED.** Canonical progress source `docs/PROJECT_PROGRESS.json`: 85% engineering; beta launch gates 4/10 passed.

## Confirmed current infrastructure

| Resource | Identifier / status |
| --- | --- |
| Railway project | `c663389c-453c-4645-a83d-299b94089864` |
| Railway production environment (only environment) | `0b4f06c3-504a-4610-8995-395c2f4d3d1f` |
| Core API service | `81b678e2-7136-436d-9058-7d20647dc1b7` |
| Core Worker service | `238af942-0628-47d5-9280-04a49373423f` |
| Both services GitHub source branch | `feat/research-workspace-mvp` |
| Current API deployment rollback reference | `17c9134b-f49c-4358-a879-7ca77b55b936` (SUCCESS) |
| Current Worker (leave untouched) | `dc501061-d434-454a-bc7d-4658b991a2f1` (SUCCESS) |
| New candidate | Draft PR #18, `release/beta-candidate-20261119` |
| Supabase project | `hwmtayrecsfxernhssro` |

## Preflight already passing (no mutations)

- Real public API GET `/health`: HTTP 200; `analysis_version=finance-structured-v6.4.2`; `queue_write_mode` absent, classified as `legacy_missing_marker`.
- GET job-status without authentication: HTTP 401. This is a read-only endpoint, never a queued analysis request.
- Candidate API launched under Uvicorn with a synthetic `sb_secret_*` key: health shows `queue_write_mode=service_role`, anon GET job-status HTTP 401. No production key or external request.
- Disposable PostgreSQL 17: server-role can enqueue jobs with OLD grants still enabled, then restricted client write permissions and owner SELECT/metadata INSERT continue to behave after the reviewed migration.
- Immutable CI evidence: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952. The opt-in live Supabase/Auth/Storage E2E remained skipped.

## Deployment procedure — requires separate production change approval

1. Recheck **exact PR #18 reviewed commit**, GitHub Checks and current Railway service IDs/source branch/config, status, variable **names** and latest API/Worker deployment IDs; verify no pending staged changes.
2. Prepare the candidate source exclusively for the **API** service. Do NOT modify Worker source or service settings. Railway production is the only existing environment; creating a staging environment or additional service may add costs, so do not do it silently.
3. Deploy the reviewed server-owned queue API **before altering Supabase grants**. Verify its new deployment is SUCCESS/Online, `/health` service/version is expected and no error spikes. Existing browser user grants must remain during this overlap.
4. Run strict GET-only check: `python backend/scripts/read_only_release_probe.py --require-server-owned`. It must PASS with `queue_writer=service_role` and anonymous job-status 401. This is necessary but NOT sufficient for successful queue insertion.
5. After explicit approval, run disposable two-user HTTPS E2E from a trusted secured runner using **candidate** test code and protected secrets. Note: GitHub `workflow_dispatch` safe controls are currently on Draft candidate, not default `main`; **do not assume they can be triggered from an unmerged PR**. Obtain a reviewed secure dispatch/bootstrap method or use a manually authorized trusted runtime without exposing credentials. Confirm real API/Worker analysis and Storage tenant isolation. This action can create 2 synthetic Auth users/PDF and consume Gemini quota.
6. Only after API and live E2E PASS, reconcile the different remote migration history. Apply only `supabase/migrations/20261117215315_beta_server_owned_result_writes.sql` in a reviewed change window; never blanket `supabase db push`. Run `supabase/tests/beta_write_grants.sql`, security advisors and the live two-user E2E again.
7. Verify no unexpected user-visible errors or Worker retry spikes, then proceed separately with external SMTP signup, real mobile Safari PDF, Vercel staged Production preview and controlled rollback.

## Rollback boundaries

- **Before DB grant migration:** if new API deployment fails, restore the known-good API deployment/source. The Worker, Supabase data and grants remain untouched.
- **After DB grant migration:** DO NOT roll back to an old API that enqueues via browser JWT, because it will fail against revoked grants. Roll forward to a verified server-owned API. Re-opening browser result/job writes restores an integrity and potential Gemini-cost risk; it is a last-resort separately reviewed incident response, never automatic.
- Keep user documents and completed analyses intact. Do not increase GitHub Actions $1 budget, expose service-role credentials, or promote Draft PR #18 to production as a side effect of this runbook.

## Next handoff

Gate `api_migration` is PENDING. The current operational blocker is intentional: live API still uses the old release source. When operator production-change approval exists, perform API-only rollout and real E2E in that order. Report 85% engineering / 4 of 10 beta gates until independently verified results justify changing them.
