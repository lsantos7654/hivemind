# Ruff Code Structure

## Complete Annotated Directory Tree

```
repo/
├── Cargo.toml                    # Workspace root — defines all 47 crates, shared deps, profiles
├── Cargo.lock                    # Locked dependency versions
├── pyproject.toml                # Python package config (Maturin build backend)
├── rust-toolchain.toml           # Pins Rust 1.92
├── clippy.toml                   # Clippy lint configuration
├── ruff.schema.json              # Auto-generated JSON Schema for ruff config
├── Dockerfile                    # Container build specification
├── README.md                     # Project overview and quickstart
├── CONTRIBUTING.md               # Development guide and contribution workflow
├── CHANGELOG.md                  # Release history
│
├── crates/                       # All Rust workspace crates (47 total)
│   │
│   ├── ruff/                     # Main CLI binary
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs           # Entry: sets allocator, parses args, calls run()
│   │       ├── lib.rs            # run() dispatcher; handles all top-level commands
│   │       ├── args.rs           # Clap-based CLI argument structs
│   │       ├── cache.rs          # Cache file management (lint results per file)
│   │       ├── printer.rs        # Diagnostic output formatting (text, JSON, SARIF, etc.)
│   │       ├── resolve.rs        # Configuration file discovery and resolution
│   │       ├── stdin.rs          # stdin handling utilities
│   │       ├── version.rs        # Version string generation
│   │       ├── diagnostics.rs    # Top-level diagnostic types
│   │       └── commands/         # One module per subcommand
│   │           ├── check.rs      # `ruff check` — lint files
│   │           ├── format.rs     # `ruff format` — format files
│   │           ├── check_stdin.rs
│   │           ├── format_stdin.rs
│   │           ├── add_noqa.rs   # `ruff check --add-noqa` — insert suppression comments
│   │           ├── clean.rs      # `ruff clean` — clear cache
│   │           ├── show_files.rs # `ruff check --show-files`
│   │           ├── show_settings.rs # `ruff check --show-settings`
│   │           ├── rule.rs       # `ruff rule <code>` — rule documentation
│   │           ├── server.rs     # `ruff server` — start LSP
│   │           ├── analyze_graph.rs # `ruff analyze graph` — import graph
│   │           └── completions/  # Shell completion generation
│   │
│   ├── ruff_linter/              # Core linting engine (~1000 source files)
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs            # Public API: lint_only(), lint_fix()
│   │       ├── linter.rs         # Orchestrator: runs all checker passes in order
│   │       ├── checkers/         # Check pass implementations
│   │       │   ├── ast/          # AST-based checks (bulk of the rules)
│   │       │   │   ├── mod.rs    # AST checker visitor that dispatches to rules
│   │       │   │   ├── analyze/  # Per-node-type analysis modules
│   │       │   │   └── annotation.rs
│   │       │   ├── imports.rs    # Import-level checks (isort, etc.)
│   │       │   ├── logical_lines.rs  # Per logical line checks
│   │       │   ├── physical_lines.rs # Per physical line checks
│   │       │   ├── tokens.rs     # Token-level checks
│   │       │   └── filesystem.rs # File-level checks (permissions, extensions)
│   │       ├── rules/            # All rule implementations, organized by linter
│   │       │   ├── airflow/      # AIR rules (Apache Airflow compatibility)
│   │       │   ├── flake8_2020/  # YTT rules
│   │       │   ├── flake8_annotations/ # ANN rules
│   │       │   ├── flake8_async/ # ASYNC rules
│   │       │   ├── flake8_bandit/ # S rules (security)
│   │       │   ├── flake8_boolean_trap/ # FBT rules
│   │       │   ├── flake8_bugbear/ # B rules
│   │       │   ├── flake8_builtins/ # A rules
│   │       │   ├── flake8_commas/ # COM rules
│   │       │   ├── flake8_comprehensions/ # C4 rules
│   │       │   ├── flake8_copyright/ # CPY rules
│   │       │   ├── flake8_datetimez/ # DTZ rules
│   │       │   ├── flake8_debugger/ # T10 rules
│   │       │   ├── flake8_django/ # DJ rules
│   │       │   ├── flake8_errmsg/ # EM rules
│   │       │   ├── flake8_executable/ # EXE rules
│   │       │   ├── flake8_future_annotations/ # FA rules
│   │       │   ├── flake8_gettext/ # INT rules
│   │       │   ├── flake8_implicit_str_concat/ # ISC rules
│   │       │   ├── flake8_import_conventions/ # ICN rules
│   │       │   ├── flake8_logging/ # LOG rules
│   │       │   ├── flake8_logging_format/ # G rules
│   │       │   ├── flake8_no_pep420/ # INP rules
│   │       │   ├── flake8_pie/ # PIE rules
│   │       │   ├── flake8_print/ # T20 rules
│   │       │   ├── flake8_pyi/ # PYI rules (stub files)
│   │       │   ├── flake8_pytest_style/ # PT rules
│   │       │   ├── flake8_quotes/ # Q rules
│   │       │   ├── flake8_raise/ # RSE rules
│   │       │   ├── flake8_return/ # RET rules
│   │       │   ├── flake8_self/ # SLF rules
│   │       │   ├── flake8_simplify/ # SIM rules
│   │       │   ├── flake8_slots/ # SLOT rules
│   │       │   ├── flake8_tidy_imports/ # TID rules
│   │       │   ├── flake8_todos/ # TD rules
│   │       │   ├── flake8_type_checking/ # TCH rules
│   │       │   ├── flake8_unused_arguments/ # ARG rules
│   │       │   ├── flake8_use_pathlib/ # PTH rules
│   │       │   ├── isort/        # I rules (import sorting)
│   │       │   ├── numpy/        # NPY rules (NumPy compatibility)
│   │       │   ├── pandas_vet/   # PD rules (pandas compatibility)
│   │       │   ├── pep8_naming/  # N rules
│   │       │   ├── perflint/     # PERF rules (performance)
│   │       │   ├── pycodestyle/  # E/W rules (PEP 8 style)
│   │       │   ├── pydocstyle/   # D rules (docstring conventions)
│   │       │   ├── pyflakes/     # F rules (undefined names, unused imports, etc.)
│   │       │   ├── pygrep_hooks/ # PGH rules
│   │       │   ├── pylint/       # PL rules (Pylint subset)
│   │       │   ├── pyupgrade/    # UP rules (modern Python syntax)
│   │       │   ├── refurb/       # FURB rules
│   │       │   ├── ruff/         # RUF rules (Ruff-specific)
│   │       │   └── tryceratops/  # TRY rules
│   │       ├── registry/         # Rule registry (code → metadata mapping)
│   │       ├── settings/         # Configuration data structures
│   │       ├── message/          # Diagnostic output formats (text, JSON, SARIF, JUnit, GitHub)
│   │       ├── fix/              # Fix applicator and conflict resolution
│   │       ├── docstrings/       # Docstring extraction and style parsers
│   │       │   ├── extraction.rs
│   │       │   ├── google.rs     # Google-style docstring parser
│   │       │   ├── numpy.rs      # NumPy-style docstring parser
│   │       │   └── styles.rs
│   │       └── test.rs           # Test utilities for rule authors
│   │
│   ├── ruff_python_parser/       # Python parser
│   │   └── src/
│   │       ├── lib.rs            # parse_module(), parse_expression() public API
│   │       ├── lexer.rs          # Main lexer (tokenizer)
│   │       ├── lexer/
│   │       │   ├── cursor.rs     # Source character cursor
│   │       │   ├── indentation.rs # INDENT/DEDENT token generation
│   │       │   └── interpolated_string.rs # F-string/t-string tokenization
│   │       ├── parser/
│   │       │   ├── mod.rs        # Parser state, lookahead, error recovery
│   │       │   ├── expression.rs # Pratt-based expression parser
│   │       │   ├── statement.rs  # Statement parser
│   │       │   ├── pattern.rs    # match/case pattern parser
│   │       │   ├── recovery.rs   # Panic-mode error recovery
│   │       │   └── helpers.rs
│   │       ├── token.rs          # Token enum definitions
│   │       ├── token_set.rs      # Compact token bitset
│   │       └── string.rs         # String literal parsing (escapes, prefixes)
│   │
│   ├── ruff_python_formatter/    # Code formatter
│   │   └── src/
│   │       ├── lib.rs            # format_module_source(), format_node() API
│   │       └── ...               # Per-node formatting logic
│   │
│   ├── ruff_formatter/           # Language-agnostic formatter IR
│   │   └── src/
│   │       └── ...               # IR nodes, printer, line breaking logic
│   │
│   ├── ruff_python_ast/          # AST node types (31 source files)
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── ast.rs            # All AST node structs/enums
│   │       ├── visitor.rs        # Recursive visitor trait
│   │       └── ...               # Helper traits and impls
│   │
│   ├── ruff_python_semantic/     # Semantic analysis
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── model.rs          # SemanticModel — central semantic state
│   │       ├── binding.rs        # Binding types (Import, ClassDef, FunctionDef, etc.)
│   │       ├── scope.rs          # Scope stack and scope kinds
│   │       ├── branches.rs       # Branch tracking for control flow
│   │       └── ...
│   │
│   ├── ruff_server/              # LSP server
│   │   └── src/
│   │       └── ...               # LSP protocol handling, document sync
│   │
│   ├── ruff_workspace/           # Workspace config and file discovery
│   │   └── src/
│   │       └── ...               # pyproject.toml discovery, config merging
│   │
│   ├── ruff_db/                  # File system database (Salsa-based)
│   │   └── src/
│   │       └── ...               # Virtual file system, input tracking
│   │
│   ├── ruff_wasm/                # WebAssembly bindings
│   │   └── src/
│   │       └── lib.rs            # WASM-exported API for playground
│   │
│   ├── ruff_notebook/            # Jupyter notebook support
│   │   └── src/
│   │       └── ...               # .ipynb parsing, cell extraction, result merging
│   │
│   ├── ruff_diagnostics/         # Diagnostic data structures
│   ├── ruff_source_file/         # Source file abstractions (SourceCode, Locator)
│   ├── ruff_text_size/           # TextRange, TextSize types
│   ├── ruff_cache/               # Cache file format and management
│   ├── ruff_macros/              # Procedural macros (derive, etc.)
│   ├── ruff_index/               # Typed index wrappers (newindex!)
│   ├── ruff_graph/               # Import dependency graph
│   ├── ruff_python_importer/     # Import resolution
│   ├── ruff_python_index/        # Fast source indexing
│   ├── ruff_python_literal/      # Python literal value parsing
│   ├── ruff_python_trivia/       # Whitespace, comment, trivia utilities
│   ├── ruff_python_codegen/      # Python source code generation from AST
│   ├── ruff_annotate_snippets/   # Error snippet rendering (caret diagnostics)
│   ├── ruff_markdown/            # Markdown code block linting
│   ├── ruff_options_metadata/    # Metadata for config schema generation
│   ├── ruff_memory_usage/        # Memory profiling utilities
│   ├── ruff_dev/                 # Development binary (cargo dev ...)
│   ├── ruff_benchmark/           # Benchmarking harness
│   │
│   ├── ty/                       # Type checker binary (in development)
│   ├── ty_ide/                   # IDE support for type checker
│   ├── ty_server/                # LSP server for type checker
│   ├── ty_static/                # Static type analysis engine
│   ├── ty_module_resolver/       # Module import resolution for type checker
│   ├── ty_project/               # Type checker project config
│   ├── ty_python_semantic/       # Type-aware semantic analysis
│   ├── ty_combine/               # Type inference/combining logic
│   ├── ty_site_packages/         # Stdlib stub handling
│   ├── ty_test/                  # Type checker test harness
│   ├── ty_vendored/              # Vendored type stubs
│   └── ty_wasm/                  # WASM bindings for type checker
│
├── docs/                         # MkDocs documentation source
│   └── ...                       # Markdown docs for rules, configuration, etc.
│
├── python/                       # Python wrapper package
│   └── ...                       # Python source for PyPI package
│
├── playground/                   # Web playground
│   └── ...                       # WASM frontend (likely TypeScript/JS)
│
├── scripts/                      # Build and utility scripts
│   └── ...                       # Schema generation, release scripts
│
├── assets/                       # Static assets (images for docs/README)
├── changelogs/                   # Per-version changelog fragments
└── fuzz/                         # Fuzzing harnesses for the parser
```

