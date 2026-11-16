"""Run frozen-engine vs Docling Parse complete-model analysis, no production writes.

This benchmark invokes the exact live v6.4.2 downstream llm_result() from
app.main twice on each SHA-locked original, changing ONLY extract_pages.
Both arms use no prior findings, exactly the same Gemini config and strict
evidence / finding repair / rescue validation. Keep source and results private.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import logging
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import time
from typing import Any
from uuid import uuid4

import httpx

from app import main as engine
from benchmark.evaluate import evaluate_one, collect_evidence
from benchmark.table_shadow import StorageSource
ROOT = Path(__file__).resolve().parents[1]
MODES = ("baseline", "docling_parse")
MAX_SUBPROCESS_SECONDS = 150
MAX_ANALYSIS_SECONDS = 440
DEFAULT_IDS = ("B01", "B02")
MAX_PAIRS = 3

def baseline_pages(pdf_bytes: bytes) -> tuple[int, list[dict[str, Any]]]:
    """Byte-for-byte logic equivalence to production 8cd5e37 extract_pages."""
    import fitz  # Control ONLY; Docling Parse arm never imports or invokes fitz.
    if not pdf_bytes.startswith(b"%PDF-") or len(pdf_bytes) > engine.MAX_BYTES:
        raise ValueError("Invalid PDF size or signature")
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("Encrypted PDF")
            count = len(document)
            if count < 1 or count > engine.MAX_PAGES:
                raise ValueError("Invalid number of pages")
            pages = [
                {"page": index + 1,
                 "text": re.sub(r"\s+", " ", engine.sanitize_pdf_text(
                     document[index].get_text("text"))).strip()[:engine.MAX_PAGE_CHARS]}
                for index in range(min(count, engine.MAX_PAGES_TO_SCAN))
            ]
            pages = [p for p in pages if p["text"]]
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise ValueError("Corrupt PDF") from exc
    if not pages:
        raise ValueError("No extractable PDF text")
    return count, pages

def parser_child(pdf_path: Path, mode: str, output: Path) -> int:
    if mode not in MODES:
        raise ValueError("Unknown parse arm")
    start = time.perf_counter()
    try:
        pdf = pdf_path.read_bytes()
        if mode == "baseline":
            count, pages = baseline_pages(pdf)
        else:
            from app.pdf_replacement import extract_pages
            count, pages = extract_pages(pdf, backend="docling_parse")
        # Strict 1-based, unique, source-page identity.
        numbers = [p["page"] for p in pages]
        if not pages or len(numbers) != len(set(numbers)) or sorted(numbers) != numbers:
            raise ValueError("Bad page-located parser output")
        result = {"status": "ok", "page_count": count, "pages": pages,
                  "parse_seconds": round(time.perf_counter() - start, 4),
                  "child_peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)}
    except Exception as exc:
        result = {"status": "failed", "error_type": type(exc).__name__}
    output.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return 0 if result["status"] == "ok" else 2

def isolated_parser(pdf: Path, mode: str, output: Path) -> dict:
    env = dict(os.environ)
    for name in list(env):
        if name.startswith(("SUPABASE_", "GEMINI_", "OPENAI_", "ANTHROPIC_", "BENCHMARK_", "FULL_AB_")):
            env.pop(name)
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_TELEMETRY="1")
    started = time.perf_counter()
    try:
        process = subprocess.run(
            [sys.executable, "-m", "benchmark.full_analysis_ab",
             "--child", str(pdf), "--mode", mode, "--output", str(output)],
            env=env, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=MAX_SUBPROCESS_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "wall_seconds": round(time.perf_counter() - started, 4)}
    if not output.exists():
        return {"status": "process_error", "exit_code": process.returncode,
                "wall_seconds": round(time.perf_counter() - started, 4)}
    data = json.loads(output.read_text(encoding="utf-8"))
    data["wall_seconds"] = round(time.perf_counter() - started, 4)
    if process.returncode and data["status"] == "ok":
        return {"status": "process_error", "exit_code": process.returncode,
                "wall_seconds": data["wall_seconds"]}
    return data

def find_summary(result: dict[str, Any], manifest_entry: dict, pages: list[dict]) -> dict:
    findings = result.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError("Unexpected findings structure")
    status_counts = Counter(
        f.get("verification", {}).get("status", "unknown")
        for f in findings if isinstance(f, dict)
    )
    score = evaluate_one(manifest_entry, result,
                         pages={str(p["page"]): p["text"] for p in pages})
    method = result.get("methodology") or {}
    evidence = collect_evidence(result)
    return {
        "mode": result.get("mode"),
        "analysis_version": result.get("analysis_version"),
        "model": result.get("model"),
        "models_used": result.get("models_used"),
        "findings_count": len(findings),
        "screen_passed_findings": status_counts.get("screen_passed", 0),
        "review_required_findings": status_counts.get("review", 0),
        "findings_coverage_status": (result.get("findings_coverage") or {}).get("status"),
        "findings_repair": result.get("findings_verification"),
        "methodology_repair": result.get("methodology_verification"),
        "methodology_has_evidence": bool(method.get("evidence")),
        "methodology_variables": len(method.get("variables") or []),
        "source_evidence_quotes": len(evidence),
        "within_input_page_exact_citation_share": score.get("citation_page_precision"),
        "claim_evidence_coverage": score.get("claim_evidence_coverage"),
        "lexical_gold_alias_coverage_screen": score.get("gold_fact_coverage_screen"),
        "lexical_gold_aliases_matched": score.get("gold_fact_matches"),
        "lexical_gold_aliases_missing": score.get("gold_fact_missing"),
        "verified_human_precision": None,
    }

def analyze_with_model(count: int, pages: list[dict]) -> tuple[dict, list[dict], float]:
    """Exact unchanged async llm_result() including repair/rescue; observe HTTP usage."""
    if engine.active_ai_provider() != "gemini":
        raise RuntimeError("Configured Gemini model not available; extractive fallback forbidden")
    usage: list[dict[str, Any]] = []
    original_post = httpx.AsyncClient.post
    async def traced_post(self, url, *args, **kwargs):
        if not isinstance(url, str) or "generativelanguage.googleapis.com/v1beta/models/" not in url:
            return await original_post(self, url, *args, **kwargs)
        model = url.split("/models/", 1)[1].split(":", 1)[0]
        began = time.perf_counter()
        record: dict[str, Any] = {"model": model}
        try:
            response = await original_post(self, url, *args, **kwargs)
            record["status_code"] = response.status_code
            if response.is_success:
                payload = response.json()
                m = payload.get("usageMetadata") or {}
                record["usage"] = {name: m.get(name) for name in
                    ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount")}
                records = payload.get("candidates") or []
                record["finish_reason"] = records[0].get("finishReason") if records else "no_candidates"
            return response
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        finally:
            record["wall_seconds"] = round(time.perf_counter() - began, 4)
            usage.append(record)
    httpx.AsyncClient.post = traced_post
    began = time.perf_counter()
    try:
        # No production job/analysis writes and no prior-result revalidation advantage.
        result = asyncio.run(asyncio.wait_for(
            engine.llm_result(count, pages, prior_findings=[]),
            timeout=MAX_ANALYSIS_SECONDS))
        if result.get("mode") != "llm":
            raise RuntimeError("Not a full model-backed result")
        return result, usage, round(time.perf_counter() - began, 4)
    finally:
        httpx.AsyncClient.post = original_post

def tally_usage(records: list[dict]) -> dict:
    sums: dict[str, int] = {}
    for r in records:
        for k, v in (r.get("usage") or {}).items():
            if isinstance(v, int) and v >= 0:
                sums[k] = sums.get(k, 0) + v
    return {
        "api_attempts": len(records),
        "status_codes": [r.get("status_code") for r in records],
        "models_attempted": [r.get("model") for r in records],
        "provider_wall_seconds": round(sum(r.get("wall_seconds", 0) for r in records), 4),
        "token_counts_observed": sums,
        "has_rate_limit": any(r.get("status_code") == 429 for r in records),
        "usage_complete": all("usage" in r for r in records),
        "cost_usd": None,
    }

def pair_status(items: list[dict]) -> dict:
    matched = all(r.get("status") == "ok" for r in items) and len(items) == 2
    a, b = (next((i for i in items if i["backend"] == m), {}) for m in MODES)
    qa, qb = a.get("summary") or {}, b.get("summary") or {}
    if not matched:
        return {"paired": False, "comparable": False,
                "reason": "One or both model/parser analysis arms failed"}
    models_same = qa.get("models_used") == qb.get("models_used")
    return {
        "paired": True,
        "comparable": models_same,
        "same_model_path": models_same,
        "baseline_screen_passed": qa.get("screen_passed_findings"),
        "docling_screen_passed": qb.get("screen_passed_findings"),
        "baseline_review": qa.get("review_required_findings"),
        "docling_review": qb.get("review_required_findings"),
        "baseline_lexical_gold": qa.get("lexical_gold_alias_coverage_screen"),
        "docling_lexical_gold": qb.get("lexical_gold_alias_coverage_screen"),
        "warning": "Single runs are nondeterministic and lexical screens are not human precision.",
    }

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--child", type=Path)
    p.add_argument("--mode", choices=MODES)
    p.add_argument("--output", type=Path)
    p.add_argument("--ids", nargs="+", default=list(DEFAULT_IDS))
    args = p.parse_args()
    if args.child:
        return parser_child(args.child, args.mode, args.output)
    if os.getenv("FULL_AB_ALLOW_MODEL_CALLS") != "1" or engine.active_ai_provider() != "gemini":
        raise RuntimeError("Refusing non-Gemini or unapproved full-analysis model benchmark")
    if len(args.ids) < 1 or len(args.ids) > MAX_PAIRS or len(set(args.ids)) != len(args.ids):
        p.error("Specify 1..3 distinct benchmark paper IDs")
    source = StorageSource()
    if not source.upload:
        raise RuntimeError("Private artifact persistence required; refusing silent results loss")
    manifest = json.loads((ROOT / "benchmark/manifest.json").read_text(encoding="utf-8"))["papers"]
    full = json.loads((ROOT / "benchmark/table_corpus.sha256.json").read_text(encoding="utf-8"))["papers"]
    allowed = {row["id"]: row for row in full}
    papers = {row["id"]: row for row in manifest}
    if any(paper_id not in allowed or paper_id not in papers for paper_id in args.ids):
        p.error("Unrecognized benchmark corpus ID")
    # Prevent accidental default log output of model error bodies and PDF snippets.
    logging.basicConfig(level=logging.CRITICAL)
    engine.log.disabled = True
    source.run_id = "full-ab-" + uuid4().hex
    scores = []
    stop_reason = None
    print(json.dumps({
        "event": "full_ab_start", "ids": args.ids, "run_id": source.run_id,
        "frozen_engine": "finance-structured-v6.4.2",
        "same_model_and_prompt": True, "prior_findings_both_empty": True,
        "storage_writes": "private_new_artifacts_only",
    }), flush=True)
    for i, paper_id in enumerate(args.ids):
        pdf, identity, owner = source.get_pdf(allowed[paper_id])
        sequence = list(MODES if i % 2 == 0 else reversed(MODES))
        runs = []
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "locked-source.pdf"
            pdf_path.write_bytes(pdf)
            for arm in sequence:
                outcome: dict = {"backend": arm}
                try:
                    extraction = isolated_parser(pdf_path, arm, Path(directory) / (arm + ".json"))
                    outcome["extraction"] = {k: v for k, v in extraction.items() if k != "pages"}
                    if extraction["status"] != "ok":
                        raise RuntimeError("Parser did not complete")
                    if extraction["page_count"] != allowed[paper_id]["pages"]:
                        raise RuntimeError("Page count changed")
                    result, trace, model_seconds = analyze_with_model(
                        extraction["page_count"], extraction["pages"])
                    outcome["status"] = "ok"
                    outcome["analysis_wall_seconds"] = model_seconds
                    outcome["total_wall_seconds_excl_storage"] = round(
                        model_seconds + extraction["wall_seconds"], 4)
                    outcome["usage"] = tally_usage(trace)
                    outcome["summary"] = find_summary(result, papers[paper_id], extraction["pages"])
                    outcome["result"] = engine.sanitize_json_payload(result)
                except Exception as exc:
                    outcome["status"] = "failed"
                    outcome["error_type"] = type(exc).__name__
                    outcome["failure_stage"] = "extract" if outcome.get("extraction", {}).get("status") != "ok" else "model_or_validation"
                    # A pair is incomplete; stop after recording this paper so
                    # quota errors do not cascade into additional model attempts.
                    stop_reason = "analysis_arm_failed"
                runs.append(outcome)
                safe_log = {key: val for key, val in outcome.items()
                            if key not in ("result",)}
                print(json.dumps({"event": "full_ab_arm", "paper": paper_id, **safe_log},
                                 ensure_ascii=False, allow_nan=False), flush=True)
                if stop_reason:
                    break
        pairing = pair_status(runs)
        packet = {"id": paper_id, "source_sha256": identity["sha256"],
                  "analysis_version": engine.ANALYSIS_VERSION,
                  "order": sequence, "runs": runs, "paired_screen": pairing,
                  "no_source_or_production_data_mutation": True,
                  "independently_reviewed": False,
                  "provider_price_verified": False}
        saved = source.save_artifact(owner, paper_id, packet)
        if not saved:
            raise RuntimeError("Private artifact upload disabled")
        scores.append({"paper": paper_id, "pair": pairing, "arms": [
            {k: v for k, v in outcome.items() if k not in ("result",)}
            for outcome in runs]})
        print(json.dumps({"event": "full_ab_pair", "paper": paper_id, **pairing,
                          "artifact_private_saved": True}, ensure_ascii=False), flush=True)
        if stop_reason:
            break
    overall = {"event": "full_ab_complete", "run_id": source.run_id,
               "requested_papers": len(args.ids), "completed_pair_packets": len(scores),
               "fully_paired": sum(1 for x in scores if x["pair"]["paired"]),
               "matched_provider_model_path": sum(1 for x in scores if x["pair"]["comparable"]),
               "halt_reason": stop_reason,
               "human_verified_cell_accuracy": None,
               "production_modified": False, "adoption_eligible": False}
    print(json.dumps(overall, ensure_ascii=False), flush=True)
    return 0 if stop_reason is None else 2

if __name__ == "__main__":
    raise SystemExit(main())
