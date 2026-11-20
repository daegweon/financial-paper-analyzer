# PaperSignal Finance Paper Benchmark v1

## Purpose

This benchmark checks whether PaperSignal extracts the right research design, sample, econometric method, empirical findings, and limitations from real finance/economics papers. It is deliberately not a generic summarization benchmark.

The benchmark contains ten public/open-access candidate papers covering:
- factor pricing and cross-sectional returns;
- consumption-based pricing and foreign risk factors;
- Fama-French / Carhart factor regressions;
- Markov regime-switching;
- liquidity premia;
- exchange-rate / equity-market nonlinear cointegration;
- Korean macro-financial volatility;
- ESG / return / volatility relationships;
- corporate financing policy and volatility-of-volatility;
- realized-volatility portfolio optimization.

## Important status

**The benchmark set is curated; the ten PDF analyses have not yet been run.** The manifest contains source-grounded expected facts, not fabricated model scores. The article-specific PDF version and page numbers must be confirmed after downloading the PDFs.

Do not treat an article being publicly accessible as automatic permission to redistribute it. Check the license on each publisher page. The PLOS Korea paper explicitly uses the Creative Commons Attribution License. Several MDPI pages identify CC BY; verify the article footer for each paper before redistribution.

## Paper set

| ID | Market / topic | Method family | DOI |
|---|---|---|---|
| B01 | Brazil / factor sufficiency | Panel factor estimators, MG, CCE | 10.3390/ijfs11040144 |
| B02 | Korea / foreign consumption risk | Two-country consumption pricing, GMM | 10.3390/ijfs11020062 |
| B03 | Morocco / factor model pricing | OLS, FF3, Carhart 4-factor | 10.3390/ijfs11010020 |
| B04 | China / bull-bear regimes | Markov-switching CAPM and FF3 | 10.3390/ijfs6020054 |
| B05 | Poland / liquidity premium | Fixed effects, HAC | 10.3390/ijfs8010013 |
| B06 | ASEAN-5 / FX and equities | Panel ARDL / NARDL, PMG | 10.3390/ijfs11010007 |
| B07 | Korea / macro volatility | GARCH-MIDAS, adaptive LASSO | 10.1371/journal.pone.0300393 |
| B08 | US / ESG and returns | Multifactor panel regressions | 10.3390/jrfm18070367 |
| B09 | US / corporate finance and VOV | High-dimensional fixed effects | 10.3390/jrfm18020096 |
| B10 | Thailand / portfolio construction | Realized-volatility optimization | 10.3390/jrfm18050269 |

Full metadata, expected facts, source URLs, and critical caveats are in `manifest.json`.

## How to run the first benchmark

1. Download each article PDF from its publisher page. Use the publisher's current PDF version, not a third-party re-upload.
2. Confirm the article's license and save the PDF locally.
3. Rename files with the benchmark ID prefix, e.g. `B01_factor-sufficiency.pdf`, `B02_korea-durable-consumption.pdf`.
4. Sign in to the PaperSignal test account and upload the ten PDFs. The title field should retain the B01–B10 prefix.
5. Run Gemini analysis once per paper. The free-tier quota is shared at the Google project level; run a small batch first and pause if the API returns 429.
6. In Supabase SQL Editor, run `export_analyses.sql` and save the returned rows as `results/analysis_results.json`.
7. Run the screening evaluator:

```bash
python benchmark/evaluate.py \
  --results benchmark/results/analysis_results.json \
  --out benchmark/results/scorecard.json
```

Optional page-level verification:
- Save extracted page text for each paper as `benchmark/pages/B01.json`, where the JSON object maps page numbers to extracted page text.
- Then pass `--pages-dir benchmark/pages`. The evaluator checks whether every stored evidence quote is an exact substring of its claimed page.

## What the evaluator reports

- **Gold-fact coverage:** deterministic alias matching against the source-grounded facts in the manifest. This is a screening signal only; it is not semantic accuracy.
- **Claim evidence coverage:** share of extracted research claims that have at least one evidence excerpt.
- **Citation-page precision:** when page text files are provided, share of evidence excerpts that exactly match the claimed page.
- **Human review score:** optional review annotations for factual correctness, citation support, and unsupported claims.

The automatic alias matcher can miss valid paraphrases and can occasionally match a term in the wrong context. Never publish its score as a standalone model-accuracy claim. A reviewer must inspect numeric values, signs, statistical significance, and causal language against the paper's tables and text.

## Human review protocol

