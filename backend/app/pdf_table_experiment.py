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
    # Different Camelot flavors often detect the same physical table.
    # Keep the best-scoring candidate only when both geometry and row labels
    # indicate that the candidates are the same table; retain distinct tables.
    def overlap_ratio(a: list[float], b: list[float]) -> float:
        if len(a) != 4 or len(b) != 4:
            return 0.0
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
        iy = max(0.0, min(ay2, by2) - max(ay1, by1))
        intersection = ix * iy
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - intersection
        return intersection / union if union else 0.0

    def row_labels(item: dict[str, Any]) -> set[str]:
        return {
            " ".join(row[0].casefold().split())
            for row in item["rows"]
            if row and row[0].strip()
        }

    selected: list[dict[str, Any]] = []
    for candidate in sorted(
        results,
        key=lambda item: (
            float(item.get("accuracy") or 0)
            - 0.15 * float(item.get("whitespace") or 0)
        ),
        reverse=True,
    ):
        candidate_labels = row_labels(candidate)
        duplicate_index = None
        for index, existing in enumerate(selected):
            existing_labels = row_labels(existing)
            union = candidate_labels | existing_labels
            label_overlap = (
                len(candidate_labels & existing_labels) / len(union)
                if union else 0.0
            )
            if (
                candidate["page"] == existing["page"]
                and label_overlap >= 0.6
                and overlap_ratio(candidate["bbox"], existing["bbox"]) >= 0.5
            ):
                duplicate_index = index
                break
        if duplicate_index is None:
            selected.append(candidate)
    return selected
