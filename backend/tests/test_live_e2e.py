"""Opt-in live beta E2E test.

Creates two short-lived, email-confirmed QA-only Supabase Auth users through
the Admin API, exercises the real API/Worker flow, and removes only resources
created by this test. It never disables email confirmation or uses customer
accounts. Enable explicitly with PAPERSIGNAL_E2E_ENABLED=1.
"""
from __future__ import annotations

import os
import secrets
import time
from urllib.parse import parse_qs, quote, urlsplit
from uuid import UUID, uuid4

import fitz
import httpx
import pytest

ENABLED = os.getenv("PAPERSIGNAL_E2E_ENABLED") == "1"


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        # An explicitly started live E2E must fail, not silently pass as skipped.
        pytest.fail(f"Required live E2E configuration missing: {name}")
    return value


LIVE_SUPABASE_ORIGIN = "https://hwmtayrecsfxernhssro.supabase.co"
LIVE_API_ORIGIN = "https://papersignal-api-production.up.railway.app"
LIVE_E2E_ACKNOWLEDGMENT = "RUN_SYNTHETIC_LIVE_E2E"


def _validate_live_e2e_target(
    supabase_url: str, api_url: str, acknowledgment: str
) -> None:
    """Reject unreviewed targets before any user or PDF can be created."""
    if acknowledgment != LIVE_E2E_ACKNOWLEDGMENT:
        raise RuntimeError("Live E2E requires explicit synthetic-test approval.")
    if supabase_url != LIVE_SUPABASE_ORIGIN or api_url != LIVE_API_ORIGIN:
        raise RuntimeError(
            "Live E2E target is not the reviewed Supabase/Railway project. "
            "No users or files have been created."
        )


def _assert_server_ready_for_live_e2e(api: httpx.Client) -> None:
    """Fail before creating disposable accounts unless the new API is live."""
    try:
        response = api.get("/health")
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise RuntimeError("Live API health preflight failed.") from error
    if not isinstance(body, dict) or body.get("queue_write_mode") != "service_role":
        raise RuntimeError(
            "Live API has not confirmed the server-owned analysis queue release. "
            "Do not create live E2E users or apply the database grants migration."
        )
    if body.get("analysis_mode") != "ai" or body.get("ai_provider") != "gemini":
        raise RuntimeError(
            "Live API is not configured for Gemini-backed AI analysis. "
            "No QA users or PDFs have been created."
        )


def _assert_gemini_analysis_result(result: object) -> None:
    """Reject extractive fallbacks or other providers as a false Gemini pass."""
    models_used = result.get("models_used") if isinstance(result, dict) else None
    if (
        not isinstance(result, dict)
        or result.get("mode") != "llm"
        or result.get("provider") != "gemini"
        or not isinstance(models_used, list)
        or not any(
            isinstance(model, str) and model.startswith("gemini-")
            for model in models_used
        )
    ):
        raise AssertionError(
            "Live E2E expected a successful Gemini LLM analysis with model metadata."
        )


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


def _admin_headers(service_key: str, publishable_key: str) -> dict[str, str]:
    if service_key.startswith("sb_secret_"):
        return {"apikey": service_key, "Content-Type": "application/json"}
    return {
        "apikey": publishable_key,
        "Authorization": "Bearer " + service_key,
        "Content-Type": "application/json",
    }


def _user_headers(api_key: str, token: str) -> dict[str, str]:
    return {"apikey": api_key, "Authorization": "Bearer " + token}


def _create_user(
    client: httpx.Client,
    email: str,
    password: str,
    admin_headers: dict[str, str],
) -> str:
    response = client.post(
        "/auth/v1/admin/users",
        headers=admin_headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"papersignal_e2e": True},
        },
    )
    response.raise_for_status()
    return response.json()["id"]


