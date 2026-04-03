# Ruff: Python Linter and Formatter

## Repository Purpose and Goals

Ruff is an extremely fast Python linter and code formatter written in Rust. Its primary goal is to unify the Python code quality toolchain — replacing Flake8, Black, isort, pydocstyle, pyupgrade, autoflake, and dozens of their plugins — with a single, blazingly fast tool. Ruff is 10–100x faster than equivalent Python-based tools, enabling lint checks and formatting that previously took seconds to complete in milliseconds even on large codebases.

Ruff aims to be a drop-in replacement for the most common Python code quality tools, maintaining rule-for-rule parity while providing a dramatically better developer experience through speed, unified configuration, and automatic fix support.

## Key Features and Capabilities

- **900+ built-in lint rules** spanning 70+ rule categories, first-party implementations of Flake8 and its plugins, Pylint, isort, pydocstyle, pyupgrade, and more
- **Python code formatter** with Black-compatible output, including import sorting (isort)
- **Automatic fix support** for the majority of rules, enabling `ruff check --fix` to auto-correct violations
- **Caching** to avoid re-analyzing unchanged files across runs
- **LSP server** (`ruff server`) for native editor integration (VS Code, Neovim, Helix, etc.)
- **Jupyter notebook support** — linting and formatting `.ipynb` files
- **Hierarchical configuration** via `pyproject.toml`, `ruff.toml`, or `.ruff.toml` with per-directory overrides
- **`noqa` directives** with rule-specific suppression and automatic noqa management
- **stdin support** for integration into pipelines and pre-commit hooks
- **Dependency graph analysis** (`ruff analyze graph`) for import cycle detection
- **WebAssembly playground** for browser-based experimentation
- **`ty`** — an in-development Python type checker built alongside Ruff (separate binary)

## Implemented Plugin Categories (Selected)

`pyflakes` (F), `pycodestyle` (E/W), `pep8-naming` (N), `pydocstyle` (D), `pyupgrade` (UP), `flake8-bugbear` (B), `flake8-comprehensions` (C4), `flake8-simplify` (SIM), `flake8-bandit` (S), `flake8-async` (ASYNC), `flake8-logging` (LOG), `isort` (I), `pylint` (PL), `airflow` (AIR), `ruff-specific` (RUF), and 50+ more.

## Primary Use Cases and Target Audience

- **Python developers** who want fast, unified code quality tooling in CI and local workflows
- **Large codebases** (FastAPI, Pandas, Hugging Face, PyTorch, Polars, Pydantic, Jupyter) where speed is critical
- **Teams** migrating from Flake8 + Black + isort setups wanting a single tool
- **Editor plugin authors** via the LSP server protocol
- **Pre-commit hook users** via the `ruff-pre-commit` integration

## High-Level Architecture Overview

Ruff is a Rust workspace monorepo with 47 crates organized into clear layers:

1. **Parsing layer** — `ruff_python_parser`: hand-written recursive descent parser with Pratt expression parsing, producing Python ASTs for all Python 3.12+ syntax including f-strings, pattern matching, and type parameter syntax.

2. **AST layer** — `ruff_python_ast`: AST node type definitions and visitor infrastructure.

3. **Semantic analysis layer** — `ruff_python_semantic`: scope analysis, binding resolution, type inference hints, import tracking.

4. **Linting engine** — `ruff_linter`: orchestrates multiple checker passes (AST, token, logical line, physical line, filesystem), hosts all rule implementations, manages the fix engine and diagnostic output.

5. **Formatting engine** — `ruff_python_formatter` + `ruff_formatter`: a Rome/Prettier-inspired intermediate representation (IR) approach to formatting, with Python-specific logic on top of a language-agnostic base.

6. **CLI binary** — `ruff`: command-line interface handling argument parsing, configuration resolution, caching, printer output, file watching, and command dispatch.

7. **LSP server** — `ruff_server`: Language Server Protocol implementation for editor integration.

8. **Type checker (in development)** — `ty` and related crates: a full Python type checker being developed as part of the same monorepo.

Performance is achieved through: custom allocators (jemalloc on Linux/macOS, mimalloc on Windows), parallel processing with Rayon, incremental computation via Salsa, and aggressive caching.

## Related Projects and Dependencies

- **Salsa** — incremental computation framework (used for caching and incremental analysis)
- **Rome/Biome formatter** — architectural inspiration for the IR-based formatter
- **Rayon** — data parallelism for parallel file processing
- **Clap** — CLI argument parsing
- **Serde/TOML** — configuration deserialization
- **Insta** — snapshot testing framework
- **Maturin** — Rust/Python binding build tool (for the Python package on PyPI)
- **MkDocs** — documentation site generation
- **tikv-jemallocator / mimalloc** — custom allocators for performance
