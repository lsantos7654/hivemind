---
name: clear_ephemeral_agents
description: Clear all ephemeral subagent sessions (one-shot explorers, curators, daemons) that may not have been auto-cleaned. Finds them via list_sessions and deletes via delete_session.
---

# Clear ephemeral agents

Ephemeral subagent sessions auto-delete on terminal state, but edge cases
(crashes, races) can leave orphaned ones behind. This command finds and
bulk-deletes them.

## Step 1 — Find ephemeral sessions

Call `list_sessions` with `live_only=false`. Filter the result to sessions
with `ephemeral: true`. If none, say "No orphaned ephemeral sessions found."
and stop.

## Step 2 — Report and confirm

If found, tell the user how many (e.g. "Found 3 orphaned ephemeral
sessions:"), list each with its `id` and `title`, and ask for confirmation.

## Step 3 — Delete

On confirmation, call `delete_session(session_id=...)` for each. Run all
deletes in parallel (single message, multiple tool calls). Report the
result: "Deleted N of N ephemeral sessions." If any fail, note which IDs
and the errors.
