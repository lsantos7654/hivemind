# Mypy Code Structure

## Top-Level Directory Layout

```
mypy/                        # Main type-checker Python package
mypyc/                       # Python-to-C compiler (co-located, separate package)
test-data/                   # Data-driven test fixtures (.test files)
docs/                        # Sphinx documentation source
misc/                        # Utility scripts (not part of the installable package)
conftest.py                  # pytest configuration and test collection hooks
pyproject.toml               # Build system metadata, tool configuration
setup.py                     # Legacy setuptools entry point (delegates to pyproject.toml)
runtests.py                  # Convenience test runner
tox.ini                      # tox environment definitions
mypy_self_check.ini          # mypy config used to type-check mypy itself
mypy_bootstrap.ini           # mypy config used during bootstrap (before mypyc compile)
build-requirements.txt       # Extra deps needed only at build time (for mypyc)
mypy-requirements.txt        # Runtime deps (mirrors pyproject.toml dependencies)
test-requirements.txt        # Full test dependency list
action.yml                   # GitHub Actions composite action definition
```

## `mypy/` Package — Core Type Checker

### Entry Points and CLI

| File | Purpose |
|------|---------|
| `__main__.py` | `python -m mypy` entry point; calls `mypy.main.main()` |
| `main.py` | Argument parsing (`argparse`), option assembly, top-level `main()` function |
| `api.py` | Programmatic API: `run(args)` and `run_dmypy(args)` returning `(stdout, stderr, exit_code)` |

### Build Pipeline

| File | Purpose |
|------|---------|
| `build.py` | Core build orchestrator: `build()` function, `State` class (per-file state), `Graph` type alias, dependency management, incremental cache management |
| `build_worker/` | Sub-package for parallel build workers: `__main__.py`, `worker.py` |
| `find_sources.py` | Source file discovery: `create_source_list()`, `SourceFinder` class |
| `modulefinder.py` | Module search path resolution: `FindModuleCache`, `BuildSource`, `SearchPaths`, `ModuleNotFoundReason` |
| `fscache.py` | File system read cache (`FileSystemCache`): avoids repeated stat/read calls within a single build |
| `fswatcher.py` | File system watcher (`FileSystemWatcher`) for daemon mode: detects changed files between runs |
| `metastore.py` | Cache metadata I/O: `.mypy_cache` directory management |
| `cache.py` | Low-level binary cache serialization primitives: `ReadBuffer`, `WriteBuffer`, tag-based I/O |

### Parsing

| File | Purpose |
|------|---------|
| `parse.py` | Top-level parse dispatch: chooses between native and fallback parsers |
| `fastparse.py` | Main parser: converts CPython `ast` module AST to mypy AST nodes |
| `nativeparse.py` | Integration with the optional `ast-serialize` native parser |
| `sharedparse.py` | Shared parsing utilities |

### AST Nodes

| File | Purpose |
|------|---------|
| `nodes.py` | All AST node classes: `MypyFile`, `FuncDef`, `ClassDef`, `AssignmentStmt`, `TypeInfo`, `Var`, `SymbolTable`, etc. Approximately 7000 lines. |
| `visitor.py` | Base `NodeVisitor` class for AST traversal |
| `traverser.py` | `TraverserVisitor` and `ExtendedTraverserVisitor`: visit all nodes depth-first |
| `mixedtraverser.py` | Mixed traversal combining nodes and types |
| `treetransform.py` | Base class for AST transformations |
| `strconv.py` | AST-to-string conversion for debugging |

### Type System

