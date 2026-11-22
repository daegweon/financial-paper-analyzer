# PaperSignal — production E2E and release closeout

## Superseding status — 2026-11-22

The entries below preserve the 2026-11-20 release-closeout record. Current state:
- `main` is `0c2e5b10c39eca1d6577fc36d9fcbe830dd653d2`; Vercel Production `dpl_MShcWWKJSoXDLZLbtxMcZvhzvq6G` is READY on the canonical domain; Railway API and Worker are Online 1/1.
- PR #41 is merged and its inline evidence UX is in Production. The 100% reader control maps to the former 90% visual size; equation parameter explanations are removed; comprehension-quiz typography is larger; duplicate evidence citations are grouped.
- 15 stale/duplicate PRs (#2–#16, #39, #40) were closed as superseded/archived on 2026-11-22. Their branches/commit history were retained. No open PRs or GitHub Issues remain after the cleanup check.
- GitHub Actions were not run for this closeout.
- The remaining tasks are external/human-owned: qualified review of six benchmark findings, live OpenAlex/public-PDF smoke, native iOS/Android QA, external SMTP/mailbox validation, leaked-password-protection decision, Gemini billing-tier confirmation, and account-level Actions billing verification. The current checklist is in [PROJECT_HANDOFF.md §10](PROJECT_HANDOFF.md).


**Updated:** 2026-11-20 (Asia/Seoul)  
**Current main:** `cec2d1a7ebdce8186a76e94b86181147eac1986c`  
**Canonical URL:** https://financial-paper-analyzer.vercel.app

## Verified complete

- Vercel production alias is attached to READY deployment `dpl_HBMsBWFBE4xY7yCNi9KQUE79KCJV`, deployed from main SHA `d6cc166a1ad0f0a396aa12d70ca81068198f3d03`.
- Comparing deployed SHA to current main shows only workflow/test/documentation changes after the deployed SHA; no application-runtime files changed. The deployed runtime therefore matches current main's app code.
- Deployed frontend contains Google sign-in, mobile logout and race-safe Supabase `getSession()` bootstrap.
- Live two-account synthetic E2E passed: [GitHub Actions #44722388440](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44722388440). The preflight passed, the real Worker/Gemini analysis completed, the owner retrieved a page-evidenced result, and the second user was denied access.
- A separate read-only Production query confirmed zero remaining synthetic Auth users, paper rows, PDF Storage objects, analysis jobs and analyses.
- Production migration `20261120102957` (`beta_server_owned_result_writes`) was applied. Authenticated clients cannot create analyses/jobs or edit trusted status fields; permitted paper-upload columns and owner-scoped reads remain; service-role writes remain.
- Railway API/Worker are online. Last-hour API sample: 13 requests, 11 2xx, 2 4xx, 0 5xx (small sample, not a load test).
- Supabase Performance Advisor: no findings. Security Advisor: one warning, leaked-password protection disabled.
- GitHub Actions cost optimization PR #23 is merged. The account-reported Actions usage was 1,800/2,000 minutes on 2026-11-20; current billing usage and $0 hard-stop budget cannot be independently read through the connected GitHub tools. The daily monitor remains enabled.

## Current production vs beta candidate

The production runtime includes the mobile Google sign-in and logout/session fixes.

The full inline original-PDF viewer, page-linked evidence UI and junior-learning modules are in Draft PR #18 and its READY Preview:
https://financial-paper-analyzer-j6y0g8r1k-daegweonai-9583.vercel.app

These broader candidate features are **not** in the canonical production runtime. PR #18 is non-mergeable/diverged from main (compare reports 494 commits ahead and 12 behind). Do not merge it directly; reconcile/rebase the candidate and run exact-head CI/Preview first.

Candidate QA evidence: [Checks #44687211580](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44687211580) passed API, frontend lint/build, disposable PostgreSQL policy tests and local synthetic Chromium/WebKit browser workflows. PDF unit tests cover page bounds, signed URL page fragments and link renewal. This is not a native iOS/Android device test.

## Remaining external or human-owned items

1. Real Google OAuth consent/callback smoke on the canonical production URL (the live E2E used synthetic email/password accounts).
2. Actual iOS Safari and Android Chrome checks, especially native PDF rendering, zoom, orientation, signed-link renewal and session expiry.
3. External SMTP provider/sender-domain configuration and confirmation/password-reset email tests.
4. Decide whether to enable Supabase leaked-password protection. The connected Supabase tools expose SQL/advisors but not Auth configuration mutation; no Auth policy was silently changed.
5. Designate the administrator Supabase Auth UUID before setting `PAPERSIGNAL_ADMIN_USER_IDS`; set any service-wide AI budget only after administrator approval.
6. Confirm Gemini billing mode in Google AI Studio before configuring cost reporting; never infer free/paid mode.
7. Qualified finance-domain review of six findings still flagged `review` in the latest mixed-version B01–B10 snapshot. The assistant second-pass audit is not expert sign-off.
8. Confirm GitHub Actions billing has a $0 budget with stop-usage protection. The account-reported 90% usage was not independently queryable through the connected GitHub API.

## Deployment automation

The 2026-11-21 15:40 Asia/Seoul task was updated to compare the alias with current runtime code first and skip deployment when production is already current. This avoids an unnecessary deployment and Actions-minute consumption.

## Rollback references

- Previous Vercel rollback candidate: `dpl_5y2EUXPkUDBeYomp2nxuok728Maa`; re-check READY state immediately before any rollback.
- `17c9134b-f49c-4358-a879-7ca77b55b936` is REMOVED and must not be used.
- Railway API rollback baseline: `0b5716db-b720-49db-b15c-babf77b26e5a`; re-check availability immediately before rollback.
- Worker deployment `dc501061-d434-454a-bc7d-4658b991a2f1` remains unchanged.

## Cost and mutation guardrails

- No paid Vercel plan upgrade or domain purchase.
- No additional production deployment was initiated in this closeout.
- No further Supabase migration was applied after the successful server-owned result-write migration.
- No customer records were modified by the synthetic E2E; only uniquely named temporary fixtures were created and cleaned.
- No analysis-engine prompt/model changes were made.
