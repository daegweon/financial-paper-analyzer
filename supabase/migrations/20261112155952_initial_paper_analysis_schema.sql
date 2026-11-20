
create extension if not exists pgcrypto;
create table if not exists public.papers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (length(title) between 1 and 500),
  original_filename text not null,
  storage_path text not null unique,
  content_type text not null default 'application/pdf',
  size_bytes bigint not null check (size_bytes > 0 and size_bytes <= 31457280),
  page_count integer check (page_count is null or page_count >= 0),
  status text not null default 'uploaded' check (status in ('uploaded','processing','completed','failed')),
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, user_id)
);
create index if not exists papers_owner_created_idx on public.papers (user_id, created_at desc);
create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  paper_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'completed' check (status in ('completed','failed')),
  model text not null,
  result jsonb not null default '{}'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  foreign key (paper_id, user_id) references public.papers (id, user_id) on delete cascade
);
create index if not exists analyses_paper_created_idx on public.analyses (paper_id, created_at desc);
create index if not exists analyses_owner_created_idx on public.analyses (user_id, created_at desc);
alter table public.papers enable row level security;
alter table public.analyses enable row level security;
revoke all on public.papers, public.analyses from anon;
revoke all on public.papers, public.analyses from authenticated;
grant select, insert on public.papers to authenticated;
grant select on public.analyses to authenticated;
grant select, insert, update, delete on public.papers, public.analyses to service_role;
create policy papers_select_own on public.papers for select to authenticated
  using ((select auth.uid()) = user_id);
create policy papers_insert_own on public.papers for insert to authenticated
  with check ((select auth.uid()) = user_id AND storage_path like (user_id::text || '/%'));
create policy analyses_select_own on public.analyses for select to authenticated
  using ((select auth.uid()) = user_id);
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('papers', 'papers', false, 31457280, array['application/pdf'])
on conflict (id) do update set public = false, file_size_limit = 31457280,
  allowed_mime_types = array['application/pdf'];
create policy papers_storage_owner_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'papers' AND (storage.foldername(name))[1] = (select auth.uid())::text);
create policy papers_storage_owner_select on storage.objects for select to authenticated
  using (bucket_id = 'papers' AND (storage.foldername(name))[1] = (select auth.uid())::text);
create policy papers_storage_owner_delete on storage.objects for delete to authenticated
  using (bucket_id = 'papers' AND (storage.foldername(name))[1] = (select auth.uid())::text);
