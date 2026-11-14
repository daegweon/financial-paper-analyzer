# PaperSignal - Production Integration Verification

**Run date:** 2026-11-14 (KST)  
**Target:** `https://financial-paper-analyzer.vercel.app`  
**API:** `https://papersignal-api-production.up.railway.app`  
**Database:** Supabase project `hwmtayrecsfxernhssro` (Seoul)

## Verified against actual deployed HTTPS endpoints

| Check | Actual result | Status |
|---|---|---|
| Vercel homepage | HTTP 200 | PASS |
| Railway Python FastAPI `/health` | HTTP 200, `status=ok` | PASS |
| Anonymous `POST /api/analyze/{uuid}` | HTTP 401 | PASS |
| Invalid bearer token `POST /api/analyze/{uuid}` | HTTP 401 | PASS |
| Authorized-origin CORS preflight | HTTP 200, origin + Authorization allowed | PASS |
| Supabase Auth settings | HTTP 200, email provider enabled | PASS |
| Supabase public `papers` SELECT | HTTP 401, permission denied | PASS |
| Supabase public `analyses` SELECT | HTTP 401, permission denied | PASS |
| Deployed Next.js JavaScript includes expected API base URL | Yes | PASS |
| Deployed Next.js JavaScript includes Supabase URL | Yes | PASS |
| Supabase checkpoint RLS policy | Explicit service_role-only policy | PASS |

## Python integration contract tests

From repository root:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

On an isolated Python 3.12 Vercel sandbox, **68 tests passed and 1 opt-in live E2E test was skipped**. They cover:

- Valid synthetic PDF text extraction and page-number provenance
- Invalid signature and oversize rejection
- Blank/scanned PDF requiring OCR
- Exact page-level source excerpt verification
- Authentication missing or cross-user paper denied
- Mocked authenticated flow: JWT validation -> private document metadata -> authenticated PDF fetch -> analysis INSERT -> paper status PATCH

**Important:** The authenticated integration test stubs Supabase HTTP responses. It does **not** prove successful execution of a real email-confirmed user session against live Supabase.

## Outstanding live E2E scenario

The live test is in `backend/tests/test_live_e2e.py`. It provisions two
unique, short-lived Supabase Auth users through the server-side Admin API,
marks only those disposable QA users email-confirmed, and signs them in. It
does not disable project-wide email confirmation and does not require stored
test-account credentials.

To run it manually, set:

- `PAPERSIGNAL_E2E_ENABLED=1`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PAPERSIGNAL_API_URL`

The test then uploads a synthetic two-page PDF, runs the real API/Worker flow,
checks saved analysis evidence, and verifies that a second user cannot read
the first user's job, paper, analysis, or private PDF. It removes only its own
rows, Storage object and temporary Auth users after the job reaches a terminal
state. If a job remains active, it retains the fixture so the Worker does not
lose its source document.

**Not yet verified:** delivery of a real signup confirmation email and the
user's inbox/link journey. Keep a manual signup-and-email-confirmation smoke
test as a public-beta release gate; do not turn off email confirmation.


## Durable worker and recovery verification (2026-11-14)

- Railway API and independent Worker are both online in production; extractive API remains online.
- A synthetic two-page PDF completed through the real Supabase queue and Worker using `finance-structured-v6.2`.
- A second real Worker execution persisted two checkpoints: `pdf_extracted` and `analysis_result`.
- The completed job was deliberately re-queued to simulate a crash after result commit. The Worker detected the existing `job_id` result and completed the job without creating a second analysis row (one result row remained).
- A disposable SQL integration probe verified checkpoint upsert uniqueness and analysis upsert idempotency. Test rows were removed afterward.
- Retry/backoff, terminal failure after the configured attempt limit, lease renewal, stale-lease recovery and duplicate-active-job prevention were previously exercised.
- Supabase checkpoint data is protected by RLS and an explicit `service_role`-only policy. New `sb_secret_*` keys are sent in the `apikey` header only.

## Auth readiness update (2026-11-14)

- Signup UI distinguishes pending email confirmation from a completed session and exposes a resend-confirmation action. It uses the Supabase project's configured Site URL.
- Google sign-in UI is implemented using Supabase Auth OAuth with PKCE, automatic URL code exchange, current-origin redirects, and account selection. The Google provider is not yet active: a Google Web OAuth Client ID/Secret must be created and entered in Supabase Auth settings. See `docs/BETA_RELEASE_RUNBOOK.md`.
- Google callback URI for Google Cloud: `https://hwmtayrecsfxernhssro.supabase.co/auth/v1/callback`. Supabase's Site URL and redirect allow list must include the production, Vercel Preview, and local origins documented in the runbook.
- The actual email inbox confirmation journey remains unverified. The Supabase organization stays on Free; its built-in SMTP is restricted to organization team-member addresses. Configure custom SMTP and test an accessible external inbox before public beta.
- Leaked Password Protection remains disabled by explicit product decision: keep the Supabase organization on Free and do not upgrade to Pro solely for this feature. Its single security-advisor `WARN` is accepted and documented; no separate `ERROR` or `CRITICAL` findings should remain.
- Latest Vercel Preview for the auth UI is READY. Railway API and Worker remain Online; the latest API/Worker image builds execute the backend test stage before packaging.

