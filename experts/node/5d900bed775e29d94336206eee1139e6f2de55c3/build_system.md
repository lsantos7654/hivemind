# Node.js — Build System

## Build System Type

Node.js uses **GYP** (Generate Your Projects) as its primary meta-build system, coordinated by `configure.py` and `Makefile` (Unix/macOS) or `vcbuild.bat` (Windows). An experimental **GN** build (`BUILD.gn`, `node.gni`) is also present but not the primary path.

Key build files:
- `node.gyp` — Primary GYP project file defining all build targets, source lists, and feature flags.
- `node.gypi` / `common.gypi` — Shared GYP variables and compiler flags.
- `configure` / `configure.py` — Python-based configuration script that detects platform, compiler, and optional features, then invokes GYP to generate platform-native build files (Makefiles on Unix, MSVC project files on Windows).
- `Makefile` — Unix/macOS top-level orchestration; wraps `./configure` + `make -C out`.
- `vcbuild.bat` — Windows build entry point, supports Visual Studio and LLVM toolchains.
- `pyproject.toml` — Python tool dependencies (used by build scripts).

## External Dependencies and Management

All major C/C++ dependencies are **vendored** in `deps/` and built from source as part of the Node.js build. There is no runtime package manager for C++ dependencies.

| Dependency | Location | Purpose |
|------------|----------|---------|
| V8 | `deps/v8/` | JavaScript engine |
| libuv | `deps/uv/` | Async I/O, event loop |
| OpenSSL | `deps/openssl/` | TLS, crypto (can use system OpenSSL via `--shared-openssl`) |
| npm | `deps/npm/` | Bundled package manager |
| undici | `deps/undici/` | HTTP client (fetch API) |
| llhttp | `deps/llhttp/` | HTTP/1.x parser |
| nghttp2 | `deps/nghttp2/` | HTTP/2 |
| ngtcp2 | `deps/ngtcp2/` | QUIC/HTTP3 |
| c-ares | `deps/cares/` | Async DNS |
| SQLite | `deps/sqlite/` | Embedded database |
| amaro | `deps/amaro/` | TypeScript type-stripping (SWC) |
| ada | `deps/ada/` | WHATWG URL parser |
| simdjson | `deps/simdjson/` | Fast JSON parsing |
| zlib | `deps/zlib/` | Deflate/gzip |
| brotli | `deps/brotli/` | Brotli compression |
| zstd | `deps/zstd/` | Zstandard compression |
| googletest | `deps/googletest/` | C++ unit testing |
| postject | `deps/postject/` | SEA resource injection |
| LIEF | `deps/LIEF/` | Binary analysis for SEA |
| icu-small | `deps/icu-small/` | ICU internationalization data (small/trimmed) |
| histogram | `deps/histogram/` | HDR histogram |
| nbytes | `deps/nbytes/` | Safe byte counting |
| ncrypto | `deps/ncrypto/` | Crypto helper library |
| uvwasi | `deps/uvwasi/` | WASI implementation |
| merve | `deps/merve/` | Additional utility library |
| minimatch | `deps/minimatch/` | Glob matching |
| corepack | `deps/corepack/` | Package manager proxy |

Many deps support system-provided alternatives via `--shared-<dep>` configure flags (e.g., `--shared-openssl`, `--shared-zlib`, `--shared-libuv`).

JavaScript/Node.js tooling dependencies (ESLint, doc generators, etc.) live under `tools/` and are separate from the runtime build.

## Build Targets and Commands

### Unix / macOS

**Configure and build:**
```sh
# Minimum: configure + build
./configure
make -j4

# With options
./configure --debug           # Debug build (outputs to out/Debug/)
./configure --shared-openssl  # Use system OpenSSL
./configure --with-intl=full-icu  # Full ICU locale support
./configure --enable-quic     # Enable QUIC module
make -j$(nproc)
```

**Install:**
```sh
make install                  # Install to /usr/local (default PREFIX)
make install PREFIX=/opt/node # Custom install prefix
```

