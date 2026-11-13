#!/usr/bin/env python3
"""Screening evaluator for PaperSignal finance-paper benchmark (stdlib only).

This is not a semantic judge. Alias coverage is a diagnostic signal and must
be followed by human review against the publisher PDF.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

RATING = {"correct": 1.0, "partial": 0.5, "missing": 0.0, "incorrect": 0.0}
CITATION_RATING = {"exact": 1.0, "partial": 0.5, "missing": 0.0, "wrong": 0.0}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def flatten_strings(value: Any, *, omit_keys: set[str] | None = None) -> list[str]:
    omit_keys = omit_keys or {"warnings"}
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in omit_keys:
                continue
            found.extend(flatten_strings(item, omit_keys=omit_keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_strings(item, omit_keys=omit_keys))
    elif isinstance(value, str):
        found.append(value)
    elif isinstance(value, (int, float)):
        found.append(str(value))
    return found


def fact_alias_match(fact: dict[str, Any], analysis_text: str) -> bool:
    aliases = fact.get("aliases", [])
    return any(normalize(alias) in analysis_text for alias in aliases if len(normalize(alias)) >= 2)


def collect_evidence(value: Any) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence" and isinstance(item, list):
                evidence.extend(x for x in item if isinstance(x, dict))
            else:
                evidence.extend(collect_evidence(item))
    elif isinstance(value, list):
        for item in value:
            evidence.extend(collect_evidence(item))
    # De-duplicate exact page/quote pairs.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for item in evidence:
        try:
            key = (int(item.get("page", -1)), str(item.get("quote", "")))
        except (TypeError, ValueError):
            continue
        if key not in seen:
            seen.add(key)
            deduped.append({"page": key[0], "quote": key[1]})
    return deduped


def citation_precision(evidence: list[dict[str, Any]], pages: dict[str, str] | None) -> float | None:
    if pages is None:
        return None
    if not evidence:
        return 0.0
    valid = 0
    for item in evidence:
        page_text = pages.get(str(item["page"]), "")
        if item["quote"] and item["quote"] in page_text:
            valid += 1
    return valid / len(evidence)


def claim_evidence_coverage(analysis: dict[str, Any]) -> float | None:
    claims: list[dict[str, Any]] = []
    for key in ("hypotheses", "contributions", "findings", "robustness_checks", "limitations", "implications"):
        value = analysis.get(key, [])
        if isinstance(value, list):
            claims.extend(item for item in value if isinstance(item, dict))
    methodology = analysis.get("methodology")
    if isinstance(methodology, dict):
        variables = methodology.get("variables", [])
        if isinstance(variables, list):
            claims.extend(item for item in variables if isinstance(item, dict))
    if not claims:
        return None
    supported = sum(1 for item in claims if isinstance(item.get("evidence"), list) and item["evidence"])
    return supported / len(claims)


def human_review_score(review: dict[str, Any] | None) -> dict[str, float | None]:
    if not review:
        return {"fact_score": None, "citation_score": None, "unsupported_claim_score": None, "human_score": None}
    fact_ratings = review.get("facts", {})
    fact_values = [RATING[v] for v in fact_ratings.values() if v in RATING]
    fact_score = sum(fact_values) / len(fact_values) if fact_values else None
    citation_ratings = review.get("citations", {})
    citation_values = [CITATION_RATING[v] for v in citation_ratings.values() if v in CITATION_RATING]
    citation_score = sum(citation_values) / len(citation_values) if citation_values else None
    reviewed_claims = int(review.get("reviewed_claims", 0) or 0)
    unsupported_claims = int(review.get("unsupported_claims", 0) or 0)
    unsupported_score = (
        max(0.0, 1.0 - unsupported_claims / reviewed_claims)
        if reviewed_claims > 0 else None
    )
    components = [x for x in (fact_score, citation_score, unsupported_score) if x is not None]
    human_score = sum(components) / len(components) if components else None
    return {
        "fact_score": fact_score,
        "citation_score": citation_score,
        "unsupported_claim_score": unsupported_score,
        "human_score": human_score,
    }


def evaluate_one(
    paper: dict[str, Any],
    analysis: dict[str, Any],
    *,
    review: dict[str, Any] | None = None,
    pages: dict[str, str] | None = None,
) -> dict[str, Any]:
    text = normalize(" ".join(flatten_strings(analysis)))
    facts = paper.get("gold_facts", [])
    weighted_total = sum(float(f.get("weight", 1)) for f in facts)
    weighted_hit = sum(
        float(f.get("weight", 1)) for f in facts if fact_alias_match(f, text)
    )
    matched = [f["id"] for f in facts if fact_alias_match(f, text)]
    missing = [f["id"] for f in facts if not fact_alias_match(f, text)]
    evidence = collect_evidence(analysis)
    human = human_review_score(review)
    return {
        "paper_id": paper["id"],
        "title": paper["title"],
        "model": analysis.get("model"),
        "provider": analysis.get("provider"),
        "mode": analysis.get("mode"),
        "gold_fact_coverage_screen": weighted_hit / weighted_total if weighted_total else None,
        "gold_fact_matches": matched,
        "gold_fact_missing": missing,
        "evidence_count": len(evidence),
        "claim_evidence_coverage": claim_evidence_coverage(analysis),
        "citation_page_precision": citation_precision(evidence, pages),
        **human,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("benchmark/manifest.json"))
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--pages-dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/scorecard.json"))
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    results_data = load_json(args.results)
    rows = results_data.get("results", results_data) if isinstance(results_data, dict) else results_data
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        paper_id = row.get("paper_id") or row.get("benchmark_id")
        analysis = row.get("analysis") or row.get("result")
        if paper_id and isinstance(analysis, dict):
            by_id[str(paper_id)] = analysis

    reviews_data = load_json(args.reviews) if args.reviews else {}
    reviews = reviews_data.get("reviews", reviews_data) if isinstance(reviews_data, dict) else {}
    score_rows = []
    for paper in manifest["papers"]:
        paper_id = paper["id"]
        analysis = by_id.get(paper_id)
        if not analysis:
            score_rows.append({"paper_id": paper_id, "title": paper["title"], "status": "not_run"})
            continue
        page_text = None
        if args.pages_dir:
            page_file = args.pages_dir / f"{paper_id}.json"
            if page_file.exists():
                page_text = load_json(page_file)
        score_rows.append(evaluate_one(
            paper,
            analysis,
            review=reviews.get(paper_id),
            pages=page_text,
        ))

    completed = [row for row in score_rows if row.get("status") != "not_run"]
    auto_scores = [row["gold_fact_coverage_screen"] for row in completed if row.get("gold_fact_coverage_screen") is not None]
    human_scores = [row["human_score"] for row in completed if row.get("human_score") is not None]
    output = {
        "benchmark_version": manifest["benchmark_version"],
        "paper_count": len(manifest["papers"]),
        "completed_count": len(completed),
        "not_run_count": len(manifest["papers"]) - len(completed),
        "mean_gold_fact_coverage_screen": sum(auto_scores) / len(auto_scores) if auto_scores else None,
        "mean_human_score": sum(human_scores) / len(human_scores) if human_scores else None,
        "warning": "Alias coverage is not semantic accuracy. Human review against publisher PDFs is required.",
        "results": score_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in (
        "paper_count", "completed_count", "not_run_count",
        "mean_gold_fact_coverage_screen", "mean_human_score", "out"
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
