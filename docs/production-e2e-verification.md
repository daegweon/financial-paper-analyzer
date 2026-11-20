# PaperSignal - Production Integration Verification

**Run date:** 2026-11-13 (KST)  
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
| Supabase security advisor | No warnings | PASS |

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

## Known gaps

- LLM-assisted interpretation is disabled until `OPENAI_API_KEY` is securely configured on Railway.
- PDF processing is synchronous and scans the first 50 pages; OCR is not implemented.
- The application currently supports neither deletion of paper records nor durable queued processing.
- GitHub Actions workflows on this private repo have repeatedly returned `startup_failure` with no jobs. This is a CI/integration issue to investigate; the 10 tests were executed independently.
- Full real-browser signup and authenticated PDF persistence remain unverified.

## Security notes

- All user-owned tables have RLS policies.
- Anonymous Data API SELECT of `papers` and `analyses` is denied.
- Storage bucket `papers` is private.
- Never expose Supabase service-role/secret keys, and never commit external AI API keys.
- For regression tests, use an isolated environment with controlled test accounts instead of changing production email-confirmation settings.


---

## 2026-11-20 — Real production two-account E2E closeout

**GitHub Actions:** [#44722388440](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44722388440)  
**Pinned test source:** `431059a1116a50f39fd56d565c35a1afc081b8fc`  
**Result:** PASS — `1 passed, 27 deselected`.

The manual workflow verified the protected secrets, fixed Production Supabase/API origins and server-owned API health marker before mutating data. The live test then:

1. Created two distinct temporary synthetic Supabase Auth users.
2. Uploaded a private synthetic two-page PDF as user A and verified the original PDF bytes and owner-only signed URL.
3. Enqueued analysis through Railway API, observed a terminal `completed` job and read the saved result with page-level evidence.
4. Confirmed user B received 404/empty owner-scoped results for A's paper/job/analysis and could not download or sign A's private PDF.
5. Ran scoped cleanup in `finally`.

A separate read-only Production SQL query after the run returned zero for synthetic Auth users, paper rows, PDF Storage objects, analysis jobs and analyses.

Production migration `20261120102957` (`beta_server_owned_result_writes`) had been applied before this run. Railway API/Worker remained online; the API's observed last-hour sample was 13 requests with zero 5xx responses.

### Current production frontend

The canonical alias `financial-paper-analyzer.vercel.app` points to READY deployment `dpl_HBMsBWFBE4xY7yCNi9KQUE79KCJV`, deployed from main SHA `d6cc166a1ad0f0a396aa12d70ca81068198f3d03`. Current main is `cec2d1a7ebdce8186a76e94b86181147eac1986c`; later changes modify only workflow/test/documentation files, not application-runtime files. The deployed frontend contains Google sign-in, mobile logout and the race-safe `getSession()` bootstrap.

### Scope not proven by this live API E2E

- This test used synthetic email/password accounts, not a live Google OAuth consent flow.
- It proves the API/Worker/DB/Storage two-account path, not native iOS Safari/Android Chrome behavior.
- The full inline original-PDF viewer and junior-learning components remain on Draft PR #18 and its READY Preview (https://financial-paper-analyzer-j6y0g8r1k-daegweonai-9583.vercel.app); they are not in the current canonical production runtime.
- Supabase Security Advisor still warns that leaked-password protection is disabled. SMTP, administrator designation and qualified review of six benchmark findings remain outstanding.
