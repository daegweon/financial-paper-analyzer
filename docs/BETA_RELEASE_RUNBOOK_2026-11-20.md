# PaperSignal beta release runbook — 2026-11-20

## Current verified baseline

- Candidate: `release/beta-candidate-20261119`, Draft PR #18; current candidate frontend code SHA `0cdf4fed96df40521a99c5969e3d3703bebde8a8`.
- Engineering completion: 98%; current independently passed release gates: **4/10**. This is not release authorization.
- Exact-head GitHub Checks [#44683909825](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44683909825) passed API, frontend lint/typecheck/build, disposable PostgreSQL 17 policy/index checks (including the AI usage-ledger migration contract), GET-only live API preflight and synthetic Chromium/WebKit browser QA. The live production E2E job was deliberately skipped.
- Vercel Preview is **READY** for the current candidate frontend code: deployment `dpl_HTsQiR2ykz72x7q6xE7c5Ww3yTht`, [open Preview](https://financial-paper-analyzer-nwik7wcju-daegweonai-9583.vercel.app). Alias: https://financial-paper-analyzer-git-release-bet-9ad043-daegweonai-9583.vercel.app. Subsequent repository changes are documentation-only and do not alter this frontend code.
- Production API: Railway service `81b678e2-7136-436d-9058-7d20647dc1b7`, live deployment `0b5716db-b720-49db-b15c-babf77b26e5a`, immutable commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732`, status SUCCESS. It does not yet run the current quota/ledger candidate code.
- Current rollback baseline: live deployment `0b5716db-b720-49db-b15c-babf77b26e5a` (SUCCESS; rollback-capable). The previously listed `17c9134b-f49c-4358-a879-7ca77b55b936` is REMOVED and cannot be used as a rollback target.
- Existing Railway worker service `238af942-0628-47d5-9280-04a49373423f` remains untouched on deployment `dc501061-d434-454a-bc7d-4658b991a2f1`, commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, status SUCCESS.
- Read-only Production check (2026-11-20): Railway API had 446 requests, 0 server errors, 219 client errors and p99 latency 9 ms over the last 24 hours (not a load test). Supabase has 9 migration versions through `20261113234956`; `ai_usage_events` and `ai_admin_settings` are absent. No Production migration was applied.
- Railway API currently has no `PAPERSIGNAL_ADMIN_USER_IDS`, `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD` or `GEMINI_BILLING_MODE` variable. The admin console remains locked until an administrator UUID is explicitly configured; billing mode remains unknown.
- Supabase security advisor reports leaked-password protection disabled; no performance advisor findings. This Auth setting has not been changed because it affects signup policy and requires an administrator decision.

## Approval and secrets

The separate manual E2E launcher in PR #19 is pinned to audited source `431059a1116a50f39fd56d565c35a1afc081b8fc`. Its four secrets are the exact names below. It is not active on `main` until PR #19 is reviewed and merged.

Do not execute any Production migration, live E2E, Railway deployment, Vercel Production promotion, or client-write revocation until an authorized human explicitly approves the specific action and target.

Required protected Actions secrets for the manual E2E launcher (PR #19):
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PAPERSIGNAL_API_URL`

These are the exact names referenced by `.github/workflows/papersignal-live-e2e.yml` in PR #19. Do not create similarly named `E2E_*` secrets; the workflow will not read them.

Use only dedicated synthetic test accounts and synthetic PDFs. Do not use real customer accounts, private PDFs, or user-owned data.

Railway API variables to prepare for the administrator console:
- `PAPERSIGNAL_ADMIN_USER_IDS`: comma-separated, verified Supabase Auth UUID allowlist; keep empty until an administrator is explicitly designated.
- `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD`: optional initial service-wide USD budget. A persisted `ai_admin_settings` value takes precedence.
- `GEMINI_BILLING_MODE`: set to `free` or `paid_standard` only after verifying the actual Google AI Studio project billing tier; otherwise leave `unknown`.
- `SUPABASE_SERVICE_ROLE_KEY`: server-only; never add to `NEXT_PUBLIC_*` variables.

## Staged deployment sequence

### 0. Preflight and backup
1. Confirm PR #18 source SHA and exact-head CI success. The current frontend code SHA has a READY Preview at the URL in the baseline above; re-check the deployment if any frontend code changes.
2. Record current Railway API and Worker service/deployment IDs, environment variable names (not values), Supabase migration history and table row counts.
3. Verify the live API baseline deployment `0b5716db-b720-49db-b15c-babf77b26e5a` is still rollback-capable. Do not use the removed deployment `17c9134b-f49c-4358-a879-7ca77b55b936`.
4. Confirm the approved administrator UUID and monthly budget owner.
5. Obtain explicit approval for each Production mutation below.

### 1. Server-owned analysis quota RPC
1. Reconcile the remote Supabase migration history; do not use `db push` blindly.
2. Review `20261119100000_server_owned_analysis_quota.sql` and its PostgreSQL verification script.
3. Apply the additive quota RPC migration only after approval.
4. Deploy the API revision that calls the RPC.
5. Verify authenticated quota behavior, duplicate-job idempotency, daily/active limits, anonymous 401 and health marker. Do not revoke browser write grants yet.

### 2. AI usage ledger and administrator settings
1. Deploy the API revision containing best-effort AI usage event writes and the server-authorized admin endpoints. If the ledger table is not present yet, telemetry writes are deliberately non-fatal; expect a short observability gap.
2. After approval, apply `20261120120000_ai_usage_events_ledger.sql`.
3. Run the reviewed SQL verification script: browser roles cannot read/write `ai_usage_events` or `ai_admin_settings`; service_role can write events and manage the single global budget; idempotency uniqueness and timestamp index exist.
4. Set the verified administrator UUID allowlist and optional initial budget in Railway. Do not expose any service-role or admin configuration through frontend variables.
5. Verify a successful analysis writes one or more provider-attempt rows with token/latency metadata. Confirm unknown billing mode remains NULL and does not become a fabricated zero-cost event.
6. Verify an ordinary authenticated user receives 403 from both admin endpoints and sees no AI cost/budget data. Verify the designated admin can read model costs, pricing provenance, token/latency metrics and update the service-wide monthly budget.
7. Confirm a truncated monthly query never reports within-budget.

### 3. Real synthetic two-account E2E
1. Use the manual E2E workflow only after explicit approval and after confirming it is pinned to the reviewed source commit.
2. Test Account A and Account B separately: sign in, upload synthetic PDF, analyze, read original PDF and cited page, refresh signed URL, resume jobs and log out.
3. Verify Account A cannot list/read/update Account B's paper, analysis, PDF object, job or usage events; repeat in reverse.
4. Verify admin-only usage endpoints are inaccessible to both non-admin accounts.
5. Verify cleanup is scoped only to the synthetic test users and fixture paths; preserve all real historical PDFs and analyses.
6. Save sanitized CI evidence only. Never print access tokens, service-role keys, signed URLs or private user data.

### 4. Client-write revocation
Only after the new API is deployed and the real two-account E2E above passes:
1. Review and apply `20261117215315_beta_server_owned_result_writes.sql`.
2. Re-run the same ownership, queue quota, idempotency and result-write contract tests.
3. Verify the current frontend uses server-owned writes and no longer depends on revoked browser write grants.
4. Do not revoke grants early as a shortcut.

### 5. SMTP, native mobile and rollback rehearsal
- Configure external SMTP for public email signup and verify signup, email confirmation, password reset and redirect URLs.
- On actual iOS Safari and Android Chrome devices, test PDF rendering, page navigation, signed URL refresh, viewport rotation, download/open fallback and session expiry.
- Rehearse rollback to the recorded API deployment before any DB mutation. Additive tables/RPCs can remain unused after an API rollback; do not drop tables or delete user data.
- If client-write revocation has been applied, do not simply roll back to an old frontend that still expects browser writes. Restore a compatible server-owned frontend/API or obtain separate approval for a narrowly scoped grant rollback.

## Go / no-go checklist

- [ ] Human approval recorded for the exact migration/deployment target.
- [ ] Remote migration history reconciled.
- [ ] Candidate API deployed and health/auth probes pass.
- [ ] Quota RPC and AI ledger migrations verified.
- [ ] Admin UUID allowlist and global budget confirmed.
- [ ] Non-admin 403 and admin access verified.
- [ ] Real synthetic two-account Auth/Storage/PDF E2E passes.
- [ ] Client-write revocation only after the E2E pass.
- [ ] SMTP and native mobile checks pass.
- [ ] Rollback target and operator steps confirmed.

Before public signup, have an administrator decide whether to enable Supabase Auth leaked-password protection; the current security advisor reports it disabled. Also confirm the actual Google AI Studio billing mode before setting `GEMINI_BILLING_MODE`; unknown billing must remain unknown, not zero-cost.

Until all required gates are independently evidenced, keep PR #18 as a draft beta candidate and do not promote Vercel Production.
