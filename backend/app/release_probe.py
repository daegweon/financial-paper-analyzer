"""Read-only check of the EXISTING PaperSignal Railway API.

The target is a compiled-in exact HTTPS origin. This probe never receives
credentials, creates users, queues work, uploads PDFs or writes to Supabase.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

LIVE_API_ORIGIN = "https://papersignal-api-production.up.railway.app"
HEALTH_URL = LIVE_API_ORIGIN + "/health"
NO_AUTH_URL = (
    LIVE_API_ORIGIN
    + "/api/analyze/00000000-0000-4000-8000-000000000001/status"
    + "?job_id=00000000-0000-4000-8000-000000000002"
)


class ReadOnlyProbeError(RuntimeError):
    """A release safety preflight did not satisfy its contract."""


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ReadOnlyProbeError("Live API redirected unexpectedly; no redirect followed.")


@dataclass(frozen=True)
class ApiProbeResult:
    service: str
    status: str
    queue_write_mode: str
    anon_status_code: int
    analysis_version: str


def _request(opener, url: str) -> tuple[int, bytes]:
    if url not in (HEALTH_URL, NO_AUTH_URL):
        raise ReadOnlyProbeError("Unexpected endpoint requested.")
    req = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with opener.open(req, timeout=12) as response:
            if response.geturl() != url:
                raise ReadOnlyProbeError("Live API changed its destination.")
            status = response.status
            raw = response.read(8193)
            if len(raw) > 8192:
                raise ReadOnlyProbeError("Live API response unexpectedly large.")
            return status, raw
    except HTTPError as error:
        # 401 is the expected anonymous result for the *read-only* status API.
        return error.code, b""
    except ReadOnlyProbeError:
        raise
    except (URLError, TimeoutError, OSError):
        raise ReadOnlyProbeError("Live API was not reachable over the pinned HTTPS origin.") from None


def probe_live_api(opener=None, *, require_server_owned: bool = False) -> ApiProbeResult:
    if opener is None:
        opener = build_opener(RejectRedirects())

    health_status, raw = _request(opener, HEALTH_URL)
    if health_status != 200:
        raise ReadOnlyProbeError("Live API /health did not return HTTP 200.")
    try:
        health = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ReadOnlyProbeError("Live API returned invalid health JSON.") from None
    if not isinstance(health, dict):
        raise ReadOnlyProbeError("Live API health payload was not an object.")
    if health.get("status") != "ok" or health.get("service") != "papersignal-api":
        raise ReadOnlyProbeError("Live API health service/status does not match PaperSignal.")
    version = health.get("analysis_version")
    if not isinstance(version, str) or not version.strip():
        raise ReadOnlyProbeError("Live API analysis version was not reported.")

    declared = health.get("queue_write_mode")
    if declared is None:
        # The old API legitimately predates the security release; still online.
        writer = "legacy_missing_marker"
    elif declared == "service_role":
        writer = "service_role"
    elif declared == "unavailable":
        raise ReadOnlyProbeError("Live API explicitly reports queue writer unavailable.")
    else:
        raise ReadOnlyProbeError("Live API returned an unexpected queue writer mode.")

    status_code, _ = _request(opener, NO_AUTH_URL)
    if status_code != 401:
        raise ReadOnlyProbeError("Anonymous analysis job status was not denied with HTTP 401.")

    if require_server_owned and writer != "service_role":
        raise ReadOnlyProbeError(
            "Server-owned API has not been deployed. Do NOT apply the client grants migration."
        )

    return ApiProbeResult(
        service="papersignal-api",
        status="ok",
        queue_write_mode=writer,
        anon_status_code=status_code,
        analysis_version=version,
    )
