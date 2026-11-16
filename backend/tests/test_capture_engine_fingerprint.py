"""Tests for source fingerprint capture and secret exclusion."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.capture_engine_fingerprint import capture, sha256_text


MAIN = '''import os
ANALYSIS_VERSION = "finance-structured-v6.4.2"
MAX_BYTES = 100
MAX_PAGES = 300
MAX_PAGES_TO_SCAN = 50
MAX_PAGE_CHARS = 4500
MAX_LLM_CHARS = 220000
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
EVIDENCE_SCHEMA = {"type": "object"}
_EVIDENCE_TRANSLATION = {}
def extract_pages(data):
    return data
def build_analysis_prompt(pages):
    return str(pages)
async def _generate_gemini(prompt):
    return prompt
'''


def make_repo(root: Path):
    (root / "backend/app").mkdir(parents=True)
    (root / "backend").mkdir(exist_ok=True)
    (root / "backend/app/main.py").write_text(MAIN, encoding="utf-8")
    (root / "backend/app/worker.py").write_text("def worker(): return True\n", encoding="utf-8")
    (root / "backend/requirements.txt").write_text("PyMuPDF==1.26.3\n", encoding="utf-8")
    (root / "backend/Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")


def test_capture_fingerprints_are_stable_and_include_required_segments(tmp_path, monkeypatch):
    make_repo(tmp_path)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_FALLBACK_MODEL", raising=False)
    report = capture(tmp_path, production_commit="a" * 40)
    assert report["record_type"] == "SOURCE_FINGERPRINT_ONLY_NOT_FULL_PIPELINE_BASELINE"
    assert report["production_commit"] == "a" * 40
    assert report["model_config"]["gemini_primary_model"] == "gemini-3.5-flash-lite"
    assert report["model_config"]["gemini_fallback_model"] == "gemini-3.6-flash"
    assert report["segments"]["prompt_sha256"] == sha256_text("def build_analysis_prompt(pages):\n    return str(pages)")
    assert len(report["segments"]["schema_sha256"]) == 64
    assert report["extraction_config"]["MAX_PAGES_TO_SCAN"] == 50


def test_capture_reads_only_safe_model_names_and_never_serializes_secrets(tmp_path, monkeypatch):
    make_repo(tmp_path)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "DO_NOT_READ_OR_EMIT_THIS_SECRET")
    report = capture(tmp_path, production_commit="b" * 40)
    encoded = json.dumps(report)
    assert report["model_config"]["gemini_primary_model"] == "gemini-test-model"
    assert "DO_NOT_READ_OR_EMIT_THIS_SECRET" not in encoded
    assert "GEMINI_API_KEY" not in encoded
    assert report["model_config"]["secret_values_included"] is False
    assert report["model_config"]["secret_environment_variables_read"] == []


def test_missing_source_file_fails_closed(tmp_path):
    (tmp_path / "backend").mkdir()
    try:
        capture(tmp_path, production_commit="c" * 40)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Missing source files must not produce a fingerprint report")
