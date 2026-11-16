"""Deterministic zero-provider replay of stored v6.3.9 findings against both parsers.

NOT a new model-backed analysis: same frozen historical claims and source quotes
are revalidated using current v6.4.2 validators against exact-original PDF
pages extracted by either existing PyMuPDF or Docling Parse.

Store only new private benchmark JSON results. Never update analysis/job tables.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import tempfile
import time
from urllib.parse import urlencode
from uuid import uuid4

from app import main as engine
from benchmark.full_analysis_ab import isolated_parser
from benchmark.table_shadow import StorageSource

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmark/table_corpus.sha256.json"
HISTORICAL_VERSION = "finance-structured-v6.3.9"
MODES = ("baseline", "docling_parse")


def historical_result(source: StorageSource, spec: dict, owner: str) -> dict:
    q = urlencode({"select":"id,user_id","original_filename":"eq." + spec["filename"],"limit":2})
    body, _ = source.request("/rest/v1/papers?" + q)
    rows = json.loads(body)
    if len(rows) != 1 or rows[0]["user_id"] != owner:
        raise ValueError("Paper source ownership mismatch")
    paper_id = rows[0]["id"]
    q = urlencode({"select":"result,created_at",
                   "paper_id":"eq." + paper_id,
                   "status":"eq.completed",
                   "order":"created_at.desc",
                   "limit":"20"})
    body, _ = source.request("/rest/v1/analyses?" + q)
    records = json.loads(body)
    matches = [x["result"] for x in records
               if isinstance(x.get("result"), dict)
               and x["result"].get("analysis_version") == HISTORICAL_VERSION]
    if not matches:
        raise ValueError("Historical v6.3.9 analysis missing")
    return matches[0]


def all_page_quotes(raw: object) -> list[dict]:
    """Recursively include every cited source page, including legends."""
    quotes = []
    seen = set()
    def scan(value):
        if isinstance(value, dict):
            page, text = value.get("page"), value.get("quote")
            if type(page) is int and isinstance(text, str) and text.strip():
                key = (page, text)
                if key not in seen:
                    seen.add(key)
                    quotes.append({"page":page,"quote":text})
            for child in value.values():
                scan(child)
        elif isinstance(value, list):
            for child in value:
                scan(child)
    scan(raw)
    return quotes


def review_historical_against_pages(raw: dict, pages: list[dict]) -> dict:
    citations = all_page_quotes(raw)
    retained = sum(
        bool(engine.validate_evidence([item], pages))
        for item in citations
    )
    old_findings = raw.get("findings") or []
    if not isinstance(old_findings, list):
        raise ValueError("Unexpected historical findings")
    validated = engine._normalize_findings(old_findings, pages)
    statuses = Counter((item.get("verification") or {}).get("status")
                       for item in validated)
    accepted_ids = []
    for i, item in enumerate(old_findings[:8]):
        if isinstance(item, dict) and engine._normalize_findings([item], pages):
            accepted_ids.append(i)
    return {
        "stored_citations":len(citations),
        "citations_revalidated_on_parsed_page_text":retained,
        "citation_retention":round(retained/len(citations),4) if citations else None,
        "stored_findings":len(old_findings),
        "findings_preserving_direct_source_evidence":len(validated),
        "findings_screen_passed_by_current_validator":statuses.get("screen_passed",0),
        "findings_review_required_by_current_validator":statuses.get("review",0),
        "original_finding_indexes_with_evidence":accepted_ids,
        "pages_with_text":len(pages),
        "independently_human_reviewed":False,
        "note":"Historical claims replay; no new Gemini generation or source-cell accuracy proof",
    }


def main() -> int:
    import sys
    args=sys.argv[1:]
    if args and args != ["--all"]:
        raise ValueError("Only --all permitted")
    source = StorageSource()
    if not source.upload:
        raise RuntimeError("Private JSON artifact storage is required")
    source.run_id="replay-" + uuid4().hex
    specs=json.loads(CORPUS.read_text(encoding="utf-8"))["papers"]
    outputs=[]
    problems=[]
    print(json.dumps({"event":"replay_start","run_id":source.run_id,
                      "papers":len(specs),"historical_version":HISTORICAL_VERSION,
                      "provider_calls":0,"production_mutation":False}),flush=True)
    for spec in specs:
        try:
            pdf,identity,owner=source.get_pdf(spec)
            old=historical_result(source,spec,owner)
            variants=[]
            with tempfile.TemporaryDirectory() as path:
                src=Path(path)/"locked.pdf"
                src.write_bytes(pdf)
                for mode in MODES:
                    out=isolated_parser(src,mode,Path(path)/(mode+".json"))
                    if out.get("status")!="ok" or out.get("page_count")!=spec["pages"]:
                        variants.append({"backend":mode,"status":"failed",
                                         "error_type":out.get("error_type") or out.get("status")})
                        continue
                    variants.append({"backend":mode,"status":"ok",
                                     "extraction_wall_seconds":out["wall_seconds"],
                                     "child_peak_rss_mib":out.get("child_peak_rss_mib"),
                                     "metrics":review_historical_against_pages(old,out["pages"])})
            bundle={"id":spec["id"],"identity_sha256":identity["sha256"],
                    "source_version":HISTORICAL_VERSION,"current_validator_version":engine.ANALYSIS_VERSION,
                    "runs":variants,"no_ai_calls":True}
            if not source.save_artifact(owner,spec["id"],bundle):
                raise RuntimeError("Private persistence unavailable")
            safe={"event":"replay_paper","id":spec["id"],"runs":variants,
                  "saved_private":True}
            print(json.dumps(safe,ensure_ascii=False),flush=True)
            outputs.append({"id":spec["id"],"runs":variants})
        except Exception as exc:
            problems.append({"id":spec["id"],"error_type":type(exc).__name__})
            print(json.dumps({"event":"replay_error",**problems[-1]}),flush=True)
    summary={"event":"replay_summary","run_id":source.run_id,
             "papers_requested":len(specs),"papers_completed":len(outputs),
             "problems":problems,"provider_calls":0,
             "full_model_ab_completed":False,
             "human_gold_accuracy":None,"promotion_eligible":False}
    print(json.dumps(summary),flush=True)
    return int(bool(problems or any(r.get("status")!="ok" for paper in outputs for r in paper["runs"])))

if __name__=="__main__":
    raise SystemExit(main())
