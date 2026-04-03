# pre-commit: APIs and Interfaces

## Public APIs and Entry Points

### CLI Entry Point

```
pre-commit = pre_commit.main:main
```

The `main(argv)` function in `pre_commit/main.py:202` is the sole public Python entry point. It accepts an optional `argv` list (defaults to `sys.argv[1:]`).

### Subcommands

| Command | Function | File |
|---------|----------|------|
| `pre-commit run` | `run(config_file, store, args)` | `commands/run.py:338` |
| `pre-commit install` | `install(config_file, store, hook_types, ...)` | `commands/install_uninstall.py:114` |
| `pre-commit uninstall` | `uninstall(config_file, hook_types)` | `commands/install_uninstall.py:164` |
| `pre-commit autoupdate` | `autoupdate(config_file, tags_only, freeze, ...)` | `commands/autoupdate.py:162` |
| `pre-commit clean` | `clean(store)` | `commands/clean.py` |
| `pre-commit gc` | `gc(store)` | `commands/gc.py` |
| `pre-commit install-hooks` | `install_hooks(config_file, store)` | `commands/install_uninstall.py:144` |
| `pre-commit try-repo` | `try_repo(args)` | `commands/try_repo.py` |
| `pre-commit validate-config` | `validate_config(filenames)` | `commands/validate_config.py` |
| `pre-commit validate-manifest` | `validate_manifest(filenames)` | `commands/validate_manifest.py` |
| `pre-commit migrate-config` | `migrate_config(config_file)` | `commands/migrate_config.py` |
| `pre-commit sample-config` | `sample_config()` | `commands/sample_config.py` |
| `pre-commit init-templatedir` | `init_templatedir(config, store, directory, ...)` | `commands/init_templatedir.py` |
| `pre-commit hook-impl` | `hook_impl(store, *, config, color, hook_type, ...)` | `commands/hook_impl.py:256` |

---

## Key Classes and Functions

### `Hook` NamedTuple — `pre_commit/hook.py:13`

```python
class Hook(NamedTuple):
    src: str                           # 'local', 'meta', or repo URL
    prefix: Prefix                     # resolved environment directory
    id: str
    name: str
    entry: str                         # command to run (shlex-parsed)
    language: str                      # e.g. 'python', 'node', 'system'
    alias: str
    files: str                         # regex for files to include
    exclude: str                       # regex for files to exclude
    types: Sequence[str]               # identify tags that ALL must match
    types_or: Sequence[str]            # identify tags where ANY must match
    exclude_types: Sequence[str]
    additional_dependencies: Sequence[str]
    args: Sequence[str]
    always_run: bool
    fail_fast: bool
    pass_filenames: bool
    description: str
    language_version: str
    log_file: str
    minimum_pre_commit_version: str
    require_serial: bool
    stages: Sequence[str]
    verbose: bool

    @property
    def install_key(self) -> tuple[Prefix, str, str, tuple[str, ...]]: ...

    @classmethod
    def create(cls, src: str, prefix: Prefix, dct: dict[str, Any]) -> Hook: ...
```

### `Store` — `pre_commit/store.py:59`

```python
class Store:
    get_default_directory = staticmethod(_get_default_directory)

    def __init__(self, directory: str | None = None) -> None: ...

    # Clone a remote repo at a specific ref; returns local path
    def clone(self, repo: str, ref: str, deps: Sequence[str] = ()) -> str: ...

    # Create a local-repo scaffold directory; returns path
    def make_local(self, deps: Sequence[str]) -> str: ...

    # Exclusive file lock (for concurrent safety)
    @contextlib.contextmanager
    def exclusive_lock(self) -> Generator[None]: ...

    # SQLite connection (transaction)
    @contextlib.contextmanager
    def connect(self, db_path: str | None = None) -> Generator[sqlite3.Connection]: ...

    # Track which config files are in use (for gc)
    def mark_config_used(self, path: str) -> None: ...
```

**Cache location** (in priority order):
1. `PRE_COMMIT_HOME` environment variable
2. `$XDG_CACHE_HOME/pre-commit`
3. `~/.cache/pre-commit`

### `Language` Protocol — `pre_commit/lang_base.py:27`

Each language module implements this protocol:

```python
class Language(Protocol):
    ENVIRONMENT_DIR: str | None  # None = no install needed

    def get_default_version(self) -> str: ...
    def health_check(self, prefix: Prefix, version: str) -> str | None: ...
    def install_environment(
        self, prefix: Prefix, version: str,
        additional_dependencies: Sequence[str],
    ) -> None: ...
    def in_env(self, prefix: Prefix, version: str) -> ContextManager[None]: ...
    def run_hook(
        self, prefix: Prefix, entry: str, args: Sequence[str],
        file_args: Sequence[str], *, is_local: bool,
        require_serial: bool, color: bool,
    ) -> tuple[int, bytes]: ...
```

