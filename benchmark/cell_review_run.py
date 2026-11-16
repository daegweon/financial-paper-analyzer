"""One-shot private review preparation and bounded Stream experiment; no promotion.

Uses exact original PDFs and the existing shadow artifacts. Does not label its own
outputs as gold, modify analyses/jobs, call a model, or create any public endpoint.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
import urllib.parse

from benchmark.cell_review import evaluate, select_caption_pages, valid_box
from benchmark.table_shadow import MAX_PDF_BYTES, StorageSource, package_versions

ROOT = Path(__file__).resolve().parent
PRIOR_RUN = "tables-1503f4d527fa419a9d48d0576c3f616d"
PRIORITY = ("B01", "B02", "B09", "B10")
# Search hints from historical review triage, NOT correct answers or gold labels.
SEARCH_HINTS = {
    "B01": ["0.9548", "0.2987", "434.53", "49,066.00", "0.00026", "−0.00013", "0.000004"],
    "B02": ["49.942", "78.394", "209.734", "113.840", "408.203", "0.633", "0.345"],
    "B09": ["0.929", "−0.074", "0.643"],
    "B10": ["0.11", "0.17", "0.20", "0.04"],
}


def projection(tables: list, pages: list[int]) -> str:
    rows = [{"page": t["page"], "bbox": [round(float(x), 3) for x in t["bbox"]], "rows": t["rows"]}
            for t in tables if t["page"] in pages]
    rows.sort(key=lambda t: (t["page"], t["bbox"], json.dumps(t["rows"])))
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def child(pdf: Path, selected: list[int], output: Path) -> None:
    started = time.perf_counter()
    import fitz
    tables = []
    with fitz.open(pdf) as doc:
        if any(type(p) is not int or not 1 <= p <= len(doc) for p in selected):
            raise ValueError("Invalid selected source pages")
        if len(selected) != len(set(selected)):
            raise ValueError("Duplicate page selection")
        if selected:
            import camelot
            for table in camelot.read_pdf(str(pdf), pages=','.join(map(str, selected)), flavor="stream"):
                page = int(table.page)
                if page not in selected:
                    raise ValueError("Parser returned an unselected page")
                height = doc[page-1].rect.height
                cells = []
                rows = [[str(v).strip() for v in row] for row in table.df.values.tolist()]
                for i, row in enumerate(table.cells):
                    for j, cell in enumerate(row):
                        box = [float(cell.x1), height-float(cell.y2), float(cell.x2), height-float(cell.y1)]
                        if not valid_box(box):
                            raise ValueError("Invalid cell geometry")
                        cells.append({"row": i, "column": j, "text": rows[i][j], "bbox": box})
                tables.append({"page": page, "bbox": list(table._bbox),
                               "table_bbox_coordinate_system": "pdf_points_bottom_left",
                               "coordinate_system": "pdf_points_top_left", "cells": cells, "rows": rows})
    output.write_text(json.dumps({"status": "ok", "selected_pages": selected, "tables": tables,
        "extraction_seconds": round(time.perf_counter()-started, 6),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 3)},
        ensure_ascii=False, allow_nan=False), encoding="utf-8")


def isolated(pdf: Path, pages: list[int], output: Path, timeout: float = 30) -> dict:
    env = {k: os.environ[k] for k in ("PATH", "PYTHONPATH", "HOME", "LANG", "LC_ALL", "LD_LIBRARY_PATH", "TMPDIR") if k in os.environ}
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MPLBACKEND="Agg")
    started = time.perf_counter()
    with tempfile.TemporaryFile() as err:
        try:
            p = subprocess.run([sys.executable, "-m", "benchmark.cell_review_run", "--child", str(pdf),
                                "--pages", json.dumps(pages), "--output", str(output)],
                               env=env, stdout=subprocess.DEVNULL, stderr=err, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "wall_seconds": round(time.perf_counter()-started, 6)}
    if p.returncode or not output.exists():
        return {"status": "process_error", "exit_code": p.returncode,
                "wall_seconds": round(time.perf_counter()-started, 6)}
    result = json.loads(output.read_text())
    result["wall_seconds"] = round(time.perf_counter()-started, 6)
    return result


def prepare(source: StorageSource, spec: dict) -> dict:
    import fitz
    pdf, identity, owner = source.get_pdf(spec)
    # Read only the known private run; never enumerate arbitrary user artifacts.
    artifact = f"/storage/v1/object/{source.artifact_bucket}/{owner}/benchmarks/{PRIOR_RUN}/{spec['id']}.json"
    body, _ = source.request(artifact)
    prior = json.loads(body)
    if prior.get("id") != spec["id"] or prior.get("identity", {}).get("sha256") != identity["sha256"]:
        raise ValueError("Prior artifact source mismatch")
    prior_stream = [r for r in prior["runs"] if r["engine"] == "camelot-stream" and r["status"] == "ok"]
    if len(prior_stream) != 1:
        raise ValueError("Missing or ambiguous prior Stream result")
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        if len(doc) != spec["pages"]:
            raise ValueError("Source page-count mismatch")
        pages = [{"page": i+1, "text": p.get_text("text", sort=True)} for i, p in enumerate(doc)]
        selection = select_caption_pages(pages, cap=8)
        hits = [{"search_hint": hint, "pages": [p["page"] for p in pages if hint in p["text"]]}
                for hint in SEARCH_HINTS[spec["id"]]]
        negative_candidates = selection["unselected"][:1]
        figures = [p["page"] for p in pages if p["page"] in selection["unselected"] and "Figure " in p["text"]]
        if figures:
            negative_candidates = sorted(set(negative_candidates+[figures[0]]))
        requested = sorted(set(selection["selected"]+negative_candidates+[n for hit in hits for n in hit["pages"]]))
        review_pages = requested[:12]
        renders = []
        for n in review_pages:
            page = doc[n-1]
            raw = page.get_pixmap(matrix=fitz.Matrix(120/72, 120/72), colorspace=fitz.csGRAY).tobytes("png")
            renders.append({"page": n, "source_sha256": identity["sha256"], "dpi": 120,
                            "width": page.rect.width, "height": page.rect.height,
                            "png_sha256": hashlib.sha256(raw).hexdigest(),
                            "png_base64": base64.b64encode(raw).decode("ascii")})
    runs, compact = [], []
    with tempfile.TemporaryDirectory(prefix="papersignal-cell-review-") as tmp:
        path = Path(tmp)/"source.pdf"
        path.write_bytes(pdf)
        # Alternate order to reduce a fixed first-run bias. Two repeats are descriptive only.
        for repeat, order in enumerate((("all", "selected"), ("selected", "all")), 1):
            current = {}
            for variant in order:
                chosen = list(range(1, spec["pages"]+1)) if variant == "all" else selection["selected"]
                result = isolated(path, chosen, Path(tmp)/f"{repeat}-{variant}.json")
                result.update(variant=variant, repeat=repeat)
                runs.append(result)
                current[variant] = result
                compact.append({k:v for k,v in result.items() if k != "tables"})
                compact[-1]["candidate_tables"] = len(result.get("tables", []))
            if all(current[v]["status"] == "ok" for v in ("all", "selected")):
                same = projection(current["all"]["tables"], selection["selected"]) == projection(current["selected"]["tables"], selection["selected"])
                compact[-1]["selected_page_matrix_equivalent"] = same
    if any(r["status"] != "ok" for r in runs):
        raise RuntimeError("At least one parser execution failed; no quality result")
    baseline = next(r for r in runs if r["variant"] == "all")
    previous_equal = projection(baseline["tables"], list(range(1, spec["pages"]+1))) == projection(prior_stream[0]["tables"], list(range(1, spec["pages"]+1)))
    packet = {"schema_version": 1, "id": spec["id"], "identity": identity,
              "review_status": "unreviewed", "source_pages": renders,
              "selection": selection, "render_pages_omitted": requested[12:],
              "negative_candidate_pages_not_gold": negative_candidates,
              "machine_search_hints_not_gold": hits, "candidate_runs": runs,
              "prior_run": PRIOR_RUN, "prior_matrix_equivalent": previous_equal,
              "annotations": [], "evaluation": evaluate([], [], identity["sha256"])}
    if len(json.dumps(packet, ensure_ascii=False).encode()) > MAX_PDF_BYTES:
        raise ValueError("Review packet exceeds private artifact budget")
    if not source.save_artifact(owner, spec["id"], packet):
        raise RuntimeError("Private review artifact persistence is required")
    return {"id": spec["id"], "source_sha256": identity["sha256"], "pages": spec["pages"],
            "selection": selection, "source_renders": len(renders), "render_pages_omitted": requested[12:],
            "negative_candidate_pages_not_gold": negative_candidates,
            "search_hints": len(hits), "hints_with_page_hits": sum(bool(h["pages"]) for h in hits),
            "prior_matrix_equivalent": previous_equal, "runs": compact,
            "human_reviewed_targets": 0, "accuracy": None, "saved_private": True,
            "promotion_eligible": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--pages")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.child:
        child(args.child, json.loads(args.pages), args.output)
        return 0
    source = StorageSource()
    source.run_id = source.run_id.replace("tables-", "cell-review-")
    if not source.upload or source.bucket != "papers":
        raise ValueError("Explicit private source and artifact configuration required")
    specs = json.loads((ROOT/"table_corpus.sha256.json").read_text())["papers"]
    results, errors = [], []
    print(json.dumps({"event": "cell_review_start", "run_id": source.run_id, "versions": package_versions(),
                      "page_cap": 8, "parser_timeout_seconds": 30, "repeats": 2}), flush=True)
    for spec in specs:
        if spec["id"] not in PRIORITY:
            continue
        try:
            result = prepare(source, spec)
            results.append(result)
            print(json.dumps({"event": "cell_review_result", **result}, allow_nan=False), flush=True)
        except Exception as exc:
            err = {"id": spec["id"], "error_type": type(exc).__name__}
            errors.append(err)
            print(json.dumps({"event": "cell_review_error", **err}), flush=True)
    print(json.dumps({"event": "cell_review_complete", "run_id": source.run_id,
                      "completed": len(results), "expected": len(PRIORITY), "errors": errors,
                      "promotion_eligible": False, "human_reviewed_targets": 0,
                      "accuracy": None, "provider_calls": 0}), flush=True)
    return 1 if errors or len(results) != len(PRIORITY) else 0


if __name__ == "__main__":
    raise SystemExit(main())
