# PaperSignal reanalysis review — 2026-11-13

## Executive status

All ten benchmark papers remain completed in Supabase. Six targeted papers (B01, B03, B04, B05, B08, B09) were reanalyzed with `finance-structured-v5`.

- Methodology is now present for **10/10** papers.
- Structured findings are present for **9/10** papers.
- The latest analyses contain **175** page-validated evidence excerpts and **24** structured findings.
- Eight papers used Gemini Flash-Lite and two used Gemini Flash.
- Lexical gold-fact coverage screening is **90.0%** after adding source-grounded Korean paraphrase aliases.

The coverage score is a lexical screening metric, not semantic accuracy. Because aliases were refined after the first scorecard, the current 90.0% must not be compared directly with the earlier 74.25%.

## Targeted reanalysis comparison

| Paper | Previous method | Current method | Findings before → after | Evidence before → after |
|---|---|---|---:|---:|
| B01 | Present | Present | 0 → 3 | 13 → 18 |
| B03 | Missing | Present | 2 → 1 | 10 → 9 |
| B04 | Present | Present | 0 → 2 | 11 → 12 |
| B05 | Missing | Present | 3 → 2 | 20 → 22 |
| B08 | Present | Present | 0 → 0 | 15 → 8 |
| B09 | Missing | Present | 1 → 4 | 10 → 20 |

## What improved

- B01: findings increased from 0 to 3; five variables now carry individual page citations. The summary still falls back to a no-verifiable-summary message.
- B03: methodology is now present (OLS, 59 firms, 2008–2017 monthly sample, data sources, and variables). One structured finding remains.
- B04: findings increased from 0 to 2; the Markov regime-switching design and latent regime interpretation are now represented.
- B05: methodology is now present, including FE estimation, HAC standard errors, and a set of five control variables. Two findings are structured.
- B09: methodology is now present with HDFE, sample, data sources, variables and four findings.

## Outstanding defect: B08

B08's v5 result has a complete panel-regression methodology and its summary describes the directions of ESG scores / ESG momentum against returns / volatility. Its page-1 abstract evidence also explicitly states these empirical relationships. However, the structured `findings` array is still empty and a warning says no verifiable empirical finding was found.

This is a real structured-output extraction defect, not merely an alias-screening issue. It should be fixed with a targeted findings-only extraction pass that uses the already extracted page text and requires one exact page quote per finding. Do not fabricate findings from the summary.

## Other quality issue: B01 summary

B01 now has three findings and methodology, but the summary field is a fallback message because the summary-specific evidence check did not pass. A future repair should construct a concise summary only from already validated findings and methodology evidence, or run a short summary-only pass.

## Evaluation limitations

- All stored evidence excerpts passed the backend's page-level citation validation at analysis time. This verifies that the quote is present on the cited extracted page, not that it semantically supports every associated claim.
- The alias coverage score can miss paraphrases and cannot judge numerical correctness.
- Coefficient signs, units, t-statistics, p-values, significance levels, causal interpretation, and claim-to-quote entailment still require human review against the publisher PDFs.
- The ten analyses are not yet a fully controlled same-version experiment: B02 remains v3; B06, B07 and B10 remain v4; the six targeted reanalyses are v5.

## Recommended next action

Implement a small targeted findings-repair pass for B08 and a summary repair for B01, then re-run only those two papers. Afterward, perform a human audit of the most material numeric claims and citations before treating this benchmark as an accuracy claim.
