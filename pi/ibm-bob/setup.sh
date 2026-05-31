#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(
        f"Python 3.11+ is required for the IBM Bob connector; found {sys.version.split()[0]}. "
        "Install Python 3.11+ and rerun setup.sh."
    )
PY

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Install the IBM Bob LiteLLM provider from a vendored wheel. This avoids failures
# on machines/corporate networks where PyPI package discovery cannot find
# litellm-ibm-bob.
python -m pip install vendor/litellm_ibm_bob-0.1.0-py3-none-any.whl

cat <<'EOF'
Installed IBM Bob connector dependencies.
Next:
  export BOBSHELL_API_KEY='<your_bob_api_key>'
  ~/.pi/ibm-bob/start.sh
EOF
