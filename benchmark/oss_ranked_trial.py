"""Ranked, read-only complete PDF-parser replacement feasibility benchmark.

Order: pypdfium2 -> pdfplumber -> GROBID -> MinerU -> Marker.
The PyMuPDF baseline is a reference control only. All engines are evaluated
against EXACT original 10 SHA-locked private PDFs and the SAME previously
saved v6.3.9 claims with the unmodified v6.4.2 validation functions.

No new Gemini analysis; original engine, analyses, jobs and PDFs unchanged.
Uninstalled/model-backed/service-only candidates are recorded as NOT RUN,
never scored as zero precision. No public PDF text or owner identifiers in logs.
"""
from __future__ import annotations

from io import BytesIO
import json
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

from app import main as engine
from benchmark.full_analysis_ab import baseline_pages
from benchmark.full_analysis_replay import historical_result, review_historical_against_pages
from benchmark.table_shadow import StorageSource

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("pypdfium2", "pdfplumber", "grobid", "mineru", "marker")
LOCAL_EXECUTABLE = ("pypdfium2", "pdfplumber")
TIMEOUT = 100


def normalize_page(text: str) -> str:
    return re.sub(r"\s+", " ", engine.sanitize_pdf_text(text)).strip()[:engine.MAX_PAGE_CHARS]


def read_pages(pdf_bytes: bytes, mode: str) -> tuple[int, list[dict[str, Any]]]:
    """No fitz used by candidate parsers, same count/page/text contract."""
    if not isinstance(pdf_bytes, bytes) or not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF signature")
    if len(pdf_bytes) > engine.MAX_BYTES:
        raise ValueError("PDF exceeds resource limit")
    if mode == "baseline":
        return baseline_pages(pdf_bytes)
    if mode == "pypdfium2":
        import pypdfium2
        values = []
        with pypdfium2.PdfDocument(pdf_bytes) as doc:
            count = len(doc)
            if not 1 <= count <= engine.MAX_PAGES:
                raise ValueError("Invalid PDF page count")
            for i in range(min(count, engine.MAX_PAGES_TO_SCAN)):
                page = doc[i]
                try:
                    textpage = page.get_textpage()
                    try:
                        text = textpage.get_text_bounded()
                    finally:
                        textpage.close()
                finally:
                    page.close()
                txt = normalize_page(text)
                if txt:
                    values.append({"page":i+1,"text":txt})
        if not values:
            raise ValueError("No text in pypdfium2")
        return count, values
    if mode == "pdfplumber":
        import pdfplumber
        values = []
        with pdfplumber.open(BytesIO(pdf_bytes)) as doc:
            count = len(doc.pages)
            if not 1 <= count <= engine.MAX_PAGES:
                raise ValueError("Invalid PDF page count")
            for i in range(min(count, engine.MAX_PAGES_TO_SCAN)):
                txt = normalize_page(doc.pages[i].extract_text(layout=False) or "")
                if txt:
                    values.append({"page":i+1,"text":txt})
        if not values:
            raise ValueError("No text in pdfplumber")
        return count, values
    raise ValueError("Unconfigured parser mode: never silently use baseline")


