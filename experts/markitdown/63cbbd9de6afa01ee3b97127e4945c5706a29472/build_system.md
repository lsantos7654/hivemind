# MarkItDown — Build System

## Build System Type

The entire monorepo uses **Hatchling** as the build backend and **Hatch** as the project management tool. All four packages share the same pattern:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Hatch provides virtual environment management, test runner integration, and script shortcuts. The project does **not** use `setup.py`, `setup.cfg`, or `poetry`. All configuration is in `pyproject.toml` per package.

## Configuration Files

| File | Purpose |
|---|---|
| `packages/markitdown/pyproject.toml` | Core library: version, deps, optional extras, hatch envs, coverage config |
| `packages/markitdown-mcp/pyproject.toml` | MCP server package config |
| `packages/markitdown-sample-plugin/pyproject.toml` | Sample plugin; also declares the `markitdown.plugin` entry-point |
| `packages/markitdown-ocr/pyproject.toml` | OCR plugin config |
| `.pre-commit-config.yaml` | Pre-commit hooks (linting/formatting checks before commit) |
| `Dockerfile` (root) | Docker build for the CLI tool |
| `packages/markitdown-mcp/Dockerfile` | Docker build for the MCP server |

## Core Library Dependencies (`packages/markitdown/pyproject.toml`)

### Required (always installed)

```toml
dependencies = [
  "beautifulsoup4",          # HTML parsing
  "requests",                # HTTP fetching
  "markdownify",             # HTML-to-Markdown conversion
  "magika~=0.6.1",           # Google's content-type detection (pinned minor)
  "charset-normalizer",      # Character encoding detection
  "defusedxml",              # Safe XML parsing (prevents XML bombs)
]
```

### Optional Feature Groups

```toml
[project.optional-dependencies]
all   = [python-pptx, mammoth~=1.11.0, pandas, openpyxl, xlrd, lxml,
         pdfminer.six>=20251230, pdfplumber>=0.11.9, olefile, pydub,
         SpeechRecognition, youtube-transcript-api~=1.0.0,
         azure-ai-documentintelligence, azure-identity]
pptx  = ["python-pptx"]
docx  = ["mammoth~=1.11.0", "lxml"]
xlsx  = ["pandas", "openpyxl"]
xls   = ["pandas", "xlrd"]
pdf   = ["pdfminer.six>=20251230", "pdfplumber>=0.11.9"]
outlook              = ["olefile"]
audio-transcription  = ["pydub", "SpeechRecognition"]
youtube-transcription = ["youtube-transcript-api~=1.0.0"]
az-doc-intel         = ["azure-ai-documentintelligence", "azure-identity"]
```

Install a specific group: `pip install 'markitdown[pdf,docx]'`  
Install everything: `pip install 'markitdown[all]'`

### MCP Package Dependencies

```toml
# packages/markitdown-mcp/pyproject.toml
dependencies = [
  "mcp~=1.8.0",                        # MCP Python SDK (pinned minor)
  "markitdown[all]>=0.1.1,<0.2.0",    # Core library with all extras
]
```

The MCP server also implicitly uses `uvicorn` and `starlette` (declared as transitive deps from `mcp`) for the HTTP/SSE transport.

### Sample Plugin Dependencies

```toml
# packages/markitdown-sample-plugin/pyproject.toml
dependencies = [
  "markitdown>=0.1.0a1",   # Core library (any 0.1.x)
  "striprtf",               # RTF parsing
]
```

## Build Targets and Entry Points

### CLI Entry Point

```toml
# packages/markitdown/pyproject.toml
[project.scripts]
markitdown = "markitdown.__main__:main"
```

After `pip install markitdown`, the `markitdown` executable is available.

### MCP Server Entry Point

```toml
# packages/markitdown-mcp/pyproject.toml
[project.scripts]
markitdown-mcp = "markitdown_mcp.__main__:main"
```

### Plugin Entry Point Convention

Third-party plugins must declare an entry point in group `markitdown.plugin`:

