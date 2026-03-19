# Neovim Code Structure

## Annotated Directory Tree

```
neovim/
├── CMakeLists.txt          # Top-level CMake build definition
├── CMakePresets.json       # Preset configurations (Debug, Release, etc.)
├── Makefile                # Convenience wrapper around CMake
├── BSDmakefile             # BSD-specific make wrapper
├── build.zig               # Experimental Zig build entry point
├── build.zig.zon           # Zig package manifest
├── README.md               # Project overview and quick-start
├── BUILD.md                # Detailed build instructions
├── INSTALL.md              # Installation guide
├── CONTRIBUTING.md         # Contributor guidelines
├── MAINTAIN.md             # Maintainer documentation
├── AGENTS.md               # AI agent guidance for contributors
├── LICENSE.txt             # Apache 2.0 license
│
├── cmake/                  # Custom CMake modules (Find*, Util, Deps, etc.)
├── cmake.config/           # CMake version/feature defines
├── cmake.deps/             # Subproject: downloads and builds all bundled deps
│   └── CMakeLists.txt      # Dependency options (USE_BUNDLED_*, versions)
├── cmake.packaging/        # CPack packaging configuration
│
├── src/                    # All C source code
│   ├── nvim/               # Main editor source (see below)
│   ├── cjson/              # Vendored JSON library
│   ├── mpack/              # Vendored msgpack library
│   ├── klib/               # Vendored generic C data structures
│   ├── xdiff/              # Vendored xdiff diff algorithm
│   ├── tee/                # Standalone tee utility (Windows)
│   ├── xxd/                # Standalone xxd hex dump utility
│   ├── gen/                # Lua code-generation scripts (pre-compilation)
│   ├── man/                # Man page source
│   └── uncrustify.cfg      # C code style configuration
│
├── runtime/                # Runtime files (loaded at startup)
│   ├── lua/vim/            # Lua standard library (vim.* namespace)
│   ├── plugin/             # Built-in opt-out plugins
│   ├── pack/dist/opt/      # Built-in opt-in plugins
│   ├── doc/                # Help documentation (.txt files)
│   ├── syntax/             # Syntax highlighting definitions
│   ├── ftplugin/           # Filetype-specific plugins
│   ├── indent/             # Indentation rules
│   ├── autoload/           # Autoloaded Vimscript functions
│   ├── colors/             # Color scheme definitions
│   ├── queries/            # Tree-sitter queries (highlights, folds, etc.)
│   ├── compiler/           # Compiler integration files
│   ├── keymap/             # Keyboard layout maps
│   ├── spell/              # Spell check data
│   └── tutor/              # Interactive tutorial
│
├── test/                   # Test suite
│   ├── functional/         # End-to-end functional tests (busted)
│   ├── unit/               # C unit tests
│   ├── old/                # Legacy Vim test suite
│   ├── benchmark/          # Performance benchmarks
│   ├── busted/             # Busted test framework customization
│   └── testutil.lua        # Shared test utilities
│
├── contrib/                # Contribution helpers (syntax files, etc.)
├── deps/                   # Source for bundled dependencies (fetched at build)
└── scripts/                # Maintenance and CI scripts
```

## Main Source Directory: `src/nvim/`

The editor's C code is organized into subsystem directories plus a flat collection of modules at the top level.

### Top-level modules (selected key files)

