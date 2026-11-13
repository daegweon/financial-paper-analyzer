import asyncio

import app.worker as worker


def test_worker_uses_new_supabase_secret_as_apikey_only(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE_ROLE_KEY", "sb_secret_test")
    monkeypatch.setattr(worker, "SUPABASE_KEY", "sb_publishable_test")
    assert worker.headers() == {
        "apikey": "sb_secret_test",
        "Content-Type": "application/json",
    }


def test_worker_supports_legacy_service_role_jwt(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE_ROLE_KEY", "legacy-service-role-jwt")
    monkeypatch.setattr(worker, "SUPABASE_KEY", "legacy-anon-key")
    assert worker.headers() == {
        "apikey": "legacy-anon-key",
        "Authorization": "Bearer legacy-service-role-jwt",
        "Content-Type": "application/json",
    }


def test_worker_rejects_missing_service_role_secret(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE_ROLE_KEY", "")
    with __import__("pytest").raises(RuntimeError, match="SUPABASE_SERVICE_ROLE_KEY"):
        worker.headers()


def test_worker_rejects_legacy_key_without_publishable_key(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE_ROLE_KEY", "legacy-service-role-jwt")
    monkeypatch.setattr(worker, "SUPABASE_KEY", "")
    with __import__("pytest").raises(RuntimeError, match="SUPABASE_PUBLISHABLE_KEY"):
        worker.headers()

def test_worker_accepts_new_secret_without_publishable_key(monkeypatch):
    monkeypatch.setattr(worker, "SERVICE_ROLE_KEY", "sb_secret_test")
    monkeypatch.setattr(worker, "SUPABASE_KEY", "")
    assert worker.headers() == {
        "apikey": "sb_secret_test",
        "Content-Type": "application/json",
    }
