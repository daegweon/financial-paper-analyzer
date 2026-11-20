# PaperSignal v6.3.9 — Ten-paper benchmark report

- Run date: 2026-11-16 (Asia/Seoul)
- Repository branch: `feat/research-workspace-mvp`
- Analysis version: `finance-structured-v6.3.9`
- Scope: existing B01–B10 paper records in the private Supabase workspace
- Run status: 10/10 durable analysis jobs completed; all latest paper analyses report v6.3.9
- Prior analyses were retained; new results were appended as new analysis records.

## Aggregate comparison

| Metric | Previous baseline (v6.1/v6.2 mix) | v6.3.9 | Change |
|---|---:|---:|---:|
| Papers | 10 | 10 | — |
| Extracted findings | 24 | 71 | +47 |
| Screen-passed findings | 15 | 53 | +38 |
| Review-required findings | 9 | 18 | +9 |
| Screen-passed share | 62.5% | 74.6% | +12.1 pp |
| Weighted lexical Gold-fact screen | 84.9% | 90.5% | +5.6 pp |

The Gold-fact metric is a lexical alias-presence screen over the structured analysis payload. It is not a human-verified precision/recall score, does not establish that each alias is used in the correct context, and is not a page-level citation accuracy metric. The previous baseline is a mixed v6.1/v6.2 snapshot, not a same-day randomized control.

## Per-paper results

| Paper | Findings | Screen-passed | Review | Gold-fact screen |
|---|---:|---:|---:|---:|
| B01 | 6 | 2 | 4 | 100.0% |
| B02 | 8 | 2 | 6 | 100.0% |
| B03 | 6 | 5 | 1 | 100.0% |
| B04 | 8 | 8 | 0 | 87.5% |
| B05 | 7 | 5 | 2 | 100.0% |
| B06 | 8 | 8 | 0 | 75.0% |
| B07 | 8 | 8 | 0 | 100.0% |
| B08 | 4 | 4 | 0 | 80.0% |
| B09 | 8 | 5 | 3 | 100.0% |
| B10 | 8 | 6 | 2 | 62.5% |

## Operational observations

- All 10 jobs in the benchmark batch completed.
- B02 required a retry after the Gemini primary model returned 503 and the fallback hit the Free Tier daily request quota (429); the retry later completed using the fallback model.
- B01, B02, B03, B05, B09 and B10 ran a targeted Findings repair pass.
- No paper ran the third table-first rescue pass in this batch.
- B04, B06, B07 and B08 completed without a Findings repair pass.
- The worker logs expose token usage for individual Gemini calls, but a complete, reliable per-paper cost/latency aggregation was not persisted for this batch. Cost improvement is therefore not claimed.

## Interpretation and release gate

Positive signals:
1. Findings volume and screen-passed count increased materially.
2. Screen-passed share improved from 62.5% to 74.6%.
3. The lexical Gold-fact screen increased from 84.9% to 90.5%.
4. The conditional repair strategy did not trigger a third rescue pass for any of these 10 papers.

Remaining risks:
1. 18 findings still require review; B01 and B02 are the largest review-heavy cases.
2. A screen pass is a rule-based evidence check, not a substitute for researcher review.
3. Page-level citation correctness, coefficient/significance fidelity, and critical-caveat compliance have not yet been independently human-scored across all 10 papers.
4. Cost and latency cannot be compared reliably from the persisted run data.

Decision: v6.3.9 is a promising benchmark candidate, not yet a fully quality-certified release. Do not claim cost savings or public-beta readiness from this benchmark alone. The next task is a targeted human audit of all review-required findings and material claims, beginning with B01, B02, B09 and B10.
