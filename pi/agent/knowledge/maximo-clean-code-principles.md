# Maximo / IBM SWE Intern Clean Code Principles

- Prefer boring code.
- Follow existing repo conventions.
- Do not introduce abstractions without clear reuse.
- Keep public API changes minimal.
- Avoid reflection/dynamic magic unless already used nearby.
- Prefer explicit domain names over clever names.
- Every behavior change needs a test or a stated reason why not.
- If touching persistence/integration/config, call out compatibility and migration risk.
- Prefer extension points over modifying core behavior.
- Do not invent Maximo APIs; inspect existing usage first.
- Avoid new dependencies unless explicitly approved.
- Keep normal ticket diffs small, ideally 1-3 files.
- No new class unless it has a clear responsibility.
- No method over ~60 lines unless justified.
- Avoid generic names like Processor, Handler, Manager, Service, Helper, Util unless repo convention requires them.
- Ask up to 3 clarifying questions before coding if requirements, data model impact, integration behavior, or extension point choice is unclear.
