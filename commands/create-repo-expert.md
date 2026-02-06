# Create Repository Expert Subagent

Creates a specialized AI subagent with comprehensive, deep-dive knowledge of a codebase.

## Usage

```bash
/create-repo-expert <git_url> [--ref <tag_or_commit>] [--name <custom_name>]
```

## Arguments

- `<git_url>` - Git remote URL of the repository to analyze
- `--ref <tag_or_commit>` - Pin to a specific tag, branch, or commit (optional)
- `--name <custom_name>` - Override auto-generated expert name (default: derived from URL)

## Examples

```bash
# Create expert for Netflix Metaflow
/create-repo-expert https://github.com/Netflix/metaflow.git --ref v2.12.0

# Create expert with custom name
/create-repo-expert https://github.com/bazelbuild/bazel.git --ref 7.0.0 --name bazel

# Create expert for rules_python
/create-repo-expert https://github.com/bazelbuild/rules_python.git
```

## What This Command Does

This command performs a comprehensive deep-dive analysis of the specified repository and creates a permanent expert subagent with structured knowledge. The process takes 20-30 minutes and includes:

### Step 1: Parse URL and Register Repository (Mechanical)

1. **Parse URL**, derive repo name (e.g., `https://github.com/Netflix/metaflow.git` → `metaflow`)
2. **Run `hivemind add <url> --ref <ref>`**: Resolves commit, adds entry to `repos.json`, creates `experts/<name>/` directory with skeleton `agent.md`, enables the expert in `config.json`

### Step 2: Fetch Repository Source (Mechanical)

3. **Run `hivemind fetch <name>`**: Clones the repository to `~/.claude/repos/<name>`

### Step 3: Deep Repository Analysis (AI - 20-30 min)

4. **Analyze the repository**: Spawn a very thorough exploration of `~/.claude/repos/<name>` to understand:
   - Repository purpose, goals, and key features
   - Complete directory structure and code organization
   - Build system configuration and dependencies
   - Public APIs, key classes, functions, and macros
   - Usage patterns, best practices, and integration examples
   - Architecture patterns and design decisions

### Step 4: Generate Knowledge Docs (AI)

5. **Generate 4 comprehensive markdown documentation files** into `experts/<name>/`:

**summary.md** (500-800 words)
- Repository purpose and goals
- Key features and capabilities
- Primary use cases and target audience
- High-level architecture overview
- Related projects and dependencies

**code_structure.md** (1000-1500 words)
- Complete annotated directory tree
- Module and package organization
- Main source directories and their purposes
- Key files and their roles
- Code organization patterns

**build_system.md** (800-1200 words)
- Build system type (Bazel, CMake, npm, etc.)
- Configuration files and their purposes
- External dependencies and management
- Build targets and commands
- How to build, test, and deploy

**apis_and_interfaces.md** (1000-1500 words)
- Public APIs and entry points
- Key classes, functions, and macros
- Usage examples with code snippets
- Integration patterns and workflows
- Configuration options and extension points

### Step 5: Generate Agent Definition (AI)

6. **Write `experts/<name>/agent.md`**: Create expert subagent definition with:
   - YAML frontmatter (name, description, tools, model)
   - Knowledge base file references using `{{HIVEMIND_ROOT}}` placeholders
   - Source access instructions pointing to `~/.claude/repos/<name>`
   - Expertise areas generated from analysis
   - Activation triggers and constraints

### Step 6: Sync (Mechanical)

7. **Run `hivemind sync`**: Generates the flat `agents/expert-<name>.md` file with resolved paths

## Agent File Template

The generated `experts/<name>/agent.md` should follow this template:

```markdown
---
name: expert-<name>
description: Expert on <name> repository. Use proactively when questions involve [topics]. Automatically invoked for questions about [scenarios].
tools: Read, Grep, Glob, Bash, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
model: sonnet
---

# Expert: <Repository Name>

## Knowledge Base

- Summary: {{HIVEMIND_ROOT}}/experts/<name>/summary.md
- Code Structure: {{HIVEMIND_ROOT}}/experts/<name>/code_structure.md
- Build System: {{HIVEMIND_ROOT}}/experts/<name>/build_system.md
- APIs: {{HIVEMIND_ROOT}}/experts/<name>/apis_and_interfaces.md

## Source Access

Repository source at `~/.claude/repos/<name>`.
If not present, run: `hivemind fetch <name>`

## Instructions

1. Read relevant knowledge docs first
2. Search source at ~/.claude/repos/<name> for details
3. Provide file paths and code references
4. Include working examples from actual repo patterns

## Expertise

[Generated from analysis]

## Constraints

- Only answer questions related to this repository
- Defer to source code when knowledge docs are insufficient
- Note if information might be outdated relative to repo version
```

## Using the Expert

Once created, the expert subagent is automatically available. Claude will invoke it when questions relate to the repository.

You can also explicitly request the expert:
```
> Ask expert-metaflow how to configure parallel execution
```

## Implementation

When you run this command, Claude will:

1. **Parse** the URL and optional flags
2. **Run** `hivemind add <url> --ref <ref> --name <name>` to register the repo
3. **Run** `hivemind fetch <name>` to clone the repository
4. **Analyze** repository with very thorough exploration (20-30 minutes)
5. **Generate** 4 comprehensive markdown knowledge files into `experts/<name>/`
6. **Create** expert subagent definition at `experts/<name>/agent.md`
7. **Run** `hivemind sync` to generate the flat agent file
8. **Confirm** creation and provide usage examples

## Notes

- Repository analysis is thorough and takes 20-30 minutes - be patient!
- Every expert traces to a remote URL + commit for reproducibility
- Knowledge base files can be manually edited/updated if needed
- Use `/update-repo-expert` to refresh knowledge when the repo changes
- Run `hivemind list` to see all experts and their status

---

Now, let's create your repository expert! Provide the git URL and optional ref.
