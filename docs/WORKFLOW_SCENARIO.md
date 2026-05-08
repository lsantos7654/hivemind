# Hivemind Reference Workflow: One Project, From Day 1 to Hotfix

This is the canonical scenario hivemind is built for. It exists so:

- **Design discussions** can ground themselves in a real story instead
  of abstractions.
- **Templates and skills** (`templates/hivemind.md.j2`,
  `opencode/commands/*`, `opencode/skills/*`) can point at this doc as
  the authoritative narrative for *why* each capability exists.
- **Tests** can be derived from the `▶ Test:` callouts inline at
  every beat — every callout names a behavior an integration test
  should exercise.

The story spans one project from a fresh checkout through to a
post-merge hotfix. Every hivemind feature shipped today appears in
sequence; nothing aspirational is included. If a beat is here, it
works.

## Cast

**The user.** A single human at one machine. Has been running
hivemind across many projects over the past year — their orchestrator
has accumulated a substantial cross-project memory tree that survives
each project's start and end.

**The orchestrator.** A long-lived hivemind session running in a tmux
window over the user's `main` worktree. Persists across days,
projects, and tmux restarts. Its memory tree
(`~/.config/opencode/hivemind/memory/_orchestrator/`) holds project
conventions, architectural decisions, and pinned facts accumulated
across every project the user has worked on.

**Branch sessions.** One hivemind session per Graphite stack PR, each
attached to its own git worktree in its own tmux window. Address
work by branch; talk to siblings; outlive their TUI windows.

**Experts.** Long-lived domain agents in the catalog
(`expert-rust`, `expert-bun`, `expert-bazel`, `expert-postgres`).
Each has its own memory tree. Spawned on demand by branch sessions
and by the orchestrator; resumable across days.

**Hivemind worker agents.** Three system-templated agents that exist
to keep the catalog and memory clean:

- `hivemind-expert-curator` — runs the slow catalog operations
  (add expert, update expert, switch version, create team) in its
  own background-mode session. Always ephemeral.
- `hivemind-memory-daemon` — auto-spawned by the engine's
  `file.write` hook when an agent's `short_memory.md` crosses the
  byte threshold. One-shot compaction pass, then vanishes. Always
  ephemeral.
- `hivemind-crawler` — fetches external docs sites for an existing
  expert (vendor docs, API references hosted separately).

## Project

A polyglot service called **prism**:

```
prism/
├── Cargo.toml          Rust workspace (core library + RPC server)
├── crates/
│   ├── prism-core/     Shared domain types + business logic
│   └── prism-rpc/      Tonic gRPC server, Diesel ORM, Postgres-backed
├── package.json        Bun workspace (web frontend)
├── apps/
│   └── web/            React + Bun preferences panel
├── MODULE.bazel        Bazel workspace, pinned to bazel 8.5.1
├── BUILD.bazel
├── docker-compose.yml  Local Postgres + adminer
└── migrations/         Diesel migrations (Postgres)
```

The user is starting work on a new feature: **user-scoped preferences
persistence**. The feature requires changes across the schema, the
Rust gRPC API, the Bun frontend, and the e2e test suite. They've
sketched it as a five-PR Graphite stack:

| PR | Branch | Scope |
|---|---|---|
| 1 | `pr1/schema` | Postgres migration: `user_preferences` table |
| 2 | `pr2/api`    | Rust gRPC: `Get/Set Preferences` endpoints |
| 3 | `pr3/web`    | React preferences panel; wires PR2 |
| 4 | `pr4/e2e`    | Bun e2e tests across PR2 + PR3 |
| 5 | `pr5/docs`   | Changelog, READMEs, OpenAPI export |

PR2 depends on PR1, PR3 depends on PR2, PR4 depends on PR2+PR3,
PR5 depends on the merged base. Linear-ish: every "downstream"
reference in the story means *the consumer of what I'm building*,
matching Graphite's convention.

---

## Phase 1 — Day 1: scope, set up, generate the team

Monday morning. The user has just `gt sync`-ed a fresh `prism` checkout.
There is one tmux window open: the orchestrator, which the user
attached to from their last project's session. It still remembers
everything it knew yesterday.

```
tmux ─┬─ window 0  → ~/work/prism (main)   TUI: orchestrator
```

The user's first move: scope the project, generate any missing
experts, bundle the result as a project team. They type into the
orchestrator:

```
/hivemind_generate_team
```

The orchestrator picks up the slash command. Walking through what
happens inside:

1. **Scope the worktree.** The orchestrator reads `package.json`,
   `Cargo.toml`, `MODULE.bazel`, and `docker-compose.yml`. Extracts
   the dependency tuples: `bun@1.3.11` (frontend),
   `react@18.3.1`, `cargo` (workspace), `tonic@0.12`,
   `diesel@2.1`, `bazel@8.5.1`, `postgres:16` (compose).
