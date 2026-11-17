# PaperSignal beta onboarding and recovery (2026-11-17)

This is a stacked draft feature above PR #14. The analysis engine, database, Worker, and production site are untouched.

Implemented:
- First-use, dismissible guide for PDF upload, evidence verification and junior learning; it has an upload CTA when the library is empty and an always-available reopen control.
- Guide-dismissal state lives in browser-local storage, scoped to an opaque authenticated user ID. No paper content, signed URL, session token, or quiz answer is stored.
- Keyboard-accessible PDF upload button instead of nonfocusable styled label; same-file re-selection is permitted.
- 30MB PDF extension/signature guard; error messages guide retry without displaying raw provider error strings or secrets.
- Failed paper metadata insert: best-effort object cleanup and explicit instruction to inspect library before manual upload, without automatic duplicate submission.
- Library loading/failure state with retry, stale-request invalidation, account-owner scoping for library and detail modal.
- Visible mobile sign-out, focus outlines, skip-to-content link, login status announcements and touch-friendly recovery controls.
- Six additional pure unit tests.

Manual QA still PENDING:
- Google/email login and real signed-PDF browser rendering on desktop Chrome, iOS Safari and Android Chrome.
- Retry behavior in simulated offline/403/metadata failure conditions; no duplicate paper creation.
- Two-account identity switching in one browser and private PDF isolation.
- Tab/Shift-Tab, 200% zoom, keyboard upload, screen-reader announcements and sign-out on 320px/390px screens.
- GitHub Actions runner startup_failure, custom SMTP email signup, controlled rollback drill.

Run the full Vercel Preview build (prebuild executes TypeScript plus 69 frontend tests). Do not label the product beta-ready until the live scenarios pass.
