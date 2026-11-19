# PaperSignal — deployment-readiness verification boundary (2026-11-19)

Two separate, immutable-source smoke checks prevent confusion between the READY frontend Preview and the old Railway API deployment.

## Local candidate API runtime

The `api` GitHub Actions job starts the **candidate** Uvicorn/ASGI app using an explicitly synthetic service-role key and unreachable localhost Supabase. It checks `/health` advertises `queue_write_mode=service_role` without exposing any key, and that unauthenticated GET job-status returns exactly HTTP 401. It never submits a job or calls a real AI provider.

Run with `python backend/scripts/smoke_candidate_http.py` after installing `backend/requirements-dev.txt`.

## Existing live API (GET only)

The `api-readonly-live` GitHub Actions job makes exactly two GET requests to the fixed public API host: health, and unauthenticated job status. It accepts `legacy_missing_marker` while the previous API is intentionally still deployed, but will *not* mistake this for new API rollout.

The first actual GitHub-hosted read-only probe on PR #18 commit `ab60a276` confirmed: `/health` OK, `analysis_version=finance-structured-v6.4.2`, unauthorized status HTTP 401, **queue_writer=legacy_missing_marker** (new server-owned queue API NOT yet live). Logs: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458065277 .

Before applying the staged Supabase database grant revocation, after reviewed API deployment, run:

```sh
python backend/scripts/read_only_release_probe.py --require-server-owned
```

A green local candidate ASGI smoke does NOT equal a deployed, authorized real job insert. A deployed `queue_write_mode=service_role` marker does NOT equal verified Storage RLS or successful real PDF analysis. Follow with a separately approved two-account HTTPS E2E before applying the DB migration. Do not change Railway source branch, deploy to Production, or modify client grants automatically.
