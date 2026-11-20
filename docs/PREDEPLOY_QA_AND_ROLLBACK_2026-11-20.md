# PaperSignal — pre-deployment QA and rollback checklist

**Prepared:** 2026-11-20 (Asia/Seoul)  
**Current main SHA:** `b04583370b09fd6972140b8f82c8dc13b685d9ba`  
**Current production alias:** `financial-paper-analyzer.vercel.app`  
**Current production deployment / rollback baseline:** `dpl_5y2EUXPkUDBeYomp2nxuok728Maa`  
**Latest auth-fix Preview before the final session-bootstrap fix:** `dpl_8tcLEBHHS46yqaimn5MEtQjbge34` (READY, Preview only; not the final merged main build)

## 1. Mobile authentication regression

- [ ] At 320×640, 375×667 and 390×844, Google sign-in is visible in the first viewport.
- [ ] Google button initiates Supabase OAuth with provider `google`, `prompt=select_account` and same-origin callback.
- [ ] After OAuth callback, the authenticated workspace loads.
- [ ] Mobile workspace header exposes a 44px-minimum logout target.
- [ ] Successful logout clears the Supabase session and returns to login.
- [ ] Reload after logout stays logged out.
- [ ] A delayed initial `getUser()` response cannot restore stale authenticated UI after `SIGNED_OUT`.

Automated coverage: `frontend/tests/e2e/auth-and-workspace.spec.ts`.

## 2. OAuth redirect and session recovery

- [ ] OAuth redirect URI matches the exact production origin.
- [ ] Google provider configuration and authorized redirect URL include `https://financial-paper-analyzer.vercel.app/`.
- [ ] Session persists after reload while signed in.
- [ ] Session does not persist after explicit logout.
- [ ] OAuth callback returns to the same origin without localhost or preview-host leakage.

The browser tests mock Supabase endpoints; the real Google consent and callback remain part of the authorized live E2E/manual smoke test.

## 3. PDF upload and analysis failure recovery

- [ ] Invalid extension/signature is rejected before Storage upload.
- [ ] A Storage 5xx is shown to the user and the upload control is re-enabled.
- [ ] Successful upload writes the private Storage object before the owner-scoped paper row.
- [ ] If the paper row insert fails after Storage upload, the uploaded object is removed as compensation.
- [ ] Analysis API 5xx is surfaced and the analyze action becomes retryable.
- [ ] Successful analysis job reaches a terminal state and its result is reloaded.
- [ ] Original PDF remains private and opens through a short-lived authenticated/signed URL.

Automated coverage: upload failure/retry readiness and analysis API failure/retry readiness are mocked in Playwright; real provider analysis is reserved for the synthetic live E2E.

## 4. User-data isolation and database/storage policy

Read-only Production inspection on 2026-11-20 found:

- RLS enabled on `papers`, `analyses`, `analysis_jobs`, and `analysis_job_checkpoints`.
- Owner-scoped SELECT/INSERT/UPDATE policies on papers, analyses and jobs.
- Private `papers` Storage bucket, PDF-only, 30 MiB maximum.
- Storage object INSERT/SELECT/DELETE policies bind the first path segment to `auth.uid()`.
- No performance-advisor findings. Security advisor warning: leaked-password protection disabled.

Automated repository contract tests assert the checked-in migration ownership and private-bucket policies. They do not replace a live two-account test.

- [ ] With two disposable Auth users A and B, verify A cannot list/download B's PDF.
- [ ] Verify A cannot read B's paper, analysis or job rows through the Data API.
- [ ] Verify A cannot insert/update a row under B's `user_id` or upload under B's Storage prefix.
- [ ] Verify B's own upload/analysis still works.
- [ ] Delete only the two disposable users and their uniquely prefixed synthetic files after the test.

The live two-account test creates users, a private synthetic PDF and an actual worker/provider job. It requires the approved protected GitHub Actions secrets and explicit operator approval; do not run it against real customer data.

## 5. Production deploy and rollback

### Before deploying

- [ ] Confirm the free Vercel deployment API quota is available. Do not upgrade the plan or incur charges.
- [ ] Confirm `main` still points to `119546fdcb3b116335b80ed9c734beff0a241e81` or a later reviewed commit.
- [ ] Confirm GitHub Checks pass for the exact SHA, including Playwright.
- [ ] Confirm the production API and Supabase schema are compatible; this frontend-only release does not apply DB migrations.
- [ ] Confirm the previous production deployment `dpl_5y2EUXPkUDBeYomp2nxuok728Maa` is still READY and rollback-capable.
- [ ] Do not promote a stale Preview. Deploy the exact reviewed `main` SHA to target `production`.

### After deployment

- [ ] Deployment state is `READY`.
- [ ] Alias `financial-paper-analyzer.vercel.app` points to the new deployment ID.
- [ ] Open the canonical alias in a private/incognito browser.
- [ ] Test Google login, workspace load, mobile logout, reload-after-logout.
- [ ] Test one disposable PDF upload and a provider analysis only after explicit live-test approval.
- [ ] Verify API health and check Railway/Supabase errors for the smoke-test window.

