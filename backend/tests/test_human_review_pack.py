"""Tests use wholly synthetic paper extracts; they are not human gold."""
from hashlib import sha256
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.human_review_pack import EXPECTED, build_review_pack


def sample():
    rows = []
    for i in range(1, 11):
        paper_id = f"B{i:02d}"
        findings = [
            {
                "claim": f"Claim {j}: coefficient -0.12",
                "estimate": "-0.12",
                "direction": "negative",
                "table_reference": "Table 2",
                "model_or_column": "Specification 1",
                "evidence": [{"page": 3, "quote": "coefficient -0.12"}],
                "significance_legend_evidence": [{"page": 3, "quote": "*** p < 0.01"}],
                "verification": {"status": "review"},
            }
            for j in range(EXPECTED.get(paper_id, 0))
        ]
        rows.append({"paper_id": paper_id, "analysis": {
            "analysis_version": "finance-structured-v6.3.9", "findings": findings,
        }})
    return {"results": rows}


def test_frozen_18_cases_are_unapproved_and_individually_fingerprinted():
    pack = build_review_pack(sample())
    assert pack["count"] == 18
    assert pack["counts"] == EXPECTED
    assert len({x["case_id"] for x in pack["cases"]}) == 18
    assert all(x["status"] == "UNREVIEWED" for x in pack["cases"])
    assert all(x["human_reviews"] == [] for x in pack["cases"])
    assert all(x["adjudication"] is None for x in pack["cases"])
    assert all(x["source_review"]["exact_quote_confirmed"] is None for x in pack["cases"])
    assert all(x["pdf_sha256"] is None for x in pack["cases"])
    assert "UNREVIEWED" in pack["record_type"]


def test_case_count_regression_or_missing_paper_fails():
    data = sample()
    data["results"][0]["analysis"]["findings"].pop()
    try:
        build_review_pack(data)
    except ValueError as exc:
        assert "Historical findings changed" in str(exc)
    else:
        raise AssertionError("Incorrect review count was silently accepted")

    data = sample()
    data["results"].pop()
    try:
        build_review_pack(data)
    except ValueError as exc:
        assert "Missing B01-B10" in str(exc)
    else:
        raise AssertionError("Missing paper was silently accepted")


def test_mixed_version_and_duplicate_paper_fail():
    data = sample()
    data["results"][1]["analysis"]["analysis_version"] = "finance-structured-v6.4.2"
    try:
        build_review_pack(data)
    except ValueError as exc:
        assert "expected frozen" in str(exc)
    else:
        raise AssertionError("Mixed benchmark version was silently accepted")

    data = sample()
    data["results"].append(data["results"][0])
    try:
        build_review_pack(data)
    except ValueError as exc:
        assert "Duplicated paper_id" in str(exc)
    else:
        raise AssertionError("Duplicate paper ID was silently accepted")


def test_pdf_hash_requires_real_pdf_header_and_does_not_mark_pages_checked(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    paper = b"%PDF-1.7\nsynthetic bytes only for digest test\n"
    (pdf_dir / "B01.pdf").write_bytes(paper)
    pack = build_review_pack(sample(), pdf_dir=pdf_dir)
    assert pack["source_pdfs"]["B01"]["sha256"] == sha256(paper).hexdigest()
    assert pack["source_pdfs"]["B01"]["pdf_pages_verified"] is False
    assert pack["source_pdfs"]["B02"]["sha256"] is None

    (pdf_dir / "B01.pdf").write_bytes(b"not actually pdf")
    try:
        build_review_pack(sample(), pdf_dir=pdf_dir)
    except ValueError as exc:
        assert "not a PDF" in str(exc)
    else:
        raise AssertionError("Non-PDF source was silently accepted")


def test_invalid_citation_page_is_excluded_not_human_verified():
    data = sample()
    data["results"][0]["analysis"]["findings"][0]["evidence"] = [
        {"page": False, "quote": "invalid"},
        {"page": -3, "quote": "negative"},
        {"page": 2, "quote": "source"},
    ]
    pack = build_review_pack(data)
    assert pack["cases"][0]["direct_evidence"] == [{"page": 2, "quote": "source"}]
    assert pack["cases"][0]["source_review"]["source_page"] is None
