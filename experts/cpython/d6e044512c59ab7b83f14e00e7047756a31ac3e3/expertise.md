### Language and Runtime
- Python 3.15 language features, syntax, and semantics
- Python grammar (`Grammar/python.gram` PEG grammar format)
- AST node types defined in `Parser/Python.asdl`
- Tokenizer and lexer (`Parser/tokenizer/`, `Parser/lexer/`)
- PEG parser engine (`Parser/pegen.c`) and parser generation (`Tools/peg_generator/`)
- Compiler pipeline: AST → symtable → bytecode → code object
  - Symbol table and scope analysis (`Python/symtable.c`)
  - Code generation (`Python/codegen.c`, `Python/compile.c`)
  - Bytecode assembly and optimization (`Python/assemble.c`, `Python/flowgraph.c`)
- Bytecode instruction set: definitions in `Python/bytecodes.c` (DSL), IDs in `Include/opcode_ids.h`
- Code object (`PyCodeObject`) layout and fields (`Include/cpython/code.h`, `InternalDocs/code_objects.md`)
- Frame objects (`_PyInterpreterFrame`) and frame lifecycle (`InternalDocs/frames.md`)

### Interpreter Execution
- Bytecode evaluation loop (`Python/ceval.c`, `InternalDocs/interpreter.md`)
- Adaptive specializing interpreter: how counters work, when specialization fires (`Python/specialize.c`)
- Instruction specializations (e.g., `LOAD_ATTR_MODULE`, `BINARY_OP_ADD_INT`)
- Inline cache entries and their layout
- `EXTENDED_ARG` and wide instructions
- Recursion limit enforcement (`Python/ceval.c:Py_EnterRecursiveCall`)
- Stack references (`_PyStackRef`) design (`InternalDocs/stackrefs.md`)
- Exception handling mechanism and exception tables (`InternalDocs/exception_handling.md`)
- Generator, coroutine, and async generator execution (`InternalDocs/generators.md`)

### JIT Compiler
- Copy-and-patch JIT architecture (`InternalDocs/jit.md`, `Python/jit.c`)
- Trace recorder: how hot loops are detected and traces are built (`Python/optimizer.c`)
- Micro-ops (UOps) and the optimizer IR (`Python/optimizer_bytecodes.c`)
- Optimizer analysis and type propagation (`Python/optimizer_analysis.c`, `Python/optimizer_symbols.c`)
- LLVM stencil generation (`Tools/jit/`)
- JIT build requirements and `--enable-experimental-jit` configure flag
- Executor objects (`_PyExecutorObject`) and side exits

### Memory Management
- Reference counting: `Py_INCREF`, `Py_DECREF`, `Py_CLEAR`, immortal objects
- Cyclic garbage collector design and generations (`InternalDocs/garbage_collector.md`, `Python/gc.c`)
- Free-threaded GC (`Python/gc_free_threading.c`)
- Quiescent-State Based Reclamation (QSBR) for deferred reference counting (`InternalDocs/qsbr.md`)
- Memory allocator tiers: `PyMem_Malloc`, `PyObject_Malloc`, `PyMem_RawMalloc`
- mimalloc integration (`Objects/mimalloc/`)
- `tracemalloc` and memory profiling

### Type System and Object Model
- `PyObject` and `PyVarObject` base structures (`Include/object.h`)
- `PyTypeObject` full slot layout (`Include/cpython/object.h`)
- Number protocol: `PyNumberMethods` (nb_add, nb_multiply, etc.)
- Sequence protocol: `PySequenceMethods`
- Mapping protocol: `PyMappingMethods`
- Buffer protocol: `PyBufferProcs`
- `tp_new`, `tp_init`, `tp_alloc`, `tp_dealloc` lifecycle
- `tp_richcompare` and comparison protocol
- Descriptors: `PyGetSetDef`, `PyMemberDef`, `tp_getset`, `tp_members`
- `PyType_Ready()` and type finalization
- Heap-allocated vs. statically-allocated type objects
- Abstract base classes and `PyType_IsSubtype`
- `PyObject_GenericGetAttr`, `PyObject_GenericSetAttr`

### Built-in Types Internals
- Integer objects: arbitrary precision (`Objects/longobject.c`)
- String objects: PEP 393 flexible representation, interning (`Objects/unicodeobject.c`, `InternalDocs/string_interning.md`)
- Dict objects: compact hash table, split/combined tables (`Objects/dictobject.c`)
- List objects: dynamic array, timsort (`Objects/listobject.c`, `Objects/listsort.txt`)
- Tuple objects: immutable, compact (`Objects/tupleobject.c`)
- Set/frozenset: open-addressed hash table (`Objects/setobject.c`)
- Bytes/bytearray objects (`Objects/bytesobject.c`, `Objects/bytearrayobject.c`)
- Function objects: `PyFunctionObject`, closures, annotations (`Objects/funcobject.c`)
- Exception hierarchy: `BaseException`, `Exception`, subclasses (`Objects/exceptions.c`)
- Interpolation objects (PEP 750 template strings) (`Objects/interpolationobject.c`)
- Lazy import objects (`Objects/lazyimportobject.c`)

