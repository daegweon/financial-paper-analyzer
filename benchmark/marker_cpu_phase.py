"""Isolated Marker CPU no_ocr feasibility on locked original B01, no model API.

Never logs raw PDF/JSON. This test deliberately does NOT claim compatibility
unless JSON page structure and exact stored citations can be revalidated.
Marker's model weights have distinct commercial terms; no production use.
"""
from __future__ import annotations
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from benchmark.table_shadow import StorageSource
from benchmark.full_analysis_replay import historical_result, review_historical_against_pages
from app import main as engine

class Plain(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text=[]
    def handle_data(self, value):
        if value.strip():
            self.text.append(value)

def page_text(block):
    if not isinstance(block,dict):
        return ""
    out=[]
    content=block.get("html") or block.get("text")
    if isinstance(content,str):
        parser=Plain()
        parser.feed(content)
        if parser.text:
            out.extend(parser.text)
    for child in block.get("children") or []:
        out.append(page_text(child))
    return " ".join(" ".join(x for x in out if x).split())

def main():
    src=StorageSource()
    if not src.upload or src.bucket!="papers":
        raise RuntimeError("Private exact original required")
    src.run_id="marker-feasibility-"+uuid4().hex
    corpus=json.loads((Path(__file__).resolve().parents[1]/"benchmark/table_corpus.sha256.json").read_text())
    spec=next(x for x in corpus["papers"] if x["id"]=="B01")
    source,identity,owner=src.get_pdf(spec)
    historical=historical_result(src,spec,owner)
    report={"backend":"marker-pdf 2.0.0 / no_ocr",
            "original_id":"B01","source_sha256":identity["sha256"],
            "mode":"cpu_fast_disable_ocr","commercial_weight_license_cleared":False,
            "production_eligible":False,"human_gold_accuracy":None}
    try:
        with tempfile.TemporaryDirectory(prefix="papersignal-marker-") as d:
            pdf=Path(d)/"source.pdf"
            pdf.write_bytes(source)
            dest=Path(d)/"results"
            dest.mkdir()
            env=dict(os.environ)
            for k in tuple(env):
                if k.startswith(("SUPABASE_","BENCHMARK_","GEMINI_","OPENAI_","ANTHROPIC_","FULL_AB_")):
                    env.pop(k)
            env.update(TOKENIZERS_PARALLELISM="false",CUDA_VISIBLE_DEVICES="",
                       OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",
                       HOME="/tmp", XDG_CACHE_HOME="/tmp/.cache",
                       HF_HOME="/tmp/.cache/huggingface",TORCH_HOME="/tmp/.cache/torch")
            command=[
                "marker_single",str(pdf),"--mode","fast",
                "--disable_ocr","--disable_image_extraction",
                "--output_format","json","--output_dir",str(dest)
            ]
            started=time.perf_counter()
            try:
                proc=subprocess.run(command,env=env,stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                    timeout=160,check=False)
                report["subprocess_exit_code"]=proc.returncode
                if proc.returncode:
                    report["status"]="cli_failed"
                    # Never persist raw stderr: it may contain private file paths.
                    error=(proc.stderr or b"").decode("utf-8",errors="ignore").lower()
                    tags={
                        "permission_denied":("permissionerror","permission denied","read-only file system"),
                        "missing_dependency":("modulenotfounderror","importerror","no module named"),
                        "download_or_model":("hfhubhttperror","failed to download","couldn't connect","model not found"),
                        "out_of_memory":("outofmemory","out of memory","cannot allocate memory"),
                        "invalid_cli_option":("no such option","invalid value for","badparameter"),
                        "runtime_error":("runtimeerror","assertionerror","valueerror","exception")
                    }
                    report["failure_categories"]=[
                        key for key,phrases in tags.items() if any(p in error for p in phrases)
                    ][:4] or ["unknown_cli_failure"]
                else:
                    outputs=list(dest.rglob("*.json"))
                    if len(outputs)!=1:
                        report["status"]="unexpected_json_artifacts"
                        report["json_count"]=len(outputs)
                    else:
                        obj=json.loads(outputs[0].read_text(encoding="utf-8"))
                        if not isinstance(obj,list) or len(obj)!=spec["pages"]:
                            report["status"]="page_mapping_unavailable"
                            report["json_is_list"]=isinstance(obj,list)
                            report["json_pages"]=len(obj) if isinstance(obj,list) else None
                        else:
                            pages=[]
                            for index,item in enumerate(obj,1):
                                value=page_text(item)
                                value=" ".join(value.split())[:engine.MAX_PAGE_CHARS]
                                if value:
                                    pages.append({"page":index,"text":value})
                            if not pages:
                                report["status"]="empty_page_text"
                            else:
                                report["status"]="ok"
                                report["metrics"]=review_historical_against_pages(historical,pages)
            except subprocess.TimeoutExpired:
                report["status"]="timeout"
            report["wall_seconds"]=round(time.perf_counter()-started,4)
            report["max_parent_rss_mib"]=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,3)
    except Exception as exc:
        report["status"]="failed"
        report["exception_type"]=type(exc).__name__
    src.save_artifact(owner,"B01",report)
    print(json.dumps({"event":"marker_phase_result",**report,
                      "private_saved":True},ensure_ascii=False),flush=True)
    return 0 if report.get("status")=="ok" else 2

if __name__=="__main__":
    raise SystemExit(main())
