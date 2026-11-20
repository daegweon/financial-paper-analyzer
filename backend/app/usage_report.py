#!/usr/bin/env python3
"""Summarize PaperSignal content-free Gemini telemetry logs."""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

_FIELD = re.compile(r"([a-z_]+)=([^\s]+)")


def _fields(line: str) -> dict[str, str]:
    return dict(_FIELD.findall(line))


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    if percentile == 0.50:
        return round(statistics.median(ordered))
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * percentile) - 1))
    return ordered[index]


def summarize(lines: Iterable[str]) -> dict:
    models: dict[str, dict] = defaultdict(lambda: {
        "attempts": 0, "successful_usage_events": 0, "http_errors": 0,
        "prompt_tokens": 0, "candidate_tokens": 0, "thought_tokens": 0,
        "total_tokens": 0, "latency_samples_ms": [], "job_duration_samples_ms": [],
    })
    for line in lines:
        if not any(marker in line for marker in (
            "Gemini attempt telemetry", "Gemini usage provider=gemini", "Analysis job completed"
        )):
            continue
        fields = _fields(line)
        model = fields.get("model")
        if not model:
            continue
        item = models[model]
        if "Gemini attempt telemetry" in line:
            item["attempts"] += 1
            status = fields.get("http_status", "")
            if status.isdigit() and int(status) >= 400:
                item["http_errors"] += 1
            latency = fields.get("latency_ms", "")
            if latency.isdigit():
                item["latency_samples_ms"].append(int(latency))
        elif "Gemini usage provider=gemini" in line:
            item["successful_usage_events"] += 1
            for name in ("prompt_tokens", "candidate_tokens", "thought_tokens", "total_tokens"):
                value = fields.get(name, "")
                if value.isdigit():
                    item[name] += int(value)
        else:
            duration = fields.get("duration_ms", "")
            if duration.isdigit():
                item["job_duration_samples_ms"].append(int(duration))

    output = {}
    for model, item in sorted(models.items()):
        latencies = item.pop("latency_samples_ms")
        durations = item.pop("job_duration_samples_ms")
        item["latency_ms"] = {
            "samples": len(latencies),
            "median": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        }
        item["job_duration_ms"] = {
            "samples": len(durations),
            "median": _percentile(durations, 0.50),
            "p95": _percentile(durations, 0.95),
        }
        item["http_error_rate"] = round(item["http_errors"] / item["attempts"], 4) if item["attempts"] else None
        output[model] = item
    return {"models": output, "note": "Token totals are provider-reported only; no USD cost is inferred."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", type=Path, help="UTF-8 text file exported from Railway logs")
    args = parser.parse_args()
    with args.log_file.open(encoding="utf-8") as handle:
        print(json.dumps(summarize(handle), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
