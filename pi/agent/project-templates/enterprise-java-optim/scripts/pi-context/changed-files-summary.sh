#!/usr/bin/env bash
set -euo pipefail
printf '## Changed files\n'
git status --short 2>/dev/null || true
printf '\n## Diff stat\n'
git --no-pager diff --stat 2>/dev/null || true
printf '\n## Staged diff stat\n'
git --no-pager diff --cached --stat 2>/dev/null || true
printf '\n## File list\n'
{ git diff --name-only; git diff --cached --name-only; } 2>/dev/null | sort -u || true
