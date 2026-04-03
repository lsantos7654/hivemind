# pre-commit: Summary

## Repository Purpose and Goals

pre-commit is a framework for managing and maintaining multi-language pre-commit hooks. Its core purpose is to automate code quality enforcement at commit time — running linters, formatters, and other checks on staged files before they enter the repository. The project enables teams to define shared hook configurations in version control, ensuring every contributor runs the same checks consistently.

Version at this commit: **4.5.1** (Python package `pre_commit`).

## Key Features and Capabilities

- **Multi-language hook support**: Hooks can be written in Python, Node.js, Ruby, Go, Rust, Haskell, Julia, Dart, R, Perl, Lua, Swift, Conda, Coursier (JVM), Docker, .NET, and more (21 language backends total).
- **Git hook stage coverage**: Supports all major git hook stages: `pre-commit`, `pre-push`, `commit-msg`, `prepare-commit-msg`, `post-commit`, `post-merge`, `post-rewrite`, `post-checkout`, `pre-merge-commit`, `pre-rebase`, and `manual` (for CI use).
- **Isolated environments**: Each hook repository gets its own isolated environment (virtualenv, node_modules, GOPATH, etc.) cached by repository URL + revision.
- **Staged files stashing**: During `pre-commit` runs, unstaged changes are temporarily stashed so hooks only see the staged content, then restored afterward.
- **Parallel execution**: Hooks run files through a multi-threaded xargs-like partitioner respecting platform command-length limits and CPU count.
- **Automatic updates**: `pre-commit autoupdate` fetches the latest tag or HEAD commit for each hook repository, updating `.pre-commit-config.yaml` in place with parallel workers.
- **Local and meta hooks**: Supports hooks defined directly in the project config (`repo: local`) or self-referential validation hooks (`repo: meta`).
- **Git template directory integration**: `init-templatedir` installs hooks into a git template directory so all new clones automatically get pre-commit.
- **Configuration validation**: Built-in `validate-config` and `validate-manifest` commands validate YAML files against schemas.
- **Frozen refs**: `autoupdate --freeze` pins revisions to exact commit SHAs with a `# frozen: <tag>` comment for reproducibility.

## Primary Use Cases and Target Audience

- **Software development teams** wanting consistent code style and quality enforcement across contributors.
- **Individual developers** who want to prevent bad commits locally (trailing whitespace, broken syntax, secrets, etc.).
- **CI systems** (e.g., pre-commit.ci) running hooks on pull requests without installing per-language tooling individually.
- **Hook authors** who publish reusable hooks in their repositories for others to consume.

## High-Level Architecture Overview

pre-commit follows a clear layered architecture:

1. **CLI layer** (`pre_commit/main.py`): Parses arguments with argparse and dispatches to command modules.

2. **Command layer** (`pre_commit/commands/`): Each subcommand is implemented in its own module:
   - `run.py` — core hook execution
   - `install_uninstall.py` — git hook script management
   - `autoupdate.py` — config version updating
   - `hook_impl.py` — the internal hook dispatcher called by git
   - `gc.py`, `clean.py` — store maintenance
   - Others: `try_repo.py`, `migrate_config.py`, `validate_config.py`, `validate_manifest.py`, `sample_config.py`, `init_templatedir.py`, `hazmat.py`

3. **Repository/Store layer** (`pre_commit/repository.py`, `pre_commit/store.py`): Manages cloned hook repositories in a SQLite-backed cache (`~/.cache/pre-commit/`). Uses shallow cloning by default with full-clone fallback.

4. **Hook model** (`pre_commit/hook.py`, `pre_commit/clientlib.py`): `Hook` is a `NamedTuple` carrying all hook configuration. `clientlib.py` defines the `cfgv`-based schemas for `.pre-commit-config.yaml` and `.pre-commit-hooks.yaml`.

5. **Language backends** (`pre_commit/languages/`): Each language module implements the `Language` protocol (`lang_base.py`) with `install_environment`, `in_env`, `run_hook`, `health_check`, and `get_default_version`.

6. **Execution engine** (`pre_commit/xargs.py`, `pre_commit/run.py`): A `Classifier` filters filenames by type tags (via the `identify` library) and include/exclude regexes. The `xargs` module partitions files across parallel subprocesses, respecting platform command-length limits.

## Related Projects and Dependencies

**Runtime dependencies:**
- `cfgv` — schema-based YAML config validation
- `identify` — file type tagging (detects Python, shell, JSON, etc. by content/extension)
- `nodeenv` — creates isolated Node.js environments
- `pyyaml` — YAML parsing/dumping
- `virtualenv` — creates isolated Python environments

**Related ecosystem:**
- **pre-commit.ci** — a hosted CI service that runs pre-commit on pull requests
- **identify** — used to classify file types for `types`, `types_or`, `exclude_types` filtering
- Hook repositories: thousands of community hook packages (e.g., `pre-commit-hooks`, `ruff-pre-commit`, `black`, `isort`)
