# Standalone manually approved PaperSignal Live E2E launcher

**Not active until this standalone PR is reviewed and merged into `main`.** No customer account, PDF or database records are modified by the PR itself.

## Why this separate workflow exists

The full product candidate is still Draft PR #18 and must **not** be merged before live E2E and integrity migration. GitHub workflow_dispatch registration requires the workflow on the default branch. This tiny workflow allows only the audited test commit below to run from main, without merging the entire unfinished product.

## Audited immutable test source

- Exact pinned code SHA: `431059a1116a50f39fd56d565c35a1afc081b8fc` (Draft PR #18 code snapshot: corrected Storage DELETE, owner/nonowner signed-source tests, independently fail-safe cleanup).
- The job checks out **this SHA**, not the HEAD of a mutable PR branch, and verifies git rev-parse HEAD before installing dependencies.
- The run input **must equal this SHA**. Changes to E2E code require a separately reviewed update to the pin. Do not let the job run arbitrary user-supplied commits with privileged secrets.

## Human steps (NOT performed automatically)

1. Review and merge this narrow workflow-only PR into main. If kept Draft, choose **Ready for review** before merge. Do NOT merge Draft PR #18.
2. In the GitHub repo, configure protected **Actions repository secrets** `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `PAPERSIGNAL_API_URL`. Use the exact existing project/service, never paste any secret into chat, PR comments, workflow inputs or logs.
3. Go to GitHub Actions → `PaperSignal Live E2E - Manual Approval` → Run workflow on `main`. Select target `papersignal-production`, check the approval checkbox, type approved commit SHA shown above, and type exact phrase `RUN_SYNTHETIC_LIVE_E2E`. The default inputs do nothing.
4. Understand this will create two confirmed **temporary synthetic** Auth users and a private synthetic two-page PDF, initiate one real Railway Worker/Gemini analysis, verify cross-user isolation, and then delete the test-created items after a terminal job. It can consume free-tier Gemini quota. If the Worker is still busy, its temporary fixture is intentionally retained to avoid corrupting an active job.
5. Inspect the completed run and verify the temporary test resources are absent using read-only Supabase queries before approving the separate client-grants migration. If cleanup fails, do not delete arbitrary customer records; use an exact QA fixture cleanup runbook.

## Hard guardrails

- The workflow exists on main only when this narrow PR is merged; it never runs on push or pull_request.
- The job requires **all four** approval conditions: manual dispatch from `main`, correct target, explicit boolean approval, and exact code SHA plus acknowledgment phrase.
- Minimal GitHub token permission `contents: read`; no environment secrets during dependency installation; only the read-only preflight and actual E2E step receive the four protected secrets.
- Test target and server-owned `/health` writer mode are checked before creating users. No secrets or signed PDF bearer URL are printed.
- Production Supabase schema/migration is **not** changed by this workflow. Do not apply `20261117215315_beta_server_owned_result_writes.sql` until the full real E2E passes, and remote migration history has been reconciled.
- This workflow does not make Vercel Production live, alter Railway service source, deploy the Worker, or raise GitHub Actions budget.

## Status

Pending human-controlled merge, repository secret configuration and explicit manual run. Release milestone remains pending until a genuine run succeeds.
