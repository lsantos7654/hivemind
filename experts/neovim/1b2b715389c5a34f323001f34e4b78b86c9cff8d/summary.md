# Neovim Repository Summary

## Repository Purpose and Goals

Neovim is an aggressive refactor of Vim that seeks to simplify maintenance, enable advanced user interfaces without core modifications, and maximize extensibility. Forked from Vim 7.4.160, it modernizes the codebase while maintaining compatibility with Vim plugins (including Ruby and Python plugins). The project's central goals are:

- Simplify maintenance and encourage contributions
- Split work across multiple developers (clean subsystem boundaries)
- Enable advanced GUIs via a stable RPC API without patching the core
- Maximize extensibility through a powerful Lua/C API and plugin model

## Key Features and Capabilities

**Extensibility and API**
- Full-featured C API exposed over msgpack-RPC, accessible from any language (Python, Ruby, Go, Rust, Node.js, Java, Haskell, Lua, and more)
- Lua as first-class configuration and plugin language (init.lua, runtime Lua modules)
- Vimscript compatibility for legacy plugins
- Embeddable as a library (`libnvim`) for use in custom applications

**Editor Features**
- Embedded, scriptable terminal emulator (`terminal.c`)
- Asynchronous job control for non-blocking subprocess execution
- Shared data (ShaDa) across multiple editor instances
- XDG base directories support
- Floating windows and virtual text via the extmarks API
- Built-in diff viewer and fold support
- Full Unicode/multibyte support

**Developer Tooling (Built-in)**
- Language Server Protocol (LSP) client (`runtime/lua/vim/lsp/`)
- Tree-sitter integration for syntax highlighting and code analysis (`runtime/lua/vim/treesitter/`)
- Built-in diagnostic framework (`runtime/lua/vim/diagnostic.lua`)
- Health check system (`runtime/lua/vim/health.lua`)
- Built-in snippet support (`runtime/lua/vim/snippet.lua`)
- EditorConfig support (`runtime/plugin/editorconfig.lua`)

**UI System**
- Multiple UI paradigm: any number of remote UIs can attach via RPC
- TUI (built-in terminal UI) using terminfo/vterm
- UI events delivered via msgpack-RPC `redraw` notifications
- In-process UI attachment via `vim.ui_attach()` for Lua plugins

## Primary Use Cases and Target Audience

- **End users**: Drop-in Vim replacement with modern features, Lua configuration, and a rich plugin ecosystem
- **Plugin developers**: Build Lua plugins using `vim.*` APIs, LSP integrations, treesitter queries, and extmarks decorations
- **GUI/TUI developers**: Build advanced front-ends by connecting to Neovim's RPC server and consuming UI events
- **Tool integrators**: Embed `libnvim` in applications or drive Neovim programmatically via the RPC API
- **Core contributors**: Extend C subsystems (buffer, window, event loop, API) using the well-structured module system

## High-Level Architecture Overview

Neovim is structured as a **C core** with a **Lua layer** on top, communicating with the outside world via **msgpack-RPC**:

```
┌─────────────────────────────────────────────────────────┐
│                    External Clients                       │
│   (GUI, remote plugins, scripts, other Nvim instances)   │
└────────────────────────┬────────────────────────────────┘
                         │ msgpack-RPC (TCP/Unix socket)
┌────────────────────────▼────────────────────────────────┐
│                    C API layer                            │
│  src/nvim/api/  (vim.c, buffer.c, window.c, ui.c, …)    │
├─────────────────────────────────────────────────────────┤
│                   Lua subsystem                           │
│  src/nvim/lua/  (executor.c, treesitter.c, …)           │
│  runtime/lua/vim/  (lsp/, treesitter/, diagnostic, …)   │
├─────────────────────────────────────────────────────────┤
│               Core editor subsystems (C)                  │
│  buffer, window, event-loop, eval (Vimscript), TUI, …   │
├─────────────────────────────────────────────────────────┤
│              Platform abstraction (src/nvim/os/)          │
│  libuv (async I/O), filesystem, signals, processes       │
└─────────────────────────────────────────────────────────┘
```

The **event loop** (`src/nvim/event/`) wraps libuv and provides a `MultiQueue` structure that multiplexes RPC requests, job callbacks, and timer events onto a single sequential execution model. All editor state mutations happen on the main thread.

The **Lua executor** (`src/nvim/lua/executor.c`) hosts a LuaJIT (or PUC Lua) interpreter inside the process and bridges it to the C API. Lua code runs in the same process but in a cooperative (non-preemptive) model.

The **TUI** (`src/nvim/tui/`) is itself a client of the C API: it attaches as a UI and receives the same UI events that external GUIs would.

## Related Projects and Dependencies

**Core dependencies (bundled by default)**
- **libuv** — cross-platform async I/O and event loop
- **LuaJIT** (or PUC Lua 5.1 fallback) — Lua interpreter
- **luv** (`vim.uv`) — Lua bindings to libuv
- **lpeg** — Lua pattern matching library
- **tree-sitter** — incremental parsing library
- **unibilium** — terminal capability database
- **utf8proc** — Unicode processing

**Vendored sources (in `src/`)**
- `src/cjson/` — JSON library
- `src/mpack/` — msgpack library
- `src/xdiff/` — diff algorithm
- `src/klib/` — generic C data structures (kvec, khash)

**Related ecosystem projects**
- `pynvim` — Python client
- `nvim-rs` — Rust client
- `nvr` — neovim-remote CLI controller
- Numerous GUI front-ends (Neovide, FVim, Goneovim, etc.)
