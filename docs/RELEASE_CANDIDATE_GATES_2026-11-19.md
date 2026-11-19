# PaperSignal — Consolidated beta release candidate gates (2026-11-19)

Release candidate: https://github.com/daegweon/financial-paper-analyzer/pull/18 (Draft, base main, head fa526369, 0 commits behind latest main at integration). Engine frozen; no Production mutation on this milestone.

## Verified automated / provider checks

| Gate | State | Evidence / qualification |
| --- | --- | --- |
| GitHub Actions real runner allocation | PASS | https://github.com/daegweon/financial-paper-analyzer/actions/runs/44368096096 |
| Candidate Python backend regression CI | PASS | https://github.com/daegweon/financial-paper-analyzer/actions/runs/44370323274 |
| Candidate frontend lint/test/Next.js production build | PASS | Same Checks run, frontend job |
| Real PostgreSQL 17 security migration test in isolation | PASS | Same Checks run, db-policy job: cross-owner RLS and Storage metadata, owner upload defaults, deny client-forged analyses/jobs/status, permit service-role results |
| Candidate Vercel Preview production build | READY | Feature-preview deployment, not Production or authenticated E2E |
| Core Railway API and Worker current deployment | Online | Production health overview, 0 failures in recent 24h; still old code, not candidate |
| Supabase advisors | No ERROR or CRITICAL | Health 0 findings, security one accepted Leaked Password Protection WARN (Free-tier limitation) |
| GitHub browser QA | 24/24 PASS | https://github.com/daegweon/financial-paper-analyzer/actions/runs/44403257361 — desktop Chromium, Android-emulated Chromium, iPhone-emulated WebKit; synthetic users only, not real auth |

## Mandatory pending live gates (not passed)

1. **Real authenticated Preview browser test:** actual Google and verified-email login to the protected candidate Preview; open a real existing public/synthetic PDF and cite pages; verify authorization errors, keyboard and original bytes. Owner can perform Google consent; the assistant has no authorized identity or mailbox session. Do not disable Vercel protection.
2. **Two-user live E2E:** opt-in `backend/tests/test_live_e2e.py` with disposable test accounts and synthetic uploaded PDF, completed API/Worker analysis, signed file and RLS denial for user B. Requires verified secrets in the private runner; no unattended run on PR changes. If job remains active, retain fixture for Worker safety.
3. **External email signup:** configure and verify custom SMTP and real inbox delivery before public signup. Supabase Free built-in SMTP is insufficient for arbitrary public email recipients. Do not disable email confirmation.
4. **Mobile native smoke:** iOS Safari actual device and Android Chrome original PDF embedded/new-tab fallback, page navigation, 200% zoom, keyboard/VoiceOver announcements; renewal after 50 min, account switch isolation.
5. **Backend/API rollout BEFORE DB grant revocation:** the current running Railway API still registers jobs using client JWT. Deploy candidate API with server-side key, verify owned job enqueue and unauthorized paper 404, check retries and Worker health before the migration. Do not deploy the Worker just to change API behavior.
6. **Security migration:** after step 5 succeeds, apply ONLY `supabase/migrations/20261117215315_beta_server_owned_result_writes.sql` using an explicitly reviewed migration mechanism. Existing Supabase migration history versions differ from baseline repo file names. Do not `supabase db push` indiscriminately. Run read-only postgrant assertions `supabase/tests/beta_write_grants.sql` and the advisors.
7. **Staged Production preview and rollback:** build a Production-environment release with `--skip-domain`; retest protected URL and core flows. Only after explicit approval promote that exact immutable Production deployment. Record eligible prior deployment ID and exercise rollback/forward promotion with no schema downgrade.
8. **Financial research quality handoff:** targeted human review of all remaining screen-required findings and their cited PDF pages, and public-beta AI quota/budget policy. A completed analysis is not a verified empirical finding.

## Rollback / nonnegotiable safety rules

- Existing Production Vercel main deployment when checked: `dpl_33BMEgCAGgZVW9XWDk2n2VvFgmZg` (READY, commit `f5d0345cf4d4f507c0c4a521bfea71adbc14541d`). Prior READY candidate `dpl_BSDxZJFMPXrpFNvaf6i38iGScANj`.
- Railway API old deployment `17c9134b-f49c-4358-a879-7ca77b55b936`; Worker old deployment `dc501061-d434-454a-bc7d-4658b991a2f1`.
- Once DB revokes client analysis writes, do NOT roll the API backward to a version that requires browser INSERT, as it will break queueing. Roll forward to the verified server-owned API or explicitly review any exceptional rollback.
- Do not raise GitHub Actions $1 budget automatically. Do not turn public/protection settings off to bypass a failed gate.
- No Production alias assignment, privileged live E2E, new paid Supabase project, destructive migration, or auth secret disclosure is authorized by build readiness alone.

## Decision

**Technical candidate assembled, not yet beta launch-ready.** Automated gates pass, real auth/Storage E2E and release-time server/database sequencing remain pending.

## Browser smoke as an automatic PR gate — 2026-11-19

