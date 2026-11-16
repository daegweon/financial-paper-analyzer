"""Hash and verify exact preselected held-out PDF bytes with PyMuPDF.

The input PDF files must be obtained separately. This tool never downloads,
modifies, re-serializes, uploads or commits private PDF bytes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import fitz


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("heldout_papers"), list):
        raise ValueError("Manifest must contain a heldout_papers list")
    return value


def lock_heldout_pdfs(
    manifest: dict[str, Any],
    pdf_dir: Path,
    *,
    regression_sha256: set[str] | None = None,
) -> dict[str, Any]:
    papers = manifest.get("heldout_papers")
    if not isinstance(papers, list) or len(papers) < 2:
        raise ValueError("At least two preselected held-out papers are required")
    if manifest.get("record_type") != "HELDOUT_PRESELECTION_NOT_BINARY_LOCKED":
        raise ValueError("Input manifest must be the preselected, not-yet-locked record")

    root = pdf_dir.resolve(strict=True)
    updated: list[dict[str, Any]] = []
    hashes: set[str] = set()
    regression_sha256 = regression_sha256 or set()

    for item in papers:
        if not isinstance(item, dict):
            raise ValueError("Invalid held-out entry")
        paper_id = item.get("id")
        filename = item.get("pdf_filename")
        expected_pages = item.get("publisher_pdf_pages_reported")
        if not isinstance(paper_id, str) or not paper_id:
            raise ValueError("Held-out id is missing")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"{paper_id}: pdf_filename must be a simple filename")
        if type(expected_pages) is not int or expected_pages < 1:
            raise ValueError(f"{paper_id}: expected publisher page count is missing")

        path = (root / filename).resolve(strict=True)
        if path.parent != root or not path.is_file():
            raise ValueError(f"{paper_id}: PDF must be a regular file directly inside pdf_dir")
        raw = path.read_bytes()
        if not raw.startswith(b"%PDF-"):
            raise ValueError(f"{paper_id}: file does not have a PDF header")

        digest = sha256(raw).hexdigest()
        if digest in hashes:
            raise ValueError(f"{paper_id}: duplicate PDF bytes in held-out set")
        if digest in regression_sha256:
            raise ValueError(f"{paper_id}: PDF hash overlaps the regression corpus")
        try:
            document = fitz.open(stream=raw, filetype="pdf")
        except Exception as exc:
            raise ValueError(f"{paper_id}: PyMuPDF could not open the exact PDF bytes") from exc
        try:
            if not document.is_pdf or document.page_count < 1:
                raise ValueError(f"{paper_id}: invalid or empty PDF")
            actual_pages = document.page_count
            metadata = document.metadata or {}
        finally:
            document.close()

        if actual_pages != expected_pages:
            raise ValueError(
                f"{paper_id}: page count mismatch; publisher reports {expected_pages}, "
                f"exact local PDF contains {actual_pages}"
            )

        hashes.add(digest)
        updated.append({
            **item,
            "pdf_sha256": digest,
            "sha256_algorithm": "SHA-256",
            "pdf_byte_length": len(raw),
            "pdf_bytes_verified": True,
            "actual_page_count": actual_pages,
            "pdf_metadata_title": metadata.get("title") or None,
            "lock_commit": None,
            "status": "BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT",
        })

    result = dict(manifest)
    result["heldout_papers"] = updated
    result["record_type"] = "HELDOUT_BINARY_VERIFIED_PENDING_GIT_COMMIT"
    result["release_gate_status"] = "Q0_BLOCKED_UNTIL_GIT_LOCK_COMMIT_AND_BASELINE_CHECK"
    result["warning"] = (
        "PDF bytes and page counts verified locally. Commit this exact manifest, "
        "record that commit SHA in lock_commit in a follow-up commit, and only then "
        "create a new candidate branch from the frozen production baseline."
    )
    return result


def _load_regression_hashes(path: Path | None) -> set[str]:
    if path is None:
        return set()
    value = json.loads(path.read_text(encoding="utf-8"))
    papers = value.get("papers", []) if isinstance(value, dict) else []
    hashes = set()
    for paper in papers:
        if isinstance(paper, dict) and isinstance(paper.get("sha256"), str):
            hashes.add(paper["sha256"])
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description="Lock exact preselected held-out PDF bytes")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--regression-manifest", type=Path,
                        help="Optional JSON manifest with papers[].sha256 to prevent corpus overlap")
    parser.add_argument("--out", required=True, type=Path,
                        help="Private output JSON; PDF bytes are never included")
    args = parser.parse_args()
    result = lock_heldout_pdfs(
        _load(args.manifest),
        args.pdf_dir,
        regression_sha256=_load_regression_hashes(args.regression_manifest),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "record_type": result["record_type"],
        "papers": [
            {"id": x["id"], "sha256": x["pdf_sha256"], "pages": x["actual_page_count"],
             "bytes": x["pdf_byte_length"]}
            for x in result["heldout_papers"]
        ],
        "out": str(args.out),
        "note": "Git lock commit still required before a candidate branch is created.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
