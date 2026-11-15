# PaperSignal beta release gate

## Current automated verification

- Backend unit and contract suite: run with `cd backend && pytest`.
- The opt-in live E2E test is in `backend/tests/test_live_e2e.py`.
- It creates two unique, short-lived QA-only Supabase Auth users through the Admin API.
- Those test-only accounts are marked email-confirmed by the Admin API; the test does not disable project-wide email confirmation.
- It signs in both accounts, uploads a synthetic two-page PDF as user A, starts the real Railway API/Worker flow, and waits for durable analysis completion.
- It verifies the saved analysis and page evidence, then confirms user B cannot enqueue the paper, read its job, paper metadata, analysis, or private PDF.
- After the job reaches a terminal state, it removes only its own analysis/job/paper rows, Storage object, and two temporary Auth users. If the job remains active after timeout, it deliberately retains the fixture so the Worker does not lose its source PDF.

## GitHub Actions runner incident

The current GitHub run signature is `name=""`, `path="BuildFailed"`,
`conclusion=startup_failure`, zero jobs, and an empty billable timing result.
The base-branch workflow file exists and the connected GitHub account has
repository admin permission, so this is not currently attributable to a
pytest, Node.js, or YAML step failure.

Before asking GitHub Support to repair the repository's workflow registration,
check:

