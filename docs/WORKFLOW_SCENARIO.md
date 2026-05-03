# Hivemind Reference Workflow: The 9-PR Graphite Stack

This is the canonical scenario hivemind is built for. It exists so design
discussions can ground themselves in a real story instead of abstractions.

## Setup

A complex project with **9 stacked PRs** synced via [graphite](https://graphite.dev).
Each PR touches a different layer of the system:

- Frontend: React, Ant Design, TypeScript
- Backend: Postgres, Sequelize
- Infra: Kubernetes, Terraform

The user runs **git worktrees** so every branch has its own working copy
on disk, and **tmux** with one window per worktree. Each tmux window has
a long-running `hivemind` TUI attached to a session for that branch:

```
tmux ─┬─ window 0  → worktree main/        TUI: orchestrator
      ├─ window 1  → worktree pr-1-fe-1/   TUI: pr-1 session
      ├─ window 2  → worktree pr-2-fe-2/   TUI: pr-2 session
      ├─ window 3  → worktree pr-3-be-1/   TUI: pr-3 session
      ├─ ...
      └─ window 9  → worktree pr-9-docs/   TUI: pr-9 session
```

The "main" window holds the **orchestrator** — a high-level session that
knows about the whole stack. The other nine each hold a **branch
session** scoped to that PR's worktree.

## The Story

### Glanceable presence

Every TUI's footer shows how many hivemind sessions are currently alive
on this machine. The orchestrator can confirm at a glance that all nine
branch sessions plus itself are running. No mystery, no stale counts.

### Recapping the stack

The user, in the orchestrator, asks: *"give me a recap of where each PR
stands."* The orchestrator pulls the recent history from each of the
nine branch sessions, summarizes each, and presents one paragraph per
PR. The user reads the recap without leaving the orchestrator window.

### Dispatching work to every branch

Same orchestrator session: *"for each PR, fetch GitHub review comments
and address them, then report back."* The orchestrator sends a prompt
to each of the nine branch sessions. Each branch picks up the work in
its own window, runs the address-review-comments workflow against its
own worktree, and reports its results back to the orchestrator when
done.

The user can switch into any branch window mid-task and watch progress
live. When all nine finish, the orchestrator has a stack-level rollup.

### Branches talking to branches

Mid-task, the user is focused in the `pr-3` (backend) window and
realizes the schema change there has to align with `pr-1` (frontend).
Without bouncing through the orchestrator, they ask the agent in `pr-3`:
*"check with the frontend session — what shape is it expecting for this
field?"* The `pr-3` agent messages `pr-1`, gets the answer, and resumes
its own work with that information. Peer-to-peer. No central
coordinator needed.

### Forking a session for context handoff

Partway through a long planning conversation, the orchestrator decides
to delegate one slice to a fresh focused session. It forks itself into
`pr-3-impl`, which appears in the `pr-3` window as a new sub-session.
The fork inherits the orchestrator's recent context as seed — the
implementation session starts already knowing the plan instead of being
re-briefed from scratch.

### Forking an expert with its context

In `pr-3` (backend), the user spawned `expert-postgres` to design a
schema migration. The expert ran tools, did analysis, made decisions —
specific tables, specific tradeoffs, specific alternatives ruled out.
That whole reasoning chain is rich context.

In `pr-4` (a related backend PR), the user wants to continue with that
same expert *with everything it just learned*. Not a fresh spawn — the
expert's prior reasoning continues, now scoped to the new branch's
problem. What was learned in `pr-3` carries forward.

### Expert long-term memory

Distinct from forking: expert agents have their own persistent memory.
When `expert-postgres` decides something is worth remembering long-term
("this project uses snake_case for column names, never camelCase"),
that fact is available to every future invocation of `expert-postgres`,
in any session, on any branch. The expert builds up a personal
knowledge base across the project's lifetime, not just within one
conversation.

### Closing and reopening a window

The user closes the tmux window for `pr-5` to free up screen space.
Some hours later, they open a new window in the `pr-5` worktree and
resume the session. The full prior conversation is there. The
orchestrator and other branches can address `pr-5` again as if it had
never been closed. Sessions outlive the windows they're viewed in.

## What This Vision Implies

These are the load-bearing properties of the workflow, stated plainly:

- **One session per worktree, one TUI per session.** Multiple branches
  in flight, each with its own context, its own files, its own agent
  conversation.

- **Every session is addressable from every other session.** The
  orchestrator can talk to a branch; a branch can talk to a peer; the
  user can be anywhere and route work anywhere else. There is no
  "client side" vs "server side" — just sessions on this machine that
  can find each other.

- **Sessions can read each other's history.** Recapping, forking,
  briefing — all rely on the conversation in session A being legible
  to a process operating in session B.

- **Forking carries context.** Both whole-session forks (handing off a
  conversation) and expert-scoped forks (handing off a subagent's
  reasoning chain) preserve the context that makes them valuable.

- **Experts persist beyond any single session.** Their long-term
  memory accumulates across every place they're used.

- **Sessions outlive their TUIs.** Closing a window doesn't lose work.
  Reopening picks up where it left off.

## Out of Scope

- **Multiple machines.** The whole story happens on one host. No
  remote attach, no cross-machine session discovery.

- **Two windows live-viewing the same session.** Each session is
  experienced from one place at a time. If you want a second view,
  fork a recap session — don't multi-attach.
