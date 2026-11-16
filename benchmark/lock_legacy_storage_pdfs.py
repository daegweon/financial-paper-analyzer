"""Hash the exact B01-B10 PDF bytes stored in PaperSignal's private Supabase bucket.

Read-only: this script only GETs paper metadata and private Storage objects.
It never writes to Supabase, prints credentials, or writes PDF bytes to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import fitz
import httpx

DEFAULT_INVENTORY = Path(__file__).with_name("legacy_regression_storage_inventory_2026-11-17.json")
EXPECTED_IDS = {f"B{i:02d}" for i in range(1, 11)}


def _validate_inventory(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    if inventory.get("record_type") != "LEGACY_REGRESSION_STORAGE_METADATA_ONLY_NOT_BINARY_LOCK":
        raise ValueError("Expected the metadata-only B01-B10 inventory")
    papers = inventory.get("papers")
    if not isinstance(papers, list) or len(papers) != 10:
        raise ValueError("Inventory must contain exactly ten regression papers")
    if {item.get("id") for item in papers if isinstance(item, dict)} != EXPECTED_IDS:
        raise ValueError("Inventory must contain each paper B01-B10 exactly once")
    if any(not isinstance(item, dict) for item in papers):
        raise ValueError("Invalid paper inventory entry")
    return sorted(papers, key=lambda item: item["id"])


def _checked_response(response: httpx.Response, *, operation: str) -> None:
    if response.status_code != 200:
        # Deliberately omit response bodies, headers and signed URLs from errors.
        raise RuntimeError(f"Supabase {operation} failed (HTTP {response.status_code})")


def lock_legacy_storage_pdfs(
    client: Any,
    *,
    supabase_url: str,
    service_role_key: str,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """Download bytes in memory, verify identity/page counts, return SHA-256 only."""
    if not isinstance(supabase_url, str) or urlparse(supabase_url).scheme != "https":
        raise ValueError("SUPABASE_URL must be an HTTPS URL")
    if not isinstance(service_role_key, str) or not service_role_key.strip():
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
    papers = _validate_inventory(inventory)
    base = supabase_url.rstrip("/")
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Accept": "application/json",
    }
    output = []

    for expected in papers:
        paper_id = expected["id"]
        filename = expected.get("original_filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"{paper_id}: invalid inventory filename")
        expected_size = expected.get("size_bytes")
        expected_pages = expected.get("pages")
        if type(expected_size) is not int or expected_size < 1:
            raise ValueError(f"{paper_id}: invalid expected file size")
        if type(expected_pages) is not int or expected_pages < 1:
            raise ValueError(f"{paper_id}: invalid expected page count")

        metadata_response = client.get(
            f"{base}/rest/v1/papers",
            headers=headers,
            params={
                "select": "original_filename,storage_path,size_bytes,page_count,content_type,status",
                "original_filename": f"eq.{filename}",
                "status": "eq.completed",
                "limit": "2",
            },
        )
        _checked_response(metadata_response, operation="paper metadata lookup")
        rows = metadata_response.json()
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError(f"{paper_id}: expected exactly one completed private paper record")
        row = rows[0]
        if row.get("original_filename") != filename or row.get("content_type") != "application/pdf":
            raise ValueError(f"{paper_id}: paper metadata does not match the inventory")
        if row.get("status") != "completed":
            raise ValueError(f"{paper_id}: paper analysis record is not completed")
        if row.get("size_bytes") != expected_size or row.get("page_count") != expected_pages:
            raise ValueError(f"{paper_id}: stored metadata differs from the locked inventory")

        storage_path = row.get("storage_path")
        if (
            not isinstance(storage_path, str)
            or storage_path.startswith("/")
            or "\\" in storage_path
            or any(part in {"", ".", ".."} for part in storage_path.split("/"))
        ):
            raise ValueError(f"{paper_id}: unsafe or missing private storage path")

        object_url = (
            f"{base}/storage/v1/object/authenticated/papers/"
            f"{quote(storage_path, safe='/')}"
        )
        file_response = client.get(object_url, headers=headers)
        _checked_response(file_response, operation="private PDF download")
        raw = file_response.content
        if not isinstance(raw, bytes) or not raw.startswith(b"%PDF-"):
            raise ValueError(f"{paper_id}: stored object is not a PDF")
        if len(raw) != expected_size:
            raise ValueError(f"{paper_id}: exact PDF byte length differs from the inventory")

        try:
            document = fitz.open(stream=raw, filetype="pdf")
        except Exception as exc:
            raise ValueError(f"{paper_id}: PyMuPDF could not open the stored PDF") from exc
        try:
            if not document.is_pdf or document.needs_pass:
                raise ValueError(f"{paper_id}: stored PDF is invalid or encrypted")
            actual_pages = document.page_count
        finally:
            document.close()
        if actual_pages != expected_pages:
            raise ValueError(f"{paper_id}: actual PDF page count differs from the inventory")

        output.append({
            "id": paper_id,
            "original_filename": filename,
            "size_bytes": len(raw),
            "page_count": actual_pages,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "sha256_algorithm": "SHA-256",
            "status": "BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT",
        })

    return {
        "record_type": "LEGACY_REGRESSION_BINARY_VERIFIED_PENDING_GIT_LOCK_COMMIT",
        "source": "Exact bytes downloaded read-only from the private Supabase papers bucket",
        "paper_count": len(output),
        "total_bytes": sum(item["size_bytes"] for item in output),
        "total_pages": sum(item["page_count"] for item in output),
        "papers": output,
        "lock_commit": None,
        "warning": (
            "Commit this manifest to the handoff branch and record that Git commit SHA in a "
            "follow-up commit before using B01-B10 as the frozen regression corpus."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash B01-B10 exact private Storage PDF bytes (read-only)")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--out", type=Path, required=True,
                        help="Private output JSON; contains SHA-256 only, never PDF bytes or storage paths")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0), follow_redirects=False) as client:
        result = lock_legacy_storage_pdfs(
            client, supabase_url=supabase_url,
            service_role_key=service_role_key, inventory=inventory,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "record_type": result["record_type"],
        "paper_count": result["paper_count"],
        "total_pages": result["total_pages"],
        "total_bytes": result["total_bytes"],
        "papers": [{"id": x["id"], "sha256": x["sha256"]} for x in result["papers"]],
        "out": str(args.out),
        "note": "No secret values, storage paths or PDF bytes were written.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
