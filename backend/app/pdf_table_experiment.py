"""Optional table extractor. Never imported by the production request path."""
from __future__ import annotations

import math
import os
import tempfile
import time
from typing import Any


SUPPORTED_FLAVORS = frozenset({"lattice", "stream", "network", "hybrid"})


def extract_tables_camelot(
    pdf_bytes: bytes,
    pages: list[int] | None = None,
    *,
    flavors: tuple[str, ...] = ("lattice", "stream"),
    deduplicate: bool = True,
    diagnostics: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return source-located candidates, not verified financial facts.

    ``pages`` is 1-based; None means all pages and [] means no pages.
    Use deduplicate=False in benchmarks to preserve every parser candidate.
    Errors are optionally recorded without exception messages or private paths.
    Missing dependencies still return [], preserving the optional adapter API.
    """
    if not isinstance(pdf_bytes, bytes) or not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Expected PDF bytes")
    if pages is not None and (
        not isinstance(pages, list)
        or any(type(p) is not int or p < 1 for p in pages)
    ):
        raise ValueError("pages must contain positive, 1-based integers")
    if not flavors or any(f not in SUPPORTED_FLAVORS for f in flavors):
        raise ValueError("Unsupported or empty parser flavors")
    if len(set(flavors)) != len(flavors):
        raise ValueError("Duplicate parser flavors")

    def record(**fields: Any) -> None:
        if diagnostics is not None:
            diagnostics.append(fields)

    if pages == []:
        record(status="skipped_empty_page_selection")
        return []
    try:
        import camelot
    except ImportError:
        record(status="dependency_unavailable", dependency="camelot-py")
        return []

    results: list[dict[str, Any]] = []
    # The directory context also cleans up on parser/serialization failures.
    with tempfile.TemporaryDirectory(prefix="papersignal-tables-") as tmp:
        path = os.path.join(tmp, "input.pdf")
        with open(path, "wb") as handle:
            handle.write(pdf_bytes)
        page_arg = ",".join(map(str, dict.fromkeys(pages))) if pages else "all"
        for flavor in flavors:
            started = time.perf_counter()
            count = 0
            try:
                tables = camelot.read_pdf(path, pages=page_arg, flavor=flavor)
                for table in tables:
                    try:
                        values = table.df.values
                        raw_rows = values.tolist() if hasattr(values, "tolist") else values
                        rows = [[str(cell).strip() for cell in row] for row in raw_rows]
                        if not rows or not any(cell for row in rows for cell in row):
                            continue
                        page = int(getattr(table, "page", 0) or 0)
                        bbox = list(getattr(table, "_bbox", ()) or ())
                        if page < 1 or (pages is not None and page not in pages):
                            raise ValueError("Invalid source page")
                        if len(bbox) != 4 or not all(math.isfinite(float(x)) for x in bbox):
                            raise ValueError("Invalid source bounding box")
                        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                            raise ValueError("Degenerate bounding box")
                        report = getattr(table, "parsing_report", {}) or {}
                        results.append({
                            "page": page, "flavor": flavor, "bbox": bbox,
                            "accuracy": report.get("accuracy"),
                            "whitespace": report.get("whitespace"), "rows": rows,
                        })
                        count += 1
                    except Exception as exc:
                        record(status="table_error", flavor=flavor, error_type=type(exc).__name__)
                record(status="ok", flavor=flavor, tables=count,
                       elapsed_ms=round((time.perf_counter() - started) * 1000, 3))
            except Exception as exc:
                record(status="parser_error", flavor=flavor, error_type=type(exc).__name__,
                       elapsed_ms=round((time.perf_counter() - started) * 1000, 3))

    if not deduplicate:
        return results

    def overlap(a: list[float], b: list[float]) -> float:
        area = lambda r: (r[2] - r[0]) * (r[3] - r[1])
        intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
        union = area(a) + area(b) - intersection
        return intersection / union if union > 0 else 0.0

    def score(item: dict[str, Any]) -> float:
        try:
            value = float(item.get("accuracy") or 0) - 0.15 * float(item.get("whitespace") or 0)
            return value if math.isfinite(value) else -math.inf
        except (TypeError, ValueError):
            return -math.inf

    selected: list[dict[str, Any]] = []
    for candidate in sorted(results, key=score, reverse=True):
        # Structural parser scores cannot adjudicate conflicting numeric cells.
        # Collapse only an identical cell matrix at overlapping source geometry.
        if not any(candidate["page"] == old["page"]
                   and candidate["rows"] == old["rows"]
                   and overlap(candidate["bbox"], old["bbox"]) >= 0.5
                   for old in selected):
            selected.append(candidate)
    return selected
