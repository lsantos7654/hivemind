## TODO

- [X] simplify to only use opencode
- [X] enabling/disabling an expert via the tui should send an event and all clients should be updated accordingly
    - [X] currently opening a new session still shows disabled experts. Current solution involves restarting the server
    - post-mutation hook registry (`hooks.py`) now fires `/global/dispose` automatically from every ingress (CLI/TUI/MCP). MCP path accepts the session interrupt; see `HIVEMIND.md` for the abort-and-continue flow.
- [ ] add to mcp server ability to pick a specific version/tag/commit
    - `refresh_agent` fetches latest only; `switch-version` is CLI-only. Want an MCP `switch_version(name, commit)` tool.
- [ ] add background agents to workflow (plugin)


- [-] should notes.md | memory.md | short/long_memory.md be part of the agent class?
    - [ ] per-agent memory tree at `~/.config/opencode/hivemind/memory/<name>/` — every agent gets `MEMORY.md` + `short_memory.md` + `long_memory.md`. Memory section appended to each deployed `agents/<id>.md` explains the convention (threshold ~400 lines; short → long consolidation is prompt-level).
    - [X] under this paradigm each session is just like an object being instantiated, while the agent/expert is like a class in a way. The long term memories are stored at the expert level, under user config not under hivemind itself.
- [-] the orchestrator itself should have memories that it can keep track of under `~/.config/opencode/`
    - scaffolding done: `_orchestrator/` dir created by `lifecycle.bootstrap_workspace()` via `agents.memory.ensure_orchestrator_memory()`.
    - still need: opencode rules snippet that instructs the orchestrator to read/write it (currently the dir exists but nothing tells main to use it).
- [X] where is session data and plans stored today?
- [-] currently we have 2 ways of running hivemind with and without a server, should we implement 2 strategies for this, since they can effect some of the other features we have implemented
    - `runtime.RuntimeContext` (attached / detached / test) scaffold exists; detected once at ingress startup via `is_server_running()`.
    - downstream callers still auto-behave based on `get_server_url()` returning `None`. Explicit mode-dispatch in listeners not wired yet.
- [X] should we simplify the mcp server given the new abstraction?
    - unified lifecycle tools: `list_agents`, `show_agent`, `enable_agent`, `disable_agent`, `delete_agent`, `refresh_agent`. Kind-specific creators retained (`create_git_expert`, `create_team`). `_MUTATION_TOOLS` dispatcher hook removed — domain mutations fire `hooks.fire_post_mutation()` themselves.


- [ ] update exit as well
```bash
╰─❯ hivemind
▄
█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀█ █▀▀█
█  █ █  █ █▀▀▀ █  █ █    █  █ █  █ █▀▀▀
▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀

Session   Bazel aspects explained
Continue  opencode -s ses_253253768ffeoC4SBtauvfRXL7
```


## Follow-ups from the refactor

Out of scope for the layering refactor, noted in `refactor.md` / `CONTEXT.md`:

- [ ] split `opencode.py` into `AgentFormatter` / `AgentDeployer` / `InstanceNotifier` if it grows further (flagged by `expert-design-patterns-for-humans`; cheap to do later, not urgent now).
- [ ] serve experts as dynamic MCP tools instead of `agents/*.md` files. Would use `notifications/tools/list_changed` on the live stdio channel and eliminate the `/global/dispose` race entirely. Flagged by `expert-opencode` as the cleanest long-term fix. Large refactor — agent bodies would need to be expressible as tool schemas, which is a poor fit for markdown knowledge docs.
- [ ] opencode-side file watcher on `{agents,agent}/**/*.md` — would also eliminate the race, but requires an opencode change (not a hivemind one). Flagged by `expert-system-design-primer`.


## Wont Do

- [X] after enabling an expert the session is interrupted and I need to manually continue, ideally it would be nice if this wasn't the case.
    - confirmed structural via opencode source (`mcp/index.ts:527-548`, `ConfigAgent.load`): the only invalidation primitive opencode exposes tears down the in-flight tool-call state. Accepted. Documented in `HIVEMIND.md` so main warns the user before any mutation tool call and verifies state with a read-only call after `continue`.



can you consult the bazel expert and give me a rundown on how aspects work
