drop index if exists public.analyses_job_id_unique_idx;
create unique index analyses_job_id_unique_idx on public.analyses(job_id);
