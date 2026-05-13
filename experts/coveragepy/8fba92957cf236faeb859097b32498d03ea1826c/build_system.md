# Coverage.py — Build System

## Build System Overview

Coverage.py uses **setuptools** as its build backend (declared in `pyproject.toml` `[build-system]`), with a **C extension** (`coverage.tracer`) that builds optionally — the package falls back to pure Python tracing if the C extension can't be compiled (e.g., on PyPy, or when `COVERAGE_DISABLE_EXTENSION=1` is set).

## Key Build Files

| File | Purpose |
|---|---|
| `setup.py` | Main build script: C extension compilation, `.pth` file generation, entry points, extras |
| `pyproject.toml` | Build system declaration, tool configs (mypy, pylint, pytest, ruff, scriv) |
| `Makefile` | Developer convenience targets: `venv`, `install`, `test`, `lint`, `mypy`, `kit`, `upgrade` |
| `tox.ini` | Multi-environment test orchestration for Python 3.10–3.15 + PyPy3 |
| `MANIFEST.in` | Files included in sdist |
| `.github/workflows/kit.yml` | cibuildwheel-powered multi-platform wheel building |
| `.github/workflows/publish.yml` | PyPI publication workflow |

## C Extension (`coverage.tracer`)

Defined in `setup.py` lines 238–253:
```python
Extension(
    "coverage.tracer",
    sources=[
        "coverage/ctracer/datastack.c",
        "coverage/ctracer/filedisp.c",
        "coverage/ctracer/module.c",
        "coverage/ctracer/tracer.c",
    ],
)
```

The build uses `ve_build_ext` (a subclass of `setuptools.command.build_ext.build_ext`) that wraps compilation in `BuildFailed` exception handling. If the extension fails to build, `setup()` retries without it. On MSVC, C11 atomics flags are added (`/std:c11 /experimental:c11atomics`). The extension is automatically skipped on PyPy (detected via `platform.python_implementation()`).

Environment variable `COVERAGE_DISABLE_EXTENSION` can force skipping the extension build.

## Entry Points

From `setup.py`:
- `coverage = coverage.cmdline:main` — the primary `coverage` CLI command
- `coverage3 = coverage.cmdline:main_deprecated` (deprecated)
- `coverage-X.Y = coverage.cmdline:main_deprecated` (deprecated)

The package is not `zip_safe` because it needs to access `htmlfiles/*.*` as filesystem assets.

## `.pth` File Generation

During setup, `make_pth_file()` reads `coverage/pth_file.py`, strips comments, minifies the code, and writes `a1_coverage.pth` containing `import sys; exec(...)`. This `.pth` file auto-starts coverage measurement in subprocesses when `COVERAGE_PROCESS_START` is set. The name prefix `a1_` ensures it runs early in the `.pth` loading order (after editable install `__editable__*.pth` files but before most user packages).

## Extras

- `[toml]` extra: provides `tomli` (for Python < 3.11), enabling `pyproject.toml` configuration reading via `coverage/tomlconfig.py`.

## Build Commands

| Command | Purpose |
|---|---|
| `pip install .` | Standard install with C extension |
| `COVERAGE_DISABLE_EXTENSION=1 pip install .` | Install without C extension (pure Python only) |
| `python setup.py build_ext --inplace` | In-place C extension build for development/testing |
| `python -m build` | Build both sdist and binary wheel |
| `COVERAGE_DISABLE_EXTENSION=1 python -m build --wheel` | Build py3-none-any wheel (no extension) |
| `make kit` | Combined: sdist + binary + pure wheel builds |

## Test Infrastructure

Testing uses **tox** with per-Python-version environments. Each tox env:
1. Runs `igor.py zip_mods` (build test fixture zip files)
2. Builds the C extension in-place: `python setup.py build_ext --inplace`
3. Installs coverage in editable mode: `pip install -e .`
4. Runs `igor.py clean_for_core <core>` + `igor.py test_with_core <core>`
5. Repeats for each tracer core (ctrace, pytrace, sysmon on 3.12+)

Tests use **pytest** with plugins:
- `pytest-xdist` for parallel test execution (`-n auto --dist loadgroup`)
- `pytest-flaky` for rerunning flaky tests
- `pytest-failed-first` for running previous failures first
- `Hypothesis` for property-based testing (`HYPOTHESIS_PROFILE=ci` in CI)

The `tools/pytest` config in `pyproject.toml` sets default options: `-q -n auto --dist loadgroup -p no:legacypath --no-flaky-report -rfEX --failed-first`, `strict = true`, `python_classes = ["*Test"]`.

## Quality Tools

| Tool | Config Location | Purpose |
|---|---|---|
| MyPy | `pyproject.toml [tool.mypy]` | Strict type checking (`disallow_untyped_defs=true`, etc.) |
| Pylint | `pyproject.toml [tool.pylint.*]` | Code quality (lenient config, many checks disabled) |
| Ruff | `pyproject.toml [tool.ruff]` | Code formatting only (linting disabled), line-length=100 |
| pre-commit | `.pre-commit-config.yaml` | Pre-commit hooks: trailing-whitespace, end-of-file-fixer, check-yaml, etc. |
| check-manifest | `Makefile lint` | Verify MANIFEST.in completeness |

## Dependency Management

Dependencies follow a `pip-compile` (uv pip compile) pattern:
- `.in` files declare direct dependencies
- `.pip` files are compiled with full hashes (`--generate-hashes`) and universal resolution (`--universal`)
- `make upgrade` updates all `.pip` files with a 10-day cooldown (`UV_EXCLUDE_NEWER=P10D`)
- `make upgrade_one package=<name>` upgrades a single package without cooldown

Key dependency groups:
- `requirements/pip.pip` — core pip dependencies (pip, setuptools)
- `requirements/pytest.pip` — pytest + plugins + hypothesis
- `requirements/dev.pip` — linting/formatting tools
- `requirements/light-threads.pip` — concurrency libs (greenlet, eventlet, gevent)
- `requirements/mypy.pip` — type checker
- `requirements/kit.pip` — wheel building (build, cibuildwheel)
- `requirements/tox.pip` — tox + tox-gh
- `doc/requirements.pip` — Sphinx + extensions

## CI/CD Pipelines

GitHub Actions workflows (in `.github/workflows/`):
- **Testsuite** (`testsuite.yml`): Matrix of OS × Python version, runs tox per-core tests; 15min timeout per job
- **Quality** (`quality.yml`): Lint, mypy, docs build, link check, pre-commit verification
- **Kits** (`kit.yml`): cibuildwheel builds wheels for all platforms (manylinux, macOS, Windows, PyPy, free-threaded)
- **Coverage** (`coverage.yml`): Meta-coverage — runs test suite measuring coverage.py with itself
- **Publish** (`publish.yml`): PyPI publication from GitHub Releases
- **Python Nightly** (`python-nightly.yml`): Tests against CPython nightly builds
- **CodeQL** (`codeql-analysis.yml`): Static security analysis
- **Dependency Review** (`dependency-review.yml`): Vulnerability scanning for dependency changes

## Releases

Release management is scripted in `igor.py` and `howto.txt`:
- `make release_version` → `make edit_for_release` → `make relbranch` → `make relcommit1` → `make relcommit2` → `make tag` → `make build_kits` → `make pypi_upload`
- Changelogs managed via `scriv` (configured in `pyproject.toml [tool.scriv]`)
- GitHub releases auto-generated from changelog entries via `make github_releases`