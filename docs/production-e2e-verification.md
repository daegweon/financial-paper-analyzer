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

On an isolated Vercel sandbox, 10 tests passed (0 failed). They cover:

- Valid synthetic PDF text extraction and page-number provenance
- Invalid signature and oversize rejection
- Blank/scanned PDF requiring OCR
- Exact page-level source excerpt verification
- Authentication missing or cross-user paper denied
- Mocked authenticated flow: JWT validation -> private document metadata -> authenticated PDF fetch -> analysis INSERT -> paper status PATCH

**Important:** The authenticated integration test stubs Supabase HTTP responses. It does **not** prove successful execution of a real email-confirmed user session against live Supabase.

## Outstanding live E2E scenario

Supabase Auth has `mailer_autoconfirm=false`, requiring email confirmation. Do not disable this merely to pass tests. Use a real verified test account:

1. Open the Vercel URL; sign up and verify email.
2. Sign in, upload the deliberately synthetic QA PDF.
3. Open the document and click **분석 시작**.
4. Confirm the result is `extractive`, shows two pages and page-numbered text excerpts.
5. Confirm a new row exists in `papers` and `analyses` for the same authenticated user.
6. Sign in as a second account and verify the first user's paper is invisible and inaccessible.
7. Verify no exception or 5xx in Railway runtime logs and the browser console.
8. Verify PDF document and analysis record can be re-opened after refreshing the page.

Sample synthetic PDF can be generated from `backend/tests/test_integration_contract.py` (fixture function `make_pdf`). It contains **no genuine financial research**.

## Durable worker and recovery verification (2026-11-14)

- Railway API and independent Worker are both online in production; extractive API remains online.
- A synthetic two-page PDF completed through the real Supabase queue and Worker using `finance-structured-v6.2`.
- A second real Worker execution persisted two checkpoints: `pdf_extracted` and `analysis_result`.
- The completed job was deliberately re-queued to simulate a crash after result commit. The Worker detected the existing `job_id` result and completed the job without creating a second analysis row (one result row remained).
- A disposable SQL integration probe verified checkpoint upsert uniqueness and analysis upsert idempotency. Test rows were removed afterward.
- Retry/backoff, terminal failure after the configured attempt limit, lease renewal, stale-lease recovery and duplicate-active-job prevention were previously exercised.
- Supabase checkpoint data is protected by RLS and an explicit `service_role`-only policy. New `sb_secret_*` keys are sent in the `apikey` header only.

## Known gaps

- PDF extraction currently scans up to the first 50 pages; OCR for image-only PDFs is not implemented.
- Full real-browser signup, verified-email upload, and cross-account isolation remain unverified. Do not disable email confirmation merely to pass this check.
- GitHub Actions on this private repository have repeatedly returned `startup_failure` before jobs start. Python checks were executed independently; investigate runner quota / repository Actions configuration before enforcing branch protection.
- Supabase Auth leaked-password protection is disabled and should be enabled in the Auth security settings.
- Deletion/retention UX for papers, analyses and checkpoints still needs a product-level lifecycle policy.

## Security notes

- All user-owned tables have RLS policies.
- Anonymous Data API SELECT of `papers` and `analyses` is denied.
- Storage bucket `papers` is private.
- Never expose Supabase service-role/secret keys, and never commit external AI API keys.
- For regression tests, use an isolated environment with controlled test accounts instead of changing production email-confirmation settings.
