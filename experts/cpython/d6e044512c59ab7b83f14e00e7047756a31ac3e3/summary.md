# CPython Repository Summary

## Repository Purpose and Goals

CPython is the reference implementation of the Python programming language, maintained by the Python Software Foundation (PSF). This repository contains the complete source code for Python 3.15.0 alpha 7, the authoritative interpreter used by the vast majority of Python users worldwide.

The primary goals of CPython are:
- Serve as the canonical Python language implementation, defining correct behavior by example
- Provide a stable, high-performance interpreter for production use
- Expose a well-defined C API for embedding Python and writing C extension modules
- Ship a comprehensive standard library ("batteries included" philosophy)
- Support multiple platforms: Unix/Linux, macOS, Windows, iOS, Android, Emscripten/WASM

## Key Features and Capabilities

**Language Runtime:**
- Full Python 3.x language implementation including the latest syntax features
- Reference-counting garbage collector supplemented by a cyclic garbage collector
- A GIL (Global Interpreter Lock) build and an experimental free-threaded (no-GIL) build (`Py_GIL_DISABLED`)
- Sub-interpreter support with per-interpreter state isolation
- Lazy imports support (`PyImport_SetLazyImportsMode`)

**Performance Infrastructure:**
- Adaptive specializing interpreter ("tier 1"): bytecode instructions are monitored at runtime and replaced with specialized variants for common type patterns
- Experimental copy-and-patch JIT compiler ("tier 2"): traces of hot bytecode sequences are compiled to native machine code via LLVM-based stencils (`Tools/jit/`, `Python/jit.c`)
- Profile-Guided Optimization (PGO) and Link-Time Optimization (LTO) build modes

**C Extension API:**
- Stable ABI / Limited API (`Py_LIMITED_API`) for binary-compatible extensions across Python versions
- Full CPython-private API for performance-critical or implementation-specific extensions
- Argument Clinic (`Tools/clinic/`) for auto-generating argument parsing boilerplate
- `PyModuleDef`-based multi-phase module initialization (PEP 489)

**Standard Library:**
- 200+ modules covering networking, file I/O, cryptography, compression, databases, concurrency, testing, and more
- Pure-Python fallback implementations for many C-accelerated modules (e.g., `_pyio.py`, `_pydatetime.py`)
- `asyncio` for cooperative multitasking
- `unittest`, `doctest`, and a `test` package with thousands of regression tests

## Primary Use Cases and Target Audience

- **Application developers**: Build web services, data pipelines, automation scripts, and desktop applications using Python
- **Library/framework authors**: Write high-performance C extensions or pure-Python libraries distributed via PyPI
- **Embedders**: Embed the Python interpreter inside a C/C++ application using the embedding API (`Py_Initialize`, `PyConfig`, `PyRun_*`)
- **Language implementors and contributors**: Extend or modify the Python language itself — grammar, compiler, bytecodes, standard library
- **Platform porters**: Add or maintain Python support on new operating systems or architectures

## High-Level Architecture Overview

CPython's execution pipeline flows through several layers:

1. **Source text → Tokens** (`Parser/tokenizer/`): The tokenizer produces a token stream from UTF-8 source text.
2. **Tokens → Concrete Syntax Tree** (`Parser/pegen.c`, `Grammar/python.gram`): A PEG parser (generated from the grammar) produces a CST.
3. **CST → Abstract Syntax Tree** (`Python/ast.c`, `Parser/Python.asdl`): The AST is defined by the ASDL schema and constructed from the CST.
4. **AST → Bytecode** (`Python/compile.c`, `Python/codegen.c`, `Python/assemble.c`): The compiler lowers the AST to a `PyCodeObject` containing bytecode instructions and metadata.
5. **Bytecode → Execution** (`Python/ceval.c`, `Python/bytecodes.c`): The adaptive interpreter executes bytecode in a frame-based virtual machine. Hot loops can be JIT-compiled (`Python/optimizer.c`, `Python/jit.c`).

The runtime state is organized hierarchically:
- `PyRuntime` (`Include/internal/pycore_runtime.h`): process-global singleton
- `PyInterpreterState` (`Include/internal/pycore_interp.h`): per-interpreter state (multiple interpreters per process)
- `PyThreadState` (`Include/cpython/pystate.h`): per-thread state (multiple threads per interpreter)
- `_PyInterpreterFrame` (`Include/internal/pycore_frame.h`): per-function-call execution frame

## Related Projects and Dependencies

- **Python Package Index (PyPI)**: Distribution channel for third-party packages
- **pip**: The standard package installer (not in this repo; ships with CPython as `ensurepip`)
- **LLVM/Clang**: Required for JIT compilation (`--enable-experimental-jit` configure flag)
- **OpenSSL/LibreSSL**: Required for `ssl` and `hashlib` modules
- **SQLite**: Required for the `sqlite3` module
- **zlib, bz2, lzma, zstd**: Compression library dependencies
- **libffi**: Required for the `ctypes` module
- **Tcl/Tk**: Required for the `tkinter` module
- **autoconf 2.72 + autoconf-archive**: Required to regenerate the `configure` script
- **MicroPython, PyPy, Jython, GraalPy**: Alternative Python implementations that conform to the language spec but do not share this codebase