def _login(
    client: httpx.Client, email: str, password: str, api_key: str
) -> tuple[str, str]:
    response = client.post(
        "/auth/v1/token",
        params={"grant_type": "password"},
        headers={"apikey": api_key},
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    payload = response.json()
    return payload["access_token"], payload["user"]["id"]


def _delete_user(
    client: httpx.Client, user_id: str, admin_headers: dict[str, str]
) -> None:
    response = client.delete(
        "/auth/v1/admin/users/" + quote(user_id, safe=""),
        headers=admin_headers,
    )
    if response.status_code not in {200, 204, 404}:
        response.raise_for_status()


def _remove_storage_object(
    client: httpx.Client, object_path: str, admin_headers: dict[str, str]
) -> None:
    # The Supabase Storage batch-delete endpoint requires DELETE, not POST.
    # Delete through the Storage API so the underlying PDF is removed too.
    response = client.request(
        "DELETE",
        "/storage/v1/object/papers",
        headers=admin_headers,
        json={"prefixes": [object_path]},
    )
    if response.status_code not in {200, 204, 404}:
        response.raise_for_status()


def _cleanup_disposable_e2e(
    client: httpx.Client,
    admin_headers: dict[str, str],
    *,
    user_a: str | None,
    user_b: str | None,
    object_path: str | None,
    paper_id: str | None,
    job_id: str | None,
    job_terminal: bool,
) -> None:
    """Clean up ONLY generated fixtures, never a customer's record.

    Attempt all applicable table and Storage cleanup even if one fails. If any
    deletion fails, retain the QA Auth users for an auditable manual recovery.
    """
    if job_id and not job_terminal:
        raise RuntimeError(
            "E2E job is nonterminal; disposable fixture and users retained "
            "to avoid racing a live worker."
        )

    def check_uuid(value: str, label: str) -> None:
        try:
            if str(UUID(value)) != value.lower():
                raise ValueError("Noncanonical UUID")
        except (ValueError, TypeError, AttributeError):
            raise RuntimeError("Refusing cleanup: invalid " + label) from None

    if user_a:
        check_uuid(user_a, "QA owner ID")
    if user_b:
        check_uuid(user_b, "QA second user ID")
    if user_a and user_b and user_a == user_b:
        raise RuntimeError("Refusing cleanup: QA users must be distinct.")
    if paper_id:
        check_uuid(paper_id, "QA paper ID")
        if not user_a:
            raise RuntimeError("Refusing cleanup: paper has no QA owner.")
    if object_path:
        if not user_a or not object_path.startswith(user_a + "/papersignal-e2e-"):
            raise RuntimeError("Refusing cleanup: PDF does not belong to the QA owner.")
        filename = object_path[len(user_a) + 1:]
        if (not filename.endswith(".pdf")
                or len(filename) != len("papersignal-e2e-") + 32 + 4
                or any(ch not in "0123456789abcdef" for ch in filename[16:-4])):
            raise RuntimeError("Refusing cleanup: PDF has an unexpected QA-only filename.")

    failed: list[str] = []
    if paper_id:
        for table in ("analyses", "analysis_jobs", "papers"):
            params = {"user_id": "eq." + user_a}
            params["paper_id" if table != "papers" else "id"] = "eq." + paper_id
            try:
                response = client.delete(
                    "/rest/v1/" + table, params=params, headers=admin_headers
                )
                response.raise_for_status()
            except (httpx.HTTPError, ValueError):
                failed.append(table + " rows")
    if object_path:
        try:
            _remove_storage_object(client, object_path, admin_headers)
        except (httpx.HTTPError, ValueError):
            failed.append("Storage PDF")

    if failed:
        raise RuntimeError(
            "QA cleanup requires manual recovery: " + ", ".join(failed)
            + "; temporary Auth users were retained."
        )

    users_failed: list[str] = []
    for label, user_id in (("B", user_b), ("A", user_a)):
        if not user_id:
            continue
        try:
            _delete_user(client, user_id, admin_headers)
        except (httpx.HTTPError, ValueError):
            users_failed.append("user " + label)
    if users_failed:
        raise RuntimeError(
            "QA cleanup requires manual recovery: " + ", ".join(users_failed)
        )


def _check_private_pdf_http(
    client: httpx.Client,
    object_path: str,
    source_pdf: bytes,
    key: str,
    owner_token: str,
    other_token: str,
) -> None:
    """Verify actual owner PDF bytes and owner-only signed-link issuance.

    Signed links are bearer capabilities and can be shared by their holder;
    the isolation check is that non-owners cannot generate one.
    """
    path = quote(object_path, safe="/")
    private = "/storage/v1/object/authenticated/papers/" + path
    sign = "/storage/v1/object/sign/papers/" + path
    owner = _user_headers(key, owner_token)
    other = _user_headers(key, other_token)

    owned = client.get(private, headers=owner)
    assert owned.status_code == 200 and owned.content == source_pdf, (
        "The source PDF was not readable by its owner."
    )
    denied = client.get(private, headers=other)
    assert denied.status_code in {400, 401, 403, 404}, (
        "A non-owner unexpectedly accessed the private source PDF."
    )

    signed = client.post(sign, headers=owner, json={"expiresIn": 60})
    assert signed.status_code == 200, "The owner cannot sign their source PDF."
    try:
        signed_url = signed.json()["signedURL"]
    except (ValueError, KeyError, TypeError):
        raise AssertionError("The signed source response was invalid.") from None
    if not isinstance(signed_url, str):
        raise AssertionError("The signed PDF URL must be a relative path.")
    parts = urlsplit(signed_url)
    if (parts.scheme or parts.netloc or parts.fragment
            or parts.path != "/object/sign/papers/" + path
            or not parse_qs(parts.query).get("token")):
        raise AssertionError("The signed PDF URL has an unexpected path.")
    # Keep the request pinned to this Supabase origin; never log a signing token.
    signed_file = client.get("/storage/v1" + signed_url)
    assert signed_file.status_code == 200 and signed_file.content == source_pdf, (
        "The signed PDF URL did not return the original document."
    )

    denied_sign = client.post(sign, headers=other, json={"expiresIn": 60})
    assert denied_sign.status_code in {400, 401, 403, 404}, (
        "A non-owner unexpectedly obtained an owner-private signing URL."
    )


def _response(status_code: int, payload: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://supabase.test"),
    )



def test_live_e2e_target_requires_explicit_acknowledgment():
    with pytest.raises(RuntimeError, match="explicit synthetic-test approval"):
        _validate_live_e2e_target(
            LIVE_SUPABASE_ORIGIN, LIVE_API_ORIGIN, ""
        )
    _validate_live_e2e_target(
        LIVE_SUPABASE_ORIGIN, LIVE_API_ORIGIN, LIVE_E2E_ACKNOWLEDGMENT
    )


@pytest.mark.parametrize(
    "supabase_url,api_url",
    [
        ("http://hwmtayrecsfxernhssro.supabase.co", LIVE_API_ORIGIN),
        (LIVE_SUPABASE_ORIGIN + ".example.org", LIVE_API_ORIGIN),
        (LIVE_SUPABASE_ORIGIN, LIVE_API_ORIGIN + "/api"),
        (LIVE_SUPABASE_ORIGIN, "https://evil.railway.app"),
        ("https://staging.supabase.co", LIVE_API_ORIGIN),
    ],
)
def test_live_e2e_refuses_unauthorized_targets(supabase_url, api_url):
    with pytest.raises(RuntimeError, match="not the reviewed"):
        _validate_live_e2e_target(
            supabase_url, api_url, LIVE_E2E_ACKNOWLEDGMENT
        )


def test_live_e2e_health_requires_server_owned_queue_and_gemini():
    class FakeClient:
        def __init__(self, payload, status=200):
            self.payload = payload
            self.status = status

        def get(self, path):
            assert path == "/health"
            return httpx.Response(
                self.status, json=self.payload,
                request=httpx.Request("GET", LIVE_API_ORIGIN + path),
            )

    ready = {
        "status": "ok",
        "queue_write_mode": "service_role",
        "analysis_mode": "ai",
        "ai_provider": "gemini",
    }
    _assert_server_ready_for_live_e2e(FakeClient(ready))
    with pytest.raises(RuntimeError, match="has not confirmed"):
        _assert_server_ready_for_live_e2e(FakeClient({"status": "ok"}))
    with pytest.raises(RuntimeError, match="not configured for Gemini"):
        _assert_server_ready_for_live_e2e(
            FakeClient({**ready, "analysis_mode": "extractive"})
        )
    with pytest.raises(RuntimeError, match="not configured for Gemini"):
        _assert_server_ready_for_live_e2e(
            FakeClient({**ready, "ai_provider": "openai"})
        )
    with pytest.raises(RuntimeError, match="health preflight failed"):
        _assert_server_ready_for_live_e2e(FakeClient({"detail": "Unavailable"}, 503))


def test_live_e2e_requires_verified_gemini_result():
    _assert_gemini_analysis_result({
        "mode": "llm",
        "provider": "gemini",
        "models_used": ["gemini-3.5-flash-lite"],
    })
    with pytest.raises(AssertionError, match="successful Gemini LLM"):
        _assert_gemini_analysis_result({
            "mode": "extractive",
            "provider": "extractive",
            "models_used": [],
        })
    with pytest.raises(AssertionError, match="successful Gemini LLM"):
        _assert_gemini_analysis_result({
            "mode": "llm",
            "provider": "openai",
            "models_used": ["gpt-5.6-terra"],
        })
    with pytest.raises(AssertionError, match="successful Gemini LLM"):
        _assert_gemini_analysis_result({
            "mode": "llm",
            "provider": "gemini",
            "models_used": [],
        })


def test_missing_explicit_live_e2e_configuration_fails_instead_of_skipping(monkeypatch):
    monkeypatch.delenv("PAPERSIGNAL_QA_MISSING", raising=False)
    with pytest.raises(BaseException) as error:
        _required("PAPERSIGNAL_QA_MISSING")
    assert "Required live E2E configuration missing" in str(error.value)


def test_admin_headers_keep_secret_key_out_of_bearer_header():
    headers = _admin_headers("sb_secret_test", "sb_publishable_test")
    assert headers["apikey"] == "sb_secret_test"
    assert "Authorization" not in headers


def test_admin_headers_support_legacy_service_role_jwt():
    headers = _admin_headers("legacy-service-role-jwt", "legacy-publishable-key")
    assert headers["apikey"] == "legacy-publishable-key"
    assert headers["Authorization"] == "Bearer legacy-service-role-jwt"


def test_create_user_marks_only_disposable_qa_user_as_confirmed():
    class FakeClient:
        def __init__(self):
            self.call = None

        def post(self, path, **kwargs):
            self.call = (path, kwargs)
            return _response(200, {"id": "11111111-1111-4111-8111-111111111111"})

    client = FakeClient()
    user_id = _create_user(
        client,
        "papersignal-e2e@example.com",
        "one-time-password",
        {"apikey": "sb_secret_test"},
    )
    path, kwargs = client.call
    assert path == "/auth/v1/admin/users"
    assert kwargs["json"]["email_confirm"] is True
    assert kwargs["json"]["user_metadata"]["papersignal_e2e"] is True
    assert user_id == "11111111-1111-4111-8111-111111111111"


def test_delete_user_targets_only_requested_auth_user():
    class FakeClient:
        def __init__(self):
            self.call = None

        def delete(self, path, **kwargs):
            self.call = (path, kwargs)
            return _response(204)

    client = FakeClient()
    _delete_user(
        client,
        "11111111-1111-4111-8111-111111111111",
        {"apikey": "sb_secret_test"},
    )
    assert client.call[0] == "/auth/v1/admin/users/11111111-1111-4111-8111-111111111111"


def test_remove_storage_object_uses_supabase_storage_delete_api():
    seen = []

    def mock_transport(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.method == "DELETE"
        assert request.url.path == "/storage/v1/object/papers"
        assert request.headers["apikey"] == "sb_secret_test"
        assert request.read()
        import json
        assert json.loads(request.content)["prefixes"] == [
            "11111111-1111-4111-8111-111111111111/test.pdf"
        ]
        return httpx.Response(200, json=[])

    with httpx.Client(
        transport=httpx.MockTransport(mock_transport), base_url=LIVE_SUPABASE_ORIGIN,
    ) as client:
        _remove_storage_object(
            client,
            "11111111-1111-4111-8111-111111111111/test.pdf",
            {"apikey": "sb_secret_test"},
        )
    assert len(seen) == 1


def test_remove_storage_object_rejects_failed_cleanup():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(405, json={"message": "not allowed"})
        ),
        base_url=LIVE_SUPABASE_ORIGIN,
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            _remove_storage_object(client, "synthetic/test.pdf", {"apikey": "test"})


def test_private_pdf_acl_and_signed_bytes_with_mock_storage():
    original = _make_pdf()
    object_path = "11111111-1111-4111-8111-111111111111/synthetic.pdf"
    visited: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        visited.append((request.method, request.url.path))
        assert request.url.host == "hwmtayrecsfxernhssro.supabase.co"
        is_owner = request.headers.get("authorization") == "Bearer qa-owner"
        if request.url.path.startswith("/storage/v1/object/authenticated/papers/"):
            return httpx.Response(200, content=original) if is_owner else httpx.Response(403)
        if request.method == "POST" and request.url.path.startswith(
            "/storage/v1/object/sign/papers/"
        ):
            if not is_owner:
                return httpx.Response(403)
            assert request.read() == b'{"expiresIn":60}'
            return httpx.Response(200, json={
                "signedURL": "/object/sign/papers/" + object_path + "?token=fixture"
            })
        if request.method == "GET" and request.url.path.startswith(
            "/storage/v1/object/sign/papers/"
        ):
            return httpx.Response(200, content=original)
        raise AssertionError("Unexpected Storage mock request")

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(handler)
    ) as client:
        _check_private_pdf_http(
            client, object_path, original, "publishable-fixture",
            "qa-owner", "qa-other"
        )
    assert [method for method, _ in visited] == ["GET", "GET", "POST", "GET", "POST"]


