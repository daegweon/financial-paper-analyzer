# Ranked PDF parser replacement: B01-B10 evidence replay

Date: 2026-11-17 (Asia/Seoul); **FINAL checkpoint after Marker CPU trial**
Priority explicitly requested: **pypdfium2 → pdfplumber → GROBID → MinerU → Marker**.
**Production remains FROZEN; no candidate promoted.** This checkpoint covers the first two exact-source measured candidates, the other engines' feasibility gates, and a separately queued Marker CPU attempt.

## Exact source & quality gate
- Ten SHA-256/ETag/length/page-count checked original PDFs (209 pages).
- Same stored v6.3.9 result claims/quotes rechecked by unchanged v6.4.2 evidence/finding validators on baseline versus each candidate extractor.
- Baseline **346/346** quote/page pairs and **54** current-screen-passed findings are a *compatibility gate*, not human-confirmed PDF correctness.
- No Gemini calls, SQL analysis/job updates, or PDF writes. Full model quality/financial numeric cell gold unverified.

## Completed measurements

| Metric | PyMuPDF baseline | pypdfium2 5.15.2 | pdfplumber 0.11.10 |
|---|---:|---:|---:|
| Papers successfully processed | 10/10 | 10/10 | 10/10 |
| Previous exact quotes preserved | **346/346 (100%)** | 292/346 (84.39%) | 14/346 (4.05%) |
| Findings with direct evidence | **71** | 64 | 2 |
| Screen-passed findings under current v6.4.2 verifier | **54** | 50 | 1 |
| Sum parser subprocess wall (10 PDFs) | 7.0552 s | **6.1527 s** | 24.1568 s |
| Maximum child-process RSS | 97.555 MiB | **80.621 MiB** | 309.734 MiB |
| Full-service accuracy / Gemini latency / cost | Not measured | Not measured | Not measured |

These numbers are the reproducible run's *isolated subprocess* durations, not overall service throughput. The former baseline PDF text is reused in the historical findings, creating an advantage for exact quote matching; neither the 100% reference or the candidate percentages establish real PDF source truth. Missing matches can arise from altered whitespace/reading order, not necessarily missing underlying facts; yet they are currently rejected by PaperSignal's strict source-citation verification.

| Paper | Baseline exact quote retention | pypdfium2 | pdfplumber | Screen-passed findings (baseline / PDFium / plumber) |
|---|---:|---:|---:|---:|
| B01 | 31/31 | 24/31 | 1/31 | 2 / 2 / 1 |
| B02 | 48/48 | 29/48 | 2/48 | 2 / 1 / 0 |
| B03 | 33/33 | 26/33 | 3/33 | 5 / 4 / 0 |
| B04 | 29/29 | 25/29 | 0/29 | 8 / 8 / 0 |
| B05 | 37/37 | 35/37 | 3/37 | 5 / 5 / 0 |
| B06 | 27/27 | 25/27 | 1/27 | 8 / 8 / 0 |
| B07 | 43/43 | 40/43 | 1/43 | 8 / 8 / 0 |
| B08 | 39/39 | 37/39 | 2/39 | 4 / 4 / 0 |
| B09 | 33/33 | 32/33 | 0/33 | 5 / 5 / 0 |
| B10 | 26/26 | 19/26 | 1/26 | 7 / 5 / 0 |

## Remaining candidates in the requested order

**GROBID (3): NOT EXECUTED.** The official full-text REST endpoint returns TEI, and page/coordinate attribution is different from PaperSignal's exact page-text input contract; a dedicated Java GROBID service is absent, and official docs advise several GB RAM. Current isolated Railway runner hard limit is 1 GB. This is an infrastructure and integration feasibility blocker, not measured extraction quality. Apache 2.0 code.

**MinerU (4): NOT EXECUTED.** Current official hardware docs specify **minimum 16GB RAM** for local pipeline / engine modes (and additional disk/model costs), far above the benchmark's 1 GB; using an unaudited external hosted parser for locked private storage is not allowed. MinerU uses a custom Apache-derived license with extra commercial/attribution conditions. No accuracy result recorded.

