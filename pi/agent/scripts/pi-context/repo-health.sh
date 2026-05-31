#!/usr/bin/env bash
set -euo pipefail
printf '## Repo\n'
printf 'PWD: %s\n' "$PWD"
printf '\n## Git status\n'
git status --short --branch 2>/dev/null || true
printf '\n## Recent commits\n'
git --no-pager log --oneline -5 2>/dev/null || true
printf '\n## Top-level files\n'
find . -maxdepth 2 -type f | sed 's#^./##' | sort | head -200
printf '\n## Build/test indicators\n'
find . -maxdepth 4 \( -name 'pom.xml' -o -name 'build.gradle' -o -name 'build.gradle.kts' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements*.txt' -o -name 'Makefile' \) -print | sort