For each paper, check at least:
1. title, authors, year, journal and DOI;
2. sample, country, frequency and period;
3. dependent / independent variables and factor definitions;
4. model family, estimator, standard errors and identification strategy;
5. coefficient sign, magnitude, units, p-value / significance level;
6. robustness checks actually performed (not merely suggested);
7. author-stated limitations;
8. each material AI claim against the cited PDF page.

Use `review_template.json`. Rating meanings:
- `correct`: supported by the paper and accurately stated;
- `partial`: direction is right but an important qualifier / unit / condition is missing;
- `missing`: expected fact is omitted;
- `incorrect`: contradicts the paper or invents a result;
- citation `exact`: the quote is verbatim and the page number is right;
- citation `partial`: relevant but clipped / page uncertain;
- citation `wrong`: quote or page is wrong.

## Privacy / free-tier handling

This set is intended for public research papers only. Gemini Free Tier inputs and outputs may be used by Google to improve products and may be human-reviewed. Do not include internal company research, client information, credentials, personal data, or confidential papers in this benchmark.

## Current benchmark status

- [x] Ten candidate papers selected
- [x] Source-grounded gold facts and critical caveats drafted
- [x] Screening evaluator and human-review template
- [ ] Download and license-check all exact PDF versions
- [ ] Upload ten PDFs and run Gemini
- [ ] Human-review every critical fact and citation
- [ ] Publish a measured quality report

## Generate a human evidence-review packet

After exporting analyses as JSON, create a Markdown packet that preserves each finding's table reference, model/column, estimate, significance and direct PDF quotations:

```bash
python benchmark/build_review_packet.py \
  --results benchmark/results/analysis_results.json \
  --out benchmark/results/human-review-packet.md
```

The packet includes a per-finding reviewer decision and notes area. It deliberately marks zero findings as approved: generation is administrative assistance only and never changes an analysis verification status. Review every claim against the exact publisher PDF before recording a decision.

## Generate the offline quality dashboard

After producing the evaluator scorecard, render a standalone HTML dashboard:

```bash
python benchmark/evaluate.py --results benchmark/results/analysis_results.json --out benchmark/results/scorecard.json
python benchmark/quality_dashboard.py --scorecard benchmark/results/scorecard.json --out benchmark/results/quality-dashboard.html
```

The dashboard reports only metrics present in the scorecard. Missing PDF page text and missing human reviews remain **미측정**; they are never treated as zero or inferred from alias coverage. It shows per-paper missing Gold facts and does not approve findings. Open the generated HTML locally; no service or network connection is required.

## Diagnose evidence and numeric-claim gaps

Run the offline triage against exported analyses:

```bash
python benchmark/diagnose.py \
  --results benchmark/results/analysis_results.json \
  --pages-dir benchmark/pages \
  --out benchmark/results/diagnostics.json
```

The report flags missing direct evidence, quotations not found on their stated PDF page, and numeric result fields (estimate/coefficient/significance/statistic/p-value) whose values are absent from the direct quotation. It deliberately does not treat structural counts in prose as regression estimates unless they are explicitly stored in numeric result fields. The diagnostic is conservative triage, not a semantic judge; it never approves a finding or changes the analysis.

## Compare engine versions on paired papers

Evaluate the baseline and candidate exports separately, then compare their scorecards:

```bash
python benchmark/evaluate.py --results benchmark/results/v1.json --out benchmark/results/v1-scorecard.json
python benchmark/evaluate.py --results benchmark/results/v2.json --out benchmark/results/v2-scorecard.json
python benchmark/compare_scorecards.py --baseline benchmark/results/v1-scorecard.json --candidate benchmark/results/v2-scorecard.json --out benchmark/results/v1-v2-comparison.json
```

Only papers with measured values in both scorecards contribute to each metric's paired aggregate. Missing scores are excluded rather than treated as zero. The report includes per-paper deltas and improved/regressed/unchanged counts. It is descriptive and does not establish causal model improvement; alias coverage is only a screening signal, page precision requires exact PDF text, and human scores require explicit reviewer input.

## Analyze failure categories and fallback attempts

Export the Railway API text logs and run:

```bash
python benchmark/failure_report.py railway-api.log --out benchmark/results/failure-report.json
```

The report groups failed analysis jobs into authentication, authorization, missing resource, provider quota, timeout, provider unavailable, invalid model response, other HTTP and application errors. It also counts Gemini attempts/errors by model. An alternate-model HTTP 200 is not automatically counted as a recovered job; correlate the same job with a later completion event before deriving recovery rate. Logs without a model identifier cannot be attributed to a model. This is offline, read-only triage and does not retry or mutate jobs.
