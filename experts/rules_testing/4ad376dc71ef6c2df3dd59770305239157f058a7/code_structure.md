# Code Structure and Organization

## Complete Directory Tree

```
rules_testing/
├── .bazelci/              # Bazel CI configuration
├── .bcr/                  # Bazel Central Registry metadata
├── .github/               # GitHub Actions and workflows
├── lib/                   # Main source code (public API)
│   ├── private/          # Internal implementation details
│   ├── analysis_test.bzl # Analysis test framework
│   ├── test_suite.bzl    # Test aggregation
│   ├── truth.bzl         # Truth-style assertions entry point
│   ├── unit_test.bzl     # Unit test support
│   ├── unittest.bzl      # Legacy compatibility layer
│   ├── util.bzl          # Testing utilities
│   └── BUILD             # Build definitions
├── tests/                 # Test suite for the library itself
│   ├── default_info_subject/
│   ├── matching/
│   ├── struct_subject/
│   ├── testdata/
│   ├── analysis_test_tests.bzl
│   ├── truth_tests.bzl
│   ├── unit_test_tests.bzl
│   ├── unittest_tests.bzl
│   └── BUILD
├── docs/                  # Sphinx-based documentation
│   ├── source/
│   │   ├── api/          # API reference documentation
│   │   ├── _static/      # Static assets
│   │   ├── analysis_tests.md
│   │   ├── best_practices.md
│   │   ├── conf.py       # Sphinx configuration
│   │   ├── guides.md
│   │   ├── index.md
│   │   ├── test_suite.md
│   │   ├── truth.md
│   │   └── unit_tests.md
│   ├── requirements.in
│   ├── requirements.txt
│   ├── run_sphinx_build.sh
│   └── BUILD
├── docgen/                # Documentation generation tooling
│   ├── docgen.bzl
│   ├── func_template.vm
│   ├── header_template.vm
│   ├── provider_template.vm
│   ├── rule_template.vm
│   └── BUILD
├── e2e/                   # End-to-end integration tests
│   └── bzlmod/
│       ├── BUILD.bazel
│       ├── MODULE.bazel
│       ├── tests.bzl
│       └── WORKSPACE
├── MODULE.bazel           # Bzlmod module definition
├── WORKSPACE.bazel        # Legacy WORKSPACE setup
├── WORKSPACE.bzlmod       # Empty marker for bzlmod
├── BUILD                  # Root build file
├── .bazelrc              # Bazel configuration
├── .bazelignore          # Files to ignore
├── README.md             # Project overview
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # Contribution guidelines
├── RELEASING.md          # Release process
├── AUTHORS               # Project authors
├── CODEOWNERS           # Code ownership
├── LICENSE              # Apache 2.0 license
└── addlicense.sh        # License header script
```

## Module and Package Organization

### lib/ - Public API Surface

The `lib/` directory contains the public API that users import in their tests. Each `.bzl` file is designed as a focused entry point:

**Primary Entry Points**:
- `analysis_test.bzl`: Exports `analysis_test()` function and convenience `test_suite()` alias for creating tests that run during analysis phase
- `truth.bzl`: Exports the `truth` struct (containing `truth.expect`), `matching` utilities, and `subjects` constructors for direct subject creation
- `unit_test.bzl`: Exports `unit_test()` for testing generic Starlark code
- `test_suite.bzl`: Exports `test_suite()` for aggregating multiple tests into a single target
- `util.bzl`: Exports utility functions like `helper_target()`, `runfiles_paths()`, `merge_kwargs()`, etc.
- `unittest.bzl`: Compatibility layer for skylib's unittest.bzl, allowing gradual migration

### lib/private/ - Implementation Layer

The `lib/private/` directory contains all internal implementation details. This separation ensures users only depend on stable public APIs.

**Core Framework Implementation**:
- `analysis_test.bzl`: Implements the actual analysis test rule, including the test harness, environment setup, and failure collection
- `expect.bzl`: Implements the `Expect` class, which is the factory for creating all subject types
- `expect_meta.bzl`: Implements `ExpectMeta`, which tracks context information (call chains, error metadata) for better error messages

**Subject Implementations** (each wraps a specific type):
- `target_subject.bzl`: `TargetSubject` for asserting on Bazel targets
- `action_subject.bzl`: `ActionSubject` for asserting on actions
- `file_subject.bzl`: `FileSubject` for asserting on files
- `runfiles_subject.bzl`: `RunfilesSubject` for asserting on runfiles
- `default_info_subject.bzl`: `DefaultInfoSubject` for DefaultInfo provider
- `depset_file_subject.bzl`: `DepsetFileSubject` for depsets of files
- `collection_subject.bzl`: `CollectionSubject` for lists and collections
- `dict_subject.bzl`: `DictSubject` for dictionaries
- `struct_subject.bzl`: `StructSubject` for structs
- `str_subject.bzl`: `StrSubject` for strings
- `int_subject.bzl`: `IntSubject` for integers
- `bool_subject.bzl`: `BoolSubject` for booleans
- `label_subject.bzl`: `LabelSubject` for labels
- `execution_info_subject.bzl`: `ExecutionInfoSubject` for execution info
- `instrumented_files_info_subject.bzl`: `InstrumentedFilesInfoSubject` for coverage info
- `run_environment_info_subject.bzl`: `RunEnvironmentInfoSubject` for run environment