2. **Identify which experts are needed.** Maps tuples to canonical
   expert names: `expert-bun`, `expert-react`, `expert-rust`,
   `expert-tonic`, `expert-diesel`, `expert-bazel`, `expert-postgres`.
3. **Check the catalog.** Calls `list_agents` (MCP, sub-second).
   Most experts already exist from prior projects:
   `expert-bun @ 1.3.11` ✓, `expert-react @ 18.3.1` ✓,
   `expert-rust ✓`, `expert-bazel @ 8.5.1` ✓,
   `expert-postgres @ 16` ✓. Two are missing:
   `expert-tonic`, `expert-diesel`.
4. **Spawn the curator to add the missing experts.** Two parallel
   background-mode `Task` calls:

   ```
   Task(subagent_type="hivemind-expert-curator", background=true,
        description="add tonic", prompt="add expert from
        https://github.com/hyperium/tonic at tag v0.12.x")
   Task(subagent_type="hivemind-expert-curator", background=true,
        description="add diesel", prompt="add expert from
        https://github.com/diesel-rs/diesel at tag v2.1.x")
   ```

   Each curator runs in its own session, clones the repo, runs the
   AI analysis pass, registers the expert in the catalog. Because
   the curator agent declares `ephemeral: true` in frontmatter, both
   sessions auto-delete on terminal state. The orchestrator's
   subagent tree briefly shows two curator entries; both vanish on
   completion. Total wall-clock: ~3 minutes.
5. **Bundle into a team.** The orchestrator calls
   `prep_create_team` (MCP) with roster
   `[expert-bun, expert-react, expert-rust, expert-tonic,
   expert-diesel, expert-bazel, expert-postgres]` and team name
   `prism`. The curator runs once more (background, ephemeral) to
   write the team-lead's per-member sections; on completion
   `finalize_create_team` deploys `team-lead-prism.md`.
6. **Enable the team.** Direct `enable_agent("team-lead-prism")`.
   Engine receives `/global/reload-agents`, picks up the new agent
   without disposing any session.

The orchestrator reports back in one paragraph: which experts were
already in the catalog, which were created, the team that was
assembled. Total wall-clock: ~5 minutes for a stack the user has
never set up before.

> **▶ Test:** `/hivemind_generate_team` end-to-end against a
> tmpdir worktree containing `package.json` + `Cargo.toml` +
> `MODULE.bazel`. Assert: missing experts created, existing
> experts left untouched, team-lead deployed and enabled, every
> curator session auto-deleted (subagent tree returns to baseline).

> **▶ Test:** Curator session has `ephemeral === true` on its
> session row. Two parallel curators do not race the catalog (no
> overlapping `hivemind.json` writes).

> **▶ Test:** `/global/reload-agents` is non-destructive. The
> orchestrator's MCP subprocess survives the team's enablement
> (no SIGTERM, no `Tool execution aborted`).

---

## Phase 2 — The stack lights up

The user creates the five worktrees with `gt create -m`. For each
worktree, they open a new tmux window, `cd` into it, and run
`hivemind`. Each TUI attaches to a fresh session scoped to that
branch's worktree.

```
tmux ─┬─ window 0  → main         TUI: orchestrator   (ses_orch_aaa)
      ├─ window 1  → pr1/schema   TUI: pr1 session    (ses_pr1_bbb)
      ├─ window 2  → pr2/api      TUI: pr2 session    (ses_pr2_ccc)
      ├─ window 3  → pr3/web      TUI: pr3 session    (ses_pr3_ddd)
      ├─ window 4  → pr4/e2e      TUI: pr4 session    (ses_pr4_eee)
      └─ window 5  → pr5/docs     TUI: pr5 session    (ses_pr5_fff)
```

Every TUI's footer shows the same number: `● 6 sessions`. The
orchestrator can confirm at a glance that all five branch sessions
plus itself are alive on this machine. The number comes from the
WebSocket presence channel (patch 0015) — each TUI maintains one
long-lived `/presence` connection; the server tallies the
deduplicated focus values across all clients.

> **▶ Test:** Boot N TUIs in N tmpdir directories; the presence
> count converges to N within 100 ms of the last TUI's mount. Kill
> any single TUI and the count drops by exactly 1 within a beat.

> **▶ Test:** Patch 0015's `_clients` map is keyed by underlying
> `ServerWebSocket`, not Hono's per-callback `WSContext` wrapper.
> An open WebSocket is the presence beacon; CLOSE frame triggers
> `onClose` synchronously. (Regression test: the dispatch had a
> bug where focus updates on Hono's wrapper looked like new
> connections.)

The user runs `/list_sessions` from the orchestrator. The TUI renders
the full tree:

```
ses_orch_aaa  Orchestrator                          (active 2s ago)
ses_pr1_bbb  pr1/schema                            (active 30s ago)
ses_pr2_ccc  pr2/api                               (active 28s ago)
ses_pr3_ddd  pr3/web                               (active 25s ago)
ses_pr4_eee  pr4/e2e                               (active 22s ago)
ses_pr5_fff  pr5/docs                              (active 20s ago)
```

