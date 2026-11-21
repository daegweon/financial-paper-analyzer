# PaperSignal — canonical project handoff

> **Purpose:** This is the canonical continuity document for future ChatGPT/Codex sessions. Read it first before changing code, infrastructure, configuration, or production.
>
> **Last verified:** 2026-11-21 (Asia/Seoul)  
> **Repository:** [daegweon/financial-paper-analyzer](https://github.com/daegweon/financial-paper-analyzer)  
> **Production URL:** https://financial-paper-analyzer.vercel.app  
> **Latest application release commit:** `c05a47a8dc0304ff74f860485912e7003271affd` (PR #38; evidence disclosure and library-first workspace).  
> The current `main` may advance further through documentation-only closeout commits. Connected Vercel/Railway services deploy on main updates, including documentation-only commits. Always fetch the current main SHA and latest deployment IDs before changing or rolling back anything.

This document supersedes earlier release-status snapshots for the *current state*. Older dated documents remain useful as historical evidence and detailed runbooks; do not interpret their old deployment/PR status as current.

## 1. Start here in a new session

1. Read this document completely.
2. Read the root [README](../README.md) for commands, runtime configuration, supported limits and engine overview.
3. Read the most relevant detailed runbook before performing a live test or deployment:
   - [Beta release runbook](BETA_RELEASE_RUNBOOK.md)
   - [Production E2E verification](production-e2e-verification.md)
   - [Manual live E2E launcher](PAPERSIGNAL_MANUAL_E2E_LAUNCHER_2026-11-19.md)
   - [Pre-deploy QA and rollback](PREDEPLOY_QA_AND_ROLLBACK_2026-11-20.md)
4. Check the live GitHub main SHA, latest Vercel Production deployment, and both Railway services before making assumptions. This document is a verified snapshot, not a substitute for a fresh status check.
5. **Do not repeat completed deployment or migration work.** PRs #35, #36 and #37 are merged; no open PRs remained at the last check. Vercel Production and Railway API/Worker all run the latest main deployment. The public recommendations API is present in the deployed backend.
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

## 3. Current production state — verified 2026-11-21

### GitHub

- Default branch: `main`
- Latest application release commit: `c05a47a8dc0304ff74f860485912e7003271affd` (PR #38).
- PRs #35 (final workspace UX), #36 (public PDF discovery/import), #37 (recommendations/citations/sorting/pagination), and #38 (evidence disclosure/library-first UX) are all squash-merged.
- PR #38 exact-head CI: [Checks run #44897801859](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44897801859) — backend 247 passed/1 skipped, frontend 82 unit tests, Playwright 9/9, disposable PostgreSQL contracts passed.
- PR #37 merge resolved the Preview 404: the Preview frontend called `/api/public-papers/recommendations` before the Railway Production API had the route. The merged backend and frontend now ship together.
- No open PRs remained after PR #38.
- Documentation-only commits can trigger Vercel and Railway deployments; avoid unnecessary direct-to-main documentation commits and verify all connected services after any such change.

### Vercel frontend

- Canonical domain: https://financial-paper-analyzer.vercel.app
- PR #38 application release deployment: `dpl_DAL2QkzSn3k1wAMAY2gBGon7G1wm`.
- State: `READY`; canonical alias `financial-paper-analyzer.vercel.app` is attached.
- Deployed application commit: `c05a47a8dc0304ff74f860485912e7003271affd`. A later documentation-only closeout commit may trigger another identical application deployment; fetch the live alias/deployment before further operations.

### Railway API and Worker

Both services use repository `daegweon/financial-paper-analyzer`, branch `main`, and were redeployed after PR #38 on application release commit `c05a47a8dc0304ff74f860485912e7003271affd`. A documentation-only closeout commit may trigger another redeploy; fetch live deployment IDs before operational actions.

| Service | Latest PR #38 release deployment | State | Replicas |
|---|---|---|---:|
| `papersignal-api` | `a85ec587-2bcd-4da5-ae2d-113050bff09f` | SUCCESS / Online | 1/1 |
| `papersignal-worker` | `eb406651-b7bf-43c9-befa-9c6450cd9465` | SUCCESS / Online | 1/1 |

- API health endpoint: `GET /health` returned HTTP 200 after deployment.
- Railway environment status showed both services online, zero crashed replicas and no current warning/critical issues.
- The API and Worker were redeployed automatically after PR #38 merged because both Railway services track `main`; both are Online 1/1.
- PR #38 is UI-only and does not change the API contract, database schema, or analysis engine. No migration was required.
- The deployed backend continues to include `GET /api/public-papers/recommendations` and the extended search/citation sorting API.

### Administrator

- The Google OAuth account that owns three papers is the designated administrator.
- Railway API variable `PAPERSIGNAL_ADMIN_USER_IDS` is configured with that account's Supabase Auth UUID.
- The UUID is intentionally not copied into Git or this handoff.
- The user manually confirmed that the administrator dashboard displays normally.
- Admin route: `/admin/ai-usage`.
- Administrator allowlisting is server-side; do not add administrator checks only in the frontend.
- Do not change the configured administrator account unless the user explicitly requests it.

### Deployment automation

- The one-time **PaperSignal 운영 배포 확인** automation for 2026-11-21 15:40 KST is **disabled**. The rollout it was meant to check has already been completed. Leave it disabled; do not run or re-enable it as a duplicate deployment.
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

**How to continue:** Read [Public research PDF discovery/import runbook](PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md) for endpoints, security boundaries, configuration and QA. Check whether PR #37 is merged and deployed before asserting that the enhancement is live. First-author sorting is performed over the currently loaded result set because OpenAlex's works list does not provide the nested first-author-name sort needed for a global server sort. OpenAlex optional server-only `OPENALEX_API_KEY` can be configured if keyless usage limits become a blocker. Do not confuse free-to-read Open Access with redistribution rights.

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

## 9C. Inline source-evidence hover / info popover — PR #41

The PR #38 collapsible UI still left a repeated full-width "원문 근거 보기" row under each claim, which users found visually noisy. PR #41 replaces those rows with one small inline `i` icon per claim/evidence group. Hovering the claim/explanation text itself (not just the icon) opens a lightweight, non-interactive quote preview that follows the pointer. Clicking the adjacent i opens a separate detailed popover with every citation and original-PDF page actions; outside click or ESC closes it. Touch opens the detailed popover by tapping i; keyboard focus opens the preview and Enter/Space opens details. Multiple citations for one claim are grouped into the same popover. Print/PDF output still includes all source quotations while hiding the on-screen icon. A follow-up code review removed a duplicate icon in the junior guide and added coverage for pointer-follow, hover persistence, keyboard behavior, outside-click dismissal, and one icon per junior claim.

**2026-11-22 user-requested readability follow-up:** the same PR adds an 8px gap between claim text and the evidence icon, a symbol-by-symbol equation explainer (prioritizing extracted paper variable definitions and marking unknown meanings instead of guessing), and larger report/junior-guide typography. The regression test covers the formula `L(C) = a*C^b + c`, `-E_P[log(pass_rate(C))] = α*C^-k`, ten symbols, the extracted definition for C, report body type size, and icon spacing.

**2026-11-22 follow-up after the user's next Preview review:** PR #41 now includes a dedicated 0.65em spacer between body claim text and its evidence icon; A−/A+/기본 reading controls with 80–140% scale and localStorage persistence; and an equation-symbol tokenizer that splits implicit multiplication aCb into a, C, b without collapsing case-distinct C/c. Equation variable definitions pass their original-PDF evidence through to the explainer. The browser regression checks 10 symbols, font scaling, persisted preference, and icon gap. The user's previous screenshot used an older Preview hostname; use only the exact-head Preview linked in the current PR after CI completes.

**How to continue:** Read [Inline source-evidence hover / info popover UX](INLINE_EVIDENCE_HOVER_POPOVER_2026-11-21.md). Verify the latest PR #41 head and Preview before merge. The Preview build and full CI must pass before Production merge. This is frontend-only; no backend, schema, or analysis-engine change.

## 10. Remaining work and explicit non-blockers

The initial product release is live; PR #41's current evidence/readability follow-up remains in Preview validation and is not yet deployed to Production. The 2026-11-22 follow-up requested by the user is prepared in detached commit objects and must not be pushed until the user's no-GitHub-Actions instruction changes. The following are follow-up quality/extension items, not reasons to reopen the completed release without a concrete need.

### Recommended lightweight post-release checks
1. User manually opens the canonical production URL and confirms the new persistent logout/header and full-width report feel correct on their actual devices.
2. Perform one real Google OAuth sign-in/sign-out on the canonical domain if not already repeated after the final UI deployment.
3. Open an existing paper, open the original PDF, follow a page-level evidence link, use report navigation, export the report, and return to the library.
4. If a new production Gemini E2E is needed, run the manual workflow with the exact current main SHA and verify cleanup.

### Known product limitations / future enhancements
- OCR for scanned/image-only PDFs is not implemented.
- Standalone extraction/rendering of PDF figures and tables as separate image assets is not implemented.
- Per-paper interactive model/algorithm simulators are not implemented.
- Native-device iOS Safari and Android Chrome testing has not been replaced by Playwright viewport tests; perform device testing if the user reports a device-specific issue.
- The B01–B10 human expert review is incomplete (six findings remained review-required in the latest mixed-version snapshot).
- README currently references `docs/analysis-v6.3.md`, but that file was not present in the repository when this handoff was prepared. Reconcile the stale link or add a real v6.3/v6.4.2 engine note in a separate documentation-only change; do not invent a missing document.

### Do not reopen without evidence
- Do not restart engine tuning for minor cosmetic changes.
- Do not add OCR, figure extraction or simulators to the initial release unless the user explicitly expands scope.
- Do not repeat the completed PR #35 merge or production deployment.
- Do not apply database migrations merely to "make sure"; inspect the exact migration ledger first.
- Do not re-enable the paused 15:40 deployment automation.

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

The next session should begin from the current production state at main commit `e71d468c445849a480fced28e8a77e84b4892d51`, not from old feature branches or pre-release snapshots.

Default next-session objective: **maintain the released product, fix reproducible production defects, and avoid unnecessary scope expansion.** If no concrete bug or user-requested feature exists, report that the project is released and wait for the next product task rather than manufacturing more development work.
