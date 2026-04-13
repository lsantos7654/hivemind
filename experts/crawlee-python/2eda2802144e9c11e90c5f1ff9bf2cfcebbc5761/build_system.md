# Crawlee for Python — Build System

## Build System Type

Crawlee uses **Hatchling** as its PEP 517 build backend and **uv** as the package manager. Task automation is handled by **poethepoet** (`poe`). The single source of truth for all build, dependency, and tool configuration is `pyproject.toml`.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

The wheel build target is:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/crawlee"]
```

This means only the `src/crawlee/` package is included in distributions; tests, docs, and the website are excluded.

## External Dependencies

### Core (always installed)

| Package | Version constraint | Role |
|---|---|---|
| `impit` | `>=0.8.0` | Default HTTP client with TLS fingerprint impersonation |
| `pydantic` | `>=2.11.0` | Data models for Request, Configuration, storage models |
| `pydantic-settings` | `>=2.12.0` | Environment-variable-backed Configuration class |
| `pyee` | `>=9.0.0` | Event emitter (EventManager) |
| `psutil` | `>=6.0.0` | CPU/memory metrics for autoscaling |
| `yarl` | `>=1.18.0` | URL parsing and manipulation |
| `tldextract` | `>=5.1.0` | Extracts eTLD+1 for enqueue strategies |
| `protego` | `>=0.5.0` | robots.txt parsing |
| `cachetools` | `>=5.5.0` | LRU cache for robots.txt and dedup |
| `more-itertools` | `>=10.2.0` | Iterator utilities |
| `colorama` | `>=0.4.0` | Cross-platform terminal colors |
| `async-timeout` | `>=5.0.1` | Async timeout helpers |
| `typing-extensions` | `>=4.1.0` | Backports for Python 3.10 compatibility |

### Optional Extras

Install with `pip install 'crawlee[<extra>]'` or `pip install 'crawlee[all]'`.

| Extra | Key packages | Purpose |
|---|---|---|
| `beautifulsoup` | `beautifulsoup4[lxml]>=4.12.0`, `html5lib>=1.0` | BeautifulSoupCrawler HTML parsing |
| `parsel` | `parsel>=1.10.0` | ParselCrawler XPath/CSS parsing |
| `playwright` | `playwright>=1.27.0`, `browserforge>=1.2.3`, `apify_fingerprint_datapoints>=0.0.2` | PlaywrightCrawler browser automation |
| `adaptive-crawler` | `playwright`, `scikit-learn>=1.6.0`, `jaro-winkler>=2.0.3`, `browserforge>=1.2.4`, `apify_fingerprint_datapoints>=0.0.3` | AdaptivePlaywrightCrawler with ML predictor |
| `httpx` | `httpx[brotli,http2,zstd]>=0.27.0`, `browserforge`, `apify_fingerprint_datapoints` | HttpxHttpClient |
| `curl-impersonate` | `curl-cffi>=0.9.0` | CurlImpersonateHttpClient (TLS impersonation) |
| `cli` | `cookiecutter>=2.6.0`, `inquirer>=3.3.0`, `rich>=13.9.0`, `typer>=0.12.0` | `crawlee create` project scaffold command |
| `sql_sqlite` | `sqlalchemy[asyncio]>=2.0.0,<3.0.0`, `aiosqlite>=0.21.0` | SQLite storage backend |
| `sql_postgres` | `sqlalchemy[asyncio]>=2.0.0,<3.0.0`, `asyncpg>=0.24.0` | PostgreSQL storage backend |
| `sql_mysql` | `sqlalchemy[asyncio]>=2.0.0,<3.0.0`, `aiomysql>=0.3.2`, `cryptography` | MySQL storage backend |
| `redis` | `redis[hiredis]>=7.0.0` | Redis storage backend |
| `otel` | `opentelemetry-api>=1.34.1`, `opentelemetry-sdk>=1.34.1`, `opentelemetry-distro[otlp]`, `opentelemetry-instrumentation-httpx`, `wrapt>=1.17.0` | OpenTelemetry distributed tracing |
| `all` | All of the above (except `sql_mysql`) | Everything |

### Dev Dependencies (`[dependency-groups.dev]`)

The `dev` group includes all testing, linting, and type-checking tools:

- `ruff~=0.15.0` — linter and formatter
- `ty~=0.0.0` — Astral's type checker (replaces mypy for this project)
- `pytest<10.0.0`, `pytest-asyncio<2.0.0`, `pytest-xdist<4.0.0`, `pytest-cov<8.0.0`, `pytest-rerunfailures<17.0.0`, `pytest-timeout<3.0.0` — test framework
- `fakeredis[probabilistic,json,lua]<3.0.0` — in-memory Redis mock for tests
- `apify_client` — for e2e tests on the Apify platform
- `pre-commit<5.0.0` — git hook manager
- `poethepoet<1.0.0` — task runner
- `pydoc-markdown<5.0.0` — API doc generation
- `proxy-py<3.0.0` — local proxy server for proxy tests
- `uvicorn[standard]<1.0.0` — local test HTTP server

## Build Targets and Commands

All commands are run with `uv run poe <task>` (or directly via `uv run <tool>`).

### Installation

```bash
# Install all dependencies (including all extras) and dev tools, then set up pre-commit + Playwright
uv run poe install-dev
# Equivalent to:
uv sync --all-extras && uv run pre-commit install && uv run playwright install

