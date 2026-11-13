# PaperSignal analysis engine v6

## Goal

v6 separates initial paper extraction from targeted empirical-results verification. It is designed to reduce empty findings arrays, avoid losing a summary when the model's top-level summary citation is missing, and flag numerical inconsistencies for researcher review.

## Pipeline

1. **Primary structured analysis** — the configured provider extracts bibliographic metadata, research question, hypotheses, methodology, findings, robustness checks, limitations, implications and page citations.
2. **Citation normalization** — page quotes are matched after Unicode typography and whitespace normalization, while the stored quote is sliced from the original extracted page text.
3. **Deterministic numeric screen** — each finding's numeric tokens, estimate sign and reported significance are compared with the text of its cited PDF pages.
4. **Conditional second pass** — only if findings are empty or a numeric/significance screen flags an issue, the model receives a focused prompt containing the abstract and the most results-relevant pages. It returns a findings-only JSON schema. Supported first-pass findings are retained and merged with validated repair findings.
5. **Evidence-based summary fallback** — if the model's own summary citation cannot be validated, the API composes a short summary from already validated methodology and findings, with those original citations attached.
6. **Persist and display** — the same Supabase schema is used; the frontend shows the numeric screen result and whether a second pass was attempted.

## Conditional second-pass behavior

- No extra model request is made when the primary findings pass the numeric screen.
- A findings-only request is made when no findings survive citation validation or when numeric/significance checks need review.
- The findings-only prompt prioritizes the abstract, results, regression tables, discussion and conclusion pages.
- The repair response uses the same evidence validation as the primary response. Unsupported or unquoted claims are not accepted.
- Gemini uses the configured primary and fallback models. OpenAI is kept compatible with the same findings-only schema for a future provider switch.

## Numeric screening fields

Each finding contains a `verification` object:

- `status`: `screen_passed` or `review`
- `numeric_supported`: whether numeric tokens in the claim, estimate and significance field appear on cited pages
- `unsupported_numeric_tokens`: numeric tokens not found on the cited pages
- `direction_consistent`: a preliminary sign check when the estimate is an explicitly signed numeric value
- `significance_supported`: whether the cited page supports the stated significance level/wording when it is explicit
- `method`: `cited_page_numeric_screen`

**Important limitation:** `screen_passed` means only that these deterministic checks did not find a mismatch. It is not a semantic proof that the cited text entails the claim, and it does not replace a researcher's review of table columns, standard errors, units, coefficient interpretation, p-values, multiple testing, or causal identification.

## Summary fallback

The fallback uses only already validated methodology-section evidence and validated finding claims. It does not invent an abstract or infer results from unsupported text. If neither section has validated evidence, the fallback remains an explicit "source evidence unavailable" message.

## Version and compatibility

- Analysis version: `finance-structured-v6`
- No database migration is required.
- Existing v3/v4/v5 analysis rows remain unchanged.
- New analyses are tagged v6.
- The provider abstraction and findings-only schema are shared by Gemini and the future OpenAI provider.