def test_private_pdf_rejects_other_user_signed_link():
    original = _make_pdf()
    object_path = "11111111-1111-4111-8111-111111111111/synthetic.pdf"

    def handler(request: httpx.Request) -> httpx.Response:
        is_owner = request.headers.get("authorization") == "Bearer qa-owner"
        if "/object/authenticated/papers/" in request.url.path:
            return httpx.Response(200, content=original) if is_owner else httpx.Response(403)
        if request.method == "POST":
            return httpx.Response(200, json={
                "signedURL": "/object/sign/papers/" + object_path + "?token=fixture"
            })
        return httpx.Response(200, content=original)

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(AssertionError, match="non-owner unexpectedly obtained"):
            _check_private_pdf_http(
                client, object_path, original, "fixture", "qa-owner", "qa-other"
            )


def test_private_pdf_rejects_unexpected_signed_link_path():
    original = _make_pdf()
    object_path = "11111111-1111-4111-8111-111111111111/synthetic.pdf"
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.method == "GET":
            return httpx.Response(200, content=original) if len(seen) == 1 else httpx.Response(403)
        return httpx.Response(200, json={
            "signedURL": "/object/sign/papers/other-user/unrelated.pdf?token=fixture"
        })

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(AssertionError, match="unexpected path"):
            _check_private_pdf_http(
                client, object_path, original, "fixture", "qa-owner", "qa-other"
            )
    assert len(seen) == 3


