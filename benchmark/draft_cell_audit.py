"""Source-first ASSISTANT visual drafts, never human gold or release approval.

Expected labels are represented by digests of exact whitespace-normalized text.
Digests avoid storing raw source matrices; they are not privacy encryption. The
PDF words must resolve the annotated regions BEFORE any candidate is examined.
No production imports, provider calls, data writes or promotion are performed.
"""
from __future__ import annotations
import hashlib
import math
import re
import unicodedata
from typing import Any

SHA = re.compile(r"[0-9a-f]{64}\Z")
CAPTION = re.compile(r"^\s*Table\s+(?:\d+(?:\.\d+)*|[A-Z]\d+)\s*[.:]\s+\S", re.I)
COMPANION_LABELS = {
    "reported_std_dev": ("Std. Dev.", "Standard deviation"),
    "standard_error": ("Std. Error", "Std. Error.", "Standard error"),
    "t_statistic": ("t-stat", "t-statistic"),
}


def norm(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    return "".join(unicodedata.normalize("NFC", text).replace("−", "-").split())


def digest(text: str) -> str:
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def box_ok(box: Any) -> bool:
    return (isinstance(box, (list, tuple)) and len(box) == 4
            and all(type(n) in (int, float) and math.isfinite(n) for n in box)
            and 0 <= box[0] < box[2] and 0 <= box[1] < box[3])


def inside(outer: list, inner: list) -> bool:
    x, y = (inner[0] + inner[2])/2, (inner[1] + inner[3])/2
    return outer[0] < x < outer[2] and outer[1] < y < outer[3]


def anchor_ok(anchor: Any) -> bool:
    return (isinstance(anchor, dict) and box_ok(anchor.get("bbox"))
            and isinstance(anchor.get("text_sha256"), str)
            and bool(SHA.fullmatch(anchor["text_sha256"])))


def resolve(anchor: dict, words: list) -> dict | None:
    """Resolve a visually labelled single-line ROI using native PDF words.

    Left-to-right ordering accommodates subscript baseline differences. This is
    deliberately NOT a general reading-order reconstructor or OCR fallback.
    """
    if not anchor_ok(anchor):
        raise ValueError("Invalid source anchor")
    found = [w for w in words if inside(anchor["bbox"], w[:4])]
    if not found:
        return None
    found.sort(key=lambda w: (w[0], w[1]))
    # Require vertical overlap; don't silently stitch separate source rows.
    if max(w[1] for w in found) >= min(w[3] for w in found):
        return None
    if digest("".join(w[4] for w in found)) != anchor["text_sha256"]:
        return None
    return {"bbox": [min(w[0] for w in found), min(w[1] for w in found),
                     max(w[2] for w in found), max(w[3] for w in found)],
            "text_sha256": anchor["text_sha256"]}


def validate(target: dict) -> None:
    if not isinstance(target.get("id"), str) or not target["id"]:
        raise ValueError("Missing target ID")
    for key in ("source_sha256", "render_sha256"):
        if not isinstance(target.get(key), str) or not SHA.fullmatch(target[key]):
            raise ValueError("Locked source and inspected render required")
    if type(target.get("page")) is not int or target["page"] < 1:
        raise ValueError("Invalid page")
    if target.get("coordinate_system") != "pdf_points_top_left":
        raise ValueError("Explicit source coordinate system required")
    if not all(isinstance(target.get(k), str) and target[k].strip()
               for k in ("variable", "model", "statistic", "layout")):
        raise ValueError("Missing reviewed semantics")
    if set(target.get("anchors", {})) != {"row", "column", "value"}:
        raise ValueError("Three source anchors required")
    if not all(anchor_ok(a) for a in target["anchors"].values()):
        raise ValueError("Invalid anchor")
    companions = target.get("companions", [])
    if not isinstance(companions, list):
        raise ValueError("Invalid companions")
    for c in companions:
        if (c.get("kind") not in COMPANION_LABELS or type(c.get("row_offset")) is not int
                or c["row_offset"] == 0 or not anchor_ok(c.get("label"))
                or not anchor_ok(c.get("value"))):
            raise ValueError("Invalid companion")
        if c["label"]["text_sha256"] not in {digest(t) for t in COMPANION_LABELS[c["kind"]]}:
            raise ValueError("Companion label/kind conflict")


def observe(target: dict, tables: list[dict], source_sha256: str,
            words: list, render_sha256: str, source_page: int) -> dict:
    """Descriptive source/candidate agreement. NEVER returns certified accuracy."""
    validate(target)
    result = {"id": target["id"], "status": "draft_review_pending", "candidate_agreement": None,
              "review_origin": "assistant", "human_reviewed": False,
              "certified_accuracy": None, "promotion_eligible": False}
    if (target["source_sha256"] != source_sha256 or target["render_sha256"] != render_sha256
            or target["page"] != source_page):
        return {**result, "status": "source_or_render_mismatch"}
    if (target.get("review_origin") != "assistant" or target.get("review_status") != "visual_draft"
            or target.get("source_render_checked") is not True):
        return result
    if any(not isinstance(w, (list, tuple)) or len(w) < 5 or not box_ok(w[:4])
           or not isinstance(w[4], str) for w in words):
        raise ValueError("Malformed native source words")
    anchors = dict(target["anchors"])
    for i, c in enumerate(target.get("companions", [])):
        anchors[f"c{i}_label"], anchors[f"c{i}_value"] = c["label"], c["value"]
    resolved = {k: resolve(a, words) for k, a in anchors.items()}
    if any(a is None for a in resolved.values()):
        return {**result, "status": "source_anchor_mismatch"}
    outcomes = []
    for table in tables:
        if table.get("page") != source_page:
            continue
        if table.get("coordinate_system") != "pdf_points_top_left":
            raise ValueError("Candidate coordinate system missing")
        cells = table.get("cells", [])
        if any(not box_ok(c.get("bbox")) or type(c.get("row")) is not int
               or type(c.get("column")) is not int or min(c["row"], c["column"]) < 0
               or not isinstance(c.get("text"), str) for c in cells):
            raise ValueError("Invalid candidate cell")
        def locate(a):
            hits = [c for c in cells if inside(c["bbox"], a["bbox"])]
            return hits[0] if len(hits) == 1 else None
        placed = {k: locate(a) for k, a in resolved.items()}
        if placed["value"] is None:
            if any(inside(c["bbox"], resolved["value"]["bbox"]) for c in cells):
                outcomes.append(False)  # overlapping candidate cells: ambiguous
            continue
        ok = all(c is not None and digest(c["text"]) == resolved[k]["text_sha256"]
                 for k, c in placed.items())
        if ok:
            row, col, val = (placed[k] for k in ("row", "column", "value"))
            ok = (row["row"] == val["row"] and row["column"] != val["column"]
                  and col["column"] == val["column"] and col["row"] != val["row"])
            for i, c in enumerate(target.get("companions", [])):
                label, value = placed[f"c{i}_label"], placed[f"c{i}_value"]
                ok &= (value["column"] == val["column"]
                       and value["row"] == val["row"] + c["row_offset"]
                       and label["row"] == value["row"] and label["column"] == row["column"])
        outcomes.append(bool(ok))
    status = ("missing" if not outcomes else "agreement" if all(outcomes)
              else "conflict" if any(outcomes) else "mismatch")
    return {**result, "status": status, "candidate_agreement": bool(outcomes) and all(outcomes),
            "source_anchors_resolved": len(resolved), "candidate_overlaps": len(outcomes)}


def caption_inventory(pages: list[dict], selected: list[int]) -> dict:
    """Independent native-line diagnostic, not a visually reviewed table census."""
    numbers = [p["page"] for p in pages]
    if (any(type(p) is not int or p < 1 for p in numbers) or len(set(numbers)) != len(numbers)
            or len(set(selected)) != len(selected) or set(selected) - set(numbers)):
        raise ValueError("Invalid inventory pages")
    hits = [{"page": p["page"], "caption_count": sum(bool(CAPTION.match(s)) for s in p["lines"])}
            for p in pages]
    hits = [p for p in hits if p["caption_count"]]
    return {"pages_scanned": len(pages), "selected_pages": len(selected),
            "caption_instances": sum(h["caption_count"] for h in hits),
            "caption_pages": [h["page"] for h in hits],
            "unselected_caption_pages": [h["page"] for h in hits if h["page"] not in selected],
            "captionless_or_image_tables_audited": False, "table_recall": None}


def expand_document(document: dict) -> list[dict]:
    """Expand shared, hash-only visual anchors; never invent review provenance."""
    targets = []
    common = {k: document[k] for k in (
        "source_sha256", "page", "render_sha256", "coordinate_system", "model",
        "layout", "statistic", "source_render_checked", "review_origin", "review_status")}
    for row in document["targets"]:
        target = {**common, **row,
                  "anchors": {k: document["anchors"][v] for k, v in row["anchors"].items()},
                  "companions": [{**c, "label": document["anchors"][c["label"]],
                                  "value": document["anchors"][c["value"]]}
                                 for c in row.get("companions", [])]}
        validate(target)
        targets.append(target)
    if len({t["id"] for t in targets}) != len(targets):
        raise ValueError("Duplicate draft target IDs")
    return targets
