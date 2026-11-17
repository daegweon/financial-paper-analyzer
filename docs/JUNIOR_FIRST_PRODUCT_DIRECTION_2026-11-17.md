# PaperSignal — Junior-first product direction
Decision date: 2026-11-17

## Primary persona and value proposition

**Primary user:** A junior professional working in the financial sector who has limited formal finance/financial-engineering knowledge, but needs to learn quickly from papers, market research and evidence-based reports. Examples include early-career wealth management, product, risk, securities research support, and engineering-adjacent roles.

**Product promise:** “Read one finance paper, understand the unfamiliar ideas, know which conclusions are source-supported, and identify what to verify before using it at work.”

Not a generic AI summary factory, not a substitute for licensed investment advice, and not an automated trading-decision service.

### Core jobs to be done
1. **Comprehend:** What question is this paper asking, how was it studied, and what terms do I need to know?
2. **Verify:** Which findings can I trace to original PDF pages, which are only automated first-pass matches, and which still need review?
3. **Apply cautiously:** Does this research apply to my market, asset class, time period, and role? What could invalidate the inference?
4. **Communicate:** Convert what is established into a short, source-linked briefing for a manager or teammate, without implying stronger evidence than the paper provides.

## Design principles
- Default learning layer first; full original findings, methods and PDF remain one click below.
- Separate **paper-derived statements**, **general educational background**, and **hypothetical practical questions** visually and in wording.
- No model rewriting of numbers/signs/p-values for beginners. Preserve the original extraction and citations.
- Only auto-screen-passed findings with nonempty page/quote references may appear in the 3-minute overview; **screen pass is not human verification**.
- Missing methods, unsupported findings and absent original evidence are explicitly marked as missing/review-required; do not substitute general finance knowledge as paper facts.
- Prefer learner dignity: practical, concise, professional language rather than childish explanations.
- No recommendations to buy/sell specific securities; clarify uncertainty and applicability.
- Support role-tailored learning later, but keep a common evidence-first baseline for all employees.

## Product roadmap, ordered by junior learning impact

### P0 — Implemented as first staged UI feature (not production deployed)
**Junior 3-minute reading guide**:
- “What was this paper investigating?” = existing extracted research question and labeled AI summary.
- “What data and methods were used?” = existing extracted research design, sample, period and strategy.
- “Which results have traceable evidence?” = up to three automated screen-passed findings with page links, transparent “not independently verified” messaging and unresolved count.
- “Unfamiliar terms” = static Korean glossary cards triggered only when matching words are present in the analysis; each card includes an explanation and a question to check.
- “Could this be relevant to my job?” = three generic caveat questions about sample comparability, significance vs economic impact and correlation vs causation. These are **educational prompts**, not paper conclusions or trading advice.
- Optional limitations extracted from the paper stay labeled as such.
- Full technical report remains available below the guide.

**Source code:** `frontend/lib/junior-guide.ts`, `frontend/components/JuniorPaperGuide.tsx`, `frontend/components/JuniorPaperGuide.module.css`; integration in `frontend/app/page.tsx`; pure tests in `frontend/tests/junior-guide.test.mjs`.

**Verification:** isolated Vercel sandbox / Next.js 16.4.6: TypeScript, existing authentication + job-recovery tests, all 7 new guide tests, and production build pass. No live-user walkthrough or reviewed junior comprehension study completed. No merge into production.

### P1 — Prioritize next (not yet implemented)
- More useful **“Why is this model used?”** explanation for validated named methods, with assumptions, strengths and failure modes; every generated example must be marked synthetic.
- Role-aware “How would I use this at work?” prompts for WM, risk, research and product/technology teams, labeled as potential applications rather than paper-supported results.
- Three-stage progressive disclosure: first-pass 1-minute brief → 3-minute guide → full technical analysis/evidence.
- In-line paper evidence navigation (PDF page anchored citations, figures, tables) and clearer “unsupported / requires review” handling.
- Junior-friendly 1-page internal briefing with claim–evidence–limitation columns and no invented recommendations.

### P2 — Later, after accuracy gates
- Question-and-answer tutor over a paper with strict source citations and abstention.
- Role-specific quizzes on definitions, assumptions and interpretation, with validated answers.
- Learning history that tracks user-selected concepts, not private workplace data collection by default.

## Success metrics / evidence gates

1. **Understanding:** In moderated junior-user testing, measure the fraction who can accurately state the paper's question, method and one limitation before vs after using the guide (no invented improvement baseline).
2. **Grounding:** Zero newly approved unsupported numeric results or causal claims in the junior layer; no hidden high-risk “review_required” findings promoted as verified.
3. **Time-to-first-understanding:** Track time for a new user to locate the question, method and first linked source page.
4. **Transfer:** Have the junior correctly explain at least one **scope or applicability limitation** to a colleague without overstating the paper.
5. **Nonregression:** Existing Q0/Q1/Q2/P0 release gates remain independent and blocked; adding a guide does not raise these gates or justify deployment.

## Progress accounting

This decision changes **who the product is for**, not just the menu wording. Existing ~73% weighted engineering estimate stays unchanged until the new junior-specific workflow has real target-user testing. It does not prove any improvement in financial literacy or readiness for production.

No new QA Supabase key requested; the user explicitly deferred this credential. This feature uses the current stored v6.4.2 result schema and deterministic static teaching notes without changing any backend infrastructure.
