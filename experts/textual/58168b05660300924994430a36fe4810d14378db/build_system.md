# Textual Build System

## Build System Type and Configuration

Textual uses **Poetry** as its primary build system and dependency management tool. Poetry is a modern Python packaging and dependency management system that provides deterministic builds, virtual environment management, and simplified publishing workflows.

### Primary Configuration Files

**pyproject.toml** (central configuration)
```toml
[tool.poetry]
name = "textual"
version = "7.5.0"
description = "Modern Text User Interface framework"
authors = ["Will McGugan <will@textualize.io>"]
license = "MIT"
```

Poetry configuration sections in pyproject.toml include:
- Project metadata (name, version, description, authors, license)
- Homepage, repository, and documentation URLs
- Python version constraints and dependencies
- Optional dependency groups ([syntax] extras)
- Development dependencies ([tool.poetry.group.dev.dependencies])
- File inclusion/exclusion rules for distribution

**build-system** (PEP 517/518 compliant):
```toml
[build-system]
requires = ["poetry-core>=1.2.0"]
build-backend = "poetry.core.masonry.api"
```

**Makefile** (development workflow automation)
- Provides convenient targets for common tasks
- All Python commands run via `$(run) := poetry run` for environment isolation
- Supports parallel testing, documentation building, and code quality checks

### Configuration Files

**mypy.ini**: Static type checking configuration for MyPy type checker

**.coveragerc**: Code coverage configuration for pytest-cov
```ini
[run]
# Coverage settings for test runs
```

**.pre-commit-config.yaml**: Pre-commit hooks configuration
- Runs code formatters and linters before commits
- Ensures code quality standards

**mkdocs-*.yml**: Documentation build configuration
- mkdocs-common.yml: Shared configuration
- mkdocs-online.yml: Online documentation settings
- mkdocs-offline.yml: Offline documentation settings
- mkdocs-nav.yml: Navigation structure

**pytest configuration** in pyproject.toml:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--strict-markers"
markers = [
    "syntax: marks tests that require syntax highlighting",
]
asyncio_default_fixture_loop_scope = "function"
```

**ruff configuration** in pyproject.toml:
```toml
[tool.ruff]
target-version = "py39"
```

## External Dependencies

### Core Runtime Dependencies

**rich** (>=14.2.0)
- The text rendering engine powering all Textual output
- Provides console abstraction, text styling, and color support
- Segment-based rendering for efficient terminal updates
- Rich protocol integration for custom renderables

**markdown-it-py** (with linkify extras, >=2.1.0)
- Markdown parsing for Markdown and MarkdownViewer widgets
- CommonMark compliant with extensions

**mdit-py-plugins**
- Additional markdown-it-py plugins
- Extends markdown capabilities

**typing-extensions** (^4.4.0)
- Backports of newer typing features for Python 3.9+
- Enables modern type hints on older Python versions

**platformdirs** (>=3.6.0,<5)
- Cross-platform directory path resolution
- User data, config, and cache directory locations

### Optional Dependencies: Syntax Highlighting

The `[syntax]` extras group provides tree-sitter based syntax highlighting (requires Python >=3.10):

**tree-sitter** (>=0.25.0)
- Fast incremental parsing library
- Foundation for syntax highlighting

**Language-specific tree-sitter parsers** (all >=0.23.0):
- tree-sitter-python, tree-sitter-markdown
- tree-sitter-json, tree-sitter-toml, tree-sitter-yaml
- tree-sitter-html, tree-sitter-css
- tree-sitter-javascript, tree-sitter-rust, tree-sitter-go
- tree-sitter-regex, tree-sitter-xml, tree-sitter-sql
- tree-sitter-java, tree-sitter-bash

Installation: `pip install textual[syntax]` or `poetry install --extras syntax`

**pygments** (^2.19.2)
- Fallback syntax highlighting when tree-sitter unavailable
- Wider language support with lower performance

### Development Dependencies

**Testing**:
- pytest (^8.3.1): Testing framework
- pytest-asyncio: Async test support
- pytest-xdist (^3.6.1): Parallel test execution
- pytest-cov (^5.0.0): Code coverage measurement
- pytest-textual-snapshot (^1.0.0): Visual regression testing

**Code Quality**:
- black (24.4.2): Code formatter
- mypy (^1.0.0): Static type checker
- isort (^5.13.2): Import sorting
- pre-commit (^2.13.0): Git hook management

**Documentation**:
- mkdocs (^1.3.0): Documentation site generator
- mkdocs-material (^9.0.11): Material theme for mkdocs
- mkdocstrings (^0.20.0): API reference generation from docstrings
- mkdocstrings-python (^1.0.0): Python-specific docstring parsing
- mkdocs-git-revision-date-localized-plugin (^1.2.5): Last update dates
- mkdocs-rss-plugin (^1.5.0): RSS feed generation
- mkdocs-exclude (^1.0.2): File exclusion for docs

**Development Tools**:
- textual-dev (^1.7.0): Textual developer tools (console, run command, etc.)
- griffe (0.32.3): Python API inspection for documentation
- httpx (^0.23.1): HTTP client for testing/examples
- types-setuptools (^67.2.0.1): Type stubs for setuptools

## Build Targets and Commands

### Setup and Installation

**Initial setup** (one-time):
```bash
poetry shell           # Create/activate virtual environment
make setup             # Install all dependencies including syntax extras
make install-pre-commit # Install git pre-commit hooks
```

The `make setup` target runs:
```makefile
setup:
    poetry install
    poetry install --extras syntax
