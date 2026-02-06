# Update Repository Expert Knowledge Base

Refreshes the knowledge base for an existing repository expert subagent by re-analyzing the repository and regenerating all documentation files.

## Usage

```bash
/update-repo-expert <name>
```

## Arguments

- `<name>` - Name of the expert to update (e.g., `bazel`, `metaflow`, `rules-python`)

## Examples

```bash
# Update the bazel knowledge base
/update-repo-expert bazel

# Update the metaflow knowledge base
/update-repo-expert metaflow
```

## What This Command Does

This command refreshes the knowledge base for an existing repository expert without recreating the agent definition or losing any customizations. The process takes 20-30 minutes.

### 1. Locate Existing Expert

Looks up the expert in `experts/<name>/` within the hivemind repo.

If the expert is not found, the command will fail with an error. Run `hivemind list` to see available experts.

### 2. Verify Repository Is Fetched

Checks that `~/.claude/repos/<name>` exists. If not, runs `hivemind fetch <name>` to clone it.

If the expert has no entry in `repos.json`, prompts for the repository URL.

### 3. Optionally Update Repository Source

If `--ref` is provided or the user requests it, updates the repo to a newer commit/tag before re-analysis.

### 4. Deep Repository Re-Analysis (AI - 20-30 min)

Spawns a very thorough exploration of `~/.claude/repos/<name>` to capture any changes since the last analysis:
- New features and capabilities
- Updated directory structure
- Build system changes
- New or modified APIs
- Updated dependencies
- Architecture changes

### 5. Regenerate Knowledge Files

Creates fresh versions of all 4 comprehensive markdown documentation files in `experts/<name>/`:

**summary.md** (500-800 words)
- Updated repository purpose and goals
- Current key features and capabilities
- Latest use cases and target audience
- Current architecture overview
- Updated dependencies

**code_structure.md** (1000-1500 words)
- Current directory tree with annotations
- Updated module organization
- New or reorganized source directories
- Modified key files
- Current code patterns

**build_system.md** (800-1200 words)
- Current build configuration
- Updated dependencies
- New build targets
- Modified build commands
- Updated dependency graph

**apis_and_interfaces.md** (1000-1500 words)
- Current public APIs
- New or updated functions/classes/macros
- Updated usage examples
- New integration patterns
- Updated best practices

### 6. Preserve Agent Definition

**IMPORTANT:** The `experts/<name>/agent.md` file is **NOT** modified. This preserves:
- Custom agent instructions you may have added
- Modified tool access configurations
- Expertise sections and activation triggers
- Any other agent customizations

Only the 4 knowledge markdown files are updated with fresh content.

### 7. Sync

Runs `hivemind sync` to regenerate the flat agent file in `agents/` with resolved paths.

### 8. Confirm Update

Displays a summary of what was updated:
- Which knowledge files were regenerated
- Confirmation that agent definition was preserved
- Next steps

## Storage Structure

All files live within the hivemind repo:

```
experts/<name>/
├── agent.md                (PRESERVED - not modified)
├── summary.md              (UPDATED)
├── code_structure.md       (UPDATED)
├── build_system.md         (UPDATED)
└── apis_and_interfaces.md  (UPDATED)
```

## When to Use This Command

Update your repository experts when:

- **Major feature additions** - New capabilities or modules added to the repository
- **Architecture changes** - Refactoring or reorganization of code structure
- **Dependency updates** - New or updated external dependencies
- **Build system changes** - Modified build configuration or new targets
- **API changes** - New public APIs or breaking changes to existing ones
- **Periodic refresh** - Monthly or quarterly updates to keep knowledge current

## Implementation

When you run this command, Claude will:

1. **Verify** the expert exists in `experts/<name>/`
2. **Check** that `~/.claude/repos/<name>` is fetched (run `hivemind fetch <name>` if not)
3. **Analyze** the repository with very thorough exploration (20-30 minutes)
4. **Generate** fresh versions of all 4 markdown knowledge files
5. **Write** updated files to `experts/<name>/`
6. **Preserve** `experts/<name>/agent.md` (no modifications)
7. **Run** `hivemind sync` to regenerate the flat agent file
8. **Report** what was updated and confirm success

## Notes

- Re-analysis is thorough and takes 20-30 minutes
- Knowledge files are overwritten completely (not merged)
- Agent definition is never modified - customizations are safe
- Knowledge updates are tracked in git (commit with `hivemind` repo)
- Run `hivemind list` to see all experts and their status

---

Now, provide the expert name to refresh its knowledge base.
