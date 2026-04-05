# CPython Build System

## Build System Type

CPython uses a **classic Autoconf + Make** build system on Unix-like platforms and **MSBuild** on Windows.

Key configuration files:
- `configure.ac` — Autoconf source (requires autoconf 2.72, autoconf-archive, aclocal 1.16, pkg-config)
- `configure` — Generated shell script (regenerate with `Tools/build/regen-configure.sh` or `autoreconf -ivf -Werror`)
- `Makefile.pre.in` — Makefile template; filled in by `configure` to produce `Makefile`
- `pyconfig.h.in` — C configuration header template; filled in by `configure` to produce `pyconfig.h`
- `aclocal.m4` — Custom autoconf macros
- `Modules/makesetup` — Script that processes `Modules/Setup` to decide which extension modules to build statically vs. dynamically vs. skip

## External Dependencies

| Dependency | Module(s) | Required? |
|---|---|---|
| OpenSSL / LibreSSL | `ssl`, `hashlib` (OpenSSL backend) | Optional but recommended |
| SQLite ≥ 3.15.2 | `sqlite3` | Optional |
| libffi | `ctypes` | Optional (bundled fallback for some platforms) |
| zlib | `zlib`, `zipfile`, `gzip` | Optional |
| libbz2 | `bz2` | Optional |
| liblzma | `lzma` | Optional |
| libzstd | `compression.zstd` | Optional |
| Tcl/Tk | `tkinter` | Optional |
| readline / libedit | Interactive REPL line editing | Optional |
| LLVM/Clang | JIT compiler (`--enable-experimental-jit`) | Optional |
| libexpat | `xml.parsers.expat`, `xml.etree` | Bundled in `Modules/_expat/` |
| libmpdec | `decimal` C extension | Bundled in `Modules/_decimal/libmpdec/` |
| HACL* crypto | `hashlib` pure-C implementations | Bundled in `Modules/_hacl/` |
| mimalloc | Memory allocator | Bundled in `Objects/mimalloc/` |

Run `./configure --help` to see all optional feature flags.

## Key Configure Options

```sh
# Debug build (enables assertions, reference debug)
./configure --with-pydebug

# Optimized build (PGO + LTO)
./configure --enable-optimizations

# Free-threaded build (no GIL, experimental)
./configure --disable-gil

# Experimental copy-and-patch JIT
./configure --enable-experimental-jit

# Build with specific Python prefix
./configure --prefix=/opt/python3.15

# Stable ABI (limited C API) check
./configure --with-stable-abi

# Enable DTrace probes
./configure --with-dtrace

# Address sanitizer build
./configure --with-address-sanitizer

# Build shared library (libpython)
./configure --enable-shared
```

## Build Targets

### Primary build targets (in `Makefile.pre.in`):

```sh
# Build the interpreter (default)
make

# Run the full test suite
make test

# Run tests with verbose output
make testall

# Install (requires sudo if prefix requires it)
sudo make install

# Install without overwriting existing python3 symlink
sudo make altinstall

# Build documentation (requires Sphinx)
make -C Doc/ html

# Clean build artifacts
make clean

# Deep clean (remove configure outputs too)
make distclean
```

### Code generation targets (regenerate generated C files):

```sh
# Regenerate all generated files
make regen-all

# Regenerate bytecode interpreter dispatch cases
# Source: Python/bytecodes.c → Python/generated_cases.c.h
make regen-cases

# Regenerate JIT executor cases
make regen-executor-cases

# Regenerate optimizer micro-op cases
make regen-optimizer-cases

# Regenerate opcode IDs header
make regen-opcode-ids

# Regenerate opcode metadata Python module
make regen-opcode-metadata-py

# Regenerate PEG parser from Grammar/python.gram
make regen-pegen

# Regenerate AST C code from Parser/Python.asdl
make regen-ast

# Regenerate frozen stdlib modules (importlib bootstrap)
make regen-frozen

# Regenerate Argument Clinic files
make clinic

# Regenerate token definitions
make regen-token
```

### Optimization / PGO / LTO targets:

```sh
# Profile-Guided Optimization build (3-step: instrument, profile, optimize)
make profile-opt

# Build with LLVM BOLT (feedback-directed reordering, requires llvm-bolt)
make profile-bolt-stamp

# Coverage build
make coverage
```

### Testing targets:

```sh
# Quick smoke test
make quicktest

# Test a single module
make test TESTOPTS="-v test_ast"

# Test with multiple processes
make test TESTOPTS="-j4"

# Clinic-specific tests
make clinic-tests

# Run the embedding tests
./Programs/_testembed
```

## How to Build

### Unix/Linux/macOS standard build:

```sh
git clone https://github.com/python/cpython.git
cd cpython
./configure
make -j$(nproc)
make test
sudo make install
```

### Debug build (for development):

```sh
mkdir debug && cd debug
../configure --with-pydebug
make -j$(nproc)
./python -m test -j4
```

### Free-threaded (no-GIL) build:

```sh
./configure --disable-gil
make -j$(nproc)
# Produces python3.15t (note the 't' suffix)
./python3.15t -c "import sys; print(sys._is_gil_enabled())"
```

### JIT-enabled build (requires LLVM ≥ 16):

```sh
./configure --enable-experimental-jit
make -j$(nproc)
```

### Windows build:

```
PCbuild\build.bat -e -d    # debug build with external deps
PCbuild\build.bat -e       # release build with external deps
PCbuild\PCbuild.sln        # open in Visual Studio
```

## Module Build System

Extension modules are configured via `Modules/Setup` (and platform-specific `Modules/Setup.*.in` files). The `Modules/makesetup` script processes these to determine:
- Statically linked modules (compiled into the interpreter)
- Dynamically linked modules (`.so`/`.pyd` files)
- Disabled modules

Modules not in `Modules/Setup` are auto-detected by `configure` through feature tests.

## Source Code Regeneration Workflow

When modifying grammar, opcodes, or AST node types:

1. **Grammar changes** (`Grammar/python.gram`): Run `make regen-pegen` to regenerate `Parser/parser.c`
2. **AST changes** (`Parser/Python.asdl`): Run `make regen-ast` to regenerate `Python/Python-ast.c` and `Include/internal/pycore_ast.h`
3. **Opcode/bytecode changes** (`Python/bytecodes.c`): Run `make regen-cases` → regenerates `Python/generated_cases.c.h`, `Python/executor_cases.c.h`, `Include/opcode_ids.h`, `Lib/_opcode_metadata.py`
4. **Argument Clinic** (`*.clinic` files): Run `make clinic` to regenerate `clinic/*.c.h` files

The `Tools/cases_generator/` directory contains the bytecode DSL processor. The `Tools/peg_generator/` directory contains the PEG parser generator.
