# PaperSignal — Mobile and original PDF usability checkpoint (2026-11-17)

## Product rule: engine frozen

For this milestone **do not change** Gemini/LLM prompts, extraction, page evidence validation, PyMuPDF, FastAPI, queues, database, migrations, or Railway Worker. Focus on the user's ability to log in, open the uploaded **original** PDF, navigate cited pages and recover from common interruptions.

This checkpoint builds on Draft PR #11 and is implemented in Draft PR [#12](https://github.com/daegweon/financial-paper-analyzer/pull/12).

## Frontend changes

- Mobile sign-in now puts the actual form higher on small screens instead of reserving ~350 px for the promotional pitch.
- The research detail is a labelled modal dialog with Escape-to-close, focus containment and focus restoration. Background body scrolling is paused while open.
- PDF controls and source actions are touch-friendly on narrow screens; the original PDF is still embedded using its authorized private Storage URL, and the new-tab fallback remains.
- Page number typing is separate from navigation: users can type, for example, **27** without the first **2** triggering a partial navigation. Enter/blur commits and clamps within the paper's known page count; invalid or blank text retains the current page.
- Signed source URLs are requested with the existing one-hour expiry. The UI refreshes them after 50 minutes when the reader is reopened or pages are navigated, adds a manual **링크 갱신** action and retries a failed initial sign with **다시 연결**. In-flight signing is ignored after closing/switching papers or after another signing request.
- The new-tab link uses the displayed original page and avoids navigating with an already stale URL. When the token is stale, the first click renews it and the user can click again.
- Next.js prebuild now runs the existing `npm run lint` suite, including the PDF input/expiry helper tests; no additional production library was added.

## Automated checks

- TypeScript: `cd frontend && npm run lint`
- Production build (includes the prebuild suite): `cd frontend && npm run build`
- PDF helper cases: bounded pages, invalid/missing count, signed-URL fragment replacement, multi-digit page text and bad inputs, fifty-minute refresh threshold and invalid timestamp.

**Do not mark any manual scenario PASS without actually executing it.** A successful preview build proves only build/test success, not authenticated PDF or browser engine behavior.

## Manual smoke matrix — all currently PENDING

| Viewport/browser | Scenario | Status |
| --- | --- | --- |
| 360 × 740 Android Chrome | Open login without excessive hero scroll; sign in with verified test account | PENDING |
| 390 × 844 iPhone Safari | Google sign-in, OAuth redirect and private library visibility | PENDING |
| 375 × 812 Android Chrome | Open paper, PDF viewer, next/previous, input page 27 then Enter | PENDING |
| 390 × 844 iPhone Safari | Open citation in junior guide; verify original uploaded page; use new-tab fallback if native embed is unsupported | PENDING |
| 768 × 1024 tablet | Modal width, buttons, keyboard navigation, source PDF rendering | PENDING |
| 1440 × 900 desktop Chrome/Edge | Tab stays in dialog; Escape closes; focus returns to previously selected paper | PENDING |
| Safari/VoiceOver and Chrome screen reader | Dialog title, close name, page-number label and link announcements | PENDING |
| Any authenticated browser | Leave viewer open beyond 50 minutes, navigate; verify refreshed link and no PDF authorization error | PENDING |
| Any authenticated browser | Simulate sign URL error, click **다시 연결**, confirm recovery | PENDING |
| Any browser, two test users | Account B cannot see/open Account A's paper or signed PDF | PENDING |
| Any browser | Switch papers while PDF signing is slow: old PDF must never appear in the new paper | PENDING |
| Any browser | Restore viewport width 320 px and 200% text zoom; confirm controls remain usable | PENDING |

For each test, capture browser/version, viewport, result, console/network errors, and screenshots **without** signed URLs, cookies, JWTs, or private paper text.

## Next product increment

1. Complete live authenticated Chrome/Safari testing of this PR without disturbing production.
2. After priority 1 is verified, build the junior-oriented chart/table interpretation experience: what the axes/columns mean, reported significance and caveats; always distinguish extracted source facts from general explanations.
3. Follow with role-based learning paths, comprehension check, then beta release gates.

## Release and progress rules

- This is a stacked **Draft PR**, not merged to `main` and not promoted to production.
- Backend engine performance is intentionally unchanged.
- No new secrets or database schema are required.
- Overall feature-completion estimate remains **74.5% (~75%)** pending live checks. Q0/Q1/Q2/P0 = **0/4**; public beta readiness remains around 45%. These are planning estimates, not measured user outcomes.

## Build-cap verification blocker — 2026-11-17

- Vercel Preview for early markup commit `b7b95984` returned **READY**. This proves only that intermediate commit's Next.js build completed.
- An explicit Preview build request for the final branch failed with Vercel API **HTTP 402, `api-deployments-free-per-day`** (Hobby daily limit greater than 100). This is a deployment quota, not an application build failure.
- Later CSS, navigation/renewal, prebuild test enforcement, failure handling and docs commits therefore have **no confirmed fresh Vercel build**. The complete 43-test frontend suite has not been independently executed on the final branch in this session.
- After deployment quota availability is restored, run the branch's Preview production build (which invokes `prebuild` / `npm run lint`) and the manual scenarios above. Do not upgrade Vercel or change production deployment target merely to bypass a development-preview limit.
