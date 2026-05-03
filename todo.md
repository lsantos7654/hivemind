# TODO

Ordered top-to-bottom by what's most actionable. Drop or refile items that no longer match reality.

- [ ] **MCP `switch_version(name, commit)` tool** — wrap the existing async `switch_version` in `agents/git_analyzed.py:502` with a thin tool in `mcp/tools.py`. Plumbing only.
- [ ] **Orchestrator memory prompt snippet** — `_orchestrator/` is already scaffolded by `agents.memory.ensure_orchestrator_memory()`; missing piece is the rules text in deployed opencode config that tells main to read/write it.
- [ ] **Finish `RuntimeContext` dispatch** — `current_context()` is wired through `opencode.py`, but call sites still branch on `ctx.server_url is None` rather than `ctx.mode`. Convert the remaining checks to explicit mode dispatch.
- [ ] **Rename `commands` → `skills`** — confirm semantic equivalence with opencode's skills concept, then rename.
- [ ] **MCP cross-session reference tool** — built on the per-session inbox added by patches `0007` / `0008`.
- [ ] **Add `/agents` support** — clarify intended scope (opencode's own `/agents` path vs hivemind's `agents/` symlink) before starting.
- [ ] **Background agents via opencode `/plugins`** — depends on the plugin API surface.
- [ ] **Jinja templates with editable AI-generated sections** — let templates evolve without re-analysing every expert.
- [ ] **opencode file watcher on `agents/**/*.md`** — patch to enable `OPENCODE_EXPERIMENTAL_FILEWATCHER` scoped to agents/. Largely obviated by `/global/reload-agents`, but removes the HTTP poke.



- [ ] `daemon` memory management background agent to manage short and long term memories
- [ ] expose list sessions as a command `/list_sessions`
