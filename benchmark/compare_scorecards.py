#!/usr/bin/env python3
"""Compare two PaperSignal benchmark scorecards without imputing missing values."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

METRICS = (
    "gold_fact_coverage_screen",
    "claim_evidence_coverage",
    "citation_page_precision",
    "human_score",
)


def _rows(scorecard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in scorecard.get("results", []):
        if isinstance(row, dict) and row.get("paper_id"):
            result[str(row["paper_id"])] = row
    return result


def compare_scorecards(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    before, after = _rows(baseline), _rows(candidate)
    paper_ids = sorted(set(before) | set(after))
    comparisons = []
    aggregate: dict[str, dict[str, Any]] = {}
    for metric in METRICS:
        pairs = []
        for paper_id in sorted(set(before) & set(after)):
            a, b = before[paper_id].get(metric), after[paper_id].get(metric)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                pairs.append((paper_id, float(a), float(b)))
        deltas = [b - a for _, a, b in pairs]
        aggregate[metric] = {
            "paired_count": len(pairs),
            "baseline_mean": sum(a for _, a, _ in pairs) / len(pairs) if pairs else None,
            "candidate_mean": sum(b for _, _, b in pairs) / len(pairs) if pairs else None,
            "mean_delta": sum(deltas) / len(deltas) if deltas else None,
            "improved_count": sum(1 for d in deltas if d > 0),
            "regressed_count": sum(1 for d in deltas if d < 0),
            "unchanged_count": sum(1 for d in deltas if d == 0),
        }
    for paper_id in paper_ids:
        a, b = before.get(paper_id), after.get(paper_id)
        row = {
            "paper_id": paper_id,
            "baseline_present": a is not None,
            "candidate_present": b is not None,
            "metrics": {},
        }
        for metric in METRICS:
            av = a.get(metric) if a else None
            bv = b.get(metric) if b else None
            valid = isinstance(av, (int, float)) and isinstance(bv, (int, float))
            row["metrics"][metric] = {
                "baseline": av if isinstance(av, (int, float)) else None,
                "candidate": bv if isinstance(bv, (int, float)) else None,
                "delta": float(bv) - float(av) if valid else None,
                "paired": valid,
            }
        comparisons.append(row)
    return {
        "baseline_version": baseline.get("benchmark_version"),
        "candidate_version": candidate.get("benchmark_version"),
        "paper_count_union": len(paper_ids),
        "paired_paper_count": len(set(before) & set(after)),
        "aggregate": aggregate,
        "papers": comparisons,
        "warning": (
            "Paired scorecard comparison is descriptive, not proof of causal model improvement. "
            "Missing scores are excluded, never imputed as zero. Alias coverage is not semantic accuracy; "
            "citation precision requires exact page text and human score requires explicit human review."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/comparison.json"))
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = compare_scorecards(baseline, candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"paired_paper_count": result["paired_paper_count"], "aggregate": result["aggregate"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
