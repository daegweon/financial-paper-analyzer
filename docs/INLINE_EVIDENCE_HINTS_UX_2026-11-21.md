# PaperSignal — Inline source-evidence hints

> **Date:** 2026-11-21 (Asia/Seoul)  
> **Scope:** Follow-up to PR #38; frontend-only UI/UX refinement.

## Problem observed in the production screenshot

The first iteration changed each green quotation block into a collapsed disclosure, but retained a full-width bordered row for every citation. A report with many citations therefore still rendered a long sequence of empty rows. The interaction technically hid the quotation text but did not meaningfully reduce visual noise.

## UX decision

Treat source evidence as optional supporting context rather than a primary report block.

### Default report view

- Render one small, outlined **i** icon inline next to the claim, field, or section it supports.
- Group all citations supplied to one evidence list behind that single icon; do not render one row or icon per individual quote.
- Keep the report text and data cards visually unchanged.
- The icon is keyboard-focusable and has an accessible label that includes the number of available citations.

### Hover and focus preview

- On desktop, pointer hover or keyboard focus opens a compact tooltip near the icon.
- Preview the first citation's page number and a short excerpt; when more citations exist, show the remaining count and tell the user to click for the full list.
- Keep the preview open while the pointer is over either the icon or the tooltip.
- The tooltip is read-only and contains no links or buttons. Escape dismisses it; moving away or moving focus also closes it.

### Click / touch popover

- Clicking the icon (or pressing Enter/Space) opens a persistent, non-modal popover.
- The popover lists all citations in the group, each with its original page number, full excerpt, and a button/link to open the original PDF at that page when available.
- Close via the close control, Escape, or clicking outside. When closed using the close control or Escape, return focus to the icon.
- On touch devices, tapping the icon opens the popover; the interaction does not depend on hover.
- Long groups scroll inside the popover instead of expanding the report layout.

### Print / PDF

The interactive icon, tooltip, and popover are hidden in print. A compact print-only block outputs every citation and page number so report exports retain their source evidence.

## Design-system and accessibility review

This implementation follows established interaction guidance rather than inventing a hover-only widget:

1. **WAI-ARIA Authoring Practices — Tooltip Pattern:** tooltips appear on hover/focus, do not receive focus, and are dismissed with Escape; content with focusable controls should use a non-modal dialog/popover instead.  
   https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/
2. **W3C WCAG 2.2 — SC 1.4.13 Content on Hover or Focus:** supplemental hover/focus content must be dismissible, hoverable, and persistent.  
   https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html
3. **IBM Carbon — Toggletip:** click-triggered supplemental content can include interactive elements and remains open until deliberately dismissed.  
   https://www.carbondesignsystem.com/building-blocks/core/components/toggletip/guidelines
4. **IBM Carbon — Forms / Offering Help:** use a small outlined information icon for supplemental, non-essential guidance; avoid using tooltips as a catch-all for essential information.  
   https://www.carbondesignsystem.com/building-blocks/core/patterns/forms

The implementation uses the read-only tooltip pattern for hover/focus and the click-triggered popover pattern for the complete evidence list and PDF actions. This separation avoids putting interactive links inside a tooltip.

## Implementation

- Shared component: `frontend/components/EvidenceHint.tsx`.
- Main report: existing `EvidenceList` delegates to the shared component; evidence icons sit inline beside the supported content.
- Junior guide: direct finding quotations use the shared component.
- Visual-reading cards: source quotation and significance-legend quotation are grouped under one icon.
- Global styles: compact inline icon, viewport-aware floating tooltip/popover, responsive touch target, and print-only evidence block.
- No backend, database, authentication, storage, API, or analysis-engine changes.

## Regression coverage

Playwright coverage verifies:
- No full-width `details.evidence` rows remain.
- Hover preview shows the source excerpt and remains open while the pointer enters it.
- Escape dismisses hover/focus preview.
- Keyboard focus exposes the preview.
- Clicking opens the full multi-citation popover and exposes original-PDF page actions.
- Clicking outside closes the popover.
- Touch-sized viewport still supports tap-to-open.
- Junior-guide quotations use the same popover.
- Print mode includes the source quotes while hiding the interactive icon.

The CI result and Preview/Production deployment state are added here after validation.