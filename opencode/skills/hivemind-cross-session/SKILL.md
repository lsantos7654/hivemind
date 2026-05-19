---
name: hivemind-cross-session
description: Patterns for messaging or inspecting other live opencode sessions on this machine. Load when the user wants to coordinate work across sessions, hand off context to another worktree, ping a busy session, list what's currently running, or chain results between sessions. Covers list_sessions, read_session, send_message, and when to prefer Task(source_session_id=...) over send_message.
---

# Cross-session messaging

Four MCP verbs cover every cross-session interaction that isn't a `Task`
spawn:

- `list_sessions(live_only=true, tree=false, roots?, limit?)` —
  discovery. By default returns only "live" sessions (a TUI is
  currently attached). Subagents render under their live parent.
  Pass `tree=true` for nested `{...session, children:[...]}`;
  `live_only=false` to see every session in the DB.
- `read_session(session_id, index=-1)` — peek at a session's exchange
  history without waking it. Returns one user+assistant pair as plain
  text — grep/awk/rg friendly. Index 0 = first exchange, -1 = last.
  Read-only: no messages land in the target session, no side effects.
- `send_message(session_id, message)` — append to another session's
  inbox. Delivered immediately if the target is idle, queued and
  delivered on next idle if busy. Never throws BusyError, so it's
  safe to ping a session that's mid-turn. The recipient automatically
  sees `[From: ses_xxx]\n\n` prepended where `ses_xxx` is your
  session ID — attribution is handled by the engine, no caller action
  required.
- `delete_session(session_id)` — hard-delete a session and its
  descendants.

## Peek before ping

Before sending a message, check what the target session is doing:

1. `list_sessions(live_only=true, tree=true)` — find the target
2. `read_session(target_id, -1)` — read its last exchange
3. Decide: ping with `send_message`, fork with
   `Task(source_session_id=...)`, or leave it alone

This avoids waking a session that's mid-flow when you just need a
quick look at its output.

## Typical flow

1. `list_sessions(live_only=true, tree=true)` to find the target
2. `read_session(target_id, -1)` to peek at its current state
3. `send_message(target_id, "<task or question>")` to dispatch
4. The recipient sees `[From: ses_xxx]` (auto-attached) and calls
   `send_message` back when its turn finishes

## When to prefer Task over send_message

- **`read_session(session_id, index=-1)` — pure read.** Returns the
  text of a past exchange. No forking, no waking, no tool calls. Use
  to check progress or retrieve a previous answer without any
  round-trip.
- **`Task(source_session_id=...)` — read-only style.** Forks the
  source session's full history into a fresh subagent. The source
  itself receives no new messages. Use when you want to "ask another
  session a question without disturbing it" and need the full context
  (tools, file reads, etc.) to answer, not just the final text.
- **`send_message(session_id, message)` — write style.** The
  recipient session does the work and replies in place. Use when you
  want the target session itself to advance.

The three are mutually exclusive — pick the one that matches your
intent.

### Ephemeral forks for one-off questions

`Task(source_session_id=..., ephemeral=true)` deletes the forked
subagent's session as soon as it returns. Use when the fork is
purely a probe — you want the answer in your message history but
don't care about the intermediate work and won't resume the
forked session. Keeps your subagent tree from accumulating one
short-lived fork per "ask another session a quick question."
Ephemeral and `task_id` are mutually exclusive.

## Limits

- Same-host only. Cross-machine session messaging isn't supported.
- `read_session` works against any session in the DB (not just live
  ones) — messages are stored in SQLite and survive process exit.
- The recipient must be a live session (its TUI process running) for
  `send_message` delivery. Closed sessions can be resumed via
  `hivemind -- -s ses_xxx` first.
- `send_message` returns a delivery receipt (`{queued, depth}`); the
  recipient's actual response lands later via the inbox flow.
