-- Tighten Supabase's default service_role grants for administrator accounting tables.
-- The AI usage ledger is append-only; only trusted server reads/inserts are required.
REVOKE ALL PRIVILEGES ON TABLE public.ai_usage_events
  FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT ON TABLE public.ai_usage_events TO service_role;

-- The global budget is maintained by an upsert in the trusted API.
-- Delete/truncate/trigger/reference privileges are not required.
REVOKE ALL PRIVILEGES ON TABLE public.ai_admin_settings
  FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.ai_admin_settings TO service_role;
