create policy "service_role_manages_analysis_job_checkpoints"
on public.analysis_job_checkpoints
for all
to service_role
using (true)
with check (true);