| File | Purpose |
|------|---------|
| `main.c` | Program entry point; initializes subsystems and enters the event loop |
| `version.c` | Version information; forked from Vim 7.4.160 |
| `buffer.c` / `buffer.h` | Buffer management (open, close, read, write) |
| `window.c` / `window.h` | Window and split management |
| `normal.c` | Normal mode key handling (largest single file) |
| `edit.c` | Insert mode implementation |
| `ex_docmd.c` | Ex command dispatch (`:`-commands) |
| `ex_cmds.c` | Individual Ex command implementations |
| `eval.c` | Vimscript expression evaluator |
| `autocmd.c` | Autocommand (event) system |
| `channel.c` | I/O channel management (jobs, RPC, terminal) |
| `terminal.c` | Built-in terminal emulator |
| `ui.c` / `ui_compositor.c` | UI abstraction and compositor |
| `drawscreen.c` / `drawline.c` | Screen rendering |
| `highlight.c` / `highlight_group.c` | Highlight groups and attributes |
| `extmark.c` | Extmarks (virtual text, decorations, annotations) |
| `decoration.c` | Decoration provider system |
| `diff.c` | Built-in diff subsystem |
| `fold.c` | Code folding |
| `search.c` | Pattern search (including regex) |
| `regexp.c` | Regular expression engine |
| `spell.c` / `spellfile.c` | Spell checking |
| `syntax.c` | Legacy syntax highlighting |
| `quickfix.c` | Quickfix and location list |
| `memline.c` | Buffer text storage (B-tree of line segments) |
| `memfile.c` | Memory-mapped file for undo/redo |
| `undo.c` | Undo tree implementation |
| `shada.c` | ShaDa (shared data) file read/write |
| `mark.c` / `marktree.c` | Marks and the mark interval tree |
| `mapping.c` | Key mapping system |
| `keycodes.c` | Key name/code translation |
| `option.c` / `optionstr.c` | Options system |
| `getchar.c` | Key input handling |
| `message.c` | Message display and history |
| `log.c` | Internal logging |
| `memory.c` | Memory allocation wrappers |
| `path.c` | Path manipulation utilities |
| `charset.c` | Character encoding utilities |
| `mbyte.c` | Multibyte/Unicode support |
| `strings.c` | String utilities |
| `fuzzy.c` | Fuzzy matching (used in completion) |
| `linematch.c` | Line-based diff matching algorithm |
| `clipboard.c` | System clipboard integration |
| `context.c` | Context save/restore (for `:wshada`, etc.) |
| `profile.c` | Script profiling |
| `sha256.c` | SHA-256 implementation |

### Subsystem Directories in `src/nvim/`

#### `api/` — Public C API
- `vim.c` — Global API functions (`nvim_exec_lua`, `nvim_command`, `nvim_eval`, etc.)
- `buffer.c` — Buffer API (`nvim_buf_get_lines`, `nvim_buf_set_lines`, etc.)
- `window.c` — Window API (`nvim_win_get_cursor`, `nvim_win_set_buf`, etc.)
- `tabpage.c` — Tabpage API
- `autocmd.c` — Autocmd API (`nvim_create_autocmd`, `nvim_exec_autocmds`)
- `extmark.c` — Extmark API (`nvim_buf_set_extmark`, `nvim_buf_get_extmarks`)
- `command.c` — Command API (`nvim_create_user_command`)
- `options.c` — Options API (`nvim_get_option_value`, `nvim_set_option_value`)
- `ui.c` — UI attachment API (`nvim_ui_attach`, `nvim_ui_detach`)
- `vimscript.c` — Vimscript execution API
- `win_config.c` — Floating window configuration API
- `ui_events.in.h` — UI event definitions (parsed by code generator)
- `private/` — Internal API helpers (defs, dispatch, converter, helpers, validate)

#### `eval/` — Vimscript evaluator
- `typval.c` — Type value (typval_T) operations
- `userfunc.c` — User-defined Vimscript functions
- `vars.c` — Variable management (g:, b:, w:, t:, s:, l:, v:)
- `funcs.c` — Built-in Vimscript function implementations
- `buffer.c`, `window.c` — Vimscript buffer/window functions
- `encode.c` — Encoding utilities (JSON, msgpack)

#### `event/` — Async event loop
- `loop.c` / `loop.h` — Main `Loop` struct wrapping libuv + MultiQueue
- `multiqueue.c` — Multi-level event queue (main, thread, fast)
- `stream.c` / `rstream.c` / `wstream.c` — Stream I/O abstractions
- `proc.c` / `libuv_proc.c` — Process management
- `socket.c` — Unix/TCP socket support
- `signal.c` — Signal handling
- `time.c` — Timer support

