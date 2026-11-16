"""Extraction preflight tests use synthetic PDFs only."""
import hashlib
import json
from pathlib import Path
import sys

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.extraction_preflight import run_preflight


def make_pdf(path: Path, pages: int):
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Synthetic page {i + 1} with financial research text.")
    doc.save(path)
    doc.close()


def test_preflight_uses_locked_hash_and_production_extractor_without_provider_calls(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    path = pdf_dir / "H01.pdf"
    make_pdf(path, 2)
    raw = path.read_bytes()
    manifest = {
        "record_type": "HELDOUT_LOCKED",
        "heldout_papers": [{
            "id": "H01", "pdf_filename": "H01.pdf",
            "pdf_sha256": hashlib.sha256(raw).hexdigest(),
            "pdf_byte_length": len(raw), "actual_page_count": 2,
        }],
    }
    report = run_preflight(manifest, pdf_dir, repeats=2)
    assert report["record_type"] == "LOCAL_EXTRACTION_PREFLIGHT_NOT_FULL_PIPELINE_BASELINE"
    assert report["provider_calls"] == 0
    row = report["measurements"][0]
    assert row["pdf_sha256"] == hashlib.sha256(raw).hexdigest()
    assert row["actual_page_count"] == 2
    assert row["pages_scanned"] == 2
    assert row["empty_text_pages"] == 0
    assert len(row["extracted_text_sha256"]) == 64
    assert len(row["prompt_sha256"]) == 64
    assert len(row["extract_ms"]) == 2


def test_wrong_pdf_hash_and_page_count_fail_closed(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    path = pdf_dir / "H01.pdf"
    make_pdf(path, 2)
    raw = path.read_bytes()
    manifest = {
        "record_type": "HELDOUT_LOCKED",
        "heldout_papers": [{
            "id": "H01", "pdf_filename": "H01.pdf",
            "pdf_sha256": "0" * 64,
            "pdf_byte_length": len(raw), "actual_page_count": 2,
        }],
    }
    with pytest.raises(ValueError, match="SHA-256 differs"):
        run_preflight(manifest, pdf_dir)

    manifest["heldout_papers"][0]["pdf_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["heldout_papers"][0]["actual_page_count"] = 3
    with pytest.raises(ValueError, match="page count differs"):
        run_preflight(manifest, pdf_dir)


def test_invalid_repeats_and_unlocked_manifest_fail_closed(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    with pytest.raises(ValueError, match="binary locked"):
        run_preflight({"record_type": "HELDOUT_PRESELECTION_NOT_BINARY_LOCKED",
                       "heldout_papers": [{}, {}]}, pdf_dir)
    with pytest.raises(ValueError, match="repeats"):
        run_preflight({"record_type": "HELDOUT_LOCKED", "heldout_papers": [{}, {}]},
                      pdf_dir, repeats=0)
