#!/usr/bin/env python3
"""Non-mutating deployment preflight. No bearer token, service key or user data."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.release_probe import ReadOnlyProbeError, probe_live_api


def main() -> int:
    parser = argparse.ArgumentParser(description="Pinned, GET-only PaperSignal release preflight")
    parser.add_argument(
        "--require-server-owned", action="store_true",
        help="Fail unless the deployed API reports server-owned queue writes",
    )
    args = parser.parse_args()
    try:
        result = probe_live_api(require_server_owned=args.require_server_owned)
    except ReadOnlyProbeError as error:
        print("READ_ONLY_API_RELEASE_PROBE_FAILED: " + str(error), file=sys.stderr)
        return 2
    print(
        "READ_ONLY_API_RELEASE_PROBE_PASS "
        + "service=" + result.service
        + " anon_status=" + str(result.anon_status_code)
        + " queue_writer=" + result.queue_write_mode
        + " analysis_version=" + result.analysis_version
    )
    if result.queue_write_mode == "legacy_missing_marker":
        print("RELEASE_GATE_PENDING: old API is healthy but server-owned queue release is not proven.")
    else:
        print("RELEASE_READINESS_SIGNAL: server-owned API code is deployed; authenticated E2E still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