# Just sync dependencies without pre-commit/playwright
uv run poe install-sync
# Equivalent to:
uv sync --all-extras
```

### Linting

```bash
# Check formatting (ruff format --check) + lint rules (ruff check)
uv run poe lint

# Auto-fix formatting and fixable lint issues
uv run poe format
# Equivalent to:
uv run ruff check --fix && uv run ruff format
```

### Type Checking

```bash
# Run Astral ty type checker
uv run poe type-check
# Equivalent to:
uv run ty check
```

The type checker targets Python 3.10 and covers `src/`, `tests/`, `scripts/`, `docs/`, and `website/`. The `project_template/` and `versioned_docs/` directories are excluded.

### Testing

```bash
# Run all unit tests (isolation-sensitive tests first, then the rest in parallel)
uv run poe unit-tests

# Run unit tests with coverage (XML report → coverage-unit.xml)
uv run poe unit-tests-cov

# Run a single test file
uv run pytest tests/unit/path/to/test_file.py

# Run a single test by name
uv run pytest tests/unit/path/to/test_file.py::test_name -v

# Run end-to-end template tests (requires Apify credentials)
uv run poe e2e-templates-tests
```

The `unit-tests` task runs in two phases:
1. Tests marked `@pytest.mark.run_alone` are run with `--numprocesses=1` (no parallelism).
2. All other tests run with `--numprocesses=${TESTS_CONCURRENCY:-auto}` and `-x` (fail-fast) via `pytest-xdist`.

### Build and Publish

```bash
# Build the wheel and sdist
uv run poe build
# Equivalent to:
uv build --verbose

# Publish to PyPI (requires APIFY_PYPI_TOKEN_CRAWLEE env var)
uv run poe publish-to-pypi
# Equivalent to:
uv publish --verbose --token ${APIFY_PYPI_TOKEN_CRAWLEE}
```

### Full Check Suite

```bash
# Run lint + type-check + unit-tests in sequence
uv run poe check-code
```

### Documentation

```bash
# Build the Docusaurus website (with API reference generation)
cd website && uv run poe build-docs
# Equivalent to:
./build_api_reference.sh && corepack enable && yarn && yarn build

# Run docs dev server
cd website && uv run poe run-docs
```

### Cleanup

```bash
uv run poe clean
# Removes: .coverage, .pytest_cache, .ruff_cache, .ty_cache, dist, htmlcov, website build artifacts
```

## Code Style Configuration

All style settings are in `pyproject.toml` under `[tool.ruff]`:

- **Line length**: 120 characters
- **Quote style**: single quotes (except docstrings, which use double quotes per PEP 257 / Google format)
- **Docstring format**: Google style (enforced by Ruff's `D` rules)
- **Import sorting**: `known-first-party = ["crawlee"]`
- **Ruff select**: `["ALL"]` with an explicit `ignore` list (e.g., `ANN401`, `C901`, `PLR0913`)
- **Per-file ignores**: Tests suppress `D` (pydoc), `S101` (assert), `T20` (print), `SLF001` (private member access)

## Pre-Commit Hooks

Defined in `.pre-commit-config.yaml`. Installs via `uv run pre-commit install`. Hooks run on commit and typically include ruff formatting/linting checks.

## Commit Convention

Conventional Commits format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, etc.

## Supply-Chain Defense

```toml
[tool.uv]
exclude-newer = "24 hours"
```

This ensures that only packages published more than 24 hours ago are resolved, providing a minimal defense against supply-chain attacks that publish malicious versions immediately.

## Environment Variables for Configuration

The `Configuration` class reads the following `CRAWLEE_` prefixed environment variables (among others):

| Variable | Default | Description |
|---|---|---|
| `CRAWLEE_LOG_LEVEL` | `INFO` | Logging verbosity |
| `CRAWLEE_STORAGE_DIR` | `./storage` | Local storage root directory |
| `CRAWLEE_PURGE_ON_START` | `true` | Clear storage on each run start |
| `CRAWLEE_INTERNAL_TIMEOUT` | `None` | Timeout for internal async operations |
| `CRAWLEE_DEFAULT_BROWSER_PATH` | `None` | Path to browser executable |
| `CRAWLEE_DISABLE_BROWSER_SANDBOX` | `false` | Disable Playwright browser sandbox |
| `APIFY_*` | — | Apify platform integration settings |

All configuration can also be set programmatically via `Configuration(...)` and injected into the `ServiceLocator` before starting a crawler.