### Rollback

If auth, page loading, PDF upload or API compatibility regresses:

1. Stop further testing and do not change the database.
2. Re-check that `dpl_5y2EUXPkUDBeYomp2nxuok728Maa` is still the immediately previous production deployment and remains rollback-capable.
3. Roll back the production alias to that deployment.
4. Verify `financial-paper-analyzer.vercel.app` resolves to the rollback deployment.
5. Preserve logs and the failed deployment ID; fix on a new branch and repeat CI before retrying.

No production migrations, account creation, user-data mutation or service-plan changes are authorized by this checklist.


## Latest pre-deploy verification — 2026-11-20 17:50 KST

- Merged pre-deploy QA and auth-session fix to main: `b04583370b09fd6972140b8f82c8dc13b685d9ba`.
- Exact-main GitHub Checks [#44705352686](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44705352686) passed: backend pytest, frontend TypeScript lint, Next.js production build and Playwright Chromium **5/5**.
- Playwright coverage: Google button visible at 320×640, 375×667 and 390×844; Google OAuth provider/redirect/prompt; mobile logout and signed-out reload; invalid PDF rejection and Storage 503 recovery; analysis API 503 retry readiness.
- Auth bootstrap now uses Supabase `getSession()` for local UI hydration, subscribed before reading the persisted session. Server-side API/JWT validation and database RLS remain the authorization boundary. This avoids an in-flight `getUser()` request racing with logout.
- Read-only Production database check: RLS enabled on papers, analyses, analysis_jobs and analysis_job_checkpoints; private PDF bucket limited to 30 MiB and application/pdf; owner-scoped Storage path policies confirmed. Supabase performance advisor: no findings. Security advisor: leaked-password protection disabled (administrator decision remains).
- Read-only Railway API metrics (24h): 451 requests, 241 2xx, 210 4xx, 0 5xx; p99 latency 4–9 ms across observed buckets. This is an operational sample, not a load test.
- Production alias remains on prior deployment `dpl_5y2EUXPkUDBeYomp2nxuok728Maa`, which is still the rollback baseline. The current main commit has not been deployed because Vercel returned `api-deployments-free-per-day` / build-rate-limit. No plan upgrade or payment was made.
- The free deployment retry remains scheduled for 2026-11-21 15:40 Asia/Seoul. On retry, deploy exact current main SHA to target production, verify the alias points to the new READY deployment, then run the manual smoke checklist above.


---

## Final closeout — 2026-11-20 (supersedes the earlier pre-deploy checklist)

- Production Vercel alias `financial-paper-analyzer.vercel.app` is attached to READY deployment `dpl_HBMsBWFBE4xY7yCNi9KQUE79KCJV`, deployed from main SHA `d6cc166a1ad0f0a396aa12d70ca81068198f3d03`.
- Current main is `cec2d1a7ebdce8186a76e94b86181147eac1986c`. Comparing deployed SHA to current main shows only workflow/test/documentation changes after the deployed SHA; no application-runtime files changed. The deployed runtime therefore matches current main's app code.
- Deployed frontend source contains the Google sign-in button, mobile logout action and race-safe Supabase `getSession()` bootstrap.
- Live two-account E2E passed: [#44722388440](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44722388440). Preflight passed; the actual Worker/Gemini analysis completed; user B was denied access to A's paper, job, analysis and private PDF.
- A separate read-only Production query confirmed zero remaining synthetic Auth users, paper rows, PDF Storage objects, jobs and analyses.
- Production migration `20261120102957` (`beta_server_owned_result_writes`) was applied; authenticated client writes to analyses/jobs and trusted status fields are blocked while permitted paper uploads and owner-scoped reads remain. Service-role writes remain available.
- Railway API and Worker are online. Last-hour API sample: 13 requests, 11 2xx, 2 4xx, 0 5xx (small sample, not a load test). Supabase Performance Advisor has no findings; Security Advisor still reports leaked-password protection disabled.
- The full inline original-PDF viewer and junior-learning modules remain in Draft PR #18 and its READY Preview (https://financial-paper-analyzer-j6y0g8r1k-daegweonai-9583.vercel.app); they are not in the canonical production runtime. PR #18 is non-mergeable/diverged and must be reconciled before any promotion.
- PR #23 CI-cost optimization is merged. The scheduled 2026-11-21 15:40 deployment check was updated to skip redundant deployment when production runtime code is already current.
- Remaining human-only items: real Google OAuth smoke on production, actual iOS/Android device checks, SMTP provider configuration, leaked-password-protection decision, administrator UUID/service-wide budget/Gemini billing-mode designation, qualified review of six benchmark findings, and confirmation of GitHub Actions $0 stop-usage budget.
