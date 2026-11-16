"""Run a reproducible, extraction-only preflight on pre-locked PDFs.

Imports the frozen production PyMuPDF extract_pages/build_analysis_prompt code.
No LLM/provider calls are made. PDF text is never written to the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any

import fitz


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("record_type") != "HELDOUT_LOCKED":
        raise ValueError("Held-out manifest must be binary locked")
    papers = value.get("heldout_papers")
    if not isinstance(papers, list) or len(papers) < 2:
        raise ValueError("At least two locked held-out papers are required")
    return value


def run_preflight(
    manifest: dict[str, Any],
    pdf_dir: Path,
    *,
    repeats: int = 5,
) -> dict[str, Any]:
    if type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError("repeats must be an integer from 1 to 20")
    backend_root = Path(__file__).resolve().parents[1] / "backend"
    sys.path.insert(0, str(backend_root))
    from app.main import ANALYSIS_VERSION, build_analysis_prompt, extract_pages

    requirements = (backend_root / "requirements.txt").read_text(encoding="utf-8")
    pinned = next(
        (line.split("==", 1)[1].strip() for line in requirements.splitlines()
         if line.strip().lower().startswith("pymupdf==")),
        None,
    )
    runtime = str(fitz.VersionBind)
    rows = []
    root = pdf_dir.resolve(strict=True)

    for paper in manifest["heldout_papers"]:
        paper_id = paper["id"]
        filename = paper["pdf_filename"]
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"{paper_id}: invalid PDF filename")
        path = (root / filename).resolve(strict=True)
        if path.parent != root or not path.is_file():
            raise ValueError(f"{paper_id}: PDF must be inside pdf_dir")
        raw = path.read_bytes()
        digest = _sha(raw)
        if digest != paper.get("pdf_sha256"):
            raise ValueError(f"{paper_id}: exact PDF SHA-256 differs from locked manifest")
        if len(raw) != paper.get("pdf_byte_length"):
            raise ValueError(f"{paper_id}: PDF byte length differs from locked manifest")

        durations = []
        final_pages = None
        page_count = None
        prompt = None
        for _ in range(repeats):
            start = time.perf_counter()
            page_count, pages = extract_pages(raw)
            durations.append((time.perf_counter() - start) * 1000)
            final_pages = pages
            prompt = build_analysis_prompt(pages)

        if page_count != paper.get("actual_page_count"):
            raise ValueError(f"{paper_id}: extracted page count differs from locked page count")
        page_text = "\n".join(f"{p['page']}\0{p['text']}" for p in final_pages)
        rows.append({
            "id": paper_id,
            "pdf_sha256": digest,
            "pdf_byte_length": len(raw),
            "actual_page_count": page_count,
            "pages_scanned": len(final_pages),
            "empty_text_pages": page_count - len(final_pages),
            "extracted_chars": sum(len(p["text"]) for p in final_pages),
            "prompt_chars": len(prompt),
            "extracted_text_sha256": _sha(page_text.encode("utf-8")),
            "prompt_sha256": _sha(prompt.encode("utf-8")),
            "extract_ms": [round(x, 3) for x in durations],
            "median_extract_ms": round(statistics.median(durations), 3),
        })

    return {
        "record_type": "LOCAL_EXTRACTION_PREFLIGHT_NOT_FULL_PIPELINE_BASELINE",
        "analysis_version": ANALYSIS_VERSION,
        "pymupdf_runtime_version": runtime,
        "pymupdf_pinned_version": pinned,
        "pymupdf_pin_match": runtime == pinned,
        "provider_calls": 0,
        "measurements": rows,
        "warning": (
            "Extraction-only local measurements. They do not measure Gemini output quality, "
            "provider latency/cost, full pipeline latency, or production memory."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight locked PDFs through frozen production extraction")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--require-pinned", action="store_true",
                        help="Exit nonzero if local PyMuPDF differs from backend/requirements.txt")
    args = parser.parse_args()
    report = run_preflight(_load_manifest(args.manifest), args.pdf_dir, repeats=args.repeats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "record_type": report["record_type"],
        "pymupdf_runtime_version": report["pymupdf_runtime_version"],
        "pymupdf_pinned_version": report["pymupdf_pinned_version"],
        "pymupdf_pin_match": report["pymupdf_pin_match"],
        "provider_calls": 0,
        "papers": [
            {"id": x["id"], "pages": x["actual_page_count"],
             "pages_scanned": x["pages_scanned"], "empty_text_pages": x["empty_text_pages"],
             "median_extract_ms": x["median_extract_ms"]}
            for x in report["measurements"]
        ],
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))
    if args.require_pinned and not report["pymupdf_pin_match"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
