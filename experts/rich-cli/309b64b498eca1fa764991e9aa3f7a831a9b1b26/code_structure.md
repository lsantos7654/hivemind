# Rich-CLI Code Structure

## Complete Directory Tree

```
rich-cli/
├── .git/                        # Git version control
├── .gitignore                   # Git ignore patterns
├── CHANGELOG.md                 # Version history and release notes
├── LICENSE                      # MIT License
├── README.md                    # Project documentation and usage examples
├── poetry.lock                  # Poetry dependency lock file
├── pyproject.toml               # PEP 621 project configuration and build system
├── imgs/                        # Documentation images and screenshots
│   ├── alignment1.png           # Examples for README
│   ├── csv1.png
│   ├── json1.png
│   ├── markdown1.png
│   ├── network1.png
│   ├── padding1.png
│   ├── pager1.png
│   ├── panel1.png
│   ├── printing1.png
│   ├── rich-cli-splash.jpg
│   ├── rules1.png
│   ├── style1.png
│   ├── syntax1.png
│   ├── syntax2.png
│   ├── syntax3.png
│   └── width1.png
├── src/                         # Source code root
│   └── rich_cli/                # Main package
│       ├── __init__.py          # Package initialization (mostly empty)
│       ├── __main__.py          # Main CLI implementation and entry point
│       ├── markdown.py          # Custom markdown code block rendering
│       ├── pager.py             # Interactive pager implementation
│       └── win_vt.py            # Windows virtual terminal support
├── test_data/                   # Test fixtures and sample data
│   ├── airtravel.csv            # CSV test file
│   ├── deniro.csv               # CSV test file
│   ├── mlb_players.csv          # Large CSV test file
│   ├── notebook.ipynb           # Jupyter notebook test file
│   └── test.rst                 # ReStructuredText test file
└── tests/                       # Test suite
    ├── __init__.py__            # Test package initialization
    └── test_main.py             # Unit tests for CLI
```

## Module and Package Organization

The project follows a simple, flat package structure with clear separation of concerns:

### Primary Source Package: `src/rich_cli/`

The source code is organized as a single Python package under the `src/` layout (modern Python best practice). This structure isolates the source from the project root and prevents accidental imports during development.

**Package Components:**

1. **`__init__.py`** (1 line): Minimal package marker with just version import
2. **`__main__.py`** (940 lines): Core CLI logic
3. **`markdown.py`** (33 lines): Markdown rendering extension
4. **`pager.py`** (81 lines): Interactive pager application
5. **`win_vt.py`** (62 lines): Windows compatibility layer

This flat structure makes the codebase easy to navigate and understand, with each module having a single, well-defined responsibility.

## Main Source Directories and Their Purposes

### `/src/rich_cli/` - Core Implementation

The main package contains all functionality with no subdirectories, reflecting the project's focused scope. Each file addresses a specific concern:

**Primary Module (`__main__.py`)**: Contains all CLI logic including argument parsing, input reading, format detection, rendering coordination, and output management. This 940-line file is intentionally monolithic to keep related functionality together.

**Extension Modules**: Three small, focused modules extend specific functionality:
- `markdown.py`: Customizes markdown rendering
- `pager.py`: Implements interactive scrolling
- `win_vt.py`: Handles Windows terminal compatibility

### `/tests/` - Test Suite

Contains unit tests using pytest. Currently includes one test file that validates the CLI doesn't have duplicate option flags, using Click's testing utilities and monkeypatching.

### `/test_data/` - Test Fixtures

Sample files for manual testing and development:
- CSV files of various sizes (321 bytes to 57KB)
- Jupyter notebook with sample cells
- ReStructuredText document

### `/imgs/` - Documentation Assets

Screenshots and images demonstrating Rich-CLI features, embedded in README.md and used for promotional purposes.

## Key Files and Their Roles

### `pyproject.toml` - Project Configuration

The build system configuration using PEP 621 format and Poetry 2.x. Key sections:

- **`[project]`**: Metadata including name, version (1.8.1), description, license, authors, and Python version requirement (>=3.9)
- **`[project.dependencies]`**: Runtime dependencies (rich, click, requests, textual, rich-rst)
- **`[project.scripts]`**: Defines the `rich` command entry point pointing to `rich_cli.__main__:run`
- **`[build-system]`**: Specifies poetry-core as the build backend
- **`[tool.poetry.group.dev.dependencies]`**: Development tools (black, mypy)

