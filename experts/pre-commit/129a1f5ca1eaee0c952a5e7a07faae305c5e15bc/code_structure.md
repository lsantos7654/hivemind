# pre-commit: Code Structure

## Annotated Directory Tree

```
pre-commit/
├── pre_commit/                    # Main package
│   ├── __init__.py                # Empty marker
│   ├── __main__.py                # python -m pre_commit entry point
│   ├── main.py                    # CLI argument parsing; dispatches to commands
│   ├── constants.py               # CONFIG_FILE, MANIFEST_FILE, VERSION, DEFAULT
│   ├── clientlib.py               # Config/manifest schemas (cfgv), Hook types, STAGES
│   ├── hook.py                    # Hook NamedTuple definition
│   ├── repository.py              # Hook environment install/load logic
│   ├── store.py                   # SQLite-backed cache; clone/make_local
│   ├── lang_base.py               # Language protocol; shared helpers
│   ├── all_languages.py           # languages dict mapping name→module
│   ├── staged_files_only.py       # Unstaged change stashing context manager
│   ├── xargs.py                   # Parallel partitioned subprocess runner
│   ├── git.py                     # Git helper functions
│   ├── envcontext.py              # Environment variable patching context manager
│   ├── prefix.py                  # Prefix class (path resolution in hook envs)
│   ├── util.py                    # cmd_output*, CalledProcessError, rmtree, etc.
│   ├── color.py                   # Terminal color formatting
│   ├── output.py                  # write_line, write_line_b output helpers
│   ├── errors.py                  # FatalError exception
│   ├── error_handler.py           # Context manager for FatalError/sys.exit
│   ├── logging_handler.py         # Colored logging handler
│   ├── parse_shebang.py           # Executable lookup and shebang parsing
│   ├── yaml.py                    # yaml_load / yaml_dump wrappers
│   ├── yaml_rewrite.py            # YAML comment-preserving rewrite utilities
│   ├── file_lock.py               # Cross-platform file locking
│   │
│   ├── commands/                  # One module per CLI subcommand
│   │   ├── __init__.py
│   │   ├── run.py                 # `pre-commit run` — core hook execution
│   │   ├── install_uninstall.py   # `install` / `uninstall` git hooks
│   │   ├── autoupdate.py          # `autoupdate` — bump rev in config
│   │   ├── hook_impl.py           # `hook-impl` — internal git hook dispatcher
│   │   ├── gc.py                  # `gc` — garbage collect unused cached repos
│   │   ├── clean.py               # `clean` — remove entire cache
│   │   ├── try_repo.py            # `try-repo` — test hooks from a local/remote repo
│   │   ├── migrate_config.py      # `migrate-config` — upgrade old config format
│   │   ├── validate_config.py     # `validate-config` — lint config files
│   │   ├── validate_manifest.py   # `validate-manifest` — lint hook manifests
│   │   ├── sample_config.py       # `sample-config` — emit starter config
│   │   ├── init_templatedir.py    # `init-templatedir` — install into git template
│   │   └── hazmat.py              # `hazmat` — composable tools for hook entries
│   │
│   ├── languages/                 # Language backend implementations
│   │   ├── __init__.py
│   │   ├── python.py              # Python: virtualenv + pip install
│   │   ├── node.py                # Node.js: nodeenv + npm install
│   │   ├── ruby.py                # Ruby: bundled rbenv + gem install
│   │   ├── golang.py              # Go: downloads go toolchain or uses system
│   │   ├── rust.py                # Rust: cargo install
│   │   ├── conda.py               # Conda: conda env create
│   │   ├── coursier.py            # Coursier (Scala/JVM): cs install
│   │   ├── dart.py                # Dart: pub global activate
│   │   ├── docker.py              # Docker: docker build + run
│   │   ├── docker_image.py        # Docker (image only): docker pull + run
│   │   ├── dotnet.py              # .NET: dotnet tool install
│   │   ├── haskell.py             # Haskell: stack install
│   │   ├── julia.py               # Julia: Pkg.add + precompile
│   │   ├── lua.py                 # Lua: luarocks install
│   │   ├── perl.py                # Perl: cpanm install
│   │   ├── r.py                   # R: renv + Rscript
│   │   ├── swift.py               # Swift: swift build
│   │   ├── pygrep.py              # pygrep: regex-based file matching (no install)
│   │   ├── fail.py                # fail: always-failing hook (no install)
│   │   ├── unsupported.py         # system: runs command on PATH (no install)
│   │   └── unsupported_script.py  # script: runs script files (no install)
│   │
│   ├── meta_hooks/                # Built-in meta-repo hooks
│   │   ├── __init__.py
│   │   ├── check_hooks_apply.py   # Checks that configured hooks apply to ≥1 file
│   │   ├── check_useless_excludes.py  # Finds excludes that match no files
│   │   └── identity.py            # Prints filenames (debugging tool)
│   │
│   └── resources/                 # Bundled data files (package_data)
│       ├── hook-tmpl              # Shell template for installed git hook scripts
│       ├── rbenv.tar.gz           # Bundled rbenv for Ruby
│       ├── ruby-build.tar.gz      # Bundled ruby-build plugin
│       ├── ruby-download.tar.gz   # Ruby download helper
│       ├── empty_template_*.      # Template files for local repo scaffolding
│       │   (Cargo.toml, main.rs, go.mod, main.go, package.json,
│       │    setup.py, environment.yml, Makefile.PL, pubspec.yaml,
│       │    renv.lock, activate.R, LICENSE.renv, .npmignore,
│       │    pre-commit-package-dev-1.rockspec,
│       │    pre_commit_placeholder_package.gemspec)
│       └── __init__.py
│
├── tests/                         # Test suite mirroring package structure
│   ├── conftest.py                # Shared pytest fixtures
│   ├── commands/                  # Tests for each command module
│   ├── languages/                 # Tests for each language backend
│   ├── meta_hooks/                # Tests for meta hooks
│   └── *.py                       # Unit tests for core modules
│
├── testing/                       # Test infrastructure
│   ├── util.py                    # Test helper functions
│   ├── language_helpers.py        # Shared language test helpers
│   ├── resources/                 # Minimal hook repos used in tests
│   │   ├── script_hooks_repo/     # Shell script hooks
│   │   ├── python_hooks_repo/     # Python hooks
│   │   ├── failing_hook_repo/     # Always-failing hooks
│   │   └── ...                    # Many more test repos
│   ├── zipapp/                    # zipapp packaging infrastructure
│   └── make-archives              # Script to rebuild bundled archives
│
├── .pre-commit-config.yaml        # pre-commit config used on this repo itself
├── .pre-commit-hooks.yaml         # Hook manifest published by this repo
├── setup.cfg                      # Package metadata and entry points
├── setup.py                       # Minimal build shim
├── tox.ini                        # tox + pytest configuration
├── requirements-dev.txt           # Dev dependencies
├── CHANGELOG.md                   # Version history
└── CONTRIBUTING.md                # Contribution guide
```