```toml
# packages/markitdown-sample-plugin/pyproject.toml
[project.entry-points."markitdown.plugin"]
sample_plugin = "markitdown_sample_plugin"
```

The value `"markitdown_sample_plugin"` is the Python module path; it must expose `register_converters(markitdown, **kwargs)`.

## How to Build

### Install from PyPI

```bash
pip install 'markitdown[all]'        # Install everything
pip install 'markitdown[pdf,docx]'   # Install specific extras
pip install markitdown-mcp           # Install MCP server (includes markitdown[all])
```

### Install from Source (Development Mode)

```bash
git clone git@github.com:microsoft/markitdown.git
cd markitdown

# Install core library in editable mode with all extras
pip install -e 'packages/markitdown[all]'

# Install sample plugin (optional)
pip install -e 'packages/markitdown-sample-plugin'

# Install MCP server
pip install -e 'packages/markitdown-mcp'
```

### Using `uv` (recommended for speed)

```bash
uv venv --python=3.12 .venv
source .venv/bin/activate
uv pip install -e 'packages/markitdown[all]'
```

## How to Test

Tests use **Hatch** as the test runner (which wraps `pytest` internally).

```bash
# Navigate to the core package
cd packages/markitdown

# Install hatch if not already installed
pip install hatch

# Enter the hatch shell (activates the default env with all extras + openai)
hatch shell

# Run all tests
hatch test

# Run a specific test file
hatch test tests/test_module_vectors.py

# Run tests with coverage
hatch test --cover
```

The default Hatch test environment (`hatch-test`) installs all optional dependencies plus `openai` (needed for LLM-related test cases):

```toml
[tool.hatch.envs.hatch-test]
features = ["all"]
extra-dependencies = ["openai"]
```

### Pre-commit Checks

Before submitting a PR, run all pre-commit hooks:

```bash
pre-commit run --all-files
```

### Type Checking

```toml
[tool.hatch.envs.types]
features = ["all"]
extra-dependencies = ["openai", "mypy>=1.0.0"]

[tool.hatch.envs.types.scripts]
check = "mypy --install-types --non-interactive --ignore-missing-imports {args:src/markitdown tests}"
```

Run with:

```bash
hatch run types:check
```

### Test Coverage Configuration

```toml
[tool.coverage.run]
source_pkgs = ["markitdown", "tests"]
branch = true
parallel = true
omit = ["src/markitdown/__about__.py"]

[tool.coverage.report]
exclude_lines = ["no cov", "if __name__ == .__main__.:", "if TYPE_CHECKING:"]
```

## How to Deploy / Publish

The project uses **hatchling**'s dynamic versioning from `__about__.py`:

```toml
[tool.hatch.version]
path = "src/markitdown/__about__.py"
```

Current version: `0.1.6b2` (from `src/markitdown/__about__.py:3`).

Build a distribution:

```bash
cd packages/markitdown
pip install build
python -m build
```

This produces `dist/markitdown-0.1.6b2.tar.gz` and `dist/markitdown-0.1.6b2-py3-none-any.whl`.

The sdist is configured to include only the source tree:

```toml
[tool.hatch.build.targets.sdist]
only-include = ["src/markitdown"]
```

## Docker

### CLI Container

```bash
# Build
docker build -t markitdown:latest .

# Run (pipe a file in, get Markdown out)
docker run --rm -i markitdown:latest < your-file.pdf > output.md
```

### MCP Server Container

```bash
cd packages/markitdown-mcp
docker build -t markitdown-mcp:latest .

# Run (STDIO mode, for MCP clients)
docker run --rm -i markitdown-mcp:latest

# Run (HTTP mode)
docker run --rm -p 3001:3001 markitdown-mcp:latest markitdown-mcp --http
```

## Python Version Support

All packages require **Python >= 3.10**. Tested on CPython 3.10, 3.11, 3.12, 3.13, and PyPy implementations.

```toml
requires-python = ">=3.10"
classifiers = [
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
]
```
