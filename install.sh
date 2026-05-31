#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.pi/agent" "$HOME/.pi/ibm-bob"
rsync -a "$root/pi/ibm-bob/" "$HOME/.pi/ibm-bob/"
rsync -a "$root/pi/agent/prompts/" "$HOME/.pi/agent/prompts/"
rsync -a "$root/pi/agent/skills/" "$HOME/.pi/agent/skills/"
rsync -a "$root/pi/agent/knowledge/" "$HOME/.pi/agent/knowledge/"
rsync -a "$root/pi/agent/project-templates/" "$HOME/.pi/agent/project-templates/"
cp "$root/pi/agent/models.json" "$HOME/.pi/agent/models.json"
cp "$root/pi/agent/settings.json" "$HOME/.pi/agent/settings.json"
chmod +x "$HOME/.pi/ibm-bob"/*.sh "$HOME/.pi/ibm-bob/server.py" 2>/dev/null || true
find "$HOME/.pi/agent/project-templates" -name '*.sh' -exec chmod +x {} \; 2>/dev/null || true
cat <<'EOF'
Installed pi setup.

Next:
  ~/.pi/ibm-bob/setup.sh
  export BOBSHELL_API_KEY='<your_bob_api_key>'
  ~/.pi/ibm-bob/start.sh
EOF
