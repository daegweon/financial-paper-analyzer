# PaperSignal — held-out preselection (not yet binary-locked)

Registered: 2026-11-17, before creation of a new release-eligible candidate branch.

This registration preselects two publisher-version papers outside B01-B10. The current execution environment could inspect publisher PDFs and their page counts but could not retrieve their raw binary bytes. Therefore SHA-256 values are deliberately null, exact local byte/page validation is pending, and Q0 remains BLOCKED. Never substitute hashes of extracted text or HTML for PDF hashes.

| ID | Paper | DOI | Publisher PDF pages reported | Methods |
| --- | --- | --- | ---: | --- |
| H01 | Prediction and Allocation of Stocks, Bonds, and REITs in the US Market | 10.1007/s10614-024-10589-2 | 40 | VAR, TVP-VAR, DMA/DMS, genetic algorithm, portfolio optimization |
| H02 | Forecasting returns with machine learning and optimizing global portfolios: evidence from the Korean and U.S. stock markets | 10.1186/s40854-024-00648-w | 30 | LASSO, Ridge, Elastic Net, Random Forest, LightGBM, XGBoost, FX and portfolio optimization |

Both publisher pages identify the articles as open access and specify CC BY 4.0. Verify the licence page again before any redistribution. The original PDF bytes remain the authoritative benchmark objects.

- H01 article: https://link.springer.com/article/10.1007/s10614-024-10589-2
- H01 publisher PDF: https://link.springer.com/content/pdf/10.1007/s10614-024-10589-2.pdf
- H02 article: https://link.springer.com/article/10.1186/s40854-024-00648-w
- H02 publisher PDF: https://link.springer.com/content/pdf/10.1186/s40854-024-00648-w.pdf

## Lock procedure

1. Obtain the exact publisher PDF bytes, without converting or re-saving them.
2. Run `python -m benchmark.lock_heldout_pdfs --manifest benchmark/heldout_preregistration_2026-11-17.json --pdf-dir <private-pdf-dir> --out <private-locked-manifest.json>`.
3. Check the PyMuPDF page count and SHA-256 for each exact PDF. Compare the two hashes to each other and to the B01-B10 regression PDF hashes.
4. Commit the completed lock manifest on this planning branch. Record that commit as `lock_commit` in a follow-up commit, then create a fresh candidate branch from frozen production SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`.
5. Never tune against these papers; keep them strictly held out. No lock is valid if a model prompt or parser has already been tuned against their content.

Current status: PRESELECTED ONLY. PDF SHA-256 = null for both. No Q0 pass is claimed.


## Exact-byte verification utility

The repository now includes \`benchmark/lock_heldout_pdfs.py\`. Once the two actual publisher PDF files are available locally, run:

\`\`\`bash
python -m benchmark.lock_heldout_pdfs \\
  --manifest benchmark/heldout_preregistration_2026-11-17.json \\
  --pdf-dir /private/path/to/heldout-pdfs \\
  --out /private/path/to/heldout-binary-verified.json
\`\`\`

It uses PyMuPDF to verify PDF readability and exact page count, hashes the original unmodified bytes with SHA-256, rejects duplicate held-out files and optionally rejects hashes overlapping a supplied regression manifest. It never uploads or commits PDF bytes. The result is still not Git-locked: commit the verified manifest and record the resulting commit SHA in a follow-up commit before creating a new candidate branch.

Local lock-utility test reproduction: 7/7 synthetic checks passed after fixing one test assertion to match the utility's error contract. This is not a connected repository CI run. Exact publisher PDF bytes remain unavailable in the execution runtime; SHA-256 is still null for both papers and Q0 remains BLOCKED.


## Binary lock completed from user-uploaded PDFs

Exact original PDF bytes were supplied in the project conversation and opened with PyMuPDF. Both page counts, metadata/DOI and Creative Commons Attribution 4.0 licence text were verified.

| ID | Pages | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| H01 | 40 | 2,521,298 | 816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127 |
| H02 | 30 | 5,223,546 | d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283 |

The immutable binary lock is commit 149311ec2993cac3bd410c10ac7feb202d582fc7; the follow-up manifest records that lock SHA in commit 59b68fbc902bd17b656d606246d17b19a5614acf. A fresh candidate branch was then created from the frozen v6.4.2 production SHA. No tuning preceded the lock on this candidate branch.

