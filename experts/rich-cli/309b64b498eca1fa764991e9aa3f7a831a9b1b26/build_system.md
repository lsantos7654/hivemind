# Rich-CLI Build System

## Build System Type and Configuration

Rich-CLI uses **Poetry 2.x** as its build system with **PEP 621** compliant project metadata. The configuration is centralized in `pyproject.toml`, following modern Python packaging standards.

### Build Backend Configuration

The build system section in `pyproject.toml`:

```toml
[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
```

This specifies Poetry Core as the build backend, which handles:
- Building source distributions (sdist)
- Building wheel distributions
- Installing the package in development or production mode
- Managing virtual environments (when using Poetry CLI)

### PEP 621 Project Metadata

The project uses the standardized `[project]` section for metadata:

```toml
[project]
name = "rich-cli"
version = "1.8.1"
description = "Command Line Interface to Rich"
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
```

**Key Metadata Fields:**

- **name**: Package name on PyPI (`rich-cli`)
- **version**: Current release version (1.8.1)
- **authors**: Will McGugan (willmcgugan@gmail.com)
- **classifiers**: Development status (5 - Production/Stable), supported platforms (Windows, MacOS, Linux), Python versions (3.9-3.13)
- **urls.homepage**: GitHub repository link

### Entry Points

The package defines two types of entry points:

```toml
[project.scripts]
rich = "rich_cli.__main__:run"

[project.entry-points."pipx.run"]
rich-cli = "rich_cli.__main__:run"
```

- **Console script**: Creates the `rich` command that calls the `run()` function
- **pipx entry point**: Allows `pipx run rich-cli` without installation

## External Dependencies and Management

### Runtime Dependencies

Defined in `[project.dependencies]`:

```toml
dependencies = [
    "rich (>=12.4.0,<13.0.0)",      # Core rendering engine
    "click (>=8.0.0,<9.0.0)",       # CLI framework
    "requests (>=2.0.0,<3.0.0)",    # HTTP client for URL fetching
    "textual (>=0.1.18,<0.2.0)",    # Terminal UI for pager
    "rich-rst (>=1.1.7,<2.0.0)",    # ReStructuredText support
]
```

**Dependency Analysis:**

1. **Rich** (>=12.4.0): The foundation library providing all rendering capabilities. Version constrained to major version 12 to ensure API stability.

2. **Click** (>=8.0.0): CLI framework handling argument parsing, options, help formatting. Version 8+ required for modern features.

3. **Requests** (>=2.0.0): HTTP client for fetching remote resources via URLs. Wide version range reflects stable API.

4. **Textual** (>=0.1.18): Terminal user interface framework powering the interactive pager. Currently pre-1.0, constrained to 0.1.x for API stability.

5. **rich-rst** (>=1.1.7): Extension for ReStructuredText rendering, also from the Textualize ecosystem.

**Indirect Dependencies** (managed automatically):
- Pygments: Syntax highlighting (via Rich)
- Markdown-it-py: Markdown parsing (via Rich)
- commonmark: Markdown spec (via Rich)

### Development Dependencies

Two separate systems define dev dependencies:

**Poetry Legacy Format:**
```toml
[tool.poetry.group.dev.dependencies]
black = "22.3.0"
mypy = "0.942"
```

**Modern Dependency Groups:**
```toml
[dependency-groups]
dev = ["black==22.3.0", "mypy==0.942"]
```

Development tools:
- **black** (22.3.0): Code formatter for consistent style
- **mypy** (0.942): Static type checker for type hint validation

### Dependency Lock File

`poetry.lock` contains pinned versions of all dependencies and their transitive dependencies, ensuring reproducible builds across environments. This file should be committed to version control.

## Build Targets and Commands

### Installation Methods

**For End Users:**

1. **PyPI (pip)**:
   ```bash
   python -m pip install rich-cli
   ```

2. **pipx** (recommended for CLI tools):
   ```bash
   pipx install rich-cli
   ```

3. **Homebrew** (macOS):
   ```bash
   brew install rich
   ```

4. **Conda/Mamba**:
   ```bash
   mamba install -c conda-forge rich-cli
   ```

**For Developers:**

1. **Poetry Development Installation**:
   ```bash
   poetry install
   ```
   Installs package in editable mode with development dependencies.

