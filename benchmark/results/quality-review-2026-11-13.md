# PaperSignal benchmark quality review — 2026-11-13

## Executive result

- All 10/10 benchmark papers have a completed Gemini analysis saved in Supabase.
- 165 unique evidence excerpts were stored after the backend page-level exact-text validator accepted them.
- Weighted gold-fact alias coverage screening: **74.25%**.
- Models: {"gemini-3.5-flash-lite":8,"gemini-3.6-flash":2}.
- Analysis schema versions: {"finance-structured-v3":4,"finance-structured-v4":6}.

**Important:** 74.25% is a lexical screening score, not a claim that the model is 74.25% accurate. Alias matching can undercount correct paraphrases and can overcount terms that appear in the wrong context. The backend checks that a quote exists on the cited extracted PDF page, but this alone does not prove that the quote semantically supports the associated claim.

## Cross-paper findings

1. **Structured findings are missing in three analyses:** B01, B04, and B08 have no entries in the `findings` array even though their summaries describe substantive empirical results.
2. **Methodology sections are incomplete in three analyses:** B03, B05, and B09 were normalized to `확인 불가` because no methodology evidence passed validation.
3. **Language consistency:** B05's summary and much of its analysis are in English despite the Korean output requirement.
4. **Benchmark version consistency:** B01–B04 use `finance-structured-v3`; B05–B10 use `finance-structured-v4`. Scores are therefore not a fully controlled comparison of one fixed prompt/schema version.
5. **Claim-to-quote semantic support needs human review:** for example, B10 includes company names in an implication claim while its attached quote speaks more generally about stock characteristics. The cited page may contain additional context, but the quote shown does not itself substantiate those names.

## Paper-level review

| Paper | Alias coverage | Verified excerpts | Findings | Methodology |
|---|---:|---:|---:|---|
| B01 | 58.3% | 13 | 0 | Present |
| B02 | 100.0% | 15 | 2 | Present |
| B03 | 50.0% | 10 | 2 | Incomplete |
| B04 | 75.0% | 11 | 0 | Present |
| B05 | 75.0% | 20 | 3 | Incomplete |
| B06 | 75.0% | 13 | 1 | Present |
| B07 | 75.0% | 36 | 6 | Present |
| B08 | 80.0% | 15 | 0 | Present |
| B09 | 66.7% | 10 | 1 | Incomplete |
| B10 | 87.5% | 22 | 3 | Present |

## Recommended improvements

1. Normalize PDF typography during citation matching (Unicode ligatures, dashes, and whitespace) while storing the matched excerpt from the actual extracted page text. This may recover legitimate methodology/findings citations currently rejected by strict string matching.
2. Make the prompt require concise, separately cited empirical findings and distinguish hypotheses from realized results.
3. Add a post-generation quality gate: warn or request a focused second pass when methodology is empty or when a substantive summary exists but the findings array is empty.
4. Re-run B01–B04 with the current v4 engine if a version-controlled comparison is needed. This consumes additional Gemini quota.
5. Human-review all material numeric results and the semantic relationship between every claim and its cited passage before using the benchmark score as a product-quality claim.

## Scope

This is the first automated screening report, not the final expert-validated benchmark. Exact PDF page text is available to the backend validator at analysis time; this report uses the stored validated-evidence counts. A separate human audit against all ten publisher PDFs remains outstanding.