The release candidate now runs **24 synthetic localhost-only Playwright scenarios** on three browser profiles in the dedicated `browser-qa` GitHub Actions job. All **24/24 PASS** on run https://github.com/daegweon/financial-paper-analyzer/actions/runs/44403257361 , covering junior progress, role quiz and source-page navigation. See `docs/BETA_BROWSER_CI_2026-11-19.md`. This does not satisfy live authentication, PDF Storage or device release gates.

## Progress baseline and safe real-account gate — 2026-11-19

- Engineering milestone completion **85%**, real beta release gates **4/10 passed**. Source: `docs/PROJECT_PROGRESS.json`; the figure is evidence-weighted estimation and is not approval to release.
- Manual production E2E requires GitHub `workflow_dispatch` on reviewed main, target `production`, `confirm_live_e2e=true` and acknowledgment `RUN_SYNTHETIC_LIVE_E2E`. Existing `backend/tests/test_live_e2e.py` additionally enforces exact Supabase/Railway URLs and `/health.queue_write_mode=service_role` before it creates any disposable users.
- **Still PENDING:** the running Railway API has not been verified as new server-owned job-writer code. Do not apply the client-write revocation migration before the updated API is actually deployed and verified. Authenticated private PDF, Google/email, SMTP and mobile release gates remain open.

## Verified API deployment preflight (2026-11-19)

- New `api-readonly-live` GitHub job confirms the **existing** Railway API is healthy and unauthorized GET job-status requests return 401. Actual result: `queue_writer=legacy_missing_marker`, analysis engine `finance-structured-v6.4.2`; do not treat it as deployed server-owned API.
- Isolated candidate Uvicorn smoke with synthetic env confirmed server-owned health signal and anonymous denial. Disposable PostgreSQL 17 verified server-role queue insertion **before** client grant revocation and enforced client-write denial **after**. Entire suite https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952 PASS (129 backend, 24/24 browsers, database, frontend, live read-only probe; 1 live E2E skipped).
- **Railway production is the only configured environment.** Core API and Worker source branches remain `feat/research-workspace-mvp`. Do not mutate Worker or simply merge PR #18 hoping API updates.
- Manual rollout steps and rollback constraints: `docs/RAILWAY_API_CUTOVER_2026-11-19.md`. Real authenticated two-user HTTPS E2E, new API deployment, DB migration, SMTP and mobile remain PENDING.

## API-only deployment verified (2026-11-19)

- **Engineering 86%; beta launch gates 4/10 PASSED**. Actual Railway API deployment `0b5716db-b720-49db-b15c-babf77b26e5a` (pinned immutable `ace3fbd5`) is SUCCESS. Worker unchanged `dc501061-d434-454a-bc7d-4658b991a2f1`.
- GitHub `api-readonly-live` now strictly requires `queue_write_mode=service_role`; public `/health` returned this marker and anonymous GET job-status denied with HTTP 401. Verification: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44462359704 .
- API 5xx sample was 0/10 in one-hour window; do not generalize beyond that sample. Release candidate PR #18 remains Draft; Railway API is pinned to `ace3fbd5` not latest PR docs commit.
- **Not yet passed:** user A actual upload/analysis, user B denial over Supabase HTTP and signed Storage, and client write permission revocation. The live Supabase authenticated grants remain open; do not apply `20261117215315_beta_server_owned_result_writes.sql` before approved E2E.

## Original PDF signed-source and cleanup readiness (2026-11-19)

- Engineering **87%** / release gates **4/10 passed**. Source of truth: `docs/PROJECT_PROGRESS.json`.
- Actual HTTP Storage test will now require owner original bytes + owner signed URL and signed bytes, non-owner cannot GET or request a signed link. Cleanup uses documented Storage **DELETE** endpoint for test-created PDF, not POST. Unit tests use `httpx.MockTransport` with no external data.
- All automatic checks passed: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44467502056 (133 backend tests pass, 1 real E2E skipped, 24/24 synthetic-browser tests, database policy and frontend).
- Read-only actual Supabase inspection found 0 temporary E2E Auth users / papers / Storage files / active jobs. **Real live E2E remains pending** and its manual run still requires approval and scoped keys.

## Separate human-approved live E2E launcher, not yet executed (2026-11-19)

- **Engineering 88% / live beta gates 4/10 PASS**. Manual workflow staged in separate Draft PR #19 https://github.com/daegweon/financial-paper-analyzer/pull/19 against `main` — not yet merged/active. It pins actual tested E2E source `431059a1116a50f39fd56d565c35a1afc081b8fc` from PR #18, requires exact multi-factor manual workflow inputs, and limits secrets to privileged E2E steps.
- New cleanup contract fixes partial-failure recovery, scopes deletions by QA user and paper, rejects unexpected PDF paths and never deletes active Worker fixtures. Verified CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44472720847 (143 Python passes/1 opt-in skip and 24/24 Playwright); launcher CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44473470809 (57 Python passes).
- Human must explicitly review/merge ONLY PR #19, configure protected Actions secrets and approve/manual-run E2E; production user-data tests remain pending. **Do NOT mark live_auth_pdf passed until the real two-account HTTP run passes and cleanup is verified.** Only after that may the reviewed SQL write-grant revocation proceed.
