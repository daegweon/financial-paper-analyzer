# PaperSignal — canonical project handoff

> **Purpose:** This is the canonical continuity document for future ChatGPT/Codex sessions. Read it first before changing code, infrastructure, configuration, or production.
>
> **Last verified:** 2026-11-22 (Asia/Seoul)  
> **Repository:** [daegweon/financial-paper-analyzer](https://github.com/daegweon/financial-paper-analyzer)  
> **Production URL:** https://financial-paper-analyzer.vercel.app  
> **Latest application release:** Production is synced to the current `main` HEAD after the 2026-11-22 reader-scale correction; verify the live main SHA and Vercel deployment before operational changes.  
> Connected Vercel/Railway services deploy on main updates, including documentation-only commits. Always fetch the current main SHA and latest deployment IDs before changing or rolling back anything.

This document supersedes earlier release-status snapshots for the *current state*. Older dated documents remain useful as historical evidence and detailed runbooks; do not interpret their old deployment/PR status as current.

## 0. Latest release note — 2026-11-22

- Reader-size control semantics were corrected: **100% is the default label and renders at the former 90% visual size**. The effective CSS scale is `readingScale / 100 - 0.1`; controls range from 90% to 150% in 10-point steps. Existing localStorage values from the previous 80–140 scale are migrated by adding 10 and marking `papersignal-reading-scale-version=2`, preserving the user's previous visual size.
- The change was deployed to Production from the current release source and synchronized to `main`. GitHub Actions were not run; the Checks workflow is PR/workflow_dispatch-triggered, not push-triggered.
- The public financial-paper discovery/import feature is part of the released product. Its user flow, API routes, OpenAlex behavior, sorting/pagination, private PDF storage and SSRF/security boundaries are summarized in §9A and fully documented in [PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md](PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md).
- Production URL: https://financial-paper-analyzer.vercel.app.

## 1. Start here in a new session

1. Read this document completely.
2. Read the root [README](../README.md) for commands, runtime configuration, supported limits and engine overview.
3. Read the most relevant detailed runbook before performing a live test or deployment:
   - [Beta release runbook](BETA_RELEASE_RUNBOOK.md)
   - [Production E2E verification](production-e2e-verification.md)
   - [Manual live E2E launcher](PAPERSIGNAL_MANUAL_E2E_LAUNCHER_2026-11-19.md)
   - [Pre-deploy QA and rollback](PREDEPLOY_QA_AND_ROLLBACK_2026-11-20.md)
4. Check the live GitHub main SHA, latest Vercel Production deployment, and both Railway services before making assumptions. This document is a verified snapshot, not a substitute for a fresh status check.
5. **Do not repeat completed deployment or migration work.** PRs #35–#41 are included in the current Production source. Vercel Production and Railway API/Worker track `main`; verify their live deployments before operational changes. The public recommendations/search/import APIs are present in the deployed backend.
6. Keep the analysis engine at v6.4.2 unless a reproducible quality improvement is demonstrated without regressions. The user's preference is to prioritize product completion and operational reliability over repeated minor engine tuning.
7. Avoid asking the user to repeat facts already in this document. Make safe, reversible progress autonomously; ask only when a genuine user decision, credential, device action, or approval is required.

## 2. Product purpose and design principles

PaperSignal is an evidence-first financial research paper workspace for finance professionals, especially junior users who need to understand financial/econometric papers without already having deep specialist knowledge.

Core product promise:
- Upload a financial/economics/securities research PDF.
- Extract a structured explanation of the research question, design, sample, methods, empirical results, robustness, limitations and implications.
- Tie material claims to page-level quotations from the original PDF.
- Let the reader open the original PDF and jump to cited pages.
- Help junior users understand tables, graphs, methods and workplace implications.
- Keep each user's papers, analyses and private PDFs isolated.

Non-negotiable quality principles:
- Never invent a page citation or present an unsupported claim as directly evidenced.
- Keep model interpretation distinct from facts directly extracted from the paper.
- Preserve source conflicts and uncertainty rather than silently choosing a value.
- A completed analysis job does not mean every finding is factually correct or expert-approved.
- Do not reduce overall analysis quality to improve a narrow metric.
- Do not expose service-role keys, model API keys, or other server secrets in frontend code, browser storage, Git, logs, or this document.

## 3. Current production state — verified 2026-11-22

### GitHub

- Default branch: `main`.
- The production release source, including PR #41's evidence/readability work and the reader-scale correction, is synchronized to the current `main` HEAD.
- PRs #35, #36, #37, #38 and #41 are included in the production source. Verify current PR status from GitHub rather than relying on old branch snapshots.
- GitHub Actions were **not run** for the 2026-11-22 reader-scale correction. The `checks.yml` workflow is triggered by `pull_request` and `workflow_dispatch`, not by a push to `main`; the live E2E workflow is manual-only.
- Do not manually dispatch or rerun GitHub Actions unless the user explicitly asks.

### Vercel frontend

- Canonical domain: https://financial-paper-analyzer.vercel.app
- Production deployment is built from the current `main` release source and is assigned to the canonical alias.
- Always query the live Vercel project for the current deployment ID, state and aliases before a later rollback or deployment; do not reuse deployment IDs from historical sections.

### Railway API and Worker

- Both services are connected to repository `daegweon/financial-paper-analyzer`, branch `main`.
- A `main` update can automatically redeploy both services even when a change is frontend/documentation focused. Verify API and Worker state after each main update.
- Public paper discovery endpoints remain part of the backend: `GET /api/public-papers/recommendations`, `GET /api/public-papers/search`, and authenticated `POST /api/public-papers/download`.
- The reader-scale correction is frontend-only; no database migration or backend API change is required.

### Administrator

- The Google OAuth account that owns three papers is the designated administrator.
- Railway API variable `PAPERSIGNAL_ADMIN_USER_IDS` is configured with that account's Supabase Auth UUID.
- The UUID is intentionally not copied into Git or this handoff.
- The user manually confirmed that the administrator dashboard displays normally.
- Admin route: `/admin/ai-usage`.
- Administrator allowlisting is server-side; do not add administrator checks only in the frontend.
- Do not change the configured administrator account unless the user explicitly requests it.

### Deployment automation

- The one-time **PaperSignal 운영 배포 확인** automation for 2026-11-21 15:40 KST is **disabled**. Leave it disabled; do not run or re-enable it as a duplicate deployment.
- A separate daily **GitHub Actions 사용량 감시** automation exists. It is unrelated to application deployment.

## 4. Final UI/UX release (PR #35)

User-reported issues and shipped changes:

1. **Logout was only at the bottom of the sidebar.** Account actions and logout are now available in the persistent workspace header at all responsive breakpoints, including inside the paper reader and admin dashboard.
2. **Analysis appeared in a narrow 570px side panel.** The paper analysis now opens as a full-width report workspace.
3. **The report was difficult to scan.** Bibliographic details and executive summary lead the report, followed by a compact key-information overview.
4. **Side tabs hid other report content.** A sticky horizontal section index uses anchor navigation; every report section remains in one continuous document.
5. **Reader controls were hard to reach while scrolling.** Original PDF, export, back-to-library and logout controls remain accessible in the sticky paper-reader toolbar.

Additional preservation requirements:
- Keep the original PDF viewer; do not reconstruct the PDF as HTML.
- Preserve page-level evidence links and navigation from a finding to the original PDF page.
- Preserve keyboard focus management and Escape-to-close behavior.
- Keep mobile, tablet and desktop layouts responsive.
- Avoid returning to a tab interface that hides sections from the reader.

PR #35 CI evidence:
- Backend: 218 passed, 1 skipped.
- Frontend: lint/TypeScript and production build passed; 82 unit tests passed.
- Playwright: 6/6 passed.
- Responsive logout checked at 320, 390, 768, 1024 and 1440 pixel widths.
- Full-width analysis report checked at 320, 390, 768 and 1280 pixel widths.
- Section anchor navigation, original PDF display and logout from the report were tested.
- Disposable PostgreSQL migration/ownership contract job passed.

The new UI is already in Production. Do not create another UI PR for the same changes.

## 5. Product architecture and major features

### Runtime architecture

- Frontend: Next.js 16.4.6, React 19.2.1, TypeScript, hosted on Vercel.
- API: Python FastAPI + PyMuPDF, hosted on Railway.
- Worker: separate Railway process using `python -m app.worker`.
- Authentication, PostgreSQL persistence and private PDF storage: Supabase project in Seoul.
- Source of truth: this private GitHub repository.
- AI provider: Gemini by default; provider-neutral normalized result schema supports a future provider switch.
- Keep API keys and privileged credentials server-side in Railway environment variables.

### Core user workflow

1. User signs up/signs in with email or Google OAuth.
2. User uploads a PDF into their private library.
3. The original PDF remains private and can be opened in the reader.
4. User starts analysis; the API creates a durable analysis job and returns promptly.
5. The separate Worker claims the job and processes it with leases, heartbeat, retry, checkpoints and idempotent persistence.
6. The frontend polls job state and displays the structured report.
7. User navigates report sections, follows evidence to original PDF pages, and uses junior-learning guidance.
8. User can return to the library or sign out from the persistent account controls.

### Analysis report and junior learning

The structured report includes:
- Bibliographic metadata and executive summary.
- Research question, hypotheses and academic contributions.
- Research design, sample, period, data sources, variables, equations and identification strategy.
- Empirical findings, direction, estimates and statistical significance when explicitly reported.
- Robustness checks, limitations, finance/economic implications and keywords.
- Page-level evidence excerpts and verification metadata.

Junior-focused modules in the product include:
- Three-minute paper-reading guidance.
- Table/graph reading learning cards.
- Workplace/finance-use implications.
- Original-page links for supporting evidence.

### Current documented PDF limits

- Maximum upload size: 30 MiB.
- PDF page count: 1–300.
- Text analysis scans the first 50 pages.
- Image-only/scanned PDFs require OCR; OCR is not currently included.
- Do not imply OCR or full image extraction is supported.

## 6. Analysis engine and benchmark state

### Current engine

- Current deployed engine: **v6.4.2** (`finance-structured-v6.4.2`).
- Keep v6.4.2 as the baseline. Do not restart an open-ended engine optimization loop.
- Gemini primary model documented/configured: `gemini-3.5-flash-lite`.
- Gemini fallback model documented/configured: `gemini-3.6-flash`.
- Primary/fallback output budgets are documented in README.
- If the primary model is temporarily unavailable or truncated, the Worker can retry with the configured fallback model.
- Evidence quotes are checked against extracted text from the cited PDF page before persistence. This verifies quote/page matching, not semantic correctness.

### Evolution

The engine evolved through v6, v6.1, v6.2, v6.3 and v6.4.2. Important v6.2+ capabilities include:
- Research-design-aware classification: balanced/unbalanced panels, repeated cross-sections, time series, cross-sectional and portfolio optimization.
- Typed sample dimensions and source-level count reports.
- Preserve conflicting source counts instead of silently selecting one.
- Only calculate N×T for evidence-backed balanced panels.
- Table/model/column context and separately cited significance legends.
- Context-aware p-value, coefficient and significance checks.
- Conditional methodology/findings recovery passes.
- Explicit findings coverage states so job completion is not confused with extraction completeness.

These are screening/triage controls, not proofs of statistical validity or semantic entailment. Material findings still need expert review against the publisher PDF.

### B01–B10 benchmark

The ten-paper benchmark set covers factor pricing, consumption risk, factor models, regime switching, liquidity premia, FX/equity nonlinear cointegration, macro volatility, ESG, corporate finance/VOV, and portfolio optimization.

Latest benchmark README snapshot dated 2026-11-20:
- All ten B01–B10 PDFs had been uploaded and analyzed.
- Latest stored analysis records were mixed-version: B01/B02/B09 v6.4.0, B10 v6.4.2, B03–B08 v6.3.9.
- 63 stored findings: 57 screen-passed and 6 review-required.
- Historical v6.3.9 snapshot: 71 findings, 53 screen-passed and 18 review-required.
- The assistant's second-pass audit of the six current review records is recorded in `benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md`.
- These are not expert sign-off. Human review of critical facts, estimates, signs, significance, sample definitions and citations remains incomplete.

Before any future engine upgrade, export paired results from the same B01–B10 PDFs, run the evaluator and evidence diagnostics, compare per-paper/per-field regressions, and require human review of high-impact discrepancies. Do not treat alias coverage as factual accuracy.

## 7. Gemini production verification

The latest approved live workflow before PR #35 is:
- [GitHub Actions #44865742221](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44865742221)
- Source commit: `b6ce635ceafb3958ba119c44003dd4d15b029e1e`.
- Workflow conclusion: success; live test job passed (1 passed, 27 deselected).
- Preflight confirmed the target and server-owned API mode before creating fixtures.
- Two temporary QA accounts and a synthetic two-page PDF were used.
- The real Railway API/Worker analysis completed and the test verified user A's result and user B's inability to access user A's paper/job/analysis/private PDF.
- Scoped cleanup ran; a read-only query after the test found zero remaining QA users/paper/job/analysis rows.

Important model telemetry nuance from that run:
- Primary `gemini-3.5-flash-lite` returned HTTP 503 (temporary high demand).
- Fallback `gemini-3.6-flash` returned HTTP 200 and produced a successful response.
- The Worker completion log still labeled the job's model field with the configured primary model. Treat that as a telemetry-label mismatch; use per-attempt telemetry to identify the model actually responding.
- The live test ran on the immediately preceding production commit. PR #35 changes only UI/docs/frontend E2E and does not change the API/Worker/analysis behavior.

The manual workflow remains intentionally manual-only:
- Workflow: `.github/workflows/papersignal-live-e2e.yml`
- Branch: `main`
- Inputs required:
  - `target=papersignal-production`
  - `approve_mutations=true`
  - `approved_commit=<exact current main SHA>`
  - `acknowledgment=RUN_SYNTHETIC_LIVE_E2E`
- It creates only temporary QA users and one synthetic PDF, runs actual Gemini analysis, checks tenant isolation, and cleans up only its own fixtures after a terminal job.
- If rerunning after this handoff, use the exact then-current `main` SHA, not the previous `b6ce635...` SHA.
- Never run against customer papers or reusable customer accounts.

## 8. Administrator operations

- Admin page: https://financial-paper-analyzer.vercel.app/admin/ai-usage
- The Google OAuth account with three papers is the only configured administrator.
- The user has already confirmed that the dashboard renders correctly after sign-in.
- Admin API authorization is enforced server-side through `PAPERSIGNAL_ADMIN_USER_IDS`.
- Admin usage reporting and global monthly budget configuration are implemented.
- Do not reveal the Auth UUID or any server environment values in the repository.
- Do not assume Gemini billing mode. The cost reporting mode should remain unknown unless the actual Google AI Studio billing tier has been explicitly confirmed and configured. Do not infer free/paid from model names or usage telemetry.

## 9. Security and data boundaries

- Email/password and Google OAuth authentication are supported.
- User-owned papers, analyses and jobs are protected by row-level ownership controls.
- PDF Storage is private; original PDFs must not be made public.
- Backend verifies the user's JWT and performs owner-scoped reads/writes.
- Trusted queue mutations, usage-ledger writes and administrator settings are server-owned.
- The AI usage ledger is append-only: service role has SELECT/INSERT only.
- Administrator settings permit only the server operations needed for SELECT/INSERT/UPDATE.
- Browser roles do not have direct access to administrator accounting tables.
- No new database migration is needed for PR #35; it changes no database schema.
- The latest migration recorded in the repository/production sequence is `20261121032957_restrict_ai_usage_ledger_privileges.sql`.
- Never put service-role credentials or Gemini API keys in frontend environment variables, source control, logs, or this document.

## 9A. Public finance-paper search and URL import — post-release feature

Public-paper discovery/import was first shipped on [PR #36](https://github.com/daegweon/financial-paper-analyzer/pull/36). The follow-up enhancement was merged in [PR #37](https://github.com/daegweon/financial-paper-analyzer/pull/37) as production commit `96393bf434b150106389693bffd8e35da0a42fca`. Exact-head CI [run #44893776957](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44893776957) passed: backend 247 passed/1 skipped, frontend 82 unit tests, Playwright 9/9, and disposable PostgreSQL contracts. It adds no-query recommendations, OpenAlex citation counts, title/citation/first-author/year sorting, 100-record API batches with 10-record local pages, and immutable search-query snapshots for stable pagination after the input is edited or cleared.

**Production rollout (2026-11-21):** Vercel deployment `dpl_VwrZw98r6w46NqgQ8QmxX4eJd1hb` is READY and aliases `financial-paper-analyzer.vercel.app`; Railway API deployment `363d6432-a37a-455e-ab4d-f83d0b36f778` and Worker deployment `d81402e0-8aa8-4f0c-861c-a27000490157` are SUCCESS/Online 1/1 on the same commit. Both the frontend and backend now contain `/api/public-papers/recommendations`.

**Troubleshooting note:** the earlier PR Preview displayed `404 Not Found` because its new frontend called the recommendations route while the Railway Production API still ran the previous `main` commit, which did not yet define that route. Merging PR #37 and deploying the API resolved the version mismatch. If this symptom recurs, compare the frontend commit and Railway API commit before changing the UI.

**Current status:** PRs #36 and #37 are merged and the feature is live in Production. After login, open **나의 연구 라이브러리 → 공개 금융 논문 찾아보기**. Users can browse no-query recommendations across asset pricing/markets, portfolio/risk, ETFs/market microstructure, and macro/rates/FX; search OpenAlex by keyword; sort by relevance, citation count, title, first author or publication date; and import a public PDF URL or a result with a PDF link into their own private library. Direct device-file upload remains available.

**Implementation quick reference:** `GET /api/public-papers/recommendations`, `GET /api/public-papers/search`, and authenticated `POST /api/public-papers/download` are implemented in `backend/app/public_papers.py`; the UI and existing private upload flow are in `frontend/app/page.tsx`. Search fetches up to 100 records per API batch and renders 10 per local page. First-author sorting is local to the currently loaded result set. Imported PDFs are stored through the user's existing private Storage upload path; public search/download requires a user Bearer JWT. The download service validates HTTPS/public DNS destinations, blocks private/internal IPs and redirects, and enforces PDF signature, page-count and 30 MiB limits. Open Access does not imply redistribution rights.

Read [Public research PDF discovery/import runbook](PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md) for full endpoint schemas, provider behavior, security boundaries, configuration and QA. The feature currently uses OpenAlex; `OPENALEX_API_KEY` is optional and server-only.

## 9B. Analysis evidence disclosure and library-first workspace — PR #38

PR #38 is **merged and deployed**. It changes report evidence excerpts from always-visible green quote boxes into keyboard-accessible, initially collapsed disclosures; users open only the citations they want to inspect. The junior three-minute guide's direct quotes use the same disclosure. The existing table/graph learning cards were already collapsible and remain so. Print/PDF export opens previously closed evidence before printing and restores each user's original open/closed state afterward, so citations are not lost from exported reports.

The login landing page now shows the user's own workspace first (library, analysis jobs, stats, filters and comparison), followed by the collapsible getting-started guide, then public finance-paper discovery/import. The direct PDF upload button remains available in the library heading.

**Release status (2026-11-21):**
- Application merge commit: `c05a47a8dc0304ff74f860485912e7003271affd`.
- PR #38 exact-head CI: [#44897801859](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44897801859) — backend 247 passed/1 skipped, frontend 82 passed, Playwright 9/9 passed, disposable PostgreSQL contracts passed.
- Vercel Production: READY, deployment `dpl_DAL2QkzSn3k1wAMAY2gBGon7G1wm`.
- Railway API: SUCCESS / Online 1/1, deployment `a85ec587-2bcd-4da5-ae2d-113050bff09f`.
- Railway Worker: SUCCESS / Online 1/1, deployment `eb406651-b7bf-43c9-befa-9c6450cd9465`.
- Official domain: https://financial-paper-analyzer.vercel.app

**How to continue:** Read [Analysis evidence disclosure and library-first workspace](ANALYSIS_EVIDENCE_DISCLOSURE_AND_LIBRARY_FIRST_2026-11-21.md). The application feature is released; only address reproducible production issues or new user requests.

## 9C. Inline source-evidence hover / info popover — PR #41, merged and in Production

PR #41 is merged. The current Production UI uses one compact inline `i` icon per evidence-backed claim/group. Hovering the claim text opens a short, non-interactive source preview; clicking `i` opens the detailed citation popover with original-PDF page actions. The interaction supports pointer hover, keyboard focus/activation, Escape/outside-click dismissal and touch tap. Multiple citations for one claim share one icon. Print/PDF output retains source quotations while hiding screen-only controls.

**2026-11-22 final readability decisions now in Production:**
- The reader control displays **100% as its default**, while the actual rendered size equals the former 90% visual size. The effective scale is `readingScale / 100 - 0.1`; the label range is 90–150% in 10-point steps. Previous localStorage values are migrated by +10 with marker `papersignal-reading-scale-version=2`, preserving the prior visual size.
- Equation parameter/symbol explanation cards were removed at the user's request; the paper's formulas remain visible.
- The "논문 읽기 이해도 점검" title, questions, answer choices and feedback use larger typography.
- Duplicate variable evidence citations are consolidated under the parent "주요 변수" icon only when both PDF page and normalized quote match. Evidence unique to one variable remains beside that variable.
- Public finance-paper discovery/import remains available from the research library; see §9A and `PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md`.

**Current release source:** `main` commit `0c2e5b10c39eca1d6577fc36d9fcbe830dd653d2`; Vercel Production deployment `dpl_MShcWWKJSoXDLZLbtxMcZvhzvq6G` is READY on https://financial-paper-analyzer.vercel.app. PR #41 is merged; no Preview review or further merge is required for this feature.

**How to continue:** Treat this feature as released. Only reopen for a reproducible Production defect or a new explicit user request. No backend, database or analysis-engine change is part of the reader-scale correction.

## 10. Remaining work and explicit non-blockers — closeout 2026-11-22

The core PaperSignal product is released in Production. The repository housekeeping pass closed 15 obsolete/duplicate PRs (PR #39/#40 duplicates of merged #41; PR #2–#16 superseded/archived). Their branches and commit history were retained. There are no remaining open PRs or GitHub Issues after the closeout check. GitHub Actions were not run.

### Remaining external / human-owned items

These cannot be honestly marked complete by code changes alone:

1. **Finance expert review:** six findings across five claim units in the latest mixed-version B01–B10 snapshot remain `review`. The AI second-pass audit is not expert sign-off. See `benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md`.
2. **Public-paper live smoke:** CI mocks OpenAlex and publisher PDF servers. On Production, verify a small real OpenAlex search and a permitted public/CC-licensed PDF import through the private library flow.
3. **Native mobile QA:** test original-PDF rendering, zoom, rotation, signed-link renewal and session expiry on actual iOS Safari and Android Chrome devices. Playwright viewport tests are not native-device verification.
4. **External email delivery:** configure a custom SMTP provider and verified sender domain; test signup confirmation, resend and password reset in a real external mailbox. Supabase built-in SMTP is not suitable for an external beta.
5. **Auth security decision:** Supabase Security Advisor still warns that leaked-password protection is disabled. A project owner must decide/enable it in Auth settings; connected Supabase tools used in this closeout do not expose that Auth configuration mutation.
6. **Gemini billing mode:** confirm the actual Google AI Studio tier (Free or Paid Standard) before setting the server-side billing-mode configuration. Unknown mode must continue to produce unknown USD cost rather than an invented estimate.
7. **GitHub Actions billing:** account-level $0 budget / stop-usage protection could not be independently verified through the repository connector. Check GitHub account billing settings if Actions spend control is required.
8. **Production Google OAuth regression:** earlier Preview sign-in/return-to-library flow was confirmed; repeat sign-in/sign-out on the canonical Production domain after the final release.

### Confirmed current operational state

- GitHub `main`: `0c2e5b10c39eca1d6577fc36d9fcbe830dd653d2`.
- Vercel canonical Production: READY, `dpl_MShcWWKJSoXDLZLbtxMcZvhzvq6G`.
- Railway API and Worker: Online 1/1, zero current service issues at the last status check.
- Supabase migration ledger: 14 applied versions through `20261121032957`; no pending migration was identified.
- AI usage ledger and administrator monthly-budget reporting are implemented; cost estimates remain unknown when billing mode or token data is incomplete. This is reporting, not an invoice or automatic spend cap.
- Supabase Advisor: two INFO notices for intentionally service-role-only accounting tables with RLS enabled/no policies; one WARN for leaked-password protection disabled; one INFO for an unused index; no health notices.

### Intentionally deferred product enhancements (not release blockers)

- OCR for scanned/image-only PDFs.
- Standalone extraction/rendering of figures and tables as image assets.
- Per-paper interactive model/algorithm simulators.
- Additional public paper providers/DOI resolution beyond the current OpenAlex flow.
- Structured database provenance fields for imported-paper DOI, original URL and license.

### Do not reopen without evidence

- Do not restart analysis-engine tuning for minor cosmetic changes; keep the released engine frozen.
- Do not add deferred enhancements to the completed release unless the product scope is explicitly expanded.
- Do not apply database migrations merely to "make sure"; inspect the live migration ledger first.
- Do not run GitHub Actions unless the user explicitly requests it.
- Do not create unnecessary deployments or apply unnecessary database migrations.

## 11. Historical documentation to preserve

These existing files contain useful design rationale, prior decisions and test procedures. They are historical/detail references; this handoff is the current status source.

- [Analysis engine v6](analysis-v6.md)
- [Analysis engine v6.1](analysis-v6.1.md)
- [Analysis engine v6.2](analysis-v6.2.md)
- [Gemini live verification](gemini-live-verification.md)
- [Production E2E verification](production-e2e-verification.md)
- [Beta release runbook](BETA_RELEASE_RUNBOOK.md)
- [Manual live E2E launcher](PAPERSIGNAL_MANUAL_E2E_LAUNCHER_2026-11-19.md)
- [Pre-deploy QA and rollback](PREDEPLOY_QA_AND_ROLLBACK_2026-11-20.md)
- [Release closeout (2026-11-20)](RELEASE_CLOSEOUT_2026-11-20.md)
- [AI usage observability (2026-11-20)](AI_USAGE_OBSERVABILITY_2026-11-20.md)
- [Finance paper benchmark](../benchmark/README.md)

Some older documents describe a state before the final product integration and must not be treated as current. In particular, older notes that say the full PDF reader/junior learning UI is only in a draft PR have been superseded by PR #28 and the final PR #35 rollout.

## 12. Final continuation instruction

The next session should begin from the current Production state at the live `main` HEAD and latest Vercel/Railway deployments, not from old feature branches or pre-release snapshots.

Default next-session objective: **maintain the released product, fix reproducible production defects, and avoid unnecessary scope expansion.** If no concrete bug or user-requested feature exists, report that the project is released and wait for the next product task rather than manufacturing more development work.
