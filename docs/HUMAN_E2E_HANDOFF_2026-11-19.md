# PaperSignal — human-owned remaining actions (2026-11-20)

**Current engineering completion: 98%. Current independently passed release gates: 4/10.** The engineering percentage measures implemented work; it is not launch permission.

## Completed autonomously in this checkpoint

- Candidate frontend code SHA `0cdf4fed96df40521a99c5969e3d3703bebde8a8` passed GitHub Checks [#44683909825](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44683909825): API, frontend, disposable PostgreSQL 17 (including the AI usage-ledger migration contract), GET-only live API preflight and synthetic Chromium/WebKit browser QA. Live production E2E was skipped.
- Vercel Preview is READY: [open current Preview](https://financial-paper-analyzer-nwik7wcju-daegweonai-9583.vercel.app) (deployment `dpl_HTsQiR2ykz72x7q6xE7c5Ww3yTht`).
- All ten benchmark PDFs have article-level license statements checked; the license report is `benchmark/results/license-audit-2026-11-20.md`.
- The six `review` findings in the latest B01–B10 analyses received an assistant second-pass PDF audit. The report is `benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md`. The six database statuses remain `review`; this is not human expert sign-off.
- Production state was inspected read-only: Supabase has nine migration versions through `20261113234956` and no `ai_usage_events` / `ai_admin_settings` tables. Railway API remains on immutable commit `ace3fbd5`; Worker remains unchanged on commit `8cd5e37`.
- Corrected the runbook's protected-secret names, Railway Worker service/deployment IDs and rollback reference. No Production data, schema, deployment or account was changed.

## Actions requiring an authorized human

### 1. Review the narrow manual E2E launcher PR

Review [Draft PR #19](https://github.com/daegweon/financial-paper-analyzer/pull/19). It adds only a manual-only workflow and its runbook. If acceptable, mark it Ready for review and merge **PR #19 only** into `main`. Do **not** merge product Draft PR #18.

The workflow is pinned to the audited immutable test source `431059a1116a50f39fd56d565c35a1afc081b8fc`. It is not active on `main` until PR #19 is merged.

### 2. Configure the exact protected GitHub Actions secrets

In [GitHub Actions repository secrets](https://github.com/daegweon/financial-paper-analyzer/settings/secrets/actions), configure these exact four names. The workflow does not read `E2E_*` aliases:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PAPERSIGNAL_API_URL`

Never paste values into chat, PR comments, workflow inputs or logs.

### 3. Explicitly approve and dispatch the synthetic live E2E

After PR #19 is merged and the four secrets are configured, go to GitHub Actions → **PaperSignal Live E2E - Manual Approval** → Run workflow on `main`, then set:

- `target = papersignal-production`
- `approve_mutations = true`
- `approved_commit = 431059a1116a50f39fd56d565c35a1afc081b8fc`
- `acknowledgment = RUN_SYNTHETIC_LIVE_E2E`

This explicitly authorizes creation of two temporary synthetic Auth users, one private two-page synthetic PDF, one real Railway Worker/Gemini analysis job and scoped cleanup. It can consume Gemini quota. Do not dispatch unless that exact test mutation is approved. Share only the resulting run URL, never credentials.

### 4. Approve the staged Production API/database rollout

The current Production API is live on deployment `0b5716db-b720-49db-b15c-babf77b26e5a` / commit `ace3fbd5`. The candidate quota RPC, AI usage-ledger writer and admin endpoints are not live. The remote Supabase database has nine migration versions through `20261113234956`; neither `ai_usage_events` nor `ai_admin_settings` exists yet.

After migration-history reconciliation and separate change approval, follow the exact sequence in `docs/BETA_RELEASE_RUNBOOK_2026-11-20.md`:

1. Apply the additive server-owned analysis quota RPC migration.
2. Deploy the candidate API that calls the RPC and writes best-effort AI usage events.
3. Apply and verify the additive AI usage-ledger/admin-settings migration.
4. Run the real synthetic two-account Auth/Storage/PDF/analysis isolation test against the upgraded API.
5. Only after that passes, consider the client-write revocation migration.
6. Do not promote Vercel Production until the current Preview, real E2E and rollback gates pass.

The old deployment `17c9134b-f49c-4358-a879-7ca77b55b936` is REMOVED and cannot be used as rollback. The current live baseline `0b5716db-b720-49db-b15c-babf77b26e5a` is the current rollback reference; verify it is still available immediately before any change. The Worker service is `238af942-0628-47d5-9280-04a49373423f` and must remain untouched.

### 5. Set administrator-only AI controls when an administrator is designated

The administrator console is not an end-user budget feature. It exposes one service-wide monthly AI budget and administrator-only usage/cost reports; ordinary users do not get personal budgets or access to raw AI costs.

- Set Railway `PAPERSIGNAL_ADMIN_USER_IDS` only after verifying the intended Supabase Auth UUID.
- Optionally set `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD` after the administrator chooses a service-wide budget.
- Set `GEMINI_BILLING_MODE` to `free` or `paid_standard` only after checking the actual Google AI Studio billing configuration. It is currently absent, so cost remains unknown rather than fabricated as zero.

### 6. Resolve the remaining platform/security and review checks

- **SMTP:** configure an external SMTP provider and verify signup, confirmation and password reset with an external mailbox.
- **Native devices:** verify original PDF rendering, page navigation, signed-link renewal, rotation and session expiry on actual iOS Safari and Android Chrome devices.
- **Auth security:** Supabase's security advisor reports leaked-password protection disabled. An administrator should decide whether to enable it; it has not been changed because it affects signup policy.
- **Rollback:** rehearse the current API rollback procedure before Production migrations and document the compatible frontend/API recovery path after client-write revocation.
- **Research audit:** arrange a qualified human reviewer for the six current review-flagged findings. Prioritize B03's table/prose discrepancy and B05's difference-in-differences interpretation. The assistant second-pass report is preparation, not expert sign-off.

## Current operational snapshot (read-only)

- Railway API, last 24 hours: 446 requests, 0 server errors, 219 client errors, p99 latency 9 ms. This is a small observed sample, not a load test.
- Supabase performance advisor: no findings. Security advisor: one warning (leaked-password protection disabled).
- No Production migration, candidate API deployment, client-write revocation, live synthetic E2E, SMTP change, mobile-device test or Vercel Production promotion was performed in this checkpoint.

## Guardrails

- Keep PR #18 Draft until every required gate is independently evidenced.
- Do not apply migrations with a blind `supabase db push`; reconcile the remote history first.
- Never delete or overwrite historical user PDFs or analyses.
- Keep the finance analysis engine frozen; no v6.x heuristic changes were made.
- AI budget configuration remains administrator-owned and service-wide, never a per-user end-user setting.