2. **Manual Development Installation**:
   ```bash
   pip install -e .
   ```
   Editable install using PEP 621 metadata.

### Building Distribution Packages

**Using Poetry:**

```bash
# Build both wheel and source distribution
poetry build

# Outputs:
#   dist/rich_cli-1.8.1-py3-none-any.whl
#   dist/rich-cli-1.8.1.tar.gz
```

**Using build (PEP 517 tool)**:

```bash
python -m build

# Produces same outputs using the build backend
```

### Publishing to PyPI

**With Poetry:**

```bash
# Configure PyPI credentials
poetry config pypi-token.pypi <token>

# Publish
poetry publish --build
```

**With twine:**

```bash
# Build first
poetry build

# Upload
twine upload dist/*
```

## How to Build, Test, and Deploy

### Development Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/Textualize/rich-cli.git
   cd rich-cli
   ```

2. **Install with Poetry**:
   ```bash
   poetry install
   ```
   This creates a virtual environment and installs all dependencies.

3. **Activate Environment**:
   ```bash
   poetry shell
   ```

4. **Verify Installation**:
   ```bash
   rich --version
   # Should output: 1.8.0 (note: hardcoded version in __main__.py)
   ```

### Testing

**Run Unit Tests**:
```bash
# With Poetry
poetry run pytest

# Or in activated environment
pytest
```

**Manual Testing**:
```bash
# Test syntax highlighting
rich src/rich_cli/__main__.py

# Test markdown rendering
rich README.md

# Test CSV rendering
rich test_data/deniro.csv

# Test JSON
echo '{"hello": "world"}' | rich - --json

# Test pager
rich README.md --pager
```

**Type Checking**:
```bash
poetry run mypy src/rich_cli
```

**Code Formatting**:
```bash
# Check formatting
poetry run black --check src/

# Apply formatting
poetry run black src/
```

### Building for Distribution

**Standard Build Process**:

1. **Update Version**: Modify version in `pyproject.toml` and `__main__.py` (VERSION constant)

2. **Update Changelog**: Add entry to `CHANGELOG.md`

3. **Build Package**:
   ```bash
   poetry build
   ```

4. **Verify Build**:
   ```bash
   # Check wheel contents
   unzip -l dist/rich_cli-1.8.1-py3-none-any.whl

   # Test installation
   pip install dist/rich_cli-1.8.1-py3-none-any.whl
   ```

### Deployment Process

**Publishing Release**:

1. **Tag Release**:
   ```bash
   git tag -a v1.8.1 -m "Release version 1.8.1"
   git push origin v1.8.1
   ```

2. **Publish to PyPI**:
   ```bash
   poetry publish --build
   ```

3. **Create GitHub Release**: Navigate to GitHub releases and create release from tag with changelog excerpt

**Distribution Channels**:

- **PyPI**: Primary distribution via `poetry publish`
- **Homebrew**: Maintained separately by Homebrew community (formula in homebrew-core)
- **Conda-forge**: Maintained via conda-forge feedstock repository

### Continuous Integration

The project uses modern Python tooling suitable for CI/CD:

**Typical CI Pipeline**:
1. Install Poetry
2. Install dependencies: `poetry install`
3. Run type checker: `poetry run mypy src/`
4. Run tests: `poetry run pytest`
5. Check formatting: `poetry run black --check src/`
6. Build package: `poetry build`

**Environment Matrix**:
- Python versions: 3.9, 3.10, 3.11, 3.12, 3.13
- Platforms: Linux, macOS, Windows

### Version Management

The project maintains version numbers in two locations:

1. **`pyproject.toml`**: Official package version
2. **`__main__.py`**: VERSION constant (currently "1.8.0", slightly out of sync)

**Best Practice**: Update both locations when releasing. Consider single-source versioning in future.

### Cross-Platform Considerations

**Windows-Specific Handling**:
- `win_vt.py` enables virtual terminal processing automatically
- No special build steps required for Windows

**Platform Detection**:
- Runtime detection in `win_vt.py` using `platform.system()`
- Universal wheel works across all platforms

**Dependencies**:
- All dependencies are pure Python except potential C extensions in indirect dependencies
- Binary wheels typically available for all platforms on PyPI

The build system is modern, straightforward, and follows Python packaging best practices with clear separation between build, development, and runtime dependencies.
