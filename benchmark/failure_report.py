#!/usr/bin/env python3
"""Aggregate PaperSignal analysis failures and Gemini fallback attempts from exported logs."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

_FIELD = re.compile(r"([a-z_]+)=([^\s]+)")


def classify_failure(status: int | None, reason: str) -> str:
    text = reason.casefold()
    if status == 401 or "unauthorized" in text or "jwt" in text or "인증" in text:
        return "authentication"
    if status == 403 or "forbidden" in text or "permission" in text or "권한" in text:
        return "authorization"
    if status == 404 or "not found" in text or "찾을 수 없" in text:
        return "resource_not_found"
    if status == 429 or "rate limit" in text or "quota" in text or "resource_exhausted" in text or "할당량" in text:
        return "provider_quota"
    if status in (408, 504) or "timeout" in text or "timed out" in text:
        return "timeout"
    if status in (500, 502, 503) or "unavailable" in text or "service error" in text:
        return "provider_unavailable"
    if "json" in text or "parse" in text or "schema" in text or "응답 형식" in text:
        return "invalid_model_response"
    if status is not None and status >= 400:
        return "http_error_other"
    return "application_error"


def summarize_failures(lines: Iterable[str]) -> dict:
    failures = []
    attempts = []
    for line in lines:
        fields = dict(_FIELD.findall(line))
        if "Gemini attempt telemetry" in line:
            attempts.append(fields)
        if "Analysis job failed" in line or "Analysis job crashed" in line:
            status_raw = fields.get("status")
            status = int(status_raw) if status_raw and status_raw.isdigit() else None
            reason = fields.get("reason", fields.get("error", ""))
            category = classify_failure(status, reason)
            failures.append({
                "category": category,
                "status": status,
                "duration_ms": int(fields["duration_ms"]) if fields.get("duration_ms", "").isdigit() else None,
            })
    categories = Counter(item["category"] for item in failures)
    model_attempts = Counter(item.get("model", "unknown") for item in attempts)
    model_errors = Counter(
        item.get("model", "unknown")
        for item in attempts
        if (item.get("http_status", "").isdigit() and int(item["http_status"]) >= 400)
        or item.get("outcome") == "transport_error"
    )
    return {
        "failed_job_count": len(failures),
        "failure_categories": dict(sorted(categories.items())),
        "failed_jobs": failures,
        "gemini_attempt_count": len(attempts),
        "gemini_attempts_by_model": dict(sorted(model_attempts.items())),
        "gemini_failed_attempts_by_model": dict(sorted(model_errors.items())),
        "warning": "Log-derived diagnostics only. A fallback attempt is not proof that a user job recovered; correlate with job completion events before measuring recovery rate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", type=Path)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/failure-report.json"))
    args = parser.parse_args()
    with args.log_file.open(encoding="utf-8") as handle:
        report = summarize_failures(handle)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("failed_job_count", "failure_categories", "gemini_attempt_count", "gemini_failed_attempts_by_model")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
