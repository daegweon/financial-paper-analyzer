alter table public.analyses
  add column if not exists job_id uuid references public.analysis_jobs(id) on delete set null;

create unique index if not exists analyses_job_id_unique_idx
  on public.analyses(job_id);

create index if not exists analyses_paper_user_idx
  on public.analyses(paper_id,user_id,created_at desc);

create table if not exists public.analysis_job_checkpoints (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.analysis_jobs(id) on delete cascade,
  stage text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(job_id,stage)
);

alter table public.analysis_job_checkpoints enable row level security;
revoke all on public.analysis_job_checkpoints from public,anon,authenticated;
grant select,insert,update,delete on public.analysis_job_checkpoints to service_role;
create index if not exists analysis_job_checkpoints_job_updated_idx
  on public.analysis_job_checkpoints(job_id,updated_at desc);
