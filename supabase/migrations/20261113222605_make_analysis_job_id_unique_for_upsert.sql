create unique index if not exists analysis_jobs_one_active_per_paper_idx
on public.analysis_jobs(paper_id)
where status in ('queued','processing');