No subagents alive yet — the team's just been seated.

---

## Phase 3 — Orchestrator dispatches work to every branch

The user, still in the orchestrator window, opens the GitHub PR for
PR1, copy-pastes a paragraph of design context, and types:

> "For each PR in the stack, fetch its review comments off GitHub,
> address them in-place where you can, and report back when done.
> Use the per-branch session for each."

The orchestrator parses the request. It doesn't try to do the work
itself — it has five sibling sessions for exactly this purpose. It
calls `send_message` five times, one per branch:

```python
# inside the orchestrator's tool sequence
for pr_id in [ses_pr1_bbb, ses_pr2_ccc, ses_pr3_ddd, ses_pr4_eee, ses_pr5_fff]:
    send_message(
        session_id=pr_id,
        message=f"Fetch review comments for your PR off GitHub, address what you can, and "
                f"send_message back to ses_orch_aaa with a short summary when done.",
    )
```

Each branch session receives the message via the per-session inbox
(patch 0007). Their TUIs flash the new turn into view. Each branch
agent picks up the work in its own window: `gh pr view`, walks the
comments, makes edits scoped to that worktree, runs the local checks.

The user can switch into any branch tmux window mid-task and watch
progress live. When each branch finishes, it sends a short summary
back to the orchestrator's session via `send_message`.

When all five replies have landed, the orchestrator has a stack-level
rollup it can return to the user as a single message.

> **▶ Test:** `send_message` from session A → session B causes
> session B's inbox to fire, regardless of whether B is currently
> idle or mid-turn. Multiple inbox entries deliver in arrival order.

> **▶ Test:** `send_message`-driven turns persist across TUI
> reconnect. If window B is closed mid-turn and reopened, the
> in-flight reply continues; the user sees its tail.

> **▶ Test:** Fan-out from the orchestrator to N siblings runs
> truly in parallel — each receiving session enters busy state
> within tens of ms of the others. There is no orchestrator-side
> serialization queue.

---

## Phase 4 — Deep design conversation with `expert-rust` (PR2)

Tuesday. The user is working in PR2 (`pr2/api`). They want to design
the gRPC layer carefully — specifically the interplay between
`tonic` (server framework), `prost` (protobuf serialization), and
`diesel` (ORM). The PR2 session spawns `expert-rust` (background mode
because the conversation will be ongoing):

```python
Task(
    subagent_type="expert-rust",
    background=true,
    description="design tonic+diesel interplay",
    prompt="""Design the gRPC service layer for prism's preferences API.
    Constraints: tonic for transport, prost for serialization, diesel for
    ORM. We need clean error mapping from diesel::result::Error to tonic::Status,
    and the protobuf types should not leak into the diesel models.
    Walk through the layered approach you'd recommend."""
)
```

The expert spawns at depth-1 under PR2 as a background subagent. PR2's
TUI footer shows `● 1 subagents`. The user keeps working on PR2's
boilerplate while the expert thinks.

A few minutes later, the expert returns its first message via the
ready-task `<system-reminder>` pipeline. The user reads
`read_task_result(task_id="ses_rust_xyz")` — a long, structured
analysis that recommends a `service` layer translating between
domain types and protobuf types, and a separate `repo` layer
wrapping diesel. The user replies in the rust expert's session
(via the standard "send_message into the subagent" path) with a
follow-up: "agreed. now sketch the error mapping."

The conversation continues. By end-of-day Tuesday the rust expert
has produced ~5 turns of deep analysis. The user copies a few
recommendations into the PR2 code, commits, and closes the laptop.

The expert's session ID — `ses_rust_xyz` — is now durable. It
persists in the database; the underlying runner has long since
finished its turn. The conversation lives on.

> **▶ Test:** Spawning an expert with `background=true` registers
> it in `SessionBackground` and returns immediately. Buffered
> result is consumable via `read_task_result`. Multi-turn extension
> via `send_message` into the subagent ID works.

> **▶ Test:** Closing the parent TUI mid-conversation does not
> dispose the expert subagent. The session row + message history
> survive process exit.

---

## Phase 5 — Resume the rust conversation, days later

Thursday. The user is back in PR2 (`pr2/api`) — they've implemented
the layered design and now want to revisit the error-mapping
question with the rust expert. They want **the same expert session**,
not a fresh one — it remembers the constraints, the layering, the
specific pieces of code already discussed.

```python
Task(
    subagent_type="expert-rust",
    task_id="ses_rust_xyz",                  # ← resume the Tuesday session
    description="error mapping followup",
    prompt="""I implemented the layered approach you suggested.
    The repo layer returns diesel::Result<T>; the service layer
    translates to tonic::Status. But I'm hitting cases where I want
    to surface diesel::Error::NotFound as tonic's NotFound but
    DatabaseError as Internal. Show me the conversion impl you'd write."""
)
```

