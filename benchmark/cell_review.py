"""Offline, fail-closed exact-cell review. Never imported by the production engine.

Candidate matrices are NOT ground truth. Gold annotations must be independently
reviewed against the SHA-locked PDF renders. This evaluator never promotes a build.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Any

CAPTION = re.compile(r"^\s*Table\s+(?:\d+(?:\.\d+)*|[A-Z]\d+)\s*[.:]\s+\S", re.I)
SHA256 = re.compile(r"[0-9a-f]{64}")


def normalized(value: str) -> str:
    """Only whitespace, canonical Unicode and typographic minus; no rounding."""
    if not isinstance(value, str):
        raise ValueError("Cell text must be a string")
    return "".join(unicodedata.normalize("NFC", value).replace("−", "-").split())


def valid_box(box: Any) -> bool:
    return (isinstance(box, (list, tuple)) and len(box) == 4
            and all(type(x) in (float, int) and math.isfinite(x) for x in box)
            and box[0] < box[2] and box[1] < box[3])


def contains_center(outer: list, inner: list) -> bool:
    x, y = (inner[0]+inner[2])/2, (inner[1]+inner[3])/2
    return outer[0] < x < outer[2] and outer[1] < y < outer[3]


def select_caption_pages(pages: list[dict], cap: int = 8) -> dict:
    """A preregistered experimental selector, not a table detector or gold label."""
    if type(cap) is not int or not 1 <= cap <= 16:
        raise ValueError("cap must be between 1 and 16")
    numbers = [p["page"] for p in pages]
    if (any(type(p) is not int or p < 1 for p in numbers)
            or len(numbers) != len(set(numbers))):
        raise ValueError("Pages must be positive and unique")
    candidates = sorted(p["page"] for p in pages
                        if any(CAPTION.match(line) for line in p["text"].splitlines()))
    return {"strategy": "standalone-table-caption-v1", "cap": cap,
            "selected": candidates[:cap], "omitted_by_cap": candidates[cap:],
            "unselected": sorted(set(numbers)-set(candidates[:cap])),
            "complete": not candidates[cap:], "table_recall_known": False}


def review_ready(item: dict) -> bool:
    reviewers = item.get("reviewers", [])
    return (item.get("review_status") == "independently_reviewed"
            and item.get("review_origin") == "human"
            and item.get("source_render_checked") is True
            and isinstance(reviewers, list) and len(reviewers) >= 2
            and all(isinstance(x, str) and x.strip() for x in reviewers)
            and len({x.strip() for x in reviewers}) == len(reviewers))


def validate_target(target: dict) -> None:
    if not isinstance(target.get("id"), str) or not target["id"]:
        raise ValueError("Missing target ID")
    if not isinstance(target.get("source_sha256"), str) or not SHA256.fullmatch(target["source_sha256"]):
        raise ValueError("A locked PDF SHA-256 is required")
    if type(target.get("page")) is not int or target["page"] < 1:
        raise ValueError("Invalid source page")
    for field in ("variable", "model", "statistic"):
        if not isinstance(target.get(field), str) or not target[field].strip():
            raise ValueError("Variable, model and statistic must be labelled")
    if target.get("coordinate_system") != "pdf_points_top_left":
        raise ValueError("Explicit top-left PDF-point coordinates required")
    anchors = target.get("anchors", {})
    if not isinstance(anchors, dict) or not all(key in anchors for key in ("row", "column", "value")):
        raise ValueError("Row, column and value anchors are required")
    for anchor in anchors.values():
        if not isinstance(anchor, dict):
            raise ValueError("Invalid anchor")
        if not valid_box(anchor.get("bbox")) or not normalized(anchor.get("text", "")):
            raise ValueError("Invalid or empty anchor")
    for companion in target.get("companions", []):
        if (type(companion.get("row_offset")) is not int
                or not valid_box(companion.get("bbox"))
                or not normalized(companion.get("text", ""))
                or not isinstance(companion.get("kind"), str)):
            raise ValueError("Invalid companion statistic")


def _locate(cells: list[dict], anchor: dict) -> dict | None:
    found = [c for c in cells if contains_center(c["bbox"], anchor["bbox"])]
    # Multiple cells at a position, including duplicated geometry, are ambiguous.
    return found[0] if len(found) == 1 else None


def score_target(target: dict, tables: list[dict], source_sha256: str) -> dict:
    validate_target(target)
    result = {"id": target["id"], "status": "review_pending", "exact": None}
    if target["source_sha256"] != source_sha256:
        return {**result, "status": "source_mismatch"}
    if not review_ready(target):
        return result
    statuses = []
    for table in tables:
        if table.get("page") != target["page"]:
            continue
        if table.get("coordinate_system") != "pdf_points_top_left":
            raise ValueError("Candidate coordinates must be explicit")
        cells = table.get("cells", [])
        if any(not valid_box(c.get("bbox")) or type(c.get("row")) is not int
               or type(c.get("column")) is not int or c["row"] < 0 or c["column"] < 0
               or not isinstance(c.get("text"), str) for c in cells):
            raise ValueError("Invalid candidate cell")
        located = {k: _locate(cells, a) for k, a in target["anchors"].items()}
        if located["value"] is None:
            continue
        if any(c is None for c in located.values()):
            statuses.append(False)
            continue
        exact = all(normalized(located[k]["text"]) == normalized(a["text"])
                    for k, a in target["anchors"].items())
        exact &= (located["row"]["row"] == located["value"]["row"]
                  and located["column"]["column"] == located["value"]["column"]
                  and located["row"]["column"] != located["value"]["column"]
                  and located["column"]["row"] != located["value"]["row"])
        for anchor in target.get("companions", []):
            c = _locate(cells, anchor)
            exact &= bool(c and normalized(c["text"]) == normalized(anchor["text"])
                          and c["column"] == located["value"]["column"]
                          and c["row"] == located["value"]["row"] + anchor["row_offset"])
        statuses.append(bool(exact))
    if not statuses:
        return {**result, "status": "missing", "exact": False}
    if all(statuses):
        return {**result, "status": "exact", "exact": True}
    return {**result, "status": "conflict" if any(statuses) else "mismatch", "exact": False}


def score_negative_page(item: dict, tables: list[dict], source_sha256: str) -> dict:
    """Count raw candidate hits on an independently labelled table-free page.

    This is a detection diagnostic, NOT a downstream false-approval measure.
    """
    if (not isinstance(item.get("id"), str) or not item["id"]
            or item.get("kind") != "no_table_page"
            or type(item.get("page")) is not int or item["page"] < 1
            or not isinstance(item.get("source_sha256"), str)
            or not SHA256.fullmatch(item["source_sha256"])):
        raise ValueError("Invalid negative-page annotation")
    status = "source_mismatch" if item["source_sha256"] != source_sha256 else "review_pending"
    count = None
    if status != "source_mismatch" and review_ready(item):
        status = "assessed"
        count = sum(t.get("page") == item["page"] for t in tables)
    return {"id": item["id"], "status": status, "candidate_hits": count}


def evaluate(targets: list[dict], tables: list[dict], source_sha256: str,
             negative_pages: list[dict] | None = None) -> dict:
    if len({x.get("id") for x in targets}) != len(targets):
        raise ValueError("Duplicate target IDs")
    negative_pages = negative_pages or []
    if len({n.get("id") for n in negative_pages}) != len(negative_pages):
        raise ValueError("Duplicate negative control IDs")
    negative_outcomes = [score_negative_page(n, tables, source_sha256) for n in negative_pages]
    negatives_ready = bool(negative_pages) and all(n["candidate_hits"] is not None for n in negative_outcomes)
    outcomes = [score_target(t, tables, source_sha256) for t in targets]
    assessed = [o for o in outcomes if o["exact"] is not None]
    correct = sum(o["exact"] is True for o in assessed)
    fully_reviewed = bool(targets) and len(assessed) == len(targets)
    return {"targets": len(targets), "assessed": len(assessed), "exact": correct,
            "exact_cell_accuracy": correct / len(assessed) if fully_reviewed else None,
            "fully_reviewed": fully_reviewed, "outcomes": outcomes,
            "negative_outcomes": negative_outcomes,
            "negative_page_hit_rate": (sum(n["candidate_hits"] > 0 for n in negative_outcomes)
                                       / len(negative_outcomes)) if negatives_ready else None,
            "promotion_eligible": False,
            "blocking_gates": (["independent_source_review_incomplete"] if not fully_reviewed else [])
                + ([] if negatives_ready else ["negative_controls_not_adjudicated"])
                + ["full_pipeline_non_regression_not_run",
                   "end_to_end_resource_cost_budget_not_validated", "held_out_quality_not_run"]}


def render_html(packet: dict) -> str:
    """Offline review display: source first, parser candidates hidden by default."""
    images = []
    for page in packet["source_pages"]:
        raw = base64.b64decode(page["png_base64"], validate=True)
        if not raw.startswith(b"\x89PNG\r\n\x1a\n") or hashlib.sha256(raw).hexdigest() != page["png_sha256"]:
            raise ValueError("Invalid review render")
        if page["source_sha256"] != packet["identity"]["sha256"]:
            raise ValueError("Render/source identity mismatch")
        encoded = base64.b64encode(raw).decode("ascii")
        images.append(f'<section><h2>PDF page {int(page["page"])}</h2>'
                      f'<p>PDF dimensions: {float(page["width"]):.2f} x {float(page["height"]):.2f} pt</p>'
                      f'<img alt="Original PDF page" src="data:image/png;base64,{encoded}"></section>')
    candidates = html.escape(json.dumps(packet.get("candidate_runs", []), indent=2, ensure_ascii=False))
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>PaperSignal source review</title>'
            '<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px}'
            'img{max-width:100%;border:1px solid #aaa}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
            'section{margin:40px 0}details{border:1px solid;padding:16px}</style>'
            '<h1>Source-first cell review — UNREVIEWED</h1><p>Source PDF SHA-256: <code>'
            + html.escape(packet["identity"]["sha256"]) + '</code></p>'
            '<p>Label original row, column, value and companion statistics before opening candidates. '
            'Do not infer p-values or call Std. Dev. a standard error. Two independent human reviewers '
            'must adjudicate the same source. Images are generated renders, not proof of completed review.</p>'
            + ''.join(images) + '<details><summary>Reveal parser candidates after source labelling</summary><pre>'
            + candidates + '</pre></details></html>')


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--html", type=Path, required=True)
    args = parser.parse_args()
    args.html.write_text(render_html(json.loads(args.packet.read_text())), encoding="utf-8")


if __name__ == "__main__":
    main()
