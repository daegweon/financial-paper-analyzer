# PaperSignal — Read-only cross-browser beta QA (2026-11-17)

## Scope
This change adds an opt-in Playwright browser test harness above Draft PR #15. It does not change the finance analysis engine, Gemini, Railway Worker, Supabase schema/Auth policy, or production deployment.

Installed @playwright/test version 1.65.1 as a development-only package. Browser QA is NEVER executed in a Vercel build. Next.js prebuild runs the existing frontend tests plus five new pure safety tests for target URL validation.

## Target security
- PAPERSIGNAL_BROWSER_QA must be explicitly set to 1.
- PAPERSIGNAL_BROWSER_QA_URL must identify this project's feature Preview, or localhost port 3000; production, main aliases, arbitrary hosts, paths, query strings and credentials fail closed.
- For a protected Preview, pass the temporary VERCEL_OIDC_TOKEN from the linked project's authenticated Vercel development context. The custom browser route adds the token only for requests to the exact Preview origin, never to Google, Supabase or external origins.
- Do not disable Vercel Deployment Protection to run browser QA.
- No uploads, analysis execution, Auth user creation, deletion or mutations; only login, read, navigation, token sign requests, logout and a simulated one-time signing error intercepted inside the browser.
- No browser storage-state export, Playwright trace, video or screenshots. No token, signed URL, credentials or PDF body in debug output.

## Browser coverage
- desktop Chromium: 1440x900
- Android-style Chromium: 375x812
- iPhone-style WebKit: 390x844

Anonymous checks: login, Google button, signup/login switch and 320px width.
Authenticated email QA checks: login, open pre-existing multi-page analyzed QA PDF, signed document HTTP response and real PDF magic bytes, original source iframe page navigation, citation jump, new-tab fallback, Escape/focus restoration, logout, and a simulated PDF signing error with a manual successful retry.
Two-user browser check: after account A signs out and B signs in, A's paper and open modal are absent from B's UI.

This browser check does NOT independently verify iOS Safari visual rendering or VoiceOver announcements, real Google consent OAuth, SMTP email confirmation, signed-link renewal after 50 minutes, or backend tenant RLS. Those remain separate real-device/production-release gates. Supabase signed URLs are bearer capabilities: possession of A's valid signed URL does not constitute a valid RLS isolation test; use the existing backend two-user integration suite for private Storage authorization.

## Running the tests
Run from the frontend directory on a browser-capable CI or trusted developer environment:

1. npm install
2. npx playwright install --with-deps chromium webkit
3. Supply PAPERSIGNAL_BROWSER_QA=1 and PAPERSIGNAL_BROWSER_QA_URL as the exact https Preview origin (or localhost:3000).
4. If Vercel Preview protection is enabled, obtain a short-lived development VERCEL_OIDC_TOKEN through the authenticated Vercel CLI context; do not commit or print it.
5. npm run test:browser:anonymous
6. For authenticated checks, set PAPERSIGNAL_QA_EMAIL and PAPERSIGNAL_QA_PASSWORD from a dedicated verified QA account; set PAPERSIGNAL_QA_PAPER_ID to the UUID of an existing analyzed, multi-page, public/synthetic QA paper whose results contain at least one positive page citation. Then run npm run test:browser:authenticated.
7. For tenant checks, additionally configure PAPERSIGNAL_QA_B_EMAIL and PAPERSIGNAL_QA_B_PASSWORD for a DIFFERENT verified test account. Run npm run test:browser:tenant.

Do not reuse real customer credentials or private confidential papers. No QA secrets need to be added to the app frontend environment.

## Release gates and evidence
- Run the browser suites in all three browser profiles; record date, exact Preview commit, browser/device, pass/fail and non-secret issue description.
- Actual mobile Safari, Android Chrome, two-account backend RLS, Google callback, external SMTP, production smoke and rollback drill must be separately signed off.
- If credentials or Vercel access are missing, mark browser tests PENDING; do not report them passed because TypeScript/Next.js build succeeded.
- GitHub Actions continues to show startup_failure with zero jobs. Diagnose account Actions billing and repository settings before attributing it to app code.
- Do not merge stacked Draft PRs or promote to production until gates are met.


