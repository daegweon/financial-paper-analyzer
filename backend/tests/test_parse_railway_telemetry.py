"""Synthetic Railway log aggregation tests; no real paper text or credentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.parse_railway_telemetry import aggregate_logs


def test_aggregate_job_attempts_tokens_and_pipeline_latency_without_cost_guess():
    logs = [
        {"timestamp": "2026-11-17T00:00:00Z",
         "message": "INFO:papersignal:Claimed job_id=job-12345678 paper_id=paper-12345678 attempt=1"},
        {"timestamp": "2026-11-17T00:00:02Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=job-12345678 provider_call_id=call1234567890 attempt=1/2 model=gemini-3.5-flash-lite status=503 elapsed_ms=180.5 body=unavailable"},
        {"timestamp": "2026-11-17T00:00:03Z",
         "message": "INFO:papersignal:Gemini usage job_id=job-12345678 provider_call_id=call1234567890 attempt=2/2 provider_attempts=2 model=gemini-3.6-flash elapsed_ms=900.0 finish=STOP prompt_tokens=120 candidate_tokens=30 thought_tokens=5 total_tokens=155"},
        {"timestamp": "2026-11-17T00:00:04Z",
         "message": "INFO:papersignal:Gemini attempt succeeded job_id=job-12345678 provider_call_id=call1234567890 attempt=2/2 provider_attempts=2 model=gemini-3.6-flash elapsed_ms=900.0 total_elapsed_ms=1900.0"},
        {"timestamp": "2026-11-17T00:00:10Z",
         "message": "INFO:papersignal:Analysis job completed job_id=job-12345678 paper_id=paper-12345678 provider=gemini model=gemini-3.6-flash pages=40"},
    ]
    metadata = {"job-12345678": {"paper_sha256": "a" * 64, "commit": "b" * 40, "repeat": 1}}
    result = aggregate_logs(logs, metadata)
    job = result["jobs"][0]
    assert job["status"] == "completed"
    assert job["pipeline_latency_ms"] == 10000
    assert job["provider_attempts_total"] == 2
    assert job["prompt_tokens_total"] == 120
    assert job["candidate_tokens_total"] == 30
    assert job["thought_tokens_total"] == 5
    assert job["provider_cost_usd"] is None
    assert job["paper_sha256"] == "a" * 64
    call = job["provider_calls"][0]
    assert call["models"] == ["gemini-3.5-flash-lite", "gemini-3.6-flash"]
    assert call["attempts"][0]["http_status"] == 503
    assert call["total_elapsed_ms"] == 1900.0


def test_aggregate_all_models_failed_and_worker_retry_without_raw_logs():
    logs = [
        {"timestamp": "2026-11-17T01:00:00Z",
         "message": "INFO:papersignal:Claimed job_id=job-fail-123456 paper_id=paper-987654 attempt=2"},
        {"timestamp": "2026-11-17T01:00:01Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=job-fail-123456 provider_call_id=call9876543210 attempt=1/2 model=gemini-3.5-flash-lite status=503 elapsed_ms=100.0 body=busy"},
        {"timestamp": "2026-11-17T01:00:02Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=job-fail-123456 provider_call_id=call9876543210 attempt=2/2 model=gemini-3.6-flash status=429 elapsed_ms=200.0 body=quota"},
        {"timestamp": "2026-11-17T01:00:02Z",
         "message": "ERROR:papersignal:All Gemini models failed job_id=job-fail-123456 provider_call_id=call9876543210 attempts=2 total_elapsed_ms=1400.0 failures=gemini-3.5-flash-lite=503; gemini-3.6-flash=429"},
        {"timestamp": "2026-11-17T01:00:03Z",
         "message": "WARNING:papersignal:Analysis job failed job_id=job-fail-123456 status=503 reason=provider unavailable"},
        {"timestamp": "2026-11-17T01:00:04Z",
         "message": "WARNING:papersignal:Failed job scheduled for retry job_id=job-fail-123456"},
    ]
    result = aggregate_logs(logs)
    job = result["jobs"][0]
    assert job["status"] == "failed"
    assert job["retry_scheduled_count"] == 1
    assert job["provider_attempts_total"] == 2
    assert job["provider_calls"][0]["final_status"] == "all_models_failed"
    serialized = str(result)
    assert "provider unavailable" not in serialized
    assert "busy" not in serialized
    assert job["provider_cost_usd"] is None


def test_ignores_malformed_and_unrelated_log_records():
    result = aggregate_logs([
        {"timestamp": "not-a-time", "message": "bad"},
        {"timestamp": "2026-11-17T00:00:00Z", "message": "unrelated startup message"},
        {"message": "missing timestamp"},
    ])
    assert result["jobs"] == []
