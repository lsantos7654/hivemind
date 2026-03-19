# Neovim Build System

## Build System Type

Neovim uses **CMake** as its primary build system (minimum version 3.16), with a convenience `Makefile` wrapper. An experimental **Zig** build (`build.zig` / `build.zig.zon`) is also present but not the primary path.

### Key Configuration Files

| File | Purpose |
|------|---------|
| `CMakeLists.txt` | Top-level CMake project |
| `CMakePresets.json` | Named presets (Debug, Release, RelWithDebInfo, etc.) |
| `Makefile` | Convenience wrapper; delegates to CMake |
| `BSDmakefile` | BSD-specific make wrapper (use `gmake` on BSD) |
| `cmake/` | Custom CMake modules: `Deps.cmake`, `Find.cmake`, `Util.cmake`, `InstallHelpers.cmake` |
| `cmake.config/` | Version/feature defines passed to the compiler |
| `cmake.deps/CMakeLists.txt` | Separate subproject that downloads and builds all bundled dependencies |
| `cmake.packaging/` | CPack packaging rules (DEB, RPM, etc.) |

## External Dependencies

### Core Dependencies (Bundled by Default via `cmake.deps/`)

All are controlled by `USE_BUNDLED=ON` (default). Each has an individual `USE_BUNDLED_<NAME>` option.

| Dependency | CMake Option | Purpose |
|------------|-------------|---------|
| **libuv** | `USE_BUNDLED_LIBUV` | Async I/O, event loop, sockets, processes |
| **LuaJIT** | `USE_BUNDLED_LUAJIT` | Primary Lua interpreter (JIT-compiled) |
| **PUC Lua** | `USE_BUNDLED_LUA` | Fallback Lua interpreter (tests only unless `PREFER_LUA=ON`) |
| **luv** | `USE_BUNDLED_LUV` | Lua bindings to libuv (`vim.uv`) |
| **lpeg** | `USE_BUNDLED_LPEG` | Lua pattern matching library |
| **tree-sitter** | `USE_BUNDLED_TS` | Incremental parsing library |
| **tree-sitter parsers** | `USE_BUNDLED_TS_PARSERS` | Bundled grammars (C, Lua, Vim, etc.) |
| **unibilium** | `USE_BUNDLED_UNIBILIUM` | Terminal capability database |
| **utf8proc** | `USE_BUNDLED_UTF8PROC` | Unicode text processing |
| **gettext** | `USE_BUNDLED_GETTEXT` | Internationalization (Windows only by default) |
| **libiconv** | `USE_BUNDLED_LIBICONV` | Character encoding conversion (Windows only by default) |
| **wasmtime** | `USE_BUNDLED_WASMTIME` | WebAssembly runtime for tree-sitter (optional, off by default) |

Bundled sources are downloaded to `.deps/` at build time and statically linked.

### Vendored Sources (Always Included, in `src/`)

These are directly compiled into the Neovim binary:

| Directory | Purpose |
|-----------|---------|
| `src/cjson/` | JSON library |
| `src/mpack/` | MessagePack library |
| `src/klib/` | Generic C data structures (kvec, khash — header-only) |
| `src/xdiff/` | Myers diff algorithm |

## Build Targets and Commands

### Quick Start

```bash
# Clone
git clone https://github.com/neovim/neovim
cd neovim

# Build (RelWithDebInfo is recommended for development)
make CMAKE_BUILD_TYPE=RelWithDebInfo

# Install (default prefix: /usr/local)
sudo make install

# Install to a custom prefix
make CMAKE_BUILD_TYPE=RelWithDebInfo CMAKE_INSTALL_PREFIX=$HOME/.local
make install
```

### Build Types

| Type | Optimizations | Debug Info | Use Case |
|------|---------------|------------|----------|
| `Debug` | Minimal | Full | Development/debugging (default if unspecified) |
| `Release` | Full | None | Packaging/distribution |
| `RelWithDebInfo` | Many | Enough for backtraces | Recommended for contributors |

### Common Make Targets

