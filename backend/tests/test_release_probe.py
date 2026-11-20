"""No live network access in these contract tests."""
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from app.release_probe import (
    HEALTH_URL, NO_AUTH_URL, ReadOnlyProbeError, probe_live_api, _request,
)


class FakeResponse:
    def __init__(self, url, status, body):
        self.url, self.status, self.body = url, status, body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.body[:limit]


class FakeOpener:
    def __init__(self, health=None, anon_status=401, redirect=None):
        self.health = health if health is not None else {
            "status": "ok",
            "service": "papersignal-api",
            "analysis_version": "finance-structured-v6.4.2",
        }
        self.anon_status = anon_status
        self.redirect = redirect
        self.calls = []

    def open(self, req: Request, timeout):
        assert req.get_method() == "GET"
        assert not req.has_header("Authorization")
        assert timeout == 12
        self.calls.append(req.full_url)
        if req.full_url == HEALTH_URL:
            body = (json.dumps(self.health).encode()
                    if not isinstance(self.health, bytes) else self.health)
            return FakeResponse(self.redirect or HEALTH_URL, 200, body)
        if req.full_url == NO_AUTH_URL:
            if self.anon_status == 401:
                raise HTTPError(req.full_url, 401, "Not authorized", {}, None)
            return FakeResponse(NO_AUTH_URL, self.anon_status, b"{}")
        raise AssertionError("Probe made an unexpected live request.")


def test_legacy_api_readonly_probe_does_not_claim_server_queue_readiness():
    mock = FakeOpener()
    result = probe_live_api(mock)
    assert result.queue_write_mode == "legacy_missing_marker"
    assert result.anon_status_code == 401
    assert mock.calls == [HEALTH_URL, NO_AUTH_URL]
    with pytest.raises(ReadOnlyProbeError, match="not been deployed"):
        probe_live_api(FakeOpener(), require_server_owned=True)


def test_new_server_only_api_health_marker_is_accepted():
    mock = FakeOpener(health={
        "status": "ok", "service": "papersignal-api",
        "queue_write_mode": "service_role",
        "analysis_version": "finance-structured-v6.4.2",
    })
    result = probe_live_api(mock, require_server_owned=True)
    assert result.queue_write_mode == "service_role"
    assert mock.calls == [HEALTH_URL, NO_AUTH_URL]


@pytest.mark.parametrize("mode", ["unavailable", "authenticated", "disabled", 1])
def test_rejects_unsafe_or_unknown_queue_writer_modes(mode):
    mock = FakeOpener(health={
        "status": "ok", "service": "papersignal-api",
        "queue_write_mode": mode,
        "analysis_version": "finance-structured-v6.4.2",
    })
    with pytest.raises(ReadOnlyProbeError, match="queue writer"):
        probe_live_api(mock)


@pytest.mark.parametrize("health", [
    {"status": "fail", "service": "papersignal-api", "analysis_version": "v1"},
    {"status": "ok", "service": "other-project", "analysis_version": "v1"},
    {"status": "ok", "service": "papersignal-api", "analysis_version": ""},
    [],
    b"not-json",
])
def test_rejects_unhealthy_mismatched_or_invalid_health(health):
    with pytest.raises(ReadOnlyProbeError):
        probe_live_api(FakeOpener(health=health))


@pytest.mark.parametrize("code", [200, 403, 404, 500])
def test_anonymous_status_must_be_exactly_401(code):
    with pytest.raises(ReadOnlyProbeError, match="was not denied"):
        probe_live_api(FakeOpener(anon_status=code))


def test_redirect_or_unexpected_url_rejected():
    with pytest.raises(ReadOnlyProbeError, match="changed its destination"):
        probe_live_api(FakeOpener(redirect="https://other.example.com/health"))
    with pytest.raises(ReadOnlyProbeError, match="Unexpected endpoint"):
        _request(FakeOpener(), "https://example.com/")


def test_health_request_never_sends_credentials():
    mock = FakeOpener()
    probe_live_api(mock)
    assert len(mock.calls) == 2
    assert all(path.startswith("https://papersignal-api-production.up.railway.app/") for path in mock.calls)