@pytest.mark.parametrize("fail_resource", [None, "analysis_jobs", "storage"])
def test_cleanup_deletes_only_owned_fixture_and_preserves_users_on_failure(fail_resource):
    owner = "11111111-1111-4111-8111-111111111111"
    second = "22222222-2222-4222-8222-222222222222"
    paper = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    path = owner + "/papersignal-e2e-" + "a" * 32 + ".pdf"
    calls = []

    def transport(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        assert req.method == "DELETE"
        if req.url.path.startswith("/rest/v1/"):
            assert req.url.params.get("user_id") == "eq." + owner
            assert req.url.params.get(
                "id" if req.url.path.endswith("/papers") else "paper_id"
            ) == "eq." + paper
        if req.url.path == "/storage/v1/object/papers":
            import json
            assert json.loads(req.content) == {"prefixes": [path]}
        if fail_resource == "storage" and req.url.path == "/storage/v1/object/papers":
            return httpx.Response(503)
        if fail_resource == "analysis_jobs" and req.url.path.endswith("/analysis_jobs"):
            return httpx.Response(503)
        return httpx.Response(204)

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(transport)
    ) as client:
        kwargs = {
            "user_a": owner, "user_b": second,
            "paper_id": paper, "object_path": path,
            "job_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "job_terminal": True,
        }
        if fail_resource:
            with pytest.raises(RuntimeError, match="manual recovery"):
                _cleanup_disposable_e2e(client, {"apikey": "fixture"}, **kwargs)
        else:
            _cleanup_disposable_e2e(client, {"apikey": "fixture"}, **kwargs)

    paths = [r.url.path for r in calls]
    assert paths[:4] == [
        "/rest/v1/analyses", "/rest/v1/analysis_jobs",
        "/rest/v1/papers", "/storage/v1/object/papers",
    ]
    expected_users = [
        "/auth/v1/admin/users/" + second,
        "/auth/v1/admin/users/" + owner,
    ]
    if fail_resource:
        assert paths == paths[:4], "Any table or Storage error must retain QA users"
    else:
        assert paths[4:] == expected_users
    assert len(calls) == (4 if fail_resource else 6)


