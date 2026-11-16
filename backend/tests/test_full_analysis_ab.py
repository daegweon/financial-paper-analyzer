from benchmark import full_analysis_ab as ab
import pytest

def test_pair_rejects_unpaired():
    assert not ab.pair_status([{"backend": "baseline", "status": "failed"}])["comparable"]

def test_tally_provider_failure_no_invented_cost():
    report = ab.tally_usage([{"model": "example", "status_code": 429, "wall_seconds": 3}])
    assert report["has_rate_limit"]
    assert report["cost_usd"] is None
    assert not report["usage_complete"]

def test_tally_usage_real_counts_only():
    report = ab.tally_usage([{"model": "test", "status_code": 200,
                              "wall_seconds": 1,
                              "usage": {"promptTokenCount": 17, "totalTokenCount": 20}}])
    assert report["token_counts_observed"]["promptTokenCount"] == 17
    assert report["usage_complete"]

def test_main_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("FULL_AB_ALLOW_MODEL_CALLS", raising=False)
    monkeypatch.setattr(ab.engine, "active_ai_provider", lambda: "gemini")
    monkeypatch.setattr("sys.argv", ["full_analysis_ab"])
    with pytest.raises(RuntimeError, match="Refusing"):
        ab.main()

def test_pair_model_mismatch_fails_comparability():
    rows = [
      {"backend":"baseline","status":"ok","summary":{"models_used":["one"]}},
      {"backend":"docling_parse","status":"ok","summary":{"models_used":["two"]}}
    ]
    p=ab.pair_status(rows)
    assert p["paired"] and not p["comparable"]

def test_none_of_these_modules_run_production_db_mutations():
    import inspect
    code=inspect.getsource(ab)
    assert "_process_analysis_job(" not in code
    assert "claim_analysis_job" not in code
    assert "rest/v1/analyses" not in code

def test_docling_parse_import_and_shared_page_counter_dependencies():
    from docling_parse.pdf_parser import DoclingPdfParser
    from pdfminer.pdfpage import PDFPage
    assert DoclingPdfParser and PDFPage