### C Extension Development
- Writing C extensions: `PyModuleDef`, `PyMethodDef`, `PyMODINIT_FUNC`
- Single-phase vs. multi-phase module initialization (PEP 489)
- `Py_mod_exec`, `Py_mod_multiple_interpreters`, `Py_mod_gil` slots
- Argument Clinic: syntax, format strings, generated code (`Tools/clinic/`)
- `PyArg_ParseTuple`, `PyArg_ParseTupleAndKeywords`, `Py_BuildValue` format strings
- `PyCFunction`, `PyCFunctionFast`, `PyCFunctionWithKeywords` calling conventions
- `METH_VARARGS`, `METH_KEYWORDS`, `METH_FASTCALL`, `METH_NOARGS`, `METH_O` flags
- Defining custom types in C: full `PyTypeObject` example
- `PyModule_AddObjectRef`, `PyModule_Add`, `PyModule_AddType`
- Stable/limited ABI (`Py_LIMITED_API`, `Misc/stable_abi.toml`)
- `PyAPI_FUNC`, `PyAPI_DATA`, `Py_EXPORTED_SYMBOL` macros
- Error handling: `PyErr_SetString`, `PyErr_Format`, `PyErr_Clear`, `PyErr_Occurred`

### Import System
- `importlib` bootstrap (`Lib/importlib/`)
- `sys.meta_path`, `sys.path_hooks`, finders and loaders
- `PyImport_ImportModule`, `PyImport_ImportModuleLevelObject`
- `PyImport_AppendInittab` for embedding built-in modules
- Frozen modules: `_freeze_module`, `regen-frozen` target
- Lazy imports (`PyImport_SetLazyImportsMode`, `Objects/lazyimportobject.c`)
- `.pyc` files: magic number (`PyImport_GetMagicNumber`), marshal format
- Namespace packages (PEP 420)

### Threading and Concurrency
- GIL: acquisition, release, `Py_BEGIN_ALLOW_THREADS` / `Py_END_ALLOW_THREADS`
- `PyThreadState`, `PyInterpreterState` management
- Free-threaded builds (`--disable-gil`, `Py_GIL_DISABLED`), per-object locking
- Critical sections API (`Include/critical_section.h`, `Python/critical_section.c`)
- `threading` module internals
- `asyncio` event loop (`Lib/asyncio/`, `InternalDocs/asyncio.md`)
- Sub-interpreters: `_interpreters` module, channels, queues

### Standard Library
- `os`, `sys`, `pathlib`, `shutil` — file system operations
- `socket`, `ssl`, `urllib`, `http` — networking
- `asyncio` — cooperative multitasking
- `threading`, `multiprocessing`, `concurrent.futures` — concurrency
- `json`, `csv`, `tomllib`, `configparser` — data formats
- `re` — regular expressions (SRE engine in `Modules/_sre/`)
- `logging` — structured logging framework
- `unittest`, `doctest` — testing frameworks
- `sqlite3` — SQLite database bindings
- `ctypes` — C FFI
- `dataclasses`, `typing`, `annotationlib` — type system support
- `importlib` — import machinery
- `zipimport`, `zipapp` — ZIP-based module loading
- `collections`, `itertools`, `functools` — data structures and functional utilities
- `io` — I/O abstractions (`_io` C module + `_pyio.py` fallback)
- `hashlib`, `hmac`, `secrets` — cryptography
- `zlib`, `bz2`, `lzma`, `compression.zstd` — compression

### Build System
- `configure`/`configure.ac` — autoconf-based configuration
- `Makefile.pre.in` — build targets, code generation targets
- `Modules/makesetup` and `Modules/Setup` — extension module configuration
- PGO (Profile-Guided Optimization) build
- LTO (Link-Time Optimization) build
- `regen-*` make targets and when to use them
- Windows build: `PCbuild/`, MSBuild projects
- macOS framework build: `Mac/`
- Android and iOS platform builds
- Emscripten/WASM build support
- `pixi` package management for dev dependencies

### Debugging and Profiling
- CPython debug build (`--with-pydebug`): assertions, ref debug, object tracking
- `gdb` helpers (`Tools/gdb/`)
- `faulthandler` module
- `tracemalloc` memory tracing
- `sys.settrace`, `sys.setprofile`
- `sys.monitoring` (PEP 669) low-overhead instrumentation
- `perf` profiling integration (`Python/perf_jit_trampoline.c`)
- DTrace probes (`--with-dtrace`)
- Remote debugging support (`Modules/_remote_debugging/`, `Include/cpython/pystate.h`)

### Developer Tools
- `Tools/cases_generator/` — bytecode DSL processor
- `Tools/peg_generator/` — PEG grammar → C parser generator
- `Tools/clinic/` — Argument Clinic C argument parsing codegen
- `Tools/jit/` — JIT stencil builder using LLVM
- `Tools/c-analyzer/` — C API stability analysis
- `Tools/build/` — build helper scripts
- `Tools/scripts/` — miscellaneous developer scripts
- `blurb` (news fragment management, `Misc/NEWS.d/`)
- `mypy` type checking configuration (`Misc/mypy/`)

### Platform and Porting
- Platform-specific `#ifdef` patterns (`MS_WINDOWS`, `__APPLE__`, etc.)
- `pyconfig.h` configuration macros
- `osdefs.h` — OS-specific path separators
- Cross-compilation support
- Stable ABI guarantees across platforms
