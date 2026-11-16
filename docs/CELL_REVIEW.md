# Exact-cell review and bounded Stream experiment

## Scope and non-goals

This is isolated on `experiment/pdf-table-engines`, not the production analysis path. It prepares source-first review packets and a fail-closed evaluator. It does not certify the 18 historical review-required findings, replace PyMuPDF, change a supported finding, call a model, or promote a build.

The first batch prioritizes B01, B02, B09 and B10 (15 of the 18 historical review-required findings). Numeric search hints come from historical machine-claim triage and are explicitly NOT answers. Parser outputs are never copied into approved gold.

Public publisher-page/PDF retrieval and screenshot attempts were rate-limited or failed. Do not describe these references as visually inspected exact-source gold. Instead, render the SHA-locked private original PDFs in the benchmark process and save the images privately for independent review. Generating a render is not the same as a person reviewing it.

## Reproducible experiment, fixed before execution

- Original corpus lock: `benchmark/table_corpus.sha256.json`.
- Prior private candidate run: `tables-1503f4d527fa419a9d48d0576c3f616d`.
- Page selector: standalone `Table <number>.` or `Table <number>:` caption lines, first eight matching pages. No expected answer or numeric search hint is used by the selector.
- Empty selection means no parser pages, never `all`. More than eight caption pages leaves an explicit omitted-by-cap list and an incomplete flag. Missing captions, continued tables and unsupported numbering can cause omissions; table recall remains unknown.
- Compare fresh all-page Stream with fresh page-selected Stream, two repeats with reversed order. Timeout: 30 seconds for each parser subprocess. One-shot benchmark service only, 1 vCPU / 1 GB. No public route, cron, or restart loop.
- Preserve individual cell geometry in top-left PDF points; preserve legacy table bounding boxes with their separate bottom-left coordinate-system tag.
- Compare full cell matrices on the selected pages, and the new all-page matrices against the prior private artifacts. Projection equality does NOT show that omitted pages contain no relevant table.
- Extraction timing excludes download, rendering and private upload. Child RSS is not total service memory. Four papers/two repeats are descriptive, not an SLA, a statistical speed guarantee, or full-pipeline improvement.

## Private source-first review packets

Each new JSON artifact contains the locked PDF identity, generated PNG source pages and image hashes, candidate cell geometry/matrices, page-selection omissions, candidate negative pages, machine search hints and an EMPTY annotation list. Source renders are capped at 12 pages per paper with explicit omissions. Negative candidates are not certified table-free pages.

Artifacts stay in the existing private JSON-only `papersignal-benchmark-artifacts` bucket under a new `cell-review-<uuid>` namespace. Existing artifacts/PDFs/analyses/jobs are not overwritten. No raw PDF, image, table payload, owner identifier, key or signed URL is committed or logged. Parser subprocesses receive an allowlisted environment without provider/Storage credentials. Credentials remain server-side Railway references.

Export a securely downloaded packet to a local offline view:

```sh
python -m benchmark.cell_review /private/B01.json --html /private/B01-review.html
```

Original source images appear before parser candidates, which are collapsed by default to reduce anchoring bias. Do not host these private HTML files publicly. Image and source hashes are checked before display. Candidate strings are HTML-escaped.

## Gold annotation contract

A target labels `id`, `source_sha256`, 1-based `page`, `variable`, `model`, `statistic`, and `coordinate_system="pdf_points_top_left"`. `anchors.row`, `anchors.column`, and `anchors.value` each contain an exact source `bbox=[x0,y0,x1,y1]` and `text`. Row/column anchors must resolve to distinct cells aligned with the value in one candidate table. A transposed table uses the actual visual row and column; variable/model semantics are explicitly reviewed metadata, not inferred from a numeric match.

Optional `companions` carry a `kind`, source box, exact text, and the reviewed row offset from the value (same column). Use this for standard errors, standard deviations and t-statistics without conflating them. Preserve parentheses, numeric precision, signs and significance stars. A printed p-value of `0.00` is retained literally; it does not authorize a fabricated threshold or an exact mathematical zero. Missing significance legends remain a review issue, not a licence to invent one.

Approved targets require `review_status="independently_reviewed"`, `review_origin="human"`, `source_render_checked=true`, and two different nonempty reviewer IDs. These fields must reflect actual independent work. The assistant must not manufacture human approval. Software validates the record format; it cannot prove reviewers' identities or that they truly inspected a PDF.

Call `evaluate(targets, candidate_tables, source_sha256, negative_pages=...)`. A reviewed negative control has `kind="no_table_page"`, source hash/page, and the same independent-review fields. The negative-page hit rate is a raw table-detection diagnostic, not a downstream false-approval rate.

No targets, partial review, changed source hashes or missing negative reviews return unavailable metrics, not artificial 100% scores. Multiple conflicting candidates cannot be adjudicated using Camelot's structural score. `promotion_eligible` is always false: full-pipeline non-regression, complete benchmark coverage, held-out papers, and validated total-service cost/resource budgets are separate gates.

## Tests and execution

Local focused tests cover incorrect signs/stars/precision/merged cells; correct numbers in incorrect rows/columns; mismatched companion statistics; conflicting/duplicate tables; wrong source/page; unreviewed/partial/empty gold; invalid geometry; annotation leakage; negative controls; caption-only page selection; and escaped offline rendering. The isolated `Dockerfile.cell-review` also runs the complete existing backend pytest suite before executing the benchmark. This does not include frontend builds or live E2E unless their own gates run.

The execution-only runner branch must override `railway.toml` to this Dockerfile and `python -m benchmark.cell_review_run`. NEVER merge this runner configuration into production. After completion, verify no running benchmark replicas and preserve the checkpoint in Git.
