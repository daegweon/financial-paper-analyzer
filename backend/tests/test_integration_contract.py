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


def test_authenticated_pdf_full_analysis_contract(monkeypatch):
    """Auth -> paper ownership -> private storage -> extraction -> SQL insert/patch."""
    user_id = "11111111-1111-4111-8111-111111111111"
    paper_id = "22222222-2222-4222-8222-222222222222"
    path = user_id + "/contract.pdf"
    requests_seen = []
    pdf_data = make_pdf()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout")
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return None
        async def get(self, url, **kwargs):
            requests_seen.append(("GET", url, kwargs))
            assert kwargs["headers"]["Authorization"] == "Bearer valid_test_jwt"
            if url.endswith("/auth/v1/user"):
                return httpx.Response(200, json={"id": user_id})
            if url.endswith("/rest/v1/papers"):
                return httpx.Response(200, json=[{"id": paper_id, "user_id": user_id, "storage_path": path}])
            if "/storage/v1/object/authenticated/papers/" in url:
                return httpx.Response(200, content=pdf_data)
            return httpx.Response(404)
        async def post(self, url, **kwargs):
            requests_seen.append(("POST", url, kwargs))
            assert kwargs["json"]["paper_id"] == paper_id
            assert kwargs["json"]["user_id"] == user_id
            assert kwargs["json"]["result"]["page_count"] == 1
            assert kwargs["json"]["result"]["mode"] == "extractive"
            return httpx.Response(201, json={})
        async def patch(self, url, **kwargs):
            requests_seen.append(("PATCH", url, kwargs))
            assert kwargs["json"] == {"status": "completed", "page_count": 1}
            return httpx.Response(204)

    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "publishable_mock")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    res = TestClient(module.app).post(
        "/api/analyze/" + paper_id,
        headers={"Authorization": "Bearer valid_test_jwt"},
    )
    assert res.status_code == 200, res.text
    assert res.json() == {"status": "completed", "mode": "extractive", "page_count": 1}
    assert [method for method, _, _ in requests_seen] == [
        "GET", "GET", "GET", "POST", "PATCH"
    ]


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
