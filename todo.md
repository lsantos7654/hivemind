# TODO

Ordered top-to-bottom by what's most actionable. Drop or refile items that no longer match reality.

- [ ] **Verify "enable without restart" works end-to-end** — patch 0016 (`Extend reload-agents to invalidate Skill and Command state`) extends `/global/reload-agents` so it now also invalidates Skill + Command caches in addition to Agent state. The new engine binary is in place. To verify, restart your current opencode session, then drop a SKILL.md / command / agent file in `opencode/{skills,commands,agents}/`, run `hivemind redeploy`, and confirm it shows up without another restart.


---

## Larger conversations needed

- [ ] **Memory architecture** — orchestrator memory rules, memory daemon/compaction, expert memory hygiene. Decisions surfaced so far:
  - Provider model: option (b) "no external deps, all providers managed by opencode only." Subagent model preferred over external daemon — nothing runs without orchestrator insight, and a session-tied daemon can be inspected/killed via the TUI.
  - Concern: a rogue agent doing work without our knowledge. Mitigations: explicit-commands-only, no shell execution, event-triggered (not always-on).
  - Trigger model: event-based, e.g. "short-term memory exceeds N lines → spawn the daemon agent for compaction."
  - Touches: `_orchestrator/` directory scaffolding (created by `lifecycle.py:249`, no rules text in `HIVEMIND.md` instructs the orchestrator to use it yet); expert memory directives in deployed `agent.md` files; possible background agent for memory consolidation.
  - Still need: full design conversation before implementation.

---

## Closed

### Patch hygiene

- [x] **Phase 1 patch consolidation** — squashed 18 code patches → 13 (commit `7d40f1d`). 0019+0020 → WS presence; 0008+0009 → Session.fork extensions; 0011+0013+0015+0016 → Background Task lifecycle.

### Skills / commands / user agents

- [x] **Skills wiring (`opencode/skills/`)** — drop `<name>/SKILL.md`, run `hivemind redeploy`, opencode picks it up. Symlinked into `~/.config/opencode/skills/` on every redeploy. (`fab5b1e`)
- [x] **Commands deployed by `redeploy`** — was previously only deployed by `hivemind init`. Now `redeploy_all_agents()` re-runs `init_dirs()` so commands stay in sync. (`fab5b1e`)
- [x] **User-supplied agents in `opencode/agents/`** — drop a markdown file, run `hivemind redeploy`, agent lands as a `user_supplied` catalog entry (unlisted). `enable_agent` to deploy. (`fab5b1e`)
- [x] **`hivemind-cross-session` skill** — pulled cross-session messaging out of HIVEMIND.md into a load-on-demand skill.
- [x] **`hivemind-expert-management` skill** — catalog states + mutations + workflows pulled out of HIVEMIND.md into a skill. HIVEMIND.md now points to it.
- [x] **`/hivemind_generate_team` slash command** — scopes a worktree, finds tech deps, ensures relevant experts exist + enabled, bundles them into a project team.
- [x] **`/hivemind_sync` slash command** — lighter sibling of `/hivemind_generate_team`: scopes the worktree (including single-tool version pins like `.bazelversion`), proposes which experts to enable, create, or `switch_version` so the catalog matches the project's pinned versions; executes only on confirmation. No team is created.
- [x] **`/list_sessions` slash command** — renders a tree of live sessions and their subagents on demand.
- [x] **HIVEMIND.md trim** — 231 → ~175 lines after extracting cross-session and catalog mechanics into the two skills above.

### MCP tools

- [x] **`ref_name` provenance for ref-less expert adds** — `prep_create_expert` now resolves `origin/HEAD` after clone and stores the default branch (e.g. `"main"`) when no `--ref` is passed, so the catalog always carries provenance instead of leaving `ref_name=""`. One-shot migration in `bootstrap_workspace` backfills existing entries (skips silently when the repo isn't cloned). Removes the `git describe` improvisation that drove `/hivemind_sync`'s "close enough" group.
- [x] **MCP `switch_version(name, commit)` tool** — wraps the existing async `switch_version` in `agents/git_analyzed.py`. (`fab5b1e`)
- [x] **MCP cross-session reference tool** — done via `send_message` (`mcp/tools.py:222`) backed by per-session inbox (patch 0007).
- [x] **MCP `delete_session(session_id)` tool** — hard-removes a subagent session (recursively, after aborting any in-flight prompt). Fires `session.deleted` so the parent's footer subagent pill auto-decrements and `list_sessions` no longer shows it. Replaces the broken `archive_session` design that only flipped a never-read flag.

### Engine

- [x] **`/global/reload-agents` covers skills + commands** — patch 0016 extends the endpoint so adding a SKILL.md / commands/*.md doesn't require an opencode restart.
- [x] **Background agents** — `Task(background=true)` in patch 0010, results buffered on parent session and pulled via `read_task_result`. Cascade cancellation when parent aborts.

### Code quality

- [x] **Finish `RuntimeContext` dispatch** — `opencode.py:notify_instance_reload()` and `_server_url()` now dispatch on `ctx.mode` with `assert_never` exhaustiveness instead of branching on `ctx.server_url is None`. Test mode is now distinguishable from detached.
- [x] **Jinja templates with editable AI-generated sections** — `description.md` and `expertise.md` are preserved across `update_agent` runs (`git.py:163-171`).

---

## Dropped / reframed

- ~~**Rename `commands` → `skills`**~~ — these are NOT the same thing in opencode. `Command` is the slash-command system loaded from `/.opencode/command*/`. `Skill` is a separate system loaded from `**/SKILL.md`. Renaming would lose the distinction.
- ~~**opencode file watcher on `agents/**/*.md`**~~ — superseded. `/global/reload-agents` (patch 0004 + 0016 extension) handles the use case across agents, skills, and commands. If a regression appears, fix it there rather than introducing a watcher.
