# IBM Maximo / MAS Guidelines

## Investigation First

Before editing, identify:
- product/module area
- existing extension points
- object structures / MBOs / services involved
- integration contracts and external callers
- DB/config implications
- permission/security boundaries
- existing tests and patterns

## Upgrade Safety

Prefer extension/configuration-compatible changes over modifying central behavior. Flag anything that could affect:
- upgrade compatibility
- integrations
- object structure payloads
- automation scripts
- database assumptions
- security/authorization
- performance in large customer datasets

## Implementation Defaults

- Follow existing Maximo/MAS conventions in the repo.
- Keep changes local and incremental.
- Preserve public behavior unless the ticket explicitly changes it.
- Be conservative with persistence, transactions, and integration payloads.
- Avoid logging customer-sensitive values.
- Consider tenant/customer configuration variability.

## Questions to Ask

- Is this behavior customer-configurable?
- Is there an existing extension point?
- Will this change affect integrations or object structures?
- Does this run in batch, UI, API, or automation-script context?
- What permissions are required?
- What happens on large data volumes?
- How is this tested today?
