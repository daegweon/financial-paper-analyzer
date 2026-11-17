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
