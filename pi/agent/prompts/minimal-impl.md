---
description: Implement the smallest clean change, avoiding over-engineering
argument-hint: "<task>"
---
Implement the smallest clean change for: $ARGUMENTS

Rules:
- Investigate existing patterns first.
- Prefer local, boring, idiomatic changes.
- Do not add dependencies without approval.
- Do not introduce new abstractions unless clearly justified.
- Avoid new classes/interfaces unless necessary.
- Keep the diff small and reviewable.
- If requirements are ambiguous or risk is non-trivial, stop after an inline plan and ask before editing.
- After changes, run or recommend exact tests.
