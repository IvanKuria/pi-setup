#!/usr/bin/env bash
set -euo pipefail
printf '## Optim/archive-related files\n'
find . -type f | grep -Ei 'optim|archive|retention|purge|extract|restore|reconcile|access.*definition' | head -300 || true
printf '\n## SQL/data movement hints\n'
grep -R --line-number -Ei 'delete from|truncate|archive|retention|purge|extract|restore|optim|commit interval|batch size' . 2>/dev/null | head -300 || true
