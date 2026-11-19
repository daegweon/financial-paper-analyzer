import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.compare_scorecards import compare_scorecards


def test_comparison_uses_only_paired_measured_values():
    baseline = {"benchmark_version": "v1", "results": [
        {"paper_id": "B01", "gold_fact_coverage_screen": 0.5, "human_score": None},
        {"paper_id": "B02", "gold_fact_coverage_screen": 0.8},
    ]}
    candidate = {"benchmark_version": "v2", "results": [
        {"paper_id": "B01", "gold_fact_coverage_screen": 0.7, "human_score": 0.9},
        {"paper_id": "B02", "gold_fact_coverage_screen": None},
        {"paper_id": "B03", "gold_fact_coverage_screen": 1.0},
    ]}
    result = compare_scorecards(baseline, candidate)
    gold = result["aggregate"]["gold_fact_coverage_screen"]
    assert result["paired_paper_count"] == 2
    assert gold["paired_count"] == 1
    assert gold["mean_delta"] == 0.2
    assert gold["improved_count"] == 1
    assert result["aggregate"]["human_score"]["paired_count"] == 0
    assert result["papers"][1]["metrics"]["gold_fact_coverage_screen"]["delta"] is None


def test_comparison_does_not_treat_missing_papers_as_zero():
    result = compare_scorecards(
        {"results": [{"paper_id": "B01", "citation_page_precision": 1.0}]},
        {"results": []},
    )
    metric = result["aggregate"]["citation_page_precision"]
    assert metric["paired_count"] == 0
    assert metric["baseline_mean"] is None
    assert metric["candidate_mean"] is None
    assert "never imputed as zero" in result["warning"]
