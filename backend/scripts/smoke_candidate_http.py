#!/usr/bin/env python3
"""Start the candidate FastAPI in CI with synthetic config and verify real HTTP.

No Supabase/Gemini calls, production secrets, user records or database writes.
This only checks the candidate ASGI process and its authentication boundary.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:18553"
DUMMY_SUPABASE = "http://127.0.0.1:54321"
DUMMY_SECRET = "sb_secret_synthetic_release_smoke"
WAIT_SECONDS = 25


def run() -> None:
    env = os.environ.copy()
    env.update({
        "SUPABASE_URL": DUMMY_SUPABASE,
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_synthetic_ci",
        "SUPABASE_SERVICE_ROLE_KEY": DUMMY_SECRET,
        "AI_PROVIDER": "extractive",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
    })

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "18553", "--no-access-log"],
        cwd=BACKEND,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + WAIT_SECONDS
        payload = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Candidate API exited before local HTTP health became ready.")
            try:
                with urlopen(ORIGIN + "/health", timeout=2) as response:
                    if response.status != 200:
                        raise RuntimeError("Candidate API local health was not HTTP 200.")
                    payload = json.loads(response.read(4096))
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        if not isinstance(payload, dict):
            raise RuntimeError("Candidate API local health did not become available.")
        if payload.get("status") != "ok" or payload.get("service") != "papersignal-api":
            raise RuntimeError("Candidate API returned an unexpected service or health status.")
        if payload.get("queue_write_mode") != "service_role":
            raise RuntimeError("Candidate API did not initialize server-owned queue writer.")
        if DUMMY_SECRET in json.dumps(payload):
            raise RuntimeError("Candidate API health leaked a server credential.")

        request = Request(
            ORIGIN
            + "/api/analyze/00000000-0000-4000-8000-000000000001/status"
            + "?job_id=00000000-0000-4000-8000-000000000002",
            method="GET",
        )
        try:
            with urlopen(request, timeout=3) as response:
                code = response.status
        except HTTPError as error:
            code = error.code
        if code != 401:
            raise RuntimeError("Anonymous candidate job status access was not denied.")

        print(
            "CANDIDATE_API_HTTP_SMOKE_PASS "
            "queue_write_mode=service_role anon_status=401 no_external_requests=true"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=6)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)


if __name__ == "__main__":
    try:
        run()
    except (RuntimeError, ValueError, OSError) as error:
        print("CANDIDATE_API_HTTP_SMOKE_FAILED: " + str(error), file=sys.stderr)
        raise SystemExit(1) from None
