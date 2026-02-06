# Rich Code Structure

## Complete Directory Tree

```
rich/
├── rich/                      # Main source package (100 Python modules)
│   ├── __init__.py           # Package entry point with print(), inspect(), get_console()
│   ├── __main__.py           # Module entry point (python -m rich)
│   │
│   ├── Core Rendering
│   │   ├── console.py        # Central Console class - primary API entry point
│   │   ├── protocol.py       # Renderable protocol definitions
│   │   ├── segment.py        # Segment: atomic unit of styled output
│   │   ├── measure.py        # Measurement system for renderables
│   │   ├── text.py           # Text class - styled text with spans
│   │   ├── style.py          # Style definitions and composition
│   │   ├── styled.py         # Styled wrapper for renderables
│   │   └── region.py         # Screen region definitions
│   │
│   ├── High-Level Components
│   │   ├── table.py          # Table rendering with columns and rows
│   │   ├── tree.py           # Tree structure visualization
│   │   ├── panel.py          # Panels with borders
│   │   ├── columns.py        # Multi-column layout
│   │   ├── align.py          # Alignment wrapper
│   │   ├── padding.py        # Padding wrapper
│   │   ├── constrain.py      # Size constraint wrapper
│   │   ├── rule.py           # Horizontal rules
│   │   ├── layout.py         # Advanced layout system
│   │   └── containers.py     # Container types (Lines, Renderables)
│   │
│   ├── Progress and Status
│   │   ├── progress.py       # Progress tracking with multiple bars
│   │   ├── progress_bar.py   # Individual progress bar rendering
│   │   ├── status.py         # Spinner status indicators
│   │   ├── spinner.py        # Spinner animations
│   │   ├── live.py           # Live updating display
│   │   └── live_render.py    # Live render abstractions
│   │
│   ├── Content Rendering
│   │   ├── syntax.py         # Syntax highlighting via Pygments
│   │   ├── markdown.py       # Markdown rendering
│   │   ├── json.py           # JSON pretty printing
│   │   ├── pretty.py         # Pretty printing for Python objects
│   │   ├── repr.py           # Enhanced repr rendering
│   │   ├── traceback.py      # Beautiful traceback rendering
│   │   └── emoji.py          # Emoji support
│   │
│   ├── Text Processing
│   │   ├── markup.py         # BBCode-style markup parsing
│   │   ├── highlighter.py    # Text highlighting patterns
│   │   ├── cells.py          # Cell width calculations
│   │   ├── _wrap.py          # Text wrapping algorithms
│   │   └── _emoji_replace.py # Emoji substitution
│   │
│   ├── Color and Theming
│   │   ├── color.py          # Color definitions and conversions
│   │   ├── color_triplet.py  # RGB color triplets
│   │   ├── palette.py        # Color palette management
│   │   ├── theme.py          # Theme system
│   │   ├── themes.py         # Built-in themes
│   │   ├── terminal_theme.py # Terminal color themes
│   │   ├── default_styles.py # Default style definitions
│   │   └── _palettes.py      # Standard color palettes
│   │
│   ├── Platform Support
│   │   ├── _windows.py       # Windows-specific functionality
│   │   ├── _win32_console.py # Win32 console API
│   │   ├── _windows_renderer.py # Windows rendering
│   │   ├── jupyter.py        # Jupyter notebook support
│   │   └── _fileno.py        # File descriptor utilities
│   │
│   ├── Utilities and Helpers
│   │   ├── _inspect.py       # Object inspection
│   │   ├── _log_render.py    # Log rendering
│   │   ├── _loop.py          # Iteration helpers
│   │   ├── _ratio.py         # Ratio distribution algorithms
│   │   ├── _pick.py          # Selection utilities
│   │   ├── _stack.py         # Stack data structure
│   │   ├── _timer.py         # Timer utilities
│   │   ├── _null_file.py     # Null file object
│   │   ├── _extension.py     # IPython extension
│   │   ├── _export_format.py # Export format templates (HTML, SVG)
│   │   ├── filesize.py       # File size formatting
│   │   ├── file_proxy.py     # File proxy wrapper
│   │   ├── pager.py          # Terminal pager
│   │   ├── scope.py          # Scope rendering for locals
│   │   ├── screen.py         # Screen buffer
│   │   ├── control.py        # Terminal control sequences
│   │   ├── ansi.py           # ANSI code handling
│   │   ├── bar.py            # Bar chart components
│   │   ├── box.py            # Box drawing styles
│   │   ├── errors.py         # Error definitions
│   │   ├── logging.py        # Logging handler
│   │   ├── prompt.py         # Input prompts
│   │   ├── abc.py            # Abstract base classes
│   │   └── _spinners.py      # Spinner animation data
│   │
│   └── _unicode_data/        # Unicode width data for different versions
│       ├── __init__.py
│       ├── _versions.py
│       └── unicode*.py       # Unicode 4.1 through 17.0 data files
│
├── tests/                     # Comprehensive test suite
│   ├── test_*.py             # Unit tests for each module
│   ├── conftest.py           # Pytest configuration
│   └── render.py             # Test rendering utilities
│
├── examples/                  # Example scripts demonstrating features
│   ├── table_movie.py        # Animated table example
│   ├── downloader.py         # Multi-file download progress
│   ├── tree.py               # Directory tree visualization
│   ├── progress.py           # Progress bar examples
│   └── *.py                  # 30+ example scripts
│
├── docs/                      # Sphinx documentation
│   └── source/
│       ├── conf.py           # Sphinx configuration
│       └── *.rst             # Documentation source files
│
├── benchmarks/                # Performance benchmarks
│   ├── benchmarks.py         # Benchmark suite
│   └── snippets.py           # Benchmark code snippets
│
├── tools/                     # Development tools
├── imgs/                      # Documentation images
├── assets/                    # Project assets
└── questions/                 # FAQ content
```