def child(path: Path, mode: str, output: Path) -> int:
    began=time.perf_counter()
    try:
        count,pages=read_pages(path.read_bytes(),mode)
        numbers=[p["page"] for p in pages]
        if len(numbers)!=len(set(numbers)) or numbers!=sorted(numbers) or numbers[-1]>count:
            raise ValueError("Bad source-located page IDs")
        content={"status":"ok","page_count":count,"pages":pages,
                 "parser_seconds":round(time.perf_counter()-began,4),
                 "child_max_rss_mib":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,3)}
    except Exception as exc:
        content={"status":"failed","error_type":type(exc).__name__}
    output.write_text(json.dumps(content,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    return 0 if content["status"]=="ok" else 2


def run_child(pdf: Path, mode: str, output: Path) -> dict:
    env=dict(os.environ)
    for key in tuple(env):
        if key.startswith(("SUPABASE_","BENCHMARK_","GEMINI_","OPENAI_","ANTHROPIC_","FULL_AB_")):
            env.pop(key,None)
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    began=time.perf_counter()
    try:
        proc=subprocess.run([sys.executable,"-m","benchmark.oss_ranked_trial",
                             "--child",str(pdf),"--engine",mode,"--output",str(output)],
                            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                            check=False,timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"status":"timeout","wall_seconds":round(time.perf_counter()-began,4)}
    data=json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"status":"process_error"}
    data["wall_seconds"]=round(time.perf_counter()-began,4)
    if proc.returncode and data.get("status")=="ok":
        return {"status":"process_error","exit_code":proc.returncode,"wall_seconds":data["wall_seconds"]}
    return data


def blocked_later_candidates() -> list[dict]:
    """Feasibility gates, NOT simulated source evaluation results."""
    return [
       {"backend":"grobid","status":"not_executed",
        "reason":"no dedicated local GROBID REST server; requires separate Java service and multi-GB RAM; 1 GB runner cannot validate page-located TEI citations",
        "source_quote_accuracy":None,"promotion_eligible":False},
       {"backend":"mineru","status":"not_executed",
        "reason":"OCR/layout/model infrastructure and hardware budget unavailable in isolated 1 GB CPU service; no private model deployment approved",
        "source_quote_accuracy":None,"promotion_eligible":False},
       {"backend":"marker","status":"not_executed",
        "reason":"isolated runner lacks Marker model runtime/weights; model-weight commercial licensing requires separate approval, and page-located source compatibility is untested",
        "source_quote_accuracy":None,"promotion_eligible":False}
    ]


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--child",type=Path)
    parser.add_argument("--engine",choices=("baseline",)+LOCAL_EXECUTABLE)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--ids",nargs="+",default=[f"B{i:02d}" for i in range(1,11)])
    args=parser.parse_args()
    if args.child:
        return child(args.child,args.engine,args.output)
    if args.ids!=[f"B{i:02d}" for i in range(1,11)]:
        parser.error("Use the full locked B01–B10 cohort; no selective success denominator")
    source=StorageSource()
    if not source.upload or source.bucket!="papers":
        raise RuntimeError("Only private exact-original source and private JSON artifacts allowed")
    source.run_id="ranked-oss-"+uuid4().hex
    specs=json.loads((ROOT/"benchmark/table_corpus.sha256.json").read_text(encoding="utf-8"))["papers"]
    if [x["id"] for x in specs]!=args.ids:
        raise RuntimeError("Source corpus identity/order mismatch")
    storage=[]
    failures=[]
    print(json.dumps({"event":"ranked_start","run_id":source.run_id,"order":ORDER,
                      "baseline":"deployed-v6.4.2-parser","provider_calls":0,
                      "production_writes":0,"source_papers":10}),flush=True)
    # Stage 1: exactly one baseline per original, then all pypdfium2 papers.
    # Stage 2: all pdfplumber papers; stage 3–5 fail-closed environment gates.
    with tempfile.TemporaryDirectory(prefix="papersignal-oss-trial-") as temp:
        for spec in specs:
            pdf,identity,owner=source.get_pdf(spec)
            old=historical_result(source,spec,owner)
            fp=Path(temp)/(spec["id"]+".pdf")
            fp.write_bytes(pdf)
            storage.append({"spec":spec,"file":fp,"owner":owner,
                            "identity":identity,"historical":old,"runs":[]})
        for mode in ("baseline",)+LOCAL_EXECUTABLE:
            successes=0
            for entry in storage:
                paper=entry["spec"]["id"]
                result=run_child(entry["file"],mode,Path(temp)/(paper+"-"+mode+".json"))
                compact={k:v for k,v in result.items() if k!="pages"}
                if compact["status"]=="ok" and compact.get("page_count")==entry["spec"]["pages"]:
                    compact["metrics"]=review_historical_against_pages(entry["historical"],result["pages"])
                    successes+=1
                elif compact["status"]=="ok":
                    compact["status"]="source_page_count_mismatch"
                compact["backend"]=mode
                entry["runs"].append(compact)
                if compact["status"]!="ok":
                    failures.append({"id":paper,"backend":mode,"error_type":compact.get("error_type",compact["status"])})
                print(json.dumps({"event":"ranked_result","paper":paper,**compact},ensure_ascii=False),flush=True)
            print(json.dumps({"event":"ranked_phase","backend":mode,
                              "completed":successes,"expected":len(storage)}),flush=True)
        for phase in blocked_later_candidates():
            print(json.dumps({"event":"ranked_phase",**phase}),flush=True)
        for entry in storage:
            payload={"id":entry["spec"]["id"],"sha256":entry["identity"]["sha256"],
                     "legacy_source_version":"finance-structured-v6.3.9",
                     "revalidator_version":engine.ANALYSIS_VERSION,
                     "runs":entry["runs"],"unexecuted_candidates":blocked_later_candidates(),
                     "human_accuracy":None,"provider_calls":0,"production_writes":0}
            if not source.save_artifact(entry["owner"],entry["spec"]["id"],payload):
                failures.append({"id":entry["spec"]["id"],"backend":"artifact","error_type":"save_disabled"})
    records=[]
    for mode in ("baseline",)+LOCAL_EXECUTABLE:
        runs=[next(r for r in x["runs"] if r["backend"]==mode) for x in storage]
        ok=[r for r in runs if r["status"]=="ok"]
        citations=sum(r["metrics"]["citations_revalidated_on_parsed_page_text"] for r in ok)
        total=sum(r["metrics"]["stored_citations"] for r in ok)
        records.append({"backend":mode,"completed":len(ok),"expected":len(storage),
                        "quote_retained":citations,"quotes_total_of_completed":total,
                        "source_evidence_findings":sum(r["metrics"]["findings_preserving_direct_source_evidence"] for r in ok),
                        "screen_passed_findings":sum(r["metrics"]["findings_screen_passed_by_current_validator"] for r in ok),
                        "sum_parser_wall_s":round(sum(r["wall_seconds"] for r in ok),4),
                        "max_child_rss_mib":max((r.get("child_max_rss_mib",0) for r in ok),default=None),
                        "promotion_eligible":False})
    print(json.dumps({"event":"ranked_summary","run_id":source.run_id,
                      "completed_papers":len(storage),"failures":failures,
                      "evaluated":records,
                      "not_executed":blocked_later_candidates(),
                      "human_gold":None,"new_model_analysis":False,
                      "promotion_eligible":False},ensure_ascii=False),flush=True)
    return int(bool(failures))


if __name__=="__main__":
    raise SystemExit(main())
