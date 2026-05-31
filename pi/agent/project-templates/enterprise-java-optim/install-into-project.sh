#!/usr/bin/env bash
set -euo pipefail
src="$(cd "$(dirname "$0")" && pwd)"
cp -R "$src/AGENTS.md" .
mkdir -p .pi/knowledge scripts/pi-context
cp -R "$src/.pi/knowledge/"* .pi/knowledge/
cp -R "$src/scripts/pi-context/"* scripts/pi-context/
chmod +x scripts/pi-context/*.sh
printf 'Installed enterprise Java/Optim pi project template into %s\n' "$PWD"
