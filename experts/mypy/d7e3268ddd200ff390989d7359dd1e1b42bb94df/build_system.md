# Mypy Build System

## Build System Type

Mypy uses **setuptools** with a `pyproject.toml`-based build (`PEP 517/518`). The build backend is `setuptools.build_meta`. There is also a legacy `setup.py` that delegates to the standard setuptools machinery.

**Key build configuration files:**
- `pyproject.toml` — canonical project metadata, dependencies, build config, tool settings
- `setup.py` — legacy setuptools entry (mostly a stub)
- `build-requirements.txt` — additional packages needed only during the build (type stubs for build-time dependencies)
- `mypy-requirements.txt` — runtime dependency list (mirrors `pyproject.toml` dependencies for reference)
- `test-requirements.txt` / `test-requirements.in` — full test dependency set
- `tox.ini` — tox environment definitions for running tests and linters
- `MANIFEST.in` — additional files to include in the sdist
- `action.yml` — GitHub Actions composite action (for using mypy in CI workflows)

## External Dependencies

### Runtime Dependencies (always required)

| Package | Version | Purpose |
|---------|---------|---------|
| `typing_extensions` | `>=4.6.0` | Backports of new typing features used internally and exposed to users |
| `mypy_extensions` | `>=1.0.0` | `@trait`, `@mypyc_attr`, `TypedDict` (legacy), `DefaultNamedArg` etc. |
| `pathspec` | `>=1.0.0` | `.gitignore`-style glob pattern matching for `--exclude` options |
| `tomli` | `>=1.1.0` (Python < 3.11 only) | TOML config file parsing (stdlib `tomllib` used on 3.11+) |
| `librt` | `>=0.8.0` (CPython only) | High-performance binary serialization for the `.mypy_cache` format |

### Optional Dependencies

| Extra | Package | Purpose |
|-------|---------|---------|
| `dmypy` | `psutil>=4.0` | Process and memory stats for the daemon |
| `mypyc` | `setuptools>=50` | Required to compile extensions with mypyc |
| `reports` | `lxml` | XML/HTML type check report generation |
| `faster-cache` | `orjson` | Faster JSON serialization for cache files |
| `native-parser` | `ast-serialize>=0.1.1,<1.0.0` | Native (Rust-based) parser backend |

### Build-time-only Dependencies

Listed in `build-requirements.txt` and `pyproject.toml [build-system].requires`:
- `types-psutil` — type stubs needed when mypy type-checks itself during build
- `types-setuptools` — type stubs for setuptools

### Test Dependencies (`test-requirements.txt`)

- `pytest`, `pytest-xdist` — test runner with parallel execution
- `pytest-cov` — coverage reporting
- `attrs` — needed to test attrs plugin
- `lxml-stubs` — stubs for the lxml report optional dep
- `tomli` — (for Python < 3.11 in test environments)

## Mypyc Compilation

Mypy ships its own source pre-compiled with mypyc for performance. The compilation is handled by `mypyc/build.py` which provides `mypycify()` — a function that produces a list of `setuptools.Extension` objects.

**How mypyc compilation works at build time:**
1. `pyproject.toml` lists `mypyc` as a build-system requirement
2. `setup.py` calls `mypycify()` from `mypyc.build` to compile the mypy package to C extensions
3. The resulting `.so`/`.pyd` files are included in the wheel

The compiled modules are identified by the `__mypyc` naming convention (e.g., `mypy__mypyc`). Only CPython is targeted; PyPy is explicitly unsupported for compiled operation.

## Build Targets and Commands

### Install (development)

```bash
# Standard editable install
pip install -e .

# With all optional extras
pip install -e ".[dmypy,mypyc,reports,faster-cache]"

# Install test requirements
pip install -r test-requirements.txt
```

### Running Tests

```bash
# Full test suite (uses pytest-xdist for parallelism)
python runtests.py

# Equivalent direct pytest invocation
pytest mypy/test mypyc/test

# Single named test
python runtests.py test_name
# or
pytest -n0 -k test_name

# Run all tests in a specific .test file
python runtests.py check-dataclasses.test
# or
pytest mypy/test/testcheck.py::TypeCheckSuite::check-dataclasses.test

# Run self-check (mypy checks mypy's own source)
python runtests.py self
# or
python -m mypy --config-file mypy_self_check.ini -p mypy

# Run linters only
python runtests.py lint
```

### Using tox

```bash
# Default environment (runs all tests)
tox run -e py

# Specific Python version
tox run -e py311

# Linting only
tox run -e lint

# Development environment
tox -e dev -- mypy --verbose test_case.py
```

### Running Formatters and Linters

Mypy uses:
- **black** (line length 99, `skip-magic-trailing-comma = true`) for formatting
- **ruff** (line length 99, many rules enabled) for linting and import sorting

```bash
# Format
black mypy mypyc

# Lint
ruff check mypy mypyc

# Both (via runtests.py)
python runtests.py lint
```

### Building Wheels

```bash
# Standard wheel build
python -m build

# Build with mypyc compilation (for distribution)
python misc/build_wheel.py

# Docker-based wheel build (for manylinux)
python misc/docker/build.py
```

### Type Checking Mypy Itself

Mypy self-checks using two config files:

```bash
# Standard self-check
python -m mypy --config-file mypy_self_check.ini -p mypy

# Bootstrap self-check (before mypyc compilation)
python -m mypy --config-file mypy_bootstrap.ini -p mypy -p mypyc
```

### Stub Generation Utilities

```bash
# Update typeshed copy inside mypy
python misc/sync-typeshed.py

# Update stub package info
python misc/update-stubinfo.py

# Test stubgenc
bash misc/test-stubgenc.sh
```

### Performance and Profiling

```bash
# Profile a type check run
python misc/profile_check.py mypy/

# Compare performance between revisions
python misc/perf_compare.py

# Analyze cache usage
python misc/analyze_cache.py
```

## Package Data

The installed package includes:
- `mypy/py.typed` — PEP 561 marker indicating mypy is typed
- `mypy/typeshed/**/*.py`, `**/*.pyi`, `stdlib/VERSIONS` — bundled typeshed
- `mypy/xml/*.xsd`, `*.xslt`, `*.css` — XML report templates

## CI Configuration

The GitHub Actions workflow (`action.yml`) allows using mypy as a composite action in CI. Tests run in parallel using `pytest-xdist` (`-nauto`). The `pyproject.toml` pytest configuration sets `addopts = "-nauto --strict-markers --strict-config"` and enforces `xfail_strict = true` (unexpected passes become failures).

Coverage is configured via `[tool.coverage]` in `pyproject.toml`, tracking branch coverage on the `mypy` package.
