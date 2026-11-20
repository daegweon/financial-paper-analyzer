-- Add the paper foreign-key lookup index for the immutable AI usage ledger.
-- This version matches the already-applied Production migration history.
CREATE INDEX IF NOT EXISTS ai_usage_events_paper_id_idx
  ON public.ai_usage_events(paper_id)
  WHERE paper_id IS NOT NULL;
