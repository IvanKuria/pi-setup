#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

find_python() {
  for candidate in "${PYTHON:-}" python3.13 python3.12 python3.11 python3; do
    [[ -z "$candidate" ]] && continue
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  cat >&2 <<'EOF'
Python 3.11+ is required for the IBM Bob connector, but no suitable Python was found.

Install one, then rerun setup:

  macOS/Homebrew:
    brew install python@3.12

  Or set explicitly:
    PYTHON=/path/to/python3.12 ~/.pi/ibm-bob/setup.sh
EOF
  exit 2
fi

printf 'Using Python: %s\n' "$PYTHON_BIN"
"$PYTHON_BIN" --version

# Recreate if an existing venv was made with an older Python.
if [[ -d .venv ]]; then
  if ! .venv/bin/python - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
  then
    echo "Existing .venv uses Python < 3.11; recreating it."
    rm -rf .venv
  fi
fi

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

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
