# PaperSignal analysis engine v6.2

## Goal

v6.2 makes sample and statistical verification conditional on the paper's research design. It prevents the system from applying balanced-panel arithmetic to unbalanced panels or non-panel studies, preserves contradictory source counts instead of silently choosing one, and uses regression-table context when checking statistical significance.

## Research-design classification

The model returns an evidence-backed `study_design_type`:

- `balanced_panel`
- `unbalanced_panel`
- `repeated_cross_section`
- `time_series`
- `cross_sectional`
- `portfolio_optimization`
- `other`
- `unknown`

It separately reports `panel_balance` and page-level evidence. If the design classification itself is not supported by a page quote, the normalizer downgrades it to `unknown`.

## Typed sample dimensions

Panel dimensions now use integer fields:

- `cross_sectional_units_count`
- `time_periods_count`
- `reported_total_observations_count`

Unknown values are represented by 0 in the model response and normalized to null. Calendar-year ranges are not parsed as observation counts.

The model also returns `sample_count_reports`, a list of source-level assertions with:
- metric: cross-sectional units, time periods, total observations, subsample observations, or other;
- label: e.g. overall, pre-crisis, post-crisis;
- integer count;
- section name;
- exact page evidence.

A count report is retained only when its numeric value appears in its validated page excerpt. Reports with the same metric/label but different values are preserved and surfaced as `source_conflicts`.

## Design-aware sample audit

- **Balanced panel:** N×T is calculated only when both dimensions are evidence-backed. It is compared with a source-reported total only when one exists.
- **Unbalanced panel:** no N×T total is calculated. The reported observed count is preserved as-is.
- **Repeated cross-section:** N×T is not applied because the same cross-sectional units need not recur.
- **Time series / cross-section / portfolio optimization:** panel multiplication is not applicable.
- **Source conflict:** inconsistent counts across sections are displayed with their source citations. The engine does not select or average them.

This avoids false mismatches such as multiplying 3,856 firms by 81 quarters in a study whose ESG coverage is unbalanced, and avoids inventing a pseudo-panel total for a portfolio optimization paper.

## Table-aware statistical significance

Each finding can carry:
- `table_reference`
- `model_or_column`
- `significance_legend_evidence`

The numeric screen now:
- checks signed coefficient estimates against cited-page values;
- treats significance levels separately from effect-size numbers;
- compares explicit p-values when both source and claim provide them;
- checks a stated significance threshold against a directly stated threshold in the result quote;
- maps `*`, `**`, and `***` to significance levels only when the table note is separately cited;
- returns unknown rather than a false failure when a star legend or column context is missing.

A missing table note is not evidence that a coefficient is insignificant. It is a reason to request researcher review.

## Summary-to-findings consistency

The engine screens whether:
- a summary describes empirical results while the structured findings list is empty;
- numerical claims in the summary appear in the structured findings or methodology fields.

A mismatch can trigger the findings-only second pass. The check is deterministic and does not claim semantic entailment.

## Conditional second passes and Gemini quota

- Methodology-only repair runs when field-level method evidence or the estimation strategy is missing, the study-design classification is unknown, or a balanced-panel consistency check requires review.
- Findings-only repair runs when findings are missing, a summary/findings mismatch is detected, or a concrete numeric/significance contradiction is found.
- A source-level count conflict is preserved as a conflict; the model is not repeatedly called to choose one number.
- Papers that pass all relevant checks do not incur extra model calls.
- Gemini primary/fallback models remain configured as before. The schemas are provider-neutral for a future OpenAI switch.

## Compatibility

- Analysis version: `finance-structured-v6.2`
- Existing v3/v4/v5/v6/v6.1 records are unchanged.
- New analyses are tagged v6.2.
- No Supabase schema migration is required. Typed sample, table-context and verification metadata are stored in the existing JSON result.
- The frontend displays design classification, source-count conflicts, table significance citations and summary consistency.

## Limitations

These are screening and triage checks, not formal statistical verification. The engine cannot reliably reconstruct every table's column alignment, detect all sample-selection rules, infer unbalanced-panel missingness mechanisms, or prove that a citation semantically entails a claim. Researchers must inspect material coefficient estimates, units, p-values, significance legends, identification assumptions and contradictory source reports in the publisher PDF.
