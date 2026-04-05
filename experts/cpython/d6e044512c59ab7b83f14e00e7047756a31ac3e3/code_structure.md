# CPython Code Structure

## Annotated Directory Tree

```
cpython/
├── Grammar/                  # Python language grammar
│   ├── python.gram           # PEG grammar definition (source of truth for parser)
│   └── Tokens                # Token definitions (also used by tokenize module)
│
├── Include/                  # Public C API headers
│   ├── Python.h              # Master include — all C extensions #include this
│   ├── object.h              # PyObject, PyTypeObject, reference counting macros
│   ├── abstract.h            # Abstract object protocol (PyObject_Call, PySequence_*, etc.)
│   ├── ceval.h               # Bytecode evaluation API (PyEval_EvalCode, recursion limits)
│   ├── import.h              # Import system API (PyImport_ImportModule, etc.)
│   ├── modsupport.h          # Module creation helpers (PyArg_ParseTuple, Py_BuildValue)
│   ├── methodobject.h        # PyMethodDef, PyCFunction typedefs
│   ├── moduleobject.h        # PyModuleDef, PyModule_* API
│   ├── longobject.h          # Integer object API
│   ├── bytesobject.h         # Bytes object API
│   ├── unicodeobject.h       # String/unicode object API
│   ├── listobject.h          # List object API
│   ├── dictobject.h          # Dict object API
│   ├── tupleobject.h         # Tuple object API
│   ├── setobject.h           # Set/frozenset API
│   ├── frameobject.h         # Frame object public API
│   ├── compile.h             # Compiler public API
│   ├── datetime.h            # datetime C API
│   ├── marshal.h             # Marshal/unmarshal bytecode
│   ├── opcode.h              # Opcode definitions
│   ├── opcode_ids.h          # Opcode numeric IDs (generated)
│   ├── critical_section.h    # Thread-safe critical section API (free-threaded builds)
│   ├── exports.h             # Py_EXPORTED_SYMBOL macros
│   ├── patchlevel.h          # PY_VERSION, PY_MAJOR_VERSION, etc.
│   ├── pyconfig.h.in         # Platform config template
│   ├── cpython/              # CPython-private but stable-ish API (not in LIMITED_API)
│   │   ├── abstract.h        # _PyObject_Vectorcall, etc.
│   │   ├── object.h          # PyTypeObject full layout, PyNumberMethods, etc.
│   │   ├── pystate.h         # PyThreadState, PyInterpreterState full structs
│   │   ├── initconfig.h      # PyConfig, PyPreConfig (embedding API)
│   │   ├── code.h            # PyCodeObject layout
│   │   ├── frameobject.h     # _PyInterpreterFrame
│   │   ├── ceval.h           # _PyEval_SetTrace, monitoring hooks
│   │   ├── compile.h         # Compiler internals exposed to extensions
│   │   ├── import.h          # _PyImport_* advanced import control
│   │   ├── longintrepr.h     # Long integer internal representation
│   │   ├── funcobject.h      # PyFunctionObject layout
│   │   ├── genobject.h       # Generator/coroutine/async-gen objects
│   │   ├── dictobject.h      # Dict internals
│   │   ├── context.h         # contextvars C API
│   │   ├── monitoring.h      # sys.monitoring C API
│   │   └── pyatomic*.h       # Atomic operations (GCC, MSVC, C11 variants)
│   └── internal/             # CPython-internal headers (not for extension authors)
│       ├── pycore_runtime.h  # _PyRuntimeState — process-global singleton
│       ├── pycore_interp.h   # PyInterpreterState internals
│       ├── pycore_ceval.h    # Interpreter loop internals, eval_breaker
│       ├── pycore_code.h     # Code object internals, adaptive counters
│       ├── pycore_frame.h    # _PyInterpreterFrame (execution frame)
│       ├── pycore_object.h   # Refcount helpers, immortal objects
│       ├── pycore_gc.h       # Garbage collector internals
│       ├── pycore_optimizer.h# JIT optimizer, _PyExecutorObject
│       ├── pycore_compile.h  # Compiler internals
│       ├── pycore_import.h   # Import system internals
│       ├── pycore_dict.h     # Dict internals (compact dict)
│       ├── pycore_longobject.h # bigint internals
│       ├── pycore_crossinterp.h# Cross-interpreter data sharing
│       ├── pycore_backoff.h  # Adaptive interpreter backoff counters
│       ├── pycore_debug_offsets.h # Debug ABI offsets for external debuggers
│       └── mimalloc/         # Embedded mimalloc allocator headers
│
├── Objects/                  # Built-in type implementations
│   ├── object.c              # Base object protocol, type system machinery
│   ├── typeobject.c          # type/class objects, MRO, metaclasses
│   ├── longobject.c          # Integer objects (arbitrary precision)
│   ├── floatobject.c         # Float objects (IEEE 754 double)
│   ├── complexobject.c       # Complex number objects
│   ├── bytesobject.c         # Immutable bytes objects
│   ├── bytearrayobject.c     # Mutable bytearray objects
│   ├── unicodeobject.c       # str objects (PEP 393 flexible string representation)
│   ├── listobject.c          # list objects
│   ├── tupleobject.c         # tuple objects
│   ├── dictobject.c          # dict objects (compact hash table, PEP 412)
│   ├── setobject.c           # set/frozenset objects
│   ├── exceptions.c          # Exception hierarchy
│   ├── funcobject.c          # Function objects
│   ├── codeobject.c          # Code objects
│   ├── frameobject.c         # Frame objects
│   ├── genobject.c           # Generator, coroutine, async generator
│   ├── cellobject.c          # Closure cell objects
│   ├── memoryobject.c        # memoryview objects
│   ├── moduleobject.c        # Module objects
│   ├── classobject.c         # Bound/unbound method objects
│   ├── descrobject.c         # Descriptors (property, staticmethod, classmethod)
│   ├── iterobject.c          # Generic iterators
│   ├── genericaliasobject.c  # PEP 585 generic aliases (list[int], etc.)
│   ├── interpolationobject.c # PEP 750 template string interpolation objects
│   ├── lazyimportobject.c    # Lazy import objects
│   ├── abstract.c            # Abstract object protocol implementation
│   ├── call.c                # Object calling protocol (_PyObject_Vectorcall)
│   └── mimalloc/             # Embedded mimalloc memory allocator
│
├── Python/                   # Core interpreter implementation
│   ├── ceval.c               # Bytecode evaluation entry points, recursion limit
│   ├── bytecodes.c           # Instruction definitions in DSL (source for generated files)
│   ├── ceval_gil.c           # GIL acquisition/release logic
│   ├── compile.c             # High-level compiler driver
│   ├── codegen.c             # AST → bytecode instruction generation
│   ├── assemble.c            # Instruction list → bytecode binary
│   ├── ast.c                 # AST construction and validation
│   ├── ast_preprocess.c      # AST preprocessing pass
│   ├── ast_unparse.c         # AST → source text (for f-string repr)
│   ├── symtable.c            # Symbol table analysis (scopes, free vars)
│   ├── specialize.c          # Adaptive specialization of bytecodes
│   ├── optimizer.c           # JIT trace recorder and optimizer driver
│   ├── optimizer_analysis.c  # Type analysis for JIT optimizer
│   ├── optimizer_bytecodes.c # Micro-op definitions for JIT
│   ├── optimizer_symbols.c   # Abstract value/type symbols for optimizer
│   ├── jit.c                 # Copy-and-patch JIT code emission
│   ├── errors.c              # Exception raising helpers
│   ├── import.c              # Import system implementation
│   ├── bltinmodule.c         # Built-in functions (print, len, range, etc.)
│   ├── sysmodule.c           # sys module implementation
│   ├── builtins.c            # Additional builtins
│   ├── context.c             # contextvars implementation
│   ├── crossinterp.c         # Cross-interpreter data transfer
│   ├── gc.c / gc_free_threading.c  # Cyclic GC implementations
│   ├── pystate.c             # PyInterpreterState, PyThreadState management
│   ├── thread.c              # Threading primitives
│   ├── bootstrap_hash.c      # Hash randomization seeding
│   ├── dtoa.c                # Float→string conversion (David Gay's dtoa)
│   ├── dynload_shlib.c       # Dynamic loading on Unix (dlopen)
│   ├── dynload_win.c         # Dynamic loading on Windows
│   ├── executor_cases.c.h    # Generated JIT executor case handlers
│   ├── generated_cases.c.h   # Generated interpreter dispatch cases
│   └── clinic/               # Clinic-generated argument parsing files
│
├── Parser/                   # Lexer and PEG parser
│   ├── tokenizer/            # Tokenizer implementation
│   ├── lexer/                # Lexer implementation
│   ├── pegen.c               # PEG parser engine
│   ├── pegen.h               # PEG parser API
│   ├── parser.c              # Generated parser (from python.gram)
│   ├── Python.asdl           # ASDL grammar for the AST node types
│   ├── asdl.py               # ASDL parser (Python)
│   ├── asdl_c.py             # ASDL → C code generator
│   ├── string_parser.c       # String literal parsing (f-strings, etc.)
│   ├── action_helpers.c      # Grammar action helper functions
│   ├── myreadline.c          # readline wrapper
│   └── token.c               # Token definitions
│
├── Modules/                  # C extension modules (built-in and optional)
│   ├── _io/                  # I/O module (_io, io)
│   ├── _ssl/                 # SSL/TLS module
│   ├── _sqlite/              # SQLite bindings
│   ├── _ctypes/              # ctypes FFI
│   ├── _decimal/             # Decimal arithmetic (libmpdec)
│   ├── _sre/                 # Regular expression engine
│   ├── _multiprocessing/     # multiprocessing support
│   ├── _hacl/                # HACL* cryptographic implementations
│   ├── _remote_debugging/    # Remote debugger support module
│   ├── _asynciomodule.c      # asyncio C accelerator
│   ├── _collectionsmodule.c  # collections C types (deque, etc.)
│   ├── _datetimemodule.c     # datetime C accelerator
│   ├── _json.c               # JSON encoder/decoder C accelerator
│   ├── _pickle.c             # pickle C accelerator
│   ├── _randommodule.c       # random module (Mersenne Twister)
│   ├── _struct.c             # struct module (binary packing)
│   ├── _hashopenssl.c        # Hash functions via OpenSSL
│   ├── _interpretersmodule.c # sub-interpreters module
│   ├── _interpchannelsmodule.c # inter-interpreter channels
│   ├── _interpqueuesmodule.c # inter-interpreter queues
│   └── makesetup             # Module build configuration
│
├── Lib/                      # Python standard library
│   ├── asyncio/              # Async I/O framework
│   ├── collections/          # Container datatypes
│   ├── concurrent/           # concurrent.futures
│   ├── compression/          # compression utilities
│   ├── ctypes/               # ctypes Python wrappers
│   ├── curses/               # curses terminal control
│   ├── dbm/                  # database key-value store
│   ├── email/                # email parsing and generation
│   ├── importlib/            # import machinery in Python
│   ├── json/                 # JSON codec
│   ├── logging/              # Logging framework
│   ├── pathlib/              # Object-oriented filesystem paths
│   ├── re/                   # Regular expressions
│   ├── sqlite3/              # SQLite bindings
│   ├── ssl.py                # SSL/TLS wrapper
│   ├── string/               # String utilities
│   ├── test/                 # Standard library test suite
│   ├── tkinter/              # Tcl/Tk GUI bindings
│   ├── tomllib/              # TOML parser
│   ├── typing.py             # Type annotations support
│   ├── unittest/             # Unit testing framework
│   ├── urllib/               # URL handling
│   ├── venv/                 # Virtual environment creation
│   ├── xml/                  # XML processing
│   ├── xmlrpc/               # XML-RPC client/server
│   ├── zipfile/              # ZIP archive handling
│   ├── zoneinfo/             # IANA timezone database
│   ├── os.py                 # OS interface
│   ├── socket.py             # Socket interface
│   ├── threading.py          # Thread-based concurrency
│   ├── dataclasses.py        # @dataclass decorator
│   ├── functools.py          # Higher-order functions
│   ├── itertools.py          # Iterator building blocks
│   ├── abc.py                # Abstract base classes
│   ├── annotationlib.py      # PEP 563/649 annotation evaluation
│   ├── _pyrepl/              # Pure-Python REPL implementation
│   └── _pydatetime.py        # Pure-Python datetime fallback
│
├── Doc/                      # Sphinx-based official documentation
│   ├── c-api/                # C API reference documentation
│   ├── library/              # Standard library reference
│   ├── extending/            # "Extending and Embedding" tutorial
│   ├── howto/                # How-to guides
│   ├── faq/                  # FAQ
│   └── conf.py               # Sphinx configuration
│
├── InternalDocs/             # CPython maintainer documentation
│   ├── interpreter.md        # Bytecode interpreter design
│   ├── compiler.md           # Compiler design
│   ├── jit.md                # JIT compiler design
│   ├── garbage_collector.md  # GC design
│   ├── frames.md             # Frame objects
│   ├── code_objects.md       # Code objects
│   ├── parser.md             # Parser guide
│   ├── exception_handling.md # Exception handling internals
│   ├── generators.md         # Generators/coroutines
│   ├── asyncio.md            # asyncio internals
│   ├── stackrefs.md          # _PyStackRef design
│   ├── qsbr.md               # Quiescent-State Based Reclamation
│   └── string_interning.md   # String interning
│
├── Tools/                    # Developer tools
│   ├── build/                # Build helper scripts
│   ├── cases_generator/      # Bytecode DSL → C code generator
│   ├── clinic/               # Argument Clinic (C argument parsing codegen)
│   ├── jit/                  # JIT stencil builder (LLVM-based)
│   ├── peg_generator/        # PEG grammar → parser C code generator
│   ├── gdb/                  # GDB helpers for CPython debugging
│   ├── inspection/           # Code inspection utilities
│   ├── c-analyzer/           # C API analyzer
│   ├── scripts/              # Miscellaneous scripts
│   └── unicode/              # Unicode data generation
│
├── PC/                       # Windows-specific files
├── PCbuild/                  # Windows MSBuild project files
├── Mac/                      # macOS-specific files (framework builds)
├── Android/                  # Android platform support
├── Platforms/                # Platform-specific configuration
├── Programs/                 # Entry point C files
│   ├── python.c              # Main entry point (calls Py_Main/Py_BytesMain)
│   ├── _freeze_module.c      # Tool: freeze stdlib modules to C arrays
│   └── _testembed.c          # Embedding API test program
├── Misc/                     # Miscellaneous project files
│   ├── NEWS.d/               # Per-change news fragments (blurb)
│   ├── stable_abi.toml       # Stable ABI symbol list
│   └── HISTORY               # Changelog
├── configure.ac              # Autoconf source for build configuration
├── Makefile.pre.in           # Makefile template (processed by configure)
├── aclocal.m4                # Autoconf macro definitions
├── pyconfig.h.in             # Configuration header template
└── README.rst                # Project README
```

## Code Organization Patterns

**Generated code**: Several C source files are auto-generated and should not be edited directly:
- `Python/generated_cases.c.h` — interpreter dispatch table, generated from `Python/bytecodes.c`
- `Python/executor_cases.c.h` — JIT executor cases, generated from `Python/optimizer_bytecodes.c`
- `Python/optimizer_cases.c.h` — optimizer transformation cases
- `Parser/parser.c` — PEG parser, generated from `Grammar/python.gram`
- `Include/opcode_ids.h` — opcode numeric IDs, generated from `Python/bytecodes.c`

**Clinic files**: `*.clinic.c` / `clinic/` subdirectories contain Argument Clinic generated argument parsing code. The source `.clinic` files live alongside the C files.

**Pure-Python fallbacks**: Many performance-critical modules have both a C accelerator in `Modules/` and a pure-Python fallback in `Lib/`. The Python version is named with a leading underscore or `_py` prefix (e.g., `Lib/_pyio.py` for `Modules/_io/`, `Lib/_pydatetime.py` for `Modules/_datetimemodule.c`).

**Header layering**: Public API headers live in `Include/`. Headers in `Include/cpython/` are CPython-specific but usable by extension authors. Headers in `Include/internal/` are for CPython internals only and subject to change without notice.
