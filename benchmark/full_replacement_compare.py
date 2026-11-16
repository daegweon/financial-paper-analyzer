"""One-shot, read-only A/B comparison of full PyMuPDF-free extraction replacements.

The frozen baseline is text extracted by PyMuPDF in the 2026-11-16
private table-shadow run, NOT a fresh call to the old engine. No provider calls,
queue claims, production result writes, or fallback to fitz.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import time
import urllib.parse

from benchmark.table_shadow import StorageSource, check_bytes

ROOT = Path(__file__).resolve().parents[1]
FROZEN_RUN = "tables-1503f4d527fa419a9d48d0576c3f616d"
MODES = ("docling", "camelot_composite")
NUM = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?(?![\w.])")
WORD = re.compile(r"[A-Za-z]{4,}|[가-힣]{2,}")


def token_recall(reference: str, candidate: str, pattern) -> float | None:
    gold = Counter(pattern.findall(reference.lower()))
    if not gold:
        return None
    got = Counter(pattern.findall(candidate.lower()))
    matched = sum(min(count, got.get(token, 0)) for token, count in gold.items())
    return round(matched / sum(gold.values()), 4)


def compare_pages(reference: list[dict], candidate: list[dict]) -> dict:
    basemap = {p["page"]: p["text"] for p in reference}
    candmap = {p["page"]: p["text"] for p in candidate}
    if len(basemap) != len(reference) or len(candmap) != len(candidate):
        raise ValueError("Duplicate pages")
    if set(candmap) - set(basemap):
        raise ValueError("Candidate cited unexpected pages")
    scores = []
    for page in reference:
        no = page["page"]
        txt = page["text"]
        out = candmap.get(no, "")
        scores.append({
            "page": no,
            "numeric": token_recall(txt, out, NUM),
            "lexical": token_recall(txt, out, WORD),
            "empty": not bool(out),
            "chars_reference": len(txt),
            "chars_candidate": len(out),
        })
    weighted_num = [s["numeric"] for s in scores if s["numeric"] is not None]
    weighted_lex = [s["lexical"] for s in scores if s["lexical"] is not None]
    return {
        "reference_pages": len(reference),
        "candidate_pages": len(candidate),
        "missing_reference_pages": [s["page"] for s in scores if s["empty"]],
        "mean_page_numeric_token_recall_against_frozen_text": round(sum(weighted_num) / len(weighted_num), 4) if weighted_num else None,
        "mean_page_lexical_token_recall_against_frozen_text": round(sum(weighted_lex) / len(weighted_lex), 4) if weighted_lex else None,
        "per_page": scores,
    }


def child(pdf: Path, mode: str, output: Path) -> int:
    from app.pdf_replacement import extract_pages
    start = time.perf_counter()
    data = pdf.read_bytes()
    count, pages = extract_pages(data, backend=mode)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output.write_text(json.dumps({
        "page_count": count,
        "pages": pages,
        "seconds": round(time.perf_counter() - start, 4),
        "max_rss_mib": round(rss / 1024, 2),
    }, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return 0


def run_child(pdf: Path, mode: str, output: Path, timeout: int) -> dict:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("SUPABASE_", "OPENAI_", "GEMINI_", "ANTHROPIC_", "BENCHMARK_")):
            env.pop(key, None)
    env.update(OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="2",
               TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_TELEMETRY="1")
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "benchmark.full_replacement_compare",
             "--child", str(pdf), "--mode", mode, "--output", str(output)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "wall_seconds": round(time.perf_counter() - start, 4)}
    if result.returncode or not output.exists():
        return {"status": "failed", "exit_code": result.returncode,
                "wall_seconds": round(time.perf_counter() - start, 4)}
    data = json.loads(output.read_text(encoding="utf-8"))
    return {"status": "ok", "wall_seconds": round(time.perf_counter() - start, 4), **data}


def load_frozen(source: StorageSource, owner: str, paper_id: str) -> list[dict]:
    path = "/storage/v1/object/" + source.artifact_bucket + "/" + urllib.parse.quote(
        owner + "/benchmarks/" + FROZEN_RUN + "/" + paper_id + ".json", safe="/")
    body, _ = source.request(path)
    blob = json.loads(body)
    runs = [r for r in blob.get("runs", []) if r.get("engine") == "pymupdf-text" and r.get("status") == "ok"]
    if len(runs) != 1 or not isinstance(runs[0].get("pages"), list):
        raise ValueError("Frozen control unavailable")
    return runs[0]["pages"]


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--child", type=Path)
    cli.add_argument("--mode", choices=MODES)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--ids", nargs="+", default=["B01", "B02", "B09", "B10"])
    cli.add_argument("--timeout", type=int, default=150)
    args = cli.parse_args()
    if args.child:
        return child(args.child, args.mode, args.output)
    corpus = json.loads((ROOT / "benchmark/table_corpus.sha256.json").read_text())["papers"]
    selected = [p for p in corpus if p["id"] in args.ids]
    if len(selected) != len(set(args.ids)) or len(set(args.ids)) != len(args.ids):
        cli.error("All requested paper IDs must be unique and present")
    source = StorageSource()
    data = []
    errors = []
    print(json.dumps({"event": "replacement_start", "ids": [p["id"] for p in selected],
                      "modes": MODES, "no_pymupdf_fallback": True}), flush=True)
    for spec in selected:
        try:
            pdf, identity, owner = source.get_pdf(spec)
            reference = load_frozen(source, owner, spec["id"])
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "source.pdf"
                path.write_bytes(pdf)
                runs = []
                for mode in MODES:
                    output = Path(folder) / (mode + ".json")
                    run = run_child(path, mode, output, args.timeout)
                    compact = {k: v for k, v in run.items() if k != "pages"}
                    compact.update({"backend": mode, "paper": spec["id"]})
                    if run["status"] == "ok":
                        if run["page_count"] != spec["pages"]:
                            compact["status"] = "page_count_mismatch"
                        else:
                            compact["comparison"] = compare_pages(reference, run["pages"])
                    runs.append(compact)
                    headline = {k: v for k, v in compact.items() if k != "comparison"}
                    if "comparison" in compact:
                        headline["metrics"] = {k: v for k, v in compact["comparison"].items() if k != "per_page"}
                    print(json.dumps({"event": "replacement_candidate", **headline}), flush=True)
            per_paper = {"id": spec["id"], "identity": identity, "runs": runs,
                         "source_control": "frozen_private_pymupdf_sort_true_not_current_full_engine"}
            source.save_artifact(owner, spec["id"], per_paper)
            data.append(per_paper)
        except Exception as exc:
            # Never log raw private paths, source text or credentials.
            errors.append({"id": spec["id"], "error_type": type(exc).__name__})
    summary = {"event": "replacement_summary", "ids": [p["id"] for p in selected],
               "completed_papers": len(data), "errors": errors,
               "candidate_failures": sum(1 for p in data for r in p["runs"] if r["status"] != "ok"),
               "production_modified": False, "model_calls": 0,
               "full_pipeline_accuracy": None, "promotion_eligible": False}
    print(json.dumps(summary), flush=True)
    return int(bool(errors or summary["candidate_failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