#### `lua/` — Lua/C bridge
- `executor.c` / `executor.h` — Main Lua executor; runs Lua code in the editor
- `treesitter.c` — Tree-sitter bindings for Lua
- `stdlib.c` — Lua standard library extensions
- `converter.c` — C↔Lua type conversion
- `secure.c` — Secure execution checks
- `base64.c`, `xdiff.c`, `spell.c` — Feature-specific Lua bindings

#### `tui/` — Built-in terminal UI
- `tui.c` — TUI implementation (attaches as a UI client)
- `input.c` — Terminal keyboard input processing
- `terminfo.c` — Terminal capability lookup
- `termkey/` — Forked termkey library for key parsing
- `vterm/` — Forked vterm library for terminal emulation

#### `os/` — Platform abstraction
- `fs.c` — Filesystem operations
- `env.c` — Environment variables
- `proc.c` — Process utilities
- `shell.c` — Shell invocation
- `signal.c` — Signal handling
- `input.c` — OS-level input
- `time.c` — Timing utilities
- `stdpaths.c` — XDG standard paths
- `pty_proc_unix.c` / `pty_proc_win.c` — PTY process management

#### `msgpack_rpc/` — RPC subsystem
- `channel.c` — RPC channel management
- `server.c` — Server socket creation
- `packer.c` / `unpacker.c` — msgpack serialization

#### `lib/` — Generic data structures
- Queue (intrusive linked list), sorted array, etc.

### `runtime/lua/vim/` — Lua Standard Library

```
runtime/lua/vim/
├── _core/                  # Eager-loaded, always available
│   ├── shared.lua          # Pure Lua utilities (usable in worker threads)
│   ├── editor.lua          # Core editor integration
│   ├── defaults.lua        # Default options and mappings
│   ├── options.lua         # Option wrappers
│   ├── util.lua            # Utility functions
│   └── …
├── lsp/                    # LSP client implementation
│   ├── client.lua          # LSP client class
│   ├── buf.lua             # Buffer-level LSP actions
│   ├── handlers.lua        # Default LSP response handlers
│   ├── protocol.lua        # LSP protocol constants
│   ├── util.lua            # LSP utilities
│   ├── diagnostic.lua      # LSP→diagnostic integration
│   ├── completion.lua      # Completion integration
│   ├── inlay_hint.lua      # Inlay hints
│   ├── semantic_tokens.lua # Semantic token highlighting
│   └── …
├── treesitter/             # Tree-sitter integration
│   ├── languagetree.lua    # Language tree (injections, parsers)
│   ├── highlighter.lua     # Syntax highlighting
│   ├── query.lua           # Query parsing and matching
│   └── …
├── diagnostic.lua          # Diagnostic framework
├── keymap.lua              # Key mapping utilities
├── fs.lua                  # Filesystem utilities
├── iter.lua                # Iterator utilities
├── health.lua              # Health check framework
├── snippet.lua             # Snippet expansion
├── text.lua                # Text manipulation
├── func.lua                # Function utilities
├── glob.lua                # Glob pattern matching
├── net.lua                 # Network utilities
├── secure.lua              # Secure execution
├── re.lua                  # Regex utilities
└── …
```

### Code Generation Patterns

The build system auto-generates several C files from Lua definition files:

| Lua source | Generated output | Content |
|------------|-----------------|---------|
| `src/nvim/auevents.lua` | `auevents.generated.h` | Autocmd event enum and names |
| `src/nvim/ex_cmds.lua` | `ex_cmds.generated.h` | Ex command table |
| `src/nvim/options.lua` | `options.generated.h` | Option definitions |
| `src/nvim/eval.lua` | `funcs.generated.h` | Built-in function table |
| `src/nvim/vvars.lua` | `vvars.generated.h` | `v:` variable definitions |
| `src/nvim/api/ui_events.in.h` | UI event wrappers | msgpack-RPC UI event dispatch |

Generated file naming conventions:
- `*.generated.c` — full generated C translation unit
- `*.c.generated.h` — static function declarations
- `*.h.generated.h` — exported function declarations
- `*.c.h` — parameterized C files (require macro defines before inclusion)
