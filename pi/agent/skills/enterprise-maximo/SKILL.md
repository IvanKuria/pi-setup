---
name: enterprise-maximo
description: Use for IBM Maximo/MAS SWE intern work, enterprise Java, Maximo business objects/MBOs, object structures, integrations, REST APIs, automation scripts, Jython/Python, DB config, and code review. Optimizes for clean, modular, minimal, upgrade-safe code that follows existing repo conventions and avoids over-engineering.
---

# Enterprise Maximo SWE Intern Skill

Use this skill for IBM Maximo, MAS, enterprise Java, integrations, automation scripts, object structures, MBO-related code, REST/API work, DB/config changes, and intern learning/review workflows.

## Core Goal

Help the user become a stronger SWE intern: write code that is clean, modular, maintainable, appropriately small, and easy for senior engineers to review.

## Non-negotiable Rules

- Prefer boring, explicit, maintainable code over clever code.
- Do not create markdown implementation plans unless explicitly requested.
- Show plans inline.
- Investigate existing patterns before editing.
- Do not invent Maximo APIs; inspect existing usage or docs/comments first.
- Prefer extension points and local changes over broad core behavior changes.
- Flag upgrade-safety, compatibility, data, integration, and config risks.
- Avoid large abstractions unless there are clear repeated call sites or project convention requires it.
- No new dependencies without explicit approval.
- Ask before edits when requirements, persistence behavior, integration behavior, or upgrade impact is unclear.

## Default Workflow

1. Identify the ticket/task goal in one sentence.
2. Inspect relevant files and existing patterns.
3. Classify risk: safe refactor, behavior change, integration change, data/config change, upgrade-safety risk.
4. Propose the smallest clean design inline.
5. Ask approval before risky changes.
6. Implement minimal diffs.
7. Run or recommend exact tests.
8. Summarize what changed, why, risk, and what to say in standup/PR.

## Clean Code Defaults

Read `references/clean-code-guidelines.md` for review/implementation.

Default constraints:
- Prefer 1-3 changed files for normal tickets.
- No new class unless it has a clear responsibility.
- No `Manager`, `Processor`, `Helper`, `Util`, or `Service` naming unless repo convention supports it.
- Keep methods short and readable; split only when names improve clarity.
- Avoid premature interfaces/abstract classes.
- Avoid framework magic if explicit code is clearer.
- Tests or stated test gap for every behavior change.

## Maximo/MAS Defaults

Read `references/maximo-guidelines.md` when Maximo-specific work is involved.

Focus on:
- existing extension points
- MBO/object structure/API conventions
- upgrade safety
- integration contracts
- DB/config compatibility
- security/permissions
- logging and observability

## Intern Development Defaults

Read `references/intern-workflow.md` for learning-focused tasks.

When useful, explain:
- what changed
- why this design is reviewable
- what a senior engineer might question
- how to describe it in standup/PR
