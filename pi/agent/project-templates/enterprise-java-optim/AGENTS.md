# Project Instructions

This repository contains enterprise Java/Python/data archiving work.

## Default behavior

- Do not create markdown plan/spec/implementation files unless explicitly requested.
- Show plans inline and wait for approval before risky implementation.
- Prefer small, reviewable diffs.
- Always run or suggest relevant test commands.
- Never change retention, deletion, archival, restore, or production configuration behavior without calling out risk.

## Java

- Inspect `pom.xml`, `build.gradle`, or parent build files before adding dependencies.
- Preserve existing logging, exception, and transaction style.
- Be explicit about transaction boundaries and resource lifecycles.

## IBM Optim / Data Archiving

- Treat access definition, extract, archive, delete/purge, restore, compare, and reports as separate phases.
- Always document validation, reconciliation, and rollback before destructive actions.
- Prefer dry-run/report-only modes for archive/delete jobs.

## Python

- Prefer type hints, structured logging, idempotent jobs, bounded retries, and config via env/files.
- Avoid loading large datasets fully into memory unless proven safe.

## Maximo / MAS Intern Coding Principles

- Prefer boring, explicit, maintainable code.
- Follow existing repo conventions before introducing patterns.
- Do not invent Maximo APIs; inspect existing usage first.
- Prefer extension points over modifying core behavior.
- Avoid new dependencies without approval.
- Avoid abstraction unless there are 3+ real call sites or a clear domain concept.
- Keep normal ticket diffs small and reviewable.
- Flag upgrade-safety, object structure, integration, DB/config, and permission risks.
- Ask clarifying questions before coding if requirements or data/integration impacts are unclear.
