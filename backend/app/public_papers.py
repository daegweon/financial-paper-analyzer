"""Authenticated public academic-paper discovery and PDF import proxy.

Security: public HTTPS only, DNS/IP pinning (SSRF and rebinding defense),
manual redirect validation, size/page limits and no privileged Storage writes.
The browser receives validated PDF bytes and reuses its existing owner-scoped
upload flow; server credentials are never used for user paper creation.
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import re
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit

import fitz
import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(prefix="/api/public-papers", tags=["public-papers"])
MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_PDF_PAGES = 300
MAX_REDIRECTS = 3
OPENALEX_URL = "https://api.openalex.org/works"
USER_AGENT = "PaperSignal-PublicResearch/1.0"
_HOST_PART = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    token = authorization.partition(" ")[2].strip()
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return token


async def _authenticated_user(token: str) -> str:
    # Lazy import avoids a cycle when main includes this router.
    from app import main
    if not main.SUPABASE_URL or not main.SUPABASE_KEY:
        raise HTTPException(status_code=503, detail="인증 서비스가 설정되지 않았습니다.")
    async with httpx.AsyncClient(timeout=15) as client:
        return await main._verify_user(client, token)


def _validate_public_https_url(url: str) -> tuple[str, str]:
    """Reject private destinations before any DNS lookup or network request."""
    if not isinstance(url, str) or not url or len(url) > 2048 or any(
        ord(char) < 33 or ord(char) == 127 for char in url
    ):
        raise HTTPException(status_code=422, detail="유효한 공개 HTTPS PDF 주소를 입력해 주세요.")
    try:
        parsed = urlsplit(url)
        port = parsed.port
        raw_host = parsed.hostname or ""
        host = raw_host.encode("idna").decode("ascii").lower().rstrip(".")
    except (ValueError, UnicodeError):
        raise HTTPException(status_code=422, detail="PDF 주소 형식이 올바르지 않습니다.")
    if (
        parsed.scheme.lower() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or len(host) > 253
        or "." not in host
        or host.endswith((".local", ".internal", ".localhost", ".test", ".invalid"))
        or not all(_HOST_PART.fullmatch(part) for part in host.split("."))
    ):
        raise HTTPException(status_code=422, detail="공개 HTTPS 주소(443 포트)만 가져올 수 있습니다.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise HTTPException(status_code=422, detail="IP 주소로 직접 연결할 수 없습니다.")
    # Keep the original URL for redirect resolution; never forward fragments.
    normalized = urlunsplit(("https", host, parsed.path or "/", parsed.query, ""))
    return normalized, host


async def _resolve_public_target(url: str) -> tuple[str, str]:
    """Pin the actual connection to validated public DNS addresses.

    Merely checking DNS then resolving it again in an HTTP client is unsafe:
    an attacker can return a public address first and an internal one later.
    We connect to the vetted IP and set SNI/Host to the original hostname.
    """
    normalized, host = _validate_public_https_url(url)
    try:
        records = await asyncio.wait_for(
            asyncio.to_thread(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM),
            timeout=5.0,
        )
    except (OSError, TimeoutError):
        raise HTTPException(status_code=422, detail="공개 PDF 서버의 주소를 확인할 수 없습니다.")
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise HTTPException(status_code=422, detail="공개 PDF 서버의 주소를 확인할 수 없습니다.")
    for address in addresses:
        candidate = ipaddress.ip_address(address)
        if (
            not candidate.is_global
            or candidate.is_multicast
            or candidate.is_reserved
            or candidate.is_unspecified
        ):
            raise HTTPException(status_code=422, detail="내부망·사설망 주소는 가져올 수 없습니다.")
    address = ipaddress.ip_address(addresses[0])
    ip_host = f"[{address}]" if address.version == 6 else str(address)
    parsed = urlsplit(normalized)
    return urlunsplit(("https", ip_host, parsed.path, parsed.query, "")), host


def _validate_pdf(data: bytes) -> None:
    if len(data) < 5 or not data.startswith(b"%PDF-") or len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=422, detail="30MB 이하의 PDF 원본 파일만 가져올 수 있습니다.")
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.needs_pass or not 1 <= len(document) <= MAX_PDF_PAGES:
                raise HTTPException(status_code=422, detail="암호화된 PDF 또는 300페이지 초과 문서는 지원하지 않습니다.")
    except HTTPException:
        raise
    except (fitz.FileDataError, ValueError, RuntimeError):
        raise HTTPException(status_code=422, detail="PDF 파일을 열 수 없습니다.")


async def _download_external_pdf(url: str) -> bytes:
    current, _ = _validate_public_https_url(url)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0, connect=8.0),
        follow_redirects=False,
        trust_env=False,
    ) as client:
        for hop in range(MAX_REDIRECTS + 1):
            pinned_url, hostname = await _resolve_public_target(current)
            request = client.build_request(
                "GET",
                pinned_url,
                headers={"Host": hostname, "Accept": "application/pdf", "User-Agent": USER_AGENT},
                extensions={"sni_hostname": hostname},
            )
            try:
                response = await client.send(request, stream=True)
            except (httpx.RequestError, OSError, TimeoutError):
                raise HTTPException(status_code=502, detail="외부 PDF 서버에 연결하지 못했습니다.")
            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location", "")
                    if not location or hop == MAX_REDIRECTS:
                        raise HTTPException(status_code=422, detail="PDF 주소의 리디렉션이 너무 많습니다.")
                    current, _ = _validate_public_https_url(urljoin(current, location))
                    continue
                if response.status_code != 200:
                    raise HTTPException(status_code=502, detail="공개 PDF 원문을 다운로드하지 못했습니다.")
                size = response.headers.get("content-length", "")
                if size.isdigit() and int(size) > MAX_PDF_BYTES:
                    raise HTTPException(status_code=413, detail="30MB를 초과하는 PDF는 가져올 수 없습니다.")
                content = bytearray()
                try:
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_PDF_BYTES:
                            raise HTTPException(status_code=413, detail="30MB를 초과하는 PDF는 가져올 수 없습니다.")
                except httpx.RequestError:
                    raise HTTPException(status_code=502, detail="PDF 다운로드 중 연결이 끊어졌습니다.")
                result = bytes(content)
                _validate_pdf(result)
                return result
            finally:
                await response.aclose()
    raise HTTPException(status_code=502, detail="PDF 다운로드에 실패했습니다.")


def _paper_search_item(work: dict) -> dict:
    best = work.get("best_oa_location")
    primary = work.get("primary_location")
    location = best if isinstance(best, dict) and best.get("is_oa") else None
    if not location and isinstance(primary, dict) and primary.get("is_oa"):
        location = primary
    pdf_url = (location or {}).get("pdf_url")
    if not isinstance(pdf_url, str) or not pdf_url.startswith("https://"):
        pdf_url = None
    authors = []
    for authorship in (work.get("authorships") or [])[:4]:
        author = authorship.get("author") if isinstance(authorship, dict) else None
        if isinstance(author, dict) and author.get("display_name"):
            authors.append(str(author["display_name"])[:100])
    oa = work.get("open_access") or {}
    return {
        "id": str(work.get("id") or "")[:150],
        "title": str(work.get("title") or work.get("display_name") or "제목 없음")[:500],
        "year": work.get("publication_year") if isinstance(work.get("publication_year"), int) else None,
        "doi": str(work.get("doi") or "")[:250],
        "authors": authors,
        "pdf_url": pdf_url,
        "landing_url": str((location or {}).get("landing_page_url") or work.get("doi") or work.get("id") or "")[:2048],
        "license": str((location or {}).get("license") or "미확인")[:80],
        "is_open_access": bool(oa.get("is_oa")),
    }


@router.get("/search")
async def search_papers(
    query: str = Query(min_length=2, max_length=200),
    page: int = Query(default=1, ge=1, le=10),
    authorization: str | None = Header(default=None),
) -> dict:
    token = _bearer_token(authorization)
    await _authenticated_user(token)
    term = query.strip()
    if len(term) < 2:
        raise HTTPException(status_code=422, detail="검색어를 두 글자 이상 입력해 주세요.")
    params = {
        "search": term,
        "filter": "is_oa:true",
        "page": page,
        "per_page": 10,
        "select": "id,title,publication_year,doi,authorships,best_oa_location,primary_location,open_access",
    }
    key = os.getenv("OPENALEX_API_KEY", "").strip()
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if key:
        headers["Authorization"] = "Bearer " + key
    try:
        async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
            response = await client.get(OPENALEX_URL, params=params, headers=headers)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="공개 논문 검색 서비스를 연결할 수 없습니다.")
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="공개 논문 검색 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="공개 논문 검색 서비스 요청이 실패했습니다.")
    try:
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("invalid OpenAlex response")
        items = [_paper_search_item(work) for work in payload["results"] if isinstance(work, dict)][:10]
        count = (payload.get("meta") or {}).get("count", 0)
        total = max(0, count) if isinstance(count, int) and not isinstance(count, bool) else 0
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=502, detail="공개 논문 검색 결과를 해석할 수 없습니다.")
    return {
        "source": "OpenAlex",
        "query": term,
        "page": page,
        "total": total,
        "has_more": page < 10 and page * 10 < total,
        "results": items,
    }


@router.post("/download")
async def download_paper(
    payload: dict,
    authorization: str | None = Header(default=None),
) -> Response:
    token = _bearer_token(authorization)
    await _authenticated_user(token)
    url = payload.get("url")
    if not isinstance(url, str):
        raise HTTPException(status_code=422, detail="PDF URL을 입력해 주세요.")
    data = await _download_external_pdf(url.strip())
    # Never cache the PDF or expose it in a public bucket: browser reuses its
    # existing authenticated private Storage upload and paper-metadata path.
    return Response(content=data, media_type="application/pdf", headers={"Cache-Control": "no-store"})