| File | Purpose |
|------|---------|
| `types.py` | All type classes: `Type`, `Instance`, `UnionType`, `TupleType`, `CallableType`, `LiteralType`, `TypeVarType`, `ParamSpecType`, `TypeVarTupleType`, `ProperType`, etc. |
| `type_visitor.py` | `TypeVisitor` and `TypeTranslator` base classes |
| `typetraverser.py` | `TypeTraverser`: visits all sub-types |
| `subtypes.py` | Subtype checking: `is_subtype()`, `is_compatible_with()`, `is_proper_subtype()` |
| `join.py` | Type join (least upper bound): `join_types()` |
| `meet.py` | Type meet (greatest lower bound): `meet_types()` |
| `typeops.py` | Type operations: `map_instance_to_supertype()`, `make_simplified_union()`, etc. |
| `expandtype.py` | Type variable substitution: `expand_type()`, `expand_type_by_instance()` |
| `applytype.py` | Apply generic type arguments to callables |
| `erasetype.py` | Type erasure: `erase_type()`, `erase_typevars()` |
| `copytype.py` | Deep-copy a type |
| `maptype.py` | `map_instance_to_supertype()` |
| `constraints.py` | Type constraint solving for generics: `infer_constraints()` |
| `solve.py` | Constraint solver: `solve_constraints()` |
| `infer.py` | Type argument inference |
| `typevars.py` | TypeVar utilities |
| `typevartuples.py` | TypeVarTuple / variadic generics utilities |
| `tvar_scope.py` | TypeVar scope tracking during analysis |

### Semantic Analysis

| File | Purpose |
|------|---------|
| `semanal.py` | Main semantic analyzer: name binding, symbol table population, import resolution (~7000 lines) |
| `semanal_main.py` | Top-level semantic analysis coordination: `semantic_analysis_for_scc()` |
| `semanal_pass1.py` | First pass semantic analysis (module-level names) |
| `semanal_shared.py` | Shared utilities for semantic analysis |
| `semanal_classprop.py` | Class property analysis |
| `semanal_enum.py` | Enum type handling |
| `semanal_infer.py` | Type inference during semantic analysis |
| `semanal_namedtuple.py` | NamedTuple processing |
| `semanal_newtype.py` | NewType processing |
| `semanal_typeddict.py` | TypedDict processing |
| `semanal_typeargs.py` | Type argument validation |
| `typeanal.py` | Type expression analysis: converts AST nodes to `Type` objects |
| `binder.py` | Type narrowing: `ConditionalTypeBinder` tracks types through branches |
| `scope.py` | Scope and namespace tracking |
| `tvar_scope.py` | TypeVar binding scope |
| `lookup.py` | Symbol lookup utilities |
| `renaming.py` | Local variable renaming |

### Type Checking

| File | Purpose |
|------|---------|
| `checker.py` | Statement type checker: `TypeChecker` class, checks all statement forms (~7000 lines) |
| `checker_shared.py` | Shared checker API: `TypeCheckerSharedApi` protocol |
| `checker_state.py` | Mutable checker state singleton |
| `checkexpr.py` | Expression type checker: `ExpressionChecker` class (~6000 lines) |
| `checkmember.py` | Member access checking: `analyze_member_access()` |
| `checkpattern.py` | Pattern matching (match/case) checking: `PatternChecker` |
| `checkstrformat.py` | String format (% and .format()) checking |
| `partially_defined.py` | Detects variables that may be used before assignment |
| `reachability.py` | Reachability analysis for dead code detection |
| `operators.py` | Operator type resolution |
| `literals.py` | Literal type utilities |

### Error System

| File | Purpose |
|------|---------|
| `errors.py` | `Errors` class, `ErrorInfo` dataclass, error collection and filtering |
| `errorcodes.py` | `ErrorCode` class and all standard error code constants (`ATTR_DEFINED`, `ARG_TYPE`, etc.) |
| `messages.py` | Human-readable error message generation: `MessageBuilder` |
| `message_registry.py` | Catalog of `ErrorMessage` instances |
| `error_formatter.py` | Output formatters (text, JSON): `OUTPUT_CHOICES` |

### Plugin System

| File | Purpose |
|------|---------|
| `plugin.py` | Plugin API base classes: `Plugin`, `CommonPluginApi`, `CheckerPluginInterface`, `SemanticAnalyzerPluginInterface`, and all `*Context` types |
| `plugins/` | Built-in plugin implementations |
| `plugins/attrs.py` | attrs library support |
| `plugins/dataclasses.py` | dataclasses support |
| `plugins/ctypes.py` | ctypes module support |
| `plugins/enum.py` | Enum type support |
| `plugins/functools.py` | functools.partial, etc. |
| `plugins/singledispatch.py` | functools.singledispatch support |
| `plugins/default.py` | Default plugin (chains all built-in plugins) |
| `plugins/proper_plugin.py` | Plugin for detecting `.serialize()` anti-patterns in mypy itself |

