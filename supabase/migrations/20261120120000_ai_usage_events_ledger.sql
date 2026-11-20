-- Immutable, privacy-minimized provider-attempt usage ledger.
-- Apply only after human review; CI applies this to disposable PostgreSQL 17.
CREATE TABLE IF NOT EXISTS public.ai_usage_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  paper_id uuid REFERENCES public.papers(id) ON DELETE SET NULL,
  analysis_job_id uuid REFERENCES public.analysis_jobs(id) ON DELETE SET NULL,
  provider text NOT NULL CHECK (length(provider) BETWEEN 1 AND 64),
  model text NOT NULL CHECK (length(model) BETWEEN 1 AND 128),
  attempt_index integer NOT NULL CHECK (attempt_index > 0),
  outcome text NOT NULL CHECK (outcome IN ('success','http_error','transport_error','invalid_response')),
  billing_mode text CHECK (billing_mode IS NULL OR billing_mode IN ('free','paid_standard')),
  http_status integer CHECK (http_status BETWEEN 100 AND 599),
  error_class text CHECK (error_class IS NULL OR length(error_class) <= 128),
  prompt_tokens bigint CHECK (prompt_tokens IS NULL OR prompt_tokens >= 0),
  candidate_tokens bigint CHECK (candidate_tokens IS NULL OR candidate_tokens >= 0),
  thought_tokens bigint CHECK (thought_tokens IS NULL OR thought_tokens >= 0),
  total_tokens bigint CHECK (total_tokens IS NULL OR total_tokens >= 0),
  latency_ms integer CHECK (latency_ms IS NULL OR latency_ms >= 0),
  idempotency_key text NOT NULL UNIQUE CHECK (length(idempotency_key) BETWEEN 16 AND 256),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (outcome = 'success' AND http_status BETWEEN 200 AND 299)
    OR outcome <> 'success'
    OR http_status IS NULL
  )
);
CREATE INDEX IF NOT EXISTS ai_usage_events_user_created_idx
  ON public.ai_usage_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ai_usage_events_job_idx
  ON public.ai_usage_events(analysis_job_id);
CREATE INDEX IF NOT EXISTS ai_usage_events_provider_model_created_idx
  ON public.ai_usage_events(provider, model, created_at DESC);
CREATE INDEX IF NOT EXISTS ai_usage_events_created_at_idx
  ON public.ai_usage_events(created_at DESC);

ALTER TABLE public.ai_usage_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_usage_events FORCE ROW LEVEL SECURITY;
REVOKE ALL ON public.ai_usage_events FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.ai_usage_events TO service_role;

-- Administrator-only service-wide monthly AI budget setting.
CREATE TABLE IF NOT EXISTS public.ai_admin_settings (
  setting_key text PRIMARY KEY CHECK (setting_key = 'monthly_budget_usd'),
  value_numeric numeric(18,8) NOT NULL CHECK (value_numeric >= 0),
  updated_by uuid NOT NULL REFERENCES auth.users(id),
  updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.ai_admin_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_admin_settings FORCE ROW LEVEL SECURITY;
REVOKE ALL ON public.ai_admin_settings FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.ai_admin_settings TO service_role;
