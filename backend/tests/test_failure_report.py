import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.failure_report import classify_failure, summarize_failures


def test_classifies_common_analysis_failure_modes():
    assert classify_failure(429, "provider quota exceeded") == "provider_quota"
    assert classify_failure(504, "upstream timed out") == "timeout"
    assert classify_failure(403, "permission denied") == "authorization"
    assert classify_failure(200, "invalid JSON schema") == "invalid_model_response"
    assert classify_failure(503, "service unavailable") == "provider_unavailable"


def test_aggregates_job_failures_and_model_attempts_without_claiming_recovery():
    report = summarize_failures([
        "WARNING Analysis job failed job_id=abc status=429 duration_ms=1200 reason=provider_quota_exceeded",
        "INFO Gemini attempt telemetry provider=gemini model=primary http_status=503 latency_ms=200",
        "INFO Gemini attempt telemetry provider=gemini model=fallback http_status=200 latency_ms=800",
        "ERROR Analysis job crashed job_id=def duration_ms=2100",
    ])
    assert report["failed_job_count"] == 2
    assert report["failure_categories"]["provider_quota"] == 1
    assert report["failure_categories"]["application_error"] == 1
    assert report["gemini_attempts_by_model"] == {"fallback": 1, "primary": 1}
    assert report["gemini_failed_attempts_by_model"] == {"primary": 1}
    assert "not proof" in report["warning"]
