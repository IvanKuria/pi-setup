---
description: Implement the approved ticket plan with small clean diffs
argument-hint: "<approved-plan-or-option>"
---
Implement this approved ticket plan: $ARGUMENTS

Rules:
- Keep the diff small and reviewable.
- Prefer edit over write; do not rewrite whole files unless necessary.
- Match existing style and patterns.
- No new dependencies without approval.
- Avoid new abstractions unless clearly justified.
- Run or identify relevant tests after changes.
- After edits, show git diff summary and call out risks.
