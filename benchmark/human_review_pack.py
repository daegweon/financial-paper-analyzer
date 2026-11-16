"""Generate a source-oriented, *unapproved* human-review queue from past analyses.

Input is a local JSON export; output is local-only and may contain paper text.
No LLM verdict, screening status or guessed PDF hash is ever human gold.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

EXPECTED = {"B01": 4, "B02": 6, "B03": 1, "B05": 2, "B09": 3, "B10": 2}
REVIEW_STATUSES = {"review", "review_required"}
LEGACY_VERSION = "finance-structured-v6.3.9"


def _analysis_rows(data: Any) -> list[dict]:
    if isinstance(data, dict):
        data = data.get("results", data.get("rows"))
    if not isinstance(data, list):
        raise ValueError("Expected list of exported analysis rows (or a 'results' list).")
    return data


def _evidence(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    items = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        page = entry.get("page")
        quote = entry.get("quote")
        if type(page) is int and page > 0 and isinstance(quote, str) and quote.strip():
            items.append({"page": page, "quote": quote})
    return items


def _source_pdf(paper_id: str, pdf_dir: Path | None) -> dict:
    if pdf_dir is None:
        return {"sha256": None, "file_present": False, "pdf_pages_verified": False}
    path = pdf_dir / f"{paper_id}.pdf"
    if not path.is_file():
        return {"sha256": None, "file_present": False, "pdf_pages_verified": False}
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError(f"{paper_id}: source is not a PDF")
    # SHA of exactly the bytes checked by a later, independent human reviewer.
    digest = sha256(data).hexdigest()
    return {"sha256": digest, "file_present": True, "pdf_pages_verified": False}


def build_review_pack(data: Any, *, pdf_dir: Path | None = None) -> dict:
    """Require all 10 legacy paper rows and the exact historical review counts."""
    rows = _analysis_rows(data)
    by_id: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid export row")
        paper_id = row.get("paper_id") or row.get("benchmark_id")
        if paper_id not in {f"B{i:02d}" for i in range(1, 11)}:
            continue
        if paper_id in by_id:
            raise ValueError(f"Duplicated paper_id {paper_id}; select one frozen analysis per paper")
        analysis = row.get("analysis") or row.get("result")
        if not isinstance(analysis, dict):
            raise ValueError(f"{paper_id}: missing structured analysis")
        version = analysis.get("analysis_version") or row.get("analysis_version")
        if version != LEGACY_VERSION:
            raise ValueError(f"{paper_id}: expected frozen {LEGACY_VERSION}, got {version!r}")
        by_id[paper_id] = analysis

    expected_papers = {f"B{i:02d}" for i in range(1, 11)}
    if set(by_id) != expected_papers:
        raise ValueError(f"Missing B01-B10: {sorted(expected_papers - set(by_id))}")

    cases: list[dict] = []
    counts = Counter()
    source_state = {}
    for paper_id in sorted(by_id):
        pdf = _source_pdf(paper_id, pdf_dir)
        source_state[paper_id] = pdf
        findings = by_id[paper_id].get("findings", [])
        if not isinstance(findings, list):
            raise ValueError(f"{paper_id}: invalid findings list")
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                raise ValueError(f"{paper_id}: invalid finding at {index}")
            verification = finding.get("verification") or {}
            if not isinstance(verification, dict):
                raise ValueError(f"{paper_id}: invalid verification at {index}")
            if verification.get("status") not in REVIEW_STATUSES:
                continue
            counts[paper_id] += 1
            fingerprint = sha256(json.dumps(
                {"paper_id": paper_id, "index": index, "finding": finding},
                sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            cases.append({
                "case_id": f"{paper_id}-{index:03d}-{fingerprint[:12]}",
                "paper_id": paper_id,
                "finding_index": index,
                "finding_sha256": fingerprint,
                "analysis_version": LEGACY_VERSION,
                "pdf_sha256": pdf["sha256"],
                "claim": finding.get("claim", ""),
                "estimate": finding.get("estimate", ""),
                "direction": finding.get("direction", ""),
                "statistical_significance": finding.get("statistical_significance", ""),
                "table_reference": finding.get("table_reference", ""),
                "model_or_column": finding.get("model_or_column", ""),
                "direct_evidence": _evidence(finding.get("evidence")),
                "legend_evidence": _evidence(finding.get("significance_legend_evidence")),
                "machine_screen": verification,
                "source_review": {
                    "source_page": None, "exact_quote_confirmed": None,
                    "table_row": None, "model_column": None,
                    "coefficient_sign_confirmed": None,
                    "standard_error_vs_std_dev_checked": None,
                    "p_value_or_star_legend_confirmed": None,
                },
                "human_reviews": [],
                "adjudication": None,
                "status": "UNREVIEWED",
            })
    actual = {p: counts[p] for p in EXPECTED}
    if actual != EXPECTED or sum(counts.values()) != 18:
        raise ValueError(f"Historical findings changed: expected {EXPECTED}, found {dict(counts)}")

    return {
        "record_type": "UNREVIEWED_SOURCE_QUEUE_NOT_HUMAN_GOLD",
        "analysis_version": LEGACY_VERSION,
        "count": len(cases),
        "counts": actual,
        "source_pdfs": source_state,
        "cases": cases,
        "warning": "This queue is a machine-derived triage artifact; actual independent human PDF/page/table reviews are REQUIRED.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export 18 unresolved historical findings, without false approvals")
    parser.add_argument("--analyses", required=True, type=Path,
                        help="JSON export with exactly one v6.3.9 analysis per B01-B10 paper")
    parser.add_argument("--pdf-dir", type=Path, help="Directory of B01.pdf to B10.pdf for SHA-256 fingerprinting")
    parser.add_argument("--out", required=True, type=Path,
                        help="LOCAL PRIVATE output JSON: do not commit source quotes to GitHub")
    args = parser.parse_args()
    result = build_review_pack(json.loads(args.analyses.read_text(encoding="utf-8")), pdf_dir=args.pdf_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "count": result["count"], "counts": result["counts"],
        "pdfs_with_sha256": sum(bool(x["sha256"]) for x in result["source_pdfs"].values()),
        "all_reviews_unapproved": all(x["status"] == "UNREVIEWED" for x in result["cases"]),
        "out": str(args.out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