### Daemon Mode (dmypy)

| File | Purpose |
|------|---------|
| `dmypy/client.py` | dmypy CLI client: sends commands to the daemon server |
| `dmypy/__main__.py` | `python -m mypy.dmypy` entry |
| `dmypy_server.py` | Daemon server: long-running process, handles `check`, `run`, `suggest`, `inspect` commands |
| `dmypy_util.py` | IPC message send/receive utilities |
| `dmypy_os.py` | OS-specific daemon helpers |
| `ipc.py` | Cross-platform IPC: `IPCServer`, `IPCClient` (Unix sockets / Windows named pipes) |
| `fswatcher.py` | Watches files for changes between daemon runs |

### Fine-Grained Incremental Mode

| File | Purpose |
|------|---------|
| `server/update.py` | `FineGrainedBuildManager`: orchestrates fine-grained re-checking after file changes |
| `server/deps.py` | Dependency graph computation at the symbol level |
| `server/trigger.py` | Trigger key computation (what causes re-checking) |
| `server/target.py` | Target identification (what needs re-checking) |
| `server/astdiff.py` | AST diffing between old and new versions of a module |
| `server/astmerge.py` | AST merging for incremental updates |
| `server/aststrip.py` | AST stripping for serialization |

### Tools

| File | Purpose |
|------|---------|
| `stubgen.py` | Stub generator: `ASTStubGenerator`, `main()` CLI entry point |
| `stubgenc.py` | C extension stub generator (introspection-based) |
| `stubtest.py` | Stub tester: verifies stubs match runtime behavior |
| `stubutil.py` | Shared stub utilities |
| `stubdoc.py` | Sphinx .rst doc parsing for better C stub signatures |
| `stubinfo.py` | Stub package metadata registry |
| `suggestions.py` | `SuggestionEngine`: infers types for unannotated functions (used by dmypy `suggest` command) |
| `inspections.py` | `InspectionEngine`: provides type-at-point information (used by dmypy `inspect` command) |

### Configuration

| File | Purpose |
|------|---------|
| `options.py` | `Options` class with all mypy configuration knobs; `PER_MODULE_OPTIONS`, `INCOMPLETE_FEATURES` |
| `config_parser.py` | Reads `mypy.ini`, `setup.cfg`, `tox.ini`, `pyproject.toml` into `Options` |
| `defaults.py` | Default constant values (Python version, recursion limit, etc.) |

### Utilities

| File | Purpose |
|------|---------|
| `util.py` | Miscellaneous helpers: `FancyFormatter`, `IdMapper`, `count_stats()`, etc. |
| `graph_utils.py` | Strongly-connected component (SCC) computation on the module dependency graph |
| `state.py` | `state` singleton for global mutable state |
| `typestate.py` | `TypeState` global: caches subtype check results |
| `gclogger.py` | GC logging utilities |
| `memprofile.py` | Memory profiling tools |
| `pyinfo.py` | Python interpreter info queries |
| `version.py` | `__version__` string |
| `git.py` | Git utilities (rev detection for dev version strings) |

## `mypyc/` Package — Python-to-C Compiler

