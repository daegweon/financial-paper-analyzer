
grant update (status, page_count, error_message, updated_at) on public.papers to authenticated;
grant insert on public.analyses to authenticated;
create policy papers_update_own on public.papers for update to authenticated
 using ((select auth.uid()) = user_id)
 with check ((select auth.uid()) = user_id AND storage_path like (user_id::text || '/%'));
create policy analyses_insert_own on public.analyses for insert to authenticated
 with check ((select auth.uid()) = user_id);
