---
description: Ask IBM Bob to use strongest available reasoning/model routing
argument-hint: "<task>"
---
Use IBM Bob with the strongest available coding/reasoning route for this task. Prefer Opus/GPT-class reasoning over fast/cheap routes if Bob's router supports that choice.

Task: $ARGUMENTS

Rules:
- Do not create markdown plan files unless explicitly requested.
- For complex work, plan inline first and wait for approval before edits.
- Optimize for correctness, safety, and maintainability over speed.
