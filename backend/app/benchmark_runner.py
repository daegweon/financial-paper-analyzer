from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import platform
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import fitz
import httpx
from fastapi import FastAPI, Header, HTTPException

from app import main as engine

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "benchmark_manifest.json").read_text(encoding="utf-8"))
REGRESSION_LOCK = json.loads((ROOT / "benchmark_regression_lock.json").read_text(encoding="utf-8"))
HELDOUT_LOCK = json.loads((ROOT / "benchmark_heldout_lock.json").read_text(encoding="utf-8"))
RUN_TOKEN = os.getenv("BENCHMARK_RUN_TOKEN", "")
ARTIFACT_BUCKET = "papersignal-benchmark-artifacts"
RUN_KIND = "frozen_v6.4.2_full_pipeline_baseline"

app = FastAPI(title="PaperSignal isolated benchmark runner", version="1.0.0")
STATE: dict[str, Any] = {
    "status": "idle",
    "run_id": None,
    "started_at": None,
    "completed_at": None,
    "progress": [],
    "results": None,
    "error": None,
    "prepared": None,
}
PREPARED: dict[str, dict[str, Any]] = {}
RUN_TASK: asyncio.Task | None = None
STATE_LOCK = asyncio.Lock()

USAGE_RE = re.compile(
    r"Gemini usage model=(?P<model>\S+) finish=(?P<finish>\S+) "
    r"prompt_tokens=(?P<prompt>\d+|None) candidate_tokens=(?P<candidate>\d+|None) "
    r"thought_tokens=(?P<thought>\d+|None) total_tokens=(?P<total>\d+|None)"
)
CANDIDATE_USAGE_RE = re.compile(
    r"Gemini usage .*?provider_call_id=(?P<call>\S+) attempt=(?P<attempt>\d+)/(?P<max>\d+) "
    r".*?model=(?P<model>\S+) elapsed_ms=(?P<elapsed>[\d.]+) finish=(?P<finish>\S+) "
    r"prompt_tokens=(?P<prompt>\d+|None) candidate_tokens=(?P<candidate>\d+|None) "
    r"thought_tokens=(?P<thought>\d+|None) total_tokens=(?P<total>\d+|None)"
)
FAIL_RE = re.compile(r"Gemini attempt failed .*?model=(?P<model>\S+).*?(?:status=(?P<status>\d+)|outcome=(?P<outcome>\S+))")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_token(value: str | None) -> None:
    if not RUN_TOKEN or not value or not secrets.compare_digest(value, RUN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid benchmark token")


def service_headers() -> dict[str, str]:
    if not engine.SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing")
    return {
        **engine.supabase_headers(engine.SERVICE_ROLE_KEY),
        "Content-Type": "application/json",
    }


def read_rss_mb() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except Exception:
        return None
    return None


class RssSampler:
    def __init__(self, interval: float = 0.05) -> None:
        self.interval = interval
        self.stop_event = threading.Event()
        self.peak_mb = read_rss_mb() or 0.0
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self.stop_event.wait(self.interval):
            value = read_rss_mb()
            if value is not None:
                self.peak_mb = max(self.peak_mb, value)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> float:
        self.stop_event.set()
        self.thread.join(timeout=1.0)
        value = read_rss_mb()
        if value is not None:
            self.peak_mb = max(self.peak_mb, value)
        return round(self.peak_mb, 2)


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.messages.append(record.getMessage())
        except Exception:
            pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_pdf(paper_id: str, raw: bytes, expected_sha: str, expected_bytes: int, expected_pages: int) -> dict[str, Any]:
    if not raw.startswith(b"%PDF-"):
        raise RuntimeError(f"{paper_id}: source did not return a PDF")
    actual_sha = sha256(raw)
    if actual_sha != expected_sha:
        raise RuntimeError(f"{paper_id}: SHA-256 mismatch")
    if len(raw) != expected_bytes:
        raise RuntimeError(f"{paper_id}: byte-length mismatch")
    with fitz.open(stream=raw, filetype="pdf") as document:
        if document.needs_pass:
            raise RuntimeError(f"{paper_id}: encrypted PDF")
        actual_pages = len(document)
    if actual_pages != expected_pages:
        raise RuntimeError(f"{paper_id}: page-count mismatch ({actual_pages} != {expected_pages})")
    return {
        "id": paper_id,
        "sha256": actual_sha,
        "bytes": len(raw),
        "page_count": actual_pages,
        "pymupdf_runtime": fitz.VersionBind,
    }


def expected_sources() -> list[dict[str, Any]]:
    manifest_by_id = {p["id"]: p for p in MANIFEST["papers"]}
    items: list[dict[str, Any]] = []
    for locked in REGRESSION_LOCK["papers"]:
        meta = manifest_by_id[locked["id"]]
        items.append({
            "id": locked["id"],
            "filename": locked["filename"],
            "title": meta["title"],
            "doi": meta.get("doi"),
            "sha256": locked["sha256"],
            "bytes": locked["size_bytes"],
            "pages": locked["page_count"],
            "source_kind": "existing_private_supabase_storage",
            "gold_facts": meta.get("gold_facts", []),
            "critical_caveats": meta.get("critical_caveats", []),
        })
    for locked in HELDOUT_LOCK["heldout_papers"]:
        items.append({
            "id": locked["id"],
            "filename": locked["pdf_filename"],
            "title": locked["title"],
            "doi": locked["doi"],
            "sha256": locked["pdf_sha256"],
            "bytes": locked["pdf_byte_length"],
            "pages": locked["actual_page_count"],
            "publisher_pdf_url": locked["publisher_pdf_url"],
            "source_kind": "locked_publisher_pdf",
            "gold_facts": [],
            "critical_caveats": [],
        })
    return items


async def prepare_sources() -> dict[str, Any]:
    if not engine.SUPABASE_URL or not engine.SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase service configuration is missing")
    if engine.active_ai_provider() != "gemini":
        raise RuntimeError("Configured provider is not Gemini; refusing a mismatched baseline")
    items = expected_sources()
    regression_names = [p["filename"] for p in items if p["id"].startswith("B")]
    headers = service_headers()
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=15.0), follow_redirects=True) as client:
        response = await client.get(
            engine.SUPABASE_URL + "/rest/v1/papers",
            headers=headers,
            params={
                "original_filename": "in.(" + ",".join(regression_names) + ")",
                "select": "id,user_id,storage_path,original_filename,size_bytes,page_count,created_at",
                "order": "created_at.desc",
            },
        )
        response.raise_for_status()
        rows = response.json()
        by_name: dict[str, dict[str, Any]] = {}
        for row in rows:
            by_name.setdefault(row["original_filename"], row)
        for item in items:
            started = time.perf_counter()
            if item["id"].startswith("B"):
                row = by_name.get(item["filename"])
                if not row:
                    raise RuntimeError(f"{item['id']}: original uploaded paper row not found")
                path = row.get("storage_path")
                if not isinstance(path, str) or not path.startswith(row["user_id"] + "/") or ".." in path:
                    raise RuntimeError(f"{item['id']}: unsafe original storage path")
                pdf = await client.get(
                    engine.SUPABASE_URL + "/storage/v1/object/authenticated/papers/" + quote(path, safe="/"),
                    headers=headers,
                )
                if pdf.status_code != 200:
                    raise RuntimeError(f"{item['id']}: original private PDF download failed ({pdf.status_code})")
                raw = pdf.content
                item["source_paper_id"] = row["id"]
                item["source_user_id"] = row["user_id"]
                item["source_storage_path"] = path
            else:
                pdf = await client.get(
                    item["publisher_pdf_url"],
                    headers={
                        "User-Agent": "Mozilla/5.0 PaperSignal-Benchmark/1.0",
                        "Accept": "application/pdf,*/*;q=0.8",
                    },
                )
                if pdf.status_code != 200:
                    raise RuntimeError(f"{item['id']}: publisher PDF download failed ({pdf.status_code})")
                raw = pdf.content
            verification = verify_pdf(item["id"], raw, item["sha256"], item["bytes"], item["pages"])
            item["download_ms"] = round((time.perf_counter() - started) * 1000, 2)
            item["verification"] = verification
            PREPARED[item["id"]] = {**item, "raw": raw}
    return {
        "record_type": "PREFLIGHT_ONLY_NO_GEMINI_CALLS",
        "analysis_version": engine.ANALYSIS_VERSION,
        "provider": engine.active_ai_provider(),
        "model": engine.active_ai_model("gemini"),
        "fallback_model": engine.GEMINI_FALLBACK_MODEL,
        "runtime": {
            "python": platform.python_version(),
            "pymupdf": fitz.VersionBind,
            "pymupdf_pin": "1.26.3",
            "pymupdf_pin_match": fitz.VersionBind == "1.26.3",
        },
        "provider_calls": 0,
        "papers": [
            {k: v for k, v in item.items() if k not in {"gold_facts", "critical_caveats", "raw", "publisher_pdf_url"}}
            for item in PREPARED.values()
        ],
        "all_hashes_and_page_counts_verified": len(PREPARED) == 12,
    }


