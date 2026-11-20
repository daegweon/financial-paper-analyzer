-- Tests for the new migration in a disposable Postgres service only.
-- Uses two synthetic identities; raises SQL exceptions on any regression.
DO $$
BEGIN
  IF has_table_privilege('authenticated','public.analyses','INSERT')
    OR has_table_privilege('authenticated','public.analysis_jobs','INSERT')
    OR has_column_privilege('authenticated','public.analysis_jobs','status','UPDATE')
    OR has_column_privilege('authenticated','public.papers','status','UPDATE')
    OR has_column_privilege('authenticated','public.papers','status','INSERT')
    OR has_column_privilege('authenticated','public.papers','page_count','INSERT')
    OR has_column_privilege('authenticated','public.papers','metadata','INSERT')
    OR has_column_privilege('authenticated','public.papers','created_at','INSERT')
  THEN RAISE EXCEPTION 'Client analysis/queue/status write privileges remain unexpectedly open';
  END IF;
  IF NOT (
    has_column_privilege('authenticated','public.papers','user_id','INSERT')
    AND has_column_privilege('authenticated','public.papers','title','INSERT')
    AND has_column_privilege('authenticated','public.papers','original_filename','INSERT')
    AND has_column_privilege('authenticated','public.papers','storage_path','INSERT')
    AND has_column_privilege('authenticated','public.papers','size_bytes','INSERT')
    AND has_table_privilege('authenticated','public.papers','SELECT')
    AND has_table_privilege('authenticated','public.analyses','SELECT')
    AND has_table_privilege('authenticated','public.analysis_jobs','SELECT')
  ) THEN RAISE EXCEPTION 'Legitimate client upload or read grants were removed';
  END IF;
  IF NOT (
    has_table_privilege('service_role','public.analyses','INSERT')
    AND has_table_privilege('service_role','public.analysis_jobs','INSERT')
    AND has_table_privilege('service_role','public.analysis_jobs','UPDATE')
    AND has_table_privilege('service_role','public.papers','UPDATE')
  ) THEN RAISE EXCEPTION 'Trusted API/Worker write grants were removed';
  END IF;
END $$;

-- Seed existing paper, analysis, job and storage metadata without customer data.
INSERT INTO public.papers(id,user_id,title,original_filename,storage_path,size_bytes,status)
VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
       '11111111-1111-4111-8111-111111111111',
       'Synthetic fixture', 'example.pdf',
       '11111111-1111-4111-8111-111111111111/example.pdf',125,'completed');
INSERT INTO public.analyses(paper_id,user_id,model,status)
VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
       '11111111-1111-4111-8111-111111111111','test-fixture','completed');
INSERT INTO public.analysis_jobs(paper_id,user_id,status,stage)
VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
       '11111111-1111-4111-8111-111111111111','completed','completed');
INSERT INTO storage.objects(bucket_id,name)
VALUES('papers','11111111-1111-4111-8111-111111111111/example.pdf');

BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
DO $$
DECLARE
  blocked boolean;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM public.papers WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR NOT EXISTS(SELECT 1 FROM public.analyses WHERE paper_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR NOT EXISTS(SELECT 1 FROM public.analysis_jobs WHERE paper_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR NOT EXISTS(SELECT 1 FROM storage.objects WHERE bucket_id='papers' AND name='11111111-1111-4111-8111-111111111111/example.pdf')
  THEN RAISE EXCEPTION 'Owner lost access to their paper, analysis, job or PDF';
  END IF;

  -- Upload metadata must still succeed with the EXACT frontend column set.
  INSERT INTO public.papers(user_id,title,original_filename,storage_path,size_bytes)
  VALUES('11111111-1111-4111-8111-111111111111',
         'Permitted upload','upload.pdf',
         '11111111-1111-4111-8111-111111111111/upload.pdf',256);
  IF NOT EXISTS(
    SELECT 1 FROM public.papers
    WHERE title='Permitted upload' AND status='uploaded' AND page_count IS NULL
  ) THEN RAISE EXCEPTION 'Paper metadata defaults are not preserved'; END IF;

  blocked:=false;
  BEGIN
    INSERT INTO public.analyses(paper_id,user_id,model,status)
    VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
           '11111111-1111-4111-8111-111111111111','forged','completed');
  EXCEPTION WHEN insufficient_privilege THEN blocked:=true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Client forged an analysis'; END IF;

  blocked:=false;
  BEGIN
    INSERT INTO public.analysis_jobs(paper_id,user_id)
    VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
           '11111111-1111-4111-8111-111111111111');
  EXCEPTION WHEN insufficient_privilege THEN blocked:=true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Client bypassed API to enqueue analysis'; END IF;

  blocked:=false;
  BEGIN
    UPDATE public.papers SET status='completed' WHERE title='Permitted upload';
  EXCEPTION WHEN insufficient_privilege THEN blocked:=true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Client edited trusted paper status'; END IF;

  blocked:=false;
  BEGIN
    INSERT INTO public.papers(user_id,title,original_filename,storage_path,size_bytes,status)
    VALUES('11111111-1111-4111-8111-111111111111',
           'Forged finished paper','bad.pdf',
           '11111111-1111-4111-8111-111111111111/bad.pdf',100,'completed');
  EXCEPTION WHEN insufficient_privilege THEN blocked:=true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Client created a pre-completed paper'; END IF;
END $$;
ROLLBACK;

BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM public.papers WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR EXISTS(SELECT 1 FROM public.analyses WHERE paper_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR EXISTS(SELECT 1 FROM public.analysis_jobs WHERE paper_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
    OR EXISTS(SELECT 1 FROM storage.objects WHERE bucket_id='papers' AND name='11111111-1111-4111-8111-111111111111/example.pdf')
  THEN RAISE EXCEPTION 'Owner B can see owner A private data'; END IF;
END $$;
ROLLBACK;

BEGIN;
SET LOCAL ROLE service_role;
DO $$
BEGIN
  INSERT INTO public.analysis_jobs(paper_id,user_id,status,stage)
  VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
         '11111111-1111-4111-8111-111111111111','queued','queued');
  INSERT INTO public.analyses(paper_id,user_id,model,status)
  VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
         '11111111-1111-4111-8111-111111111111','worker','completed');
  UPDATE public.papers SET page_count=2 WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
  IF NOT EXISTS(SELECT 1 FROM public.papers WHERE page_count=2 AND id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
  THEN RAISE EXCEPTION 'Worker cannot update verified page count'; END IF;
END $$;
ROLLBACK;
SELECT 'PASS: isolated RLS and service-owned analysis write checks' AS outcome;
