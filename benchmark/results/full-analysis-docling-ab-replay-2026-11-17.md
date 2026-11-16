# PaperSignal — Full-analysis A/B attempt and ten-paper deterministic evidence replay

Recorded: 2026-11-17 (Asia/Seoul). **Production engine FROZEN; Docling Parse NOT promoted.**

## Executive decision

The requested side-by-side **new Gemini-backed full-pipeline analysis** was actually attempted with the exact same v6.4.2 downstream code (same schemas, prompts, validators and repair/rescue logic; prior_findings=[] in both arms) on original SHA-locked public papers. **It did not complete**: the PyMuPDF baseline arm on B01 and B03 failed before a paired candidate analysis due to Gemini HTTP 503 on **both** configured models. Never label this as a successful fresh full-model A/B or a completed comparison of model quality.

The failure is provider-/workload-facing: a tiny synthetic Gemini 3.5 Flash Lite probe returned HTTP 200, while Gemini 3.6 Flash probe timed out. It does not establish the root cause of the full-sized model failures; no credentials or source data were logged. The A/B runner halted on failure rather than synthesizing an extraction-only result or retrying uncontrolled.

To continue making measurable progress **without additional model calls**, revalidated the **same previously stored v6.3.9 structured findings and exact page quotes** against BOTH original-PyMuPDF and Docling Parse page text using current **v6.4.2 source validators**. This zero-provider replay finished on all ten original PDFs (209 pages) and found an important regression in citation and finding retention.

## Deterministic evidence replay — 10 identical original PDFs

| Paper | PyMuPDF quotes retained | Docling Parse quotes retained | Findings with direct evidence (before → after) | Findings screen-passed (before → after) |
|---|---:|---:|---:|---:|
| B01 | 31/31 | 25/31 | 6 → 6 | 2 → 2 |
| B02 | 48/48 | 32/48 | 8 → 4 | 2 → 1 |
| B03 | 33/33 | 27/33 | 6 → 6 | 5 → 5 |
| B04 | 29/29 | 24/29 | 8 → 8 | 8 → 8 |
| B05 | 37/37 | 35/37 | 7 → 7 | 5 → 5 |
| B06 | 27/27 | 24/27 | 8 → 8 | 8 → 8 |
| B07 | 43/43 | 41/43 | 8 → 8 | 8 → 8 |
| B08 | 39/39 | 37/39 | 4 → 4 | 4 → 4 |
| B09 | 33/33 | 32/33 | 8 → 8 | 5 → 5 |
| B10 | 26/26 | 19/26 | 8 → 6 | 7 → 5 |

**Aggregate**, under current v6.4.2 revalidation of unchanged v6.3.9 claims:

- Saved exact source page quotations: **346/346** retained by baseline; **296/346** retained by Docling Parse (**85.55%**), a loss of **50** directly verifiable quote/page pairs.
- Historical findings surviving direct-evidence validation: **71 → 65** (**-6**).
- Findings screen-passed by the **current v6.4.2 validator**, not by human adjudication: **54 → 51** (**-3**).
- For B02, 48 → 32 exact quotes, 8 → 4 supported-by-quote findings, 2 → 1 screen-passed. For B10, 26 → 19 quotes, 8 → 6 source-evidenced findings, 7 → 5 screen-passed.
- Extractor subprocess wall time summed across the same ten PDFs: **8.22s PyMuPDF vs 33.91s Docling Parse (~4.13×).** Max child RSS **101.3 MiB vs 664.7 MiB**. These are **PDF extraction**, not full-Gemini latency/cost; resources are child high-water measurements, not concurrent system memory.

## Interpretation — what we can and cannot conclude

This replay is **not** a fresh full-model generation, human-scored semantic precision/recall, a page-citation accuracy gold set, or an assertion that all omitted quotes are factually absent from Docling output. The Docling parser may reflow, normalize, split or reorder text; however, the *current unchanged PaperSignal validator* requires source-localized matching and drops claims without it. That creates a **real compatibility/coverage regression in the current analysis pipeline**, even where raw numeric-token recall was higher.

The baseline's 346/346 reflects prior claims already generated with a PyMuPDF-based extraction and revalidated against the same baseline. It is not independent human proof of factual correctness. Likewise, 54 v6.4.2 screen-passed results here differs from the historical 53 v6.3.9 screen-passed count because the validator version changed; do not conflate those scores.

Earlier extraction-only exact-source tests reported Docling Parse paper-mean numeric-token recall 95.52% versus Camelot+pdfminer 91.20% *against frozen prior text*. That proxy did **not** establish best overall performance, and this citation replay explicitly exposes why selecting by raw numerical coverage is unsafe.

## Live-model attempt log and integrity

- Implementation branch: `experiment/full-analysis-ab-runner`, based on a parser-only swap from deployed Git commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` with **identical downstream analysis code**.
- Controlled full-model attempt deployment `25ec3be7-09c9-48ad-814d-152f984a9380`: B01 baseline primary and fallback HTTP **503, 503**; unpaired, stopped before Docling model analysis.
- Controlled second attempt deployment `521aaccd-dbe4-4f82-a9a6-55dfb2e6f98a`: B03 baseline primary and fallback HTTP **503, 503**; unpaired, stopped before Docling model analysis.
- Synthetic probe deployment `007cde1b-cd6a-4673-9d29-278887241586`: primary HTTP 200; fallback `ReadTimeout`. Probe is not a paper-analysis success.
- One intermediate redeploy using Railpack instead of the explicit Dockerfile failed before execution; corrected by reconnecting the exact pinned Git source with the correct Dockerfile.
- Fixed an experimental-image missing dependency (`pdfminer.six` for page-count traversal), leaving production untouched. Subsequent focused Docker build passed **7 tests** and real 10-paper replay completed.
- Replay deployment `5d169fb9-fbf1-4781-b080-05cb6ba949e5`; private namespace `replay-49dfcc9e5d9b4c0485ff70bcc1f56028`; **10 private JSON artifacts**, no model calls.
- Existing production API/Worker unchanged on SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`; original tables retain 14 papers, 103 analyses, 102 historically completed jobs, 28 failed jobs, and 14 private PDFs. Benchmark one-shot has zero running replicas.
- Full-series provider token and cost comparison **not available**: provider failures yielded no usageMetadata; output reflects no fabricated costs. Test artifact bucket remains private; raw claims and PDF texts are **not** in Git.

## Decision / next gate

**Do not replace PyMuPDF with the present Docling Parse integration.** It has a demonstrated current-validator citation/finding regression, a large memory increase and a slower extraction stage. This is a gate failure even without completing Gemini A/B. Keep old engine frozen and preserve the experimental alternative in a separate branch.

Before reconsideration: (1) independently review source quotes, especially B02/B10 and exact table cells; (2) fix explicit source-to-page text representation issues in a test-only parser adapter without loosening numeric validator; (3) rerun ten-paper evidence replay with zero regressions; (4) restore Gemini model availability and complete paired fresh end-to-end analysis with matched provider models, token/cost/latency telemetry and held-out evidence; (5) require human approval before production promotion.

**Final state:** fresh full-model comparison **blocked/incomplete**, deterministic ten-paper evidence comparison **complete**, production changes **none**.
