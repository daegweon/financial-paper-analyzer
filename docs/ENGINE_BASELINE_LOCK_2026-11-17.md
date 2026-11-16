# PaperSignal v6.4.2 baseline lock — 2026-11-17

## Immutable baseline

- Frozen production branch: `feat/research-workspace-mvp`
- Frozen production SHA: `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`
- Analysis version: `finance-structured-v6.4.2`
- Production dependency pin: `PyMuPDF==1.26.3`
- New release candidate branch: `experiment/engine-quality-v6-4-2-heldout-locked`, created directly from the frozen SHA after the held-out binary lock commit.
- Held-out lock commit: `149311ec2993cac3bd410c10ac7feb202d582fc7`

## Held-out PDFs

The two user-uploaded original publisher PDFs were checked as exact bytes with PyMuPDF:
- H01: 40 pages, 2,521,298 bytes, SHA-256 `816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127`.
- H02: 30 pages, 5,223,546 bytes, SHA-256 `d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283`.

Both are committed in the pre-registration manifest. The first commit with both exact hashes is the lock commit above; a follow-up manifest commit records its SHA.

## Source fingerprints

The JSON file beside this document records SHA-256 and Git blob SHA-1 for the API, Worker, requirements and Dockerfile, plus separate prompt/schema/extraction/model-config fingerprints. Secret values are excluded. Runtime model names are corroborated by Worker logs: Gemini primary `gemini-3.5-flash-lite`, fallback `gemini-3.6-flash`.

## Local extraction preflight — not a production benchmark

The uploaded PDFs were passed through the production extraction algorithm locally. This environment had PyMuPDF 1.26.7, while production pins 1.26.3. It extracted 40/40 pages and 30/30 pages with no empty text pages. Five-run local median extraction times were H01 249.978 ms and H02 107.494 ms. These are not production timings and must not be used to claim Q2 success. Exact per-paper text hashes and run details are in `baseline_lock_v6.4.2_2026-11-17.json`.

## Still blocked

- Q0: original B01-B10 PDF byte hashes are not yet locked, and the exact production v6.4.2 full-pipeline baseline is incomplete.
- Q1: 18 actual two-reviewer legacy adjudications and 50+ independently reviewed material claims are still missing.
- Q2: no Gemini full-pipeline H01/H02 baseline has been run in the pinned production runtime; billable cost, full latency and peak RSS remain unmeasured. Railway logs show previous 503/429 failures on other jobs.
- P0: two-account RLS/auth/upload, external SMTP and final release/rollback checks remain outstanding.

No engine code was modified in this baseline step. No production deployment or database write was performed. Do not tune until baseline and source locks are complete; do not mark any gate PASS based on local extraction preflight.
