-- Beta integrity boundary (staged only; NOT yet applied to the live project).
-- Deploy and verify server-owned POST /api/analyze first, while the old
-- authenticated client write privileges still exist. Only then apply.
--
-- Signed-in browser users may upload paper metadata and read their own
-- analyses/jobs, but only the trusted API + Worker (service_role) can create
-- or update analysis jobs, results and paper analysis status.

-- Existing users could create fake "verified" analysis rows and enqueue
-- arbitrary jobs through PostgREST, bypassing the authenticated API flow.
revoke insert on table public.analyses from authenticated;
revoke insert on table public.analysis_jobs from authenticated;

-- These were column-level grants: revoking table-level UPDATE alone would
-- NOT remove them. Workers update these using service_role.
revoke update (status, stage, error_message, analysis_id, updated_at,
               started_at, completed_at)
  on table public.analysis_jobs from authenticated;
revoke update (status, page_count, error_message, updated_at)
  on table public.papers from authenticated;

-- Keep a client-side paper upload path, but disallow client claims of
-- completed/failed status, page count, audit timestamps or other metadata.
-- Original upload UI supplies exactly these allowed fields (content_type
-- is optional and defaults to 'application/pdf').
revoke insert on table public.papers from authenticated;
grant insert (user_id, title, original_filename, storage_path,
              content_type, size_bytes)
  on table public.papers to authenticated;

-- Eliminate stale client write policies so future accidental GRANTs do not
-- silently reopen these routes. SELECT policies stay enabled and unchanged.
drop policy if exists analyses_insert_own on public.analyses;
drop policy if exists analysis_jobs_insert_own on public.analysis_jobs;
drop policy if exists analysis_jobs_update_own on public.analysis_jobs;
drop policy if exists papers_update_own on public.papers;

-- No grants or owner-visible policies for SELECT are removed.
-- No service_role privilege changes; worker and API retain server writes.
