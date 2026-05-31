# Enterprise Java Guidelines

## First Inspection

- Identify build system: Maven, Gradle, Ant, mixed multi-module.
- Inspect parent build files before adding dependencies.
- Locate application framework: Spring Boot, Jakarta EE, batch framework, plain CLI.
- Find test commands and existing test patterns.

## Coding Defaults

- Preserve project style and package boundaries.
- Prefer small changes and explicit naming.
- Avoid new dependencies unless justified.
- Use constructor injection where applicable.
- Avoid static global state for data pipeline logic.
- Keep business rules separate from infrastructure where practical.

## Data/DB Safety

- Make transaction boundaries explicit.
- Use try-with-resources for JDBC and streams.
- Avoid unbounded result sets; use pagination/cursors/batches.
- Consider isolation level and locking behavior.
- For batch writes/deletes, document commit interval and retry semantics.

## Testing

Prefer targeted tests:
- unit tests for eligibility/selection logic
- integration tests for repository/query behavior
- dry-run tests for archive job planning
- regression tests for edge cases/nulls/time zones

## Review Red Flags

- Broad `DELETE`/`UPDATE` without precise predicates.
- Date/time zone assumptions.
- Silent swallowing of exceptions.
- Logging PII/secrets.
- Retrying non-idempotent operations.
- Hidden behavior changes in refactors.
