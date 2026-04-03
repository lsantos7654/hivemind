# Mypy: Static Type Checker for Python

## Repository Purpose and Goals

Mypy is the canonical optional static type checker for Python. Its primary purpose is to verify Python programs using type annotations (as specified in PEP 484, PEP 526, and related PEPs) without running the code. The project is maintained under the `python` GitHub organization and is tightly integrated with CPython's typing ecosystem.

The core goals of mypy are:
- Find bugs in Python programs through static analysis before they manifest at runtime
- Support gradual typing, allowing type annotations to be adopted incrementally
- Remain fully compatible with Python's runtime: type annotations do not affect program execution
- Provide excellent integration with IDEs, CI pipelines, and developer tooling

## Key Features and Capabilities

**Type Checking Engine**
- Full support for PEP 484 type annotations and all subsequent typing PEPs (526, 544, 586, 589, 591, 612, 613, 646, 655, 673, 675, etc.)
- Type inference: variables without annotations get inferred types from assignments
- Generics support with TypeVar, ParamSpec, TypeVarTuple, and Unpack
- Structural subtyping via Protocol (PEP 544)
- TypedDict, NamedTuple, and Enum type checking
- Overloaded functions via @overload
- Literal types, Final, ClassVar
- Pattern matching (match/case) type narrowing

**Incremental and Daemon Mode**
- Incremental checking: only re-checks files that changed and their dependents
- `dmypy` (daemon mypy): long-running process that keeps module state in memory for sub-second re-checks on large codebases
- Fine-grained incremental mode tracks dependencies at the symbol level

**Stub Generation and Testing**
- `stubgen`: generates `.pyi` stub files from Python source or C extension modules
- `stubtest`: verifies that stub files are consistent with the actual runtime behavior of a library
- Bundled typeshed: includes the complete typeshed (stubs for the standard library and popular third-party packages)

**Plugin System**
- Extensible via plugins that can customize type inference for specific libraries or patterns
- Built-in plugins for: attrs, dataclasses, ctypes, enum, functools, singledispatch
- Plugins can hook into semantic analysis and type checking phases

**Mypyc — Python-to-C Compiler**
- `mypyc` compiles mypy-annotated Python code to C extensions using the CPython C API
- Compiled code runs 2–10x faster than interpreted Python
- Mypy itself is compiled with mypyc for distribution

**Configuration Flexibility**
- Supports `mypy.ini`, `setup.cfg`, `tox.ini`, and `pyproject.toml` configuration
- Per-module configuration overrides for granular control
- Wide variety of strictness options from lenient to strict mode

## Primary Use Cases and Target Audience

- **Application developers** adding type checking to Python codebases, from small scripts to large monorepos
- **Library authors** ensuring APIs are correctly typed and stubs are accurate
- **CI/CD pipelines** catching type errors before code is merged or deployed
- **IDE tooling** (via Language Server Protocol) for in-editor type information
- **Performance-critical Python** using mypyc to compile annotated code to C

## High-Level Architecture Overview

Mypy processes programs through several sequenced phases:

1. **Source discovery** (`find_sources.py`, `modulefinder.py`): locates all Python files and modules to be checked based on CLI arguments and configuration
2. **Parsing** (`fastparse.py`, `parse.py`): converts Python source into an AST using the CPython `ast` module (or optionally `ast-serialize` for a native parser)
3. **Semantic analysis** (`semanal.py`, `semanal_main.py`, `semanal_*.py`): resolves names, builds symbol tables, processes imports, handles special forms (NamedTuple, TypedDict, etc.)
4. **Type checking** (`checker.py`, `checkexpr.py`, `checkmember.py`, `checkpattern.py`, `checkstrformat.py`): traverses the AST and verifies type correctness
5. **Error reporting** (`errors.py`, `error_formatter.py`, `messages.py`): collects and formats diagnostics

The build system (`build.py`) orchestrates all phases, manages the module dependency graph, and handles incremental caching. The daemon server (`dmypy_server.py`, `server/update.py`) maintains live state for fine-grained incremental re-checking.

Type representation lives in `types.py` (abstract type classes) and `nodes.py` (AST node classes). Subtyping logic is in `subtypes.py`; type joining and meeting (for union/intersection) in `join.py` and `meet.py`.

## Related Projects and Dependencies

- **typeshed** (bundled at `mypy/typeshed/`): stubs for the Python standard library and popular third-party packages
- **mypy_extensions**: provides `@trait`, `@mypyc_attr`, `TypedDict` (legacy), and other utilities
- **typing_extensions**: backports of new typing features to older Python versions
- **pathspec**: used for `.gitignore`-style file exclusion patterns
- **tomli / tomllib**: TOML configuration parsing (stdlib on Python 3.11+)
- **librt**: internal Anthropic/mypy library for optimized serialization and cache I/O (`librt.internal`, `librt.base64`)
- **psutil**: optional dependency for `dmypy` memory profiling
- **lxml**: optional dependency for XML/HTML report generation
- **orjson**: optional faster JSON backend for cache files
- **ast-serialize**: optional native parser backend
- **setuptools**: required for mypyc compilation
- **mypyc** (co-located in `mypyc/`): the compiler that turns annotated mypy code into C extensions; mypy itself is shipped pre-compiled using mypyc
