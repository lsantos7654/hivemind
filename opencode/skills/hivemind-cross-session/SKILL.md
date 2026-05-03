---
name: hivemind-cross-session
description: Patterns for messaging or inspecting other live opencode sessions on this machine. Load when the user wants to coordinate work across sessions, hand off context to another worktree, ping a busy session, list what's currently running, or chain results between sessions. Covers list_sessions, send_message, and when to prefer Task(source_session_id=...) over send_message.
---

# Cross-session messaging

Two MCP verbs cover every cross-session interaction that isn't a `Task`
spawn:

- `list_sessions(live_only=true, tree=false, roots?, limit?)` —
  discovery. By default returns only "live" sessions (a TUI is
  currently attached). Subagents render under their live parent.
  Pass `tree=true` for nested `{...session, children:[...]}`;
  `live_only=false` to see every session in the DB.
- `send_message(session_id, message)` — append to another session's
  inbox. Delivered immediately if the target is idle, queued and
  delivered on next idle if busy. Never throws BusyError, so it's
  safe to ping a session that's mid-turn.

## Typical flow

1. `list_sessions(live_only=true, tree=true)` to find the target
2. `send_message(target_id, "<task or question>")` to dispatch
3. Ask the recipient to `send_message` back to *your* session ID
   when its turn finishes — that's how the result returns

## When to prefer Task over send_message

- **`Task(source_session_id=...)` — read-only style.** Forks the
  source session's full history into a fresh subagent. The source
  itself receives no new messages. Use when you want to "ask another
  session a question without disturbing it."
- **`send_message(session_id, message)` — write style.** The
  recipient session does the work and replies in place. Use when you
  want the target session itself to advance.

The two are mutually exclusive — pick the one that matches your
intent.

## Limits

- Same-host only. Cross-machine session messaging isn't supported.
- The recipient must be a live session (its TUI process running).
  Closed sessions can be resumed via `hivemind -- -s ses_xxx` first.
- `send_message` returns a delivery receipt (`{queued, depth}`); the
  recipient's actual response lands later via the inbox flow.
