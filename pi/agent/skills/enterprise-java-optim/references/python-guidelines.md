# Python Data/Pipeline Guidelines

## Defaults

- Use type hints for public functions and data structures.
- Prefer pure transform functions with tests.
- Use structured logging; avoid printing secrets or sensitive records.
- Config via env vars, config files, or secret stores; no hardcoded credentials.
- Make jobs idempotent and restartable.
- Add timeouts and retries with bounded backoff for network/DB calls.

## Data Job Safety

- Separate scan/plan, execute, validate, and cleanup phases.
- Prefer dry-run mode for destructive or expensive operations.
- Checkpoint long-running jobs.
- Track counts, failed records, skipped records, and reconciliation outputs.
- Use explicit transaction scopes and batch sizes.

## Testing

- Unit-test transforms and selection predicates.
- Mock external systems at boundaries.
- Include malformed/empty/duplicate input cases.
- Test restart/idempotency behavior when possible.

## Review Red Flags

- Unbounded memory loading of large datasets.
- Bare `except` or swallowed exceptions.
- Non-idempotent retries.
- Inconsistent timezone handling.
- Credentials in source/logs.
- Partial writes without recovery plan.
