#!/usr/bin/env bash
set -euo pipefail
printf '## Maximo/MAS-related files and hints\n'
find . -type f | grep -Ei 'maximo|mas|mbo|objectstructure|object-structure|automation|autoscript|jython|integration|oslc|mea|mif|mxserver|psdi' | head -300 || true
printf '\n## Java Maximo/API usage hints\n'
grep -R --line-number --include='*.java' -E 'psdi\.|Mbo|MboSet|MXServer|UserInfo|MXException|RemoteException|object structure|OSLC|Integration|MicService' . 2>/dev/null | head -300 || true
printf '\n## Script/config hints\n'
find . -type f \( -name '*.py' -o -name '*.jy' -o -name '*.json' -o -name '*.xml' -o -name '*.properties' \) -print | grep -Ei 'automation|script|maximo|mbo|integration|object' | head -200 || true
