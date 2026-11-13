create index if not exists analysis_jobs_analysis_id_idx
  on public.analysis_jobs(analysis_id) where analysis_id is not null;
create index if not exists analysis_jobs_paper_user_idx
  on public.analysis_jobs(paper_id,user_id);
