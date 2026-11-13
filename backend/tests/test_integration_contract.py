import asyncio

"""Integration-contract tests for the PDF analysis endpoint.

This simulates Supabase Auth, private Storage, and RLS-scoped Data API calls
without creating users or documents in production.
"""
from __future__ import annotations

import fitz
import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as module


def make_pdf(text: str = "Financial asset pricing and volatility risk premium") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((45, 90), text)
    pdf = doc.tobytes()
    doc.close()
    return pdf


def test_pdf_extracts_page_text_and_correct_evidence():
    count, pages = module.extract_pages(make_pdf())
    assert count == 1
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "asset pricing" in pages[0]["text"].lower()
    result = module.extractive_result(count, pages)
    assert result["mode"] == "extractive"
    assert "asset pricing" in result["keywords"]
    assert result["evidence"][0]["quote"] in pages[0]["text"]


def test_image_only_pdf_requires_ocr():
    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    with pytest.raises(ValueError, match="OCR"):
        module.extract_pages(data)


def test_size_and_signature_limits():
    with pytest.raises(ValueError):
        module.extract_pages(b"notpdf")
    with pytest.raises(ValueError):
        module.extract_pages(b"%PDF-" + b"a" * (module.MAX_BYTES + 1))


def test_reference_requires_correct_page_and_exact_quote():
    actual = [{"page": 2, "text": "The estimated liquidity risk premium is significant."}]
    proposed = [
        {"page": 2, "quote": "liquidity risk premium"},
        {"page": 1, "quote": "liquidity risk premium"},
        {"page": 2, "quote": "invented quote does not exist"},
    ]
    assert module.validate_evidence(proposed, actual) == [
        {"page": 2, "quote": "liquidity risk premium"}
    ]


def test_unauthed_api_request_is_denied(monkeypatch):
    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    res = TestClient(module.app).post("/api/analyze/00000000-0000-4000-8000-000000000001")
    assert res.status_code == 401
    assert TestClient(module.app).get("/health").json()["status"] == "ok"


def test_authenticated_request_queues_background_job(monkeypatch):
    user_id = "11111111-1111-4111-8111-111111111111"
    paper_id = "22222222-2222-4222-8222-222222222222"
    job_id = "44444444-4444-4444-8444-444444444444"
    requests_seen = []

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return None
        async def get(self, url, **kwargs):
            requests_seen.append(("GET", url, kwargs))
            if url.endswith("/auth/v1/user"):
                return httpx.Response(200, json={"id": user_id})
            if url.endswith("/rest/v1/papers"):
                return httpx.Response(200, json=[{
                    "id": paper_id, "user_id": user_id, "storage_path": user_id + "/contract.pdf"
                }])
            if url.endswith("/rest/v1/analysis_jobs"):
                return httpx.Response(200, json=[])
            raise AssertionError("Unexpected GET " + url)
        async def post(self, url, **kwargs):
            requests_seen.append(("POST", url, kwargs))
            assert url.endswith("/rest/v1/analysis_jobs")
            assert kwargs["json"]["paper_id"] == paper_id
            assert kwargs["json"]["user_id"] == user_id
            return httpx.Response(201, json=[{"id": job_id, "status": "queued", "stage": "queued"}])

    async def fake_worker(*args):
        return None

    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module, "_process_analysis_job", fake_worker)

    res = TestClient(module.app).post(
        "/api/analyze/" + paper_id,
        headers={"Authorization": "Bearer valid_test_jwt"},
    )
    assert res.status_code == 202
    assert res.json() == {"status": "queued", "job_id": job_id, "stage": "queued"}
    assert [method for method, _, _ in requests_seen] == ["GET", "GET", "GET", "POST"]


def test_analysis_job_status_is_scoped_to_authenticated_owner(monkeypatch):
    user_id = "11111111-1111-4111-8111-111111111111"
    paper_id = "22222222-2222-4222-8222-222222222222"
    job_id = "44444444-4444-4444-8444-444444444444"

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return None
        async def get(self, url, **kwargs):
            if url.endswith("/auth/v1/user"):
                return httpx.Response(200, json={"id": user_id})
            if url.endswith("/rest/v1/analysis_jobs"):
                assert kwargs["params"]["user_id"] == "eq." + user_id
                return httpx.Response(200, json=[{
                    "id": job_id, "status": "processing", "stage": "gemini_analysis",
                    "error_message": None, "analysis_id": None, "updated_at": "2026-11-13T00:00:00Z",
                    "completed_at": None,
                }])
            raise AssertionError("Unexpected GET " + url)

    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    res = TestClient(module.app).get(
        "/api/analyze/" + paper_id + "/status",
        params={"job_id": job_id},
        headers={"Authorization": "Bearer valid_test_jwt"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "processing"
    assert res.json()["stage"] == "gemini_analysis"


def test_background_job_saves_analysis_and_completes(monkeypatch):
    user_id = "11111111-1111-4111-8111-111111111111"
    paper_id = "22222222-2222-4222-8222-222222222222"
    job_id = "44444444-4444-4444-8444-444444444444"
    analysis_id = "55555555-5555-4555-8555-555555555555"
    pdf_data = make_pdf()

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return None
        async def get(self, url, **kwargs):
            if url.endswith("/rest/v1/papers"):
                return httpx.Response(200, json=[{
                    "id": paper_id, "user_id": user_id, "storage_path": user_id + "/contract.pdf"
                }])
            if "/storage/v1/object/authenticated/papers/" in url:
                return httpx.Response(200, content=pdf_data)
            raise AssertionError("Unexpected GET " + url)
        async def post(self, url, **kwargs):
            assert url.endswith("/rest/v1/analyses")
            assert kwargs["json"]["paper_id"] == paper_id
            assert kwargs["json"]["user_id"] == user_id
            assert kwargs["json"]["result"]["mode"] == "extractive"
            return httpx.Response(201, json=[{"id": analysis_id}])
        async def patch(self, url, **kwargs):
            assert url.endswith("/rest/v1/analysis_jobs") or url.endswith("/rest/v1/papers")
            return httpx.Response(204)

    async def fake_llm_result(page_count, pages):
        return module.extractive_result(page_count, pages) | {
            "analysis_version": "extractive-v3"
        }

    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module, "llm_result", fake_llm_result)
    asyncio.run(module._process_analysis_job(paper_id, job_id, user_id, "valid_test_jwt"))




def test_other_user_paper_returns_404(monkeypatch):
    other_id = "33333333-3333-4333-8333-333333333333"
    paper_id = "22222222-2222-4222-8222-222222222222"
    calls = []

    class MockClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return None
        async def get(self, url, **kwargs):
            calls.append(url)
            if url.endswith("/auth/v1/user"):
                return httpx.Response(200, json={"id": "11111111-1111-4111-8111-111111111111"})
            if url.endswith("/rest/v1/papers"):
                return httpx.Response(200, json=[{
                    "user_id": other_id,
                    "storage_path": other_id + "/secret.pdf",
                }])
            raise AssertionError("Must not fetch other user's private PDF")
    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    monkeypatch.setattr(module.httpx, "AsyncClient", MockClient)
    res = TestClient(module.app).post(
        "/api/analyze/" + paper_id,
        headers={"Authorization": "Bearer valid_test_jwt"},
    )
    assert res.status_code == 404
    assert len(calls) == 2
