#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z "${BOBSHELL_API_KEY:-}" ]]; then
  echo "Set BOBSHELL_API_KEY first. Example: export BOBSHELL_API_KEY='<your_bob_api_key>'" >&2
  exit 2
fi
if [[ ! -d .venv ]]; then
  echo "Missing .venv; run ~/.pi/ibm-bob/setup.sh first" >&2
  exit 2
fi
export PI_BOB_PROXY_KEY="${PI_BOB_PROXY_KEY:-pi-bob-local}"
export BOB_MODELS="${BOB_MODELS:-premium}"
. .venv/bin/activate
exec uvicorn server:app --host 127.0.0.1 --port "${PI_BOB_PROXY_PORT:-4010}"