```

**Dependency updates**:
```bash
make update            # Update all dependencies (runs: poetry update)
```

### Testing

**Run full test suite**:
```bash
make test              # Run tests with 16 parallel workers
# Equivalent to: poetry run pytest tests/ -n 16 --dist=loadgroup
```

**Verbose testing**:
```bash
make testv             # Verbose test output (-vvv)
```

**Test with coverage**:
```bash
make test-coverage     # Run tests with coverage reporting
make coverage          # Generate HTML coverage report
```

**Snapshot testing**:
```bash
make test-snapshot-update  # Update visual regression snapshots
```

All test commands use pytest-xdist with 16 parallel workers (`-n 16`) and `--dist=loadgroup` for optimal test distribution.

**Running specific tests**:
```bash
make test ARGS="tests/test_app.py -k test_specific"
# The ARGS variable passes additional arguments to pytest
```

### Code Quality

**Format code**:
```bash
make format            # Format code with black (modifies files)
make format-check      # Check formatting without modifying
```

**Type checking**:
```bash
make typecheck         # Run mypy on src/textual
# Equivalent to: poetry run mypy src/textual
```

### Documentation

**Build and serve documentation locally**:
```bash
make docs-serve        # Serve online docs with live reload at http://localhost:8000
# Sets TEXTUAL_THEME=dracula and uses mkdocs-nav-online.yml
```

**Offline documentation**:
```bash
make docs-serve-offline  # Serve offline docs (no blog)
```

**Build documentation**:
```bash
make docs-build        # Build online documentation to site/
make docs-build-offline # Build offline documentation
```

**Deploy documentation**:
```bash
make docs-deploy       # Deploy to GitHub Pages (gh-deploy)
```

Documentation targets dynamically generate navigation files (mkdocs-nav-online.yml, mkdocs-nav-offline.yml) by combining mkdocs-online/offline.yml with mkdocs-nav.yml.

**Clean documentation artifacts**:
```bash
make clean-screenshot-cache  # Remove .screenshot_cache
make clean-offline-docs      # Remove docs-offline/
make clean                   # Clean all artifacts
```

### Demo and Development

**Run demo application**:
```bash
make demo              # Run built-in demo (python -m textual)
python -m textual      # Direct invocation also works
```

**Python REPL**:
```bash
make repl              # Start Python REPL in Poetry environment
```

**FAQ management**:
```bash
make faq               # Build FAQ using faqtory tool
```

### Building Distribution

**Build package**:
```bash
make build             # Build source distribution and wheel
# Runs: make docs-build-offline && poetry build
```

This creates:
- Source distribution (.tar.gz) in dist/
- Wheel distribution (.whl) in dist/
- Includes offline documentation in source distribution

**Manual build**:
```bash
poetry build           # Build without offline docs
```

## How to Build, Test, and Deploy

### Complete Development Workflow

1. **Initial Setup**:
```bash
# Clone repository
git clone https://github.com/Textualize/textual.git
cd textual

# Set up environment
poetry shell                    # Create/activate venv
make setup                      # Install dependencies
make install-pre-commit         # Install hooks
```

2. **Development Cycle**:
```bash
# Make changes to code
# Pre-commit hooks automatically run on git commit

# Run tests
make test                       # Full test suite

# Check types
make typecheck                  # Static type checking

# Format code
make format                     # Auto-format with black

# Build docs
make docs-serve                 # Preview docs locally
```

3. **Testing Strategy**:
```bash
# Fast iteration: test specific module
poetry run pytest tests/test_widget.py -v

# Visual regression: update snapshots after UI changes
make test-snapshot-update

# Full validation before PR
make test-coverage              # Ensure adequate coverage
make typecheck                  # No type errors
make format-check               # Code properly formatted
```

4. **Documentation Updates**:
```bash
# Edit docs in docs/ directory
# Preview changes
make docs-serve                 # Auto-reloads on save

# Build offline docs for distribution
make docs-build-offline
```

5. **Pre-Release Checks**:
```bash
# Run all tests
make test

# Verify types
make typecheck

# Check formatting
make format-check

# Build package
make build

# Test installation from built package
pip install dist/textual-*.whl
```

6. **Publishing** (maintainers only):
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

# Build package
make build

# Publish to PyPI
poetry publish

# Deploy documentation
make docs-deploy
```

### Testing Textual Applications

**Unit testing with pytest**:
```python
from textual.app import App
from textual.widgets import Button
import pytest

@pytest.mark.asyncio
async def test_button_press():
    class MyApp(App):
        def compose(self):
            yield Button("Click me")

    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.click(Button)
        # Assertions...
```

**Snapshot testing**:
```python
def test_widget_appearance(snap_compare):
    """Visual regression test."""
    app = MyApp()
    assert snap_compare(app)
```

### CI/CD Integration

Textual uses GitHub Actions for continuous integration (see .github/workflows/). The build system supports:
- Multi-platform testing (Linux, macOS, Windows)
- Multiple Python versions (3.9-3.14)
- Automated documentation deployment
- Pre-commit validation
- Coverage reporting

### Environment Variables

**TEXTUAL_THEME**: Set theme for documentation screenshots (e.g., `dracula`)
**TEXTUAL_LOG**: Enable logging to file for debugging
**DEBUG**: Enable debug mode for additional logging

### Performance Optimization

The build system supports:
- Parallel test execution (16 workers by default)
- Lazy widget loading for faster imports
- Documentation caching (.screenshot_cache/)
- Incremental builds via Poetry's lock file

This comprehensive build system ensures reliable, reproducible builds while providing excellent developer experience with fast feedback loops and automated quality checks.
