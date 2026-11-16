from __future__ import annotations

import sys
import types
from pathlib import Path
import pytest
from app.pdf_table_experiment import extract_tables_camelot


def table(value="-0.154***", page=7, bbox=(10, 20, 300, 400), accuracy=98.5):
    return types.SimpleNamespace(page=page, _bbox=bbox,
        parsing_report={"accuracy":accuracy,"whitespace":12.0},
        df=types.SimpleNamespace(values=[["Variable","Model (1)"],["AR_Amihud",value]]))


def install(monkeypatch, func):
    monkeypatch.setitem(sys.modules,"camelot",types.SimpleNamespace(read_pdf=func))


def test_missing_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules,"camelot",None)
    diag=[]
    assert extract_tables_camelot(b"%PDF-fake",diagnostics=diag)==[]
    assert diag[0]["status"]=="dependency_unavailable"


def test_invalid_bytes_rejected_even_without_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules,"camelot",None)
    with pytest.raises(ValueError): extract_tables_camelot(b"not PDF")


@pytest.mark.parametrize("pages", [[0],[-1],[1.5],[True],["2"],"all"])
def test_invalid_page_selections(pages):
    with pytest.raises(ValueError): extract_tables_camelot(b"%PDF-x", pages=pages)


@pytest.mark.parametrize("flavors", [(),("bogus",),("stream","stream")])
def test_invalid_flavors(flavors):
    with pytest.raises(ValueError): extract_tables_camelot(b"%PDF-x", flavors=flavors)


def test_empty_selection_does_not_call_parser(monkeypatch):
    def fail(*a,**kw): raise AssertionError("not called")
    install(monkeypatch,fail)
    assert extract_tables_camelot(b"%PDF-x",pages=[])==[]


def test_preserves_exact_cells_geometry_and_page(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table()])
    result=extract_tables_camelot(b"%PDF-x",pages=[7],flavors=("lattice",))
    assert result == [{"page":7,"flavor":"lattice","bbox":[10,20,300,400],"accuracy":98.5,
                       "whitespace":12.0,"rows":[["Variable","Model (1)"],["AR_Amihud","-0.154***"]]}]


def test_identical_overlapping_duplicates_collapsed(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table(accuracy=100 if kw["flavor"]=="lattice" else 90)])
    result=extract_tables_camelot(b"%PDF-x")
    assert len(result)==1 and result[0]["flavor"]=="lattice"


@pytest.mark.parametrize("value", ["0.154***","-0.154**","-0.145***","(0.154)"])
def test_conflicting_sign_stars_coefficient_or_se_never_discarded(monkeypatch,value):
    install(monkeypatch,lambda *a,**kw:[table(value if kw["flavor"]=="stream" else "-0.154***")])
    assert len(extract_tables_camelot(b"%PDF-x"))==2


def test_benchmark_keeps_all_flavors(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table()])
    assert len(extract_tables_camelot(b"%PDF-x",deduplicate=False))==2


def test_distinct_tables_not_merged(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table(),table(bbox=(10,500,300,800))])
    assert len(extract_tables_camelot(b"%PDF-x",flavors=("stream",)))==2


def test_same_table_different_pages_not_merged(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table(),table(page=8)])
    assert len(extract_tables_camelot(b"%PDF-x",flavors=("stream",)))==2


def test_parser_errors_distinct_from_empty_and_no_private_message(monkeypatch):
    paths=[]
    def parse(path, pages, flavor):
        paths.append(path)
        if flavor=="lattice": raise RuntimeError("SECRET signed URL must not be logged")
        return []
    install(monkeypatch,parse);diag=[]
    assert extract_tables_camelot(b"%PDF-x",diagnostics=diag)==[]
    assert [d["status"] for d in diag]==["parser_error","ok"]
    assert "SECRET" not in repr(diag)
    assert all(not Path(p).exists() for p in paths)


def test_bad_table_does_not_hide_good_table(monkeypatch):
    install(monkeypatch,lambda *a,**kw:[table(page=0),table()]);diag=[]
    assert len(extract_tables_camelot(b"%PDF-x",flavors=("stream",),diagnostics=diag))==1
    assert diag[0]["status"]=="table_error"


def test_array_values_supported(monkeypatch):
    t=table();t.df.values=types.SimpleNamespace(tolist=lambda:[["a","b"],["x","-1***"]])
    install(monkeypatch,lambda *a,**kw:[t])
    assert extract_tables_camelot(b"%PDF-x",flavors=("stream",))[0]["rows"][1][1]=="-1***"