**Run tests:**
```sh
make test                     # All tests + docs lint
make test-only                # All tests without docs
make jstest                   # JavaScript tests + addon tests
make cctest                   # C++ unit tests
make test-ci                  # Full CI test suite
make test-wpt                 # Web Platform Tests
```

**Linting:**
```sh
make lint                     # JS + C++ + Markdown lint
make lint-js                  # ESLint only
make lint-cpp                 # cpplint + checkimports
make lint-md                  # Markdown lint
make format-cpp               # Format C++ changes with clang-format
make lint-js-fix              # Auto-fix JS lint issues
```

**Coverage:**
```sh
make coverage                 # Build + test + generate report
```

**Documentation:**
```sh
make doc                      # Build HTML documentation
```

**Benchmarks:**
```sh
make bench-addons-build       # Build benchmark addons
node benchmark/run.js <category>
```

**Releases:**
```sh
make release-only             # Prepare for release
make binary                   # Build release binary tarball
make pkg                      # Build macOS installer
make tar                      # Source tarball
```

**Miscellaneous:**
```sh
make clean                    # Remove build artifacts
make distclean                # Remove all build + test artifacts
make help                     # List all targets with descriptions
```

### Windows

```bat
vcbuild                      # Basic build (Release)
vcbuild debug                # Debug build
vcbuild test                 # Build + run tests
vcbuild release nosign       # Release build without signing
vcbuild /help                # Show all options
```

### Makefile Variables

```sh
BUILDTYPE=Debug   # or Release (default)
PREFIX=/usr/local # Install prefix
V=1               # Verbose build output
```

## Build Configuration Options (./configure flags)

```sh
--debug                         # Build Debug configuration
--release                       # Build Release (default)
--shared                        # Build as shared library (libnode.so)
--shared-openssl                # Use system OpenSSL
--shared-zlib                   # Use system zlib
--shared-cares                  # Use system c-ares
--shared-libuv                  # Use system libuv
--shared-nghttp2                # Use system nghttp2
--shared-sqlite                 # Use system SQLite
--with-intl=<mode>              # ICU intl: none | small-icu | full-icu | system-icu
--without-ssl                   # Disable OpenSSL
--enable-fips                   # Enable FIPS-compliant OpenSSL
--enable-quic                   # Enable QUIC module
--without-node-snapshot         # Disable startup snapshot
--without-node-code-cache       # Disable built-in code cache
--cross-compiling               # Cross-compile
--dest-cpu=<arch>               # Target CPU (arm, arm64, x64, etc.)
--dest-os=<os>                  # Target OS
--openssl-fips=<path>           # FIPS OpenSSL module path
--node-builtin-modules-path=<p> # Load JS builtins from disk (for development)
--verbose                       # Verbose configure output
```

## How to Build (Quick Start)

### macOS/Linux (typical development build):
```sh
git clone https://github.com/nodejs/node.git
cd node
./configure
make -j4
./node --version  # Verify: v26.0.0-pre
```

### Development iteration (faster rebuilds):
- Use `--node-builtin-modules-path=$(pwd)/lib` so JS files are loaded from disk without relinking.
- Use **ccache** (`export CC="ccache cc"`, `export CXX="ccache c++"`) to cache C++ compilation.
- Only rebuild with `make -j$(nproc)` after C++ changes; JS changes don't require a rebuild with the above flag.

### Running a single test:
```sh
./node test/parallel/test-fs-readfile.js
```

### Running the test suite with a filter:
```sh
make jstest PARALLEL_ARGS="-J --test-dirname parallel/test-fs*"
```

## Continuous Integration

CI is driven by `make test-ci` which executes:
1. `build-ci` — Full build
2. Addon builds (`build-addons`, `build-js-native-api-tests`, `build-node-api-tests`, `build-sqlite-tests`)
3. `jstest` — All JavaScript tests
4. `cctest` — C++ tests
5. Linting

CI config is located in `.github/` (GitHub Actions workflows) and `tools/actions/`.
