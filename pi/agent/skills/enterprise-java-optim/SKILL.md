---
name: enterprise-java-optim
description: Use for complex enterprise Java, IBM Optim/data archiving, retention, extract/archive/delete/restore workflows, DB2/Oracle/Postgres/JDBC, Spring/batch jobs, and Python automation around archival/data pipelines. Enforces terminal-first plans, production safety, validation, rollback, and small reviewable changes.
---

# Enterprise Java + IBM Optim Skill

Use this skill whenever the task involves Java enterprise systems, IBM Optim, data archiving, retention, migration, DB batch processing, or Python data automation.

## Non-negotiable UX Rules

- Do **not** create markdown implementation/plan/spec files unless the user explicitly asks.
- Plans must be shown inline in the terminal/chat.
- Before editing files, classify the task risk:
  - Safe investigation
  - Safe refactor
  - Behavior change
  - Data movement/archive behavior change
  - Data deletion/purge risk
  - Production configuration risk
- For behavior/data/config/schema/archive/delete risk, ask for approval before edits.
- Prefer small, reviewable diffs.
- State assumptions and unknowns explicitly.

## Workflow

1. Inspect repo structure and build system first.
2. Identify relevant modules, entry points, tests, and data boundaries.
3. Produce an inline plan.
4. Ask for approval if changes are risky.
5. Implement minimal changes.
6. Run or recommend exact validation commands.
7. Summarize changed files, risks, and follow-ups.

## Java Guidelines

Read `references/java-guidelines.md` when doing Java work.

Key defaults:
- Inspect `pom.xml`, `build.gradle`, or parent build files before dependencies.
- Preserve existing coding/logging/exception style.
- Be explicit about transactions and resource lifecycles.
- Prefer constructor injection and testable seams.
- Avoid broad rewrites unless asked.

## IBM Optim / Archiving Guidelines

Read `references/optim-workflow.md` when doing Optim/archive work.

Always distinguish:
- access definition / selection criteria
- extract
- archive/storage
- delete/purge
- restore/query access
- compare/reconciliation/reporting

Never silently change retention, purge, archive selection, or restore behavior.

## Python Guidelines

Read `references/python-guidelines.md` when doing Python data/pipeline work.

Defaults:
- idempotent scripts/jobs
- structured logging
- retries/timeouts
- config via env/files, not literals
- tests around transforms and edge cases

## Optional Knowledge

If present, inspect these files for project/user conventions:

- `AGENTS.md`
- `.pi/knowledge/*.md`
- `~/.pi/agent/knowledge/*.md`
- project README/runbooks
