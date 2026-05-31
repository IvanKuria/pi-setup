---
description: Safely review, commit, and optionally push current changes
argument-hint: "<commit-message>"
---
Safely commit current changes with message: $ARGUMENTS

Workflow:
1. Run git status.
2. Review changed files and diff summary.
3. Check for secrets, accidental files, generated junk, or oversized diffs.
4. If risk is acceptable, stage changes.
5. Commit with the provided message.
6. Ask before pushing unless I explicitly included "push" in the request.

Use exact git commands. Stop and ask if anything looks risky.
