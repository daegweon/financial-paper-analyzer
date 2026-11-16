# PaperSignal — Exact-cell review preparation and bounded Stream experiment

Date: 2026-11-16 (Asia/Seoul)
Decision: retain the bounded extraction candidate in the experimental branch; no production promotion.

## Implemented and executed

Added a fail-closed exact-cell evaluator, source-first private review packets, an offline HTML viewer, and a caption-selected Camelot Stream benchmark. The evaluator checks exact row/column/value relationships, signs, stars, companion statistics, page and source identity. Structural parser scores never resolve conflicting cells. Empty, partial, non-human or source-mismatched annotations do not produce a full accuracy score. Independent-review metadata is a record requirement, not authenticated proof that a person reviewed the source.

Local new-unit suite: 48 passed (latest repeat 0.07s). The isolated Railway image ran the full repository backend suite: 193 passed, 1 skipped, 6 deprecation warnings, 4.00s. The opt-in live E2E was not enabled; no frontend build or live user-flow test occurred. Warnings concerned PyMuPDF/SWIG and the Starlette/AnyIO deprecated alias. Production dependency files and engine code were not changed.

## Same-source execution results

Four original PDFs (B01/B02/B09/B10; 86 pages) were SHA-256/ETag/size/page-count checked. A standalone table-caption selector, fixed before execution and capped at eight pages per document, selected 23 pages. There were no cap-induced omissions in this batch, but missing-caption/continuation omissions remain possible. Selection does not use the historical numerical search hints.

Each document ran all-page Stream and selected-page Stream twice, reversing order in the second repeat. All 16 executions succeeded; source and artifact errors were zero. The following times are arithmetic means of two subprocess wall measurements per document.

| Paper | Selected / total pages | All-page Stream seconds | Selected-page Stream seconds | Observed reduction |
|---|---:|---:|---:|---:|
| B01 | 7 / 31 | 3.469 | 1.325 | 61.8% |
| B02 | 6 / 20 | 2.458 | 1.169 | 52.5% |
| B09 | 5 / 16 | 2.203 | 1.307 | 40.7% |
| B10 | 5 / 19 | 2.152 | 1.134 | 47.3% |

Across all eight trials per variant, summed wall time was 20.565219s versus 9.869005s (52.01% less). Maximum child RSS was 219.316 versus 173.758 MiB. Per pass, raw candidate counts were 107 versus 41; these are not true-table counts or false-positive rates.

All eight selected-page matrix comparisons matched. All four fresh all-page matrix projections also matched the prior private Stream artifacts. Projection equality uses complete cell text matrices and table boxes rounded to 0.001 PDF points; it is not a verified source-cell accuracy score and says nothing about omitted pages.

Timing includes process launch/import/extraction/serialization, but excludes Storage transfers, the page-selection scan, source rendering, artifact upload and the full AI analysis pipeline. Child RSS is not aggregate container/concurrent-service memory. Four papers and two repeats are descriptive, not a latency SLA or a general speed guarantee. The 1 vCPU / 1 GB cap is an experimental execution limit, not an approved production budget. No model calls occurred; monetary infrastructure cost was not measured.

## Review artifacts and unresolved gold

Four new private JSON packets contain 33 generated grayscale source-page renders, source/render hashes, actual cell geometry, candidate matrices, and eight candidate negative-control pages. Numerical hints were only used to locate review pages. All annotation lists remain EMPTY. Generated pages have NOT been visually reviewed and there are zero independently human-reviewed target cells. Exact-cell accuracy, table recall and negative-page hit rate remain unavailable. None of the historical 18 review-required findings has been certified by this work.

The packets are in the existing private JSON-only papersignal-benchmark-artifacts bucket under the new cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c namespace. Storage metadata confirmed four new objects, totaling 9,915,979 bytes. Total artifact objects increased from 10 to 14. No public link, authenticated/anonymous artifact policy or public endpoint was added. The offline viewer displays source images before the collapsed parser output. See docs/CELL_REVIEW.md for the annotation contract and private local rendering command.

## Containment and decision

The benchmark finished with zero running replicas and no pending work. API deployment 17c9134b-f49c-4358-a879-7ca77b55b936 and Worker deployment dc501061-d434-454a-bc7d-4658b991a2f1 stayed online and unchanged. Before/after database counts match: 14 papers, 103 analyses, 102 completed jobs and 28 failed historical jobs; original private PDF objects remain 14. Existing artifacts were preserved.

The bounded strategy is a promising extraction-cost candidate, not yet a quality-approved integration. Do not activate it, relax existing numeric validation, infer that excluded pages have no relevant tables, or call this a global performance maximum. Next: independently label/adjudicate source cells and negative controls, audit omissions and significance legends, then test the complete pipeline and held-out papers under declared quality/resource/cost budgets. Restore the all-page experimental comparison when testing omissions; production remains its existing path.

## Reproduction and audit

- Implementation: 2eb467bb4692c1e01ceff7f07e3f3862f0cfed07 on experiment/pdf-table-engines.
- Execution-only branch: experiment/table-cell-review-runner; pinned commit 8c87af25652957fdbf868ccd0732c6c6e632ece9. NEVER merge its railway.toml into production.
- Isolated deployment: 5155bbf1-6cfd-4e96-858a-7148886ce2fc.
- Run: cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c.
- Versions: Camelot 1.0.9, PyMuPDF 1.26.3 (production-pinned version; previous smoke used 1.26.7), pdfminer.six 20260107, OpenCV headless 5.0.0.93, NumPy 2.5.5, pandas 3.1.1, pypdfium2 5.15.2.
- Sanitized per-repeat measurements: cell-review-metrics-2026-11-16.json.
- Raw source renders/cells are private artifacts, not Git files or chat attachments.