async def create_benchmark_user(client: httpx.AsyncClient, run_id: str, headers: dict[str, str]) -> str:
    email = f"papersignal-benchmark-{run_id}@example.invalid"
    password = secrets.token_urlsafe(36)
    response = await client.post(
        engine.SUPABASE_URL + "/auth/v1/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"papersignal_benchmark": True, "benchmark_run_id": run_id},
        },
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Benchmark user creation failed ({response.status_code})")
    payload = response.json()
    user = payload.get("user") if isinstance(payload.get("user"), dict) else payload
    user_id = user.get("id") if isinstance(user, dict) else None
    if not user_id:
        raise RuntimeError("Benchmark user creation returned no user id")
    return user_id


def parse_usage_logs(messages: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    usage: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for message in messages:
        match = CANDIDATE_USAGE_RE.search(message)
        if match:
            values = match.groupdict()
            usage.append({
                "model": values["model"],
                "provider_call_id": values["call"],
                "attempt": int(values["attempt"]),
                "max_attempts": int(values["max"]),
                "elapsed_ms": float(values["elapsed"]),
                "finish_reason": values["finish"],
                "prompt_tokens": int(values["prompt"]) if values["prompt"].isdigit() else None,
                "candidate_tokens": int(values["candidate"]) if values["candidate"].isdigit() else None,
                "thought_tokens": int(values["thought"]) if values["thought"].isdigit() else None,
                "total_tokens": int(values["total"]) if values["total"].isdigit() else None,
            })
            continue
        match = USAGE_RE.search(message)
        if match:
            values = match.groupdict()
            usage.append({
                "model": values["model"],
                "finish_reason": values["finish"],
                "prompt_tokens": int(values["prompt"]) if values["prompt"].isdigit() else None,
                "candidate_tokens": int(values["candidate"]) if values["candidate"].isdigit() else None,
                "thought_tokens": int(values["thought"]) if values["thought"].isdigit() else None,
                "total_tokens": int(values["total"]) if values["total"].isdigit() else None,
                "elapsed_ms": None,
            })
            continue
        if "Gemini attempt failed" in message:
            failed.append({"message": message[:500]})
    return usage, failed


def collect_evidence(value: Any, output: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if isinstance(value.get("page"), int) and isinstance(value.get("quote"), str):
            output.append({"page": value["page"], "quote": value["quote"]})
        for child in value.values():
            collect_evidence(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_evidence(child, output)


async def create_paper_and_job(
    client: httpx.AsyncClient,
    user_id: str,
    run_id: str,
    item: dict[str, Any],
) -> tuple[str, str, float, str, str]:
    raw = item["raw"]
    upload_started_at = utc_now()
    upload_started = time.perf_counter()
    storage_path = user_id + "/" + item["id"].lower() + "-" + uuid4().hex + ".pdf"
    upload = await client.post(
        engine.SUPABASE_URL + "/storage/v1/object/papers/" + quote(storage_path, safe="/"),
        headers={
            **service_headers(),
            "Content-Type": "application/pdf",
            "x-upsert": "false",
        },
        content=raw,
    )
    if upload.status_code not in (200, 201):
        raise RuntimeError(f"{item['id']}: benchmark PDF upload failed ({upload.status_code})")
    upload_ms = (time.perf_counter() - upload_started) * 1000
    paper_payload = {
        "user_id": user_id,
        "title": item["title"],
        "original_filename": item["filename"],
        "storage_path": storage_path,
        "content_type": "application/pdf",
        "size_bytes": len(raw),
        "page_count": item["pages"],
        "status": "uploaded",
        "metadata": {
            "papersignal_benchmark": True,
            "benchmark_run_id": run_id,
            "benchmark_dataset_id": item["id"],
            "analysis_version": engine.ANALYSIS_VERSION,
            "source_sha256": item["sha256"],
        },
    }
    paper_response = await client.post(
        engine.SUPABASE_URL + "/rest/v1/papers",
        headers={**service_headers(), "Prefer": "return=representation"},
        json=paper_payload,
    )
    if paper_response.status_code not in (200, 201):
        raise RuntimeError(f"{item['id']}: benchmark paper row insert failed ({paper_response.status_code})")
    paper_rows = paper_response.json()
    if not isinstance(paper_rows, list) or not paper_rows:
        raise RuntimeError(f"{item['id']}: benchmark paper insert returned no row")
    paper_id = paper_rows[0]["id"]
    job_payload = {
        "paper_id": paper_id,
        "user_id": user_id,
        # Processing rows are deliberately not claimable by the production
        # Worker, whose claim RPC only selects queued jobs.
        "status": "processing",
        "stage": "benchmark_reserved",
        "attempts": 0,
        "max_attempts": 1,
        "worker_id": "papersignal-isolated-baseline-runner",
    }
    job_response = await client.post(
        engine.SUPABASE_URL + "/rest/v1/analysis_jobs",
        headers={**service_headers(), "Prefer": "return=representation"},
        json=job_payload,
    )
    if job_response.status_code not in (200, 201):
        raise RuntimeError(f"{item['id']}: benchmark job insert failed ({job_response.status_code})")
    job_rows = job_response.json()
    if not isinstance(job_rows, list) or not job_rows:
        raise RuntimeError(f"{item['id']}: benchmark job insert returned no row")
    job_id = job_rows[0]["id"]
    job_created_at = job_rows[0].get("created_at") or utc_now()
    return paper_id, job_id, upload_ms, upload_started_at, job_created_at


async def fetch_job_and_analysis(
    client: httpx.AsyncClient,
    job_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    headers = service_headers()
    job_response = await client.get(
        engine.SUPABASE_URL + "/rest/v1/analysis_jobs",
        headers=headers,
        params={"id": "eq." + job_id, "select": "*", "limit": "1"},
    )
    job_response.raise_for_status()
    jobs = job_response.json()
    analysis_response = await client.get(
        engine.SUPABASE_URL + "/rest/v1/analyses",
        headers=headers,
        params={"job_id": "eq." + job_id, "select": "*", "limit": "1"},
    )
    analysis_response.raise_for_status()
    analyses = analysis_response.json()
    return (jobs[0] if jobs else None, analyses[0] if analyses else None)


def result_quality_metrics(result: dict[str, Any] | None, page_count: int) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "mode": None,
            "summary_chars": 0,
            "findings_count": 0,
            "evidence_count": 0,
            "evidence_valid_page_count": 0,
            "evidence_invalid_page_count": 0,
            "methodology_present": False,
        }
    evidence: list[dict[str, Any]] = []
    collect_evidence(result, evidence)
    valid = [e for e in evidence if 1 <= e["page"] <= page_count and e["quote"].strip()]
    invalid = [e for e in evidence if not (1 <= e["page"] <= page_count) or not e["quote"].strip()]
    methodology = result.get("methodology")
    return {
        "mode": result.get("mode"),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "summary_chars": len(result.get("summary") or ""),
        "findings_count": len(result.get("findings") or []) if isinstance(result.get("findings"), list) else 0,
        "evidence_count": len(evidence),
        "evidence_valid_page_count": len(valid),
        "evidence_invalid_page_count": len(invalid),
        "methodology_present": isinstance(methodology, dict) and any(bool(v) for v in methodology.values()),
        "gold_fact_count": None,
    }


async def run_one(
    client: httpx.AsyncClient,
    user_id: str,
    run_id: str,
    item: dict[str, Any],
) -> dict[str, Any]:
    upload_started = time.perf_counter()
    paper_id, job_id, upload_ms, upload_started_at, job_created_at = await create_paper_and_job(
        client, user_id, run_id, item
    )
    metrics: dict[str, Any] = {
        "extract_ms": 0.0,
        "llm_result_ms": 0.0,
        "prompt_chars": 0,
        "extracted_chars": 0,
        "pages_scanned": 0,
    }
    original_extract = engine.extract_pages
    original_prompt = engine.build_analysis_prompt
    original_llm = engine.llm_result

    def timed_extract(raw: bytes):
        started = time.perf_counter()
        try:
            page_count, pages = original_extract(raw)
            metrics["pages_scanned"] += len(pages)
            metrics["extracted_chars"] += sum(len(p.get("text") or "") for p in pages)
            return page_count, pages
        finally:
            metrics["extract_ms"] += (time.perf_counter() - started) * 1000

    def timed_prompt(pages: list[dict[str, Any]]):
        prompt = original_prompt(pages)
        metrics["prompt_chars"] = len(prompt)
        return prompt

    async def timed_llm(*args, **kwargs):
        started = time.perf_counter()
        try:
            return await original_llm(*args, **kwargs)
        finally:
            metrics["llm_result_ms"] += (time.perf_counter() - started) * 1000

    handler = CaptureHandler()
    old_level = engine.log.level
    engine.log.setLevel(logging.INFO)
    engine.log.addHandler(handler)
    sampler = RssSampler()
    sampler.start()
    process_started_at = utc_now()
    process_started = time.perf_counter()
    engine.extract_pages = timed_extract
    engine.build_analysis_prompt = timed_prompt
    engine.llm_result = timed_llm
    try:
        await engine._process_analysis_job(paper_id, job_id, user_id, engine.SERVICE_ROLE_KEY)
    finally:
        engine.extract_pages = original_extract
        engine.build_analysis_prompt = original_prompt
        engine.llm_result = original_llm
        engine.log.removeHandler(handler)
        engine.log.setLevel(old_level)
    process_ms = (time.perf_counter() - process_started) * 1000
    sampled_peak_rss_mb = sampler.stop()
    job, analysis = await fetch_job_and_analysis(client, job_id)
    result = analysis.get("result") if isinstance(analysis, dict) else None
    usage, failed_attempts = parse_usage_logs(handler.messages)
    prompt_tokens = sum(x.get("prompt_tokens") or 0 for x in usage)
    candidate_tokens = sum(x.get("candidate_tokens") or 0 for x in usage)
    thought_tokens = sum(x.get("thought_tokens") or 0 for x in usage)
    total_tokens = sum(x.get("total_tokens") or 0 for x in usage)
    completed = bool(job and job.get("status") == "completed" and analysis)
    return {
        "id": item["id"],
        "title": item["title"],
        "doi": item.get("doi"),
        "source_sha256": item["sha256"],
        "source_bytes": len(item["raw"]),
        "page_count": item["pages"],
        "source_kind": item["source_kind"],
        "paper_id": paper_id,
        "job_id": job_id,
        "analysis_id": analysis.get("id") if analysis else None,
        "job_status": job.get("status") if job else None,
        "job_stage": job.get("stage") if job else None,
        "job_error": job.get("error_message") if job else None,
        "analysis_created_at": analysis.get("created_at") if analysis else None,
        "job_created_at": job.get("created_at") if job else job_created_at,
        "job_started_at": job.get("started_at") if job else process_started_at,
        "job_completed_at": job.get("completed_at") if job else None,
        "upload_started_at": upload_started_at,
        "process_started_at": process_started_at,
        "upload_storage_ms": round(upload_ms, 2),
        "job_execution_ms": round(process_ms, 2),
        "upload_to_saved_ms": round((time.perf_counter() - upload_started) * 1000, 2) if completed else None,
        "extract_ms": round(metrics["extract_ms"], 2),
        "llm_result_ms": round(metrics["llm_result_ms"], 2),
        "pages_scanned": metrics["pages_scanned"],
        "extracted_chars": metrics["extracted_chars"],
        "prompt_chars": metrics["prompt_chars"],
        "provider": result.get("provider") if isinstance(result, dict) else engine.active_ai_provider(),
        "model": analysis.get("model") if analysis else None,
        "analysis_version": engine.ANALYSIS_VERSION,
        "provider_usage_calls": usage,
        "provider_failed_attempts": failed_attempts,
        "provider_usage_call_count": len(usage),
        "provider_failed_attempt_count": len(failed_attempts),
        "prompt_tokens": prompt_tokens,
        "candidate_tokens": candidate_tokens,
        "thought_tokens": thought_tokens,
        "total_tokens": total_tokens,
        "provider_cost_usd": None,
        "provider_cost_status": "NOT_EXPOSED_BY_GEMINI_RESPONSE_METADATA",
        "sampled_peak_rss_mb": sampled_peak_rss_mb,
        "result_quality": result_quality_metrics(result, item["pages"]),
        "result": result,
        "completed": completed,
    }


async def upload_result_artifact(client: httpx.AsyncClient, run_id: str, payload: dict[str, Any]) -> str | None:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path = run_id + "/baseline_full_pipeline.json"
    response = await client.post(
        engine.SUPABASE_URL + "/storage/v1/object/" + ARTIFACT_BUCKET + "/" + quote(path, safe="/"),
        headers={
            **engine.supabase_headers(engine.SERVICE_ROLE_KEY),
            "Content-Type": "application/json",
            "x-upsert": "true",
        },
        content=raw,
    )
    if response.status_code not in (200, 201):
        logging.getLogger("papersignal.benchmark").warning(
            "Artifact upload failed status=%s body_length=%s",
            response.status_code, len(response.content),
        )
        return None
    return path


async def run_full_benchmark(run_id: str) -> None:
    started_at = utc_now()
    records: list[dict[str, Any]] = []
    user_id = None
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=15.0), follow_redirects=True) as client:
            headers = service_headers()
            user_id = await create_benchmark_user(client, run_id, headers)
            async with STATE_LOCK:
                STATE["progress"] = []
            for index, item in enumerate(PREPARED.values(), start=1):
                async with STATE_LOCK:
                    STATE["progress"].append({
                        "id": item["id"],
                        "status": "running",
                        "index": index,
                        "total": len(PREPARED),
                        "started_at": utc_now(),
                    })
                try:
                    record = await run_one(client, user_id, run_id, item)
                except Exception as exc:
                    record = {
                        "id": item["id"],
                        "title": item["title"],
                        "source_sha256": item["sha256"],
                        "analysis_version": engine.ANALYSIS_VERSION,
                        "completed": False,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }
                records.append(record)
                async with STATE_LOCK:
                    STATE["progress"][-1].update({
                        "status": "completed" if record.get("completed") else "failed",
                        "finished_at": utc_now(),
                        "upload_to_saved_ms": record.get("upload_to_saved_ms"),
                        "total_tokens": record.get("total_tokens"),
                    })
                await asyncio.sleep(1.0)

            completed = sum(1 for r in records if r.get("completed"))
            failed = len(records) - completed
            latencies = sorted(r["upload_to_saved_ms"] for r in records if r.get("upload_to_saved_ms") is not None)
            tokens = sum(int(r.get("total_tokens") or 0) for r in records)
            prompt_tokens = sum(int(r.get("prompt_tokens") or 0) for r in records)
            candidate_tokens = sum(int(r.get("candidate_tokens") or 0) for r in records)
            call_count = sum(int(r.get("provider_usage_call_count") or 0) for r in records)
            rss_peak = max((float(r.get("sampled_peak_rss_mb") or 0) for r in records), default=0.0)
            payload = {
                "schema_version": 1,
                "record_type": "PAPERSIGNAL_FULL_PIPELINE_BASELINE",
                "run_id": run_id,
                "run_kind": RUN_KIND,
                "created_at": started_at,
                "completed_at": utc_now(),
                "analysis_version": engine.ANALYSIS_VERSION,
                "provider": engine.active_ai_provider(),
                "model": engine.active_ai_model("gemini"),
                "fallback_model": engine.GEMINI_FALLBACK_MODEL,
                "runtime": {
                    "python": platform.python_version(),
                    "pymupdf": fitz.VersionBind,
                    "pymupdf_pin": "1.26.3",
                    "pymupdf_pin_match": fitz.VersionBind == "1.26.3",
                },
                "isolation": {
                    "dedicated_qa_user_id": user_id,
                    "jobs_created_as_processing_to_prevent_production_worker_claim": True,
                    "production_worker_modified": False,
                    "production_api_modified": False,
                    "production_deployed": False,
                },
                "summary": {
                    "papers_total": len(records),
                    "papers_completed": completed,
                    "papers_failed": failed,
                    "completion_rate": round(completed / len(records), 4) if records else 0,
                    "upload_to_saved_p50_ms": latencies[len(latencies) // 2] if latencies else None,
                    "upload_to_saved_p95_ms": latencies[min(len(latencies) - 1, int((len(latencies) - 1) * 0.95))] if latencies else None,
                    "provider_usage_call_count": call_count,
                    "prompt_tokens": prompt_tokens,
                    "candidate_tokens": candidate_tokens,
                    "total_tokens": tokens,
                    "provider_cost_usd": None,
                    "provider_cost_status": "NOT_EXPOSED_BY_GEMINI_RESPONSE_METADATA",
                    "sampled_peak_rss_mb": round(rss_peak, 2),
                },
                "records": records,
                "warnings": [
                    "Gemini usageMetadata provides token counts but not invoice-level billed cost; provider_cost_usd is intentionally null.",
                    "RSS is sampled from the runner process during each paper and is not an isolated per-job cgroup peak.",
                    "This is the frozen production v6.4.2 baseline. Candidate telemetry A/B must be run separately under the same runtime and corpus.",
                ],
            }
            artifact_path = await upload_result_artifact(client, run_id, payload)
            payload["artifact_bucket"] = ARTIFACT_BUCKET if artifact_path else None
            payload["artifact_path"] = artifact_path
            async with STATE_LOCK:
                STATE["status"] = "completed" if failed == 0 else "completed_with_failures"
                STATE["completed_at"] = utc_now()
                STATE["results"] = payload
    except Exception as exc:
        async with STATE_LOCK:
            STATE["status"] = "failed"
            STATE["completed_at"] = utc_now()
            STATE["error"] = {"type": type(exc).__name__, "message": str(exc)[:800]}
        logging.getLogger("papersignal.benchmark").exception("Baseline run failed run_id=%s", run_id)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "papersignal-v642-baseline-runner",
        "analysis_version": engine.ANALYSIS_VERSION,
        "provider": engine.active_ai_provider(),
        "model": engine.active_ai_model("gemini") if engine.active_ai_provider() == "gemini" else None,
        "pymupdf_runtime": fitz.VersionBind,
        "pymupdf_pin_match": fitz.VersionBind == "1.26.3",
    }


@app.post("/benchmark/prepare")
async def prepare(token: str | None = Header(default=None, alias="X-Benchmark-Token")) -> dict[str, Any]:
    require_token(token)
    if STATE["status"] == "running":
        raise HTTPException(status_code=409, detail="A benchmark run is already active")
    try:
        PREPARED.clear()
        report = await prepare_sources()
        STATE["prepared"] = report
        STATE["status"] = "prepared"
        return report
    except Exception as exc:
        STATE["status"] = "prepare_failed"
        STATE["error"] = {"type": type(exc).__name__, "message": str(exc)[:800]}
        raise HTTPException(status_code=502, detail=f"Benchmark preflight failed: {type(exc).__name__}") from exc


@app.post("/benchmark/run")
async def run(token: str | None = Header(default=None, alias="X-Benchmark-Token")) -> dict[str, Any]:
    require_token(token)
    global RUN_TASK
    if len(PREPARED) != 12 or STATE["status"] != "prepared":
        raise HTTPException(status_code=409, detail="All 12 exact locked PDFs must pass preflight first")
    if RUN_TASK and not RUN_TASK.done():
        raise HTTPException(status_code=409, detail="A benchmark run is already active")
    run_id = uuid4().hex
    async with STATE_LOCK:
        STATE.update({
            "status": "running",
            "run_id": run_id,
            "started_at": utc_now(),
            "completed_at": None,
            "progress": [],
            "results": None,
            "error": None,
        })
    RUN_TASK = asyncio.create_task(run_full_benchmark(run_id))
    return {"status": "running", "run_id": run_id, "analysis_version": engine.ANALYSIS_VERSION}


@app.get("/benchmark/status/{run_id}")
async def status(run_id: str, token: str | None = Header(default=None, alias="X-Benchmark-Token")) -> dict[str, Any]:
    require_token(token)
    if STATE.get("run_id") != run_id:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return {
        "status": STATE["status"],
        "run_id": STATE["run_id"],
        "started_at": STATE["started_at"],
        "completed_at": STATE["completed_at"],
        "progress": STATE["progress"],
        "error": STATE["error"],
        "summary": STATE["results"].get("summary") if isinstance(STATE.get("results"), dict) else None,
    }


@app.get("/benchmark/results/{run_id}")
async def results(run_id: str, token: str | None = Header(default=None, alias="X-Benchmark-Token")) -> dict[str, Any]:
    require_token(token)
    if STATE.get("run_id") != run_id:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    if not isinstance(STATE.get("results"), dict):
        raise HTTPException(status_code=409, detail="Benchmark results are not ready")
    return STATE["results"]
