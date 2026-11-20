-- Disposable PostgreSQL 17 contract for the AI usage ledger.
DO $$
BEGIN
  IF has_table_privilege('anon','public.ai_usage_events','SELECT')
     OR has_table_privilege('anon','public.ai_usage_events','INSERT')
     OR has_table_privilege('authenticated','public.ai_usage_events','SELECT')
     OR has_table_privilege('authenticated','public.ai_usage_events','INSERT')
  THEN RAISE EXCEPTION 'Browser roles must not access raw AI usage events'; END IF;
  IF NOT has_table_privilege('service_role','public.ai_usage_events','INSERT')
  THEN RAISE EXCEPTION 'service_role cannot insert AI usage events'; END IF;
END $$;

BEGIN;
SET LOCAL ROLE service_role;
INSERT INTO public.ai_usage_events(
  user_id, provider, model, attempt_index, outcome,
  prompt_tokens, candidate_tokens, thought_tokens, total_tokens,
  latency_ms, idempotency_key
) VALUES (
  '11111111-1111-4111-8111-111111111111',
  'gemini','gemini-test',1,'success',100,20,NULL,120,450,
  'job-123-gemini-gemini-test-1'
);
DO $$
DECLARE event_count integer;
BEGIN
  SELECT count(*) INTO event_count FROM public.ai_usage_events
   WHERE idempotency_key='job-123-gemini-gemini-test-1';
  IF event_count <> 1 THEN RAISE EXCEPTION 'Usage event insert failed'; END IF;
  BEGIN
    INSERT INTO public.ai_usage_events(
      user_id, provider, model, attempt_index, outcome, idempotency_key
    ) VALUES (
      '11111111-1111-4111-8111-111111111111',
      'gemini','gemini-test',1,'success','job-123-gemini-gemini-test-1'
    );
    RAISE EXCEPTION 'Duplicate idempotency key was accepted';
  EXCEPTION WHEN unique_violation THEN
    NULL;
  END;
END $$;
ROLLBACK;

BEGIN;
SET LOCAL ROLE service_role;
INSERT INTO public.ai_usage_events(
  user_id, provider, model, attempt_index, outcome,
  idempotency_key
) VALUES (
  '11111111-1111-4111-8111-111111111111',
  'gemini','gemini-test',1,'transport_error',
  'job-456-gemini-gemini-test-1'
);
DO $$
BEGIN
  IF (SELECT prompt_tokens FROM public.ai_usage_events
      WHERE idempotency_key='job-456-gemini-gemini-test-1') IS NOT NULL
  THEN RAISE EXCEPTION 'Missing token usage must remain NULL'; END IF;
END $$;
ROLLBACK;
SELECT 'PASS: service-role-only usage ledger, idempotency uniqueness, nullable usage' AS outcome;
