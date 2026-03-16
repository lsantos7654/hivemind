# Posting — Code Structure

## Annotated Directory Tree

```
posting/
├── .github/                           # GitHub Actions CI/CD workflows
├── .python-version                    # Pins Python to 3.11.7
├── CONTRIBUTING.md                    # Contribution guidelines
├── LICENSE                            # Apache License 2.0
├── Makefile                           # Developer task shortcuts (test, snapshot-update)
├── NOTICE                             # Legal notices
├── README.md                          # Project overview and installation
├── mkdocs.yml                         # MkDocs documentation site config
├── pyproject.toml                     # Project metadata, dependencies, build system
├── uv.lock                            # Locked dependency versions for reproducible builds
│
├── docs/                              # MkDocs documentation source
│   ├── CHANGELOG.md                   # Release history
│   ├── index.md                       # Landing page
│   ├── faq.md                         # Frequently asked questions
│   ├── roadmap.md                     # Planned features
│   ├── assets/                        # Images, demo videos, SVGs used in docs
│   ├── guide/                         # User guide articles
│   │   ├── collections.md             # How collections and requests are organized
│   │   ├── command_palette.md         # Command palette usage
│   │   ├── configuration.md           # All config options reference
│   │   ├── environments.md            # Environment variables and .env files
│   │   ├── external_tools.md          # Editor/pager integration
│   │   ├── help_system.md             # Built-in help system docs
│   │   ├── importing.md               # Importing cURL, Postman, OpenAPI
│   │   ├── index.md                   # Guide index
│   │   ├── keymap.md                  # Keyboard shortcuts reference
│   │   ├── navigation.md              # Navigation and jump mode
│   │   ├── requests.md                # Building and sending requests
│   │   ├── scripting.md               # Python scripting API
│   │   └── themes.md                  # Theming and customization
│   ├── overrides/                     # MkDocs theme overrides
│   └── stylesheets/                   # Custom CSS for docs site
│
├── src/posting/                       # Main Python package
│   ├── __init__.py                    # Public API exports
│   ├── __main__.py                    # CLI entry point (click commands)
│   ├── _start_time.py                 # Captures process start time for perf metrics
│   ├── app.py                         # Core Textual App class (~3000 lines)
│   │
│   ├── # ── Core Data Models ──
│   ├── collection.py                  # RequestModel, Collection, Auth, Body, Options (500+ lines)
│   ├── types.py                       # Type aliases: HttpRequestMethod, PostingLayout, CertTypes
│   │
│   ├── # ── Configuration ──
│   ├── config.py                      # Settings model (pydantic-settings, YAML config)
│   ├── locations.py                   # XDG-aware path resolution for config/data/themes
│   ├── help_data.py                   # Static content for built-in help panels
│   │
│   ├── # ── HTTP & Auth ──
│   ├── auth.py                        # HttpxBearerTokenAuth (httpx.Auth subclass)
│   ├── request_headers.py             # Header name suggestions and management (412 lines)
│   │
│   ├── # ── Request Lifecycle ──
│   ├── save_request.py                # Logic for persisting requests to YAML files
│   ├── commands.py                    # Command palette provider (CommandProvider subclass)
│   │
│   ├── # ── Scripting ──
│   ├── scripts.py                     # Script execution engine + Posting API class (214 lines)
│   │
│   ├── # ── Variables & Environments ──
│   ├── variables.py                   # Variable loading, substitution, SharedVariables (158 lines)
│   │
│   ├── # ── URL Handling ──
│   ├── urls.py                        # URL utilities: protocol, path params, substitution
│   │
│   ├── # ── Navigation ──
│   ├── jumper.py                      # Jump mode: widget labeling and target resolution (60 lines)
│   ├── jump_overlay.py                # Jump mode: overlay widget showing shortcut labels (118 lines)
│   │
│   ├── # ── Import/Export ──
│   ├── importing/
│   │   ├── __init__.py
│   │   ├── curl.py                    # cURL command parser → RequestModel (260+ lines)
│   │   ├── postman.py                 # Postman collection JSON importer (235 lines)
│   │   └── open_api.py                # OpenAPI 3.x spec importer (280+ lines)
│   │
│   ├── # ── Display & Themes ──
│   ├── themes.py                      # Theme engine: builtin, user YAML, Xresources (587 lines)
│   ├── highlight_url.py               # URL syntax highlighter for Rich/Textual
│   ├── highlighters.py                # Custom Rich highlighters for response display (113 lines)
│   ├── xresources.py                  # X11 Xresources color parsing (56 lines)
│   ├── help_screen.py                 # Help overlay screen
│   ├── posting.scss                   # SCSS styles for all Textual widgets
│   │
│   ├── # ── UI Widgets ──
│   ├── widgets/
│   │   ├── __init__.py                # Widget re-exports
│   │   ├── center_middle.py           # Centering layout container
│   │   ├── confirmation.py            # Modal confirmation dialog
│   │   ├── datatable.py               # Extended DataTable widget
│   │   ├── input.py                   # Extended Input widget
│   │   ├── key_value.py               # Reusable key-value table editor
│   │   ├── rich_log.py                # Rich-formatted logging widget
│   │   ├── select.py                  # Extended Select widget
│   │   ├── tabbed_content.py          # Tabbed container with keyboard nav
│   │   ├── text_area.py               # Extended TextArea widget
│   │   ├── tree.py                    # Extended Tree widget for collection browser
│   │   ├── variable_autocomplete.py   # Autocomplete for $VARIABLE references
│   │   ├── variable_input.py          # Input with built-in variable autocomplete
│   │   │
│   │   ├── collection/                # Collection sidebar widgets
│   │   │   ├── browser.py             # CollectionBrowser: file-tree sidebar
│   │   │   └── new_request_modal.py   # Modal for creating new requests
│   │   │
│   │   ├── request/                   # Request editor panel widgets
│   │   │   ├── form_editor.py         # Form data editor (key-value table)
│   │   │   ├── header_editor.py       # Headers table editor
│   │   │   ├── method_selection.py    # HTTP method selector (dropdown)
│   │   │   ├── path_editor.py         # Path parameters editor
│   │   │   ├── query_editor.py        # Query params editor
│   │   │   ├── request_auth.py        # Auth configuration widget (Basic/Digest/Bearer)
│   │   │   ├── request_body.py        # Body editor (JSON/form/raw tabs)
│   │   │   ├── request_editor.py      # Main request panel container
│   │   │   ├── request_metadata.py    # Request name/description editor
│   │   │   ├── request_options.py     # Options: SSL, redirects, timeout, proxy
│   │   │   ├── request_scripts.py     # Script editor tabs (setup/on_request/on_response)
│   │   │   └── url_bar.py             # URL bar with method selector
│   │   │
│   │   └── response/                  # Response viewer panel widgets
│   │       ├── cookies_table.py       # Response cookies table
│   │       ├── response_area.py       # Response panel container
│   │       ├── response_body.py       # Response body viewer with syntax highlighting
│   │       ├── response_headers.py    # Response headers table
│   │       ├── response_trace.py      # Request/response trace log
│   │       └── script_output.py       # Script stdout/stderr output panel
│   │
│   ├── # ── Utilities ──
│   ├── files.py                       # File naming validation (DOS names, 255-char limit)
│   ├── yaml.py                        # Custom YAML serialization helpers
│   ├── user_host.py                   # Current user and hostname lookup
│   ├── suggesters.py                  # Textual Suggester subclasses for autocomplete
│   ├── messages.py                    # Custom Textual Message types
│   ├── tuple_to_multidict.py          # Convert tuples to httpx multidict format
│   ├── version.py                     # VERSION constant
│   └── exit_codes.py                  # Process exit code constants
│
└── tests/                             # Test suite
    ├── __snapshots__/                 # Stored UI snapshot baselines (auto-managed by syrupy)
    │   └── test_snapshots/
    ├── posting_snapshot_app.py        # Fixture: creates a Posting app for snapshot tests
    ├── resources/
    │   └── snapshot_report_template.jinja2  # HTML report template for snapshot diffs
    │
    ├── sample-collections/            # Real .posting.yaml request files for tests
    │   ├── echo.posting.yaml
    │   ├── echo-post-01.posting.yaml
    │   ├── get-random-user.posting.yaml
    │   ├── jsonplaceholder/           # Collection of JSONPlaceholder API requests
    │   └── scripts/                   # Sample scripts for testing script execution
    │
    ├── sample-configs/                # Config file fixtures for settings tests
    │   ├── custom_theme.yaml
    │   ├── custom_theme2.yaml
    │   ├── general.yaml
    │   └── modified_config.yaml
    │
    ├── sample-envs/                   # .env file fixtures for variable tests
    │   ├── sample_base.env
    │   └── sample_extra.env
    │
    ├── sample-importable-collections/ # Import test data
    │   ├── Fixer.postman_collection.json
    │   ├── postman_collection.json
    │   └── test-postman-collection.json
    │
    ├── sample-themes/                 # Theme file fixtures
    │   ├── another_test.yml
    │   └── serene_ocean.yaml
    │
    ├── test_curl_export.py            # cURL export tests
    ├── test_curl_import.py            # cURL parsing tests
    ├── test_files.py                  # File naming utility tests
    ├── test_open_api_import.py        # OpenAPI importer tests
    ├── test_postman_import.py         # Postman importer tests
    ├── test_snapshots.py              # UI snapshot integration tests (29KB, ~100 test cases)
    ├── test_urls.py                   # URL utility tests
    └── test_variables.py              # Variable substitution tests
```