## Module and Package Organization

The codebase is organized in three layers:

1. **Core infrastructure** — `store.py`, `repository.py`, `hook.py`, `clientlib.py`, `lang_base.py`, `xargs.py`, `staged_files_only.py`
2. **Command implementations** — `commands/` package, one module per CLI subcommand
3. **Language backends** — `languages/` package, one module per supported language

## Key Files and Their Roles

### `pre_commit/main.py`
The CLI entry point. Builds the argparse parser, registers all subcommands, and dispatches to command modules. Sets `PRE_COMMIT=1` indirectly via `run.py`. Handles the `COMMANDS_NO_GIT` set for commands that don't need a git repository.

### `pre_commit/clientlib.py`
Defines schemas using `cfgv` for both `.pre-commit-config.yaml` (`CONFIG_SCHEMA`) and `.pre-commit-hooks.yaml` (`MANIFEST_SCHEMA`). Contains:
- `HOOK_TYPES` — tuple of supported git hook types
- `STAGES` — HOOK_TYPES plus `'manual'`
- `load_config()` / `load_manifest()` — `functools.partial`-wrapped loaders
- Migration helpers for deprecated stage/language names
- Warning classes for mutable refs and suspicious regexes
- `META` and `LOCAL` constants

### `pre_commit/hook.py`
`Hook` is a `NamedTuple` with all hook fields: `src`, `prefix`, `id`, `name`, `entry`, `language`, `alias`, `files`, `exclude`, `types`, `types_or`, `exclude_types`, `additional_dependencies`, `args`, `always_run`, `fail_fast`, `pass_filenames`, `description`, `language_version`, `log_file`, `minimum_pre_commit_version`, `require_serial`, `stages`, `verbose`. The `install_key` property uniquely identifies an environment.