```bash
make                           # Build nvim (downloads deps automatically)
make install                   # Install to CMAKE_INSTALL_PREFIX
make deps                      # Build bundled dependencies only
make distclean                 # Remove build/ and .deps/
make CMAKE_BUILD_TYPE=Release  # Build in Release mode

# Run after build without installing:
VIMRUNTIME=runtime ./build/bin/nvim
```

### CMake Direct Usage

```bash
# Configure
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo

# Build (with Ninja for parallelism)
cmake --build build

# List all build targets
cmake --build build --target help

# Inspect resolved variables
cmake -LAH build/

# View compile commands
cat build/compile_commands.json
```

### CMake Build Options

```bash
# Use PUC Lua instead of LuaJIT
make CMAKE_EXTRA_FLAGS="-DPREFER_LUA=ON" \
     DEPS_CMAKE_FLAGS="-DUSE_BUNDLED_LUAJIT=OFF -DUSE_BUNDLED_LUA=ON"

# Enable wasmtime for tree-sitter WASM grammars
cmake -B build -DENABLE_WASMTIME=ON

# Disable ccache (used by default if installed)
CCACHE_DISABLE=true make

# Verbose build
cmake --build build --verbose

# Build Debian package
cd build && cpack -G DEB && sudo dpkg -i nvim-linux-x86_64.deb
```

## Running Tests

### Test Framework

Tests use the **busted** Lua testing framework. Functional tests drive a real Neovim instance.

```bash
# All tests
make test

# Functional tests only
make functionaltest

# Unit tests only
make unittest

# Old Vim-style tests
make oldtest

# Run a specific test file
TEST_FILE=test/functional/api/vim_spec.lua make functionaltest

# Filtered by test name
TEST_FILTER="some test name" make functionaltest
```

### Test Organization

```
test/
├── functional/     # End-to-end tests (spawn real nvim instances)
│   ├── api/        # C API tests
│   ├── lua/        # Lua stdlib tests
│   ├── plugin/     # Built-in plugin tests
│   ├── ui/         # UI rendering tests
│   └── …
├── unit/           # C unit tests (compiled, no full nvim needed)
├── old/            # Ported Vim test suite (vimscript-based)
└── benchmark/      # Performance benchmarks
```

## Code Generation

The build system runs several Lua code-generators during compilation. These are invoked by CMake before the C compilation phase:

| Generator | Input | Output |
|-----------|-------|--------|
| `src/gen/gen_api_dispatch.lua` | `src/nvim/api/*.h` | API dispatch tables and metadata |
| `src/gen/gen_api_ui_events.lua` | `src/nvim/api/ui_events.in.h` | UI event wrappers |
| `src/gen/gen_events.lua` | `src/nvim/auevents.lua` | Autocmd event enum |
| `src/gen/gen_ex_cmds.lua` | `src/nvim/ex_cmds.lua` | Ex command table |
| `src/gen/gen_options.lua` | `src/nvim/options.lua` | Options table |
| `src/gen/gen_eval.lua` | `src/nvim/eval.lua` | Built-in function table |

Always run `make distclean` (or `rm -rf build`) when:
- Changing `CMAKE_BUILD_TYPE` or `CMAKE_INSTALL_PREFIX`
- After a Git commit that adds or removes files (including in `runtime/`)
- When switching between LuaJIT and PUC Lua

## Platform Notes

- **Linux/macOS**: GCC or Clang; Ninja is strongly recommended for faster builds
- **BSD**: Use `gmake` instead of `make`
- **Windows**: MSVC (Visual Studio 2017+) with C++ Desktop Development workload is recommended; MinGW also works
- **ccache**: Automatically used if installed; speeds up incremental rebuilds significantly
- **Minimum CMake**: 3.16

## Dependency Management

When `USE_BUNDLED=ON` (default), CMake downloads dependency sources to `.deps/` and builds them as `ExternalProject`s. The final Neovim binary statically links these libraries, making it fully self-contained on most platforms.

To build dependencies separately (useful for debugging them):
```bash
make distclean
make deps   # Only builds .deps/, not nvim itself
make        # Then build nvim
```