## Read-only infrastructure baseline — November 17, 2026
This is a snapshot for the eventual release/rollback plan, NOT authorization to deploy or a successful smoke-test result.

Vercel:
- Current main Production deployment READY: dpl_33BMEgCAGgZVW9XWDk2n2VvFgmZg, commit f5d0345cf4d4f507c0c4a521bfea71adbc14541d.
- Previous READY Production rollback candidate: dpl_BSDxZJFMPXrpFNvaf6i38iGScANj, commit 8dabcb3b9c7866f20f67a039daa5f1d6e7edee28.
- This PR's Preview is not Production and must not be assigned the public domain solely because its build is READY.

Railway production environment 0b4f06c3-504a-4610-8995-395c2f4d3d1f:
- Core papersignal-api latest deployment 17c9134b-f49c-4358-a879-7ca77b55b936: SUCCESS, online, zero failures in the preceding 24 hours.
- Core papersignal-worker latest deployment dc501061-d434-454a-bc7d-4658b991a2f1: SUCCESS, online, zero failures in the preceding 24 hours.
- Separate papersignal-table-benchmark experimental service: online, but three recent failed historical deployments during the prior 24 hours. This is not evidence the main API or Worker is down. Keep engine frozen; investigate experimental cost/cleanup separately instead of expanding the beta scope.
- Railway reported no pending staged changes at inspection time.

Safe release sequence, ONLY after the real QA gates pass:
1. Re-check the exact Production/Preview commit IDs and all service health states; record tested immutable build, time and manual approval.
2. Test the staged Production build without assigning the public domain, with production environment configuration and non-sensitive synthetic data.
3. After explicit approval, promote the exact reviewed Production build to the public domain. A Preview build is not an equivalent staged Production build: promotion can rebuild with different environment variables.
4. On incident, use the recorded eligible previous Production deployment as the rollback target, then verify login, library and PDF access. Be aware that rollback suspends automatic domain assignment; a subsequent explicit promote is required to restore normal assignment.
5. No production deployment, promotion, rollback or worker restart was performed during this milestone.

## Executed isolated browser smoke — November 18, 2026

An isolated Vercel Sandbox received only frontend source. No production environment secrets, private PDFs, live Supabase credentials or customer accounts were included.

Anonymous tests against local Next.js at localhost:3000 and a dummy public Supabase URL:
- desktop Chromium: 2/2 PASS (login/signup toggle and 320px viewport overflow)
- Android Chromium emulation: 2/2 PASS
- iPhone WebKit emulation: 2/2 PASS
- Total anonymous: 6/6 PASS.

An additional local-only Playwright test intercepts requests to a synthetic Supabase endpoint at 127.0.0.1:54321 and provides fake users A/B, a fake paper, analysis and PDF.
- desktop Chromium: 3/3 PASS
- Android Chromium: 3/3 PASS
- iPhone WebKit: 3/3 PASS
- Tested: synthetic sign-in, paper reading, PDF page/citation jump, logout, manual signing retry and A/B UI isolation.
- Total synthetic authenticated-like UI integration: 9/9 PASS.
- Combined isolated local browser tests: **15/15 PASS**. These tests did not run on protected Vercel Preview.

Reproduction steps in a disposable local test process:
1. Launch the frontend dev server with NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_local_qa_only and NEXT_PUBLIC_API_URL=http://127.0.0.1:54322.
2. Set PAPERSIGNAL_BROWSER_QA=1, PAPERSIGNAL_BROWSER_QA_URL=http://localhost:3000 and PAPERSIGNAL_BROWSER_QA_MOCKS=1.
3. Run npm run test:browser:anonymous and npm run test:browser:mock.

**Do not mark real OAuth, Supabase authentication, Storage/RLS authorization, actual uploaded PDF bytes, 50-minute link renewal or mobile Safari devices as PASS.** They remain PENDING and require authorized QA credentials, Preview authentication, and device testing.
