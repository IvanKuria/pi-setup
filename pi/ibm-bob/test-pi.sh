#!/usr/bin/env bash
set -euo pipefail
PROMPT="${*:-Say hello in one sentence.}"
BASE_URL="${PI_BOB_PROXY_URL:-http://127.0.0.1:${PI_BOB_PROXY_PORT:-4010}}"

echo "== pi end-to-end test against IBM Bob connector =="
echo "Checking connector health..."
curl -fsS --max-time 5 "$BASE_URL/health" | python3 -m json.tool || {
  echo "Connector is not reachable. Start ~/.pi/ibm-bob/start.sh first." >&2
  exit 1
}

echo
echo "Running pi non-interactive prompt..."
set -x
pi --model ibm-bob/bob-best --no-session -p "$PROMPT"
