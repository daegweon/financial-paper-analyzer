# PaperSignal — First source-first visual draft audit

Date: 2026-11-16 (Asia/Seoul)
Decision: **Do not promote the page-selected Camelot path. A shared within-page omission is now demonstrated.**

## What was actually inspected

The assistant viewed source-derived raster crops from the exact locked PDFs BEFORE opening parser candidates: B01 PDF page 18, Table 2; B10 PDF page 12, Table 5. Native PDF word geometry then located the labels and numbers. No OCR, model-provider call or publisher replacement PDF was used. These are assistant visual drafts, NOT independently human-reviewed gold. B02/B09 received text-caption inventory checks only; their source cells were not visually audited in this checkpoint.

B01 Table 2 has variables in columns and Parameter / Std. Dev. / t-stat in rows. The printed `Std. Dev.` label is preserved as `reported_std_dev`; no conversion to standard error or new p-value/star claim is allowed. Five parameter targets, each with two companion statistics, cover 15 numeric cells.

B10 Table 5 has return-constraint rows and separate realized-volatility / Sharpe columns. At the 3% row, 0.20 is the volatility value and 0.15 is the Sharpe value. This is a source-based wrong-column rejection control, NOT a claim that the production engine made that specific mistake. Ten primary targets cover five volatility and five Sharpe cells. No significance interpretation was added.

Together: 15 primary target bundles / 25 numeric cells. Expected exact text is stored as normalization digests plus source/render hashes and source regions, not raw page images or complete source matrices. Digests are not encryption or proof of human review.

## Actual frozen-output audit

Each target was compared against the FOUR previously saved output variants: all-page and selected-page Stream, two repeats each. These are 60 checks of frozen candidates, NOT 60 independent targets, new parser runs or a new live AI analysis.

| Source crop | Unique primary targets | All-page output, each repeat | Selected-page output, each repeat |
|---|---:|---:|---:|
| B01 p18 Table 2 | 5 (15 numeric cells with companions) | 0 agreement; 5 missing | 0 agreement; 5 missing |
| B10 p12 Table 5 | 10 | 10 agreement | 10 agreement |

All source anchors resolved and inspected crop hashes reproduced. Across four variants: 40 agreement checks, 20 missing checks, zero unassessed checks. This is a small, purposively selected assistant-draft diagnostic, NOT general accuracy, precision/recall or human certification.

Inspection of the original B01 candidate payload confirmed that page 18 contained only a detected Table 4 region, around top-left y386–498 PDF points; Table 2's parameter row is around y135–144. The omission is inside an already selected page. Increasing the page cap alone cannot recover this observed failure. Previously reported all-versus-selected matrix equality was true, but both variants shared the same omission; equality cannot establish source completeness.

## Page-selection diagnostic

All 86 pages of the four priority PDFs were scanned via native source text blocks/lines. The same standalone-caption convention was applied independently of candidate matrices; it is NOT an independent visual table census.

| Paper | Source pages | Selected pages | Caption instances, including continuations/appendices | Caption pages outside selection |
|---|---:|---:|---:|---:|
| B01 | 31 | 7 | 11 | 0 |
| B02 | 20 | 6 | 7 | 0 |
| B09 | 16 | 5 | 5 | 0 |
| B10 | 19 | 5 | 9 | 0 |

All 32 caption instances fell within the 23 selected pages. Captionless/image tables and the 63 excluded pages have NOT all been visually checked; recall remains unknown. Prose/figure negative controls remain unadjudicated. Even complete caption-page inclusion would not resolve B01's within-page omission.

## Implementation and tests

Added `benchmark/draft_cell_audit.py`, `draft_cell_audit_run.py`, `visual_drafts_20261116.json`, and `backend/tests/test_draft_cell_audit.py`. Source identity, inspected-render identity and native source anchors must match before candidate comparison. Exact signs, stars, precision, row/column relations and companion label semantics are checked. Conflicting candidates are not chosen by parser confidence. Assistant drafts always return `human_reviewed=false`, `certified_accuracy=null`, and `promotion_eligible=false`. Existing independent-human-review gates and production validators remain unchanged.

Local synthetic rejection suite: **37 passed in 0.08s**. Cases cover transposed tables, same number in wrong columns, sign/star/rounding changes, wrong row/column, Std. Dev. versus standard-error label mismatch, wrong source/page/render, overlapping conflicting cells and attempted reviewer-status substitution. The isolated Railway image's `RUN pytest -q` build gate completed successfully; its exact terminal count was not recovered from the available log excerpt, so this report does not invent a new total. Live E2E and frontend build were not run.

## Containment and audit trail

Implementation commit: da3f12dd108e2f44e53f7fdf55b13a224b7c4fef on experiment/pdf-table-engines. Compare against 04cde88 shows only four added experimental/test files; no production code/dependencies/config change.

Execution-only branch experiment/visual-draft-audit-runner is pinned to fb5895d28336c9ed9da6c4d32f6bb674b5e649fa. NEVER merge runner railway.toml into production. Deployment b61322f7-edf3-4d71-a830-a4884c09862e finished SUCCESS with zero running replicas and no pending work. Run: visual-draft-audit-c569a95eb0f44b608a608493de8a9910; four documents completed, zero errors, four NEW private audit JSON artifacts. Prior raw artifacts remain untouched.

Original data unchanged: 14 papers, 103 analyses, 102 completed / 28 failed historical jobs, 14 private PDF objects. Private JSON artifact count is now 18 (was 14). API deployment 17c9134b-f49c-4358-a879-7ca77b55b936 and Worker dc501061-d434-454a-bc7d-4658b991a2f1 remain online and unchanged. No model call, queue claim, schema/RLS change, public endpoint or cron was added.

Temporary source-access runners used recipient-encrypted payloads and no database/Storage writes; credentials stayed server-side and no raw PDF/image was committed or publicly served. First static-page exports missed target hints and were not labelled. Source-native location corrected them before these two drafts were recorded. Execution-only export branches must not be merged into production.

## Next decision

Keep production unchanged. The next targeted candidate is caption/geometry-bounded TABLE-REGION recovery on multi-table pages, rather than more page-cap tuning. Test it against these frozen source drafts and untouched controls, without using numerical answers to locate regions. Complete B02/B09 and remaining-table visual audits, independent human adjudication, negative controls, full-pipeline and held-out quality/resource/cost gates before any promotion. All 18 historical review-required findings remain unapproved. No overall engine improvement or global performance maximum is claimed.
