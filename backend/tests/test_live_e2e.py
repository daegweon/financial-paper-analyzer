"""Opt-in live beta E2E test.

Requires two pre-verified disposable Supabase Auth users and a server-side
service key for deterministic cleanup. Never points at a production project
unless PAPERSIGNAL_E2E_ENABLED=1 is explicitly set.
"""
from __future__ import annotations

import os
import time
from urllib.parse import quote
from uuid import uuid4

import fitz
import httpx
import pytest

ENABLED = os.getenv("PAPERSIGNAL_E2E_ENABLED") == "1"
pytestmark = pytest.mark.skipif(
    not ENABLED,
    reason="Set PAPERSIGNAL_E2E_ENABLED=1 and provide disposable verified test accounts.",
)


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Missing opt-in E2E configuration: {name}")
    return value


def _make_pdf() -> bytes:
    document = fitz.open()
    page1 = document.new_page()
    page1.insert_text(
        (45, 90),
        "Synthetic finance research. This paper studies liquidity risk and asset pricing.",
    )
    page1.insert_text(
        (45, 120),
        "We use a panel of 12 banks from 2018 to 2023 with fixed effects.",
    )
    page2 = document.new_page()
    page2.insert_text(
        (45, 90),
        "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
    )
    data = document.tobytes()
    document.close()
    return data


def _login(client: httpx.Client, email: str, password: str, api_key: str) -> tuple[str, str]:
    response = client.post(
        "/auth/v1/token",
        params={"grant_type": "password"},
        headers={"apikey": api_key},
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    payload = response.json()
    return payload["access_token"], payload["user"]["id"]


def _user_headers(api_key: str, token: str) -> dict[str, str]:
    return {"apikey": api_key, "Authorization": "Bearer " + token}


def _admin_headers(service_key: str, publishable_key: str) -> dict[str, str]:
    if service_key.startswith("sb_secret_"):
        return {"apikey": service_key, "Content-Type": "application/json"}
    return {
        "apikey": publishable_key,
        "Authorization": "Bearer " + service_key,
        "Content-Type": "application/json",
    }


def test_live_signup_upload_analysis_and_cross_user_isolation():
    supabase_url = _required("SUPABASE_URL").rstrip("/")
    publishable_key = _required("SUPABASE_PUBLISHABLE_KEY")
    service_key = _required("SUPABASE_SERVICE_ROLE_KEY")
    api_url = _required("PAPERSIGNAL_API_URL").rstrip("/")
    user_a_email = _required("E2E_USER_A_EMAIL")
    user_a_password = _required("E2E_USER_A_PASSWORD")
    user_b_email = _required("E2E_USER_B_EMAIL")
    user_b_password = _required("E2E_USER_B_PASSWORD")

    pdf = _make_pdf()
    object_path = None
    paper_id = None
    analysis_id = None
    job_id = None
    job_terminal = False

    with httpx.Client(base_url=supabase_url, timeout=45) as supabase, httpx.Client(
        base_url=api_url, timeout=45
    ) as api:
        token_a, user_a = _login(supabase, user_a_email, user_a_password, publishable_key)
        token_b, user_b = _login(supabase, user_b_email, user_b_password, publishable_key)
        assert user_a != user_b, "E2E accounts must be distinct."

        suffix = uuid4().hex
        object_path = f"{user_a}/papersignal-e2e-{suffix}.pdf"
        paper = {
            "user_id": user_a,
            "title": "PaperSignal E2E Synthetic QA " + suffix,
            "original_filename": "papersignal-e2e.pdf",
            "storage_path": object_path,
            "content_type": "application/pdf",
            "size_bytes": len(pdf),
            "page_count": 2,
            "status": "uploaded",
        }

        try:
            upload = supabase.post(
                "/storage/v1/object/papers/" + quote(object_path, safe="/"),
                headers={
                    **_user_headers(publishable_key, token_a),
                    "Content-Type": "application/pdf",
                    "x-upsert": "false",
                },
                content=pdf,
            )
            upload.raise_for_status()

            inserted = supabase.post(
                "/rest/v1/papers",
                headers={
                    **_user_headers(publishable_key, token_a),
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=paper,
            )
            inserted.raise_for_status()
            paper_id = inserted.json()[0]["id"]

            queued = api.post(
                f"/api/analyze/{paper_id}",
                headers={"Authorization": "Bearer " + token_a},
            )
            assert queued.status_code == 202, queued.text
            job_id = queued.json()["job_id"]

            deadline = time.monotonic() + int(os.getenv("E2E_TIMEOUT_SECONDS", "900"))
            status = None
            while time.monotonic() < deadline:
                response = api.get(
                    f"/api/analyze/{paper_id}/status",
                    params={"job_id": job_id},
                    headers={"Authorization": "Bearer " + token_a},
                )
                response.raise_for_status()
                status = response.json()
                if status["status"] in {"completed", "failed"}:
                    job_terminal = True
                    break
                time.sleep(5)

            assert status is not None and status["status"] == "completed", status
            analysis_id = status["analysis_id"]
            assert analysis_id

            result_response = supabase.get(
                "/rest/v1/analyses",
                params={"id": "eq." + analysis_id, "paper_id": "eq." + paper_id, "select": "id,result,model"},
                headers=_user_headers(publishable_key, token_a),
            )
            result_response.raise_for_status()
            rows = result_response.json()
            assert len(rows) == 1
            result = rows[0]["result"]
            assert result.get("mode") in {"llm", "extractive"}
            assert result.get("analysis_version")
            assert result.get("evidence"), "Expected page-level evidence in the saved result."

            # User B must not be able to enqueue or read User A's paper or PDF.
            denied = api.post(
                f"/api/analyze/{paper_id}",
                headers={"Authorization": "Bearer " + token_b},
            )
            assert denied.status_code == 404

            hidden = supabase.get(
                "/rest/v1/papers",
                params={"id": "eq." + paper_id, "select": "id"},
                headers=_user_headers(publishable_key, token_b),
            )
            hidden.raise_for_status()
            assert hidden.json() == []

            private_pdf = supabase.get(
                "/storage/v1/object/authenticated/papers/" + quote(object_path, safe="/"),
                headers=_user_headers(publishable_key, token_b),
            )
            assert private_pdf.status_code in {400, 401, 403, 404}
        finally:
            # Clean only the uniquely named E2E fixture and rows created above.
            admin = _admin_headers(service_key, publishable_key)
            if paper_id and job_terminal:
                supabase.delete(
                    "/rest/v1/analyses",
                    params={"paper_id": "eq." + paper_id},
                    headers=admin,
                )
                supabase.delete(
                    "/rest/v1/analysis_jobs",
                    params={"paper_id": "eq." + paper_id},
                    headers=admin,
                )
                supabase.delete(
                    "/rest/v1/papers",
                    params={"id": "eq." + paper_id},
                    headers=admin,
                )
                if object_path:
                    supabase.request(
                        "DELETE",
                        "/storage/v1/object/papers",
                        headers=admin,
                        json={"prefixes": [object_path]},
                    )
            elif paper_id:
                pytest.fail(
                    "E2E job did not reach a terminal state before timeout; "
                    "the disposable fixture was retained for safe recovery."
                )                )
