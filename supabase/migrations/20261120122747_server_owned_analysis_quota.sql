-- Atomic per-user Gemini/analysis queue limits.
-- Additive: the current API may keep direct service_role inserts until upgraded.
CREATE OR REPLACE FUNCTION public.enqueue_analysis_job(p_paper_id uuid,p_user_id uuid)
RETURNS TABLE(id uuid,status text,stage text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE v_job public.analysis_jobs%ROWTYPE; v_daily_count integer; v_active_count integer;
BEGIN
  IF p_paper_id IS NULL OR p_user_id IS NULL THEN
    RAISE EXCEPTION USING ERRCODE='P0002', MESSAGE='PAPERSIGNAL_PAPER_NOT_FOUND';
  END IF;
  PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_user_id::text,0));
  PERFORM 1 FROM public.papers WHERE public.papers.id=p_paper_id AND public.papers.user_id=p_user_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE='P0002', MESSAGE='PAPERSIGNAL_PAPER_NOT_FOUND';
  END IF;
  SELECT * INTO v_job FROM public.analysis_jobs
  WHERE public.analysis_jobs.paper_id=p_paper_id
    AND public.analysis_jobs.user_id=p_user_id
    AND public.analysis_jobs.status IN ('queued','processing')
  ORDER BY public.analysis_jobs.created_at DESC LIMIT 1;
  IF FOUND THEN
    RETURN QUERY SELECT v_job.id,v_job.status,v_job.stage;
    RETURN;
  END IF;
  SELECT pg_catalog.count(*)::integer INTO v_daily_count FROM public.analysis_jobs
  WHERE public.analysis_jobs.user_id=p_user_id
    AND public.analysis_jobs.created_at >= pg_catalog.now()-interval '24 hours';
  IF v_daily_count >= 5 THEN
    RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='PAPERSIGNAL_DAILY_LIMIT';
  END IF;
  SELECT pg_catalog.count(*)::integer INTO v_active_count FROM public.analysis_jobs
  WHERE public.analysis_jobs.user_id=p_user_id
    AND public.analysis_jobs.status IN ('queued','processing');
  IF v_active_count >= 2 THEN
    RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='PAPERSIGNAL_ACTIVE_LIMIT';
  END IF;
  INSERT INTO public.analysis_jobs(paper_id,user_id,status,stage)
  VALUES(p_paper_id,p_user_id,'queued','queued') RETURNING * INTO v_job;
  RETURN QUERY SELECT v_job.id,v_job.status,v_job.stage;
END;
$$;
REVOKE ALL ON FUNCTION public.enqueue_analysis_job(uuid,uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.enqueue_analysis_job(uuid,uuid) TO service_role;
