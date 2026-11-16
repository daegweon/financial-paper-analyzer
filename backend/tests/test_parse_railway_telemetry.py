"""Synthetic Railway log aggregation tests; no real paper text or credentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.parse_railway_telemetry import aggregate_logs


def test_aggregate_job_attempts_tokens_and_pipeline_latency_without_cost_guess():
    logs = [
        {"timestamp": "2026-11-17T00:00:00Z",
         "message": "INFO:papersignal:Claimed job_id=11111111-1111-4111-8111-111111111111 paper_id=22222222-2222-4222-8222-222222222222 attempt=1 job_created_at=2026-11-16T23:59:58Z"},
        {"timestamp": "2026-11-17T00:00:02Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=11111111-1111-4111-8111-111111111111 provider_call_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa attempt=1/2 model=gemini-3.5-flash-lite status=503 elapsed_ms=180.5 body=unavailable"},
        {"timestamp": "2026-11-17T00:00:03Z",
         "message": "INFO:papersignal:Gemini usage job_id=11111111-1111-4111-8111-111111111111 provider_call_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa attempt=2/2 provider_attempts=2 model=gemini-3.6-flash elapsed_ms=900.0 finish=STOP prompt_tokens=120 candidate_tokens=30 thought_tokens=5 total_tokens=155"},
        {"timestamp": "2026-11-17T00:00:04Z",
         "message": "INFO:papersignal:Gemini attempt succeeded job_id=11111111-1111-4111-8111-111111111111 provider_call_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa attempt=2/2 provider_attempts=2 model=gemini-3.6-flash elapsed_ms=900.0 total_elapsed_ms=1900.0"},
        {"timestamp": "2026-11-17T00:00:10Z",
         "message": "INFO:papersignal:Analysis job completed job_id=11111111-1111-4111-8111-111111111111 paper_id=22222222-2222-4222-8222-222222222222 provider=gemini model=gemini-3.6-flash pages=40"},
    ]
    metadata = {"11111111-1111-4111-8111-111111111111": {"paper_sha256": "a" * 64, "commit": "b" * 40, "repeat": 1}}
    result = aggregate_logs(logs, metadata)
    job = result["jobs"][0]
    assert job["status"] == "completed"
    assert job["claim_to_terminal_ms"] == 10000
    assert job["job_created_to_terminal_ms"] == 12000
    assert job["job_created_at"] == "2026-11-16T23:59:58+00:00"
    assert job["latency_scope"] == "job_created_to_terminal_and_worker_claim_to_terminal"
    assert job["full_pipeline_latency_ms"] is None
    assert job["full_pipeline_latency_status"] == "UPLOAD_START_TIMESTAMP_NOT_LOGGED"
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
         "message": "INFO:papersignal:Claimed job_id=33333333-3333-4333-8333-333333333333 paper_id=44444444-4444-4444-8444-444444444444 attempt=2"},
        {"timestamp": "2026-11-17T01:00:01Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=33333333-3333-4333-8333-333333333333 provider_call_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb attempt=1/2 model=gemini-3.5-flash-lite status=503 elapsed_ms=100.0 body=busy"},
        {"timestamp": "2026-11-17T01:00:02Z",
         "message": "WARNING:papersignal:Gemini attempt failed job_id=33333333-3333-4333-8333-333333333333 provider_call_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb attempt=2/2 model=gemini-3.6-flash status=429 elapsed_ms=200.0 body=quota"},
        {"timestamp": "2026-11-17T01:00:02Z",
         "message": "ERROR:papersignal:All Gemini models failed job_id=33333333-3333-4333-8333-333333333333 provider_call_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb attempts=2 total_elapsed_ms=1400.0 failures=gemini-3.5-flash-lite=503; gemini-3.6-flash=429"},
        {"timestamp": "2026-11-17T01:00:03Z",
         "message": "WARNING:papersignal:Analysis job failed job_id=33333333-3333-4333-8333-333333333333 status=503 reason=provider unavailable"},
        {"timestamp": "2026-11-17T01:00:04Z",
         "message": "WARNING:papersignal:Failed job scheduled for retry job_id=33333333-3333-4333-8333-333333333333"},
    ]
    result = aggregate_logs(logs)
    job = result["jobs"][0]
    assert job["status"] == "failed"
    assert job["job_created_to_terminal_ms"] is None
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


def test_missing_thought_token_count_is_marked_incomplete_not_invented():
    logs = [
        {"timestamp": "2026-11-17T02:00:00Z",
         "message": "INFO:papersignal:Claimed job_id=55555555-5555-4555-8555-555555555555 paper_id=66666666-6666-4666-8666-666666666666 attempt=1"},
        {"timestamp": "2026-11-17T02:00:01Z",
         "message": "INFO:papersignal:Gemini usage job_id=55555555-5555-4555-8555-555555555555 provider_call_id=cccccccccccccccccccccccccccccccc attempt=1/1 provider_attempts=1 model=gemini-3.5-flash-lite elapsed_ms=700.0 finish=STOP prompt_tokens=100 candidate_tokens=20 thought_tokens=None total_tokens=120"},
        {"timestamp": "2026-11-17T02:00:02Z",
         "message": "INFO:papersignal:Gemini attempt succeeded job_id=55555555-5555-4555-8555-555555555555 provider_call_id=cccccccccccccccccccccccccccccccc attempt=1/1 provider_attempts=1 model=gemini-3.5-flash-lite elapsed_ms=700.0 total_elapsed_ms=710.0"},
        {"timestamp": "2026-11-17T02:00:03Z",
         "message": "INFO:papersignal:Analysis job completed job_id=55555555-5555-4555-8555-555555555555 paper_id=66666666-6666-4666-8666-666666666666 provider=gemini model=gemini-3.5-flash-lite pages=30"},
    ]
    result = aggregate_logs(logs)
    call = result["jobs"][0]["provider_calls"][0]
    assert call["prompt_tokens"] == 100
    assert call["candidate_tokens"] == 20
    assert call["thought_tokens"] == 0
    assert call["total_tokens"] == 120
    assert call["token_usage_complete"] is False


def test_malformed_job_created_timestamp_does_not_create_latency():
    logs = [
        {"timestamp": "2026-11-17T03:00:00Z",
         "message": "INFO:papersignal:Claimed job_id=77777777-7777-4777-8777-777777777777 paper_id=88888888-8888-4888-8888-888888888888 attempt=1 job_created_at=not-a-time"},
        {"timestamp": "2026-11-17T03:00:05Z",
         "message": "INFO:papersignal:Analysis job completed job_id=77777777-7777-4777-8777-777777777777 paper_id=88888888-8888-4888-8888-888888888888 provider=gemini model=gemini-3.6-flash pages=40"},
    ]
    job = aggregate_logs(logs)["jobs"][0]
    assert job["status"] == "completed"
    assert job["job_created_at"] is None
    assert job["job_created_to_terminal_ms"] is None
    assert job["full_pipeline_latency_ms"] is None