The Task tool resolves: `task_id` is set, fetch that session
verbatim, no new fork. The rust expert picks up where it left off
on Tuesday — it remembers the user wanted to keep prost types out
of diesel models, it remembers it had already suggested a
`service::Error` enum at the boundary. It produces a focused
follow-up and an implementation sketch.

The expert's memory tree — separate from this one session — also
matters. Its `~/.config/opencode/hivemind/memory/expert-rust/`
already contains accumulated knowledge from prior projects:
"the user prefers `?` over `match` for Result propagation",
"this project uses `thiserror` not `anyhow`", etc. That knowledge
is loaded as the expert's memory section on every spawn,
including this resume. Session continuity gives moment-to-moment
context; memory tree gives long-arc context.

> **▶ Test:** `Task(task_id=...)` does not create a new session.
> The resumed session's parentID is unchanged; its message
> history is intact; its `time.updated` advances.

> **▶ Test:** `Task(task_id=..., ephemeral=true)` is rejected at
> the schema layer (resume + ephemeral are mutually exclusive).

> **▶ Test:** Expert memory tree (`long_memory.md` + topic files)
> is injected into the system prompt on every spawn — including
> resume — provided `memory: true` (default for experts).

---

## Phase 6 — Memory daemon cameo: per-expert (`expert-bun`)