def test_cleanup_nonterminal_job_preserves_all_temporary_resources():
    def transport(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Nonterminal cleanup must not make a network request.")

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(transport)
    ) as client:
        with pytest.raises(RuntimeError, match="nonterminal"):
            _cleanup_disposable_e2e(
                client, {"apikey": "fixture"},
                user_a="11111111-1111-4111-8111-111111111111", user_b=None,
                object_path=None, paper_id=None,
                job_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                job_terminal=False,
            )


@pytest.mark.parametrize("bad_path", [
    "other-owner/papersignal-e2e-" + "a" * 32 + ".pdf",
    "11111111-1111-4111-8111-111111111111/customer.pdf",
    "11111111-1111-4111-8111-111111111111/papersignal-e2e-" + "g" * 32 + ".pdf",
    "11111111-1111-4111-8111-111111111111/papersignal-e2e-" + "a" * 32 + ".pdf/extra",
])
def test_cleanup_refuses_unrelated_or_invalid_storage_path(bad_path):
    def transport(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Unrelated Storage paths must never be mutated.")

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(transport)
    ) as client:
        with pytest.raises(RuntimeError, match="Refusing cleanup"):
            _cleanup_disposable_e2e(
                client, {"apikey": "fixture"},
                user_a="11111111-1111-4111-8111-111111111111", user_b=None,
                object_path=bad_path, paper_id=None,
                job_id=None, job_terminal=False,
            )


