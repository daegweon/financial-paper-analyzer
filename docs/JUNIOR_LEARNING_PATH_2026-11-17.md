# PaperSignal — Junior role learning path and comprehension check (2026-11-17)

## What changed
- Continues Draft PR #13 without merging or promoting to production.
- Adds a guided four-step path for each of the existing five role selectors (WM, Risk, Research, Product, Tech/Data): research question, methodology, evidence, workplace application.
- The question/method/evidence stages show saved source text only when available and expose the **exact existing citation page** if a valid quoted citation is present. No missing page or number is invented.
- A four-question knowledge check assesses safe interpretation: evidence quality, significance, role-specific application, and source-page verification. The role-specific content is static educational guidance. It is **not an AI-generated assessment** of paper comprehension or a professional certification.
- Show answer explanations and score after all questions are selected. Users self-attest each stage; completion checkboxes are not proof of mastery.
- Browser-only persistence: scoped to opaque Supabase user ID + paper ID + role; stores only completed stage IDs and best quiz score. Does NOT store private PDF URLs, tokens, text, names, original excerpts, or raw quiz responses.
- Accessible fieldsets/radio controls, focus-visible, touch targets, progress indicators, narrow mobile layout, storage-error fallback and reset action.
- Replaces the previously ungraded 3-question static self-check; reuses the existing role selector, avoiding duplicate role controls.
- No changes to Gemini/LLM prompts, analyzer, PDF extraction, database, backend worker, or auth policy.

## Acceptance / testing
- Run TypeScript and all existing frontend tests plus the new learning-path unit tests; Next.js production Preview build must pass.
- Manual authenticated QA: sign in/out, switch two users on one browser, switch papers and roles, reload, clear progress, test Safari private mode/storage-denied, keyboard and screen reader, Chrome/Android/iPhone layouts. Do not mark PASS without executing.
- Ensure no private paper text or credentials in localStorage or browser console. Progress saved on one device is not synced.
- **Priority #1 remains blocked on authenticated browser smoke tests** for Google sign-in, uploaded original PDF rendering, evidence click-through, signed link renewal, and two-user isolation; this implementation does not claim those tests passed.

## Release safety
- Keep stacked Draft PR. Production main, Railway, Supabase and v6.4.2 analysis engine remain unchanged.
- Beta release gates Q0/Q1/Q2/P0 stay unverified until actual browser and user acceptance tests pass.

## Next
1. Complete real authenticated browser/device tests with a reviewed Preview.
2. Validate study paths with B01–B10 (especially missing findings and citation pages).
3. User onboarding, error recovery, accessibility audit, deployment and rollback beta checklist.
