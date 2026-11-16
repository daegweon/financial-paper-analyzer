# PaperSignal: exact-corpus open-source table evaluation

Date: 2026-11-16 (Asia/Seoul)
Decision: **Experimental integration retained; unrestricted production adoption NOT approved.**

## Completed work

Hardened the optional Camelot 1.0.9 adapter and ran the original B01–B10 PDFs twice in an isolated shadow benchmark. Each pass covered 10 PDFs / 209 pages / 30 control-and-parser executions. Original Storage ETags, byte sizes and page counts matched; all ten SHA-256 values and per-paper candidate counts matched between passes. No publisher substitute or synthetic PDF was represented as the real corpus.

The focused suite passed locally (43 passed, 4.47 seconds) and in the final Railway Docker build (43 passed, 2.99 seconds). Tests include actual synthetic-PDF extraction of model columns, negative coefficients, stars and standard errors; conflict retention; explicit parser errors; input/source validation; timeouts; credential stripping; and private artifact restrictions. The complete pre-existing production regression suite was NOT rerun.

## Final measured pass

Isolated Railway one-shot service; 1 vCPU / 1 GB; sequential per-document subprocesses; 90-second timeout per parser. Times include subprocess launch/import/output but exclude Storage transfers and Docker build. RSS is the child-process high-water mark, not total container or concurrent production memory. p95 is descriptive interpolation over ten PDFs, not an SLA.

| Extraction path | Completed | Median seconds/PDF | p95 seconds/PDF | Maximum child RSS (MiB) | Candidate tables |
|---|---:|---:|---:|---:|---:|
| PyMuPDF text control | 10/10 | 0.716144 | 0.868209 | 76.020 | Not applicable |
| Camelot lattice | 10/10 | 10.038897 | 13.409829 | 554.008 | 9 |
| Camelot stream | 10/10 | 2.748525 | 4.751715 | 268.543 | 263 |

All 30 executions completed without parser/process/timeout failures. Source and artifact errors were zero. All ten full result JSON objects were saved in the separate private papersignal-benchmark-artifacts bucket, confirmed by Storage metadata. The one-shot process finished; Railway reports zero running replicas and no pending work.

The first pass also completed all 30 extraction executions. Its medians were 0.716629 / 10.541135 / 2.949695 seconds for text / lattice / stream; maximum RSS was 76.293 / 554.141 / 268.926 MiB. Candidate counts matched the final pass. All ten first-pass artifact uploads failed with HTTP 400 and the process correctly exited nonzero. Bucket discovery was changed from a 404-only assumption to listing buckets, three regression tests were added, and the entire corpus was rerun. That persistence failure is NOT counted as an end-to-end success.

## Interpretation and decision

Lattice returned 2 candidates on B04 pages 14–15 and 7 on B07 pages 6, 7, 10, 13, 14, 15 and 16; it returned none for the other eight PDFs. This does not mean those PDFs contain no tables. Default all-page lattice demonstrated overhead but no established end-to-end quality benefit, so unconditional use is not approved.

Stream returned 263 candidates, with at least one on every one of the 209 pages. This is an over-detection warning, not evidence of 263 correct tables or 100% recall. No false-positive rate or true-table recall has been measured. Its lower observed resource use than lattice makes it a candidate for bounded, page-selected recovery experiments, not a production replacement.

The PyMuPDF control performs plain-text extraction only. These results do NOT establish that the complete production engine is 4x or 14x faster, nor that financial-fact precision improved. Candidate and control tasks differ. No model/provider calls occurred; monetary infrastructure cost and full-pipeline cost/latency remain unmeasured.

## Experimental correctness changes

Different coefficients, signs, stars, standard errors or model-cell layouts are no longer discarded merely because another candidate overlaps and has a better structural parser score. Default deduplication collapses only identical full cell matrices at overlapping geometry on the same page; benchmarks can retain every candidate.

Parser failures, invalid table geometry, missing dependencies and legitimate zero-table results are distinguished. Input and page selections are validated; empty page lists do not scan all pages. Temporary files are cleaned up, provider/Storage credentials are removed from parser subprocesses, and authenticated redirects are refused.

## Operational containment

Experimental code is on experiment/pdf-table-engines. The separate runner branch experiment/table-benchmark-runner has benchmark-specific railway.toml; NEVER merge that runner configuration into production. Only the new benchmark service is pinned to runner commit d1a4b4e33ef8e898058cb0ef21b151843f74ea5c.

API and Worker remained online on existing deployments; their configuration, production dependencies and frontend code were not modified. Existing PDFs, analyses and jobs were not overwritten. The original private PDF-only bucket still has 14 objects; jobs remain completed=102 and failed=28. The new private JSON-only artifact bucket has 10 objects and no authenticated/anonymous read policy. No public endpoint or cron was added. The temporary Vercel sandbox was stopped; the benchmark's running replica count is zero after completion.

## Remaining gates

Build a visually checked, independently reviewed exact-cell gold set associating variable, model column, coefficient/sign, standard error, stars/p-value/legend and source page; include prose/figure negative controls. Prioritize B01/B02/B09/B10 and the 18 previously review-required findings.

Then compare bounded page-selected recovery against the COMPLETE existing pipeline under declared quality/runtime/memory/failure/provider-cost budgets, and repeat on held-out papers. Stop variants that harm existing supported results or total service performance. Two extraction smoke passes do NOT satisfy the independent full-quality-benchmark gate. Docling and other shortlisted parsers were not run in this checkpoint.

No production promotion occurred. No overall engine accuracy gain or global performance maximum is claimed.

## Audit trail

- Implementation commit: b19e7a6d94162982058d14e996343571eeaa1c7e.
- Artifact fix: f4c61aecf31849306ce200eb2b9a5d827bc78a7e.
- First deployment/run: d26c718d-d41b-4780-9396-152f39ab9a9a / tables-0c49ca6f39de427d876d8131dcf043d6.
- Final deployment/run: 20becdfa-272f-448f-a347-68af3c8f33b3 / tables-1503f4d527fa419a9d48d0576c3f616d.
- Measured versions: Camelot 1.0.9, PyMuPDF 1.26.7, pdfminer.six 20260107, OpenCV headless 5.0.0.93, NumPy 2.5.5, pandas 3.1.1, pypdfium2 5.15.2.
- Sanitized measurements: table-shadow-metrics-2026-11-16.json; exact-source locks: ../table_corpus.sha256.json.
- Raw table/text candidates remain administrative-only Storage objects in the final run namespace, not Git files.
