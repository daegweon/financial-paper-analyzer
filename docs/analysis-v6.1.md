# PaperSignal analysis engine v6.1

## Purpose

v6.1 is a precision-validation release based on the ten-paper v6 benchmark. It addresses false numeric flags, incomplete methodology extraction, missing empirical findings, repeated findings, and panel sample-count ambiguity.

## Pipeline

1. **Primary structured analysis** — extract bibliographic details, research question, methodology, panel dimensions, empirical findings, robustness checks and limitations.
2. **Field-level evidence validation** — design, sample, period, data sources, empirical strategy, identification strategy and equations each require their own page citation. A general methodology quote no longer automatically supports every methodology field.
3. **Numeric normalization and screening** — normalize Unicode minus signs, full-width punctuation, decimal formats and thousands separators before comparing claimed numbers with cited-page text. Date-range dashes are not interpreted as negative signs.
4. **Conditional methodology repair** — if design/sample/period evidence is missing or panel dimensions conflict, run a methodology-only second pass on method/data/sample/variable pages.
5. **Conditional findings repair** — if findings are absent or numeric screening flags a mismatch, run a findings-only second pass on a wider set of abstract/results/table/discussion/conclusion pages.
6. **Finding deduplication** — collapse repeated claims that share page-quote fingerprints and compatible numeric estimates while preserving distinct estimates and outcomes.
7. **Panel-dimension audit** — distinguish cross-sectional units, time periods, reported total observations and calculated panel observations. Reported totals are never silently replaced with calculated values.
8. **Summary audit and reconstruction** — numeric claims in the summary are screened against cited pages. If the model summary does not pass, reconstruct it only from individually evidenced methodology fields and findings that pass the preliminary numeric screen.
9. **Persistence and UI** — persist repair status, models used, duplicate counts, summary verification, panel consistency and finding-level numeric screening in the existing JSON result. No database migration is required.

## Methodology evidence

The methodology schema now requires separate evidence arrays:
- `design_evidence`
- `sample_evidence`
- `period_evidence`
- `data_sources_evidence`
- `empirical_strategy_evidence`
- `identification_strategy_evidence`
- `equations_evidence`

A field without its own validated citation is displayed as unavailable, even if another methodology field has a citation. Individually cited variables are retained independently.

## Panel dimensions

For panel data, the model extracts:
- `cross_sectional_units` — e.g. firms, banks or portfolios;
- `time_periods` — number of daily/monthly/quarterly periods;
- `reported_total_observations` — only the total explicitly reported in the paper;
- `observation_frequency` and `observation_unit`.

The backend separately calculates cross-sectional units × time periods. If this differs from the paper's reported total, the result is flagged for researcher review rather than silently corrected.

## Numeric screen limitations

The numeric screen compares tokens appearing in the claim, estimate and significance field with numbers on the cited page. It also checks an explicitly signed estimate against the stated positive/negative direction and screens significance wording.

This is a deterministic triage heuristic, not a semantic table parser. It cannot reliably infer table-column alignment, distinguish all model specifications, validate units, interpret standard errors or prove causal identification. A `screen_passed` result means only that the heuristic found no mismatch; researchers must still inspect material claims against the cited table and surrounding text.

## Conditional second passes and quota

- Methodology repair runs only when field-level method evidence is missing, design/sample/period is unavailable, or panel dimensions conflict.
- Findings repair runs only when no findings survive citation validation or a finding has a numeric/significance review flag.
- Normal papers that pass both checks incur no additional model call.
- Gemini uses the configured primary/fallback model pair. The same structured schemas are provider-neutral for a future OpenAI switch.

The wider page selectors prioritize the abstract, methodology/data/sample pages, regression tables, results, discussion and conclusion. The backend still limits PDF text extraction to its configured maximum scanned pages.

## Version and compatibility

- Analysis version: `finance-structured-v6.1`
- Existing v3/v4/v5/v6 records remain unchanged.
- New analyses are tagged v6.1.
- No Supabase schema migration is required; verification metadata is stored in the existing JSON result.