def test_cleanup_partial_auth_creation_deletes_only_created_user():
    owner = "11111111-1111-4111-8111-111111111111"
    requests = []

    def transport(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return httpx.Response(204)

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(transport)
    ) as client:
        _cleanup_disposable_e2e(
            client, {"apikey": "fixture"},
            user_a=owner, user_b=None, object_path=None, paper_id=None,
            job_id=None, job_terminal=False,
        )
    assert requests == ["/auth/v1/admin/users/" + owner]


def test_cleanup_auth_delete_failure_still_attempts_other_qa_user():
    owner = "11111111-1111-4111-8111-111111111111"
    second = "22222222-2222-4222-8222-222222222222"
    visited = []

    def transport(request: httpx.Request) -> httpx.Response:
        visited.append(request.url.path)
        return httpx.Response(503 if request.url.path.endswith(second) else 204)

    with httpx.Client(
        base_url=LIVE_SUPABASE_ORIGIN, transport=httpx.MockTransport(transport)
    ) as client:
        with pytest.raises(RuntimeError, match="user B"):
            _cleanup_disposable_e2e(
                client, {"apikey": "fixture"},
                user_a=owner, user_b=second, object_path=None, paper_id=None,
                job_id=None, job_terminal=False,
            )
    assert visited == [
        "/auth/v1/admin/users/" + second,
        "/auth/v1/admin/users/" + owner,
    ]


