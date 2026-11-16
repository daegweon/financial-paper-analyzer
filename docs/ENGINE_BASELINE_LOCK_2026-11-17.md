# PaperSignal v6.4.2 — immutable corpus lock and baseline status (2026-11-17)

## Frozen production

- Branch: `feat/research-workspace-mvp`
- Commit: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`
- Analysis version: `finance-structured-v6.4.2`
- Production PyMuPDF pin: `PyMuPDF==1.26.3`

## Binary corpus locks

Two distinct, preregistered sets are now locked before candidate code:

- Held-out set H01/H02: lock commit `149311ec2993cac3bd410c10ac7feb202d582fc7`.
- Legacy regression set B01-B10: first complete SHA-256 manifest commit `342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c`; follow-up lock-reference commit `14ed46fd032b42813dd0ccf372447bd71bd363aa`.

The new candidate branch is based on the follow-up commit, so both lock commits are ancestors of the candidate.

### B01-B10 exact PDF hashes

| ID | Pages | Bytes | SHA-256 |
|---|---:|---:|---|
| B01 | 31 | 2,999,239 | `d729eaa7fa349916e1753775f7d5a4c12b629a3eb7af77f90dec06accacfacf3` |
| B02 | 20 | 606,182 | `aa602635a2f64639ee94b666d19ed23be2eaae5b19cccc030b896e84954c7854` |
| B03 | 14 | 396,873 | `489614f7c709d28b77b0092fe2e9e589e3d917d2a906546e67813fd19dfb68dd` |
| B04 | 19 | 4,418,309 | `dca200a597c048340f8eae81b09e169149501d0bc3b6809f31e15887521bd123` |
| B05 | 24 | 1,064,697 | `0d5c61c34054a6b2534f23b0f895e69cfc6cc78cd6758187f2c9604eb33d7a2c` |
| B06 | 22 | 975,524 | `42a8102e4b60dcae6eace1b23ee18e9f9dab4b4e7c968a61994fb1d95320e6c0` |
| B07 | 23 | 3,429,628 | `10ffc3942b5c74fda8d78e1c875f8c39e05546ff7bcd69fafefc53635d7123ad` |
| B08 | 21 | 1,202,803 | `fccffb87bfceba3b0971d208d357d7953637e33aad10d34f8bdcb27cb2c5d1d6` |
| B09 | 16 | 1,076,845 | `ab69f803264927a2321240f7f93696551e7691ec27cd221b0002363d329a288e` |
| B10 | 19 | 1,590,430 | `cee6e3a7171ccb93c25a1ce306058b615b4ded852c3806691b551aa9fc0c499e` |

Totals: **10 PDFs, 209 pages, 17,760,530 bytes**. Each original attachment was opened with PyMuPDF, verified as a PDF, confirmed unencrypted, and hashed over its exact original bytes. First-page titles were checked against the locked DOI/title manifest.

B01-B10 file names, sizes and page counts match the earlier read-only Supabase private-storage inventory. The connected Supabase tool did not expose the private object bytes; therefore binary identity against the private Storage objects is **not** claimed.

### Held-out H01/H02

| ID | Pages | Bytes | SHA-256 |
|---|---:|---:|---|
| H01 | 40 | 2,521,298 | `816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127` |
| H02 | 30 | 5,223,546 | `d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283` |

## Local extraction-only preflight

The exact frozen production `sanitize_pdf_text` and `extract_pages` logic was reproduced against B01-B10. On local PyMuPDF 1.26.7 (production pin is 1.26.3), all **209/209 pages** yielded text; no empty text pages. Extracted text total: 691,985 characters. Five-run per-file medians are in `benchmark/baseline_lock_v6.4.2_2026-11-17.json`.

This is a local extraction-only preflight, **not** a production-pinned run or Q2 evidence. It contains no Gemini call, upload, database save, cost or peak-memory measurement.

## Current gate status

- Binary corpus lock: **complete** (B01-B10 + H01/H02).
- Q0: **BLOCKED** — full frozen v6.4.2 end-to-end baseline, using PyMuPDF 1.26.3 and the same model/config, has not yet been executed.
- Q1: **BLOCKED** — 18 legacy review-required findings and at least 50 material claims require two independent human reviewers.
- Q2: **BLOCKED** — no matched full-pipeline p95, provider cost or peak RSS baseline/A-B comparison.
- P0: **BLOCKED** — two-account live E2E, SMTP and release/rollback checks remain outstanding.

Historical v6.3.9 diagnostics (71 findings, 18 review-required, 53 legacy screen-passed, 346 exact quote pairs) are compatibility context only and are not v6.4.2 baseline results.
