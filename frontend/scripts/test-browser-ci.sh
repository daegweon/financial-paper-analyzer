#!/usr/bin/env bash
# Browser QA fails closed unless ALL sources point to synthetic localhost fixtures.
set -euo pipefail

if [[ "${PAPERSIGNAL_BROWSER_QA:-}" != "1" ||
      "${PAPERSIGNAL_BROWSER_QA_URL:-}" != "http://localhost:3000" ||
      "${PAPERSIGNAL_BROWSER_QA_MOCKS:-}" != "1" ||
      "${NEXT_PUBLIC_SUPABASE_URL:-}" != "http://127.0.0.1:54321" ||
      "${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:-}" != "sb_publishable_local_qa_only" ||
      "${NEXT_PUBLIC_API_URL:-}" != "http://127.0.0.1:54322" ]]; then
  echo "Refusing browser CI: only exact synthetic localhost endpoints are permitted." >&2
  exit 2
fi

log_path="$(mktemp)"
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -f "$log_path"
}
trap cleanup EXIT

npm run dev -- --hostname 127.0.0.1 --port 3000 >"$log_path" 2>&1 &
server_pid=$!
healthy=0
for _ in $(seq 1 45); do
  if curl --fail --silent --max-time 2 --output /dev/null "http://localhost:3000"; then
    healthy=1
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "Isolated Next.js server terminated before becoming ready." >&2
    exit 1
  fi
  sleep 2
done
if [[ "$healthy" != "1" ]]; then
  echo "Isolated Next.js server did not become ready." >&2
  exit 1
fi
npm run test:browser:ci
