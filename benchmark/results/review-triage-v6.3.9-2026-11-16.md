# v6.3.9 review-required findings — triage

- Date: 2026-11-16
- Scope: 18 findings marked `review` across the latest B01–B10 analyses.
- Rule: this is a triage of machine-generated claims and their cited excerpts, not a human confirmation of the underlying publisher PDF. No finding is promoted to supported here.

## Counts

| Paper | Review-required |
|---|---:|
| B01 | 4 |
| B02 | 6 |
| B03 | 1 |
| B04 | 0 |
| B05 | 2 |
| B06 | 0 |
| B07 | 0 |
| B08 | 0 |
| B09 | 3 |
| B10 | 2 |
| **Total** | **18** |

## Triage by failure mode

### A. Claim contains a coefficient/estimate that is absent from the direct evidence quote

These should remain review-required until the exact regression/table row is included as direct evidence. A nearby page quote or significance legend is not a substitute for the coefficient row.

- B01: MG coefficients (0.9548, 0.2987); Wald statistics (434.53, 49,066.00); HML risk-premium sign change (0.00026, -0.00013); CCE MSE (0.000004). Some numeric table content was placed in the separate legend field rather than the finding's direct evidence field.
- B02: consumption-growth coefficient vector (49.942, 78.394, 209.734, 113.840 and standard errors); DUS coefficient 408.203; R² comparison 0.633 vs 0.345. The evidence quote for some findings contains only prose, not the estimate row.
- B05: liquidity-premium range (2.394–2.667) and UTP After estimate (0.154); current quotes establish direction/significance in prose but omit the numeric estimate.
- B09: estimates 0.929, -0.074 and 0.643; current quotes establish direction/association but not the exact coefficient rows or their significance stars.
- B10: Sharpe-ratio series (0.11–0.17) and comparison (0.20 vs 0.04); the quotes include those numbers but the finding claim also contains portfolio counts 4 and 5, which the current structural-number filter does not fully recognize.

### B. Structural identifiers misclassified as numeric result claims

These are candidates for a narrow parser improvement, but only after a regression test demonstrates that true numeric claims remain checked.

- B02: 15 portfolios, BE/ME3–BE/ME5 group labels, 25 Fama–French portfolios, and two-country/one-country model labels.
- B03: “four out of six portfolios” is a portfolio count in a model-comparison statement, not a coefficient.
- B10: “4-stock” and “5-stock” portfolio descriptions are group identifiers, not effect-size estimates.

### C. Citation/legend linkage is incomplete

- B01 Table 5 and B09 Table 5 findings have no independently validated significance-legend excerpt.
- B03 uses a generic table note as a legend even though the claim concerns comparative model performance rather than a coefficient significance claim.
- B10 has no significance legend, which is acceptable if the result is a descriptive Sharpe-ratio comparison; do not invent a p-value.

## Recommended action

1. Do not relax the direct-quote numeric validator. It is correctly refusing to approve estimates not present in the actual finding evidence excerpt.
2. Improve extraction/repair prompts so each numeric finding cites the exact row containing the variable name, coefficient, standard error/t-statistic and stars where available. Keep significance legend as a separate, additional citation.
3. Add only narrow structural-number patterns (e.g. “four out of six portfolios”, “4-stock/5-stock portfolio”, “15 portfolios”, “BE/ME3–BE/ME5”) with paired tests proving that coefficients and test statistics remain audited.
4. Retrieve/open the exact PDF page for every candidate and have a reviewer check claim, row alignment, column/model, estimate, sign, p-value/legend and page number.
5. Re-run the 10-paper benchmark only after the focused changes pass the regression suite; compare supported precision and Gold-fact coverage, not raw finding count alone.

## Release decision

The v6.3.9 benchmark is a positive engineering signal, but the 18 review-required findings are not certified. Public beta remains gated on page-level human audit, quota/cost telemetry and the outstanding live-user E2E/SMTP/production-domain checks.