@pytest.mark.skipif(
    not ENABLED,
    reason="Set PAPERSIGNAL_E2E_ENABLED=1 to run the disposable-user live E2E test.",
)
def test_live_auth_upload_analysis_and_cross_user_isolation():
    supabase_url = _required("SUPABASE_URL").rstrip("/")
    publishable_key = _required("SUPABASE_PUBLISHABLE_KEY")
    service_key = _required("SUPABASE_SERVICE_ROLE_KEY")
    api_url = _required("PAPERSIGNAL_API_URL").rstrip("/")
    timeout_seconds = int(os.getenv("E2E_TIMEOUT_SECONDS", "900"))
    _validate_live_e2e_target(
        supabase_url, api_url, os.getenv("PAPERSIGNAL_E2E_APPROVED", "")
    )

    pdf = _make_pdf()
    admin = _admin_headers(service_key, publishable_key)
    suffix = uuid4().hex
    user_a_email = f"papersignal-e2e-a-{suffix}@example.com"
    user_b_email = f"papersignal-e2e-b-{suffix}@example.com"
    user_a_password = secrets.token_urlsafe(32)
    user_b_password = secrets.token_urlsafe(32)

    user_a = None
    user_b = None
    object_path = None
    paper_id = None
    job_id = None
    job_terminal = False

    with httpx.Client(base_url=supabase_url, timeout=45) as supabase, httpx.Client(
        base_url=api_url, timeout=45
    ) as api:
        # The server must be upgraded before any live E2E mutation can occur.
        _assert_server_ready_for_live_e2e(api)
        try:
            # Provision isolated users without disabling email confirmation.
            # Admin creation marks only these disposable QA users as confirmed.
            user_a = _create_user(supabase, user_a_email, user_a_password, admin)
            user_b = _create_user(supabase, user_b_email, user_b_password, admin)
            assert user_a != user_b, "E2E accounts must be distinct."

            token_a, signed_in_user_a = _login(
                supabase, user_a_email, user_a_password, publishable_key
            )
            token_b, signed_in_user_b = _login(
                supabase, user_b_email, user_b_password, publishable_key
            )
            assert signed_in_user_a == user_a
            assert signed_in_user_b == user_b

            object_path = f"{user_a}/papersignal-e2e-{suffix}.pdf"
            paper = {
                "user_id": user_a,
                "title": "PaperSignal E2E Synthetic QA " + suffix,
                "original_filename": "papersignal-e2e.pdf",
                "storage_path": object_path,
                "content_type": "application/pdf",
                # These are server-owned defaults, not client-supplied fields.
                "size_bytes": len(pdf),
            }

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

            # Verify original bytes and RLS Storage access before any AI job.
            _check_private_pdf_http(
                supabase, object_path, pdf, publishable_key, token_a, token_b
            )

            queued = api.post(
                f"/api/analyze/{paper_id}",
                headers={"Authorization": "Bearer " + token_a},
            )
            assert queued.status_code == 202, queued.text
            job_id = queued.json()["job_id"]

            deadline = time.monotonic() + timeout_seconds
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
                params={
                    "id": "eq." + analysis_id,
                    "paper_id": "eq." + paper_id,
                    "select": "id,result,model",
                },
                headers=_user_headers(publishable_key, token_a),
            )
            result_response.raise_for_status()
            rows = result_response.json()
            assert len(rows) == 1
            result = rows[0]["result"]
            _assert_gemini_analysis_result(result)
            assert result.get("analysis_version")
            assert result.get("evidence"), "Expected page-level evidence in the saved result."

            # User B must not enqueue the paper or read its job, metadata,
            # analysis, or private PDF.
            denied = api.post(
                f"/api/analyze/{paper_id}",
                headers={"Authorization": "Bearer " + token_b},
            )
            assert denied.status_code == 404

            hidden_job = api.get(
                f"/api/analyze/{paper_id}/status",
                params={"job_id": job_id},
                headers={"Authorization": "Bearer " + token_b},
            )
            assert hidden_job.status_code == 404

            hidden_paper = supabase.get(
                "/rest/v1/papers",
                params={"id": "eq." + paper_id, "select": "id"},
                headers=_user_headers(publishable_key, token_b),
            )
            hidden_paper.raise_for_status()
            assert hidden_paper.json() == []

            hidden_analysis = supabase.get(
                "/rest/v1/analyses",
                params={"id": "eq." + analysis_id, "select": "id"},
                headers=_user_headers(publishable_key, token_b),
            )
            hidden_analysis.raise_for_status()
            assert hidden_analysis.json() == []

            private_pdf = supabase.get(
                "/storage/v1/object/authenticated/papers/" + quote(object_path, safe="/"),
                headers=_user_headers(publishable_key, token_b),
            )
            assert private_pdf.status_code in {400, 401, 403, 404}
        finally:
            _cleanup_disposable_e2e(
                supabase, admin, user_a=user_a, user_b=user_b,
                object_path=object_path, paper_id=paper_id,
                job_id=job_id, job_terminal=job_terminal,
            )
