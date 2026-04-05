# Pydantic — Build System

## Build System Type

Pydantic uses **Hatchling** as its Python build backend (PEP 517/518 compliant), configured in `pyproject.toml`. The project is a **uv workspace** that includes `pydantic-core` (the Rust extension) as a workspace member.

The Rust component (`pydantic-core`) uses **maturin** / **Cargo** for building the PyO3 extension module.

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Primary project config: metadata, dependencies, build backend, tool configs (ruff, pyright, pytest, coverage, codespell) |
| `uv.lock` | Locked dependency manifest for deterministic installs |
| `Makefile` | Developer workflow shortcuts |
| `pydantic-core/Cargo.toml` | Rust package manifest for pydantic-core |
| `pydantic-core/Cargo.lock` | Locked Rust dependency manifest |
| `pydantic-core/build.rs` | Rust build script |
| `pydantic-core/pyproject.toml` | Separate build config for pydantic-core Python package |
| `mkdocs.yml` | Documentation site configuration |

## External Dependencies

### Runtime Dependencies

| Package | Version Constraint | Role |
|---------|-------------------|------|
| `pydantic-core` | `==2.45.0` (exact) | Rust-powered validation/serialization engine |
| `typing-extensions` | `>=4.14.1` | Extended type hint support for older Python versions |
| `annotated-types` | `>=0.6.0` | Standard annotated type metadata (e.g., `Gt`, `Len`) |
| `typing-inspection` | `>=0.4.2` | Runtime type introspection utilities |

### Optional Dependencies

| Extra | Package | Purpose |
|-------|---------|---------|
| `email` | `email-validator>=2.0.0` | Required for `EmailStr` and `NameEmail` types |
| `timezone` | `tzdata` (Windows only, Python ≥3.9) | IANA timezone data for zoneinfo |

### Development Dependency Groups

Managed via `uv` dependency groups (defined in `pyproject.toml`):

- **`dev`** (default): `coverage`, `pytest`, `pytest-mock`, `pytest-pretty`, `pytest-examples`, `dirty-equals`, `faker`, `pytest-benchmark`, `pytest-codspeed`, `pytest-run-parallel`, `packaging`, `jsonschema`, `eval-type-backport`, `pytz`
- **`linting`**: `ruff`, `pyright`, `eval-type-backport`
- **`docs`**: `mkdocs`, `mkdocs-material`, `mkdocstrings-python`, `mike`, `pydantic-settings`, `pydantic-extra-types`, etc.
- **`typechecking`**: `mypy`, `pyright`, `pyrefly`, `pydantic-settings`
- **`testing-extra`**: `cloudpickle`, `devtools`, `sqlalchemy`, `pytest-memray`

## Python Version Support

Python 3.9, 3.10, 3.11, 3.12, 3.13, and 3.14 on CPython and PyPy.

Required uv version: `>=0.8.4`.

## Build Targets and Commands

All common tasks are driven through `make`. The `Makefile` delegates to `uv run` for executing commands in the project virtual environment.

### Installation

```bash
# Install all dependencies including dev extras and pre-commit hooks
make install
# Equivalent to:
uv sync --frozen --all-groups --all-packages --all-extras
uv pip install pre-commit
uv run pre-commit install --install-hooks
```

### Linting and Formatting

```bash
make format          # Auto-format: ruff check --fix + ruff format + cargo fmt (Rust)
make lint            # Lint Python (ruff) + lint Rust
make lint-python     # ruff check + ruff format --check
make lint-rust       # cargo clippy on pydantic-core
make codespell       # Spell checking via pre-commit
```

**Ruff configuration** (from `pyproject.toml`):
- Line length: 120
- Target: Python 3.9
- Selected rules: F (Pyflakes), E (pycodestyle), I (isort), D (pydocstyle, Google convention), UP (pyupgrade), B (bugbear), T10/T20, C4, PERF, PIE, PYI006/062/063/066
- Excludes: `pydantic/v1`, `tests/mypy`, `tests/pydantic_core`

### Type Checking

```bash
make typecheck                    # Run pre-commit typecheck hook (pyright)
make test-typechecking-pyright    # cd tests/typechecking && pyright
make test-typechecking-mypy       # cd tests/typechecking && mypy
make test-typechecking-pyrefly    # cd tests/typechecking && pyrefly check
make test-mypy                    # Run mypy integration tests: pytest tests/mypy --test-mypy
make test-mypy-update             # Update mypy integration test snapshots
```

**Pyright** is configured to check `pydantic/` and `tests/test_pipeline.py`, excluding `pydantic/_hypothesis_plugin.py`, `pydantic/mypy.py`, and `pydantic/v1`.

### Testing

```bash
make test              # Run all tests: coverage run -m pytest --durations=10 --parallel-threads $NUM_THREADS
make testcov           # Run tests + generate HTML and LCOV coverage reports
make test-no-docs      # Run all tests except docs tests
make test-examples     # Run docs examples
make benchmark         # Run pytest benchmarks (pytest-benchmark + pytest-codspeed)
```

**pytest configuration** (from `pyproject.toml`):
- `testpaths = 'tests'`
- `xfail_strict = true` (unexpected passes are failures)
- Benchmark defaults: columns min/mean/stddev/outliers/rounds/iterations, group by group, warmup on, disabled by default
- Warning filters: treat most warnings as errors; ignore specific deprecation warnings

**Coverage configuration**:
- Source: `pydantic` and `pydantic_core`
- Omits: `pydantic/deprecated/*`, `pydantic/v1/*`
- Branch coverage enabled
- Excludes: `raise NotImplementedError`, `@overload`, `Protocol` classes, `assert_never`

### Documentation

```bash
make docs              # Build docs: mkdocs build --strict
make docs-serve        # Build and serve docs locally with live reload
```

Documentation uses MkDocs with the Material theme, mkdocstrings-python for API reference, and mike for versioned docs.

### Other Targets

```bash
make rebuild-lockfiles  # uv lock --upgrade (regenerate uv.lock from scratch)
make update-v1          # Run update_v1.sh to sync pydantic/v1 namespace
make clean              # Remove __pycache__, *.pyc, .coverage, build/, dist/, site/, htmlcov/
make all                # Full CI check: lint + typecheck + codespell + testcov
```

## How to Build the Python Package

```bash
# Build sdist and wheel
uv run python -m build

# The pyproject.toml sdist includes only:
#   /README.md, /HISTORY.md, /Makefile, /pydantic, /tests
```

The `hatch-fancy-pypi-readme` plugin constructs the PyPI readme from `README.md` + excerpts of `HISTORY.md`, with automatic GitHub issue/PR link substitution.

The version is read dynamically from `pydantic/version.py` via the `[tool.hatch.version]` hook.

## pydantic-core (Rust) Build

`pydantic-core` is a workspace member and is included in `uv sync`. Rust toolchain (`rustup`) is required for development. The Makefile targets for Rust include:

```bash
make lint-rust    # cargo clippy in pydantic-core
make format       # includes cargo fmt --manifest-path pydantic-core/Cargo.toml
```

For local development without building Rust from scratch, the uv workspace pins `pydantic-core` to the workspace path (`uv.sources.pydantic-core = { workspace = true }`), which will build the Rust extension automatically during `uv sync`.
