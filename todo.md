# TODO

Ordered top-to-bottom by what's most actionable. Drop or refile items that no longer match reality.

- [ ] **MCP `switch_version(name, commit)` tool** — wrap the existing async `switch_version` in `agents/git_analyzed.py:502` with a thin tool in `mcp/tools.py`. Plumbing only.
- [ ] **Finish `RuntimeContext` dispatch** — `runtime.py` defines three modes (`attached` / `detached` / `test`), but the two callers at `opencode.py:488` and `opencode.py:515` still branch on `ctx.server_url is None`. Convert to explicit `ctx.mode` dispatch so test mode is distinguishable from detached.
- [ ] **User-supplied agents in `opencode/agents/`** — drop a markdown file in `/Users/santos/projects/hivemind_opencode/opencode/agents/`, run `hivemind redeploy`, and the agent gets symlinked into opencode's `agents/` and tracked in the catalog. Likely a third agent kind alongside `git_analyzed` and `roster_templated` — body-type "user_supplied" or similar — that just copies the file through with no AI analysis.
- [ ] **Verify "enable without restart" still works end-to-end** — `notify_instance_reload()` POSTs `/global/reload-agents` (patch 0004) which calls `Agent.reloadAll()` and re-scans `agents/*.md`. Both CLI (`cli.py:64-68`) and TUI (`tui/app.py:80-92`) register listeners that fire on every mutation. User reports they recall this working previously and may now be regressed; needs an end-to-end test (enable expert via `hivemind tui`, immediately call `Task(subagent_type=...)` in an attached opencode TUI without restarting).

---

## Larger conversations needed

- [ ] **Memory architecture** — orchestrator memory rules, memory daemon/compaction, expert memory hygiene. Need a planning conversation before action. Touches: `_orchestrator/` directory scaffolding (currently created by `lifecycle.py:249` but no rules text in `HIVEMIND.md` instructs the orchestrator to use it), expert memory directives in deployed `agent.md` files, possible background agent for memory consolidation.

---

## Closed

- [x] **MCP cross-session reference tool** — done. `send_message` MCP tool at `mcp/tools.py:222` POSTs to per-session inbox (patch 0007). Inbox queues if busy, delivers when idle. `list_sessions` finds targets.
- [x] **Background agents** — done via `Task(background=true)` in patch 0010 (formerly 0011). Result buffered on parent session, retrieved via `read_task_result` tool. Cascade cancellation when parent is cancelled.
- [x] **Jinja templates with editable AI-generated sections** — done via `expertise.md` and `description.md`. Both are preserved across `hivemind expert update` runs (`git.py:163-171`, `analysis.py:46`). Edit them by hand, the next AI re-analysis won't overwrite.

---

## Dropped / reframed

- ~~**Rename `commands` → `skills`**~~ — these are NOT the same thing in opencode. `Command` (`dev/opencode/.../command/index.ts`) is the slash-command system loaded from `/.opencode/command*/`. `Skill` (`dev/opencode/.../skill/index.ts`) is a separate system loaded from `skills/**/SKILL.md`. Renaming would lose the distinction. If the goal is to expose hivemind agents as either user-invocable, file a fresh item for "expose hivemind agents as opencode skills" or "as opencode commands."
- ~~**opencode file watcher on `agents/**/*.md`**~~ — superseded. `/global/reload-agents` (patch 0004) handles the use case. If "enable without restart" turns out to be regressed (see active item above), fix it there rather than introducing a watcher.



okay forget thread 5 keep as is
thread 4 - this has already been decomposed to skills, take a look at current state
thread 3 - option b, no external dependencies, all providers need to be managed by opencode only. how we should implement this gets interesting. The subagent model is preferable because nothing runs without proper insight. If the daemon is tied to a session I can look into it and kill if necessary. Otherwise I really like option c, my fear is that we have a rogue agent doing stuff without our knowledge managed by another background daemon the server. I guess this is fine if it has very explicit commands and can't execute anything. I would want this to be launched in an event based way. like if short term memory exceeds x size trigger the daemon agent.
