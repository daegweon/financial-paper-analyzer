# PaperSignal — Open-source adoption decision (CLOSED)

Date: 2026-11-16 (Asia/Seoul)
Decision owner: project development
Scope: PDF/table parser OSS discovery and Camelot extraction experiments only. This is **not** a certification of the complete financial analysis engine.

## Decision

**Adopt zero new OSS dependencies into the production analysis engine. Stop parser-library exploration and return to core PaperSignal quality/reliability priorities.**

Retain PyMuPDF as the existing baseline and keep the Camelot adapter, source snapshots, visual drafts and test harness **in the isolated experimental branch only**. Do not promote unrestricted Camelot or the page-selected Camelot variant. Docling, MinerU, Unstructured and Science Parse are closed as unevaluated candidates, not described as tested failures.

An OSS component may be reconsidered only if an existing, user-relevant regression demonstrates a **verified whole-service** quality gain without a loss of supported findings, correct source-page alignment, error rate, latency, memory or sustainable provider/infrastructure costs. Mere extraction speed, parser self-reported accuracy and candidate counts are insufficient. No more speculative library trials.

## Before/after evidence on the identical PDFs

- Original B01/B02/B09/B10 (86 pages total), SHA/ETag/size/page-count locked; 23 caption-selected pages.
- Camelot Stream on **all** pages vs on **selected** pages, two passes with order reversed per PDF: 16/16 subprocess executions completed.
- Sum of measured extraction subprocess wall times across eight runs per configuration: **20.565219 s before -> 9.869005 s after**, **52.01% lower**, excluding Storage, page selection, image rendering, artifact writing, AI model and end-to-end service cost.
- Maximum observed child-process RSS **219.316 -> 173.758 MiB**, not concurrent service memory.
- Selected-page outputs projected onto the original all-page candidates: 8/8 matching matrices. This only confirms *matching outputs for selected pages*, NOT complete or correct source recovery.
- In the exact-source assistant visual-draft audit, **B01 PDF p18 / Table 2** was missed by **both** configurations in both saved repeats: five primary targets / 15 numeric cells, **20 missing comparisons** in four frozen variants. The same page returned a different Table 4 candidate. This is a within-page omission, not a selection-cap problem.
- B10 PDF p12 / Table 5 had 10 primary targets agreeing across four frozen variants (**40 agreements**); sample is purposive, not general precision/recall.
- **0** independent human-reviewed cells; **18** historical review-required findings remain uncertified. No source-cell accuracy gain, complete-pipeline quality non-regression, full-pipeline cost/latency gain, or held-out improvement has been demonstrated.

## Candidate disposition

| Candidate | Measured evidence | Final treatment |
|---|---|---|
| Camelot lattice all-page | 10 PDFs successful; median extraction 10.039 s, max child RSS 554 MiB, 9 candidate tables; no cell accuracy certification | **Reject production adoption** |
| Camelot stream all-page | 10 PDFs successful; median extraction 2.749 s, max child RSS 269 MiB; 263 candidates over 209 pages; 100% page detection is an over-detection warning, not precision | **Reject production adoption** |
| Camelot stream selected-pages | Four-PDF extraction savings as above, but B01 Table 2 shared omission and no overall proof | **Preserve experiment, not production** |
| Docling / MinerU / Unstructured / Science Parse | Not run against exact corpus | **Stop evaluation; do not claim superiority/inferiority** |
| PyMuPDF | Existing production dependency; legacy source-level text control and safeguards | **Retain, focus on core code improvements using current stack** |

**Important comparability limit:** PyMuPDF text-only control, Camelot table extraction and complete model-backed financial analysis do *different work*. Never describe extraction-time ratios as full engine speedup or infer document-level factual accuracy.

## Production and data safeguards

- No new OSS package imports, routes, UI, environment variables, schema changes, analysis algorithm changes or provider calls in the production API/Worker.
- No merge of the experiment branch or execution-only runner's root railway.toml.
- No automatic release from this decision. Existing paper, analysis, job and private source records remain untouched.
- Latest inspected API/Worker deployment commit: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` (Railway SUCCESS); inspected source's analysis-version constant reads `finance-structured-v6.4.2`. The `v6.3.9` ten-paper scorecard is historical and has **not** been rerun on this later production commit. Keep the two version labels distinct.
- The earlier benchmark's 90.5% lexical Gold-fact screen is an alias-presence heuristic, NOT independent source-cell accuracy.
- The existing independent human review, end-to-end quality, provider usage telemetry/quota, user E2E, SMTP and release checks remain outstanding.

## Next development direction (not an OSS hunt)

1. Resolve proven missing numeric/table evidence and the 18 review-required finding cases **using the existing stack**. Prioritize preserving page-level numeric evidence and rejecting false approvals.
2. Make model/provider token, attempts, time, and estimated cost observability durable, then evaluate overall quality/cost/latency together.
3. Establish a human-reviewed full-pipeline/held-out baseline on the actual currently deployed version before any future production promotion.
4. Continue public-beta reliability tasks (two-user isolation E2E, SMTP, sign-in, quota and release gates).

**Stop rule:** If no independently verified whole-engine quality improvement within the predeclared resource/latency budget is demonstrable, stop modifications and retain the previous production implementation. Do not continue variant tuning to raise a local extraction score.

## Evidence

- `benchmark/results/table-shadow-evaluation-2026-11-16.md`
- `benchmark/results/cell-review-preparation-2026-11-16.md`
- `benchmark/results/visual-draft-audit-2026-11-16.md`
- `benchmark/results/cell-review-metrics-2026-11-16.json`
- `benchmark/results/visual-draft-metrics-2026-11-16.json`
- `benchmark/visual_drafts_20261116.json`

Final state: **OSS assessment closed, no production adoption, no claimed global performance maximum**.
