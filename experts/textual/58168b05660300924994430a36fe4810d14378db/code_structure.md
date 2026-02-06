# Textual Code Structure

## Complete Annotated Directory Tree

```
textual/
├── src/textual/              # Main package source code
│   ├── __init__.py           # Package exports: log, on, work decorators
│   ├── __main__.py           # Demo application entry point
│   ├── app.py                # App class - root application container
│   ├── widget.py             # Widget base class - foundation for all UI elements
│   ├── screen.py             # Screen class - top-level containers for views
│   ├── dom.py                # DOMNode - base class for DOM tree elements
│   ├── message_pump.py       # MessagePump - async event queue and routing
│   ├── reactive.py           # Reactive system - declarative state management
│   ├── binding.py            # Keyboard bindings and keymap system
│   ├── actions.py            # Action system for keyboard-triggered commands
│   ├── events.py             # Event definitions (Key, Mouse, Focus, etc.)
│   ├── messages.py           # Internal messaging system
│   ├── command.py            # Command palette infrastructure
│   ├── content.py            # Content protocol for custom renderables
│   ├── geometry.py           # Geometric primitives (Offset, Region, Size, Spacing)
│   ├── color.py              # Color class with parsing and manipulation
│   ├── strip.py              # Strip - optimized row rendering primitive
│   ├── style.py              # Style classes for visual rendering
│   ├── visual.py             # Visual type system for style representation
│   ├── compose.py            # Widget composition utilities
│   ├── timer.py              # Timer for scheduled callbacks
│   ├── selection.py          # Text selection system
│   ├── notifications.py      # Toast notification system
│   ├── pilot.py              # Pilot - programmatic app control for testing
│   ├── cache.py              # FIFO and LRU cache implementations
│   ├── box_model.py          # CSS box model implementation
│   ├── rlock.py              # Reentrant lock for thread safety
│   ├── signal.py             # Signal system for pub/sub patterns
│   ├── layout.py             # Layout base class
│   ├── await_complete.py     # Async completion utilities
│   ├── await_remove.py       # Async widget removal utilities
│   ├── constants.py          # Framework-wide constants
│   ├── errors.py             # Custom exception classes
│   ├── keys.py               # Keyboard key definitions and parsing
│   ├── case.py               # String case conversion utilities
│   ├── filter.py             # Line filters for visual effects
│   ├── suggester.py          # Auto-suggestion system for inputs
│   ├── validation.py         # Input validation framework
│   │
│   ├── css/                  # CSS engine implementation
│   │   ├── __init__.py
│   │   ├── parse.py          # CSS parser
│   │   ├── tokenize.py       # CSS tokenizer
│   │   ├── stylesheet.py     # Stylesheet representation
│   │   ├── styles.py         # Styles class - computed style container
│   │   ├── query.py          # DOM query system (CSS selectors)
│   │   ├── model.py          # CSS rule and selector models
│   │   ├── match.py          # Selector matching engine
│   │   ├── scalar.py         # Scalar values (pixels, percent, etc.)
│   │   ├── errors.py         # CSS-related exceptions
│   │   ├── constants.py      # CSS constants
│   │   ├── types.py          # CSS type definitions
│   │   ├── _style_properties.py  # Style property descriptors
│   │   ├── _styles_builder.py    # Styles construction
│   │   ├── _error_tools.py       # Error reporting utilities
│   │   ├── _help_renderables.py  # Help text rendering
│   │   └── _help_text.py         # Style documentation strings
│   │
│   ├── widgets/              # Built-in widget library (58 files)
│   │   ├── __init__.py       # Widget exports with lazy loading
│   │   ├── _button.py        # Button - clickable button widget
│   │   ├── _checkbox.py      # Checkbox - boolean selection
│   │   ├── _collapsible.py   # Collapsible - expandable container
│   │   ├── _content_switcher.py  # ContentSwitcher - content switching
│   │   ├── _data_table.py    # DataTable - tabular data display
│   │   ├── _digits.py        # Digits - large numeric display
│   │   ├── _directory_tree.py    # DirectoryTree - file system browser
│   │   ├── _footer.py        # Footer - app footer with key hints
│   │   ├── _header.py        # Header - app header with title
│   │   ├── _help_panel.py    # HelpPanel - keyboard help display
│   │   ├── _input.py         # Input - single-line text input
│   │   ├── _key_panel.py     # KeyPanel - key binding display
│   │   ├── _label.py         # Label - static text display
│   │   ├── _link.py          # Link - clickable hyperlink
│   │   ├── _list_item.py     # ListItem - item in ListView
│   │   ├── _list_view.py     # ListView - scrollable list
│   │   ├── _loading_indicator.py # LoadingIndicator - loading animation
│   │   ├── _log.py           # Log - text log display
│   │   ├── _markdown.py      # Markdown/MarkdownViewer - markdown rendering
│   │   ├── _masked_input.py  # MaskedInput - formatted input
│   │   ├── _option_list.py   # OptionList - selectable option list
│   │   ├── _placeholder.py   # Placeholder - development placeholder
│   │   ├── _pretty.py        # Pretty - pretty-printed Python objects
│   │   ├── _progress_bar.py  # ProgressBar - progress visualization
│   │   ├── _radio_button.py  # RadioButton - exclusive selection
│   │   ├── _radio_set.py     # RadioSet - radio button group
│   │   ├── _rich_log.py      # RichLog - rich text log
│   │   ├── _rule.py          # Rule - horizontal/vertical line
│   │   ├── _select.py        # Select - dropdown selection
│   │   ├── _selection_list.py    # SelectionList - multi-select list
│   │   ├── _sparkline.py     # Sparkline - inline charts
│   │   ├── _static.py        # Static - static content display
│   │   ├── _switch.py        # Switch - toggle switch
│   │   ├── _tabbed_content.py    # TabbedContent/TabPane - tabbed interface
│   │   ├── _tabs.py          # Tab/Tabs - tab navigation
│   │   ├── _text_area.py     # TextArea - multi-line text editor
│   │   ├── _toast.py         # Toast - notification toast
│   │   ├── _tooltip.py       # Tooltip - hover tooltips
│   │   ├── _tree.py          # Tree - hierarchical tree view
│   │   └── _welcome.py       # Welcome - welcome screen
│   │
│   ├── layouts/              # Layout engines
│   │   ├── __init__.py
│   │   ├── factory.py        # Layout factory
│   │   ├── vertical.py       # VerticalLayout - vertical stacking
│   │   ├── horizontal.py     # HorizontalLayout - horizontal stacking
│   │   ├── grid.py           # GridLayout - CSS grid layout
│   │   └── stream.py         # StreamLayout - stream/wrap layout
│   │
│   ├── drivers/              # Platform-specific terminal drivers
│   │   ├── __init__.py
│   │   ├── linux_driver.py   # Linux terminal driver
│   │   ├── linux_inline_driver.py  # Linux inline mode driver
│   │   ├── windows_driver.py # Windows console driver
│   │   ├── win32.py          # Win32 API bindings
│   │   ├── web_driver.py     # Web browser driver
│   │   ├── headless_driver.py    # Headless driver for testing
│   │   ├── _input_reader.py      # Input reading base class
│   │   ├── _input_reader_linux.py    # Linux input reader
│   │   ├── _input_reader_windows.py  # Windows input reader
│   │   ├── _byte_stream.py       # Byte stream handling
│   │   └── _writer_thread.py     # Output writer thread
│   │
│   ├── renderables/          # Custom Rich renderables
│   │   ├── __init__.py
│   │   ├── blank.py          # Blank renderable
│   │   ├── background_screen.py  # Background screen rendering
│   │   └── (other renderables)
│   │
│   ├── document/             # Document model for TextArea
│   │   ├── __init__.py
│   │   ├── _document.py      # Document representation
│   │   ├── _edit.py          # Edit operations
│   │   └── _wrapped_document.py  # Wrapped text handling
│   │
│   ├── tree-sitter/          # Tree-sitter syntax highlighting
│   │   ├── highlights/       # Highlight query files
│   │   └── (language-specific files)
│   │
│   ├── demo/                 # Built-in demo application
│   │   └── (demo files)
│   │
│   └── (many internal modules)
│       ├── _animator.py      # Animation system
│       ├── _ansi_sequences.py    # ANSI escape sequences
│       ├── _ansi_theme.py        # ANSI color themes
│       ├── _arrange.py           # Widget arrangement
│       ├── _binary_encode.py     # Binary encoding utilities
│       ├── _border.py            # Border rendering
│       ├── _box_drawing.py       # Box drawing characters
│       ├── _callback.py          # Callback invocation
│       ├── _cells.py             # Cell width calculations
│       ├── _color_constants.py   # Named color constants
│       ├── _compat.py            # Python version compatibility
│       ├── _compositor.py        # Screen composition
│       ├── _context.py           # Context variables (active app, screen)
│       ├── _debug.py             # Debug utilities
│       ├── _dispatch_key.py      # Key dispatch system
│       ├── _doc.py               # Documentation utilities
│       ├── _duration.py          # Duration parsing
│       ├── _easing.py            # Easing functions for animation
│       ├── _event_broker.py      # Event handler registration
│       ├── _extrema.py           # Min/max tracking
│       ├── _files.py             # File utilities
│       ├── _immutable_sequence_view.py  # Immutable sequence wrapper
│       ├── _import_app.py        # App import utilities
│       ├── _keyboard_protocol.py # Keyboard protocol handling
│       ├── _layout_resolve.py    # Layout resolution
│       ├── _line_split.py        # Line splitting utilities
│       ├── _log.py               # Logging infrastructure
│       ├── _loop.py              # Event loop integration
│       ├── _on.py                # @on decorator implementation
│       ├── _path.py              # Path utilities
│       ├── _spatial_map.py       # Spatial indexing for widgets
│       ├── _styles_cache.py      # Style caching
│       ├── _types.py             # Type definitions
│       ├── _wait.py              # Wait utilities
│       ├── _work_decorator.py    # @work decorator
│       └── _worker.py            # Worker thread system
│
├── tests/                    # Comprehensive test suite
│   ├── (985+ Python test files)
│   └── snapshot_tests/       # Snapshot testing assets
│
├── examples/                 # Example applications
│   ├── calculator.py         # Calculator demo
│   ├── code_browser.py       # Code browser with syntax highlighting
│   ├── dictionary.py         # Dictionary lookup
│   ├── calculator.tcss       # Associated stylesheets
│   └── (50+ example files)
│
├── docs/                     # Documentation source
│   ├── guide/                # User guides
│   ├── api/                  # API reference
│   ├── blog/                 # Blog posts
│   ├── widgets/              # Widget documentation
│   ├── styles/               # Style documentation
│   ├── css_types/            # CSS type documentation
│   ├── events/               # Event documentation
│   ├── examples/             # Documentation examples
│   └── images/               # Documentation images
│
├── tools/                    # Development tools
├── reference/                # Reference materials
├── pyproject.toml            # Project configuration (Poetry)
├── Makefile                  # Build/test/docs automation
├── mkdocs*.yml               # Documentation configuration
├── mypy.ini                  # Type checker configuration
├── .coveragerc               # Coverage configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── CODE_OF_CONDUCT.md        # Code of conduct
└── README.md                 # Project overview
```

