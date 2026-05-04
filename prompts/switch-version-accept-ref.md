# Prompt: Allow `switch_version` to accept a tag/branch ref, not just a commit SHA

## Goal

Extend the `switch_version` MCP tool so it can accept a human-readable ref (tag name, branch name) in addition to a raw commit SHA. The handler resolves the ref to a SHA internally before proceeding with the existing switch logic.

## Problem

Today, switching an expert to a tagged release requires manual steps:

```bash
# User must manually resolve the tag
git -C ~/.cache/hivemind/repos/bazel rev-list -1 8.5.1
# Then pass the SHA
switch_version(name="bazel", commit="a3930898ad18310cbafc06a46d8c13fd75cf290c")
```

This is fragile:
- Requires knowing the clone path convention (`~/.cache/hivemind/repos/<name>/`)
- The local clone may not have the tag fetched (stale or shallow)
- Forces the caller to shell out for something the tool should handle

## Desired behavior

```
switch_version(name="bazel", commit="8.5.1")
```

The handler should:
1. First try to interpret `commit` as a raw SHA (current behavior -- if it looks like a hex string and exists in the repo, use it directly).
2. If not a valid SHA, treat it as a ref: run `git fetch --tags` on the clone, then `git rev-parse <ref>` to resolve to a SHA.
3. Proceed with the resolved SHA through the existing switch logic.

This is a backwards-compatible change -- existing callers passing full SHAs continue to work unchanged.

## Architecture

### MCP layer (`src/hivemind/mcp/tools.py`)

The `switch_version` tool definition (in the `TOOLS` list) currently has:

```python
Tool(
    name="switch_version",
    description="Switch a git_analyzed agent to a specific commit. ...",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Git-analyzed agent name"},
            "commit": {"type": "string", "description": "Target commit SHA (full or short) reachable in the cloned repo."},
        },
        "required": ["name", "commit"],
    },
)
```

Changes:
- Update the `commit` field's description to: `"Target commit SHA, tag name, or branch name. If not a valid SHA, resolved as a git ref in the cloned repo."`
- Update the tool-level description to mention that tags/branches are accepted.
- No schema changes needed -- the field type stays `string`.

The handler `_handle_switch_version` currently passes `commit` straight through to the domain function. It should remain thin -- resolution logic belongs in the domain layer.

### Domain layer (`src/hivemind/agents/git_analyzed.py`)

The `switch_version` function is the right place for the resolution logic. It already knows the agent name and has access to the repo path.

Add resolution logic **before** the existing commit-existence check:
1. Check if `target_commit` looks like a hex SHA (regex: `^[0-9a-f]{4,40}$`, case-insensitive) AND exists in the repo. If yes, use as-is (current path).
2. Otherwise, fetch tags: `git -C <repo_path> fetch --tags --quiet`
3. Resolve: `git -C <repo_path> rev-parse <target_commit>` -- this handles tags, branches, `HEAD`, `origin/main`, etc.
4. If resolution fails, return an error result: `f"Could not resolve ref '{target_commit}' in repo for agent '{name}'"`
5. Use the resolved SHA for the rest of the function.

### Git layer (`src/hivemind/git.py`)

Consider adding a helper function here rather than inlining git commands in `git_analyzed.py`:

```python
def resolve_ref(repo_path: Path, ref: str) -> str | None:
    """Resolve a ref (tag, branch, SHA prefix) to a full commit SHA.

    Fetches tags first to ensure local refs are up to date.
    Returns None if the ref cannot be resolved.
    """
```

This keeps git subprocess calls centralized (consistent with the existing `clone_from_remote`, `resolve_latest_commit`, etc.).

### Existing helpers to be aware of

- `git.py:resolve_latest_commit(repo_path, remote)` -- resolves the latest commit on the default branch via `git ls-remote`. Different use case (latest vs specific ref) but shows the pattern.
- `git_analyzed.py:commit_exists_in_repo(name, commit)` -- checks if a SHA exists in the local clone. This is already called in `switch_version` and should remain as the final validation after resolution.

## Implementation checklist

1. Add `resolve_ref(repo_path: Path, ref: str) -> str | None` to `src/hivemind/git.py`. It should:
   - Run `git -C <repo_path> fetch --tags --quiet` (ignore errors -- offline is fine, just use local refs)
   - Run `git -C <repo_path> rev-parse --verify <ref>^{commit}` (the `^{commit}` suffix dereferences annotated tags to their commit)
   - Return the full SHA on success, `None` on failure
   - Use the existing subprocess patterns in the file (check `subprocess.run` usage in neighboring functions)

2. Update `switch_version` in `src/hivemind/agents/git_analyzed.py`:
   - After validating the agent exists and is `git_analyzed`, but before checking `commit_exists_in_repo`:
   - If `target_commit` doesn't match `^[0-9a-f]{4,40}$` (case-insensitive), OR if it does match but `commit_exists_in_repo` returns False:
     - Call `resolve_ref(repo_path, target_commit)`
     - If `None`, return error result
     - Otherwise, replace `target_commit` with the resolved SHA and continue

3. Update the `switch_version` tool description in `src/hivemind/mcp/tools.py`:
   - Update `commit` property description
   - Update tool-level description

4. No arg extractor or handler changes needed -- the string passes through unchanged.

## Conventions

- `from __future__ import annotations` at the top of every module.
- Subprocess calls use `subprocess.run` with `capture_output=True`, `text=True`, `check=False` (check return code manually) -- see existing patterns in `git.py`.
- Timeouts on subprocess calls: use `constants.GIT_TIMEOUT` if it exists, otherwise a reasonable default (30s).
- Error messages should be user-friendly: `f"Could not resolve ref '{target_commit}' in repo for agent '{name}'"`.

## Verification

```bash
bazelisk test //...
```

Manual smoke test after restarting opencode:
```
switch_version(name="bazel", commit="8.5.1")  # should resolve tag -> SHA
switch_version(name="bazel", commit="a3930898ad18")  # should still work (short SHA)
switch_version(name="bazel", commit="nonexistent-ref")  # should return clear error
```
