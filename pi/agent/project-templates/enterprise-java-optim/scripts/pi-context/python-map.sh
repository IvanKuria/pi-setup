#!/usr/bin/env bash
set -euo pipefail
printf '## Python project files\n'
find . -maxdepth 4 \( -name 'pyproject.toml' -o -name 'requirements*.txt' -o -name 'setup.py' -o -name 'tox.ini' \) -print | sort
printf '\n## Python modules (top 200)\n'
find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -print | sort | head -200
printf '\n## Data/DB/logging hints\n'
grep -R --line-number --include='*.py' -E 'sqlalchemy|psycopg|cx_Oracle|oracledb|ibm_db|pyodbc|logging|getLogger|retry|backoff|batch|archive|purge|delete' . 2>/dev/null | head -200 || true