`lang_base` provides shared implementations:
- `basic_run_hook()` — delegates to `run_xargs`
- `basic_health_check()` — always returns `None` (healthy)
- `basic_get_default_version()` — returns `C.DEFAULT`
- `no_install()` — raises `AssertionError`
- `no_env()` — no-op context manager
- `run_xargs()` — shuffles files and calls `xargs.xargs()`
- `hook_cmd(entry, args)` — parses entry via `shlex.split`, handles `pre-commit hazmat` rewriting

### `Classifier` — `pre_commit/commands/run.py:73`

```python
class Classifier:
    def __init__(self, filenames: Iterable[str]) -> None: ...

    # Filter filenames by identify tags
    def by_types(
        self, names: Iterable[str],
        types: Iterable[str],     # ALL must match
        types_or: Iterable[str],  # ANY must match (if non-empty)
        exclude_types: Iterable[str],
    ) -> Generator[str]: ...

    # Get filenames that apply to a specific hook
    def filenames_for_hook(self, hook: Hook) -> Generator[str]: ...

    @classmethod
    def from_config(
        cls, filenames: Iterable[str], include: str, exclude: str,
    ) -> Classifier: ...  # applies global include/exclude regex first
```

### Config Schema Constants — `pre_commit/clientlib.py`

```python
HOOK_TYPES = (
    'commit-msg', 'post-checkout', 'post-commit', 'post-merge',
    'post-rewrite', 'pre-commit', 'pre-merge-commit', 'pre-push',
    'pre-rebase', 'prepare-commit-msg',
)
STAGES = (*HOOK_TYPES, 'manual')  # 'manual' is not installed as a git hook

LOCAL = 'local'   # repo: local
META = 'meta'     # repo: meta

load_config: Callable[[str], dict[str, Any]]    # loads .pre-commit-config.yaml
load_manifest: Callable[[str], list[dict]]      # loads .pre-commit-hooks.yaml
```

### `xargs` — `pre_commit/xargs.py:131`

```python
def xargs(
    cmd: tuple[str, ...],
    varargs: Sequence[str],
    *,
    color: bool = False,
    target_concurrency: int = 1,
    _max_length: int = ...,  # platform default (SC_ARG_MAX on POSIX)
    **kwargs: Any,
) -> tuple[int, bytes]: ...
```

`partition(cmd, varargs, target_concurrency)` splits `varargs` into batches that fit platform command-length limits.

---

## Configuration Options and Extension Points

### `.pre-commit-config.yaml` Schema

```yaml
# Global options
minimum_pre_commit_version: '4.0'   # Enforce minimum tool version
default_language_version:           # Override default versions per language
  python: python3.11
  node: '18'
default_stages: [pre-commit, pre-push]  # Default stages for all hooks
default_install_hook_types: [pre-commit]  # What `install` installs by default
files: ''           # Global regex to additionally filter files
exclude: '^$'       # Global regex to exclude files
fail_fast: false    # Stop after first failing hook
ci:                 # Configuration for pre-commit.ci (ignored by tool)
  skip: [hook-id]

repos:
  - repo: https://github.com/owner/repo
    rev: v1.2.3                     # Tag, branch, or commit SHA
    hooks:
      - id: hook-id
        # Override any manifest field:
        name: Custom Name
        alias: short-name           # Alternative ID for SKIP= and CLI
        args: [--extra-arg]
        additional_dependencies: [package==1.0]
        files: '\.py$'
        exclude: 'tests/'
        types: [python]
        types_or: []
        exclude_types: []
        stages: [pre-commit]
        always_run: false
        verbose: false
        language_version: python3.11
        require_serial: false
        log_file: '/tmp/hook.log'

  - repo: local                     # Hooks defined inline
    hooks:
      - id: my-local-hook
        name: My Local Hook
        entry: ./scripts/check.sh
        language: script
        # All manifest fields required for local hooks

  - repo: meta                      # Built-in pre-commit meta hooks
    hooks:
      - id: check-hooks-apply
      - id: check-useless-excludes
      - id: identity
```

### `.pre-commit-hooks.yaml` Schema (Hook Manifest)

```yaml
- id: my-hook
  name: My Hook
  description: What this hook does
  entry: my-command                 # Executable + args (shlex parsed)
  language: python                  # Required: one of the supported languages
  minimum_pre_commit_version: '3.0'
  alias: ''                         # Alternative ID
  files: ''                         # Regex for files to include
  exclude: '^$'                     # Regex for files to exclude
  types: [file]                     # identify tags - ALL must match
  types_or: []                      # identify tags - ANY must match
  exclude_types: []
  additional_dependencies: []       # Extra packages to install
  args: []                          # Default args passed before filenames
  always_run: false
  fail_fast: false
  pass_filenames: true              # Pass matched filenames as arguments
  language_version: default
  log_file: ''                      # Write output to this file too
  require_serial: false             # Run without parallelism
  stages: []                        # Empty = all stages
  verbose: false
```

