# Memory Compaction Daemon

How hivemind keeps per-agent memory bounded without burning context
budgets or shifting work onto the orchestrator.

## What it does

Every hivemind agent (experts, team leads, the orchestrator) writes
to its own memory tree at
`~/.config/opencode/hivemind/memory/<agent>/`:

```
<agent>/
├── short_memory.md   # current scratchpad — written after every reply
├── long_memory.md    # consolidated durable knowledge
└── <topic>.md        # topic files with descriptive filenames
```

When an agent's `short_memory.md` crosses a byte threshold (default
8 KB, configurable in `hivemind.json:memory.compaction_threshold_bytes`),
the **memory-compaction daemon** is auto-spawned as a depth-1 sibling
of the writer under main. The daemon is a `system_templated` agent
running on a lightweight model (`anthropic/claude-haiku-4-5`); it
runs one compaction pass — promoting durable entries to
`long_memory.md` (or topic files), pruning the short — then exits.

Spawning is **event-driven via a post-write hook in opencode**, not
an orchestrator instruction or external scheduler. Neither the
orchestrator nor the writing expert has to remember to invoke it.

## Story (concrete example)

You ask main: *"ask the bazel expert how `bzlmod` resolves
transitive dependencies."*

```
ses_main
└── ses_bazel_xyz   (subagent_type=bazel)
```

The bazel expert does its work, then writes a new entry to its
`short_memory.md`. The file is now 8,400 bytes. Threshold crossed.

Inside opencode, the `tool.execute.after` flow calls
`Plugin.notifyFileWrite`, which dispatches to the in-tree
hivemind-memory plugin. The plugin:

1. Reads the threshold from `hivemind.json` (cached, mtime-invalidated).
2. Looks up the writer session via `client.session.get(sessionID)` —
   one typed call, no chain walking.
