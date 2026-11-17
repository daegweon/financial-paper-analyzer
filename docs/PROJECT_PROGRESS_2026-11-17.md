# PaperSignal development progress — 2026-11-17

## Current overall engineering estimate: ~75% (not a release certification)

This is an explicit, **subjective weighted engineering estimate**, anchored to the previous `docs/PROJECT_STATE.md` 72% estimate; it is not a velocity KPI, measured source accuracy, or percentage of release gates passed.

| Workstream | Weight | Estimated completion | Weighted points |
|---|---:|---:|---:|
| Research library, PDF upload, search, comparison, exports and primary UX | 25% | 94% | 23.50 |
| Authentication, private data/RLS, job persistence | 20% | 80% | 16.00 |
| Financial paper extraction, Gemini normalization and citation verification | 25% | 70% | 17.50 |
| Real-user workflow verification | 10% | 75% | 7.50 |
| Human-grounded quantitative quality/performance benchmark | 10% | 55% | 5.50 |
| Public beta release operations | 10% | 45% | 4.50 |
| **Total** | **100%** | **74.50%** | **74.50** |

Round to **~75%** for communication. The previous junior learning pack lifted the UX sub-estimate to 91%; this additional +0.75 percentage-point adjustment reflects the original PDF side-by-side viewer, page controls and source-citation navigation lifting UX to 94% at a 25% workstream weight. This is subjective engineering feature-completion accounting, **not measured financial comprehension, factual accuracy or release-readiness**. Cross-browser manual verification remains outstanding. Do not increase it further without new verified functionality or gates. The category estimates were inherited from the prior project state and may overstate release-readiness.

## Release gate status — independent from the above percentage

- **Q0 BLOCKED:** 12 exact PDF binaries (B01-B10 + H01-H02, 279 pages) and production v6.4.2 source are locked. The full same-version Gemini baseline remains unmeasured. The QA Supabase project was provisioned separately but its private key is currently unavailable; user asked to pause that track.
- **Q1 BLOCKED:** at least 50 independently judged material claims and the 18 historical review-required findings are not yet adjudicated by two independent human reviewers. Automated quote/screens are not human semantic evidence.
- **Q2 BLOCKED:** no paired full PDF upload → Gemini analysis → saved-result p95, billable cost, peak RSS or accuracy nonregression comparison. Local B07 extraction/prompt comparison is insufficient for Q2.
- **P0 BLOCKED:** live two-user end-to-end/auth/SMTP, comprehensive release smoke, rollback and capacity/cost checks pending.

**Gate completion: 0/4.** No claim that production launch is 75% approved. Public beta preparation was previously estimated at about **45%** and remains a separate, non-gated subjective estimate.

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

## Junior workplace learning pack — further verified development

- Stacked branch `feat/junior-role-guides-and-briefing` (base `feat/junior-first-paper-reading`), source: `docs/JUNIOR_WORKFLOW_PACK_2026-11-17.md`.
- Deterministic, general-finance methodology lessons: why, assumptions and limits for GARCH/GARCH-MIDAS, CAPM, Fama–French, VAR, LASSO, DiD, event studies, portfolio optimization, regression. Match only extracted methodology fields; no extra Gemini calls or new paper facts.
- Five role-specific junior study guides: WM, risk, research/strategy, products/planning and technology/data. Clearly separate potential use questions from evidence-backed paper claims.
- Source-grounded sharing brief: original title, DOI when known, original research question, sample/method/period, up to 2 automatically screen-passed findings with stored original page quote, limitations, role prompts, caveats. Excludes unverified findings, never claims human verification; preview, clipboard copy and offline plain-text download.
- Open-ended 3-question self-check, no invented answers or scores.
- Isolated Vercel sandbox: frontend `npm run lint` **PASS** including TypeScript and **38/38** tests (5 auth + 13 job recovery + 7 junior guide + 13 workplace pack), `npm run build` **PASS** (Next.js 16.4.6). No browser click-through/live login or independent junior-user comprehension tests.
- Core UX engineering estimate raised 87%→91%, weighted total **72.75%→73.75% (~74%)**. Keep Q0/Q1/Q2/P0 **0/4** and public beta readiness around 45%.

## Original PDF side-by-side reading — next product milestone

- New stacked branch `feat/junior-inline-pdf-learning`, Draft PR #11 (base is Draft PR #10). Feature source/report: `docs/INLINE_PDF_SOURCE_READING_2026-11-17.md`.
- Embedded viewer displays the exact uploaded original PDF through browser native PDF rendering in the existing detail modal. Previous/next and bounded page selector use stored page_count; new-tab fallback remains.
- Citation links in the junior guide and all 17 detailed-report evidence-list sites now open the same inline PDF at the cited page. Table/figure references jump to the first valid evidence page when present.
- Uses existing user-authorized one-hour private Storage signed URL; no backend, schema, bucket, secrets, model calls or engine changes.
- Isolated Vercel sandbox: TypeScript + **41/41 tests passed** (5 auth + 13 durable job + 7 junior guide + 13 role/workflow + 3 PDF page-navigation); Next.js 16.4.6 production build passed.
- Manual authenticated browser smoke across Chrome/Edge/Safari not yet completed. PDF extraction of separate images/table objects and OCR remain unimplemented; do not claim them.
- Core UX estimate 91%→94%, total weighted engineering estimate **73.75%→74.50% (~75%)**. Release gates Q0/Q1/Q2/P0 remain **0/4**; beta readiness still around 45%.
