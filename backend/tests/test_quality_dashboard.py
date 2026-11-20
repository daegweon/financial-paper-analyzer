import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.quality_dashboard import render_dashboard


def test_dashboard_renders_measured_values_and_keeps_unmeasured_blank():
    html = render_dashboard({
        "benchmark_version": "1.0",
        "paper_count": 2,
        "results": [
            {"paper_id": "B01", "title": "Paper <one>", "gold_fact_coverage_screen": 0.5,
             "claim_evidence_coverage": 1.0, "citation_page_precision": None,
             "human_score": None, "gold_fact_missing": ["method"]},
            {"paper_id": "B02", "title": "Not run", "status": "not_run"},
        ],
    })
    assert "50.0%" in html
    assert "100.0%" in html
    assert "미측정" in html
    assert "분석 결과 없음" in html
    assert "Paper &lt;one&gt;" in html
    assert "어떠한 finding도 승인하지 않습니다" in html


def test_dashboard_does_not_invent_aggregate_scores_when_no_data():
    html = render_dashboard({"paper_count": 10, "results": []})
    assert "분석 완료" in html
    assert html.count("미측정") >= 4
    assert "0.0%" not in html
