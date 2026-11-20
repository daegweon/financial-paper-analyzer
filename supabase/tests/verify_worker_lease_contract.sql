-- Disposable PostgreSQL contract for worker lease ownership, recovery and retry.
-- Runs only in GitHub Actions' throwaway PostgreSQL container.

DO $$
BEGIN
  IF has_function_privilege('anon','public.claim_analysis_job(text,integer)','EXECUTE')
    OR has_function_privilege('authenticated','public.claim_analysis_job(text,integer)','EXECUTE')
    OR has_function_privilege('anon','public.renew_analysis_job_lease(uuid,text,integer)','EXECUTE')
    OR has_function_privilege('authenticated','public.renew_analysis_job_lease(uuid,text,integer)','EXECUTE')
    OR has_function_privilege('anon','public.schedule_failed_analysis_job_retry(uuid,text)','EXECUTE')
    OR has_function_privilege('authenticated','public.schedule_failed_analysis_job_retry(uuid,text)','EXECUTE')
  THEN
    RAISE EXCEPTION 'Browser roles can execute worker lease RPCs';
  END IF;
  IF NOT (
    has_function_privilege('service_role','public.claim_analysis_job(text,integer)','EXECUTE')
    AND has_function_privilege('service_role','public.renew_analysis_job_lease(uuid,text,integer)','EXECUTE')
    AND has_function_privilege('service_role','public.schedule_failed_analysis_job_retry(uuid,text)','EXECUTE')
  ) THEN
    RAISE EXCEPTION 'service_role cannot execute worker lease RPCs';
  END IF;
END $$;

BEGIN;
INSERT INTO public.papers(id,user_id,title,original_filename,storage_path,size_bytes,status)
VALUES
 ('31111111-1111-4111-8111-111111111111','11111111-1111-4111-8111-111111111111',
  'Lease recovery fixture','lease.pdf','11111111-1111-4111-8111-111111111111/lease.pdf',128,'uploaded'),
 ('31111111-1111-4111-8111-111111111112','11111111-1111-4111-8111-111111111111',
  'Lease terminal fixture','terminal.pdf','11111111-1111-4111-8111-111111111111/terminal.pdf',128,'processing');

INSERT INTO public.analysis_jobs(id,paper_id,user_id,status,stage,attempts,max_attempts)
VALUES
 ('41111111-1111-4111-8111-111111111111','31111111-1111-4111-8111-111111111111',
  '11111111-1111-4111-8111-111111111111','queued','queued',0,3),
 ('41111111-1111-4111-8111-111111111112','31111111-1111-4111-8111-111111111112',
  '11111111-1111-4111-8111-111111111111','processing','gemini_analysis',3,3);

UPDATE public.analysis_jobs
SET worker_id='worker-terminal',lease_expires_at=now()-interval '1 second'
WHERE id='41111111-1111-4111-8111-111111111112';

SET LOCAL ROLE service_role;
DO $$
DECLARE
  claimed public.analysis_jobs%ROWTYPE;
  retried boolean;
  still_queued public.analysis_jobs%ROWTYPE;
  terminal public.analysis_jobs%ROWTYPE;
  returned_count integer;
BEGIN
  -- First claim assigns one lease and increments attempts exactly once.
  SELECT * INTO claimed
  FROM public.claim_analysis_job('worker-a',300);
  IF NOT FOUND
    OR claimed.id <> '41111111-1111-4111-8111-111111111111'
    OR claimed.status <> 'processing'
    OR claimed.attempts <> 1
    OR claimed.worker_id <> 'worker-a'
    OR claimed.lease_expires_at <= now()+interval '4 minutes'
    OR claimed.lease_expires_at > now()+interval '5 minutes'
  THEN
    RAISE EXCEPTION 'Initial worker claim did not assign the expected bounded lease';
  END IF;

  -- A different worker cannot renew the current owner's lease.
  IF public.renew_analysis_job_lease(claimed.id,'worker-not-owner',300) THEN
    RAISE EXCEPTION 'Non-owner renewed a worker lease';
  END IF;
  IF NOT public.renew_analysis_job_lease(claimed.id,'worker-a',300) THEN
    RAISE EXCEPTION 'Current owner could not renew its lease';
  END IF;

  -- Expiry recovery requeues the abandoned attempt and transfers ownership.
  UPDATE public.analysis_jobs
  SET lease_expires_at=now()-interval '1 second'
  WHERE id=claimed.id;
  SELECT * INTO claimed
  FROM public.claim_analysis_job('worker-b',300);
  IF NOT FOUND
    OR claimed.id <> '41111111-1111-4111-8111-111111111111'
    OR claimed.status <> 'processing'
    OR claimed.attempts <> 2
    OR claimed.worker_id <> 'worker-b'
  THEN
    RAISE EXCEPTION 'Expired lease was not recovered by the next worker';
  END IF;
  IF public.renew_analysis_job_lease(claimed.id,'worker-a',300) THEN
    RAISE EXCEPTION 'Previous worker renewed a lease after ownership transfer';
  END IF;
  IF NOT public.renew_analysis_job_lease(claimed.id,'worker-b',300) THEN
    RAISE EXCEPTION 'New lease owner could not renew its lease';
  END IF;

  -- Only the current worker may schedule a failed attempt for bounded retry.
  UPDATE public.analysis_jobs
  SET status='failed',stage='failed',error_message='synthetic retry fixture'
  WHERE id=claimed.id;
  IF public.schedule_failed_analysis_job_retry(claimed.id,'worker-a') THEN
    RAISE EXCEPTION 'Non-owner scheduled a failed job retry';
  END IF;
  retried := public.schedule_failed_analysis_job_retry(claimed.id,'worker-b');
  IF NOT retried THEN
    RAISE EXCEPTION 'Current worker could not schedule an eligible retry';
  END IF;
  SELECT * INTO still_queued FROM public.analysis_jobs WHERE id=claimed.id;
  IF still_queued.status <> 'queued'
    OR still_queued.stage <> 'queued'
    OR still_queued.worker_id IS NOT NULL
    OR still_queued.lease_expires_at IS NOT NULL
    OR still_queued.available_at <= now()
    OR still_queued.attempts <> 2
  THEN
    RAISE EXCEPTION 'Retry did not clear ownership and apply backoff';
  END IF;

  -- A job that has exhausted attempts becomes terminal and cannot be reclaimed.
  SELECT * INTO terminal
  FROM public.claim_analysis_job('worker-c',300);
  IF FOUND THEN
    RAISE EXCEPTION 'Claim unexpectedly returned a job after max-attempt expiry';
  END IF;
  SELECT * INTO terminal
  FROM public.analysis_jobs
  WHERE id='41111111-1111-4111-8111-111111111112';
  IF terminal.status <> 'failed'
    OR terminal.stage <> 'failed'
    OR terminal.worker_id IS NOT NULL
    OR terminal.lease_expires_at IS NOT NULL
    OR terminal.completed_at IS NULL
  THEN
    RAISE EXCEPTION 'Exhausted job was not closed as terminal';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.papers
    WHERE id='31111111-1111-4111-8111-111111111112' AND status='failed'
  ) THEN
    RAISE EXCEPTION 'Paper status was not synchronized after terminal lease expiry';
  END IF;
END $$;
ROLLBACK;

SELECT 'PASS: worker claim, owner-only heartbeat, lease recovery, retry backoff and terminal expiry' AS outcome;
