# PaperSignal — Original PDF side-by-side reading (2026-11-17)

## Product objective

Help finance-sector juniors validate a paper-derived claim against the exact uploaded source PDF without switching tabs or relying on a reconstructed HTML rendering.

## Implemented

- Added a collapsible **original PDF viewer** inside the authenticated paper detail modal. It uses the existing short-lived Supabase signed URL and an HTML `iframe` to display the uploaded PDF bytes through the browser's native PDF viewer.
- Added previous/next page controls and a bounded numeric page selector using the paper's stored page count. If the page count is missing, positive page navigation remains available; nonpositive pages are clamped to page 1.
- Added a new-tab fallback for browsers that cannot render embedded PDFs.
- Junior 3-minute guide finding citations now offer **원문 p.N 화면에서 함께 보기**, opening the inline PDF at that exact page.
- All 17 evidence-list call sites across the detailed report (bibliographic information, research question, hypotheses/contributions, methodology, panel checks, variables, findings, significance legend, robustness, limitations, implications and evidence list) now route to the same inline original PDF viewer.
- Extracted table/figure references in findings are clickable when a page-level evidence citation exists, jumping to the associated original page.
- Existing report content and extracted PDF evidence remain unchanged; no HTML reconstruction of PDF pages.

## Security and scope

- Uses the currently authenticated user's already authorized private Storage signed URL (one-hour lifetime as before). No new public bucket, service key, database schema, backend endpoint or provider call.
- Signed URLs are not stored in localStorage or persisted.
- The PDF is loaded only when the user opens the viewer; the modal provides a new-tab fallback.
- No PyMuPDF/Gemini/worker/backend modifications. Analysis engine remains frozen.
- Viewer is an original PDF page navigator; it does not yet extract embedded images/tables as separately editable objects or add OCR.

## Tests

- Added `frontend/lib/pdf-viewer.ts` and `frontend/tests/pdf-viewer.test.mjs`.
- Covers page lower/upper bounds, missing/invalid page count, query-preserving signed URL fragments and stale fragment replacement.
- Isolated Vercel sandbox: `npm run lint` passed TypeScript and **41/41 tests** (OAuth 5 + durable job 13 + junior reading 7 + workplace guide 13 + PDF navigation 3).
- `NEXT_TELEMETRY_DISABLED=1 npm run build` passed (Next.js 16.4.6 optimized production build).
- No real authenticated browser click-through was performed; browser-native PDF behavior should be smoke-tested in Chrome/Edge and Safari before release.

## Progress accounting

Previous weighted engineering estimate 73.75%. Core UX estimate 91% → 94% (25% workstream weight), adding +0.75 percentage points. New weighted total **74.50% (~75%)**. This is a subjective engineering feature-completion estimate; actual junior comprehension and cross-browser rendering are not yet validated.

Q0/Q1/Q2/P0 release gates remain **0/4 passed**; public beta readiness remains separate and around 45%. Draft PR #11 stacks on Draft PR #10. Do not merge/deploy to production until release gates and manual browser checks are satisfied.
