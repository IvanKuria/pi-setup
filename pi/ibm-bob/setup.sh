#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cat <<'EOF'
Installed IBM Bob connector dependencies.
Next:
  export BOBSHELL_API_KEY='your_bob_api_key'
  ~/.pi/ibm-bob/start.sh
EOF
