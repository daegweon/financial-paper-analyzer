"""Replacement adapter contracts. No PyMuPDF/fitz is used by the module."""
from __future__ import annotations

import pytest
from app import pdf_replacement as mod


def test_only_explicit_supported_backends():
    with pytest.raises(ValueError):
        mod.extract_pages(b"%PDF-fake", "pymupdf")


def test_invalid_source_is_rejected():
    with pytest.raises(ValueError):
        mod.extract_pages(b"random", "docling")
    with pytest.raises(ValueError):
        mod.extract_pages(b"%PDF-", "unsupported")


def test_output_schema_and_truncation():
    count, pages = mod._normal_pages({1: ["abc", " " * 9, "z" * 9000], 3: ["HELLO"]}, 4)
    assert count == 4 and pages[0]["page"] == 1 and len(pages[0]["text"]) == 4500
    assert pages[1]["page"] == 3


def test_does_not_fabricate_empty_pages():
    with pytest.raises(ValueError):
        mod._normal_pages({1: [" ", ""]}, 2)


def test_mode_selection_does_not_invoke_old_backend(monkeypatch):
    called = []
    monkeypatch.setattr(mod, "_count_pages", lambda _: 2)
    monkeypatch.setattr(mod, "docling_pages", lambda _data, n: (called.append("docling") or (n, [{"page": 1, "text": "hello"}])))
    monkeypatch.setattr(mod, "camelot_composite_pages", lambda _data, n: (called.append("camelot") or (n, [{"page": 2, "text": "world"}])))
    assert mod.extract_pages(b"%PDF-test", "docling")[1][0]["page"] == 1
    assert mod.extract_pages(b"%PDF-test", "camelot_composite")[1][0]["page"] == 2
    assert called == ["docling", "camelot"]


def test_no_pymupdf_dependency_in_source():
    import inspect
    source = inspect.getsource(mod)
    assert not __import__("re").search(r"^\s*(?:from\s+fitz|import\s+fitz)", source, __import__("re").M)
