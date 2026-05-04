---
name: list_sessions
description: List all live sessions on this machine as a tree, with each root session and its spawned subagents. Use when you want a quick visual of who's running what.
---

# List sessions

Call the `list_sessions` MCP tool with `live_only=true` and `tree=true`,
then render the result as a tree:

- Each root session on its own line: `<id>  <title>  <updated>`
- Subagents indented under their parent
- If a session has no children, render it as a leaf

If the result is empty, say so plainly — no live sessions.

After rendering, do NOT take further action. The user is just getting
oriented; if they want to interact with a session, they'll say so.