Wednesday afternoon between Phases 4 and 5. The user has been
deep in `expert-bun` work on PR3 — multi-turn conversations
about Bun's bundler, HMR behavior, and React server-component
support. The bun expert has been writing notes to its
`short_memory.md` after every reply (standard memory contract:
the expert's reply turn ends with an append to short memory).

Mid-afternoon, that file crosses 8 KB. The threshold lives in
`hivemind.json:memory.compaction_threshold_bytes`. The engine's
`file.write` plugin hook (patch 0019) fires inside `tool.execute.after`,
matches the path against the configured pattern
(`**/hivemind/memory/**/short_memory.md`), and calls the in-tree
`HivemindMemoryPlugin`.

The plugin:

1. Reads the writer session via `client.session.get(ses_pr3_ddd)`.
2. Recursion guard: writer's agent is `expert-bun`, not the daemon
   itself — proceed.
3. Computes `mainID = writer.parent_id ?? writer.id`. For the
   bun expert running under PR3, the writer is the expert (depth-1
   subagent of PR3), so `mainID = ses_pr3_ddd`.
4. Spawns the daemon: `client.session.create({parent_id: ses_pr3_ddd,
   agent: "hivemind-memory-daemon", title: "compact memory: bun",
   metadata: {triggered_by_session: ses_pr3_ddd, target_agent: "bun",
   triggered_at_bytes: 8704}, ephemeral: true})`.

PR3's subagent pill ticks from 1 (the bun expert) to 2. A new entry
appears under PR3:

```
ses_pr3_ddd  (PR3)
├── ses_bun_qrs    expert-bun                    (idle — between turns)
└── ses_dmn_tuv    compact memory: bun           (running)
```

The daemon — running on the lightweight `claude-haiku-4-5` model with
`memory: false` (no recursion through its own memory section) — reads
`short_memory.md`, lists the directory for context, decides which
entries are durable vs ephemeral. It promotes a handful of facts to
`long_memory.md` ("project uses `bun --bun run` for type-stripping
TS at runtime; Bun.serve replaces tsx/ts-node here"), creates one
new topic file (`bundling.md` for the deep dive on the bundler's
HMR semantics), and writes the pruned `short_memory.md` back —
now ~1.5 KB.

Total daemon wall-clock: under a second. The runner reaches idle on
the terminal turn. Because the daemon's session was created with
`ephemeral: true`, the `onIdle` callback in
`SessionRunState` invokes `Session.remove(ses_dmn_tuv)` — the
session is deleted, and the `session.deleted` bus event fires. PR3's
TUI subagent pill drops back to 1, the daemon entry vanishes from
the subagent tree.

The compaction artifacts on disk (`long_memory.md`,
`bundling.md`) are untouched. Only the in-memory session record
goes away. The bun expert continues its conversation with the user
unaware.

> **▶ Test:** Write a 9 KB short_memory file as a non-daemon agent
> in a session under main. Within a beat, exactly one daemon
> session spawns under main with the right metadata. Once the
> daemon finishes, no daemon session remains in main's children
> list. Repeat 5x: the subagents pill never accumulates daemons.

> **▶ Test:** A second concurrent over-threshold write does NOT
> spawn a second daemon for the same target agent (the first is
> still alive). (TODO if not implemented: fold into a follow-up
> patch.)

> **▶ Test:** The daemon's session row has
> `metadata.triggered_by_session`, `target_agent`,
> `triggered_at_bytes`. The metadata is queryable via standard
> session inspection.

> **▶ Test:** Daemon session is `ephemeral === true`. Killing
> the daemon mid-pass also auto-deletes the session (cancelled is
> a terminal state).

---

## Phase 7 — Cross-session fork for context handoff (PR3 → PR4)

Wednesday evening. The user is in PR3 (`pr3/web`), wiring the React
preferences panel to the gRPC API surface. They hit an ambiguity:
the API can return either `null` or an empty object for "user has
no preferences yet". They want to know which case PR4's e2e tests
are expecting — that determines the right frontend handling.

The naive paths are slow:

- **Type into PR4's window directly** — but PR3's session would
  have to wait, and PR4's session has its own focus.
- **Ask PR4 via `send_message`** — pollutes PR4's history with a
  PR3 question, and the user has to wait for PR4 to surface the
  reply.

Better: fork PR4's session into a fresh ephemeral subagent under
PR3, ask the question once, get the answer in PR3's history, throw
the fork away.

```python
Task(
    subagent_type="explore",
    source_session_id="ses_pr4_eee",   # ← fork PR4's full history
    ephemeral=true,                    # ← throw it away when done
    description="check e2e contract",
    prompt="""Looking at the e2e tests you've written for the
    preferences API: what does your test expect when a user has
    no saved preferences? An empty preferences object, or null?"""
)
```

The Task tool's `source_session_id` path (patches 0008/0009)
calls `Session.fork({sessionID: ses_pr4_eee, parentID: ses_pr3_ddd,
ephemeral: true})`. The fork inherits PR4's full message history;
the source PR4 session is untouched. The new fork lives at depth-1
under PR3.

PR3's subagent pill ticks up. The forked subagent walks the e2e
test files PR4 has been working with — *those files are in the
fork's recall context because the original PR4 conversation
referenced them*. It reports back: "the e2e test asserts
`preferences === null` for a never-saved user; we explicitly
chose null over empty-object to disambiguate from
'all-defaults-cleared'."

The Task tool's return value lands in PR3's session as the
subagent's summary. PR3's runner reaches idle. Because the fork
was `ephemeral: true`, the runner's `onIdle` path deletes the
session. PR3's subagent pill drops back. PR4's subagent tree was
never touched. PR4's session continues unaware that a fork ever
existed.

> **▶ Test:** `Task(source_session_id=B, ephemeral=true)` from
> session A: a forked session F is created at depth-1 under A
> with B's history copied in. After the runner reaches idle, F
> is deleted. B is unmodified throughout (same `time.updated`,
> same children list).

> **▶ Test:** F can read files / call MCP tools as a fully-formed
> session in its own right. Its permission ruleset is B's
> permission OR'd with the Task-tool child overlay (deny todowrite,
> deny task by default).

> **▶ Test:** The Task tool's return value (summary) appears in
> A's message history even after F is deleted. The summary
> survives ephemeral cleanup.

---

## Phase 8 — Branches messaging branches (peer-to-peer)

Mid-day Thursday. The user is back in PR3, mid-implementation.
They realize the schema PR1 actually landed has slightly different
column names than what the design called for — PR1's reviewer
asked for `preferences_data` instead of `data`. PR3 needs to know
what the actual columns are before continuing.

There's no orchestrator in this loop. PR3's agent just asks
its peer:

```python
send_message(
    session_id="ses_pr1_bbb",
    message="""From PR3's session: I'm wiring up the preferences
    panel against PR2's API which talks to your migration. Can you
    confirm the final column names that landed? I'm seeing
    `preferences_data` in the migration sql — is that the actual
    column name we'll see in the API response, or does PR2 do
    a renaming? Reply via send_message to ses_pr3_ddd."""
)
```

PR1's session inbox fires. The PR1 agent had already finished its
own work earlier in the week — its session is idle. The inbox
delivery wakes it up via the same `_scheduleWakeUp` path used for
background-task readiness. PR1's agent reads its migration files,
confirms `preferences_data` is the final column name, and replies:

```python
send_message(
    session_id="ses_pr3_ddd",
    message="Final columns: preferences_data (jsonb), updated_at
    (timestamptz), user_id (uuid). PR2 does NOT rename — the API
    returns `preferences_data` as-is. The reviewer's reasoning:
    `data` was too generic across the schema."
)
```

PR3's inbox fires. The PR3 agent picks up, updates its frontend
mapper to expect `preferences_data`, and continues. The orchestrator
was not in this loop. The user, watching from the PR3 window, sees
the round trip happen in real time.

> **▶ Test:** Bidirectional `send_message` between two idle
> sessions: each delivery wakes the recipient and queues the
> message into its inbox. Both sessions independently advance
> turns; the message order is preserved per-session.

> **▶ Test:** `send_message` to a session that's mid-turn:
> the message lands in its inbox but does not interrupt the
> in-flight turn. The recipient picks it up on its next loop step.

---

## Phase 9 — Orchestrator pins a project convention

Thursday afternoon. The user, in the orchestrator, has just
heard back from PR3 about the column naming. They notice
something worth pinning: this project has chosen explicit-
prefixed column names everywhere in the schema, and that convention
should be respected by future spawns of *any* expert touching
this codebase.

The user types into the orchestrator:

> "remember: prism uses fully-qualified column names like
> `preferences_data`, never bare `data`. The reviewer is strict
> about this — flag it in any future schema changes."

The orchestrator picks up the cue. It writes to its own short
memory file at
`~/.config/opencode/hivemind/memory/_orchestrator/short_memory.md`:

```markdown
## prism — schema convention (2026-05-08)

Column names in `prism` migrations are fully-qualified, never bare:
`preferences_data` not `data`. Reviewer convention; PR1 landed this
way. When future PRs touch the schema, surface this constraint to
expert-postgres and expert-diesel proactively.

triggered_by: PR1↔PR3 column-name confirmation
```

Later that same day, the user pins a second item — a cross-PR
architectural decision:

> "remember: we're using tonic over tower-grpc for prism. The
> tonic+prost combination plays nicely with serde for our type
> boundary. If a future PR contemplates switching away from tonic,
> talk to expert-rust first — there's history."

The orchestrator appends:

```markdown
## prism — RPC stack decision (2026-05-08)

Chose `tonic` over `tower-grpc` for prism's gRPC layer. Reason:
tonic+prost integrates cleanly with serde at our type boundary;
tower-grpc would have required extra glue. expert-rust did the
analysis Tuesday in session ses_rust_xyz. Future PRs that
revisit RPC choice should `Task(task_id=ses_rust_xyz)` to read
the history before deciding.
```

These notes will survive the project. After prism ships and the
user moves on to next month's work, that orchestrator memory tree
still holds these entries — alongside conventions and decisions
from every project the user has worked on across the year. The
user's orchestrator is, in a very real sense, the long-term
memory of their working life.

> **▶ Test:** The orchestrator's short_memory.md grows with
> appended entries on cue. Entries include date, source PR /
> source session, and the rationale.

> **▶ Test:** Orchestrator memory is read by every spawn — when
> any subagent (expert or otherwise) starts under the orchestrator,
> the orchestrator's `_orchestrator/long_memory.md` and topic
> files are part of the orchestrator's system context. (This
> propagates project conventions implicitly.)

