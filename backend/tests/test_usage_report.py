from app.usage_report import summarize


def test_summarize_gemini_usage_and_latency_without_content():
    lines = [
        "INFO Gemini attempt telemetry provider=gemini model=gemini-primary http_status=200 latency_ms=800",
        "INFO Gemini usage provider=gemini model=gemini-primary finish=STOP prompt_tokens=100 candidate_tokens=40 thought_tokens=10 total_tokens=150 latency_ms=800",
        "INFO Analysis job completed job_id=abc paper_id=def provider=gemini model=gemini-primary pages=12 duration_ms=2400",
        "INFO Gemini attempt telemetry provider=gemini model=gemini-primary http_status=503 latency_ms=120",
        "INFO Gemini attempt telemetry provider=gemini model=gemini-fallback http_status=200 latency_ms=1100",
        "INFO Gemini usage provider=gemini model=gemini-fallback finish=STOP prompt_tokens=200 candidate_tokens=60 thought_tokens=20 total_tokens=280 latency_ms=1100",
    ]
    report = summarize(lines)
    primary = report["models"]["gemini-primary"]
    assert primary["attempts"] == 2
    assert primary["http_errors"] == 1
    assert primary["http_error_rate"] == 0.5
    assert primary["total_tokens"] == 150
    assert primary["latency_ms"]["median"] == 800
    assert primary["job_duration_ms"]["median"] == 2400
    fallback = report["models"]["gemini-fallback"]
    assert fallback["successful_usage_events"] == 1
    assert fallback["total_tokens"] == 280


def test_summarize_ignores_unrelated_or_incomplete_logs():
    report = summarize([
        "INFO user prompt contains secret content and should be ignored",
        "INFO Gemini attempt telemetry provider=gemini outcome=transport_error error_type=ReadTimeout latency_ms=900",
        "INFO Gemini usage provider=gemini model=gemini-lite total_tokens=not-reported latency_ms=bad",
    ])
    assert "models" in report
    assert "gemini-lite" in report["models"]
    assert report["models"]["gemini-lite"]["total_tokens"] == 0
    assert report["models"]["gemini-lite"]["latency_ms"]["median"] is None
    assert "USD" in report["note"]
