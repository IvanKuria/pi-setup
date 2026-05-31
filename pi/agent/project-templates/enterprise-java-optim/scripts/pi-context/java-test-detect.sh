#!/usr/bin/env bash
set -euo pipefail
printf '## Likely Java test commands\n'
if [[ -x ./mvnw ]]; then
  echo './mvnw test'
elif [[ -f pom.xml ]]; then
  echo 'mvn test'
fi
if [[ -x ./gradlew ]]; then
  echo './gradlew test'
elif [[ -f build.gradle || -f build.gradle.kts ]]; then
  echo 'gradle test'
fi
printf '\n## Test files\n'
find . -path '*/src/test/*' \( -name '*.java' -o -name '*.kt' -o -name '*.groovy' \) -print | sort | head -300
printf '\n## Test framework hints\n'
grep -R --line-number --include='*.java' -E 'org.junit|junit|TestNG|Mockito|AssertJ|@Test|@SpringBootTest' . 2>/dev/null | head -200 || true
