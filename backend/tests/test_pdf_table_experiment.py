from __future__ import annotations

import sys
import types

from app.pdf_table_experiment import extract_tables_camelot


def test_table_extractor_returns_empty_when_optional_dependency_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "camelot", None)
    assert extract_tables_camelot(b"%PDF-fake") == []


def test_table_extractor_preserves_page_rows_and_parser_quality(monkeypatch):
    class FakeTable:
        page = 7
        _bbox = (10, 20, 300, 400)
        parsing_report = {"accuracy": 98.5, "whitespace": 12.0}

        class Frame:
            values = [["Variable", "Coefficient"], ["AR_Amihud", "-0.154***"]]

        df = Frame()

    fake = types.SimpleNamespace(
        read_pdf=lambda path, pages, flavor: [FakeTable()] if flavor == "lattice" else []
    )
    monkeypatch.setitem(sys.modules, "camelot", fake)
    result = extract_tables_camelot(b"%PDF-fake", pages=[7], flavors=("lattice",))
    assert result == [{
        "page": 7,
        "flavor": "lattice",
        "bbox": [10, 20, 300, 400],
        "accuracy": 98.5,
        "whitespace": 12.0,
        "rows": [["Variable", "Coefficient"], ["AR_Amihud", "-0.154***"]],
    }]


def test_table_extractor_collapses_same_table_from_multiple_flavors(monkeypatch):
    class FakeTable:
        page = 3
        _bbox = (10, 20, 300, 400)

        def __init__(self, accuracy, whitespace):
            self.parsing_report = {"accuracy": accuracy, "whitespace": whitespace}

        class Frame:
            values = [
                ["Variable", "Model (1)"],
                ["AR_Amihud", "-0.154***"],
            ]

        df = Frame()

    def read_pdf(path, pages, flavor):
        if flavor == "lattice":
            return [FakeTable(100.0, 8.0)]
        return [FakeTable(95.0, 15.0)]

    monkeypatch.setitem(sys.modules, "camelot", types.SimpleNamespace(read_pdf=read_pdf))
    result = extract_tables_camelot(
        b"%PDF-fake", pages=[3], flavors=("lattice", "stream")
    )
    assert len(result) == 1
    assert result[0]["flavor"] == "lattice"
    assert result[0]["rows"][1] == ["AR_Amihud", "-0.154***"]


def test_table_extractor_rejects_non_pdf_bytes():
    try:
        extract_tables_camelot(b"not pdf")
    except ValueError:
        return
    raise AssertionError("non-PDF bytes must be rejected")
