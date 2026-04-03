# pre-commit: Build System

## Build System Type and Configuration Files

pre-commit uses the classic **setuptools** build system with `setup.cfg` as the primary metadata file and a minimal `setup.py` shim. It does not use `pyproject.toml`. Testing is orchestrated with **tox** and **pytest**.

**Key configuration files:**

| File | Purpose |
|------|---------|
| `setup.cfg` | Package metadata, dependencies, entry points, mypy config, coverage config |
| `setup.py` | Minimal `setup()` shim to support editable installs |
| `tox.ini` | tox environments + pytest configuration (env vars, test ignores) |
| `requirements-dev.txt` | Development/test dependencies |
| `.pre-commit-config.yaml` | Hooks this project runs on itself |

## Package Metadata (`setup.cfg`)

```ini
[metadata]
name = pre_commit
version = 4.5.1
description = A framework for managing and maintaining multi-language pre-commit hooks.
url = https://github.com/pre-commit/pre-commit
author = Anthony Sottile
license = MIT

[options]
python_requires = >=3.10
install_requires =
    cfgv>=2.0.0
    identify>=1.0.0
    nodeenv>=0.11.1
    pyyaml>=5.1
    virtualenv>=20.10.0

[options.entry_points]
console_scripts =
    pre-commit = pre_commit.main:main

[options.package_data]
pre_commit.resources =
    *.tar.gz
    empty_template_*
    hook-tmpl
```

The package includes bundled binary resources (Ruby tarballs, hook template) via `package_data`.

## External Dependencies

### Runtime Dependencies

| Package | Minimum Version | Role |
|---------|----------------|------|
| `cfgv` | ≥2.0.0 | Schema-based YAML validation with typed fields, defaults, and conditional validation |
| `identify` | ≥1.0.0 | File type detection by content/extension (produces tag sets like `{'python', 'text', 'non-executable'}`) |
| `nodeenv` | ≥0.11.1 | Creates isolated Node.js environments (used by the `node` language backend) |
| `pyyaml` | ≥5.1 | YAML parsing and dumping (`.pre-commit-config.yaml`, `.pre-commit-hooks.yaml`) |
| `virtualenv` | ≥20.10.0 | Creates isolated Python environments (used by the `python` language backend) |

### Development Dependencies (`requirements-dev.txt`)

```
covdefaults>=2.2   # Coverage defaults plugin (sets sensible omit/branch settings)
coverage           # Test coverage measurement
distlib            # Low-level packaging utilities (used by some tests)
pytest             # Test runner
pytest-env         # Sets environment variables for pytest sessions
re-assert          # Regex assertion helpers for tests
```

## Build Targets and Commands

### Installing the Package

```bash
# Standard install
pip install pre-commit

# Development (editable) install from source
pip install -e .

# With dev dependencies
pip install -e . && pip install -r requirements-dev.txt
```

### Running Tests

The primary test configuration lives in `tox.ini`:

```ini
[tox]
envlist = py,pypy3,pre-commit

[testenv]
deps = -rrequirements-dev.txt
passenv = *
commands =
    coverage erase
    coverage run -m pytest {posargs:tests} --ignore=tests/languages --durations=20
    coverage report --omit=pre_commit/languages/*,tests/languages/*
```

**Run the full test suite (excluding language integration tests):**
```bash
tox -e py
```

**Run directly with pytest:**
```bash
pytest tests/ --ignore=tests/languages
```

**Run language-specific tests (require language runtimes installed):**
```bash
pytest tests/languages/python_test.py
pytest tests/languages/node_test.py
# etc.
```

**Run with coverage:**
```bash
coverage erase
coverage run -m pytest tests/ --ignore=tests/languages
coverage report
```

**pytest environment variables** (set automatically by `pytest-env` via `tox.ini`):
```ini
[pytest]
env =
    GIT_AUTHOR_NAME=test
    GIT_COMMITTER_NAME=test
    GIT_AUTHOR_EMAIL=test@example.com
    GIT_COMMITTER_EMAIL=test@example.com
    GIT_ALLOW_PROTOCOL=file
    VIRTUALENV_NO_DOWNLOAD=1
    PRE_COMMIT_NO_CONCURRENCY=1     # Forces single-threaded execution in tests
```

### Running pre-commit on Itself

```bash
# Using tox
tox -e pre-commit

# Directly
pre-commit run --all-files --show-diff-on-failure
```

The project's own `.pre-commit-config.yaml` (checked into the repo) runs a `validate_manifest` hook from its own `.pre-commit-hooks.yaml`.

### Static Type Checking

mypy configuration is embedded in `setup.cfg`:

```ini
[mypy]
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_defs = true
enable_error_code = deprecated
warn_redundant_casts = true
warn_unused_ignores = true

[mypy-testing.*]
disallow_untyped_defs = false

[mypy-tests.*]
disallow_untyped_defs = false
```

Run mypy:
```bash
mypy pre_commit/
```

### Building Distributions

```bash
pip install build
python -m build           # Builds both sdist and wheel
python -m build --wheel   # Wheel only
python -m build --sdist   # Source distribution only
```

The `bdist_wheel` section marks the package as `universal = True` (supports Python 2 and 3 format), though Python 3.10+ is required at runtime.

### Bundled Resource Archives

The `testing/make-archives` script and `testing/get-dart.sh` are infrastructure scripts for rebuilding the bundled language archives (`rbenv.tar.gz`, `ruby-build.tar.gz`, `ruby-download.tar.gz`) that ship inside `pre_commit/resources/`. These archives are version-pinned and rarely need updating.

```bash
# Rebuild Ruby archives (rarely needed)
./testing/make-archives
```

### Environment Variable Controls

| Variable | Effect |
|----------|--------|
| `PRE_COMMIT_HOME` | Override default cache directory (`~/.cache/pre-commit`) |
| `XDG_CACHE_HOME` | Fallback cache root if `PRE_COMMIT_HOME` not set |
| `PRE_COMMIT_NO_CONCURRENCY` | Set to `1` to force single-threaded hook execution |
| `SKIP` | Comma-separated hook IDs/aliases to skip |
| `PRE_COMMIT_ALLOW_NO_CONFIG` | Set to `1` to silently skip when config is missing |
| `TRAVIS` | If set, limits concurrency to 2 (CI workaround) |

## How to Build, Test, and Deploy

**Standard development workflow:**
```bash
git clone https://github.com/pre-commit/pre-commit
cd pre-commit
pip install -e ".[dev]"          # or: pip install -e . -r requirements-dev.txt
pytest tests/ --ignore=tests/languages  # fast unit tests
tox                               # full matrix (py, pypy3, pre-commit)
```

**Package release:**
```bash
python -m build
twine upload dist/*
```
