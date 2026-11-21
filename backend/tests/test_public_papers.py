"""Public-paper import security and API tests. Network access is mocked."""
import asyncio
import socket

import fitz
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main
import app.public_papers as papers


AUTH = {"Authorization": "Bearer verified_mock_token"}


def make_pdf():
    doc = fitz.open()
    doc.new_page().insert_text((50, 80), "Financial research paper")
    data = doc.tobytes()
    doc.close()
    return data


@pytest.mark.parametrize("url", [
    "http://example.org/p.pdf",
    "file:///etc/passwd",
    "https://localhost/p.pdf",
    "https://127.0.0.1/p.pdf",
    "https://[::1]/p.pdf",
    "https://admin:password@example.org/p.pdf",
    "https://example.org:8080/p.pdf",
    "https://metadata.google.internal/latest",
    "https://example.org/p.pdf\r\nHost:localhost",
])
def test_unsafe_urls_rejected(url):
    with pytest.raises(HTTPException) as exc:
        papers._validate_public_https_url(url)
    assert exc.value.status_code == 422


def test_safe_url_normalized():
    assert papers._validate_public_https_url("https://Example.Org/p.pdf#page=2") == (
        "https://example.org/p.pdf", "example.org"
    )


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.169.254", "::1", "fc00::1",
])
def test_ssrf_private_dns_rejected(monkeypatch, address):
    monkeypatch.setattr(papers.socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))
    ])
    with pytest.raises(HTTPException):
        asyncio.run(papers._resolve_public_target("https://publisher.org/a.pdf"))


def test_ssrf_rejects_mixed_public_private_dns(monkeypatch):
    monkeypatch.setattr(papers.socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443)),
    ])
    with pytest.raises(HTTPException):
        asyncio.run(papers._resolve_public_target("https://publisher.org/a.pdf"))


def test_public_dns_pins_actual_destination(monkeypatch):
    monkeypatch.setattr(papers.socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))
    ])
    assert asyncio.run(papers._resolve_public_target("https://publisher.org/a.pdf")) == (
        "https://1.1.1.1/a.pdf", "publisher.org"
    )


def test_pdf_validation_and_limits():
    papers._validate_pdf(make_pdf())
    for data in [b"<html>bad</html>", b"%PDF-" + b"x" * papers.MAX_PDF_BYTES]:
        with pytest.raises(HTTPException):
            papers._validate_pdf(data)
    doc = fitz.open()
    doc.new_page()
    encrypted = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user"
    )
    doc.close()
    with pytest.raises(HTTPException):
        papers._validate_pdf(encrypted)


def test_both_routes_require_auth():
    api = TestClient(main.app)
    assert api.get("/api/public-papers/search?query=ETF").status_code == 401
    assert api.post("/api/public-papers/download", json={"url": "https://publisher.org/a.pdf"}).status_code == 401
    assert api.get("/api/public-papers/search?query=x", headers=AUTH).status_code == 422


def test_openalex_normalizes_oa_pdf_and_unknown_license():
    item = papers._paper_search_item({
        "id": "https://openalex.org/W1",
        "title": "ETF arbitrage",
        "publication_year": 2026,
        "authorships": [{"author": {"display_name": "Researcher"}}],
        "open_access": {"is_oa": True},
        "best_oa_location": {"is_oa": True, "pdf_url": "https://publisher.org/etf.pdf"},
    })
    assert item["pdf_url"] == "https://publisher.org/etf.pdf"
    assert item["authors"] == ["Researcher"]
    assert item["license"] == "미확인"
    assert papers._paper_search_item({"title": "No PDF", "open_access": {"is_oa": True}})["pdf_url"] is None


def test_search_uses_server_optional_key_and_pagination(monkeypatch):
    async def authenticate(token):
        assert token == "verified_mock_token"
        return "verified-user"
    monkeypatch.setattr(papers, "_authenticated_user", authenticate)
    monkeypatch.setenv("OPENALEX_API_KEY", "qa_key")
    requests = []
    class Client:
        def __init__(self, *args, **kwargs): assert kwargs["trust_env"] is False
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def get(self, url, *, params, headers):
            requests.append((url, params, headers))
            return httpx.Response(200, json={"meta": {"count": 32}, "results": [{
                "id": "https://openalex.org/W1", "title": "Portfolio",
                "best_oa_location": {"is_oa": True, "pdf_url": "https://publisher.org/a.pdf"},
                "open_access": {"is_oa": True},
            }]})
    monkeypatch.setattr(papers.httpx, "AsyncClient", Client)
    res = TestClient(main.app).get("/api/public-papers/search?query=ETF&page=2", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["has_more"] is True
    assert res.json()["results"][0]["title"] == "Portfolio"
    assert requests[0][1]["page"] == 2
    assert requests[0][2]["Authorization"] == "Bearer qa_key"


def test_download_endpoint_returns_pdf_without_privileged_write(monkeypatch):
    data = make_pdf()
    async def authenticate(token): return "verified-user"
    async def download(url):
        assert url == "https://publisher.org/p.pdf"
        return data
    monkeypatch.setattr(papers, "_authenticated_user", authenticate)
    monkeypatch.setattr(papers, "_download_external_pdf", download)
    res = TestClient(main.app).post(
        "/api/public-papers/download", json={"url": "https://publisher.org/p.pdf"}, headers=AUTH
    )
    assert res.status_code == 200 and res.content == data
    assert res.headers["cache-control"] == "no-store"
    assert res.headers["content-type"] == "application/pdf"


def test_external_download_uses_pinned_host_and_tls_sni(monkeypatch):
    data = make_pdf()
    async def resolve(url): return "https://1.1.1.1/p.pdf", "publisher.org"
    monkeypatch.setattr(papers, "_resolve_public_target", resolve)
    cls = httpx.AsyncClient
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(200, content=data)
    monkeypatch.setattr(papers.httpx, "AsyncClient", lambda **kwargs: cls(transport=httpx.MockTransport(respond)))
    assert asyncio.run(papers._download_external_pdf("https://publisher.org/p.pdf")) == data
    assert str(seen[0].url) == "https://1.1.1.1/p.pdf"
    assert seen[0].headers["Host"] == "publisher.org"
    assert seen[0].extensions["sni_hostname"] == "publisher.org"


def test_redirect_to_private_url_is_rejected(monkeypatch):
    async def resolve(url): return "https://1.1.1.1/p.pdf", "publisher.org"
    monkeypatch.setattr(papers, "_resolve_public_target", resolve)
    cls = httpx.AsyncClient
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})
    monkeypatch.setattr(papers.httpx, "AsyncClient", lambda **kwargs: cls(transport=httpx.MockTransport(respond)))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(papers._download_external_pdf("https://publisher.org/p.pdf"))
    assert exc.value.status_code == 422 and len(seen) == 1


def test_streaming_content_size_limit_without_length_header(monkeypatch):
    async def resolve(url): return "https://1.1.1.1/p.pdf", "publisher.org"
    monkeypatch.setattr(papers, "_resolve_public_target", resolve)
    cls = httpx.AsyncClient
    def respond(request):
        return httpx.Response(200, content=b"%PDF-" + b"x" * papers.MAX_PDF_BYTES)
    monkeypatch.setattr(papers.httpx, "AsyncClient", lambda **kwargs: cls(transport=httpx.MockTransport(respond)))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(papers._download_external_pdf("https://publisher.org/p.pdf"))
    assert exc.value.status_code == 413
