# PaperSignal — persistent session bootstrap (AGENTS.md)

## At the start of every new PaperSignal development session
1. Read `docs/PROJECT_PROGRESS.json` for the **canonical weighted engineering percentage** and release-gate count.
2. Read `docs/PROJECT_STATE.md`, `docs/PROJECT_DECISIONS.md`, `docs/PROJECT_CHANGELOG.md` and `docs/RELEASE_CANDIDATE_GATES_2026-11-19.md`.
3. Recheck current GitHub Draft PR #18, head commit, CI, Vercel Preview, Railway API/Worker deployments and Supabase migration history before modifying or asserting live state.
4. Resume the next pending release gate. Do NOT restart financial-analysis engine tuning.

## Every project reply
- State the overall completion percentage **from `docs/PROJECT_PROGRESS.json`**, including that it is engineering completion, not a beta launch sign-off.
- State separately independently passed release gates out of total. Never describe synthetic browser tests or rollback SQL checks as a live authenticated E2E pass.
- After substantive work, update `docs/PROJECT_PROGRESS.json`, append status to `docs/PROJECT_STATE.md` and `docs/PROJECT_CHANGELOG.md`, and ensure CI executes `node scripts/check-project-progress.mjs`.
- Only increase progress with documented tests/results; if live evidence changes or docs are inaccessible, clearly state the last verified baseline.

## Safety and scope
- Canonical release candidate: Draft PR #18 against `main`, branch `release/beta-candidate-20261119`.
- The analysis engine is frozen; optimize product completion, junior learning and beta verification.
- Live E2E that provisions temporary users/PDF requires explicit manual approval and strict target checks; never run on automatic PR CI.
- Deploy and confirm server-owned analysis queue API **before** applying the database write-grant migration. Existing remote migration versions differ from historical GitHub baseline files; do not blanket `supabase db push`.
- Never expose service secrets, raise the GitHub Actions $1 budget, promote Production or change customer data without authorization.

## 2026-11-19 human-gated real E2E checkpoint

- Engineering progress source currently 88%, beta gates 4/10. Always load the latest JSON; no claim of real beta readiness.
- Additional narrow Draft PR #19 (`chore/manual-e2e-launcher-20261119`) targets main to register a **manual-only** E2E workflow without merging Draft PR #18. GitHub CI passed. The pinned E2E code is commit `431059a1116a50f39fd56d565c35a1afc081b8fc`.
- Human steps are in `docs/HUMAN_E2E_HANDOFF_2026-11-19.md`; never manually create Auth users, invoke Gemini or apply DB migration until explicit human permission and secure runner secrets are supplied.
