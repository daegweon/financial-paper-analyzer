# PaperSignal v6.1 targeted reanalysis report — 2026-11-13

## Executive result

Six targeted papers (B01, B04, B06, B08, B09, B10) were reanalyzed successfully. Supabase confirms all six latest jobs are `completed`, and each latest analysis is `finance-structured-v6.1`.

### v6.1 subset

- 6/6 jobs completed.
- 17 structured findings.
- 150 page-validated evidence excerpts.
- 7 findings flagged for researcher review by the preliminary numeric/significance screen.
- 6/6 have a methodology design field and at least one methodology section citation.
- 6/6 have at least one structured finding.
- Mean lexical gold-fact coverage: **86.25%**.

### Current ten-paper workspace

- 6 latest analyses use v6.1; B02, B03, B05 and B07 remain on v6.
- 34 structured findings and 228 page-validated evidence excerpts across the latest ten analyses.
- 9 findings are flagged for researcher review.
- Mean lexical gold-fact coverage across the mixed-version set: **88.00%**.
- Claim-evidence coverage is 100% for retained structured claims, meaning each has at least one citation; this does not establish semantic entailment.

Do not present the 88% mixed-version metric as a controlled v6.1 score.

## Targeted comparison: v6 → v6.1

| Paper | Findings v6 → v6.1 | Evidence v6 → v6.1 | Review flags v6 → v6.1 |
|---|---:|---:|---:|
| B01 | 2 → 1 | 17 → 24 | 1 → 0 |
| B04 | 3 → 4 | 22 → 34 | 3 → 1 |
| B06 | 1 → 2 | 13 → 16 | 1 → 1 |
| B08 | 4 → 4 | 32 → 36 | 2 → 2 |
| B09 | 0 → 3 | 14 → 20 | 0 → 3 |
| B10 | 4 → 3 | 12 → 20 | 0 → 0 |

Interpretation:
- B09 recovered from zero findings to three supported findings.
- B06 recovered one additional finding and the findings-only repair pass ran.
- B04 added one finding.
- B08 retained four findings, now with separate ESG score / ESG momentum relationships.
- B01 and B10 returned one fewer finding than v6. More conservative extraction may explain the reduction, but completeness must be reviewed rather than assuming fewer is better.

## Remaining paper-specific issues

### B01 — sample description incomplete
Panel dimensions now correctly validate 12 portfolios × 4,950 daily periods = 59,400 portfolio-period observations. However, the separate `sample` field remains "확인 불가", and only one finding remains, focused on the CCE MSE comparison. The main factor-pricing significance result should be checked for omission.

### B04 — significance context
Four findings are present. One is flagged because the cited table excerpt shows a p-value but does not itself include the significance legend. The table note and model/column alignment should be reviewed before treating this as an error.

### B06 — source and extraction inconsistency
The official article itself reports different sample counts in different sections:
- Abstract: 365, 650 and 1,085 observations.
- Methodology prose: 366, 606 and 1,086 observations.
- Descriptive Table 1: 365, 605 and 1,085 observations.

The v6.1 panel checker treats 365 as a period count and multiplies by five countries, producing a mismatch. The article's own numbers are inconsistent; the product must preserve each reported figure and flag the conflict rather than select one count silently. The structured findings also include the pre-crisis asymmetric result but do not yet separately represent the whole-sample asymmetric cointegration result.

### B08 — unbalanced panel false positive
The official article says the sample expanded over time as ESG coverage grew, reports 3,856 stocks, 81 quarters and 84,345 observations. This is an unbalanced panel; 3,856 × 81 is not expected to equal the observed panel count. The v6.1 "mismatch" is therefore not evidence of a paper error. The panel audit needs a balanced/unbalanced design field and should skip multiplication for unbalanced panels. Two findings are flagged because the cited snippets omit the table significance legend; the source's table note maps ***, ** and * to p-values below 0.01, 0.05 and 0.1 respectively.

### B09 — findings recovered, numeric flags remain
Three findings now exist, compared with zero under v6. Three findings are flagged because the evidence snippets show coefficient/t-statistic columns but not the p-value threshold in the same quote. A table-aware significance parser should link the table's legend and correct column headers before deciding whether these are true mismatches.

### B10 — methodology partly recovered
The design, sample, period, data source, variables and eight methodology citations are present. However, `empirical_strategy` remains "확인 불가". This paper is a constrained portfolio-optimization study, not a conventional panel regression. Panel multiplication should be marked not applicable rather than calculating a pseudo total of 40 × 1,250.

## Verified public-source cross-checks

- B06 publisher article: https://www.mdpi.com/2227-7072/11/1/7
- B08 publisher article: https://www.mdpi.com/1911-8074/18/7/367

## Next development recommendation: v6.2

1. Add explicit panel design classification: balanced, unbalanced, repeated cross-section, time series, or not applicable.
2. Use typed numeric fields for cross-sectional unit count, time-period count and reported observations; do not parse years as counts.
3. For unbalanced panels, do not compare N×T with the observed count.
4. Preserve contradictory source counts in a conflict object with page-level evidence.
5. Add table-footnote-aware significance parsing and model/column association.
6. Add targeted repair triggers for missing sample, empirical strategy and omitted whole-sample findings.
7. Add regression tests for B06's contradictory sample counts, B08's unbalanced panel and B10's non-panel optimization design.

## Conclusion

v6.1 materially improved B09 and recovered results for B06. However, it also exposed that panel consistency checks need to understand the study design before multiplying dimensions. The next priority should be context-aware sample auditing and table-aware significance interpretation, not simply increasing the number of generated findings.