## Module and Package Organization

Ruff follows a **layered crate architecture** with strict dependency direction:

```
ruff (CLI binary)
  └── ruff_linter + ruff_python_formatter + ruff_workspace
        └── ruff_python_semantic + ruff_python_parser
              └── ruff_python_ast + ruff_python_trivia
                    └── ruff_text_size + ruff_source_file
```

Support crates (`ruff_diagnostics`, `ruff_cache`, `ruff_macros`, etc.) are used across layers.

## Code Organization Patterns

**Rule implementation pattern** — each rule category in `ruff_linter/src/rules/<category>/` contains:
- `mod.rs` — re-exports all rules in the category
- Individual rule files (e.g., `f401.rs` for F401 "unused import")
- `fixes/` subdirectory for associated fix logic
- `tests/` with snapshot test fixtures

**Checker dispatch pattern** — the AST checker in `checkers/ast/mod.rs` implements a visitor that calls into each relevant rule on each AST node visit.

**Snapshot testing** — rules use `insta` crate snapshots stored in `src/rules/<category>/snapshots/` to verify diagnostic output doesn't regress.

**Registry** — `ruff_linter/src/registry/` maps rule codes (e.g., `"F401"`) to rule metadata (name, description, fixability, stability) using code generation from `cargo dev generate-all`.
