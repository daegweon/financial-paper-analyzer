# PaperSignal v6 ten-paper benchmark review — 2026-11-13

## Executive status

**All 10/10 papers have a latest completed analysis saved in Supabase using `finance-structured-v6`.**

- Primary model: Gemini 3.5 Flash-Lite (8 papers); fallback model: Gemini 3.6 Flash (2 papers).
- 31 structured empirical findings.
- 188 page-validated evidence excerpts.
- 9 of 10 papers contain a structured methodology; 8 have section-level methodology citations. B03 has variable-level citations but no section-level methodology quote.
- 9 of 10 papers contain at least one structured finding.
- 9 of 31 findings are flagged for researcher review by the preliminary numeric/significance screen.
- Conditional second pass: 8 attempted; 5 recovered findings, 2 reviewed existing findings, 1 found no supported findings; 2 papers did not need a second pass.
- Weighted lexical gold-fact coverage: **87.5%**.
- Mean claim-evidence coverage: **100%** for the structured claims that survived normalization.

**Interpretation warning:** 87.5% is an alias-matching screening metric, not semantic accuracy. The 100% claim-evidence coverage means each retained claim has a citation; it does not prove the citation entails the claim.

## Paper-level results

| Paper | Gold-fact screen | Findings | Flagged | Evidence | Methodology | Repair |
|---|---:|---:|---:|---:|---|---|
| B01 | 100.0% | 2 | 1 | 17 | Cited | recovered |
| B02 | 100.0% | 2 | 0 | 12 | Cited | not_needed |
| B03 | 100.0% | 5 | 2 | 15 | Variable-only | reviewed |
| B04 | 100.0% | 3 | 3 | 22 | Cited | recovered |
| B05 | 100.0% | 8 | 0 | 38 | Cited | reviewed |
| B06 | 75.0% | 1 | 1 | 13 | Cited | recovered |
| B07 | 62.5% | 2 | 0 | 13 | Cited | recovered |
| B08 | 100.0% | 4 | 2 | 32 | Cited | recovered |
| B09 | 100.0% | 0 | 0 | 14 | Cited | no_supported_findings |
| B10 | 37.5% | 4 | 0 | 12 | Missing | not_needed |

## V5 → V6 targeted reanalysis comparison

| Paper | Findings v5 → v6 | Methodology v5 → v6 | Evidence v5 → v6 |
|---|---:|---|---:|
| B01 | null → 2 | — → Present | null → 17 |
| B03 | null → 5 | — → Present | null → 15 |
| B04 | null → 3 | — → Present | null → 22 |
| B05 | null → 8 | — → Present | null → 38 |
| B08 | null → 4 | — → Present | null → 32 |
| B09 | null → 0 | — → Present | null → 14 |

## Material quality issues

### 1. B09: empirical findings still missing

The summary describes debt policy, working-capital financing policy and VOV relationships, and methodology is present. However, both primary and findings-only second pass produced zero findings with accepted page citations. This is the clearest remaining extraction defect.

### 2. B10: methodology not extracted

B10 has four findings and twelve evidence excerpts, but methodology remains `확인 불가`, with no methodology citation or variables. The second pass was not triggered because v6 only triggers findings repair when findings are missing or numeric checks flag an issue. The repair trigger should also cover missing methodology.

### 3. B01: panel observation count needs correction

The v6 result describes 4,950 daily periods as "4,950 observations" while the paper's panel dimensions are 12 portfolios × 4,950 periods = 59,400 portfolio-period observations. The period count and total panel observations must be separated.

### 4. B06: main asymmetric result is underrepresented

The summary describes asymmetric cointegration in the pre-crisis and full samples, but the structured findings array contains only the conventional symmetric PARDL non-cointegration result. A targeted second pass should recover the PNARDL asymmetric results and regime distinction.

### 5. B05: duplicated findings

B05 returns eight findings, but several are near-duplicates: the amortized liquidity premium coefficient is repeated, the 0.019 p.p. monthly premium is repeated, and the liquidity/holding-period correlations are repeated. A claim/evidence deduplication stage is needed.

### 6. B03 and B04: evidence and numeric review

B03's methodology section has no section-level citation; only two variables have direct citations. B04 has all three findings flagged by the preliminary numeric/significance screen. Their coefficient, p-value and model-fit statistics need table-level human review.

### 7. B08: numeric-screen false positives from Unicode minus

B08's PDF table uses the Unicode minus sign (`−`) in values such as `−0.0017` and `−0.0019`. The current numeric regex recognizes ASCII hyphen-minus but not Unicode minus, so it flags values that are visibly present in the cited table excerpts. The numeric tokenizer should normalize Unicode minus before extraction; the stored findings themselves need not be regenerated solely for this parser bug.

## Recommended next development: v6.1

1. Fix numeric tokenization to recognize Unicode minus signs.
2. Add a methodology-only repair schema and trigger it when methodology is missing or lacks any verified method/variable evidence.
3. Improve findings repair for B09 and B06 by selecting all relevant result/table/conclusion pages, not only the first limited subset.
4. Deduplicate repeated findings using normalized claim text plus overlapping page/quote fingerprints.
5. Add a panel-dimension consistency check to distinguish time periods, cross-sectional units and total observations.
6. Re-run only B01, B04, B06, B08, B09 and B10 after the targeted fixes, rather than consuming quota on all ten papers again.

## Final conclusion

v6 provides a consistent ten-paper baseline and materially improves B08's structured findings and several earlier extraction gaps. It is not yet ready to be described as fully accurate: B09 has no structured findings, B10 has no verified methodology, B01 has a panel-count ambiguity, B06 misses its principal asymmetric result, and B05 has duplicates. The next iteration should focus on these specific defects and a manual audit of material numeric claims.
