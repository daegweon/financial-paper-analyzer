# PaperSignal — read-only live API release probe (2026-11-19)

## Why this gate exists

The current Railway API and Worker run from the historical `feat/research-workspace-mvp` source branch and Railway currently has **only the production environment**. They do NOT automatically consume the candidate in Draft PR #18. Never mistake Vercel Preview readiness for Railway backend rollout.

## Probe contract

- New GitHub PR job `api-readonly-live` performs only two HTTPS **GET** requests against an **exact, hardcoded** PaperSignal Railway API hostname.
- GET `/health` must return HTTP 200, `status=ok`, `service=papersignal-api` and a non-empty `analysis_version` string.
- GET `/api/analyze/00000000-0000-4000-8000-000000000001/status?job_id=00000000-0000-4000-8000-000000000002` without authentication must return HTTP **401**. This endpoint is strictly read-only, not analysis submission.
- Any redirect to a different URL or unexpected health schema is refused. No bearer token, service-role key, user account, PDF, queue write or database mutation. Live response bodies are never printed.
- `queue_write_mode=legacy_missing_marker`: old API still serves health requests. **Not equivalent to the reviewed API being deployed.** CI still passes because the old release is expected to remain until production rollout.
- `queue_write_mode=service_role`: the new API code reports configured server-owned job submission. **This is still not proof of an authorized job insert or E2E result.**
- `queue_write_mode=unavailable` or any other unexpected marker fails. Failure indicates rollout not ready, but never triggers automated production changes.

## Commands and release sequence

From the repository root, no credentials required:

```sh
python backend/scripts/read_only_release_probe.py
```

After a separately reviewed deployment of new Railway API code **without changing database grants**, a release operator can explicitly require the new marker:

```sh
python backend/scripts/read_only_release_probe.py --require-server-owned
```

If the strict check fails, **do not apply** `supabase/migrations/20261117215315_beta_server_owned_result_writes.sql`. Verify API release source SHA and required secret variable names and do a reviewed rollback if necessary. Even if strict check passes, execute authorized two-user real HTTP E2E before restricting client grants.

The current PR-only check does NOT deploy, reconfigure the Railway source branch, create a paid staging environment, or mutate production. Railway source configuration must be explicitly reviewed before rollout.
