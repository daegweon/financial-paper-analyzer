# PaperSignal analysis engine v6.3

## Goal

v6.3 addresses a production quality gap: an analysis job can complete successfully while the structured empirical findings array remains empty. It separates operational completion from findings-extraction completeness and adds one conditional table-first recovery pass.

## New behavior

1. The first structured analysis remains evidence-first: every claim requires a verbatim, page-level citation.
2. The existing findings-only repair pass still runs when findings are empty, summary consistency requires review, or a finding has a numeric/significance review flag.
3. If findings are still empty and extracted pages contain multiple conservative empirical-result signals, a third table-first rescue pass runs.
4. The rescue pass expands result-page selection to at most 32 pages and prioritizes regression tables, coefficient tables, table panels, notes, results, discussion and conclusions.
5. The rescue pass returns only findings supported by a contiguous quote on the stated PDF page. It must not infer a result from a hypothesis, abstract paraphrase, or domain knowledge. An empty array remains valid when no supportable result can be found.
6. findings_coverage separates quality from job status:
   - supported: at least one finding passed page/numeric screening;
   - review_required: findings exist but need researcher review;
   - incomplete: page text contains empirical-result signals but no verified finding survived;
   - not_assessable: no conservative result signal was detected.
7. The result records findings_verification rescue_attempted, rescue_status, and rescue_model. The frontend shows extraction-coverage status and third-pass outcome.

## Routing signals

The routing heuristic looks for result-oriented phrases, coefficient/statistical language, and table markers. It decides whether an extra model call is justified. It does not create claims and is not an accuracy score.

## Cost and safety

- The third pass is conditional; it is not called for every paper.
- It runs only after the first findings repair leaves the result empty and page signals indicate likely empirical content.
- It uses the same provider, server-side credentials, structured findings schema and citation validator as earlier passes.
- It does not change existing analysis rows. Only new analyses are tagged v6.3.
- If rescue cannot verify findings, the job may complete but the analysis is explicitly marked incomplete with a warning. This is preferable to fabricating results.

## Validation

Focused tests cover empirical-result signal detection, theoretical-paper no-signal behavior, table-first prompt contents, third-pass recovery, and explicit incomplete status when rescue still returns no supported finding.

The latest Railway API and Worker BuildKit test stages each reported 78 passed, 1 skipped.

## Known limitations

- Page-signal detection is a routing heuristic, not semantic understanding.
- Table OCR and complex multi-column PDF layout reconstruction are not implemented.
- Current text extraction scans at most the first 50 pages.
- Empty findings can be correct for theory-only papers or papers whose empirical results cannot be reliably extracted from available text.
- supported means the claim passed deterministic page/numeric screening; it does not prove semantic interpretation or causal validity. Human review remains necessary for material financial conclusions.