**Marker (5): ATTEMPTED, NOT ACCURACY-MEASURED.** In the isolated CPU nonroot service with `marker-pdf==2.0.0`, installation, CLI help and **two focused unit tests** succeeded. The v2.0 CLI does **not** accept the newer standalone `no_ocr` mode, so the initial CLI attempt exited code 2; it was corrected to `--mode fast --disable_ocr`. B01 original execution then exited code 1 with a sanitized `permission_denied` diagnostic. A further nonroot attempt with writable HOME, Hugging Face/PyTorch caches and temporary working directory also ended code 1 / `permission_denied` after **6.2191 s**. No page-indexed JSON was produced and **no numeric/citation/Findings score is available**. The image's heavyweight PyTorch/CUDA dependencies and the separate commercial license of Marker model weights are additional deployment concerns. This is an *execution-environment blocker*, not proof Marker text accuracy is poor. Experimental execution-only branch `experiment/marker-cpu-noocr-runner`, final commit `bbe5add099cadc56cef2295cc5bf75c21f6da8db`, final deployment `b2e9600c-c438-47f5-9ef2-6ae8fd819793`; zero running replicas after exit.

## Decision gate

- pypdfium2: less extraction time/memory, but 54 missing original exact citations and 4 lost screened findings: **full replacement not approved**.
- pdfplumber: much larger quote/finding retention regression and slower: **full replacement not approved**.
- GROBID/MinerU: cannot assign accuracy/speed score when not run.
- Marker: installed/CLI-tested but B01 CPU execution blocked by nonroot permission errors; source-citation quality NOT MEASURED, no promotion.
- No production modifications or global performance-maximum claim. A new parser needs 346/346 baseline original citations and 54/54 current screen-passed findings, verified *new* source cell accuracy, at least equivalent total time/memory/cost and paired real-model held-out tests before adoption.

## Reproduction and security

- Core code: `experiment/ranked-pdf-parser-trial`, `benchmark/oss_ranked_trial.py`.
- Execution-only branch: `experiment/ranked-pdf-parser-runner`, commit `76aad7f19456ae5a674de050097a17352ad53eea`; never merge its root `railway.toml` to production.
- Railway one-off service `c279046d-aedc-43bf-9e25-c09ab59fe38b`, deployment `bbf487c2-4a1f-4657-b8ab-4ddc159f9c0a`, private run `ranked-oss-82646488eb5d421d8556b4f261e71432`. Focused Docker build tests passed.
- Private artifact namespace stores source hashes and metrics, not full PDF text or user identifiers in Git. Existing private bucket remains private.
- Production API and Worker source/deployments untouched. No new model calls.

## Final run status and adoption verdict (post-marker)

| Requested rank | Parser | Exact B01–B10 quote/Findings test | Feasibility conclusion | Adopt into production? |
|---|---|---|---|---|
| 1 | pypdfium2 5.15.2 | **10/10 complete; 292/346 quotes; 50/54 screen-passed** | Fast and lower RSS but supported evidence regression | **No** |
| 2 | pdfplumber 0.11.10 | **10/10 complete; 14/346 quotes; 1/54 screen-passed** | Incompatible source quote representation without relaxing validator | **No** |
| 3 | GROBID | **Not executed** | Local Java/TEI service absent, multi-GB RAM needed | **Not assessed** |
| 4 | MinerU | **Not executed** | Official local minimum RAM 16GB vs 1GB benchmark cap | **Not assessed** |
| 5 | Marker 2.0 CPU `fast --disable_ocr` | **Attempted B01, no page-indexed result** | Installed; nonroot run exited with permission_denied even after writable-cache/cwd repair | **Not assessed** |

Original 10-paper production-aligned source lock remains intact: 14 paper rows, 103 analysis rows, 102 completed / 28 historical failed jobs, and 14 private PDF Storage objects. Private benchmark JSON artifacts now total **99**, including new candidate and Marker error packets; no raw paper text or credentials were published. Railway benchmark services have **0 running replicas**, while production API and Worker each remain online with unchanged source commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`.

**Final:** no full PyMuPDF replacement cleared the non-regression gate. Do not treat GROBID, MinerU or Marker failure-to-run as evidence of poor document accuracy. Future evaluations would require adequate isolated memory, source-localized JSON/TEI contracts, legal model-weight clearance where applicable, independent human page-level gold and model-backed whole-pipeline A/B when provider availability permits. No unconditional production merge.

### Official prerequisite references

- GROBID deployment / TEI API: https://grobid.org/guides/grobid-docker-and-api
- MinerU recommended hardware and license: https://github.com/opendatalab/MinerU and https://github.com/opendatalab/MinerU/blob/master/LICENSE.md
- Marker CLI and commercial weight restrictions: https://github.com/datalab-to/marker and https://pypi.org/project/marker-pdf/
