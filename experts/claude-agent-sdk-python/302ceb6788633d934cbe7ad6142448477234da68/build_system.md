# Claude Agent SDK for Python — Build System

## Build System Type and Configuration Files

The project uses **Python's standard build toolchain** based on `pyproject.toml` (PEP 517/518):

- **`pyproject.toml`** — Primary configuration: metadata, dependencies, tool settings (mypy, ruff, pytest)
- **`scripts/build_wheel.py`** — Custom wheel build script that handles CLI binary bundling
- **`scripts/initial-setup.sh`** — Developer environment bootstrap
- **`scripts/generate-changelog.sh`** — AI-powered changelog generation
- **`.github/workflows/`** — CI/CD pipelines for testing, linting, and publishing

### Build Backend

The project uses **hatchling** as the PEP 517 build backend:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Hatchling is configured to include the bundled CLI binary in the wheel via inclusion patterns in `pyproject.toml`.

## External Dependencies and Management

### Runtime Dependencies

```toml
[project]
dependencies = [
    "anyio >= 4.0.0",
    "mcp >= 0.1.0",
    "typing_extensions >= 4.0.0; python_version < '3.11'",
]
```

- **`anyio`** — Async I/O abstraction over asyncio and trio. Used for subprocess management, async primitives, and backend-agnostic concurrency.
- **`mcp`** — Model Context Protocol library. Enables in-process MCP server creation and tool schema handling.
- **`typing_extensions`** — Backport of newer typing features. Only installed on Python < 3.11.

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest >= 7.0.0",
    "pytest-asyncio >= 0.20.0",
    "anyio[trio] >= 4.0.0",
    "pytest-cov >= 4.0.0",
    "mypy >= 1.0.0",
    "ruff >= 0.1.0",
]
```

### Dependency Management

Dependencies are specified with minimum version bounds only (no upper bounds). There is no `requirements.txt` or lock file — the canonical dependency specification is in `pyproject.toml`. For development setup, install with:

```bash
pip install -e ".[dev]"
```

## Build Targets and Commands

### Standard Python Build

```bash
# Build wheel and sdist
python -m build

# Or using the custom script (recommended for releases)
python scripts/build_wheel.py
python scripts/build_wheel.py --version 0.1.49
python scripts/build_wheel.py --version 0.1.49 --cli-version 2.1.72
```

The custom `build_wheel.py` script:
1. Downloads the Claude Code CLI binary for the current platform
2. Places the binary in `src/claude_agent_sdk/` (bundled into the wheel)
3. Updates `_cli_version.py` with the bundled CLI version
4. Runs `python -m build` to produce wheel and sdist
5. Validates the distribution with `twine check`

### Platform-Specific Wheel Naming

The CI produces platform-specific wheels (not pure Python) because the bundled CLI binary is platform-specific:

| Platform | Wheel Tag |
|---|---|
| Linux x86_64 | `manylinux_2_17_x86_64` |
| Linux aarch64 | `manylinux_2_17_aarch64` |
| macOS arm64 | `macosx_11_0_arm64` |
| macOS x86_64 | `macosx_11_0_x86_64` |
| Windows amd64 | `win_amd64` |

## How to Build, Test, and Deploy

### Initial Development Setup

```bash
# Clone and set up the development environment
git clone https://github.com/anthropics/claude-agent-sdk-python
cd claude-agent-sdk-python
./scripts/initial-setup.sh

# Or manually:
pip install -e ".[dev]"
```

The `initial-setup.sh` script installs the package in editable mode with dev dependencies and configures pre-push git hooks for lint checking.

### Running Unit Tests

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=claude_agent_sdk --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_client.py -v

# Run a specific test
python -m pytest tests/test_client.py::test_query_basic -v
```

### Running End-to-End Tests

E2E tests require a valid Anthropic API key and make real API calls:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python -m pytest e2e-tests/ -v

# Run a specific e2e test
python -m pytest e2e-tests/test_mcp_tools.py -v
```

E2E tests cover:
- MCP tool execution (in-process tool calls)
- Hook event delivery and callback handling
- Partial message streaming (`StreamEvent`)
- Tool permission callbacks
- Structured output (JSON schema validation)
- Sandbox functionality
- Dynamic control flow (interrupt, model switch, etc.)

### Linting and Type Checking

```bash
# Run ruff linter
ruff check src/ tests/

# Run ruff formatter
ruff format src/ tests/

# Run mypy type checker (strict mode)
mypy src/claude_agent_sdk/
```

Ruff is configured in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "PTH", "SIM"]
```

Mypy is configured in strict mode:
```toml
[tool.mypy]
strict = true
python_version = "3.10"
```

### Pytest Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

The `asyncio_mode = "auto"` setting means all `async def test_*` functions are automatically treated as async tests without needing `@pytest.mark.asyncio` decorators.

### Release Process

**Automatic Release (CLI version bump):**
- A commit with message `chore: bump bundled CLI version to X.Y.Z` triggers the auto-release workflow
- SDK patch version auto-increments (0.1.24 → 0.1.25)
- GitHub Actions runs the full test suite on Python 3.10, 3.11, 3.12, and 3.13
- Builds platform-specific wheels and publishes to PyPI

**Manual Release (GitHub Actions):**
1. Navigate to Actions tab → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Specify the desired version number (e.g., `0.1.49`)
4. The workflow builds wheels for all platforms and publishes them

**Release Workflow Steps:**
1. Build wheels for all 5 platform targets in parallel
2. Run unit tests on Python 3.10–3.13
3. Run end-to-end tests
4. Publish to PyPI using trusted publisher (OIDC)
5. Create GitHub Release with changelog

### CI/CD Pipelines

The `.github/workflows/` directory contains:

- **Lint workflow** — Runs ruff and mypy on every PR and push
- **Test workflow** — Runs pytest on Python 3.10–3.13 matrix
- **Publish workflow** — Builds and publishes wheels to PyPI (manual trigger or CLI bump)

### Environment Variables for Build/Test

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required for e2e tests |
| `CLAUDE_CODE_STREAM_CLOSE_TIMEOUT` | Stream close timeout in ms (default: 60000) |
| `CLAUDE_CODE_ENTRYPOINT` | Telemetry identifier (`sdk-py` or `sdk-py-client`) |
| `CLAUDE_CODE_ENABLE_FINE_GRAINED_TOOL_STREAMING` | Enable detailed tool input streaming |
