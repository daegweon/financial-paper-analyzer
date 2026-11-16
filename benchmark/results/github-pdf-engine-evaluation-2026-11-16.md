# External PDF/table engine evaluation — experiment plan

## Decision

Evaluate external document/table parsers as **shadow extractors**, not replacements for PyMuPDF or the current evidence verifier. Production remains unchanged until the candidate wins on the same PDF corpus and exact page-level gold evidence.

## Candidate shortlist

| Project | Best-fit role | Strengths | Main risks | Decision |
|---|---|---|---|---|
| [Docling](https://github.com/docling-project/docling) | Full-document layout and table structure | Reading order, table structure, formulas, OCR, local execution, structured JSON | Large model/dependency footprint; CPU/RAM/latency; layout conversion may alter source order | Evaluate on separate benchmark worker |
| [Camelot](https://github.com/camelot-dev/camelot) | Text-based financial regression tables | Lattice/stream/network/hybrid and optional Table Transformer ML; table parsing metrics; DataFrame output | Primarily text PDFs; parser metrics do not prove correct cell-to-column alignment; optional ML/OCR adds weight | First low-risk candidate; isolated adapter added |
| [MinerU](https://github.com/opendatalab/MinerU) | Complex/scanned PDF parsing | Layout, OCR, tables, formulas and structured block/page outputs | Heavy inference stack and GPU/CPU resource demand; deployment/cost complexity | Evaluate only after Docling/Camelot |
| [Unstructured](https://github.com/Unstructured-IO/unstructured) | General document partitioning/RAG ingestion | Broad formats and modular ingestion | General-purpose element extraction is not specialized regression-table cell alignment; OSS benchmark caveats | Lower priority for this use case |
| [Science Parse](https://github.com/allenai/science-parse) | Scholarly metadata/sections/references | Scientific paper structure and bibliography extraction | Older project; not designed for precise regression table extraction | Metadata-only fallback, not a core candidate |

## Integration added

- `backend/app/pdf_table_experiment.py`: optional Camelot adapter; captures page, bounding box, rows, flavor and parser quality metrics.
- `backend/requirements-tables-experiment.txt`: isolated optional dependency.
- `backend/tests/test_pdf_table_experiment.py`: tests graceful absence, page/row/metric preservation, and invalid input.
- No production import, dependency, route, database schema or analysis behavior changed.

## Benchmark protocol

Run every candidate in shadow mode on the exact B01–B10 PDF bytes and preserve PyMuPDF output as the control. For each table compare:
1. table detection recall against manually inventoried result tables;
2. exact variable-row and model-column alignment;
3. coefficient/sign/standard-error/star cell accuracy;
4. page and bounding-box locator accuracy;
5. false table/false cell rate;
6. extraction latency, peak memory, CPU/GPU requirement and dependency image size.

The evaluator must score the *same target cells*, not Markdown similarity. A candidate only wins if it improves table/cell recall and exact-cell accuracy without reducing citation/page accuracy or increasing false approvals. It must also fit the intended Railway deployment resource budget.

## Acceptance gates

- No candidate replaces the baseline parser in the production path during experimentation.
- The 10-paper human-reviewed table-cell gold set must be completed before claiming an accuracy improvement.
- Zero regressions in existing numeric, direction and significance tests.
- Overall benchmark metrics cannot regress; report per-paper worst-case changes, not only averages.
- Report p50/p95 latency, peak RSS, image size, parser failure rate, and estimated per-paper cost.
- A winning integration is introduced behind a feature flag, shadow-compared, then promoted only after a second full benchmark.

## Initial recommendation

Start with Camelot because it is purpose-built for PDF tables, has multiple complementary parsers, exposes table parsing metrics, and can be integrated as an optional dependency without changing production. Evaluate Docling in a separate worker for complex layouts. Do not add all candidate dependencies to the main API image.
