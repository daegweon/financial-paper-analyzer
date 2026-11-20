# Production Supabase migration baseline — 2026-11-20

The repository migration directory is reconciled to the exact remote migration ledger read from `supabase_migrations.schema_migrations` on 2026-11-20. For each entry, the SQL statements stored by Supabase were copied into a file named `<version>_<name>.sql`.

| Version | Name |
|---|---|
| 20261112155952 | initial_paper_analysis_schema |
| 20261112160036 | authenticated_analysis_writes |
| 20261113021557 | analysis_jobs_async_queue |
| 20261113161739 | worker_leases_heartbeat_and_retry_rpc |
| 20261113222551 | analysis_stage_checkpoints_and_idempotent_results |
| 20261113222605 | make_analysis_job_id_unique_for_upsert |
| 20261113222644 | index_analysis_job_foreign_keys |
| 20261113222754 | explicit_service_role_checkpoint_policy |
| 20261113234956 | cleanup_terminal_analysis_job_checkpoints |
| 20261120102957 | beta_server_owned_result_writes |
| 20261120122747 | server_owned_analysis_quota |
| 20261120122819 | ai_usage_events_ledger |
| 20261120122859 | index_ai_usage_ledger_foreign_keys |

## Reconciliation

The previous local files `20261113000000_initial_schema.sql` and `20261113010000_analysis_jobs.sql` did not match the version/name pairs in the remote ledger. They were replaced by the exact remote history files, avoiding a future blind `supabase db push` attempting to replay already-applied schema changes under different versions.

## Safety

- This document and the migration files are a record of already-applied migrations; do not reapply them manually.
- Future migrations must use a new version greater than `20261120122859` and must be tested against disposable PostgreSQL before Production.
- Never run `supabase db push` until the remote migration list and checked-in migration directory have been compared.
- The current API rollback deployment remains `0b5716db-b720-49db-b15c-babf77b26e5a`; schema rollback is not assumed to be safe or automatic.
