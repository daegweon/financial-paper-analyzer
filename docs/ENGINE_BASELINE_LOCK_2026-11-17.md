# PaperSignal v6.4.2 baseline and Held-out lock — corrected 2026-11-17

## Immutable production baseline

- Production branch: \`feat/research-workspace-mvp\`
- Frozen production SHA: \`8cd5e37ee8eab3bf4b726b75af89e410ab48396e\`
- Analysis version: \`finance-structured-v6.4.2\`
- Production dependency pin: \`PyMuPDF==1.26.3\`
- Held-out lock commit: \`149311ec2993cac3bd410c10ac7feb202d582fc7\`

## Exact held-out PDF bytes

The two PDFs uploaded by the user were reopened as binary files, hashed with SHA-256 over the original unmodified bytes, and checked with PyMuPDF:

| ID | Pages | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| H01 | 40 | 2,521,298 | \`816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127\` |
| H02 | 30 | 5,223,546 | \`d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283\` |

Both exact hashes and page counts are stored in \`benchmark/heldout_preregistration_2026-11-17.json\`. The lock commit is the actual Git ancestor used for release-eligible candidate work.

## Corrected candidate-branch chronology

A previous branch, \`experiment/engine-quality-v6-4-2-heldout-locked\` (PR #5), was initially described as descending from the lock. GitHub's compare API proved otherwise: comparing lock commit to that branch returned \`diverged\`, 56 commits ahead / 18 behind, with merge base equal to frozen production SHA \`8cd5e37\`. It is **ineligible and superseded**. Do not merge PR #5.

The clean branch is:

- Branch: \`experiment/engine-quality-v6-4-2-heldout-clean\`
- Base commit: \`325fb7e5bda6dd05cf4888fd658018a2d8e4abbf\`
- The base commit is a descendant of the lock commit (16 documentation/manifest commits after lock; no production application-code changes).
- First candidate code commit: \`7dd13343f44702369b8a1415c750d5fdf08371f7\`, parent \`325fb7e5bda6dd05cf4888fd658018a2d8e4abbf\`, timestamp 2026-11-16 21:43:36 UTC.
- Lock commit timestamp: 2026-11-16 21:11:16 UTC.
- Git ancestry therefore establishes that the lock commit precedes and is an ancestor of the clean candidate's first code commit.

This corrected chronology replaces earlier claims that PR #5 was release-eligible.

## Frozen source and model fingerprints

The accompanying JSON records the production API/Worker/requirements/Dockerfile source fingerprints and separate prompt, schema, extraction-configuration and model-configuration hashes. Runtime model names from Railway Worker logs:

- Primary: \`gemini-3.5-flash-lite\`, thinking \`minimal\`
- Fallback: \`gemini-3.6-flash\`, thinking \`low\`

The candidate adds only job/call-correlated telemetry and redacts raw provider error bodies from application logs. The analysis version, prompt, schema, extraction logic, Gemini request body, model ordering, retry policy and user result schema are unchanged. Candidate source SHA-256 should be recaptured with \`benchmark/capture_engine_fingerprint.py\` in a local clone before a full baseline run.

## Local extraction-only preflight

The exact production \`extract_pages\` logic was reproduced locally against the two locked PDFs. The isolated runtime has PyMuPDF 1.26.7; production is pinned to 1.26.3. Both PDFs yielded all pages with text, but these results are not a production-version measurement and are **not Q2 evidence**.

| ID | Pages scanned | Empty text pages | Extracted chars | Five-run median |
| --- | ---: | ---: | ---: | ---: |
| H01 | 40/40 | 0 | 111,448 | 212.735 ms |
| H02 | 30/30 | 0 | 62,589 | 84.105 ms |

The exact per-run times and extracted-text SHA-256 values are in \`benchmark/baseline_lock_v6.4.2_2026-11-17.json\`. No Gemini calls were made. Earlier local preflight figures are superseded by this reproducible run; do not combine measurements from different code paths.

## Still blocked

- **Q0:** H01/H02 are locked, but original B01–B10 PDF binary hashes and full frozen production baseline are missing; pinned runtime measurement is not yet available.
- **Q1:** 18 actual two-reviewer historical adjudications and 50+ independently reviewed material claims remain outstanding.
- **Q2:** No H01/H02 Gemini full-pipeline baseline or paired candidate run; billable cost, full latency and peak RSS remain unmeasured. Historical production logs include 503/429 failures on other jobs.
- **P0:** two-account RLS/auth/upload, external SMTP, production release and rollback verification remain outstanding.

GitHub Actions still fails with \`startup_failure\` before creating jobs. No repository CI test result is claimed. No production deployment, database write or user-data change occurred. \`final_deploy_allowed=false\`.