3. Recursion guard: if `writer.agent === "hivemind-memory-daemon"`,
   skip. (The daemon writes to memory too; we don't want recursion.)
4. Computes `mainID = writer.parent_id ?? sessionID` — depth-1
   invariant means the writer is either main itself or a direct
   child of main. Single lookup, deterministic.
5. Spawns the daemon: `client.session.create({parent_id: mainID,
   agent: "hivemind-memory-daemon", title: "compact memory: bazel",
   metadata: { triggered_by_session, target_agent, triggered_at_bytes }})`.

Now the session tree shows:

```
ses_main
├── ses_bazel_xyz       (bazel expert — completed)
└── ses_daemon_pqr      (compact memory: bazel — running)
```

Main's TUI subagents pill ticks from 1 to 2 briefly while the daemon
runs. The daemon reads `short_memory.md`, lists the directory for
context, decides which entries are durable vs ephemeral, writes
back atomically, then exits. Because the daemon's `agent.md`
declares `ephemeral: true`, the engine deletes its session as soon
as the runner reaches idle on the terminal turn — the pill drops
back to 1 **and** the `compact memory: bazel` entry vanishes from
the subagent tree. The compaction artifacts on disk
(`long_memory.md`, topic files) are untouched; only the in-memory
session record goes away.

## Architectural commitments

- **Daemon is a `system_templated` agent** (existing kind). No new
  body class. Hivemind-managed singleton, auto-seeded into the
  catalog on bootstrap and redeploy.
- **`memory_enabled = False`** comes from the body protocol —
  `Agent.deploy()` skips the memory-tree scaffold and the
  memory-section append for the daemon.
- **Auto-spawn via opencode plugin**, not orchestrator instructions
  or external schedulers.
- **Spawn site is depth 1 under main** (sibling of the writer),
  found via one typed `parent_id` lookup. No chain walking.
- **Threshold is in bytes**, configurable in `hivemind.json`.
- **Recursion guard** via `session.agent === "hivemind-memory-daemon"`.
- **Structured attribution** — `metadata.triggered_by_session`,
  `target_agent`, `triggered_at_bytes` on every spawn. No string
  parsing, queryable from any observer (TUI session tree, MCP
  `list_sessions`, future tooling).
- **One-shot** — daemon completes one pass and exits. No loop, no
  cron, no external process.
- **Ephemeral session** — daemon's frontmatter declares
  `ephemeral: true`, and the auto-spawn plugin passes
  `ephemeral: true` explicitly so the call site documents the
  intent. Engine deletes the session on terminal state
  (completed | failed | cancelled). The subagent tree never
  accumulates `compact memory: <agent>` corpses no matter how
  many threshold-crossing writes you do per day.
- **Restricted permissions** — daemon's frontmatter scopes its
  Read/Write/Edit to `~/.config/opencode/hivemind/memory/**`
  exclusively. No Bash, no Task, no shell, no network.

## Phases that landed

| Phase | What |
|---|---|
| 1 | Cleanup: drop `notes.md` infra, drop `MEMORY.md` index, add `memory.compaction_threshold_bytes` to `hivemind.json`, add "Main session memory" paragraph to HIVEMIND.md |
| 2 | Engine patches: 0018 (`metadata` JSON column on session) + 0019 (`onFileWrite` hook with pattern filtering + hivemind-memory plugin) |
| 3 | Daemon agent: `templates/agents/hivemind-memory-daemon.md.j2` + two `_seed_system_templated` call sites in `lifecycle.py` |
| 4 | Auto-spawn plugin: `dev/opencode/.../plugin/hivemind-memory.ts` registered as an internal plugin |
| 5 | Tests: 11 new engine tests (`bun:test`) + 14 new Python tests (`pytest`) |
| 6 | Ephemeral cleanup: patches 0020 (SDK regen) + 0021 (`ephemeral` schema column, terminal-state finalizers, Task tool plumbing, frontmatter resolution); daemon template + auto-spawn callsite both flag `ephemeral: true` |

## Files

### New

- `src/hivemind/templates/agents/hivemind-memory-daemon.md.j2` —
  daemon agent template
- `tests/test_memory_daemon.py` — Python coverage
- `dev/opencode/packages/opencode/migration/20260507120000_session_metadata/migration.sql`
  — schema migration
- `dev/opencode/packages/opencode/src/plugin/hivemind-memory.ts` —
  auto-spawn plugin
- `dev/opencode/packages/opencode/test/session/metadata.test.ts` —
  metadata column tests
- `dev/opencode/packages/opencode/test/plugin/file-write-hook.test.ts`
  — hook API tests
- `dev/opencode/packages/opencode/test/plugin/hivemind-memory.test.ts`
  — auto-spawn behavior tests
- `third_party/patches/0018-Session-metadata-column.patch`
- `third_party/patches/0019-File-write-hook-hivemind-memory-compaction-auto-spaw.patch`
- `dev/opencode/packages/opencode/migration/20260508023927_session_ephemeral/migration.sql`
  — schema migration adding the `ephemeral` column
- `dev/opencode/packages/opencode/test/session/ephemeral.test.ts`
  — round-trip + finalizer tests (5 tests)
- `dev/opencode/packages/opencode/test/tool/task-ephemeral.test.ts`
  — Task tool override + frontmatter default tests (5 tests)
- `tests/test_ephemeral_invariants.py` — pin daemon + curator
  templates declare `ephemeral: true`, HIVEMIND.md docs the
  feature, skills mention it (5 tests)
- `third_party/dep_patches/0020-SDK-gen-ephemeral-on-Session-create-fork-inputs.patch`
- `third_party/patches/0021-Ephemeral-subagent-sessions.patch`

### Modified

- `src/hivemind/agents/memory.py` — drop `MEMORY.md` scaffolding
- `src/hivemind/agents/roster_templated.py` — drop notes-stub helpers
- `src/hivemind/lifecycle.py` — seed daemon in `bootstrap_workspace` +
  `redeploy_all_agents`
- `src/hivemind/models.py` — add `MemoryConfig`
- `src/hivemind/templates.py` — drop `expert_notes_template` /
  `team_lead_notes_template`
- `src/hivemind/templates/memory_section.md.j2` — drop `MEMORY.md`
  references; describe discovery via filename
- `src/hivemind/templates/team_lead.md.j2` — drop `notes.md`
  references; route off member memory trees
- `HIVEMIND.md` — drop notes references; add "Main session memory"
  paragraph
- `hivemind.json` — add `memory.compaction_threshold_bytes`
- `dev/opencode/.../session/session.sql.ts` — `metadata` column
- `dev/opencode/.../session/index.ts` — `Info.metadata` schema +
  `Session.create({metadata})`
- `dev/opencode/.../session/projectors.ts` — pass-through metadata
- `dev/opencode/.../tool/{write,edit}.ts` — call
  `Plugin.notifyFileWrite` post-write
- `dev/opencode/.../plugin/index.ts` — `notifyFileWrite` runtime +
  register `HivemindMemoryPlugin`
- `dev/opencode/packages/plugin/src/index.ts` — `Hooks.onFileWrite`
  type
- `src/hivemind/templates/agents/hivemind-memory-daemon.md.j2` —
  declare `ephemeral: true` in frontmatter
- `dev/opencode/packages/opencode/src/plugin/hivemind-memory.ts` —
  pass `ephemeral: true` on the auto-spawn `client.session.create`
- `dev/opencode/packages/opencode/test/plugin/hivemind-memory.test.ts`
  — assert spawned daemon session has `ephemeral === true`

### Deleted

- `src/hivemind/templates/expert_notes.md.j2`
- `src/hivemind/templates/team_lead_notes.md.j2`

## What you can do as a user

Mostly nothing — that's the point. The daemon is invisible until
needed and self-correcting when triggered. But:

- **See it run** — while active, the daemon shows in main's session
  tree with title `compact memory: <agent>` and the subagents pill
  ticks up briefly. Once the compaction pass completes the session
  is auto-deleted; the pill returns to baseline and the entry
  disappears from the tree. If you blink, you might miss it
  entirely — the daemon's whole life is usually under a second.
- **Drill into it (while running)** — ctrl-x-down on the daemon's
  session entry shows what it's doing. Only works while the daemon
  is alive; once it finishes the session record is gone. The
  compaction artifacts (`long_memory.md` and topic files) are the
  durable trace.
- **Kill it** — standard subagent kill. The session deletes itself
  after cancellation just like a clean exit (cancelled is a
  terminal state). Idempotent: the next over-threshold write
  triggers a fresh daemon. Cancelling main also cascades-cancels
  the daemon (existing patch 0010 behavior).
- **Tune the threshold** — edit
  `hivemind.json:memory.compaction_threshold_bytes`. Plugin
  picks up changes via mtime invalidation; no restart needed.
- **Disable entirely** — `hivemind expert disable
  hivemind-memory-daemon`. The plugin still tries to spawn but
  fails gracefully (logged, not propagated to the originating
  write).
- **Inspect attribution** — every daemon's `session.metadata` has
  `{triggered_by_session, target_agent, triggered_at_bytes}`. Useful
  for tracing why and when compaction happened.

## What's deliberately NOT in scope

- **Compaction quality.** The LLM decides what's durable vs
  ephemeral. Tests verify the daemon writes valid output and
  doesn't corrupt files; we don't grade its choices.
- **Cross-machine behavior.** Single-host by design.
- **Async or cron scheduling.** Triggers are event-only — the
  post-write hook fires synchronously inside opencode.
- **Centralized model config in `hivemind.json`.** The daemon's
  model lives in its template (matching the curator/crawler
  convention). If centralizing models per-role becomes a real
  need, that's a separate refactor across all `system_templated`
  templates.

## References

- Plan files (now superseded by this doc): the memory-daemon plan
  and the ephemeral-spawns plan, both folded into the sections above.
- Patch files:
  - `third_party/patches/0018-Session-metadata-column.patch`
  - `third_party/patches/0019-File-write-hook-hivemind-memory-compaction-auto-spaw.patch`
  - `third_party/dep_patches/0020-SDK-gen-ephemeral-on-Session-create-fork-inputs.patch`
  - `third_party/patches/0021-Ephemeral-subagent-sessions.patch`
- Daemon template: `src/hivemind/templates/agents/hivemind-memory-daemon.md.j2`
- Auto-spawn plugin: `dev/opencode/packages/opencode/src/plugin/hivemind-memory.ts`
- Test coverage:
  - `tests/test_memory_daemon.py` (14 tests)
  - `tests/test_ephemeral_invariants.py` (5 tests)
  - `dev/opencode/packages/opencode/test/session/metadata.test.ts` (3)
  - `dev/opencode/packages/opencode/test/session/ephemeral.test.ts` (5)
  - `dev/opencode/packages/opencode/test/plugin/file-write-hook.test.ts` (5)
  - `dev/opencode/packages/opencode/test/plugin/hivemind-memory.test.ts` (3)
  - `dev/opencode/packages/opencode/test/tool/task-ephemeral.test.ts` (5)
- Commits:
  - `ec7d98d` — *feat: Memory-compaction daemon with auto-spawn*
  - `2c9277c` — *feat: Ephemeral subagent sessions*
