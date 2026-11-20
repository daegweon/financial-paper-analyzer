create or replace function public.cleanup_terminal_analysis_job_checkpoints()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if old.status is distinct from new.status
     and (
       new.status = 'completed'
       or (new.status = 'failed' and new.attempts >= new.max_attempts)
     )
  then
    delete from public.analysis_job_checkpoints
    where job_id = new.id;
  end if;
  return new;
end;
$$;

revoke all on function public.cleanup_terminal_analysis_job_checkpoints() from public, anon, authenticated;

drop trigger if exists analysis_job_checkpoint_retention on public.analysis_jobs;
create trigger analysis_job_checkpoint_retention
after update of status on public.analysis_jobs
for each row
execute function public.cleanup_terminal_analysis_job_checkpoints();