## Module and Package Organization

The codebase follows a clear hierarchical organization with strong separation of concerns:

### Core Framework Layer
The top-level `src/textual/` modules provide the framework's core abstractions:
- **app.py**, **screen.py**, **widget.py**, **dom.py** form the component hierarchy
- **message_pump.py** handles async event routing
- **reactive.py** provides reactive state management
- **events.py**, **messages.py** define event and message types
- **geometry.py**, **color.py**, **strip.py**, **style.py** provide rendering primitives

### Subsystem Packages
Specialized functionality is organized into focused packages:
- **css/**: Complete CSS engine (parsing, matching, styling)
- **widgets/**: 40+ built-in widgets, each in its own file
- **layouts/**: Layout algorithms (vertical, horizontal, grid, stream)
- **drivers/**: Platform-specific terminal I/O
- **renderables/**: Custom Rich renderables
- **document/**: Document model for text editing

### Internal Modules
Modules prefixed with underscore (_) are internal implementation details:
- Animation, compositor, event broker, spatial indexing
- ANSI sequences, keyboard protocols, worker system
- Caching, debugging, compatibility utilities

## Main Source Directories and Their Purposes

**src/textual/**: Core framework implementation (246 Python files)
- Foundation classes and primitives
- Event system and message pump
- Rendering pipeline and drivers
- Complete CSS engine

**src/textual/widgets/**: Built-in widget library (58 files)
- Production-ready UI components
- Each widget in a separate file prefixed with underscore
- Lazy-loaded via `__init__.py` for fast import times

**src/textual/css/**: CSS implementation (20+ files)
- CSS tokenizer and parser
- Selector matching and specificity
- Style computation and inheritance
- Query system for DOM traversal

**tests/**: Test suite (985+ files)
- Unit tests for all components
- Integration tests
- Snapshot tests for visual regression testing
- Test fixtures and utilities

**docs/**: Documentation (extensive)
- User guides and tutorials
- API reference (auto-generated from docstrings)
- Widget gallery with live examples
- Style reference and CSS documentation

**examples/**: Example applications (50+ files)
- Demonstrate various features
- Serve as templates for developers
- Include complete apps with stylesheets

## Key Files and Their Roles

**src/textual/app.py** (3000+ lines)
- `App` class - root application container
- Screen stack management
- Rendering coordination and frame timing
- Global message routing and timer management
- Command palette integration
- Dev tools integration

**src/textual/widget.py** (5000+ lines)
- `Widget` base class - foundation for all UI elements
- Layout calculation and box model
- Rendering pipeline integration
- Event handling and message passing
- Style application and animation
- Scroll management and focus handling

**src/textual/screen.py** (1500+ lines)
- `Screen` class - top-level view containers
- Modal screen support
- Screen-specific bindings and styles
- Focus and layer management

**src/textual/message_pump.py** (1000+ lines)
- Async event queue and dispatcher
- Message priority and filtering
- Event handler discovery and invocation
- Context management for active message pumps

**src/textual/reactive.py** (600+ lines)
- Reactive attribute descriptor
- Automatic observer/watcher invocation
- Validation and type checking
- Computed reactive attributes

**src/textual/css/parse.py** (1000+ lines)
- Complete CSS parser implementation
- Tokenization and syntax analysis
- Error reporting with line/column information
- Supports Textual CSS extensions

**src/textual/css/query.py** (800+ lines)
- DOM query system similar to jQuery
- CSS selector matching
- Type-safe query results
- Query chaining and filtering

**src/textual/pilot.py** (500+ lines)
- Programmatic app control for testing
- Simulates user input (keyboard, mouse, clicks)
- Screenshot capture and comparison
- Async/await testing patterns

**pyproject.toml**
- Poetry-based project configuration
- Dependencies (rich, markdown-it-py, platformdirs, typing-extensions)
- Optional dependencies (tree-sitter language parsers)
- Build configuration and metadata
- Testing and tooling configuration

**Makefile**
- Build automation: test, format, typecheck, docs
- Poetry integration: `$(run) = poetry run`
- Parallel testing with pytest-xdist
- Documentation building (online/offline variants)

## Code Organization Patterns

**Lazy Loading**: Widgets are lazy-loaded via `__getattr__` in `widgets/__init__.py` to minimize import time.

**Private Modules**: Internal implementation uses underscore prefixes (_animator.py, _compositor.py) to signal non-public APIs.

**Type Hints**: Comprehensive type annotations with TYPE_CHECKING guards to avoid circular imports.

**Async-First**: Core APIs use asyncio (async/await, create_task, gather) with sync wrappers for convenience.

**Rich Protocol**: Extensive use of Rich's protocol classes (RenderableType, Console, Segment) for rendering.

**Descriptor Protocol**: Reactive attributes use Python descriptors for transparent value tracking.

**Context Variables**: ContextVar for active app, screen, and message pump tracking without globals.

**Testing Architecture**: Snapshot tests for visual regression, pytest-asyncio for async tests, parallel execution with pytest-xdist.

The codebase demonstrates production-quality Python with excellent documentation, comprehensive testing, and careful API design for extensibility and maintainability.
