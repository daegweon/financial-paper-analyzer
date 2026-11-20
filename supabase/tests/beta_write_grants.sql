-- Read-only post-migration acceptance assertions. Returns booleans, no user rows.
-- All fields should be TRUE after the beta_server_owned_result_writes migration.
select
  not has_table_privilege('authenticated','public.analyses','INSERT') as user_cannot_forge_analyses,
  not has_table_privilege('authenticated','public.analysis_jobs','INSERT') as user_cannot_enqueue_directly,
  not has_column_privilege('authenticated','public.analysis_jobs','status','UPDATE') as user_cannot_edit_job_status,
  not has_column_privilege('authenticated','public.papers','status','UPDATE') as user_cannot_edit_paper_status,
  not has_column_privilege('authenticated','public.papers','status','INSERT') as user_cannot_insert_completed_paper,
  not has_column_privilege('authenticated','public.papers','page_count','INSERT') as user_cannot_forge_page_count,
  has_column_privilege('authenticated','public.papers','title','INSERT') as user_can_upload_paper_metadata,
  has_column_privilege('authenticated','public.papers','storage_path','INSERT') as user_can_upload_storage_path,
  has_table_privilege('authenticated','public.papers','SELECT') as user_can_read_own_papers_via_rls,
  has_table_privilege('authenticated','public.analyses','SELECT') as user_can_read_own_analyses_via_rls,
  has_table_privilege('authenticated','public.analysis_jobs','SELECT') as user_can_read_own_job_status_via_rls,
  has_table_privilege('service_role','public.analysis_jobs','INSERT') as server_can_enqueue_jobs,
  has_table_privilege('service_role','public.analyses','INSERT') as worker_can_save_results;