**Utility Modules**:
- `matching.bzl`: Implements predicate-based matching (Matcher interface and implementations)
- `check_util.bzl`: Implements high-level assertion checking and failure reporting
- `compare_util.bzl`: Implements comparison logic for various types (lists, dicts, depsets)
- `failure_messages.bzl`: Implements error message formatting
- `ordered.bzl`: Utilities for ordered comparisons
- `truth_common.bzl`: Shared utilities across truth implementation
- `util.bzl`: Internal utility functions

## Main Source Directories and Their Purposes

### lib/ - The Testing Framework Core

Contains the entire testing framework implementation. Users should only load from the top-level `.bzl` files, never from `private/`. The structure follows a clear layering:

1. **Top-level**: Public API exports
2. **private/**: Implementation details

This organization allows the project to refactor internals without breaking users.

### tests/ - Self-Testing Suite

The tests directory contains the project's own test suite, demonstrating how to use the framework and ensuring it works correctly. Key test files:

- `truth_tests.bzl`: Tests for the Truth assertion library, covering all subject types
- `analysis_test_tests.bzl`: Tests for the analysis test framework itself
- `unit_test_tests.bzl`: Tests for unit test support
- `unittest_tests.bzl`: Tests for the unittest.bzl compatibility layer

Subdirectories like `default_info_subject/`, `matching/`, and `struct_subject/` contain focused test suites for specific components.

### docs/ - User Documentation

Contains Sphinx-based documentation that is published to ReadTheDocs. Structure:

- `source/`: Markdown/reStructuredText source files
- `source/api/`: Auto-generated API reference (from Stardoc)
- `conf.py`: Sphinx configuration
- `requirements.txt`: Python dependencies for doc generation

The documentation is built and published automatically on commits.

### docgen/ - Documentation Generation

Contains Velocity templates and Starlark code for generating API documentation from source code using Stardoc. This ensures API docs stay synchronized with implementation.

### e2e/ - Integration Tests

End-to-end tests that verify the framework works in realistic scenarios, particularly with bzlmod. The `bzlmod/` subdirectory contains a minimal project that consumes rules_testing as a dependency.

## Key Files and Their Roles

### MODULE.bazel
The bzlmod module definition. Declares dependencies on bazel_skylib, platforms, and rules_license. Development dependencies include stardoc and rules_python for documentation.

### WORKSPACE.bazel
Legacy workspace setup for non-bzlmod users. Fetches all dependencies via http_archive and sets up Python toolchains for documentation generation.

### BUILD (root)
The root BUILD file. Contains targets for the entire repository, including license checks and potentially aggregate test targets.

### lib/BUILD
Defines build targets for the library itself, likely including exports for bzlmod visibility.

### lib/private/BUILD
May contain internal visibility restrictions to prevent users from depending on private APIs.

## Code Organization Patterns

### Separation of Public and Private APIs

The strict separation between `lib/*.bzl` (public) and `lib/private/*.bzl` (private) is a key organizational pattern. This allows:
- Clear contract for users
- Freedom to refactor internals
- Better testing (tests can access private APIs for white-box testing)

### Subject Pattern

Each type has a corresponding `*_subject.bzl` file that implements:
1. A constructor (usually `new()`) that takes the actual value and `ExpectMeta`
2. Assertion methods specific to that type
3. Methods to access child subjects (e.g., `TargetSubject.runfiles()` returns `RunfilesSubject`)

This creates a fluent, chainable API.

### Factory Pattern

The `Expect` class acts as a factory for all subject types via methods like:
- `that_target()` → `TargetSubject`
- `that_action()` → `ActionSubject`
- `that_str()` → `StrSubject`

This centralized factory ensures consistent error tracking and metadata propagation.

### Metadata Threading

`ExpectMeta` is threaded through all subject creations, carrying context about:
- The test environment
- The call chain (for error messages)
- Custom failure handlers
- Provider factories

This allows rich error messages that show the full context of where an assertion failed.

### Utilities Separation

Utility functions are separated by audience:
- `lib/util.bzl`: Public utilities for test authors
- `lib/private/util.bzl`: Internal utilities for the framework

### Structured Testing

Tests are organized into focused suites:
- Each component has its own test file
- Related tests are grouped in subdirectories
- The self-hosting nature (testing framework testing itself) provides real-world usage examples

### Documentation Co-location

Documentation lives close to code:
- Docstrings in `.bzl` files
- Separate `docs/` for guides
- `docgen/` for generating API docs from docstrings

This ensures documentation stays synchronized with implementation.
