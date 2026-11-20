# PaperSignal beta release runbook — 2026-11-20

## Current verified baseline

- Candidate: `release/beta-candidate-20261119`, PR #18.
- Engineering completion: 98%; this is not release authorization.
- Independently passed release gates: 4/10.
- Production API: Railway service `81b678e2-7136-436d-9058-7d20647dc1b7`, currently deployed immutable commit `ace3fbd5dab3ea71efa3a49da8363259ea5f9732`, deployment `0b5716db-b720-49db-b15c-babf77b26e5a`.
- Known rollback target before database migration: `17c9134b-f49c-4358-a879-7ca77b55b936`.
- Existing Railway worker `dc501061-d434-454a-bc7d-4658b991a2f1` must remain untouched.
- Candidate CI: API 195 passed / 1 intentionally skipped; frontend lint/typecheck/build passed; disposable PostgreSQL 17 policy/index checks passed; GET-only live API preflight passed; 39 synthetic browser scenarios passed. Live E2E is deliberately skipped.
- Production migration history was previously observed to contain only nine versions through `20261113234956`; re-query the remote migration history immediately before any approved migration. Never assume local migration files have already been applied.

## Approval and secrets

Do not execute any Production migration, live E2E, Railway deployment, Vercel Production promotion, or client-write revocation until an authorized human explicitly approves the specific action and target.

Required protected Actions secrets for the manual E2E launcher (PR #19):
- `E2E_SUPABASE_URL`
- `E2E_SUPABASE_SERVICE_ROLE_KEY`
- `E2E_PAPERSIGNAL_API_URL`
- `E2E_PAPERSIGNAL_API_TOKEN`

Use only dedicated synthetic test accounts and synthetic PDFs. Do not use real customer accounts, private PDFs, or user-owned data.

Railway API variables to prepare for the administrator console:
- `PAPERSIGNAL_ADMIN_USER_IDS`: comma-separated, verified Supabase Auth UUID allowlist; keep empty until an administrator is explicitly designated.
- `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD`: optional initial service-wide USD budget. A persisted `ai_admin_settings` value takes precedence.
- `GEMINI_BILLING_MODE`: set to `free` or `paid_standard` only after verifying the actual Google AI Studio project billing tier; otherwise leave `unknown`.
- `SUPABASE_SERVICE_ROLE_KEY`: server-only; never add to `NEXT_PUBLIC_*` variables.

## Staged deployment sequence

### 0. Preflight and backup
1. Confirm PR #18 source SHA, CI success and Vercel Preview READY.
2. Record current Railway API and Worker deployment IDs, environment variable names (not values), Supabase migration history and table row counts.
3. Verify rollback deployment is still available.
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

Until all required gates are independently evidenced, keep PR #18 as a draft beta candidate and do not promote Vercel Production.
