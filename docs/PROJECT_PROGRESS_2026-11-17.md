# PaperSignal development progress — 2026-11-17

## Current overall engineering estimate: ~73% (not a release certification)

This is an explicit, **subjective weighted engineering estimate**, anchored to the previous `docs/PROJECT_STATE.md` 72% estimate; it is not a velocity KPI, measured source accuracy, or percentage of release gates passed.

| Workstream | Weight | Estimated completion | Weighted points |
|---|---:|---:|---:|
| Research library, PDF upload, search, comparison, exports and primary UX | 25% | 87% | 21.75 |
| Authentication, private data/RLS, job persistence | 20% | 80% | 16.00 |
| Financial paper extraction, Gemini normalization and citation verification | 25% | 70% | 17.50 |
| Real-user workflow verification | 10% | 75% | 7.50 |
| Human-grounded quantitative quality/performance benchmark | 10% | 55% | 5.50 |
| Public beta release operations | 10% | 45% | 4.50 |
| **Total** | **100%** | **72.75%** | **72.75** |

Round to **~73%** for communication. The +0.5 percentage-point change reflects an estimated two-point increase in the core UX workstream from the new persistent-job recovery feature and passing regression/build tests. This is still a subjective engineering estimate, **not** a measured release-readiness improvement. Do not increase it further without new independently verified functionality or gates. The category estimates were inherited from the prior project state and may overstate release-readiness.

## Release gate status — independent from the above percentage

- **Q0 BLOCKED:** 12 exact PDF binaries (B01-B10 + H01-H02, 279 pages) and production v6.4.2 source are locked. The full same-version Gemini baseline remains unmeasured. The QA Supabase project was provisioned separately but its private key is currently unavailable; user asked to pause that track.
- **Q1 BLOCKED:** at least 50 independently judged material claims and the 18 historical review-required findings are not yet adjudicated by two independent human reviewers. Automated quote/screens are not human semantic evidence.
- **Q2 BLOCKED:** no paired full PDF upload → Gemini analysis → saved-result p95, billable cost, peak RSS or accuracy nonregression comparison. Local B07 extraction/prompt comparison is insufficient for Q2.
- **P0 BLOCKED:** live two-user end-to-end/auth/SMTP, comprehensive release smoke, rollback and capacity/cost checks pending.

**Gate completion: 0/4.** No claim that production launch is 73% approved. Public beta preparation was previously estimated at about **45%** and remains a separate, non-gated subjective estimate.

## Work completed in this iteration — isolated frontend reliability branch

Branch: `feat/research-job-status-resilience`, based on frozen production `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`.

- New `frontend/lib/analysis-job.ts` splits durable job enqueue and status polling. Retry temporary 408, 429, 500, 502, 503, 504 responses without automatically resending the initial POST and risking duplicate work.
- Cap consecutive transient failures (default 8) and honor bounded integer `Retry-After` values. If an existing durable job is still processing after the client polling deadline, advise reopening the paper instead of declaring a server-side failure.
- Replace raw `Failed to fetch` with an actionable Korean connection message; preserve failed-job details for the paper owner.
- `frontend/app/page.tsx` now guards against stale modal reopening if another paper was selected or the modal was closed before a job completed.
- `frontend/package.json` integrates `test:analysis` into `lint`.
- Test evidence in isolated Vercel sandbox (Node.js v24): **15/15 UI unit tests passed**, including **10 new job resilience tests** and **5 pre-existing auth/OAuth tests**; `npm run lint` including TypeScript **passed**; `npm run build` using Next.js 16.4.6 / TypeScript **passed**.
- No backend analysis prompt, schema, model, PDF extraction, Railway deployment or Supabase database/secret changes were made in this iteration. Candidate remains unmerged.

## Next main-project steps without new Supabase credentials

1. Review the frontend reliability changes in an isolated Draft PR; do not merge to the Railway-linked production branch before release gates.
2. Improve user-facing resumable/reconnect job state in the research library without losing previous analysis records.
3. Continue preparing human review evidence packs and regression scenarios using existing locked PDFs; do **not** present synthetic or self-reviewed samples as independent gold.
4. Return to full Gemini model baseline and isolated DB E2E only when safe credentials and environment are available. No repeated request for new Supabase secret unless the user resumes that track.

Previous operational facts: production API + Worker at `8cd5e37`; frontend authenticated Google OAuth confirmed previously; v6.3.9 regression diagnostic was 71 findings, 18 review-required and 53 screen-passed, which is a lexical/structural screen rather than an independent accuracy certification.

## Second iteration — recover durable jobs after refresh

- `frontend/app/page.tsx` now reads active `analysis_jobs` rows from the authenticated Supabase data API when a paper opens. If an active queued/processing job exists, the detail view offers **진행 중인 분석 이어 확인** and disables a second analysis POST.
- `frontend/components/ResearchLibrary.tsx` now displays **이어 확인** beside active papers and **진행 확인** in the recent jobs tab. This works after refreshing the browser because the source is the server's durable job row, not localStorage.
- `analyze()` re-checks the server for an active job immediately before enqueueing. If this read fails, it fails closed instead of guessing that no active job exists. The backend's unique active-job DB constraint remains authoritative against cross-tab races.
- The browser-only watcher now accepts `shouldContinue`; closing the detail view or switching papers stops stale polling without canceling the worker job. Delayed completion responses cannot reopen an unrelated paper.
- New pure `findActiveAnalysisJob` selection and `AnalysisWatchStopped` behavior have regression tests for newest queued/processing selection, close-during-poll, and stale completion after paper switch.
- Independent Vercel sandbox: `npm run lint` **passed** (TypeScript + 5 existing auth tests + 13 analysis-job tests = **18/18**), and `npm run build` **passed** (Next.js 16.4.6). No live multiuser E2E or runtime production telemetry was performed.
- No backend source, prompts, Gemini provider configuration, PostgreSQL migration, Railway production deployment or live Supabase user records changed.
- **Remaining:** scoped live E2E of reload, reconnect, duplicate analysis race and RLS. Q0/Q1/Q2/P0 all still BLOCKED. Draft PR #8 must not be merged to production while the agreed release gates remain blocked.
