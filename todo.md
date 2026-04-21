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


- [X] update exit as well — exit-screen `Continue opencode -s ...` rewritten to `Continue hivemind -s ...` via `//third_party/patches/0001-rewrite-exit-continue-to-hivemind.patch`. The OPENCODE wordmark is also rebranded to HIVEMIND via `0002-rebrand-logo-to-hivemind.patch` (covers both the home-screen `<Logo />` component and the exit-screen `cli/ui.ts:wordmark`).

- [X] after enabling an expert the session is interrupted and I need to manually continue, ideally it would be nice if this wasn't the case.
    - resolved by `//third_party/patches/0004-add-reload-agents-endpoint.patch`: adds `POST /global/reload-agents` to opencode that re-reads `agents/*.md` for every active instance via `Config.invalidateState()` + `Agent.reload()`, neither of which calls `Instance.dispose()`. MCP subprocesses survive. Hivemind switched `notify_instance_reload` to the new endpoint. `HIVEMIND.md` and `CLAUDE.md` updated to drop the abort-and-continue warnings.

- [X] hardening defaults baked into the engine — `share="disabled"`, `autoshare=false`, `autoupdate=false`, `server.hostname="127.0.0.1"`, `bash.sudo *: deny` are now zod schema defaults in the bundled engine via `//third_party/patches/{0005,0006}-*.patch`. `opencode/config/defaults.json` shrunk to just the path-token permissions (which still need runtime substitution).


## Follow-ups from the refactor

Out of scope for the layering refactor, noted in `refactor.md` / `CONTEXT.md`:

- [ ] split `opencode.py` into `AgentFormatter` / `AgentDeployer` / `InstanceNotifier` if it grows further (flagged by `expert-design-patterns-for-humans`; cheap to do later, not urgent now).
- [ ] serve experts as dynamic MCP tools instead of `agents/*.md` files. Would use `notifications/tools/list_changed` on the live stdio channel. Largely obviated by the `/global/reload-agents` patch above, but the dynamic-tools form would still be cleaner. Large refactor — agent bodies would need to be expressible as tool schemas.
- [ ] opencode-side file watcher on `{agents,agent}/**/*.md` so hivemind doesn't need to call any endpoint at all. Now feasible as a patch on our fork (file-watcher infra exists at `packages/opencode/src/file/watcher.ts`, currently gated on `OPENCODE_EXPERIMENTAL_FILEWATCHER`). Could enable + scope to agents/. Tracked as a follow-up to the `/global/reload-agents` endpoint.



can you consult the bazel expert and give me a rundown on how aspects work

okay new rabbit hole and much more complexity but please humor me

what if we adopted bazel into this project, we pin the exact version of opencode we want to use. We can create diffs to maintain our own patch of opencode fully isolated. This would allow us to create more granular integration and have complete control over the code. The fork exists within the repo as a collection of diffs against a pinned version of opencode.

could you consult the bazel expert for this? Could you also do some research on which repos/rules exist for bazel that could help us with this?

Essentially we would be building the hivemind binary which wraps opencode
