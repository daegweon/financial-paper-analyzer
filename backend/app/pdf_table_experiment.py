"""Experimental PDF table extraction adapter.

This module is intentionally isolated from the production request path.
It can be enabled in a benchmark worker after installing requirements-tables-experiment.txt.
"""
from __future__ import annotations

import os
import tempfile
from typing import Any


def extract_tables_camelot(
    pdf_bytes: bytes,
    pages: list[int] | None = None,
    *,
    flavors: tuple[str, ...] = ("lattice", "stream"),
) -> list[dict[str, Any]]:
    """Extract text-based PDF tables and preserve source page and parser metrics.

    Returns an empty list when Camelot is unavailable or no tables are found.
    It never replaces the baseline PyMuPDF text extraction.
    """
    try:
        import camelot
    except ImportError:
        return []

    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Expected PDF bytes")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        handle.write(pdf_bytes)
        path = handle.name
    results: list[dict[str, Any]] = []
    try:
        page_arg = ",".join(str(int(page)) for page in pages) if pages else "all"
        for flavor in flavors:
            try:
                tables = camelot.read_pdf(path, pages=page_arg, flavor=flavor)
            except Exception:
                # Parser-specific failures should not block the primary PDF path.
                continue
            for table in tables:
                df = table.df
                rows = [
                    [str(cell).strip() for cell in row]
                    for row in df.values.tolist()
                ]
                if not rows or not any(cell for row in rows for cell in row):
                    continue
                report = getattr(table, "parsing_report", {}) or {}
                results.append({
                    "page": int(getattr(table, "page", 0) or 0),
                    "flavor": flavor,
                    "bbox": list(getattr(table, "_bbox", ()) or ()),
                    "accuracy": report.get("accuracy"),
                    "whitespace": report.get("whitespace"),
                    "rows": rows,
                })
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return results