### `pre_commit/store.py`
`Store` manages the persistent cache at `~/.cache/pre-commit/` (overridable via `PRE_COMMIT_HOME` or `XDG_CACHE_HOME`). Uses SQLite (`db.db`) to track `(repo, ref) → path` mappings. Provides:
- `clone(repo, ref, deps)` — shallow clone with full-clone fallback
- `make_local(deps)` — create local repo scaffold
- `exclusive_lock()` — file-based locking for concurrent safety
- `mark_config_used(path)` — tracks which config files are active (for `gc`)

### `pre_commit/repository.py`
Bridges config/manifest loading with environment installation:
- `all_hooks(root_config, store)` — returns all `Hook` objects from config
- `install_hook_envs(hooks, store)` — installs environments for hooks that need it
- `_hook_installed(hook)` — checks install state files
- Handles local, meta, and cloned repo hook variants

### `pre_commit/lang_base.py`
Defines the `Language` protocol (structural typing) and shared helpers:
- `Language` protocol with `ENVIRONMENT_DIR`, `install_environment`, `in_env`, `run_hook`, `health_check`, `get_default_version`
- `basic_run_hook()` — default run_hook delegating to `run_xargs`
- `run_xargs()` — shuffles files deterministically, calls `xargs.xargs`
- `hook_cmd()` — parses `entry` via `shlex.split`, handles `pre-commit hazmat` aliasing
- `environment_dir()` — path for `<env_dir>-<version>` directory

### `pre_commit/commands/run.py`
The main hook execution engine:
- `Classifier` — filters filenames by type tags and regexes
- `_run_single_hook()` — runs one hook, detects file modifications via diff
- `run()` — top-level function; manages stashing, config loading, hook filtering, skip sets
- Sets numerous `PRE_COMMIT_*` environment variables for hooks to consume

### `pre_commit/xargs.py`
Platform-aware parallel subprocess runner:
- `partition()` — splits file list into batches respecting `SC_ARG_MAX` (POSIX) or 32KB (Windows)
- `xargs()` — runs partitions concurrently with `ThreadPoolExecutor`
- Handles color via PTY (`cmd_output_p`) vs plain (`cmd_output_b`)

### `pre_commit/staged_files_only.py`
Context manager that temporarily removes unstaged changes using `git diff-index --binary` + patch files, then restores them after hooks run. Handles intent-to-add files separately.

## Code Organization Patterns

- **Protocol-based polymorphism**: Language backends implement the `Language` protocol from `lang_base.py` without inheriting from a base class. The `languages` dict in `all_languages.py` maps names to modules (each module serves as a singleton object implementing the protocol).
- **NamedTuple for immutable data**: `Hook`, `RevInfo` use `NamedTuple` for simple, hashable, immutable data.
- **`functools.partial` for schema loaders**: `load_config` and `load_manifest` are partials of `cfgv.load_from_filename`.
- **Context managers for environment isolation**: `in_env()` in each language module uses `envcontext` to patch `os.environ` temporarily.
- **Atomic file operations**: Store uses temp files + `os.replace()` for atomic writes; SQLite transactions for DB integrity.
- **`cfgv` for schema-driven validation**: All YAML loading goes through cfgv, which validates and applies defaults in one pass.
