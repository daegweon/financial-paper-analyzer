"""Synthetic fixtures only: a passing fixture is not evidence of real release readiness."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.engine_quality_gate import evaluate, POLICY_PATH

POLICY = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
CANDIDATE = "b" * 40
FROZEN = POLICY["frozen_production"]["commit"]
DIGEST = "a" * 64
HISTORICAL = {"B01": 4, "B02": 6, "B03": 1, "B05": 2, "B09": 3, "B10": 2}


def synthetic_evidence():
    regression = [{"id": f"B{i:02d}", "sha256": f"{i:064x}", "pages": 20 if i < 10 else 29}
                  for i in range(1, 11)]
    heldout = [
        {"id": f"H{i}", "sha256": f"{i+20:064x}", "pages": 30, "lock_commit": "c" * 40,
         "locked_before_candidate": True}
        for i in (1, 2)
    ]
    reviewers = [{"reviewer_id": "synthetic-reviewer-a", "verdict": "corrected"},
                 {"reviewer_id": "synthetic-reviewer-b", "verdict": "corrected"}]
    legacy = [
        {"id": f"{paper}-{j}", "paper_id": paper, "source_sha256": f"{int(paper[1:]):064x}",
         "source_page": 3, "source_quote": "Synthetic source quote 0.12",
         "source_evidence_ref": "SYNTHETIC/ROW-3",
         "reviewers": reviewers, "resolved": True, "critical_unresolved": False,
         "source_confirmed_recovery": j == 0}
        for paper, n in HISTORICAL.items() for j in range(n)
    ]
    claims = [
        {"id": f"claim-{i}", "paper_id": "H1" if i == 0 else "H2" if i == 1 else "B01",
         "source_sha256": f"{21 if i == 0 else 22 if i == 1 else 1:064x}",
         "source_page": 3, "source_quote": "Synthetic source quote 0.12",
         "source_evidence_ref": "SYNTHETIC/ROW-3", "reviewers": reviewers, "supported": True,
         "critical_false_approval": False}
        for i in range(50)
    ]

    def records(commit):
        return [
            {"paper_sha256": item["sha256"], "repeat": repeat, "commit": commit,
             "model_path": "gemini-primary|gemini-fallback", "latency_ms": 1000,
             "cost_usd": 0.01, "peak_rss_mb": 100, "provider_attempts": 1,
             "prompt_tokens": 200, "output_tokens": 200, "success": True}
            for item in regression + heldout for repeat in (1, 2)
        ]

    return {
        "candidate_commit": CANDIDATE,
        "baseline": {
            "commit": FROZEN, "analysis_version": POLICY["frozen_production"]["analysis_version"],
            **{key: DIGEST for key in ("model_config_sha256", "prompt_sha256",
                                      "schema_sha256", "extraction_sha256")},
        },
        "corpus": {"regression": regression, "heldout": heldout},
        "human_review": {
            "legacy": legacy, "claims": claims, "critical_false_approvals": 0,
            "previously_approved_lost": 0, "legacy_quotes_retained": 346,
            "screen_passed_retained": 54, "answerable_recall_gain_pp": 0,
            "heldout_all_page_citations_verified": True,
        },
        "pipeline": {
            "baseline_runs": records(FROZEN), "candidate_runs": records(CANDIDATE),
            "cost_basis": "verified_public_rate", "service_failures_not_worse": True,
            "provider_recovery_not_worse": True, "backend_tests_pass": True,
            "frontend_build_pass": True,
        },
        "release_evidence": {
            key: {"passed": True, "commit": CANDIDATE, "evidence_ref": "SYNTHETIC-NOT-PROOF"}
            for key in POLICY["quality_gates"][3]["requirements"]
        },
    }


def test_missing_evidence_fails_all_gates():
    report = evaluate(POLICY, {})
    assert report["final_deploy_allowed"] is False
    assert all(item["status"] == "BLOCKED" for item in report["gates"].values())


def test_complete_synthetic_fixture_exercises_calculator_not_real_certification():
    report = evaluate(POLICY, synthetic_evidence())
    assert report["structural_checks_passed"] is True
    assert report["final_deploy_allowed"] is False
    assert report["next_action"] == "INDEPENDENT_SOURCE_REVIEW_AND_RELEASE_OWNER_SIGNOFF"
    assert report["human_claim_precision"] == 1.0
    assert report["pipeline_metrics"]["baseline_p95_ms"] == 1000
    assert report["record_type"] == "STRUCTURAL_CHECK_NOT_INDEPENDENT_CERTIFICATION"


def test_critical_false_approval_or_duplicate_reviewer_blocks():
    sample = synthetic_evidence()
    sample["human_review"]["critical_false_approvals"] = 1
    sample["human_review"]["claims"][0]["reviewers"] = [
        {"reviewer_id": "same-person", "verdict": "supported"},
        {"reviewer_id": "same-person", "verdict": "supported"},
    ]
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q1"]["status"] == "BLOCKED"
    assert report["final_deploy_allowed"] is False


def test_p95_cost_and_memory_regressions_all_block():
    sample = synthetic_evidence()
    for row in sample["pipeline"]["candidate_runs"]:
        row["latency_ms"] = 1060
        row["cost_usd"] = .011
        row["peak_rss_mb"] = 111
    report = evaluate(POLICY, sample)
    failures = " ".join(report["gates"]["Q2"]["failures"])
    assert "p95" in failures and "cost" in failures and "RSS" in failures
    assert report["final_deploy_allowed"] is False


def test_unlocked_heldout_and_missing_external_smtp_evidence_block():
    sample = synthetic_evidence()
    sample["corpus"]["heldout"][0]["locked_before_candidate"] = False
    sample["release_evidence"]["external_smtp_confirmed"]["passed"] = False
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q0"]["status"] == "BLOCKED"
    assert report["gates"]["P0"]["status"] == "BLOCKED"


def test_false_boolean_is_not_accepted_as_measured_zero():
    sample = synthetic_evidence()
    sample["human_review"]["critical_false_approvals"] = False
    sample["human_review"]["previously_approved_lost"] = False
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q1"]["status"] == "BLOCKED"


def test_review_disagreement_requires_resolution_record():
    sample = synthetic_evidence()
    sample["human_review"]["legacy"][0]["source_confirmed_recovery"] = False
    sample["human_review"]["legacy"][0]["reviewers"] = [
        {"reviewer_id": "independent-a", "verdict": "supported"},
        {"reviewer_id": "independent-b", "verdict": "rejected"},
    ]
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q0"]["status"] == "BLOCKED"
    sample["human_review"]["legacy"][0]["disagreement_resolution_ref"] = "external-review-record"
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q0"]["status"] == "PASS"


def test_unmatched_source_sha_and_missing_page_anchor_block_accuracy():
    sample = synthetic_evidence()
    sample["human_review"]["claims"][0]["source_sha256"] = "d" * 64
    sample["human_review"]["legacy"][0]["source_page"] = 99999
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q1"]["status"] == "BLOCKED"
    assert report["gates"]["Q0"]["status"] == "BLOCKED"


def test_disallowed_heldout_page_count_blocks_q0():
    sample = synthetic_evidence()
    sample["corpus"]["heldout"][0]["pages"] = 0
    report = evaluate(POLICY, sample)
    assert report["gates"]["Q0"]["status"] == "BLOCKED"


def test_no_automatic_deployment_permission_even_for_synthetic_green_evidence():
    report = evaluate(POLICY, synthetic_evidence())
    assert all(gate["status"] == "PASS" for gate in report["gates"].values())
    assert report["structural_checks_passed"] is True
    assert report["final_deploy_allowed"] is False
