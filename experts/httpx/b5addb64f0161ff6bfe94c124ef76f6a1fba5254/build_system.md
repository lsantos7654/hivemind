## Build System

### Build System Type

HTTPX uses **Hatchling** as its build backend, configured via `pyproject.toml`. The build system declaration is:

```toml
[build-system]
requires = ["hatchling", "hatch-fancy-pypi-readme"]
build-backend = "hatchling.build"
```

The `hatch-fancy-pypi-readme` plugin is used to dynamically assemble the PyPI README from `README.md` and the latest `CHANGELOG.md` entry.

### Project Metadata

Defined in `pyproject.toml` under `[project]`:
- **Name**: `httpx`
- **Version**: Dynamic, read from `httpx/__version__.py` via `[tool.hatch.version] path = "httpx/__version__.py"`
- **Python**: Requires `>=3.9`, supports 3.9 through 3.13
- **License**: BSD-3-Clause
- **Authors**: Tom Christie

### Dependencies

**Core dependencies** (always installed):
- `certifi` — SSL certificate bundle
- `httpcore==1.*` — Low-level HTTP transport (same Encode team)
- `anyio` — Async I/O backend abstraction (supports asyncio and trio)
- `idna` — Internationalized Domain Names in Applications

**Optional dependency groups** (`[project.optional-dependencies]`):
- `brotli` — Brotli compression support (`brotli` on CPython, `brotlicffi` on PyPy)
- `cli` — Command-line client (`click==8.*`, `pygments==2.*`, `rich>=10,<15`)
- `http2` — HTTP/2 support (`h2>=3,<5`)
- `socks` — SOCKS proxy support (`socksio==1.*`)
- `zstd` — Zstandard compression support (`zstandard>=0.18.0`)

### Build Targets and Commands

**Building**:
```bash
pip install hatchling hatch-fancy-pypi-readme
hatchling build          # Builds sdist and wheel
```

**Installing**:
```bash
pip install httpx                          # Core only
pip install 'httpx[cli]'                   # With CLI
pip install 'httpx[http2]'                 # With HTTP/2
pip install 'httpx[cli,http2,brotli]'      # Multiple extras
```

**Testing**:
```bash
pip install -r requirements.txt            # Install test dependencies
pytest                                      # Run full test suite
pytest -m "not network"                    # Skip network-dependent tests
pytest tests/test_api.py                   # Run specific test file
pytest -k "test_get"                       # Run tests matching pattern
```

The test suite uses pytest with the following configuration (from `pyproject.toml`):
- `addopts = "-rxXs"` — Show extra test summary info
- `filterwarnings = ["error"]` — Treat warnings as errors (with specific ignores for trio deprecation warnings)
- Custom markers: `copied_from` (for tests adapted from other sources), `network` (for tests requiring network access)

**Linting and Type Checking**:
```bash
ruff check httpx/ tests/                   # Lint with ruff
mypy httpx/                                # Type check (strict mode)
```

Ruff configuration (from `pyproject.toml`):
- Rules: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (flake8-bugbear), `PIE` (flake8-pie)
- Ignores: `B904` (raise-without-from-inside-except), `B028` (no-explicit-stacklevel)
- Per-file ignores: `__init__.py` ignores `F403`/`F405` (star imports)

Mypy configuration:
- `strict = true` — Full strict mode
- `ignore_missing_imports = true` — Skip missing stubs for third-party packages
- Tests override: `disallow_untyped_defs = false` but `check_untyped_defs = true`

**CI/CD**:
GitHub Actions workflows in `.github/` run the test suite across multiple Python versions and operating systems.

### Entry Points

The CLI is registered as a console script:
```toml
[project.scripts]
httpx = "httpx:main"
```

This makes the `httpx` command available after `pip install httpx[cli]`.

### Version Management

Version is stored in `httpx/__version__.py`:
```python
__version__ = "0.28.1"
```

Hatchling reads this dynamically via `[tool.hatch.version] path = "httpx/__version__.py"`.

### Source Distribution

The sdist includes:
```toml
[tool.hatch.build.targets.sdist]
include = ["/httpx", "/CHANGELOG.md", "/README.md", "/tests"]
```

### Test Infrastructure

The test suite (`tests/`) uses:
- **pytest** as the test runner
- **trustme** for generating TLS certificates in tests
- **cryptography** for certificate serialization
- **uvicorn** for running ASGI test servers
- **trio** for async backend testing alongside asyncio

The `conftest.py` provides:
- `clean_environ` fixture — sanitizes environment variables between tests
- `app` — A basic ASGI application for testing
- `async_app` — An async ASGI application
- `Server` fixture — A uvicorn server instance for integration tests
- TLS certificate fixtures (`cert_pem_file`, `cert_private_key_file`, `cert_trusted_ca_file`)

Tests are organized into `tests/client/` (client-level integration tests) and `tests/models/` (unit tests for data model classes), plus top-level test files for specific modules (auth, config, content, decoders, exceptions, multipart, timeouts, utils, asgi, wsgi, main, api, status_codes, exported_members).
