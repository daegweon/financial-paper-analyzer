# PaperSignal — per-user analysis queue quota design

**Engineering 89%; live beta release gates 4/10.**

- Maximum 5 analysis jobs per user in rolling 24h; maximum 2 active jobs (`queued`/`processing`).
- Repeated enqueue for the same paper while active returns the existing job (idempotency).
- PostgreSQL advisory transaction lock serializes admission per user.
- `enqueue_analysis_job(uuid,uuid)` is SECURITY DEFINER with empty search_path, schema-qualified objects, and EXECUTE only for service_role; PUBLIC/anon/authenticated are revoked.
- Candidate API maps daily/active limit codes to actionable HTTP 429. Browser surfaces exact detail immediately and never retries POST.

## CI evidence

https://github.com/daegweon/financial-paper-analyzer/actions/runs/44526397733 — SUCCESS: 146 backend passed/1 live E2E skipped; PostgreSQL service-only RPC, idempotency, daily/active limits and RLS passed; frontend quota tests/build passed; 33 Playwright scenarios passed; strict live API GET probe passed.

## Production rollout is pending

The running Railway API is pinned to `ace3fbd5` and does not call this RPC. Production Supabase migration has NOT been applied. After explicit DB change approval: reconcile remote migration history → apply only `20261119100000_server_owned_analysis_quota.sql` while old API remains compatible → deploy RPC caller API → verify actual quotas → approved live two-user E2E → separately revoke browser write grants. Never blanket `supabase db push`.