## GitHub Actions incident update (2026-11-14)

- A fresh failed run has `name=""`, `path="BuildFailed"`, `conclusion="startup_failure"`, and `workflow_id=416243347`.
- The run jobs endpoint returns `total_count=0`, and the run timing API returns an empty `billable` object. This confirms the failure occurs before a runner/job is created.
- The repository is private, the connected account has repository admin permission, and `.github/workflows/checks.yml` exists on the base `main` branch.
- The connector cannot inspect account-level billing or all repository Actions settings. Check GitHub billing/payment authorization and Settings → Actions → General; if still failing, provide the run ID and synthetic workflow ID to GitHub Support.
- This is not evidence of a failure in the Python/Node test commands. Railway's BuildKit gate remains active.

## Beta release gate update (2026-11-14)

- Backend regression suite on the current branch: **68 passed, 1 skipped**. The skipped test is the opt-in live E2E scenario because disposable verified user credentials are not configured in this environment.
- Live E2E harness: `backend/tests/test_live_e2e.py`. It verifies two distinct verified users, private PDF upload, real API/Worker completion, saved page evidence, and second-user denial. It deletes only its own test rows and Storage object after the job reaches a terminal state.
- Manual workflow: GitHub Actions `workflow_dispatch` runs the live E2E job. Configure the documented disposable-user secrets first; the test is skipped when configuration is absent.
- Release runbook: `docs/BETA_RELEASE_RUNBOOK.md`.
- Checkpoint retention: a database trigger removes extracted page text and model-result checkpoints when a job completes or reaches terminal failure. Retryable failures retain checkpoints for resumption.
- Current production deployment: API and Worker both use the durable checkpoint/idempotency code; all three Railway services are Online. Vercel Preview builds are READY.
- Production Worker E2E on the existing synthetic two-page QA paper: first attempt received Gemini HTTP 503 from both configured models; the job was retried automatically. Attempt 2 logged `Resuming from PDF checkpoint`, completed with `finance-structured-v6.2` using `gemini-3.5-flash-lite`, and saved one analysis row with eight page-level evidence items.
- The terminal-state database trigger removed both temporary checkpoint payloads after completion. The disposable job and linked analysis row were then removed; the original synthetic paper and its pre-existing analysis were preserved.
- GitHub Actions still reports `startup_failure` before creating jobs on this private repository. To avoid making backend release safety depend on that runner, the root Railway Dockerfile now has a mandatory BuildKit test stage: it installs the dev requirements, runs the complete backend suite, and only then allows the lean runtime image to be assembled. Vercel Preview builds continue to enforce the frontend Next.js/TypeScript build. The GitHub-hosted runner provisioning issue remains separately open.
- Railway production API and Worker Docker builds both executed the mandatory BuildKit test stage successfully: **68 passed, 1 skipped** on each image build. The runtime image remains lean; pytest is not copied into the final image.
- The first attempt exposed that `.dockerignore` excluded `backend/tests`; this was corrected with explicit Docker ignore exceptions. The subsequent API and Worker deployments both built successfully and are Online.


## Known gaps

- Full real-browser signup, verified-email flow, and live two-account E2E have not yet been executed because disposable verified test-account credentials are not configured. The automated test harness is ready.
- Supabase Auth leaked-password protection remains disabled and must be enabled in Auth security settings before a broad public beta.
- GitHub Actions runner provisioning remains unresolved; inspect repository Actions billing/usage and organization policy before relying on branch protection.
- PDF extraction currently scans up to the first 50 pages; OCR for image-only PDFs is not implemented.
- Paper deletion and long-term retention UX still need a product-level lifecycle policy.
