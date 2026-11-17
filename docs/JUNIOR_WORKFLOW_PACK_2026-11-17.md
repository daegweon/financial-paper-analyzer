# PaperSignal — Junior Workplace Learning Pack (2026-11-17)

## Status
**Implemented and tested on a non-production stacked branch.** This is not deployed to users or approved for public beta.

- Branch: `feat/junior-role-guides-and-briefing`
- Parent feature: `feat/junior-first-paper-reading` (Draft PR #9)
- Frozen production reference: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`
- Backend/PyMuPDF/Gemini model/schema/worker/storage/auth changed: **NO**

## Deliverables

### 1. “Why this method?” cards (educational)
`frontend/lib/junior-workflow.ts`, `frontend/components/JuniorWorkplaceGuide.tsx`

- Deterministically matches **explicit methodology fields only** (design/empirical_strategy/identification_strategy) to known educational explanations; never infers the paper used a method solely because it appeared in the abstract/summary.
- Coverage: GARCH-MIDAS, GARCH, CAPM, Fama–French factors, VAR/TVP-VAR, LASSO, Difference-in-Differences, event studies, portfolio optimization and generic regression.
- Every card separates **why it is used**, **assumptions to check**, and **interpretation caution**.
- Specific method cards suppress redundant generic matches (GARCH-MIDAS vs GARCH; DiD vs regression).
- No match → clear “no explanatory match,” never “this paper used no method.”

### 2. Job-role learning cards
Five choices: **WM/wealth management, risk management, research/investment strategy, product/planning, software/data**.

- Each role has a focus statement, 3 concrete learning questions and a suggested practice deliverable.
- These are **generic educational prompts**, not paper-supported empirical claims or investment recommendations.
- User-chosen role only affects the questions and briefing prompts; it never changes source findings.

### 3. Grounded one-page briefing draft
- A transparent plain-text sharing draft containing original paper title, optional DOI, extracted research question, method/sample/period, **up to two automatically screen-passed original findings**, their PDF page numbers and **exact stored citation quotes**, and limitations copied from the existing result.
- A separate section labels selected role prompts as educational context.
- Existing `review_required`/unverified claims and findings lacking a valid page quote are not promoted.
- No new numeric return forecasts or implied causal assertions are generated.
- User can preview, copy to clipboard or save a local `.txt` file. Local filename is safely sanitized; no server writes, uploads or new API secrets.
- “One page” is an intended **briefing format**, not a guaranteed printed physical page count; longer papers can exceed one page.

### 4. Comprehension self-check
Three self-assessment prompts guide junior users to restate the original research question, articulate one modelling assumption and find a source-backed claim (or explain what cannot yet be verified). **No fabricated automated grade**.

## Source integrity and privacy
- Original LLM result retained. Educational text is separate from paper-extracted material.
- A `screen_passed` automated check is **not** equivalent to independent human verification; the UI and briefing state this repeatedly.
- Quoted evidence keeps source text and line breaks from existing stored result; users are directed to open the original PDF page.
- Cautions include statistical vs economic significance, correlation vs causality and limits to extrapolating future returns.
- No new provider calls, private PDF upload, database mutation, storage, browser tracking or persistent profile is introduced.

## Verification (isolated Vercel sandbox)
- Node.js 24 / TypeScript 5.9.3 / Next.js 16.4.6.
- `npm run lint`: **PASS**, including TypeScript and all four test suites.
  - OAuth tests: **5 passed**
  - Durable analysis job tests: **13 passed**
  - Initial junior research guide tests: **7 passed**
  - New role/method/briefing tests: **13 passed**
  - **Total 38 passed / 0 failed / 0 skipped**
- `NEXT_TELEMETRY_DISABLED=1 npm run build`: **PASS** (static routes built).
- Tests cover exact original quote preservation, safe filename export, unsupported result suppression, no invented absent data, method detection, role independence, and fact vs generic-question separation.
- **Not completed:** real junior-user comprehension testing, browser click-through/print-export E2E, production multi-user RLS/E2E, human semantic source verification, paired full-pipeline cost/latency/RSS, external SMTP.

## Progress accounting
Previous weighted engineering estimate: **72.75% (~73%)**.
Core product and UX workstream (25% weight) engineering estimate **87% → 91%** based on three new tested user flows (method learning, 5-role application questions, source-grounded briefing/export), without altering other workstream estimates.

New weighted estimate:
`(91 × .25) + (80 × .20) + (70 × .25) + (75 × .10) + (55 × .10) + (45 × .10) = 73.75% ≈ 74%`.

This is **subjective feature-completion accounting**, not an independently measured learning outcome or approval to launch.

Release gate status: Q0/Q1/Q2/P0 all **BLOCKED (0/4)**. Public beta readiness estimate remains **~45%**.

## Next product improvements without new Supabase credentials
- Run real junior usability and source interpretation tasks with representative finance employees.
- Make PDF figures/tables/page citations easier to compare side by side with the explanation.
- Add role-specific reading examples that remain labeled **synthetic** and document assumptions.
- Continue source-support audits and snapshot UI tests without changing production analysis code.
- Resume full Gemini baseline, live two-account E2E and release gates only when isolated credentials become available and reviewer evidence is collected.