---

## Phase 10 — Mid-stream: `/hivemind_sync` updates `expert-bun`

Friday morning. The user notices Bun shipped 1.4.0 overnight, and
prism's `package.json` already auto-bumped to it via dependabot.
The user runs `/hivemind_sync` in the orchestrator:

```
/hivemind_sync
```

The orchestrator scopes the worktree (same as `generate_team`),
extracts dependency tuples, and compares them to the catalog's
pinned versions. It produces a proposal:

```
Proposed catalog actions for prism:

  switch_version  expert-bun       1.3.11 → 1.4.0
  (everything else is already at the pinned version; no other actions needed)

Apply? [y/n]
```

The user confirms. The orchestrator spawns the curator (background,
ephemeral) to do the slow work:

```python
Task(
    subagent_type="hivemind-expert-curator",
    background=true,
    description="bump bun to 1.4.0",
    prompt="run prep_switch_version + finalize_switch_version for
    expert-bun targeting tag 1.4.0",
)
```

The curator clones bun at 1.4.0, runs the AI re-analysis pass,
rotates the HEAD symlink. On completion the orchestrator receives
the result via `read_task_result`; the curator's session
auto-deletes (ephemeral); a `/global/reload-agents` POST refreshes
the engine's view of `expert-bun` without disposing any session.

PR3 — which has been spawning expert-bun all week — picks up the
new version on its very next spawn. No restart. No orchestrator
intervention beyond the initial `/hivemind_sync` confirmation.

> **▶ Test:** `/hivemind_sync` produces an accurate proposal for
> a worktree where exactly one expert has drifted from its
> pinned version. The proposal does not execute without
> confirmation.

> **▶ Test:** `switch_version` via the curator pipeline rotates
> the HEAD symlink atomically. A spawn racing the rotation
> never sees a half-rotated state.

---

## Phase 11 — Memory daemon cameo: orchestrator scope

Friday afternoon. Over the course of the week the orchestrator's
own `short_memory.md` has grown — every cross-PR coordination,
every pinned convention, every architectural decision has been
appended. The file crosses 8 KB.

The same hook fires. Same path: `file.write` →
`HivemindMemoryPlugin` → daemon spawn. But this time the writer
is the orchestrator itself. The plugin's `mainID` computation —
`writer.parent_id ?? writer.id` — resolves to `ses_orch_aaa`
(orchestrator has no parent; `parent_id` is null).

The daemon spawns at depth-1 under the orchestrator:

```
ses_orch_aaa  (Orchestrator)
└── ses_dmn_xyz   compact memory: _orchestrator   (running)
```

It reads the orchestrator's memory tree, decides which entries
graduate from `short_memory.md` to topic files. It creates two
new topic files specifically for this project:

