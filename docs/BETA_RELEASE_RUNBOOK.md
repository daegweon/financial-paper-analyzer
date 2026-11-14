# PaperSignal beta release gate

## Current automated verification

- Backend unit and contract suite: run with `cd backend && pytest`.
- The opt-in live E2E test is in `backend/tests/test_live_e2e.py`.
- It creates two unique, short-lived QA-only Supabase Auth users through the Admin API.
- Those test-only accounts are marked email-confirmed by the Admin API; the test does not disable project-wide email confirmation.
- It signs in both accounts, uploads a synthetic two-page PDF as user A, starts the real Railway API/Worker flow, and waits for durable analysis completion.
- It verifies the saved analysis and page evidence, then confirms user B cannot enqueue the paper, read its job, paper metadata, analysis, or private PDF.
- After the job reaches a terminal state, it removes only its own analysis/job/paper rows, Storage object, and two temporary Auth users. If the job remains active after timeout, it deliberately retains the fixture so the Worker does not lose its source PDF.

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

## Supabase Auth security setting

Before public beta, enable **Leaked Password Protection** for the Email provider
in the [PaperSignal Supabase Auth settings](https://supabase.com/dashboard/project/hwmtayrecsfxernhssro/auth/providers?provider=Email).
The current Supabase security advisor still reports this control as disabled.
Re-run the Supabase security advisor after enabling it and record a clean result.

## Release gate

A beta release is not marked ready until:

1. Backend tests pass.
2. Frontend lint and production build pass.
3. The live E2E test passes using disposable, verified accounts.
4. A second user cannot read the first user's paper, PDF, analysis or job.
5. Railway API and Worker are online with no active failures.
6. Supabase Auth leaked-password protection is enabled and the Supabase security advisor has no unresolved high-severity findings.
7. Production Vercel deployment is READY and the production URL is smoke-tested.
