CREATE INDEX IF NOT EXISTS ai_usage_events_paper_id_idx
  ON public.ai_usage_events(paper_id) WHERE paper_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ai_admin_settings_updated_by_idx
  ON public.ai_admin_settings(updated_by);