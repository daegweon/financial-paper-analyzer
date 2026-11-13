# PaperSignal beta release gate

## Current automated verification

- Backend unit and contract suite: run with `cd backend && pytest`.
- The opt-in live E2E test is in `backend/tests/test_live_e2e.py`.
- It uses two distinct, pre-verified disposable Supabase Auth users.
- It uploads a synthetic two-page PDF, starts the real Railway API/Worker flow,
  waits for the durable job to complete, checks the saved analysis and page
  evidence, verifies cross-user isolation, then removes only its own test rows
  and Storage object.

## Required CI secrets

Configure these as GitHub Actions repository secrets before running the live test:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (or the new `sb_secret_*` key; server-side only)
- `PAPERSIGNAL_API_URL`
- `E2E_USER_A_EMAIL`, `E2E_USER_A_PASSWORD`
- `E2E_USER_B_EMAIL`, `E2E_USER_B_PASSWORD`

Both users must be separate, email-confirmed, disposable QA accounts in the
intended E2E Supabase project. Do not use employee or customer accounts.

## Manual execution

```bash
cd backend
PAPERSIGNAL_E2E_ENABLED=1 pytest -q tests/test_live_e2e.py
```

Set `E2E_TIMEOUT_SECONDS` if the test environment needs more than 15 minutes.
The test is skipped by default and cannot mutate a project unless explicitly
enabled. Cleanup runs in a `finally` block and is scoped to the unique test
paper ID and object path.

## Release gate

A beta release is not marked ready until:

1. Backend tests pass.
2. Frontend lint and production build pass.
3. The live E2E test passes using disposable, verified accounts.
4. A second user cannot read the first user's paper, PDF, analysis or job.
5. Railway API and Worker are online with no active failures.
6. Supabase security advisors contain no unresolved high-severity findings.
7. Production Vercel deployment is READY and the production URL is smoke-tested.
