import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.diagnose import diagnose, diagnose_finding


def test_numeric_estimate_must_appear_in_direct_evidence_quote():
    issues = diagnose_finding({
        "id": "B01-F01",
        "claim": "Coefficient is 0.9548",
        "estimate": "0.9548",
        "statistical_significance": "5%",
        "evidence": [{"page": 5, "quote": "The coefficient is positive and significant."}],
    })
    codes = {x["code"] for x in issues}
    assert "numeric_claim_not_in_direct_quote" in codes
    assert "missing_direct_evidence" not in codes


def test_page_quote_mismatch_is_flagged_and_never_approved():
    report = diagnose(
        [{"paper_id": "B02", "analysis": {"findings": [
            {"claim": "Claim", "estimate": "-0.12", "evidence": [{"page": 3, "quote": "not on page"}]},
            {"claim": "No evidence"},
        ]}}],
        {"B02": {"3": "different original text"}},
    )
    assert report["issue_counts"]["quote_not_found_on_page"] == 1
    assert report["issue_counts"]["missing_direct_evidence"] == 1
    assert "does not establish" in report["warning"]


def test_structural_numbers_are_not_scored_without_numeric_result_fields():
    issues = diagnose_finding({
        "claim": "Four out of six portfolios perform better",
        "evidence": [{"page": 4, "quote": "Four out of six portfolios perform better."}],
    })
    assert not any(x["code"] == "numeric_claim_not_in_direct_quote" for x in issues)
