# Clean Code Guidelines

## Design Principles

- Prefer small, direct changes that fit the existing codebase.
- Optimize for readability by future maintainers.
- Introduce abstraction only when it removes real duplication or clarifies a stable domain concept.
- Prefer explicit names over cleverness.
- Keep behavior changes separate from mechanical refactors when possible.

## Avoid Overbuilding

Avoid unless clearly justified:
- new dependency
- new framework pattern
- new interface with one implementation
- generic `Helper`/`Util` classes
- broad rewrites
- speculative configuration knobs
- excessive factories/builders/managers

## Review Checklist

- [ ] Does this solve the exact ticket, not a bigger imagined problem?
- [ ] Are names domain-specific and understandable?
- [ ] Is the diff small enough to review comfortably?
- [ ] Are conditionals readable?
- [ ] Is error handling explicit?
- [ ] Is logging useful but not noisy/sensitive?
- [ ] Are tests added or is the test gap explained?
- [ ] Are public APIs and compatibility preserved?

## Smells

- Method does unrelated things.
- Boolean flags change behavior in surprising ways.
- New abstraction has only one call site and unclear future.
- Code hides data/integration side effects.
- Error is swallowed or only logged.
- Names describe implementation instead of intent.
