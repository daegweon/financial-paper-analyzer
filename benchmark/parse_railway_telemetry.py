"""Aggregate job-correlated Railway Worker/Gemini logs into safe benchmark records.

The input is a JSON array of {timestamp, message} objects exported from Railway.
No request bodies, prompts, PDF text, credentials or raw log messages are copied
to output. Provider cost remains null until a dated pricing schedule is supplied.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

JOB_RE = re.compile(r"\bjob_id=([0-9a-fA-F-]{8,})")
CALL_RE = re.compile(r"\bprovider_call_id=([0-9a-fA-F]{8,})")
ATTEMPT_RE = re.compile(r"\battempt=(\d+)/(\d+)")
MODEL_RE = re.compile(r"\bmodel=([A-Za-z0-9._-]+)")
STATUS_RE = re.compile(r"\bstatus=(\d{3})")
ELAPSED_RE = re.compile(r"\belapsed_ms=([0-9]+(?:\.[0-9]+)?)")
TOTAL_ELAPSED_RE = re.compile(r"\btotal_elapsed_ms=([0-9]+(?:\.[0-9]+)?)")
TOKEN_RE = re.compile(
    r"\bprompt_tokens=(\d+|None)\s+candidate_tokens=(\d+|None)\s+thought_tokens=(\d+|None)\s+total_tokens=(\d+|None)"
)
CLAIM_RE = re.compile(r"\bClaimed job_id=([0-9a-fA-F-]{8,}) paper_id=([0-9a-fA-F-]{8,}) attempt=(\d+)")
COMPLETE_RE = re.compile(r"\bAnalysis job completed job_id=([0-9a-fA-F-]{8,}) paper_id=([0-9a-fA-F-]{8,}) provider=([A-Za-z0-9._-]+) model=([A-Za-z0-9._-]+) pages=(\d+)")
FAILED_RE = re.compile(r"\bAnalysis job failed job_id=([0-9a-fA-F-]{8,}) status=(\d{3})")
RETRY_RE = re.compile(r"\bFailed job scheduled for retry job_id=([0-9a-fA-F-]{8,})")


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def aggregate_logs(
    records: list[dict[str, Any]],
    metadata: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not isinstance(records, list):
        raise ValueError("logs must be a list")
    metadata = metadata or {}
    jobs: dict[str, dict[str, Any]] = {}
    calls: dict[tuple[str, str], dict[str, Any]] = {}

    def job_entry(job_id: str) -> dict[str, Any]:
        return jobs.setdefault(job_id, {
            "job_id": job_id, "claim_events": [], "terminal_events": [],
            "retry_events": [], "provider_calls": {},
        })

    for record in records:
        if not isinstance(record, dict):
            continue
        timestamp = record.get("timestamp")
        message = record.get("message")
        if not isinstance(timestamp, str) or not isinstance(message, str):
            continue
        try:
            at = _time(timestamp)
        except ValueError:
            continue

        claim = CLAIM_RE.search(message)
        complete = COMPLETE_RE.search(message)
        failed = FAILED_RE.search(message)
        retry = RETRY_RE.search(message)
        generic_job = JOB_RE.search(message)
        job_id = (
            claim.group(1) if claim else complete.group(1) if complete
            else failed.group(1) if failed else retry.group(1)
            if retry else generic_job.group(1) if generic_job else None
        )
        if not job_id:
            continue
        job = job_entry(job_id)

        if claim:
            job["claim_events"].append({
                "timestamp": at, "paper_id": claim.group(2), "worker_attempt": int(claim.group(3))
            })
        if complete:
            job["terminal_events"].append({
                "timestamp": at, "status": "completed", "paper_id": complete.group(2),
                "provider": complete.group(3), "model": complete.group(4), "pages": int(complete.group(5)),
            })
        if failed:
            job["terminal_events"].append({
                "timestamp": at, "status": "failed", "http_status": int(failed.group(2))
            })
        if retry:
            job["retry_events"].append(at)

        call_match = CALL_RE.search(message)
        if not call_match:
            continue
        call_id = call_match.group(1)
        key = (job_id, call_id)
        call = calls.setdefault(key, {
            "provider_call_id": call_id, "attempts": {}, "usage_events": [],
            "total_elapsed_ms": None, "final_status": None, "models": [],
        })
        job["provider_calls"][call_id] = call
        attempt = ATTEMPT_RE.search(message)
        model = MODEL_RE.search(message)
        status = STATUS_RE.search(message)
        elapsed = ELAPSED_RE.search(message)
        total_elapsed = TOTAL_ELAPSED_RE.search(message)
        if attempt:
            index = int(attempt.group(1))
            event = call["attempts"].setdefault(index, {
                "attempt": index, "model": model.group(1) if model else None,
                "http_status": int(status.group(1)) if status else None,
                "outcome": None, "elapsed_ms": None,
            })
            if model:
                event["model"] = model.group(1)
            if status:
                event["http_status"] = int(status.group(1))
                event["outcome"] = "http_error"
            if "outcome=transport" in message:
                event["outcome"] = "transport_error"
            elif "Gemini attempt succeeded" in message:
                event["outcome"] = "success"
            elif "output cap reached" in message:
                event["outcome"] = "max_tokens"
            elif "incomplete response" in message:
                event["outcome"] = "incomplete"
            elif "invalid JSON" in message or "non-object JSON" in message:
                event["outcome"] = "invalid_json"
            if elapsed:
                event["elapsed_ms"] = float(elapsed.group(1))
        if total_elapsed:
            call["total_elapsed_ms"] = float(total_elapsed.group(1))
        if "All Gemini models failed" in message:
            call["final_status"] = "all_models_failed"
        token_match = TOKEN_RE.search(message)
        if token_match:
            call["usage_events"].append({
                "prompt_tokens": int(token_match.group(1)) if token_match.group(1) != "None" else None,
                "candidate_tokens": int(token_match.group(2)) if token_match.group(2) != "None" else None,
                "thought_tokens": int(token_match.group(3)) if token_match.group(3) != "None" else None,
                "total_tokens": int(token_match.group(4)) if token_match.group(4) != "None" else None,
            })

    output = []
    for job_id, job in jobs.items():
        claims = sorted(job["claim_events"], key=lambda x: x["timestamp"])
        terminals = sorted(job["terminal_events"], key=lambda x: x["timestamp"])
        first_claim = claims[0]["timestamp"] if claims else None
        final_terminal = terminals[-1] if terminals else None
        last_time = final_terminal["timestamp"] if final_terminal else None
        pipeline_latency = (
            round((last_time - first_claim).total_seconds() * 1000, 3)
            if first_claim and last_time and last_time >= first_claim else None
        )
        provider_calls = []
        for call_id, call in job["provider_calls"].items():
            attempts = sorted(call["attempts"].values(), key=lambda x: x["attempt"])
            usage = call["usage_events"]
            provider_calls.append({
                "provider_call_id": call_id,
                "provider_attempts": len(attempts),
                "models": [x["model"] for x in attempts if x["model"]],
                "attempts": attempts,
                "prompt_tokens": sum(x["prompt_tokens"] or 0 for x in usage),
                "candidate_tokens": sum(x["candidate_tokens"] or 0 for x in usage),
                "thought_tokens": sum(x["thought_tokens"] or 0 for x in usage),
                "total_tokens": sum(x["total_tokens"] or 0 for x in usage),
                "token_usage_complete": all(
                    x[field] is not None
                    for x in usage
                    for field in ("prompt_tokens", "candidate_tokens", "thought_tokens", "total_tokens")
                ),
                "total_elapsed_ms": call["total_elapsed_ms"],
                "final_status": call["final_status"],
            })
        meta = metadata.get(job_id, {})
        output.append({
            "job_id": job_id,
            "paper_id": (final_terminal or {}).get("paper_id")
                        or (claims[-1]["paper_id"] if claims else None),
            "paper_sha256": meta.get("paper_sha256"),
            "commit": meta.get("commit"),
            "repeat": meta.get("repeat"),
            "worker_claim_attempts": len(claims),
            "retry_scheduled_count": len(job["retry_events"]),
            "status": (final_terminal or {}).get("status", "incomplete"),
            "provider": (final_terminal or {}).get("provider"),
            "final_model": (final_terminal or {}).get("model"),
            "pages": (final_terminal or {}).get("pages"),
            "pipeline_latency_ms": pipeline_latency,
            "provider_calls": provider_calls,
            "provider_attempts_total": sum(x["provider_attempts"] for x in provider_calls),
            "prompt_tokens_total": sum(x["prompt_tokens"] for x in provider_calls),
            "candidate_tokens_total": sum(x["candidate_tokens"] for x in provider_calls),
            "thought_tokens_total": sum(x["thought_tokens"] for x in provider_calls),
            "provider_cost_usd": None,
            "cost_status": "NOT_COMPUTED_NO_DATED_PRICE_SCHEDULE",
        })

    return {
        "record_type": "RAILWAY_TELEMETRY_AGGREGATE_NOT_COSTED",
        "jobs": sorted(output, key=lambda x: x["job_id"]),
        "warning": (
            "Logs do not prove factual accuracy or billable cost. Attach exact PDF SHA, candidate commit "
            "and repeat metadata before using any job in paired Q2 comparisons."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate sanitized PaperSignal Railway telemetry")
    parser.add_argument("--logs", type=Path, required=True, help="JSON array of Railway log records")
    parser.add_argument("--metadata", type=Path, help="Optional job_id -> PDF SHA/commit/repeat JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    logs = json.loads(args.logs.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8")) if args.metadata else {}
    result = aggregate_logs(logs, metadata)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "record_type": result["record_type"],
        "job_count": len(result["jobs"]),
        "completed": sum(x["status"] == "completed" for x in result["jobs"]),
        "failed": sum(x["status"] == "failed" for x in result["jobs"]),
        "incomplete": sum(x["status"] == "incomplete" for x in result["jobs"]),
        "provider_cost_computed": False,
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