```
~/.config/opencode/hivemind/memory/_orchestrator/
├── short_memory.md       (now ~1 KB; recent appendings only)
├── long_memory.md        (untouched — already substantial)
├── prism-conventions.md  (NEW — naming, schema, project structure)
└── prism-decisions.md    (NEW — RPC stack, error mapping, async approach)
```

After this Friday's compaction, prism's facts have promoted from
"this week's scratch" to "this project's permanent record." Next
week when the user starts an unrelated project, the orchestrator's
short memory will start filling again — but `prism-conventions.md`
and `prism-decisions.md` survive as durable prism context that the
orchestrator can recall any time it spawns work back into a
prism worktree.

The daemon's session deletes itself. Orchestrator's subagent tree
returns to whatever it was before. Total wall-clock: under two
seconds.

> **▶ Test:** When the writer is `ses_orch_aaa` (no parent), the
> daemon spawns under `ses_orch_aaa` itself, not under some
> phantom parent. (Regression test: an earlier version walked the
> chain to find a non-null parent and crashed.)

> **▶ Test:** The orchestrator's `_orchestrator` memory tree
> survives the daemon's compaction (file is rewritten in place,
> never moved). New topic files appear with descriptive names.

> **▶ Test:** Cross-project: after a daemon-driven compaction in
> project A, switch to project B's worktree and spawn a fresh
> orchestrator turn. The orchestrator can recall A's pinned
> conventions when relevant. (Tests the cross-project memory
> claim.)

---

## Phase 12 — Stack ships, life moves on

By end of Friday, all five PRs have landed. The user closes most
tmux windows to free screen space — keeping only the orchestrator
window plus one dev shell. The branch sessions remain in the
database, idle.

A week later the user gets a Sentry alert: prism is throwing on
the preferences endpoint when a user-id contains uppercase
characters. Quick hotfix needed.

The user opens a new tmux window in the `pr2/api` worktree and
runs `hivemind`. The TUI prompts to resume the existing session:
`ses_pr2_ccc`. The user accepts. The PR2 session loads with its
full week-old history intact — every conversation with the user,
every spawn of expert-rust, every back-and-forth with sibling
sessions. Sessions outlive the windows that view them.

The user types into the resumed PR2 session:

> "Sentry alert: preferences endpoint 500s on user_id with
> uppercase letters. Probably the diesel query is case-sensitive
> against a postgres index that's lowercase. Spawn the rust expert
> from our prior conversation and have it look at this."

The PR2 agent spawns expert-rust — but with `task_id=ses_rust_xyz`
to pick up the same Tuesday/Thursday conversation:

```python
Task(
    subagent_type="expert-rust",
    task_id="ses_rust_xyz",
    description="hotfix uppercase user_id",
    prompt="""Sentry: prism's preferences endpoint 500s when
    user_id contains uppercase. Look at the diesel query you
    helped write — likely the index is lowercase-only. Recommend
    a fix."""
)
```

The rust expert picks up. It remembers the layered service/repo
design, it remembers the choice of tonic, it remembers the user's
preference for `?` over `match`. It also has — via its memory
tree — the bun-expert's compacted notes that spawned during the
original PR3 work, along with the cross-project conventions the
orchestrator pinned. The expert recommends a `LOWER(user_id)`
index addition, sketches the migration, and notes that the
service-layer error mapping should treat constraint-violations
as `InvalidArgument` rather than `Internal`.

The fix lands as a single-PR hotfix on top of main. No team
regeneration, no expert sync, no curator spawn. The accumulated
context across the five-PR stack is what makes the hotfix fast.

> **▶ Test:** A session that has been idle for >7 days and
> survived multiple engine restarts can be resumed by `hivemind
> -- -s ses_xxx`. Full message history loads. Subsequent turns
> are continuous with the pre-restart history.

> **▶ Test:** `Task(task_id=...)` against an old session still
> works after engine restart. Token-by-token continuity is
> preserved (no truncation, no resync glitches).

> **▶ Test:** Long-arc memory: spawn expert-X in week 1, do work,
> let memory daemon compact. In week 4, spawn expert-X again.
> Expert's system prompt includes content from the topic files
> created in week 1.

---

## What this implies

Stated plainly — the load-bearing properties of the workflow:

- **One session per worktree, one TUI per session.** Multiple
  branches in flight, each with its own context, its own files,
  its own conversation. (Phase 2)

- **Every session is addressable from every other session.** The
  orchestrator can talk to a branch; a branch can talk to a peer;
  the user can be anywhere and route work anywhere else. There is
  no "client" vs "server" — just sessions on this machine that
  can find each other. (Phases 3, 7, 8)

- **Sessions can read each other's history.** Recapping, forking,
  briefing — all rely on the conversation in session A being
  legible to a process operating in session B. (Phase 7)

