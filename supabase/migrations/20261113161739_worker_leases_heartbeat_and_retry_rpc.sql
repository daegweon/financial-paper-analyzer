create or replace function public.claim_analysis_job(p_worker_id text,p_lease_seconds integer default 1200)
returns setof public.analysis_jobs language plpgsql security definer set search_path=public as $$
declare claimed public.analysis_jobs;
begin
 with recoverable as (
  update public.analysis_jobs set status='queued',stage='queued',worker_id=null,lease_expires_at=null,
   available_at=greatest(available_at,now()),updated_at=now()
  where status in ('processing','failed') and worker_id is not null and lease_expires_at is not null
   and lease_expires_at<now() and attempts<max_attempts returning paper_id
 )
 update public.papers p set status='uploaded'
 where p.id in (select paper_id from recoverable) and p.status='processing';
 with terminal as (
  update public.analysis_jobs set status='failed',stage='failed',completed_at=coalesce(completed_at,now()),
   error_message=coalesce(error_message,'Worker lease expired and retry limit was reached.'),
   worker_id=null,lease_expires_at=null,updated_at=now()
  where status in ('processing','failed') and worker_id is not null and lease_expires_at is not null
   and lease_expires_at<now() and attempts>=max_attempts returning paper_id
 )
 update public.papers p set status='failed' where p.id in (select paper_id from terminal);
 select * into claimed from public.analysis_jobs
 where status='queued' and available_at<=now() and attempts<max_attempts
 order by created_at for update skip locked limit 1;
 if not found then return; end if;
 update public.analysis_jobs set status='processing',stage='claimed',attempts=attempts+1,
  worker_id=p_worker_id,lease_expires_at=now()+make_interval(secs=>greatest(60,least(p_lease_seconds,3600))),
  started_at=coalesce(started_at,now()),updated_at=now()
 where id=claimed.id returning * into claimed;
 return next claimed;
end; $$;

create or replace function public.renew_analysis_job_lease(p_job_id uuid,p_worker_id text,p_lease_seconds integer default 1200)
returns boolean language plpgsql security definer set search_path=public as $$
begin
 update public.analysis_jobs set lease_expires_at=now()+make_interval(secs=>greatest(60,least(p_lease_seconds,3600))),
  updated_at=now() where id=p_job_id and worker_id=p_worker_id and status='processing';
 return found;
end; $$;

create or replace function public.schedule_failed_analysis_job_retry(p_job_id uuid,p_worker_id text)
returns boolean language plpgsql security definer set search_path=public as $$
declare target_paper uuid;
begin
 update public.analysis_jobs set status='queued',stage='queued',
  available_at=now()+make_interval(secs=>least(300,(15*power(2,greatest(attempts-1,0)))::integer)),
  worker_id=null,lease_expires_at=null,updated_at=now()
 where id=p_job_id and worker_id=p_worker_id and status='failed' and attempts<max_attempts
 returning paper_id into target_paper;
 if not found then return false; end if;
 update public.papers set status='uploaded' where id=target_paper;
 return true;
end; $$;

revoke all on function public.claim_analysis_job(text,integer) from public,anon,authenticated;
revoke all on function public.renew_analysis_job_lease(uuid,text,integer) from public,anon,authenticated;
revoke all on function public.schedule_failed_analysis_job_retry(uuid,text) from public,anon,authenticated;
grant execute on function public.claim_analysis_job(text,integer) to service_role;
grant execute on function public.renew_analysis_job_lease(uuid,text,integer) to service_role;
grant execute on function public.schedule_failed_analysis_job_retry(uuid,text) to service_role;