### `__main__.py` - CLI Implementation

The heart of the application. Major components:

**Constants and Configuration (lines 1-53)**:
- Import statements for all dependencies
- Format type constants (AUTO, SYNTAX, PRINT, MARKDOWN, RST, JSON, RULE, INSPECT, CSV, IPYNB)
- Box style definitions for panel rendering
- Common lexer mappings for file extension detection
- Version string

**Helper Functions**:
- `on_error()` (lines 55-67): Error handling and exit
- `read_resource()` (lines 70-121): Unified input reading from files, URLs, or stdin with automatic lexer detection
- `blend_text()` (lines 145-160): Creates gradient text effects
- `_line_range()` (lines 918-931): Calculates line ranges for head/tail display

**Custom Click Classes**:
- `ForceWidth` (lines 124-142): Renderable wrapper to force specific width
- `RichCommand` (lines 163-244): Custom help formatter with Rich styling

**Main CLI Function** (`main()`, lines 247-733):
- 50+ Click decorators defining all command-line options
- Format detection logic based on file extensions
- Dispatch to appropriate renderer (syntax, markdown, JSON, CSV, etc.)
- Output formatting with panels, padding, alignment
- Pager mode or direct console output
- HTML/SVG export handling

**Specialized Renderers**:
- `render_csv()` (lines 736-816): CSV table rendering with dialect detection
- `render_ipynb()` (lines 819-915): Jupyter notebook cell rendering

**Entry Point**:
- `run()` (lines 934-935): Wrapper function called by the CLI command

### `markdown.py` - Markdown Extension

A focused 33-line module that extends Rich's Markdown class with a custom code block renderer:

- **`CodeBlock` class**: Inherits from Rich's `TextElement` and overrides rendering to apply padding and syntax highlighting with word wrap
- **Monkey patch**: Registers the custom CodeBlock with `Markdown.elements["code_block"]` to replace Rich's default

This demonstrates how Rich-CLI customizes Rich's behavior for better CLI output.

### `pager.py` - Interactive Pager

An 81-line Textual application providing scrollable content viewing:

- **`PagerRenderable`**: Wraps pre-rendered segment lines for display
- **`PagerApp`**: Textual App subclass with keybindings:
  - `q`: quit
  - `j`/`k`: vi-style line scrolling
  - `ctrl+d`/`ctrl+u`: half-page scrolling
  - `space`: page down
- Uses Textual's `ScrollView` widget for rendering

### `win_vt.py` - Windows Compatibility

A 62-line module providing Windows terminal compatibility through virtual terminal processing:

- **Context manager** `enable_windows_virtual_terminal_processing()`: Enables ANSI escape code support on Windows
- Uses `ctypes` to call Windows kernel32.dll functions
- No-op on non-Windows platforms (yields without action)
- Restores original console mode on exit

### `CHANGELOG.md` - Version History

Documents all releases with changes categorized as Added, Changed, Fixed. Recent highlights include Python 3.9+ requirement, PEP 621 migration, UTF-8 encoding fixes, Jupyter notebook support, and SVG export.

## Code Organization Patterns

### Design Patterns

1. **Single Entry Point Pattern**: All CLI logic consolidated in `__main__.py` with a single `main()` function as the command handler

2. **Format Strategy Pattern**: Different renderers selected based on format type constant, with each format having dedicated rendering logic

3. **Decorator-Heavy Configuration**: Extensive use of Click decorators for clean, declarative CLI option definitions (50+ decorators on main function)

4. **Monkey Patching for Extension**: `markdown.py` extends Rich's behavior through element registration rather than subclassing

5. **Context Manager for Resource Management**: `win_vt.py` uses context manager for safe state restoration

### Code Style

- **Type Hints**: Comprehensive use of type annotations with `TYPE_CHECKING` guards for circular imports
- **Functional Decomposition**: Large `main()` function with helper functions for specific tasks
- **Rich Console Protocols**: Custom renderables implement `__rich_console__()` and `__rich_measure__()` protocols
- **Error Handling**: Centralized error reporting through `on_error()` helper

### Testing Strategy

Minimal but focused testing:
- One test validates CLI option uniqueness using monkeypatching
- Manual testing supported by test_data fixtures
- Relies heavily on Rich and Click's battle-tested implementations

The codebase prioritizes simplicity and readability over complex abstractions, appropriate for a CLI tool wrapping a well-tested library.
