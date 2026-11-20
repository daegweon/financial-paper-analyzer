#!/usr/bin/env python3
"""Diagnose evidence and numeric-verification gaps in exported PaperSignal analyses."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

_NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")
_NUMERIC_KEYS = ("estimate", "coefficient", "statistical_significance", "significance", "t_statistic", "p_value")


def _evidence(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [x for x in value if isinstance(x, dict) and isinstance(x.get("quote"), str) and x["quote"].strip()]


def _numeric_tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    text = str(value).replace(",", "")
    return {x.replace(",", "") for x in _NUMBER.findall(text)}


def diagnose_finding(finding: dict[str, Any], pages: dict[str, str] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    claim = str(finding.get("claim") or finding.get("text") or "")
    evidence = _evidence(finding.get("evidence"))
    finding_id = str(finding.get("id") or finding.get("finding_id") or "finding")
    if not evidence:
        issues.append({"code": "missing_direct_evidence", "severity": "high", "finding_id": finding_id})
    elif pages is not None:
        for item in evidence:
            page = str(item.get("page", ""))
            page_text = pages.get(page, "")
            if not page_text or item["quote"] not in page_text:
                issues.append({"code": "quote_not_found_on_page", "severity": "high", "finding_id": finding_id})
                break

    claimed_numbers: set[str] = set()
    for key in _NUMERIC_KEYS:
        claimed_numbers |= _numeric_tokens(finding.get(key))
    if claimed_numbers and evidence:
        evidence_text = " ".join(item["quote"] for item in evidence)
        evidence_numbers = _numeric_tokens(evidence_text)
        missing = claimed_numbers - evidence_numbers
        if missing:
            issues.append({
                "code": "numeric_claim_not_in_direct_quote",
                "severity": "high",
                "finding_id": finding_id,
                "details": ",".join(sorted(missing)),
            })
    if claim and not evidence:
        issues.append({"code": "claim_without_citation", "severity": "high", "finding_id": finding_id})
    return issues


def diagnose(results: Any, pages_by_paper: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
    rows = results.get("results", results) if isinstance(results, dict) else results
    report_rows = []
    counts: dict[str, int] = {}
    if not isinstance(rows, list):
        rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        paper_id = str(row.get("paper_id") or row.get("benchmark_id") or "unknown")
        analysis = row.get("analysis") or row.get("result") or {}
        if not isinstance(analysis, dict):
            continue
        findings = analysis.get("findings", [])
        findings = findings if isinstance(findings, list) else []
        issues = []
        for finding in findings:
            if isinstance(finding, dict):
                issues.extend(diagnose_finding(finding, (pages_by_paper or {}).get(paper_id)))
        for issue in issues:
            counts[issue["code"]] = counts.get(issue["code"], 0) + 1
        report_rows.append({
            "paper_id": paper_id,
            "finding_count": len(findings),
            "issue_count": len(issues),
            "issues": issues,
        })
    return {
        "paper_count": len(report_rows),
        "finding_count": sum(x["finding_count"] for x in report_rows),
        "issue_count": sum(x["issue_count"] for x in report_rows),
        "issue_counts": counts,
        "papers": report_rows,
        "warning": "Automated triage only. It does not establish semantic correctness or approve findings.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--pages-dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/diagnostics.json"))
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    pages = {}
    if args.pages_dir:
        for path in args.pages_dir.glob("*.json"):
            pages[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    report = diagnose(data, pages)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("paper_count", "finding_count", "issue_count", "issue_counts")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