```
mypyc/
├── __main__.py             # mypyc CLI entry point
├── build.py                # setuptools extension build integration (mypycify())
├── build_setup.py          # Build setup helpers
├── options.py              # MypycOptions: compiler options
├── common.py               # Shared constants and helpers
├── crash.py                # Crash reporting
├── subtype.py              # mypyc-level subtype check (for IR types)
├── rt_subtype.py           # Runtime subtype check
├── sametype.py             # Same-type check for IR types
├── namegen.py              # C name generation
├── annotate.py             # Annotation utilities
├── errors.py               # Error reporting
│
├── ir/                     # Intermediate Representation
│   ├── ops.py              # All IR operation classes (Register, Value, BasicBlock, etc.)
│   ├── rtypes.py           # Runtime types (RType, RInstance, RTuple, etc.)
│   ├── func_ir.py          # FuncIR, FuncDecl, FuncSignature
│   ├── class_ir.py         # ClassIR: mypyc's class representation
│   ├── module_ir.py        # ModuleIR
│   ├── deps.py             # IR-level dependency tracking
│   └── pprint.py           # IR pretty printer
│
├── irbuild/                # mypy AST → IR translation
│   ├── main.py             # Entry point: build_ir()
│   ├── builder.py          # IRBuilder: core IR construction API
│   ├── visitor.py          # AST visitor dispatching to IR builders
│   ├── expression.py       # Expression IR generation
│   ├── statement.py        # Statement IR generation
│   ├── function.py         # Function/method IR generation
│   ├── classdef.py         # Class definition IR generation
│   ├── generator.py        # Generator/coroutine IR
│   ├── for_helpers.py      # For-loop IR optimizations
│   ├── ll_builder.py       # Low-level IR builder primitives
│   ├── mapper.py           # mypy type → IR type mapping
│   ├── prepare.py          # Pre-analysis pass
│   ├── specialize.py       # Specializations for built-in operations
│   ├── context.py          # Build context
│   └── ...                 # (other irbuild helpers)
│
├── codegen/                # IR → C code generation
│   ├── emit.py             # Emitter: writes C code
│   ├── emitfunc.py         # Function C code emission
│   ├── emitclass.py        # Class C code emission
│   ├── emitmodule.py       # Module C code emission
│   ├── emitwrapper.py      # Python/C wrapper generation
│   ├── cstring.py          # C string utilities
│   └── literals.py         # Literal value emission
│
├── transform/              # IR optimization passes
├── lower/                  # IR lowering passes
├── analysis/               # IR analysis (liveness, etc.)
├── primitives/             # Primitive operation definitions
└── lib-rt/                 # C runtime library (CPy.h and *.c files)
    ├── CPy.h               # Main C runtime header
    ├── misc_ops.c          # Miscellaneous C runtime functions
    ├── dict_ops.c          # dict operations
    ├── list_ops.c          # list operations
    ├── str_ops.c           # str operations
    ├── tuple_ops.c         # tuple operations
    └── ...                 # Other runtime C files
```

## Test Structure

```
mypy/test/                  # Python test infrastructure
├── testcheck.py            # Data-driven type checker tests (check-*.test files)
├── testfinegrained.py      # Fine-grained incremental tests
├── testdaemon.py           # dmypy daemon tests
├── testsemanal.py          # Semantic analysis tests
├── teststubgen.py          # stubgen tests
├── teststubtest.py         # stubtest tests
├── testcmdline.py          # Command-line tests
└── data.py                 # Test data parsing and DataDrivenTestCase

test-data/unit/             # Data-driven test fixtures (.test files)
├── check-*.test            # Type checker test cases
├── semanal-*.test          # Semantic analysis test cases
├── cmdline.test            # CLI argument test cases
└── stubgen*.test           # stubgen test cases

mypyc/test/                 # mypyc-specific tests
mypyc/test-data/            # mypyc test fixtures
```

## Code Organization Patterns

1. **Visitor pattern**: All AST processing uses `NodeVisitor` / `TypeVisitor` subclasses. The checker, semantic analyzer, and code generators all extend these visitors.

2. **Data-driven tests**: Most behavioral tests live in `.test` files under `test-data/unit/`. Each `[case testName]` block contains input Python, expected output, and optional flags. The `testcheck.py` / `data.py` infrastructure parses and runs these.

3. **Layered analysis**: Parsing → Semantic Analysis → Type Checking. Each layer produces structured output consumed by the next.

4. **Incremental state in `State`**: The `build.State` class tracks per-file processing state (parse tree, symbol table, type map, cache metadata) across incremental runs.

5. **Binary cache format**: Mypy uses a custom binary format (via `librt.internal`) for serializing and deserializing type information to `.mypy_cache/`, far faster than JSON for large codebases.
