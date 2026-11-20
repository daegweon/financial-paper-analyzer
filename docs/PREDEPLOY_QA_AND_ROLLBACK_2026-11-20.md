# PaperSignal — pre-deployment QA and rollback checklist

**Prepared:** 2026-11-20 (Asia/Seoul)  
**Current main SHA:** `119546fdcb3b116335b80ed9c734beff0a241e81`  
**Current production alias:** `financial-paper-analyzer.vercel.app`  
**Current production deployment / rollback baseline:** `dpl_5y2EUXPkUDBeYomp2nxuok728Maa`  
**Latest auth-fix Preview:** `dpl_8tcLEBHHS46yqaimn5MEtQjbge34` (READY, but Preview only)

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
