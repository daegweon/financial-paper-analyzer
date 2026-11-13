-- Export the latest completed analysis for each benchmark paper.
-- Upload PDFs with titles beginning B01_ ... B10_ so they can be joined to the manifest.
select
  left(p.title, 3) as paper_id,
  p.id as paper_uuid,
  p.title,
  p.status as paper_status,
  p.page_count,
  latest.model,
  latest.created_at as analysis_created_at,
  latest.result as analysis
from public.papers p
join lateral (
  select a.model, a.created_at, a.result
  from public.analyses a
  where a.paper_id = p.id
    and a.user_id = p.user_id
    and a.status = 'completed'
  order by a.created_at desc
  limit 1
) latest on true
where p.title ~ '^B(0[1-9]|10)[_-]'
order by left(p.title, 3);