1. [GitHub account billing and payment settings](https://github.com/settings/billing/summary) for an account-level billing lock, failed payment authorization, or Actions spending limit.
2. Repository **Settings → Actions → General** to confirm Actions are enabled and allowed actions/workflow permissions are not restricted.
3. If the same zero-job signature persists, give GitHub Support the failing run URL and synthetic workflow ID `416243347`; request inspection of the `BuildFailed` workflow registration/dispatcher record.

Do not keep changing application code to address a failure that occurs before
GitHub creates a job. The Railway BuildKit gate remains the independent backend
release gate until GitHub Actions runs normally again.

## Deployment-time CI fallback

GitHub Actions is configured for pull requests and manual E2E runs, but the
repository currently has a runner provisioning issue (`startup_failure`
before jobs are created). Backend release safety no longer depends on that
runner:

- The root Railway Dockerfile has a BuildKit test stage that installs
  `backend/requirements-dev.txt` and runs `pytest -q` before producing the
  lean runtime image.
- Both the API and Worker production builds must pass that stage.
- The final runtime image copies only a test-pass marker; pytest and test-only
  packages are not installed into production.
- Vercel Preview builds execute the Next.js production build, including its
  TypeScript checks.

## Required CI secrets

Configure only these GitHub Actions repository secrets:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (or the new `sb_secret_*` key; server-side only)
- `PAPERSIGNAL_API_URL`

No reusable QA account credentials are needed. The test generates random addresses and passwords for each run and deletes the accounts after a terminal job.

**Scope note:** this test verifies authenticated sessions, tenant isolation, upload and analysis. It does not test outbound email delivery or the user's inbox confirmation-link journey. Keep a separate manual smoke test for a real signup and email confirmation before public beta; never disable email confirmation to make the E2E test pass.

## Manual execution

```bash
cd backend
PAPERSIGNAL_E2E_ENABLED=1 pytest -q tests/test_live_e2e.py
```

Set `E2E_TIMEOUT_SECONDS` if the test environment needs more than 15 minutes.
The test is skipped by default and cannot mutate a project unless explicitly
enabled. Cleanup runs in a `finally` block and is scoped to the unique test
paper ID and object path.

## Real email signup and confirmation

The application now displays a confirmation-pending state and supports resending
a signup confirmation email. It intentionally relies on Supabase's configured
Site URL when sending the email; it does not invent a redirect URL that may not
be on the project's allow list.

Before testing:

1. In [Supabase Auth URL Configuration](https://supabase.com/dashboard/project/hwmtayrecsfxernhssro/auth/url-configuration), set the Site URL to
   `https://financial-paper-analyzer.vercel.app`.
2. Add `https://financial-paper-analyzer.vercel.app/**` to the redirect URL allow list.
3. Keep email confirmation enabled.
4. Configure a custom SMTP provider in [Supabase Auth SMTP settings](https://supabase.com/dashboard/project/hwmtayrecsfxernhssro/auth/smtp) before sending to arbitrary external test inboxes.
5. Run a signup with a mailbox that the tester can access, open the confirmation link, verify that the browser returns to PaperSignal and the user is signed in, then test sign-out/sign-in and resend behavior.

**Current provider limitation:** the Supabase organization is on the Free plan.
Supabase's built-in SMTP is for testing only: it sends only to organization team
member addresses and is limited to 2 messages per hour across the project while
email confirmation is enabled. It is not suitable for an external beta audience.
Configure custom SMTP (for example Resend, AWS SES, Postmark, SendGrid or Brevo),
verify SPF/DKIM/DMARC for the sending domain, and test delivery before public
signup. Never disable email confirmation to bypass delivery limits.

## OAuth incident diagnosis — 2026-11-15

The original callback failure was caused by an invalid Google OAuth Client
Secret (`invalid_client`) and an earlier Supabase Site URL that sent the
browser back to `http://localhost:3000`. The operator has since created and
saved a new Google Client Secret and updated Site URL to the production
PaperSignal origin.

Post-change verification:

- Supabase Auth public settings report `external.google=true`.
- OAuth authorization requests return HTTP 302 to
  `accounts.google.com/o/oauth2/v2/auth` for both the production origin and
  the current Vercel Preview origin.
- Both redirects use the same Google Web Client ID and the correct Supabase
  callback `https://hwmtayrecsfxernhssro.supabase.co/auth/v1/callback`.
- Supabase Auth logs after the configuration update show authorization
  requests from the production and Preview origins and no new
  `invalid_client` / `Unable to exchange external code` errors.
- No callback request has yet been recorded after the configuration update.
  The Google consent, token exchange, session creation and library access
  still require a real account completing the interactive browser flow.

The frontend uses the current origin as `redirectTo` and displays a safe,
actionable message if OAuth returns an error. It removes duplicate OAuth error
parameters without altering a valid PKCE `code`.


## Google account and existing-library policy

A successful Google sign-in can create a new Auth user if the Google email
does not match an existing verified account. Supabase's automatic identity
linking is based on matching verified email addresses; do not merge accounts
solely because one person controls both. The latest QA Google identity is a
separate user from the account that owns the historical 11-paper/44-analysis
library. The existing library remains intact and visible only after signing
in with its original account.

Do not automatically move research data or attempt manual identity linking
for an identity already attached to another Auth user. Any future migration
must authenticate both source and destination accounts, obtain explicit
confirmation, and transactionally transfer the paper metadata, private
Storage objects, analysis history and jobs while preserving auditability.

## Google OAuth login

The application now exposes a Google sign-in button. It uses Supabase Auth
`signInWithOAuth({ provider: "google" })`, redirects back to the current
deployment origin, requests account selection, and uses the PKCE flow with
automatic URL code detection/exchange in the browser.

**Google provider activation is confirmed, but callback login is not yet working.**
The public Auth settings report `external.google=true` and both origins
return an HTTP 302 toward Google. Actual callback attempts failed because
Supabase holds an invalid Google OAuth Client Secret; error callbacks also
landed on a stale localhost Site URL. Follow the incident fix above.
Do not treat the HTTP 302 as a completed OAuth login.

Configuration reference (already applied by the operator):

1. In [Google Auth Platform](https://console.cloud.google.com/auth/overview),
   create a project/app and configure the OAuth consent screen for **PaperSignal**.
   If the consent screen is in Testing mode, add the Google accounts used for QA
   as test users.
2. Create an OAuth Client ID of type **Web application**.
3. Add these exact **Authorized JavaScript origins**:
   - `https://financial-paper-analyzer.vercel.app`
   - `https://financial-paper-analyzer-git-feat-resear-0de08f-daegweonai-9583.vercel.app`
   - `http://localhost:3000` (local development only)
4. Add this exact **Authorized redirect URI** in Google:
   `https://hwmtayrecsfxernhssro.supabase.co/auth/v1/callback`
5. In [Supabase Auth → Sign In / Providers → Google](https://supabase.com/dashboard/project/hwmtayrecsfxernhssro/auth/providers?provider=Google),
   enable Google and enter the Google Web Client ID and Client Secret. Keep the
   secret in Supabase Auth settings only; do not add it to Vercel or browser
   environment variables.
6. In [Supabase Auth URL Configuration](https://supabase.com/dashboard/project/hwmtayrecsfxernhssro/auth/url-configuration),
   set Site URL to `https://financial-paper-analyzer.vercel.app` and allow:
   - `https://financial-paper-analyzer.vercel.app/**`
   - `https://*-daegweonai-9583.vercel.app/**` (Vercel previews)
   - `http://localhost:3000/**` (local development only)
7. Complete a real browser smoke test with a Google account in both production
   and Preview. Confirm Google consent returns to PaperSignal, the session is
   created, and only that user's library is visible.

## Supabase Auth security setting — accepted Free-plan limitation

The Supabase security advisor reports one `WARN` finding:
**Leaked Password Protection disabled**. This is an intentional, accepted
limitation under the product's cost decision:

- Keep the Supabase organization on the **Free** plan.
- Do not upgrade to Pro solely to enable this feature.
- Leave Leaked Password Protection disabled; no configuration change is needed.
- Record the advisor warning as an accepted residual risk, not as an unresolved
  release blocker. Re-check the advisor after future Auth configuration changes
  and ensure no separate `ERROR` or `CRITICAL` findings are present.

This decision does not disable email confirmation, password verification,
RLS, or the existing API authorization checks. Users should still choose
unique, strong passwords.

## Release gate

A beta release is not marked ready until:

1. Backend tests pass.
2. Frontend lint and production build pass.
3. The live E2E test passes using disposable Auth accounts, and a real external mailbox completes signup confirmation through custom SMTP.
4. Google OAuth is enabled in Supabase and a real Google sign-in smoke test succeeds on the production origin.
5. A second user cannot read the first user's paper, PDF, analysis or job.
6. Railway API and Worker are online with no active failures.
7. The leaked-password-protection `WARN` is recorded as the accepted Free-plan limitation; no separate `ERROR` or `CRITICAL` security findings remain. Do not upgrade to Pro solely for this setting.
8. Production Vercel deployment is READY and the production URL is smoke-tested.
