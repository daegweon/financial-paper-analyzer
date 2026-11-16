# PaperSignal — Complete PyMuPDF replacement trial (experimental)

Date: 2026-11-16 (Asia/Seoul)
Outcome: **EXPERIMENT EXECUTED; NO PRODUCTION PROMOTION**
Engine development freeze: production API/Worker remain pinned to commit `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` with source version `finance-structured-v6.4.2`. Do not change the original engine while full replacements are being evaluated.

## Experiment, not a production refactor

The experimental `backend/app/main.py` imports `extract_pages` from `app.pdf_replacement` instead of `fitz`. The original `extract_pages` function and `fitz` import are removed in this experiment. The same `(page_count, [{page,text},...])` contract is exposed to the downstream engine, with no automatic PyMuPDF fallback. Isolated Docker images install candidate requirements that omit PyMuPDF. This is a full swap of the *PDF parsing boundary*, not an end-to-end Gemini-backed analysis or complete deployed web service.

Alternatives actually attempted:
- **Docling standard 2.150.0** (OCR off, table structure enabled): package installation, six contract tests, and app-main import succeeded, but 4/4 original conversion subprocesses exited with code 1 (~5 s each). Root exception was not captured; cannot conclude Docling itself cannot handle the papers. Large PyTorch/CUDA dependency burden noted. Standard execution snapshot `349e0d06-60e1-4f60-9892-f6a243d827ad`.
- **docling-slim Native converter 2.150.0**: 4/4 conversions failed with code 1 (~1.6–1.8 s); safe follow-up isolated exception class was `ImportError`. This is a packaging/API setup failure, not a PDF accuracy verdict.
- **Camelot 1.0.9 + pdfminer.six 20260107**: full replacement via a composite path because Camelot alone cannot parse arbitrary prose. **10/10 original PDFs succeeded**.
- **Docling Parse 7.26.0 (native parser without ML/OCR)**: direct alternative using Docling's underlying C++ PDF text parser, **10/10 original PDFs succeeded**. This is NOT the standard Docling layout/table-structure pipeline. The main experimental extraction entry point defaults to this option on its runner branch.

## Frozen-original comparison: B01–B10 / 209 pages

Source bytes, ETags, sizes and SHA-256 are locked in `benchmark/table_corpus.sha256.json`. Both successful alternatives produced all the original pages, with no missing pages relative to frozen PyMuPDF source text. Frozen baseline = **earlier PyMuPDF page.get_text('text',sort=True)** from private 2026-11-16 artifacts, not a fresh run of the complete current engine. The baseline retains whole-page text while replacements enforce the production 4,500-character page cap; so token coverage is a proxy with different truncation behaviour, **not independently verified source correctness or a clean extraction-quality score**.

| Paper | Camelot numeric-token recall vs frozen text | Docling Parse recall | Camelot wall s | Docling Parse wall s | Camelot RSS MiB | Docling Parse RSS MiB |
|---|---:|---:|---:|---:|---:|---:|
| B01 | 93.82% | 94.87% | 4.2363 | 3.9739 | 191.16 | 559.25 |
| B02 | 94.66% | 95.56% | 2.7801 | 3.1221 | 161.45 | 483.75 |
| B03 | 90.15% | 91.98% | 2.0231 | 2.5222 | 153.59 | 431.08 |
| B04 | 84.40% | 96.87% | 8.7367 | 3.8243 | 245.45 | 537.91 |
| B05 | 90.58% | 94.95% | 3.9269 | 4.6756 | 187.16 | 651.25 |
| B06 | 91.23% | 91.54% | 3.7778 | 4.1251 | 179.48 | 591.89 |
| B07 | 89.45% | 97.95% | 4.4941 | 3.2236 | 180.65 | 505.91 |
| B08 | 92.64% | 96.36% | 3.4228 | 3.2750 | 170.89 | 521.75 |
| B09 | 92.26% | 95.24% | 3.0301 | 2.8758 | 161.17 | 460.71 |
| B10 | 92.78% | 99.87% | 2.5811 | 2.7240 | 170.17 | 445.33 |

The mean of the ten *paper-mean page token recall* percentages is 91.20% Camelot versus 95.52% Docling Parse, not an accuracy or F1 score. Neither candidate was checked against the original page's human-confirmed numeric/column reference at scale.

| Metric | Camelot+pdfminer | Docling Parse |
|---|---:|---:|
| Subprocess completed | 10/10 | 10/10 |
| Wall-time total across ten PDFs | 39.009 s | 34.342 s |
| Per-PDF wall-time p50 | 3.600 s | 3.249 s |
| Per-PDF wall-time p95 (10 samples) | 6.828 s | 4.428 s |
| Max child RSS | 245.45 MiB | 651.25 MiB |

Timing includes subprocess loading and extraction only; excludes Storage transfer, PDF analysis-model calls, job queue latency, all operational overhead, and infrastructure cost. RSS is high-water of the isolated child, not concurrency-safe total service memory. Sample p95 is descriptive, not an SLA. Prior PyMuPDF text-only p50 was 0.716 s/PDF but is not an apples-to-apples total engine comparison.

## Verdict

**Docling Parse ranks above Camelot+pdfminer on this particular proxy, but neither is cleared to replace the frozen production engine.** Docling Parse shows better numeric-token retention on every paper, especially B04 (+12.47 percentage points), B07 (+8.50 pp), B10 (+7.09 pp), and lower median measured candidate wall time; maximum child memory is ~2.65x Camelot composite's maximum. Gemini analysis completeness, correct row/model alignment, p-values/stars, all page citations, source-only false claims, whole-service cost, and held-out coverage have NOT been verified. The known B01 Table 2 omission under Camelot has not been source-adjudicated against Docling Parse. Standard Docling conversion remains an unresolved setup failure.

Do not merge experimental source or runner `railway.toml` into production. Do not overwrite historical analyses. Preserve the source/metrics artifacts privately. Subsequent work, only if requested, should compare all original-source claims and outputs from the *complete* downstream pipeline with a held-out and human-reviewed gold set before any promotion. The prior 18 review-required findings remain unapproved. No global optimum claimed.

## Reproducible code and deployments

- Parser-swap core: `experiment/full-pymupdf-replacement` (experimental `backend/app/main.py`, `app/pdf_replacement.py`, `Dockerfile.full-replacement`, frozen comparator).
- Camelot runner: `experiment/full-parser-camelot-runner` commit `c62ca21fc15a5f908969936ce950fac11a68c537`, Railway run `b7e51804-15a2-44f1-af20-beb732434619`.
- Docling Parse runner: `experiment/full-parser-docling-parse-runner` commit `c3cc6ec7a3a2a32967a07e2ae079a3f63693dc82`, Railway run `73a3e4f5-b750-487e-931d-f1e611da58a9`.
- Standard Docling runner: `experiment/full-parser-runner` commit `67cdb2f4ebc10bb39738f3b386dda4db929c886c`, run `349e0d06-60e1-4f60-9892-f6a243d827ad`.
- Private data: source bucket `papers` unchanged at 14 PDF objects; isolated benchmark artifacts are private JSON only. Database after checks: 14 papers, 103 analyses, 102 historically completed jobs, 28 historical failed jobs.
- Railway API and Worker remain on prior success deployment and same commit. No experiment test service has a public domain, cron or running replica after completion.