## Module Organization

### Package Entry Point (`__init__.py`)

Exports the high-level API:
- `print()`: Drop-in replacement for built-in print
- `print_json()`: Pretty-print JSON
- `inspect()`: Inspect Python objects
- `get_console()`: Get global Console instance
- `reconfigure()`: Reconfigure global console

### Core Rendering Layer

**Console (`console.py`)**: The central orchestrator class that manages all rendering. Handles:
- Terminal detection and capability negotiation
- Color system detection (truecolor, 256, 16, or monochrome)
- Width and height management
- Rendering pipeline coordination
- File output and export (HTML, SVG, text)
- Print, log, and status methods

**Protocol (`protocol.py`)**: Defines the renderable protocol. Objects become renderable by implementing:
- `__rich_console__(console, options)`: Primary rendering method
- `__rich__()`: Returns another renderable (transformation)
- Simple string objects are inherently renderable

**Segment (`segment.py`)**: Atomic unit of terminal output, combining text with style information. The Console breaks all output into segments before rendering.

### High-Level Components Layer

Components that users directly interact with:
- `Table`: Full-featured table with headers, footers, borders, automatic sizing
- `Tree`: Hierarchical tree display with guide lines
- `Panel`: Content with borders and optional title/subtitle
- `Layout`: Advanced grid layout system for terminal UIs
- `Columns`: Multi-column text flow
- Various wrappers: `Align`, `Padding`, `Constrain`

### Specialized Renderers

Domain-specific rendering:
- `Syntax`: Code syntax highlighting using Pygments lexers
- `Markdown`: Full markdown support including code blocks, lists, tables
- `Traceback`: Enhanced Python traceback with syntax highlighting
- `JSON`: Pretty-printed JSON with syntax highlighting
- `Pretty`: Generic pretty-printer for Python objects

### Progress System

Multi-layered progress tracking:
- `Progress`: Main progress manager, handles multiple concurrent tasks
- `ProgressBar`: Individual bar rendering with customizable appearance
- `Status`: Spinner-based status for indeterminate progress
- `Live`: Context manager for live-updating displays

### Style and Color System

Sophisticated color handling:
- `Style`: Immutable style definition (color, bold, italic, etc.)
- `Color`: Color parsing and conversion (named, hex, RGB, ANSI)
- `Theme`: Named style collections
- Automatic downsampling based on terminal capabilities

### Platform Abstraction

Platform-specific code isolated in dedicated modules:
- Windows console API integration (`_windows*.py`)
- Jupyter notebook protocol (`jupyter.py`)
- Unicode width data for various Unicode versions

## Code Organization Patterns

**Protocol-Based Design**: Rich uses protocols (duck typing) rather than inheritance. Any object implementing `__rich_console__` can participate in rendering.

**Immutable Styles**: Style objects are immutable and composable, enabling safe style inheritance through the rendering tree.

**Lazy Rendering**: Measurements happen separately from rendering, allowing the Console to optimize layout before generating output.

**Type Hints**: Extensive use of type hints throughout the codebase with strict mypy configuration.

**Testing**: Comprehensive test coverage with snapshot testing for rendered output.

## Key Files by Functionality

| Functionality | Primary Files |
|--------------|--------------|
| Basic text output | `console.py`, `text.py`, `print.py` |
| Tables | `table.py`, `box.py` |
| Progress bars | `progress.py`, `progress_bar.py`, `live.py` |
| Syntax highlighting | `syntax.py`, `highlighter.py` |
| Colors | `color.py`, `palette.py`, `theme.py` |
| Markdown | `markdown.py` |
| Tracebacks | `traceback.py` |
| Trees | `tree.py` |
| Logging | `logging.py`, `_log_render.py` |

The codebase is well-organized with clear separation of concerns, making it easy to locate functionality and understand dependencies between modules.
