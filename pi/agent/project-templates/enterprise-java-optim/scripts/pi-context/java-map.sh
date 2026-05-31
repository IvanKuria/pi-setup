#!/usr/bin/env bash
set -euo pipefail
printf '## Build files\n'
find . -maxdepth 4 \( -name 'pom.xml' -o -name 'build.gradle' -o -name 'build.gradle.kts' -o -name 'settings.gradle' -o -name 'settings.gradle.kts' \) -print | sort
printf '\n## Java packages/classes (top 200)\n'
find . -path '*/src/*/java/*' -name '*.java' -print | sort | head -200
printf '\n## Spring/batch hints\n'
grep -R --line-number --include='*.java' -E '@SpringBootApplication|@Component|@Service|@Repository|@Transactional|JobBuilder|StepBuilder|JdbcTemplate|EntityManager' . 2>/dev/null | head -200 || true
