-- PRE-migration transitional smoke, run ONLY in GitHub disposable PostgreSQL.
-- Verifies the NEW API can queue using service_role while OLD client grants
-- still exist; proves migration sequencing can preserve service availability.
DO $$
BEGIN
  IF NOT has_table_privilege('service_role','public.analysis_jobs','INSERT')
    OR NOT has_table_privilege('authenticated','public.analysis_jobs','INSERT')
    OR NOT has_table_privilege('authenticated','public.papers','INSERT')
    OR NOT has_table_privilege('authenticated','public.papers','SELECT')
  THEN
    RAISE EXCEPTION 'Pre-migration permissions differ from the reviewed rollout baseline';
  END IF;
END $$;

BEGIN;
INSERT INTO public.papers(
  id,user_id,title,original_filename,storage_path,size_bytes
) VALUES (
  'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  '11111111-1111-4111-8111-111111111111',
  'Synthetic pre-revoke source',
  'pre-revoke.pdf',
  '11111111-1111-4111-8111-111111111111/pre-revoke.pdf',
  100
);

SET LOCAL ROLE service_role;
INSERT INTO public.analysis_jobs(paper_id,user_id,status,stage)
VALUES (
  'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  '11111111-1111-4111-8111-111111111111',
  'queued','queued'
);
DO $$
BEGIN
  IF NOT EXISTS(
    SELECT 1 FROM public.analysis_jobs
    WHERE paper_id='cccccccc-cccc-4ccc-8ccc-cccccccccccc'
      AND user_id='11111111-1111-4111-8111-111111111111'
      AND status='queued'
  ) THEN RAISE EXCEPTION 'Trusted server could not queue during pre-migration overlap'; END IF;
END $$;
ROLLBACK;

SELECT 'PASS: server-owned enqueue works before client-grant revocation' AS outcome;
