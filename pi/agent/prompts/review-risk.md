---
description: Review changes for enterprise/data-loss risk
argument-hint: "[scope]"
---
Review the current changes/scope for enterprise production risk: $ARGUMENTS

Classify each issue by severity and risk type:
- data loss / purge risk
- data movement / archive correctness
- transaction/concurrency bugs
- schema/query assumptions
- security/secrets/logging leaks
- Java error handling/resource management
- Python reliability/idempotency
- test coverage gaps

Return concise findings with file paths and actionable fixes. Do not modify files unless I ask.
