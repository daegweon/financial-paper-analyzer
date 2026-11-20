# Assistant second-pass evidence audit — 2026-11-20

**Disposition:** completed as an AI-assisted pre-review. This is not an independent human sign-off, and no stored analysis verification status was changed.

## Scope and current snapshot

- Read-only review of the latest completed analysis for each of B01–B10 in the PaperSignal Supabase project.
- Latest stored analysis versions are mixed: B01/B02/B09 v6.4.0; B10 v6.4.2; B03–B08 v6.3.9.
- Latest snapshot: **63 findings, 57 `screen_passed`, 6 `review`**. The older v6.3.9 benchmark scorecard (71 findings, 53 screen-passed, 18 review-required) remains a historical snapshot and is not the current latest-analysis count.
- Direct PDF page checks: B01 pp. 3, 11 and 18; B02 p. 10; B03 p. 12; B05 pp. 9 and 17.
- The six current `review` records belong to five distinct claim units because B01 findings #5 and #6 duplicate the same Table 4 result.

## Finding-by-finding results

### B01 — findings #5 and #6, Table 4 (PDF p. 18)

**Evidence observed**

- Table 4 reports four Wald statistics: Test 1 = 434.53, Test 2 = 49,066.00, Test 3 = 601.36, and Test 4 = 566.76; each displayed p-value is 0.00.
- The surrounding paragraph says all four tests reject the relevant null hypotheses and concludes that there are strong indications of omitted factors.
- The paper's methods discussion (p. 3) and factor vector definition (p. 11) confirm that the tested specification concerns five factors.

**Assessment: core inference supported; wording and duplication need correction.**

- Findings #5 and #6 substantially duplicate the same result and should be consolidated rather than counted as two independent discoveries.
- “Proves” is too strong; “provides evidence consistent with omitted relevant factors” is safer.
- The paper prints p-values as 0.00. Preserve the displayed precision and identify them as rounded; do not imply access to the unrounded p-values.
- The automated unsupported-number flags `5` and `1` are structural references to the five-factor specification and “Test 1”, not unsupported coefficient estimates.

**Recommended disposition:** consolidate the two records, retain the table values, and phrase significance as “reported p = 0.00 (rounded)”. Keep the stored records in `review` until a human reviewer signs off.

### B02 — finding #3, Table 3 (PDF p. 10)

**Evidence observed**

- Table 3 explicitly reports the joint null hypothesis that the U.S. factor risk prices are zero and gives Wald χ² = 68.320 with p = 0.000.
- The paragraph immediately below the table says the Wald test strongly rejects that null.

**Assessment: substantively supported; the evidence payload is incomplete.**

- The current evidence array contains the explanatory prose but omits the numeric table excerpt that directly supports `68.320` and `0.000`.
- Treat p = 0.000 as a rounded display, not a literal probability of zero.

**Recommended disposition:** add the Table 3 numeric excerpt to the evidence array and retain the claim with the rounded-p-value qualification. Keep the stored record in `review` pending human approval.

### B03 — finding #6, Tables 7 and 8 (PDF p. 12)

**Evidence observed**

- The prose says the Carhart four-factor model “outperforms” FF3F in four of six portfolios.
- However, the Adjusted R-square rows in Tables 7 and 8 show the Carhart value higher in **all six** portfolios:

| Portfolio | FF3F Adjusted R² | Carhart Adjusted R² |
|---|---:|---:|
| SL | 0.2432 | 0.2436 |
| SM | 0.1071 | 0.1094 |
| SH | 0.4287 | 0.4462 |
| BL | 0.2005 | 0.2202 |
| BM | 0.0477 | 0.0769 |
| BH | 0.7197 | 0.7215 |

- The table's F-test p-values establish that each model regression is statistically significant; they do not establish that the difference between the two models is statistically significant.

**Assessment: not supported as currently phrased.**

- “Four of six” conflicts with the Adjusted R-square values if the claim is specifically about Adjusted R-square.
- The stated `p < 0.05` comparative significance is not supported by a paired or nested between-model test in the cited evidence.

**Recommended disposition:** rewrite as a source discrepancy: “The Adjusted R-square is slightly higher for Carhart in all six portfolios, while the article's narrative says four of six outperform; the paper does not report a significance test for the between-model difference.” Do not retain a comparative `p < 0.05` claim. This finding needs focused human review.

### B05 — finding #6, Table 1 (PDF p. 9)

**Evidence observed**

- The amortized liquidity measure estimates across M1–M5 are 2.636, 2.667, 2.571, 2.460 and 2.394.
- The corresponding t-statistics are 4.164, 4.208, 4.066, 4.151 and 4.227; each estimate is marked `***`.
- The table note defines `***` as significance at the 0.01 level, and the paragraph below the table states that the estimate is positive and statistically significant at 0.01.

**Assessment: supported; direct numeric evidence should be added.**

**Recommended disposition:** retain the liquidity-premium conclusion and estimate range, but add the Table 1 row and significance note to the evidence array. Keep the record in `review` pending human approval.

### B05 — finding #7, Table 5 (PDF p. 17)

**Evidence observed**

- The `After` main-effect estimates are 0.154***, 0.148*** and 0.164***, with t-statistics 4.577, 4.639 and 5.066.
- The difference-in-differences interaction `After × Treatment` is -0.060, -0.053 and -0.074, with t-statistics 1.176, 1.050 and 1.523 and no significance stars.
- The table note defines `After` as a post-April-2013 time dummy and `Treatment` as treatment-group membership.

**Assessment: the positive post-period coefficient is supported, but the causal UTP interpretation is overstated.**

- In a difference-in-differences model, the treatment-specific effect is the `After × Treatment` interaction, not the `After` main effect.
- The interaction is negative and statistically insignificant in all three columns. The cited table therefore does not establish a significant differential UTP effect on treated firms.

**Recommended disposition:** rewrite to distinguish the common post-period association from the treatment effect: “The After coefficient is positive and significant, but the treatment interaction is negative and insignificant; the table does not establish a significant UTP treatment effect.” This finding needs focused human review.

## Summary and actions

| Finding records | Assistant second-pass result | Next action |
|---|---|---|
| B01 #5–#6 | Core Wald inference supported; duplicate and rounded-p-value wording | Consolidate; human sign-off |
| B02 #3 | Supported; numeric table evidence missing from payload | Add direct excerpt; human sign-off |
| B03 #6 | Source prose and Adjusted R² table conflict; comparative significance unsupported | Correct/qualify; human sign-off |
| B05 #6 | Supported; numeric row missing from payload | Add direct excerpt; human sign-off |
| B05 #7 | After main effect misread as treatment effect | Rewrite causal interpretation; human sign-off |

- All six stored records remain `review`; no database row or analysis result was modified.
- This audit reduces the amount of work for a qualified reviewer, but does **not** satisfy the human-review release gate.
- The highest-risk review items are B03 #6 (internal source inconsistency) and B05 #7 (difference-in-differences interpretation), followed by the B01 duplicate/rounding issue.
- No v6.x analysis-engine heuristics were changed; the engine remains frozen.
