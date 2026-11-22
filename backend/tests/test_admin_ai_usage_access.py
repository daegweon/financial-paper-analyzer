import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as module


ADMIN_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
VALID_TOKEN = "valid_test_jwt"


def configure_admin(monkeypatch, *, user_id=ADMIN_ID, admin_ids=None):
    monkeypatch.setattr(module, "SUPABASE_URL", "https://mock.supabase.test")
    monkeypatch.setattr(module, "SUPABASE_KEY", "sb_publishable_test")
    monkeypatch.setattr(module, "SERVICE_ROLE_KEY", "sb_secret_service_test")
    monkeypatch.setattr(module, "ADMIN_USER_IDS", set(admin_ids if admin_ids is not None else [ADMIN_ID]))
    monkeypatch.setattr(module, "ADMIN_MONTHLY_AI_BUDGET_USD", "")

    async def verify_user(_client, token):
        assert token == VALID_TOKEN
        return user_id

    monkeypatch.setattr(module, "_verify_user", verify_user)


class NoDatabaseAccessClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def get(self, *_args, **_kwargs):
        raise AssertionError("A non-admin request must not read administrator data.")

    async def post(self, *_args, **_kwargs):
        raise AssertionError("A non-admin request must not write administrator data.")


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/admin/ai-usage/summary?month=2026-11", None),
        ("post", "/api/admin/ai-usage/budget", {"monthly_budget_usd": "12.50"}),
    ],
)
def test_non_admin_cannot_read_or_change_service_ai_usage(monkeypatch, method, path, payload):
    configure_admin(monkeypatch, user_id=USER_ID)
    monkeypatch.setattr(module.httpx, "AsyncClient", NoDatabaseAccessClient)

    client = TestClient(module.app)
    response = (
        client.get(path, headers={"Authorization": f"Bearer {VALID_TOKEN}"})
        if method == "get"
        else client.post(
            path,
            json=payload,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    )

    assert response.status_code == 403
    assert "관리자 권한" in response.json()["detail"]


def test_empty_admin_allowlist_denies_even_a_known_user(monkeypatch):
    configure_admin(monkeypatch, user_id=ADMIN_ID, admin_ids=[])
    monkeypatch.setattr(module.httpx, "AsyncClient", NoDatabaseAccessClient)

    response = TestClient(module.app).get(
        "/api/admin/ai-usage/summary?month=2026-11",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 403


def test_admin_summary_uses_service_role_and_returns_only_aggregates(monkeypatch):
    configure_admin(monkeypatch)
    requests = []

    event = {
        "user_id": USER_ID,
        "paper_id": "33333333-3333-4333-8333-333333333333",
        "analysis_job_id": "44444444-4444-4444-8444-444444444444",
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "outcome": "success",
        "billing_mode": None,
        "prompt_tokens": 100,
        "candidate_tokens": 20,
        "thought_tokens": 0,
        "total_tokens": 120,
        "latency_ms": 250,
        "created_at": "2026-11-20T10:00:00Z",
    }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return None

        async def get(self, url, **kwargs):
            requests.append((url, kwargs))
            headers = kwargs["headers"]
            assert headers["apikey"] == "sb_secret_service_test"
            assert "Authorization" not in headers

            if url.endswith("/rest/v1/ai_usage_events"):
                assert kwargs["params"]["select"] == (
                    "user_id,paper_id,provider,model,outcome,billing_mode,"
                    "prompt_tokens,candidate_tokens,thought_tokens,total_tokens,latency_ms,created_at"
                )
                return httpx.Response(200, json=[event])
            if url.endswith("/rest/v1/ai_admin_settings"):
                return httpx.Response(200, json=[])
            raise AssertionError("Unexpected database read: " + url)

    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)

    response = TestClient(module.app).get(
        "/api/admin/ai-usage/summary?month=2026-11",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 200
    summary = response.json()
    assert summary["event_count"] == 1
    assert summary["unknown_cost_events"] == 1
    assert summary["cost_coverage_complete"] is False
    assert summary["monthly_budget_usd"] is None
    assert len(summary["users"]) == 1
    assert summary["users"][0]["user_id"] == USER_ID
    assert "events" not in summary

    serialized = response.text
    assert "paper_id" not in serialized
    assert "analysis_job_id" not in serialized
    assert len(requests) == 2


def test_admin_budget_write_uses_service_role_only(monkeypatch):
    configure_admin(monkeypatch)
    writes = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return None

        async def post(self, url, **kwargs):
            writes.append((url, kwargs))
            assert url.endswith("/rest/v1/ai_admin_settings")
            assert kwargs["headers"]["apikey"] == "sb_secret_service_test"
            assert "Authorization" not in kwargs["headers"]
            assert kwargs["params"]["on_conflict"] == "setting_key"
            assert kwargs["json"]["setting_key"] == "monthly_budget_usd"
            assert kwargs["json"]["value_numeric"] == "12.5"
            assert kwargs["json"]["updated_by"] == ADMIN_ID
            return httpx.Response(201)

    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)

    response = TestClient(module.app).post(
        "/api/admin/ai-usage/budget",
        json={"monthly_budget_usd": "12.5"},
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == {"monthly_budget_usd": "12.50", "updated": True}
    assert len(writes) == 1


@pytest.mark.parametrize("value", [-1, "-0.01", "NaN", "Infinity", True, None])
def test_admin_budget_rejects_invalid_values_without_database_write(monkeypatch, value):
    configure_admin(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", NoDatabaseAccessClient)

    response = TestClient(module.app).post(
        "/api/admin/ai-usage/budget",
        json={"monthly_budget_usd": value},
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 422

def test_admin_access_endpoint_returns_true_for_allowlisted_user(monkeypatch):
    configure_admin(monkeypatch)

    response = TestClient(module.app).get(
        "/api/admin/access",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == {"is_admin": True}


def test_admin_access_endpoint_returns_false_for_regular_user(monkeypatch):
    configure_admin(monkeypatch, user_id=USER_ID)

    response = TestClient(module.app).get(
        "/api/admin/access",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == {"is_admin": False}


def test_admin_access_endpoint_requires_authentication(monkeypatch):
    configure_admin(monkeypatch)

    response = TestClient(module.app).get("/api/admin/access")

    assert response.status_code == 401

