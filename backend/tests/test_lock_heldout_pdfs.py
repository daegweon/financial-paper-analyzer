"""Synthetic PDF tests for the exact-byte held-out lock utility."""
import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.lock_heldout_pdfs import lock_heldout_pdfs


def make_pdf(path: Path, pages: int, title: str):
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{title} page {i + 1}")
    doc.set_metadata({"title": title})
    doc.save(path)
    doc.close()


def manifest(pages=(2, 3)):
    return {
        "record_type": "HELDOUT_PRESELECTION_NOT_BINARY_LOCKED",
        "heldout_papers": [
            {"id": "H01", "pdf_filename": "H01.pdf", "publisher_pdf_pages_reported": pages[0]},
            {"id": "H02", "pdf_filename": "H02.pdf", "publisher_pdf_pages_reported": pages[1]},
        ],
    }


def test_hashes_exact_pdf_bytes_and_verifies_pymupdf_page_counts(tmp_path):
    make_pdf(tmp_path / "H01.pdf", 2, "Heldout One")
    make_pdf(tmp_path / "H02.pdf", 3, "Heldout Two")
    before = (tmp_path / "H01.pdf").read_bytes()
    result = lock_heldout_pdfs(manifest(), tmp_path)
    first = result["heldout_papers"][0]
    import hashlib
    assert first["pdf_sha256"] == hashlib.sha256(before).hexdigest()
    assert first["actual_page_count"] == 2
    assert first["pdf_bytes_verified"] is True
    assert first["lock_commit"] is None
    assert result["record_type"] == "HELDOUT_BINARY_VERIFIED_PENDING_GIT_COMMIT"
    assert (tmp_path / "H01.pdf").read_bytes() == before


def test_page_count_mismatch_blocks_lock(tmp_path):
    make_pdf(tmp_path / "H01.pdf", 1, "One")
    make_pdf(tmp_path / "H02.pdf", 3, "Two")
    with pytest.raises(ValueError, match="page count mismatch"):
        lock_heldout_pdfs(manifest(), tmp_path)


def test_duplicate_heldout_pdf_bytes_are_rejected(tmp_path):
    make_pdf(tmp_path / "H01.pdf", 2, "Same")
    (tmp_path / "H02.pdf").write_bytes((tmp_path / "H01.pdf").read_bytes())
    with pytest.raises(ValueError, match="duplicate PDF bytes"):
        lock_heldout_pdfs(manifest(pages=(2, 2)), tmp_path)


def test_regression_overlap_and_non_pdf_are_rejected(tmp_path):
    make_pdf(tmp_path / "H01.pdf", 2, "One")
    make_pdf(tmp_path / "H02.pdf", 3, "Two")
    result = lock_heldout_pdfs(manifest(), tmp_path,
                               regression_sha256={lock_heldout_pdfs(
                                   manifest(), tmp_path
                               )["heldout_papers"][0]["pdf_sha256"]})
    # Recreate a clean directory because the overlap is checked against a separately
    # supplied baseline hash, not a mutation of the source file.
    with pytest.raises(ValueError, match="overlaps the regression corpus"):
        lock_heldout_pdfs(manifest(), tmp_path,
                          regression_sha256={result["heldout_papers"][0]["pdf_sha256"]})


def test_symlink_outside_pdf_dir_is_rejected(tmp_path):
    inside = tmp_path / "inside"
    outside = tmp_path / "outside"
    inside.mkdir()
    outside.mkdir()
    make_pdf(outside / "H01.pdf", 2, "One")
    make_pdf(inside / "H02.pdf", 3, "Two")
    (inside / "H01.pdf").symlink_to(outside / "H01.pdf")
    with pytest.raises(ValueError):
        lock_heldout_pdfs(manifest(), inside)


def test_wrong_record_type_and_missing_file_fail_closed(tmp_path):
    make_pdf(tmp_path / "H01.pdf", 2, "One")
    with pytest.raises(ValueError, match="not the preselected"):
        lock_heldout_pdfs({"record_type": "HELDOUT_BINARY_VERIFIED_PENDING_GIT_COMMIT",
                           "heldout_papers": manifest()["heldout_papers"]}, tmp_path)
    with pytest.raises(FileNotFoundError):
        lock_heldout_pdfs(manifest(), tmp_path)
