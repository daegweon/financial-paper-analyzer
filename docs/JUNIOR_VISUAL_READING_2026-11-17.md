# PaperSignal — Junior visual-reading milestone (2026-11-17)

## Product focus
Engine frozen. This increment teaches junior finance users how to read original tables and figures while using the existing evidence-linked PDF viewer.

- Show cards only when an existing finding has an explicit table/figure reference.
- Separate extracted claim/estimate/significance/column and source excerpt from general learning tips.
- Reuse cited original PDF page when available. Never infer missing citation pages, chart axes, units or unreported numbers.
- "Automatic first-pass screen" never means independent expert verification.
- Built with native details, accessible summary, clear focus styles and 44px touch controls; no schema, prompts, extraction or API changes.
- No actual bitmap chart/figure extraction is added in this increment; PDF still shows the exact uploaded source.
- Stacked on Draft PR #12, not merged to production.

## Verify
- Existing frontend 43 tests plus 8 new visual-reading unit tests, TypeScript and optimized production build via Checks workflow.
- Browser QA remains PENDING for actual Google login, original PDF citation click-through, Safari/Android rendering, screen readers, expiry renewal, and cross-user isolation.
- Reference manual matrix: docs/MOBILE_SOURCE_UX_QA_2026-11-17.md.
- Manual test on B01–B10 should confirm identified refs and quotes visually correspond to real tables/figures; do not mark PASS without executing.

## Next
Complete authenticated browser/mobile smoke after Preview deployment quota allows it; implement learning routes and short comprehension questions afterwards.
