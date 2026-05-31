---
description: Finish a ticket by reviewing diff, testing, checking clean code, and preparing PR notes
argument-hint: "[ticket-id]"
---
Finish this ticket: $ARGUMENTS

Run a disciplined finish workflow:
1. Inspect git status and changed files.
2. Review diff for correctness and minimality.
3. Run relevant tests/lint if feasible; otherwise state exact commands.
4. Apply clean-code gate: over-engineering, names, size, duplication, risk.
5. Confirm no secrets or accidental files.
6. Produce PR summary with testing and risk notes.

Do not commit unless I explicitly ask.
