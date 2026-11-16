# PaperSignal Engine Release Gate — Evidence Specification

The Q0/Q1/Q2/P0 thresholds are fixed in the companion engine_release_gates_2026-11-17.json policy file. This evaluator is deliberately fail-closed. Missing values, provider 503 without completed comparisons, missing human reviews, and absent release proofs must NOT be presented as success.

Execute from the repository root:

    python -m benchmark.engine_quality_gate --evidence path/to/measured-evidence.json

An exit code of 1 blocks release. Exit 0 only means the input JSON satisfies the declared *structural checks*, not that its claims are true. A release owner MUST independently authenticate human reviewer identities, gold PDF row/page/column anchors, corpus SHA locks and their Git chronology, provider bills, two-user account isolation and live SMTP, and deployment/rollback logs. Never manufacture records for a passing result. Tests use explicitly synthetic fixtures that are not release evidence.

The evidence JSON must include the following objects:

- candidate_commit: a full Git SHA different from the frozen v6.4.2 production SHA
- baseline: frozen commit and analysis_version plus 64-character SHA-256 locks for model_config, prompt, schema, extraction settings, each suffixed "_sha256"
- corpus.regression: 10 original papers B01-B10, each with id, sha256 and pages, totaling 209 pages
- corpus.heldout: at least 2 distinct previously unused papers, each with id, sha256, lock_commit, locked_before_candidate=true; verify original lock Git commit precedes candidate tuning
- human_review.legacy: all 18 known review-required items with unique id, paper_id, source_sha256, resolved=true, critical_unresolved=false and 2 independent reviewer records with reviewer_id/verdict; source_confirmed_recovery is allowed only when both reviewers independently support or correct the claim
- human_review.claims: at least 50 distinct material source-checked claims, each with id, paper_id, source_sha256, supported, critical_false_approval=false and two independent reviewer records, including claims for each held-out paper
- human_review aggregates: critical_false_approvals, previously_approved_lost, legacy_quotes_retained, screen_passed_retained, answerable_recall_gain_pp, heldout_all_page_citations_verified
- pipeline.baseline_runs and pipeline.candidate_runs: matched records for *each* regression and held-out paper, at least repeats 1 and 2, same model_path. Each run: paper_sha256, repeat, commit, model_path, latency_ms (whole upload-to-save), cost_usd, peak_rss_mb, provider_attempts, prompt_tokens, output_tokens, success=true
- pipeline flags: cost_basis=provider_billable or verified_public_rate; service_failures_not_worse, provider_recovery_not_worse, backend_tests_pass and frontend_build_pass all true
- release_evidence: each P0 Boolean key from policy maps to a record with passed=true, commit=candidate SHA and a nonempty independently verifiable evidence_ref

P95 uses nearest-rank method across per-job full-pipeline latencies. Total provider cost and peak process RSS must meet policy limits. Human gold accuracy and any human reviewer assertions remain unverifiable by software alone.

No service should automatically promote a release solely from this evaluator's return code. Check real external evidence and deployment SHA before production promotion.

**Source-identity hardening:** each human_review legacy/claim entry must match `source_sha256` to `corpus.regression` / `corpus.heldout` for its `paper_id`, and have `source_page` (positive, within PDF page bounds), nonempty exact `source_quote` (8+ characters), and nonempty `source_evidence_ref` pointing to the reviewer-accessible source row/column evidence. Held-out entries also require their actual `pages` count. This checks structure only; the PDF and evidence link must be inspected by real reviewers.
