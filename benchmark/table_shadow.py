"""Read-only PDF shadow benchmark; optional NEW private JSON artifacts, never analyses/jobs.

Local: python -m benchmark.table_shadow --input-dir /private/pdfs --output /private/run
Storage: explicit --supabase, server-side env credentials, exact corpus allowlist.
No model invocation, production import, queue claim, public listener or promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINES = ("pymupdf-text", "camelot-lattice", "camelot-stream")
MAX_PDF_BYTES = 30 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected redirect in authenticated Storage request")


def check_bytes(data: bytes, spec: dict[str, Any], etag: str | None = None) -> dict[str, Any]:
    if not data.startswith(b"%PDF-") or len(data) != spec["bytes"]:
        raise ValueError("PDF format or byte-length mismatch")
    if etag is not None and etag.strip('"') != spec["etag"]:
        raise ValueError("Storage ETag mismatch")
    sha = hashlib.sha256(data).hexdigest()
    if spec.get("sha256") and sha != spec["sha256"]:
        raise ValueError("SHA-256 mismatch")
    return {"bytes": len(data), "sha256": sha,
            "storage_etag_checked": etag is not None,
            "source_identity": "storage_download" if etag is not None else
                               "sha256_locked_local" if spec.get("sha256") else "unverified_local"}


def package_versions() -> dict[str, str]:
    result = {}
    for name in ("camelot-py", "PyMuPDF", "pdfminer.six", "opencv-python-headless", "numpy", "pandas", "pypdfium2"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "unavailable"
    return result


def child(pdf: Path, engine: str, output: Path, expected_pages: int) -> None:
    started = time.perf_counter()
    import fitz
    with fitz.open(pdf) as doc:
        if len(doc) != expected_pages:
            raise ValueError("Page-count mismatch")
        page_count = len(doc)
        if engine == "pymupdf-text":
            # Text control, NOT a rerun of the full production analysis engine.
            pages = [{"page": n + 1, "text": page.get_text("text", sort=True)} for n, page in enumerate(doc)]
            result = {"status": "ok", "pages": pages, "tables": [], "diagnostics": []}
        else:
            sys.path.insert(0, str(ROOT / "backend"))
            from app.pdf_table_experiment import extract_tables_camelot
            diagnostics: list[dict[str, Any]] = []
            tables = extract_tables_camelot(pdf.read_bytes(), pages=list(range(1, page_count + 1)),
                                           flavors=(engine.removeprefix("camelot-"),),
                                           deduplicate=False, diagnostics=diagnostics)
            failed = any(x["status"] != "ok" for x in diagnostics)
            result = {"status": "error" if failed else "ok", "tables": tables, "diagnostics": diagnostics}
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result.update(engine=engine, page_count=page_count,
                  extraction_seconds=round(time.perf_counter() - started, 6),
                  peak_rss_mib=round(rss / (1024**2 if sys.platform == "darwin" else 1024), 3),
                  versions=package_versions())
    output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def run_isolated(pdf: Path, engine: str, output: Path, pages: int, timeout: float) -> dict[str, Any]:
    if engine not in ENGINES or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Invalid engine or timeout")
    started = time.perf_counter()
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MPLBACKEND="Agg")
    # Never pass Storage credentials into parser subprocesses.
    for name in tuple(env):
        if name.startswith(("SUPABASE_", "GEMINI_", "OPENAI_", "ANTHROPIC_")):
            env.pop(name)
    with tempfile.TemporaryFile() as err:
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", str(pdf),
                                   "--engine", engine, "--child-output", str(output), "--pages", str(pages)],
                                  stdout=subprocess.DEVNULL, stderr=err, env=env,
                                  timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {"engine": engine, "status": "timeout", "wall_seconds": round(time.perf_counter()-started, 6)}
    if proc.returncode != 0 or not output.exists():
        return {"engine": engine, "status": "process_error", "exit_code": proc.returncode,
                "wall_seconds": round(time.perf_counter()-started, 6)}
    data = json.loads(output.read_text(encoding="utf-8"))
    data["wall_seconds"] = round(time.perf_counter()-started, 6)
    output.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    return data


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    low, high = math.floor(index), math.ceil(index)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (index-low), 6)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for engine in ENGINES:
        rows = [r for r in records if r["engine"] == engine]
        successful = [r for r in rows if r["status"] == "ok"]
        times = [r["wall_seconds"] for r in successful]
        summary[engine] = {
            "attempted": len(rows), "completed": len(successful),
            "failures": len(rows)-len(successful),
            "p50_wall_seconds_successes_only": percentile(times, .5),
            "p95_wall_seconds_successes_only": percentile(times, .95),
            "max_peak_rss_mib": max((r.get("peak_rss_mib", 0) for r in successful), default=None),
            "candidate_tables": sum(r.get("table_count", 0) for r in successful),
        }
    return {"engines": summary, "promotion_eligible": False,
            "blocking_gates": ["human_reviewed_exact_cell_gold_missing",
                               "full_analysis_quality_regression_not_run",
                               "production_resource_and_cost_budget_not_validated",
                               "second_independent_full_benchmark_not_run"],
            "scope": "Extraction smoke/performance only; table counts and parser accuracy are NOT recall/precision. p95 is descriptive, not an SLA."}


class StorageSource:
    """Narrow allowlisted reads and optional new private artifacts; no database writes."""
    def __init__(self) -> None:
        self.base = os.environ["SUPABASE_URL"].rstrip("/")
        if self.base != "https://hwmtayrecsfxernhssro.supabase.co":
            raise ValueError("Unexpected Supabase project")
        self.key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.bucket = os.environ["BENCHMARK_STORAGE_BUCKET"]
        self.upload = os.getenv("BENCHMARK_UPLOAD_RESULTS") == "1"
        self.artifact_bucket = "papersignal-benchmark-artifacts"
        self.artifact_ready = False
        self.run_id = "tables-" + uuid.uuid4().hex

    def request(self, path: str, data: bytes | None = None) -> tuple[bytes, Any]:
        headers = {"apikey": self.key, "Authorization": "Bearer " + self.key}
        if data is not None:
            headers.update({"Content-Type": "application/json", "x-upsert": "false"})
        request = urllib.request.Request(self.base + path, data=data, headers=headers)
        with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
            content = response.read(MAX_PDF_BYTES + 1)
            if len(content) > MAX_PDF_BYTES:
                raise ValueError("Response exceeds resource limit")
            return content, response.headers

    def ensure_artifact_bucket(self) -> None:
        """Only this dedicated private JSON bucket can be created. Never alter papers."""
        # List before creating: missing-bucket GET status differs by Storage version.
        # Never treat every HTTP 400 as permission to create a bucket.
        body, _ = self.request("/storage/v1/bucket")
        buckets = json.loads(body)
        if not isinstance(buckets, list):
            raise ValueError("Unexpected bucket list response")
        matches = [b for b in buckets if b.get("id") == self.artifact_bucket]
        if len(matches) > 1:
            raise ValueError("Ambiguous artifact bucket")
        if matches:
            bucket = matches[0]
        else:
            self.request("/storage/v1/bucket", json.dumps({
                "id": self.artifact_bucket, "name": self.artifact_bucket, "public": False,
                "allowed_mime_types": ["application/json"], "file_size_limit": MAX_PDF_BYTES,
            }).encode())
            body, _ = self.request("/storage/v1/bucket/" + self.artifact_bucket)
            bucket = json.loads(body)
        if bucket.get("id") != self.artifact_bucket or bucket.get("public") is not False:
            raise ValueError("Benchmark artifact bucket must match and be private")

    def get_pdf(self, spec: dict[str, Any]) -> tuple[bytes, dict[str, Any], str]:
        query = urllib.parse.urlencode({"select": "storage_path,user_id,size_bytes,page_count", "original_filename": "eq." + spec["filename"], "limit": "2"})
        body, _ = self.request("/rest/v1/papers?" + query)
        rows = json.loads(body)
        if len(rows) != 1:
            raise ValueError("Missing or ambiguous corpus filename")
        row = rows[0]
        owner = row["user_id"]
        uuid.UUID(owner)
        if not row["storage_path"].startswith(owner + "/") or row["size_bytes"] != spec["bytes"]:
            raise ValueError("Storage ownership or size mismatch")
        path = "/storage/v1/object/" + urllib.parse.quote(self.bucket, safe="") + "/" + urllib.parse.quote(row["storage_path"], safe="/")
        body, headers = self.request(path)
        etag = headers.get("ETag")
        if not etag:
            raise ValueError("Missing Storage ETag")
        return body, check_bytes(body, spec, etag), owner

    def save_artifact(self, owner: str, paper_id: str, payload: dict[str, Any]) -> bool:
        if not self.upload:
            return False
        if not getattr(self, "artifact_ready", False):
            self.ensure_artifact_bucket()
            self.artifact_ready = True
        if not re.fullmatch(r"B\d{2}", paper_id):
            raise ValueError("Invalid benchmark ID")
        uuid.UUID(owner)
        path = "/storage/v1/object/" + urllib.parse.quote(self.artifact_bucket, safe="") + "/" + owner + "/benchmarks/" + self.run_id + "/" + paper_id + ".json"
        self.request(path, json.dumps(payload, ensure_ascii=False, allow_nan=False).encode())
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--engine", choices=ENGINES)
    parser.add_argument("--child-output", type=Path)
    parser.add_argument("--pages", type=int)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--supabase", action="store_true")
    parser.add_argument("--corpus", type=Path, default=ROOT/"benchmark/table_corpus.json")
    parser.add_argument("--output", type=Path, default=Path("/tmp/papersignal-table-benchmark"))
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--ids", nargs="+")
    args = parser.parse_args()
    if args.child:
        child(args.child, args.engine, args.child_output, args.pages)
        return 0
    if bool(args.input_dir) == bool(args.supabase):
        parser.error("Choose exactly one source: --input-dir or --supabase")
    specs = json.loads(args.corpus.read_text(encoding="utf-8"))["papers"]
    if args.ids:
        if set(args.ids) - {s["id"] for s in specs}:
            parser.error("Unknown benchmark ID")
        specs = [s for s in specs if s["id"] in args.ids]
    args.output.mkdir(parents=True, exist_ok=True)
    source = StorageSource() if args.supabase else None
    records, errors = [], []
    run_id = source.run_id if source else "local-" + uuid.uuid4().hex
    print(json.dumps({"event":"run_start", "run_id":run_id, "papers":[s["id"] for s in specs], "versions":package_versions()}), flush=True)
    for spec in specs:
        try:
            if source:
                pdf, identity, owner = source.get_pdf(spec)
            else:
                pdf = (args.input_dir/spec["filename"]).read_bytes()
                identity, owner = check_bytes(pdf, spec), ""
            artifacts = {"id": spec["id"], "identity": identity, "runs": []}
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)/"input.pdf"
                path.write_bytes(pdf)
                for engine in ENGINES:
                    output = args.output/(spec["id"]+"-"+engine+".json")
                    result = run_isolated(path, engine, output, spec["pages"], args.timeout)
                    artifacts["runs"].append(result)
                    compact = {k:v for k,v in result.items() if k not in ("tables", "pages", "diagnostics")}
                    compact.update(id=spec["id"], identity=identity, table_count=len(result.get("tables", [])),
                                   pages_with_tables=sorted({x["page"] for x in result.get("tables", [])}),
                                   diagnostic_statuses=sorted({x["status"] for x in result.get("diagnostics", [])}))
                    records.append(compact)
                    print(json.dumps({"event":"result", **compact}, allow_nan=False), flush=True)
            if source:
                saved = source.save_artifact(owner, spec["id"], artifacts)
                print(json.dumps({"event":"artifact", "id":spec["id"], "saved_private":saved, "run_id":run_id}), flush=True)
        except Exception as exc:
            # Exception strings may include signed URLs/paths/identities: do not log them.
            item = {"id":spec["id"], "error_type":type(exc).__name__}
            if hasattr(exc, "code"):
                item["http_status"] = exc.code
            errors.append(item)
            print(json.dumps({"event":"source_or_artifact_error", **item}), flush=True)
    report = {"run_id":run_id, "records":records, "source_errors":errors, **summarize(records)}
    (args.output/"summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({"event":"summary", **report}, ensure_ascii=False, allow_nan=False), flush=True)
    return 1 if errors or any(r["status"] != "ok" for r in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