## Module and Package Organization

The codebase is organized into logical layers with clear separation of concerns:

### Layer 1: Entry Point & CLI (`__main__.py`)
Click-based CLI with `DefaultGroup` so `posting` with no args launches the TUI. Commands: `default` (TUI), `locate`, `import`, `sponsors`.

### Layer 2: Application Core (`app.py`)
The central `Posting(App)` class wires all components together. It handles screen management, global key bindings, request sending, and event routing. At ~3000 lines this is the largest file and the integration hub.

### Layer 3: Data Models (`collection.py`, `types.py`)
Pydantic `BaseModel` classes representing every domain concept: `RequestModel`, `Collection`, `Auth`, `RequestBody`, `Header`, `QueryParam`, `PathParam`, `Cookie`, `FormItem`, `Options`, `Scripts`. These are also the public API exported from `__init__.py`.

### Layer 4: Configuration (`config.py`, `locations.py`)
`Settings` (pydantic-settings) loads `config.yaml` from XDG paths. `locations.py` provides OS-aware path resolution for config, data, and theme directories.

### Layer 5: Business Logic
- `scripts.py` — script runner and `Posting` API
- `variables.py` — environment variable loading and substitution
- `urls.py` — URL parsing and path parameter handling
- `auth.py` — custom httpx auth handler
- `request_headers.py` — header suggestion data
- `save_request.py` — YAML persistence logic
- `commands.py` — command palette integration

