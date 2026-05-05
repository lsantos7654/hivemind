# MCP Python SDK — Build System

## Build System Type and Configuration Files

The MCP Python SDK uses **Hatchling** as its build backend with **uv** as the package manager and dependency resolver. The project is configured as a **uv workspace** that includes the main `mcp` package plus example sub-projects.

Key configuration files:
- **`pyproject.toml`**: Single source of truth for project metadata, dependencies, build configuration, tool settings (ruff, pyright, pytest, coverage).
- **`uv.lock`**: Locked dependency tree for reproducible installs across all workspace members.
- **`mkdocs.yml`**: Documentation site configuration (MkDocs with Material theme).
- **`.pre-commit-config.yaml`**: Pre-commit hooks for linting and formatting.

## External Dependencies and Management

### Runtime Dependencies (always installed)
```toml
dependencies = [
    "anyio>=4.5",              # Async I/O (asyncio + trio)
    "httpx>=0.27.1",           # HTTP client for SSE/StreamableHTTP transports
    "httpx-sse>=0.4",          # SSE support for httpx
    "pydantic>=2.11.0,<3.0.0", # Data validation + JSON schema generation
    "starlette>=0.27",         # ASGI framework for HTTP transports
    "python-multipart>=0.0.9", # Multipart form parsing (Starlette dependency)
    "sse-starlette>=1.6.1",    # SSE response support
    "pydantic-settings>=2.5.2",# Settings from env vars (FASTMCP_* prefix)
    "uvicorn>=0.31.1",         # ASGI server (not on emscripten)
    "jsonschema>=4.20.0",      # Runtime JSON schema validation for tool inputs
    "pywin32>=310",            # Windows process utilities (win32 only)
    "pyjwt[crypto]>=2.10.1",   # JWT verification for OAuth bearer tokens
    "typing-extensions>=4.9.0",# Backports for older Python versions
    "typing-inspection>=0.4.1",# Function signature introspection
]
```

### Optional Extras
```toml
[project.optional-dependencies]
rich = ["rich>=13.9.4"]                          # Rich terminal output
cli = ["typer>=0.16.0", "python-dotenv>=1.0.0"]  # mcp CLI tools
ws = ["websockets>=15.0.1"]                       # WebSocket transport
```

Install with extras:
```bash
pip install "mcp[cli]"      # CLI tools
pip install "mcp[ws]"       # WebSocket support
pip install "mcp[cli,ws]"   # Both
```

### Development Dependencies
```toml
[dependency-groups]
dev = [
    "pyright>=1.1.400",          # Static type checking
    "pytest>=8.3.4",             # Test framework
    "ruff>=0.8.5",               # Linter + formatter
    "trio>=0.26.2",              # Trio backend for anyio tests
    "pytest-flakefinder>=1.1.0", # Flaky test detection
    "pytest-xdist>=3.6.1",       # Parallel test execution
    "pytest-examples>=0.0.14",   # Test code examples in docs
    "pytest-pretty>=1.2.0",      # Pretty test output
    "inline-snapshot>=0.23.0",   # Snapshot testing
    "dirty-equals>=0.9.0",       # Flexible equality assertions
    "coverage[toml]==7.10.7",    # Code coverage (pinned)
]
docs = [
    "mkdocs>=1.6.1",
    "mkdocs-glightbox>=0.4.0",
    "mkdocs-material[imaging]>=9.5.45",
    "mkdocstrings-python>=1.12.2",
]
```

## Build Targets and Commands

### Versioning
The project uses **uv-dynamic-versioning** to derive the version from git tags:
```toml
[tool.hatch.version]
source = "uv-dynamic-versioning"

[tool.uv-dynamic-versioning]
vcs = "git"
style = "pep440"
bump = true
```
The version is automatically computed from the nearest git tag (e.g., `v1.27.0` → `1.27.0`).

### Package Build
```bash
uv build                    # Build wheel + sdist into dist/
```
The wheel includes only `src/mcp` (configured via `[tool.hatch.build.targets.wheel] packages = ["src/mcp"]`).

### CLI Entry Point
```toml
[project.scripts]
mcp = "mcp.cli:app [cli]"
```
The `mcp` command is only available when the `cli` extra is installed.

## How to Build, Test, and Deploy

### Installation for Development
```bash
# Clone and install in editable mode with all dev dependencies
git clone https://github.com/modelcontextprotocol/python-sdk
cd python-sdk
uv sync --all-groups          # Install all dependency groups
```

### Running Tests
```bash
# Run full test suite (parallel by default via pytest-xdist)
uv run pytest

# Run specific test file
uv run pytest tests/server/fastmcp/test_server.py

# Run with coverage
uv run coverage run -m pytest
uv run coverage report

# Run with a specific anyio backend
uv run pytest --anyio-backend=trio
```

Pytest configuration in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
log_cli = true
xfail_strict = true
addopts = "--color=yes --capture=fd --numprocesses auto"
```
Tests run in parallel across all available CPUs by default (`--numprocesses auto`).

### Linting and Formatting
```bash
uv run ruff check src/ tests/    # Lint
uv run ruff format src/ tests/   # Format
uv run ruff check --fix          # Auto-fix lint issues
```

Ruff is configured with rules: `C4` (comprehensions), `C90` (complexity), `E`/`F` (pycodestyle/pyflakes), `I` (isort), `PERF` (performance), `PL` (pylint), `UP` (pyupgrade). Line length: 120.

### Type Checking
```bash
uv run pyright                   # Type check (strict mode)
```
Pyright is configured in strict mode for `src/mcp`, `tests`, and `examples/servers`. Some test-specific rules are relaxed (`reportUnusedFunction`, `reportPrivateUsage`).

### Documentation
```bash
uv run mkdocs serve              # Local docs server
uv run mkdocs build              # Build static site
```

### Running the MCP CLI
```bash
# Run a server file directly
uv run mcp run server.py

# Run in development mode with MCP Inspector
uv run mcp dev server.py

# Install a server into Claude Desktop
uv run mcp install server.py --name "My Server"

# Check version
uv run mcp version
```

### Running Example Servers
```bash
# FastMCP quickstart (StreamableHTTP)
uv run examples/snippets/servers/fastmcp_quickstart.py

# Then connect with Claude Code
claude mcp add --transport http my-server http://localhost:8000/mcp

# Or inspect with MCP Inspector
npx -y @modelcontextprotocol/inspector
```

### Coverage Requirements
The project enforces 100% code coverage (`fail_under = 100`) with `pragma: no cover` annotations for untestable branches. Coverage is measured with branch coverage enabled.

### uv Workspace
The `pyproject.toml` defines a uv workspace:
```toml
[tool.uv.workspace]
members = ["examples/clients/*", "examples/servers/*", "examples/snippets"]

[tool.uv.sources]
mcp = { workspace = true }
```
All example sub-projects reference the local `mcp` package from the workspace, ensuring they always test against the current source.

### Python Version Support
Requires Python ≥ 3.10. Tested against 3.10, 3.11, 3.12, and 3.13. The `target-version = "py310"` ruff setting ensures no syntax above Python 3.10 is used.
