# Isolated PostgreSQL 17 beta grants test (2026-11-19)

This regression suite runs in a disposable GitHub Actions PostgreSQL 17 service container only. It **never** receives database credentials, Supabase secrets, customer papers, or a production project URL.

It bootstraps the minimum Auth/Storage schema needed to execute the repository's real historical baseline migrations, simulates Supabase platform grants for `service_role`, applies the staged beta security migration, and checks:
- authenticated owners retain upload metadata INSERT with default status/page count;
- authenticated clients cannot forge results, enqueue jobs, or change paper status;
- two synthetic owners remain separated by real PostgreSQL RLS and Storage object metadata rules;
- the trusted service role retains analysis/job writes and paper state updates.

The test uses two static dummy UUIDs and synthetic paths. It does not validate the live Supabase Auth HTTP API or Storage signed URL issuance; those remain gated separately.

Workflow: `db-policy` job in `.github/workflows/checks.yml`. A failure must block PR readiness, and the job is not connected to any production database.