- **Forking carries context.** Both whole-session forks
  (`source_session_id`) and expert-scoped resumes (`task_id`)
  preserve the context that makes them valuable. (Phases 5, 7)

- **Forks can be ephemeral.** When a fork is purely a probe, it
  vanishes when done. The subagent tree only ever shows long-lived
  agents plus in-flight one-offs. (Phases 1, 7, plus the
  daemon cameos)

- **Experts persist beyond any single session.** Their memory
  tree accumulates across every spawn, in every project, over
  the expert's lifetime. (Phase 5; demonstrated again in
  Phase 12)

- **The orchestrator's memory is a personal long-term knowledge
  base.** Project conventions, architectural decisions, and pinned
  facts accumulate across every project. The daemon keeps it
  bounded. After a year of work, the orchestrator carries forward
  a substantial body of categorized topic files. (Phases 9, 11)

- **Sessions outlive their TUIs.** Closing a window doesn't lose
  work. Reopening picks up where it left off. (Phase 12)

- **Memory compaction is invisible until needed.** No cron, no
  scheduler, no orchestrator instructions — the engine's
  file-write hook fires the daemon, the daemon does its work,
  the daemon vanishes. The user can ignore it entirely. (Phases
  6, 11)

- **Catalog updates are non-destructive.** `/global/reload-agents`
  refreshes the engine's view of agents without disposing any
  session. MCP tool calls in flight survive the reload. (Phase 1,
  Phase 10)

## Out of scope

- **Multiple machines.** The whole story happens on one host. No
  remote attach, no cross-machine session discovery.

- **Two windows live-viewing the same session.** Each session is
  experienced from one place at a time. If you want a second
  view, fork a recap session — don't multi-attach.

- **Multi-engine support.** OpenCode is the only backend. The old
  provider abstraction has been removed; do not reintroduce it.

- **Project-scoped orchestrator.** The orchestrator is a
  user-scoped, cross-project agent. Per-project orchestration
  exists at the team-lead and branch-session level, but the
  orchestrator itself spans projects by design.

## Test matrix index

Every `▶ Test:` callout above maps to one or more integration
tests. They cluster as follows:

| Phase | Cluster | Primary primitives exercised |
|---|---|---|
| 1 | Curator pipeline + ephemeral cleanup | `prep_create_team`, `finalize_create_team`, `Task(ephemeral=true)`, `/global/reload-agents` |
| 2 | Presence + listing | WebSocket presence channel (patch 0015), `list_sessions` MCP |
| 3 | Cross-session messaging fan-out | `send_message` MCP, per-session inbox (patch 0007) |
| 4 | Background expert spawn + buffered result | `Task(background=true)`, `SessionBackground.complete`, `read_task_result` |
| 5 | Resume + memory injection | `Task(task_id=...)`, `memory: true` in agent body, system prompt assembly |
| 6 | Per-expert daemon + ephemeral | `file.write` hook (patch 0019), `HivemindMemoryPlugin`, ephemeral cleanup (patch 0021) |
| 7 | Source-fork + ephemeral | `Task(source_session_id=..., ephemeral=true)`, `Session.fork`, ephemeral cleanup |
| 8 | Bidirectional messaging | `send_message` round-trip, inbox wake-up |
| 9 | Orchestrator memory write | Orchestrator's `_orchestrator/short_memory.md` grows on cue |
| 10 | `/hivemind_sync` proposal-then-confirm | Worktree scoping, `switch_version` curator path, atomic HEAD rotation |
| 11 | Daemon at orchestrator depth | `mainID = writer.parent_id ?? writer.id` resolves to orchestrator when writer is orchestrator |
| 12 | Long-arc session + memory survival | Session resumes after engine restart; `task_id` works across restarts; long-term expert memory carries across spawns |

A reasonable test build-out targets one engine `bun:test` + one
hivemind `pytest` per phase, plus a single end-to-end harness
script that boots opencode, runs Phases 1 → 12 in sequence
against a tmpdir worktree, and asserts the cumulative state at
each beat.

## See also

- `docs/ARCHITECTURE.md` — the layered architecture this scenario
  exercises.
- `docs/MEMORY_DAEMON.md` — full architecture of the memory tree
  and auto-compaction (Phases 6, 11).
- `HIVEMIND.md` — the orchestrator instruction file. The "Ephemeral
  spawns", "Background expert spawns", "Cross-session" sections all
  reference patterns that appear in this scenario.
- `opencode/commands/hivemind_generate_team.md` — Phase 1's
  slash command.
- `opencode/commands/hivemind_sync.md` — Phase 10's slash
  command.
- `opencode/commands/list_sessions.md` — the live-tree renderer
  used in Phase 2.
- `opencode/skills/hivemind-cross-session/SKILL.md` — the
  patterns the LLM picks up implicitly during Phases 3, 7, 8.
- `opencode/skills/hivemind-expert-management/SKILL.md` — the
  patterns the LLM picks up implicitly during Phases 1, 10.
