# ScrapeGraphAI — Build System

## Build System Type and Configuration Files

ScrapeGraphAI uses **Hatchling** as its build backend, managed via `pyproject.toml`. The development workflow is driven by **uv** (Astral's fast Python package manager) and automated via a `Makefile`. Pre-commit hooks enforce code style.

Key configuration files:

| File | Purpose |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, build config, tool settings |
| `Makefile` | Developer workflow shortcuts (install, lint, test, build, clean) |
| `uv.lock` | Locked dependency tree (all transitive deps, committed) |
| `requirements.txt` | Minimal pip-compatible requirements (auto-generated or curated) |
| `requirements-dev.txt` | Dev-only dependencies |
| `pytest.ini` | Pytest configuration (markers, asyncio mode) |
| `.pre-commit-config.yaml` | Pre-commit hook definitions |
| `Dockerfile` / `docker-compose.yml` | Container deployment |
| `readthedocs.yml` | Read the Docs CI configuration |

## External Dependencies

### Core runtime (from `pyproject.toml [project.dependencies]`)

| Package | Version | Purpose |
|---|---|---|
| `langchain` | `>=1.2.0` | Core LangChain framework |
| `langchain-classic` | `>=1.0.0` | Legacy LangChain patterns (extraction chains) |
| `langchain-openai` | `>=1.1.6` | OpenAI/Azure chat model integration |
| `langchain-mistralai` | `>=1.1.1` | Mistral AI integration |
| `langchain-community` | `>=0.4.0` | Community loaders, Ollama, Ernie |
| `langchain-aws` | `>=1.1.0` | AWS Bedrock integration |
| `langchain-ollama` | `>=1.0.1` | Ollama local model integration |
| `html2text` | `>=2025.4.15` | HTML → Markdown conversion |
| `beautifulsoup4` | `>=4.14.3` | HTML parsing and cleaning |
| `python-dotenv` | `>=1.2.1` | `.env` file loading |
| `tiktoken` | `>=0.12.0` | OpenAI tokenizer |
| `tqdm` | `>=4.67.1` | Progress bars |
| `minify-html` | `>=0.18.1` | HTML minification |
| `free-proxy` | `>=1.1.3` | Free proxy pool |
| `playwright` | `>=1.57.0` | Browser automation |
| `undetected-playwright` | `>=0.3.0` | Anti-detection Playwright variant |
| `semchunk` | `>=3.2.5` | Semantic text chunking |
| `async-timeout` | `>=4.0.0` | Async operation timeouts |
| `simpleeval` | `>=1.0.3` | Safe expression evaluation |
| `jsonschema` | `>=4.25.1` | JSON Schema validation |
| `duckduckgo-search` | `>=8.1.1` | Default internet search backend |
| `pydantic` | `>=2.12.5` | Data validation and structured output |
| `scrapegraph-py` | `>=1.44.0` | ScrapeGraphAI cloud API SDK |

### Optional extras

| Extra | Packages | Use case |
|---|---|---|
| `burr` | `burr[start]==0.22.1` | Burr state machine observability |
| `docs` | `sphinx==6.0`, `furo==2024.5.6` | Documentation generation |
| `nvidia` | `langchain-nvidia-ai-endpoints>=0.1.0` | NVIDIA NIM models |
| `ocr` | `surya-ocr>=0.5.0`, `matplotlib>=3.7.2`, `ipywidgets>=8.1.0`, `pillow>=10.4.0` | Screenshot OCR |

### Dev dependencies (from `[tool.uv] dev-dependencies`)

`pytest`, `pytest-mock`, `pytest-asyncio`, `pytest-sugar`, `pytest-cov`, `pylint`, `poethepoet`, `black`, `ruff`, `isort`, `pre-commit`, `mypy`, `types-setuptools`

## Build Targets and Commands

All common tasks are available via `make`:

```bash
make install      # uv sync + pre-commit install
make lint         # ruff check + black --check + isort --check-only
make type-check   # mypy scrapegraphai tests
make test         # pytest --cov=scrapegraphai --cov-report=xml tests/
make pre-commit   # pre-commit run --all-files
make build        # uv build --no-sources  (produces dist/)
make clean        # removes dist/, build/, .mypy_cache/, .pytest_cache/, etc.
make all          # lint + type-check + test
```

## How to Build

### Install for development

```bash
pip install uv          # or: curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync                 # installs all deps including dev extras from uv.lock
uv run pre-commit install
```

### Install with optional extras

```bash
uv sync --extra ocr        # adds surya-ocr, matplotlib, pillow, ipywidgets
uv sync --extra burr       # adds burr framework
uv sync --extra nvidia     # adds langchain-nvidia-ai-endpoints
```

### Install Playwright browsers (required for web scraping)

```bash
uv run playwright install
# or if using pip:
playwright install
```

### Build distribution package

```bash
make build
# produces: dist/scrapegraphai-<version>.tar.gz and .whl
```

## How to Test

```bash
# Run all unit tests
make test
# or:
uv run pytest tests/

# Run specific test file
uv run pytest tests/graphs/smart_scraper_openai_test.py -v

# Run with coverage report
uv run pytest --cov=scrapegraphai --cov-report=html tests/

# Run integration tests only
uv run pytest tests/integration/ -v

# Run a specific node test
uv run pytest tests/nodes/fetch_node_test.py -v
```

Test configuration in `pytest.ini` sets asyncio mode and test markers. Integration tests in `tests/integration/` require real API keys set as environment variables (see `tests/graphs/.env.example`).

## How to Deploy (Docker)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Build Docker image directly
docker build -t scrapegraphai .
docker run scrapegraphai
```

## Code Quality Tools

| Tool | Config location | Purpose |
|---|---|---|
| **ruff** | `[tool.ruff]` in `pyproject.toml` | Fast linter (F, E, W, C rules; ignores E203, E501, C901) |
| **black** | `[tool.black]` — line-length 88, target py310 | Auto-formatter |
| **isort** | `[tool.isort]` — profile "black" | Import sorter |
| **mypy** | `[tool.mypy]` — strict mode, py3.10 | Static type checker |
| **pylint** | via `poe pylint-ci` | CI linting (docstring warnings disabled) |
| **pre-commit** | `.pre-commit-config.yaml` | Runs all checks before commit |

## Python Version Requirements

Requires Python `>=3.10,<4.0` (enforced in `pyproject.toml`). The build system targets Python 3.10 features (union types, structural pattern matching are not used; standard typing with `Optional` is used throughout).