### Environment Variables for Hook Execution

pre-commit sets these environment variables when running hooks (in `commands/run.py`):

| Variable | Value | Set when |
|----------|-------|----------|
| `PRE_COMMIT` | `'1'` | Always |
| `PRE_COMMIT_FROM_REF` | from-ref | `--from-ref` / `--to-ref` used |
| `PRE_COMMIT_TO_REF` | to-ref | `--from-ref` / `--to-ref` used |
| `PRE_COMMIT_ORIGIN` | from-ref | Legacy name for `FROM_REF` |
| `PRE_COMMIT_SOURCE` | to-ref | Legacy name for `TO_REF` |
| `PRE_COMMIT_LOCAL_BRANCH` | local branch | pre-push hooks |
| `PRE_COMMIT_REMOTE_BRANCH` | remote branch | pre-push hooks |
| `PRE_COMMIT_REMOTE_NAME` | remote name | pre-push hooks |
| `PRE_COMMIT_REMOTE_URL` | remote URL | pre-push hooks |
| `PRE_COMMIT_COMMIT_MSG_SOURCE` | commit source | prepare-commit-msg |
| `PRE_COMMIT_COMMIT_OBJECT_NAME` | commit object | prepare-commit-msg |
| `PRE_COMMIT_CHECKOUT_TYPE` | checkout type | post-checkout |
| `PRE_COMMIT_IS_SQUASH_MERGE` | squash flag | post-merge |
| `PRE_COMMIT_REWRITE_COMMAND` | rewrite command | post-rewrite |
| `PRE_COMMIT_PRE_REBASE_UPSTREAM` | upstream | pre-rebase |
| `PRE_COMMIT_PRE_REBASE_BRANCH` | branch | pre-rebase |

### Supported Languages

All 21 language backends (from `pre_commit/all_languages.py:27`):

| Language key | Technology | ENVIRONMENT_DIR |
|-------------|------------|-----------------|
| `python` | virtualenv + pip | `py_env` |
| `node` | nodeenv + npm | `node_env` |
| `ruby` | bundled rbenv + gem | `ruby_env` |
| `golang` | downloads Go or system | `golangenv` |
| `rust` | cargo | `rustenv` |
| `conda` | conda/mamba | `condaenv` |
| `coursier` | cs (Coursier) | `coursier_env` |
| `dart` | pub | `dart_env` |
| `docker` | Docker build | (special) |
| `docker_image` | Docker pull | (special) |
| `dotnet` | dotnet tool | `dotnetenv` |
| `haskell` | stack | `haskell_env` |
| `julia` | Pkg | `juliaenv` |
| `lua` | luarocks | `luaenv` |
| `perl` | cpanm | `perl_env` |
| `r` | renv | `r_env` |
| `swift` | swift build | `swift_env` |
| `pygrep` | regex grep | `None` |
| `fail` | always fails | `None` |
| `unsupported` | system PATH | `None` |
| `unsupported_script` | script files | `None` |

### Usage Examples

**Basic installation and usage:**
```bash
# Install hook scripts into .git/hooks/
pre-commit install

# Run all hooks on staged files (default)
pre-commit run

# Run a specific hook
pre-commit run black

# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files src/foo.py src/bar.py

# Run for a different stage
pre-commit run --hook-stage pre-push
```

**Configuration management:**
```bash
# Update all repos to latest tags
pre-commit autoupdate

# Update and freeze to commit SHAs
pre-commit autoupdate --freeze

# Update specific repos
pre-commit autoupdate --repo https://github.com/psf/black

# Validate config
pre-commit validate-config .pre-commit-config.yaml

# Validate a hook manifest
pre-commit validate-manifest .pre-commit-hooks.yaml

# Migrate old config format
pre-commit migrate-config
```

**Development / testing hooks:**
```bash
# Test hooks from a local repo without installing
pre-commit try-repo /path/to/local/hook/repo

# Test a specific ref from a remote repo
pre-commit try-repo https://github.com/owner/repo --ref main

# Skip specific hooks
SKIP=flake8,black pre-commit run --all-files
```

**Cache management:**
```bash
# Remove unused cached environments
pre-commit gc

# Remove all cached environments
pre-commit clean

# Pre-install all hook environments
pre-commit install-hooks
```

**Integration pattern — Python API usage:**
```python
from pre_commit.main import main

# Run pre-commit programmatically
exit_code = main(['run', '--all-files', '--config', '.pre-commit-config.yaml'])
```

**Writing a custom hook repository:**

`.pre-commit-hooks.yaml`:
```yaml
- id: my-python-linter
  name: My Python Linter
  entry: my-linter
  language: python
  types: [python]
  additional_dependencies: [my-linter==1.0.0]
```

Users reference it in `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/myorg/my-hooks
    rev: v1.0.0
    hooks:
      - id: my-python-linter
```
