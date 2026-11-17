"""Isolated baseline runner safety tests: no provider calls or production writes."""
from __future__ import annotations

from hashlib import sha256

import fitz
import pytest
from fastapi.testclient import TestClient

from app import benchmark_runner as runner


def pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Synthetic held-out source PDF")
    data = doc.tobytes()
    doc.close()
    return data


def test_upload_accepts_only_exact_locked_pdf_bytes(monkeypatch):
    raw = pdf_bytes()
    paper = {
        "id": "H01",
        "pdf_sha256": sha256(raw).hexdigest(),
        "pdf_byte_length": len(raw),
        "actual_page_count": 1,
    }
    monkeypatch.setattr(runner, "RUN_TOKEN", "test-token")
    monkeypatch.setitem(runner.HELDOUT_LOCK, "heldout_papers", [paper])
    runner.UPLOADED_HELDOUT.clear()
    try:
        with TestClient(runner.app) as client:
            response = client.post(
                "/benchmark/heldout/H01",
                headers={"X-Benchmark-Token": "test-token", "Content-Type": "application/pdf"},
                content=raw,
            )
            assert response.status_code == 200
            assert response.json()["status"] == "verified_in_memory"
            assert response.json()["sha256"] == sha256(raw).hexdigest()
            assert runner.UPLOADED_HELDOUT["H01"] == raw
            wrong = client.post(
                "/benchmark/heldout/H01",
                headers={"X-Benchmark-Token": "test-token", "Content-Type": "application/pdf"},
                content=raw + b"extra",
            )
            assert wrong.status_code == 422
            assert runner.UPLOADED_HELDOUT["H01"] == raw
            forbidden = client.post(
                "/benchmark/heldout/H02",
                headers={"X-Benchmark-Token": "wrong", "Content-Type": "application/pdf"},
                content=raw,
            )
            assert forbidden.status_code == 401
            unsupported = client.post(
                "/benchmark/heldout/H01",
                headers={"X-Benchmark-Token": "test-token", "Content-Type": "application/octet-stream"},
                content=raw,
            )
            assert unsupported.status_code == 415
    finally:
        runner.UPLOADED_HELDOUT.clear()


def test_upload_rejects_oversized_body(monkeypatch):
    monkeypatch.setattr(runner, "RUN_TOKEN", "test-token")
    monkeypatch.setattr(runner, "MAX_HELDOUT_BYTES", 10)
    with TestClient(runner.app) as client:
        response = client.post(
            "/benchmark/heldout/H01",
            headers={"X-Benchmark-Token": "test-token", "Content-Type": "application/pdf"},
            content=b"%PDF-" + b"x" * 20,
        )
        assert response.status_code == 413


def test_baseline_run_refuses_production_writes_even_when_opted_in(monkeypatch):
    monkeypatch.setattr(runner, "RUN_TOKEN", "test-token")
    monkeypatch.setenv("BENCHMARK_ENABLE_ISOLATED_WRITES", "true")
    monkeypatch.setenv("BENCHMARK_ALLOWED_SUPABASE_HOST", "hwmtayrecsfxernhssro.supabase.co")
    monkeypatch.setattr(runner.engine, "SUPABASE_URL", "https://hwmtayrecsfxernhssro.supabase.co")
    with pytest.raises(RuntimeError, match="Production Supabase writes"):
        runner.isolated_write_guard()
    with TestClient(runner.app) as client:
        response = client.post("/benchmark/run", headers={"X-Benchmark-Token": "test-token"})
        assert response.status_code == 403


def test_baseline_run_disabled_by_default_and_requires_explicit_staging_host(monkeypatch):
    monkeypatch.delenv("BENCHMARK_ENABLE_ISOLATED_WRITES", raising=False)
    monkeypatch.delenv("BENCHMARK_ALLOWED_SUPABASE_HOST", raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        runner.isolated_write_guard()
    monkeypatch.setenv("BENCHMARK_ENABLE_ISOLATED_WRITES", "true")
    monkeypatch.setattr(runner.engine, "SUPABASE_URL", "https://example-stage.supabase.co")
    with pytest.raises(RuntimeError, match="not configured"):
        runner.isolated_write_guard()
    monkeypatch.setenv("BENCHMARK_ALLOWED_SUPABASE_HOST", "example-stage.supabase.co")
    runner.isolated_write_guard()
