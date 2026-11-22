# PaperSignal — Administrator dashboard navigation

**Date:** 2026-11-22 (KST)  
**Repository:** https://github.com/daegweon/financial-paper-analyzer  
**Production:** https://financial-paper-analyzer.vercel.app  
**Application release commit:** `1b543c07840e69873b74c90571226ca6a19c0b31`

## User-facing behavior

- The designated administrator is the Google OAuth account `sseeve2@gmail.com`.
- After login, the desktop workspace left sidebar shows **AI 사용량 및 비용 관리** below the normal **논문 라이브러리** item.
- At viewport widths where the left sidebar is hidden (mobile), the workspace header shows a **관리자 대시보드** shortcut.
- Both links open `/admin/ai-usage`.
- Regular users see neither administrator link.
- If admin access cannot be confirmed, the UI hides the link (fail closed).

## Authorization flow

1. The workspace obtains the current Supabase session.
2. The frontend calls `GET /api/admin/access` with `Authorization: Bearer <access_token>`.
3. The backend validates the token with Supabase using the existing `_verify_user` helper.
4. The backend compares the verified Supabase Auth UUID against the server-side `PAPERSIGNAL_ADMIN_USER_IDS` allowlist.
5. It returns only `{"is_admin": true}` or `{"is_admin": false}`. No user email, UUID, usage event or cost data is returned.
6. Missing/invalid authentication is rejected (401). An authenticated non-admin receives `{"is_admin": false}`.
7. On account change, sign-out, endpoint failure or malformed response, the frontend resets the admin state to false.

**Important:** Menu visibility is only a navigation convenience. It is not authorization. The existing `GET /api/admin/ai-usage/summary` and `POST /api/admin/ai-usage/budget` endpoints independently validate the bearer token and admin allowlist on every request. Non-admin access to those routes returns 403.

## Implementation locations

| File | Responsibility |
|---|---|
| `frontend/app/page.tsx` | Reads the session, requests admin visibility, conditionally renders desktop and mobile links |
| `frontend/app/globals.css` | Admin menu and mobile shortcut styling |
| `backend/app/main.py` | `GET /api/admin/access` and existing admin usage/budget routes |
| `backend/tests/test_admin_ai_usage_access.py` | Route-level access tests |
| `frontend/app/admin/ai-usage/page.tsx` | Existing AI usage and cost dashboard |

## Dashboard functions

The administrator dashboard at `/admin/ai-usage` provides:
- Monthly service-wide AI usage and cost estimates.
- Provider/model breakdown, event outcomes, token counts and latency.
- User-level internal usage aggregates.
- Service-wide monthly AI budget configuration.
- Explicit incomplete/unknown cost statuses.

The cost report is an operational estimate, not an invoice or an automatic hard spending cap.

## Test coverage and release verification

Three tests were added:
- Allowlisted administrator receives `{"is_admin": true}`.
- Authenticated regular user receives `{"is_admin": false}`.
- Unauthenticated request receives HTTP 401.

The Railway build for application commit `1b543c0` reported **250 passed, 1 skipped** for the backend test suite. Vercel Production deployment `dpl_Gqps3z6RJedj6YpDSgU78UL1SX1S` reached READY and was assigned the canonical `financial-paper-analyzer.vercel.app` alias. Railway API and Worker deployments both completed SUCCESS and reported Online 1/1.

GitHub Actions were not run.

## Operations

- Keep `PAPERSIGNAL_ADMIN_USER_IDS` server-side in Railway API variables. Never copy the UUID or secret values into source control or browser code.
- To add/remove an administrator, update the allowlist through the approved Railway variable-management process, then verify with the authenticated account.
- Do not rely on the email label for authorization; the backend checks the verified Supabase Auth UUID.
- Do not expose this dashboard to regular users or move its authorization logic to the frontend.
