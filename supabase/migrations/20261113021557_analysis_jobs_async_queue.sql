create table if not exists public.analysis_jobs (
 id uuid primary key default gen_random_uuid(),
 paper_id uuid not null,
 user_id uuid not null references auth.users(id) on delete cascade,
 status text not null default 'queued' check (status in ('queued','processing','completed','failed')),
 stage text not null default 'queued',
 error_message text,
 analysis_id uuid references public.analyses(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 started_at timestamptz,
 completed_at timestamptz,
 foreign key (paper_id,user_id) references public.papers(id,user_id) on delete cascade
);
create index if not exists analysis_jobs_owner_created_idx on public.analysis_jobs(user_id,created_at desc);
create index if not exists analysis_jobs_paper_created_idx on public.analysis_jobs(paper_id,created_at desc);
create index if not exists analysis_jobs_active_idx on public.analysis_jobs(status,created_at) where status in ('queued','processing');
alter table public.analysis_jobs enable row level security;
revoke all on public.analysis_jobs from anon,authenticated;
grant select,insert on public.analysis_jobs to authenticated;
grant update(status,stage,error_message,analysis_id,updated_at,started_at,completed_at) on public.analysis_jobs to authenticated;
create policy analysis_jobs_select_own on public.analysis_jobs for select to authenticated using ((select auth.uid())=user_id);
create policy analysis_jobs_insert_own on public.analysis_jobs for insert to authenticated with check ((select auth.uid())=user_id and exists (select 1 from public.papers p where p.id=paper_id and p.user_id=(select auth.uid())));
create policy analysis_jobs_update_own on public.analysis_jobs for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
