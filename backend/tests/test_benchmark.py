import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.evaluate import (
    citation_precision,
    evaluate_one,
    fact_alias_match,
    human_review_score,
    normalize,
)


def test_normalize_handles_unicode_dashes_and_korean_spacing():
    assert normalize("2001–2020") == "2001-2020"
    assert normalize("  GEMINI   FLASH ") == "gemini flash"


def test_fact_alias_match_finds_expected_bilingual_phrase():
    fact = {"aliases": ["GARCH-MIDAS", "가치요인"]}
    assert fact_alias_match(fact, normalize("이 논문은 GARCH-MIDAS 모형을 사용했다."))


def test_citation_precision_checks_exact_page_text():
    evidence = [
        {"page": 1, "quote": "exact source quote"},
        {"page": 2, "quote": "wrong source quote"},
    ]
    pages = {"1": "An exact source quote appears here.", "2": "Different page text."}
    assert citation_precision(evidence, pages) == 0.5


def test_human_review_score_uses_explicit_ratings():
    review = {
        "facts": {"sample": "correct", "method": "partial", "result": "incorrect"},
        "citations": {"q1": "exact", "q2": "wrong"},
        "reviewed_claims": 4,
        "unsupported_claims": 1,
    }
    score = human_review_score(review)
    assert score["fact_score"] == 0.5
    assert score["citation_score"] == 0.5
    assert score["unsupported_claim_score"] == 0.75


def test_evaluate_one_reports_fact_coverage_and_caveat_context():
    paper = {
        "id": "B01",
        "title": "Test",
        "gold_facts": [
            {"id": "sample", "weight": 2, "aliases": ["2001–2020", "2001년부터 2020년"]},
            {"id": "method", "weight": 1, "aliases": ["GARCH-MIDAS"]},
        ],
    }
    analysis = {
        "mode": "llm",
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "summary": "표본 기간은 2001년부터 2020년이다.",
        "methodology": {"design": "GARCH-MIDAS"},
        "evidence": [{"page": 1, "quote": "source quote"}],
    }
    score = evaluate_one(paper, analysis)
    assert score["gold_fact_coverage_screen"] == 1.0
    assert score["gold_fact_matches"] == ["sample", "method"]
    assert score["citation_page_precision"] is None
