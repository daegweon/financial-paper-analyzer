"""Synthetic tests for the read-only private Supabase regression PDF locker."""
import hashlib
import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.lock_legacy_storage_pdfs import lock_legacy_storage_pdfs


def make_pdf(pages: int, title: str) -> bytes:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{title} page {index + 1}")
    raw = doc.tobytes()
    doc.close()
    return raw


def inventory():
    return {
        "record_type": "LEGACY_REGRESSION_STORAGE_METADATA_ONLY_NOT_BINARY_LOCK",
        "papers": [
            {"id": f"B{i:02d}", "original_filename": f"B{i:02d}_paper.pdf",
             "size_bytes": len(make_pdf(i, f"B{i:02d}")), "pages": i,
             "storage_etag": "opaque-not-used", "sha256": None}
            for i in range(1, 11)
        ],
    }


class Response:
    def __init__(self, status_code=200, content=b"", payload=None):
        self.status_code = status_code
        self.content = content
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, rows, blobs):
        self.rows = rows
        self.blobs = blobs
        self.calls = []

    def get(self, url, *, headers, params=None):
        self.calls.append((url, headers, params))
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["apikey"] == headers["Authorization"].removeprefix("Bearer ")
        if "/rest/v1/papers" in url:
            filename = params["original_filename"].removeprefix("eq.")
            return Response(payload=self.rows.get(filename, []))
        path = url.rsplit("/", 1)[-1]
        return Response(content=self.blobs.get(path, b""))


def make_fixture():
    rows, blobs = {}, {}
    for item in inventory()["papers"]:
        raw = make_pdf(item["pages"], item["id"])
        path = f"synthetic/{item['id']}.pdf"
        rows[item["original_filename"]] = [{
            "original_filename": item["original_filename"],
            "storage_path": path,
            "size_bytes": len(raw),
            "page_count": item["pages"],
            "content_type": "application/pdf",
            "status": "completed",
        }]
        blobs[item["id"] + ".pdf"] = raw
    return rows, blobs


def test_locks_exact_private_pdf_bytes_without_emitting_paths_or_secrets():
    inv = inventory()
    rows, blobs = make_fixture()
    client = FakeClient(rows, blobs)
    result = lock_legacy_storage_pdfs(
        client, supabase_url="https://example.supabase.co",
        service_role_key="synthetic-service-role-secret", inventory=inv,
    )
    assert result["record_type"] == "LEGACY_REGRESSION_BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT"
    assert result["paper_count"] == 10
    assert result["total_pages"] == sum(range(1, 11))
    for item in result["papers"]:
        raw = blobs[item["id"] + ".pdf"]
        assert item["sha256"] == hashlib.sha256(raw).hexdigest()
        assert item["page_count"] >= 1
        assert item["status"] == "BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT"
    encoded = str(result)
    assert "synthetic-service-role-secret" not in encoded
    assert "storage_path" not in encoded
    assert "synthetic/" not in encoded


def test_missing_or_duplicate_metadata_fails_closed():
    rows, blobs = make_fixture()
    rows["B01_paper.pdf"] = []
    with pytest.raises(ValueError, match="exactly one"):
        lock_legacy_storage_pdfs(FakeClient(rows, blobs),
            supabase_url="https://example.supabase.co", service_role_key="secret", inventory=inventory())
    rows, blobs = make_fixture()
    rows["B01_paper.pdf"].append(rows["B01_paper.pdf"][0])
    with pytest.raises(ValueError, match="exactly one"):
        lock_legacy_storage_pdfs(FakeClient(rows, blobs),
            supabase_url="https://example.supabase.co", service_role_key="secret", inventory=inventory())


def test_metadata_size_page_and_pdf_header_mismatches_fail_closed():
    rows, blobs = make_fixture()
    rows["B01_paper.pdf"][0]["size_bytes"] += 1
    with pytest.raises(ValueError, match="metadata differs"):
        lock_legacy_storage_pdfs(FakeClient(rows, blobs),
            supabase_url="https://example.supabase.co", service_role_key="secret", inventory=inventory())

    rows, blobs = make_fixture()
    blobs["B01.pdf"] = b"not-a-pdf"
    with pytest.raises(ValueError, match="not a PDF"):
        lock_legacy_storage_pdfs(FakeClient(rows, blobs),
            supabase_url="https://example.supabase.co", service_role_key="secret", inventory=inventory())


def test_missing_key_and_non_https_endpoint_are_rejected():
    rows, blobs = make_fixture()
    client = FakeClient(rows, blobs)
    with pytest.raises(ValueError, match="HTTPS"):
        lock_legacy_storage_pdfs(client, supabase_url="http://example.supabase.co",
                                 service_role_key="secret", inventory=inventory())
    with pytest.raises(ValueError, match="SERVICE_ROLE_KEY"):
        lock_legacy_storage_pdfs(client, supabase_url="https://example.supabase.co",
                                 service_role_key="", inventory=inventory())