### Layer 6: Import/Export (`importing/`)
Each importer module is independent: `curl.py` uses argparse-style parsing of cURL commands, `postman.py` parses Postman v2 JSON, `open_api.py` uses `openapi-pydantic` for structured spec parsing. All produce `RequestModel` or `Collection` instances.

### Layer 7: UI Widgets (`widgets/`)
Three sub-packages mirror the UI layout:
- `collection/` — sidebar tree browser
- `request/` — request editing widgets (one widget per request section)
- `response/` — response display widgets

### Layer 8: Display Utilities
`themes.py`, `highlight_url.py`, `highlighters.py`, `xresources.py`, `posting.scss` — all visual rendering concerns.

## Code Organization Patterns

**Pydantic everywhere:** All structured data uses Pydantic v2 models. Serialization to YAML uses custom `yaml.py` helpers. Deserialization uses model `model_validate()`.

**Textual widget pattern:** Each widget file defines exactly one main widget class, follows Textual's reactive/message pattern. Widgets communicate upward via `post_message()`.

**Type aliases in `types.py`:** Reusable types like `HttpRequestMethod = Literal["GET", "POST", ...]` are defined centrally and imported widely.

**XDG compliance:** All file paths go through `locations.py` which wraps `xdg-base-dirs` for cross-platform config/data storage.

**Async throughout:** `app.py` uses `async def` action methods; HTTP requests use `httpx.AsyncClient` with `await`; script execution is also wrapped in async context.
