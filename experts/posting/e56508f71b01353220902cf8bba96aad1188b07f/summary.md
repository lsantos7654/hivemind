# Posting — Repository Summary

## Purpose and Goals

Posting is a modern, terminal-based HTTP client (TUI application) designed as a keyboard-centric alternative to GUI tools like Postman or Insomnia. Its primary goal is to provide a powerful, efficient interface for testing and interacting with HTTP APIs directly from the terminal, with full support for remote sessions over SSH.

Requests are stored as plain YAML files (`.posting.yaml`), making them easy to version-control and share via git. The design philosophy prioritizes keyboard efficiency, developer ergonomics, and scriptability over point-and-click workflows.

**Current version:** 2.9.2
**License:** Apache 2.0
**Website:** https://posting.sh
**Repository:** https://github.com/darrenburns/posting

## Key Features and Capabilities

- **Full-featured HTTP client** — supports GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS with headers, query params, path params, cookies, request body (JSON, form, raw), and authentication (Basic, Digest, Bearer Token)
- **Terminal UI** — built with the Textual framework; runs natively in any terminal, including over SSH
- **Jump mode navigation** — rapid keyboard-driven navigation to any UI element (Ctrl+O)
- **Environment/variable support** — load `.env` files, host environment variables, use `$VAR` or `${VAR}` syntax in requests
- **Python scripting** — run Python scripts before/after requests (`setup`, `on_request`, `on_response` hooks) with access to a `Posting` API for variable management and notifications
- **Import formats** — import from cURL commands, Postman collections (JSON), and OpenAPI specs (YAML/JSON)
- **Export to cURL** — one-command export of any request to a cURL string
- **Syntax highlighting** — tree-sitter powered syntax highlighting for request/response bodies
- **Vim key bindings** — optional vi-style navigation
- **Customizable keybindings** — user-defined key remaps
- **Themes** — built-in themes, user-defined YAML themes, X11 Xresources support
- **Command palette** — quick access to all actions
- **Collections** — organize requests in nested directory hierarchies
- **Autocomplete** — variable and header name suggestions
- **Open in editor/pager** — `$EDITOR` / `$PAGER` integration

## Primary Use Cases and Target Audience

**Target audience:** Backend developers, API engineers, DevOps professionals, and CLI power-users who prefer terminal-centric workflows and want their HTTP request collections under version control.

**Primary use cases:**
1. Interactive API exploration and testing during development
2. Maintaining a versioned collection of API requests alongside a codebase
3. Scripted API workflows with pre/post-request Python hooks
4. Remote API testing over SSH without a GUI
5. Rapid prototyping of HTTP requests with variable substitution
6. Team-shared API collections stored in git repositories

## High-Level Architecture Overview

Posting is a Python application built on three main pillars:

**1. Textual TUI Framework**
The UI layer is built entirely with [Textual](https://github.com/Textualize/textual), a Python framework for building terminal applications. The main application class `Posting(App)` in `app.py` orchestrates all screens, widgets, and event handling. UI components are organized into three widget groups: collection browser, request editor, and response viewer.

**2. httpx Async HTTP Engine**
All HTTP requests are executed via `httpx.AsyncClient`, enabling non-blocking I/O within Textual's async event loop. A pinned version (0.28.1) is used with a monkeypatch to prevent httpx from loading its CLI module.

**3. Pydantic Data Models**
Request data, configuration, and authentication are modeled with Pydantic v2 `BaseModel` classes. The `RequestModel` class is the central data structure, serialized to/from YAML files for persistence. Settings are loaded via `pydantic-settings` from a YAML config file at `$XDG_CONFIG_HOME/posting/config.yaml`.

**Data flow:**
```
CLI (click) → make_posting() → Posting(App)
    → CollectionBrowser loads .posting.yaml files as RequestModel
    → User edits request in RequestEditor widgets
    → Send action → httpx.AsyncClient.send(request.to_httpx())
    → Scripts run (setup → on_request → HTTP → on_response)
    → ResponseArea displays result
```

**File layout:**
- `src/posting/` — main source package
- `src/posting/widgets/` — all Textual widget classes
- `src/posting/importing/` — format importers (cURL, Postman, OpenAPI)
- `tests/` — pytest test suite with snapshot tests

## Related Projects and Dependencies

**Core runtime dependencies:**
- [Textual](https://github.com/Textualize/textual) (`textual[syntax]==6.1.0`) — TUI framework
- [httpx](https://www.python-httpx.org/) (`httpx[brotli]==0.28.1`) — async HTTP client
- [Pydantic](https://docs.pydantic.dev/) (`pydantic>=2.9.2`) — data validation and serialization
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — config file loading
- [click](https://click.palletsprojects.com/) — CLI framework
- [textual-autocomplete](https://github.com/darrenburns/textual-autocomplete) — autocomplete widget
- [openapi-pydantic](https://github.com/mike-oakley/openapi-pydantic) — OpenAPI spec parsing
- [watchfiles](https://watchfiles.helpmanual.io/) — file system monitoring
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` file loading
- [xdg-base-dirs](https://pypi.org/project/xdg-base-dirs/) — XDG directory standard
- [pyperclip](https://pypi.org/project/pyperclip/) — clipboard access
- [PyYAML](https://pyyaml.org/) — YAML serialization

**Development tools:**
- [uv](https://docs.astral.sh/uv/) — package manager (recommended)
- [pytest](https://pytest.org/) + `pytest-textual-snapshot` + `syrupy` — testing
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) — documentation site
