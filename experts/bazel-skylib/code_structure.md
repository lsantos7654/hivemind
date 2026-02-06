# Bazel Skylib - Code Structure

## Repository Location
`/Users/santos/projects/bazel/bazel-skylib`

## Complete Directory Tree

```
bazel-skylib/
├── lib/                              # Core utility modules (PUBLIC API)
│   ├── collections.bzl               # List manipulation: after_each, before_each, uniq
│   ├── dicts.bzl                     # Dictionary ops: add, omit, pick
│   ├── new_sets.bzl                  # Modern set implementation (preferred)
│   ├── old_sets.bzl                  # Deprecated set implementation
│   ├── sets.bzl                      # Alias to new_sets.bzl
│   ├── partial.bzl                   # Functional programming: partial application
│   ├── paths.bzl                     # POSIX path manipulation
│   ├── shell.bzl                     # Shell command utilities: quote, array_literal
│   ├── selects.bzl                   # Config selection: with_or, config_setting_group
│   ├── structs.bzl                   # Struct utilities: to_dict
│   ├── types.bzl                     # Type checking: is_list, is_string, etc.
│   ├── versions.bzl                  # Bazel version checking and comparison
│   ├── unittest.bzl                  # Testing framework (unit, analysis, loading)
│   ├── subpackages.bzl               # native.subpackages() wrapper
│   └── modules.bzl                   # bzlmod module extension helpers
│
├── rules/                            # Build rules (PUBLIC API)
│   ├── copy_file.bzl                 # Copy single files with renaming
│   ├── copy_directory.bzl            # Recursive directory copying
│   ├── write_file.bzl                # Generate text files from content
│   ├── run_binary.bzl                # Execute binaries as build actions
│   ├── diff_test.bzl                 # Test comparing two files
│   ├── build_test.bzl                # Test that targets build successfully
│   ├── analysis_test.bzl             # Test rule analysis phase
│   ├── expand_template.bzl           # Template substitution
│   ├── select_file.bzl               # Select file from multi-output target
│   ├── native_binary.bzl             # Wrap pre-built executables
│   ├── common_settings.bzl           # Standard build settings (flags)
│   │
│   ├── directory/                    # Directory metadata rules (v1.7.0+)
│   │   ├── directory.bzl             # Create DirectoryInfo provider
│   │   ├── glob.bzl                  # Filter files from directories
│   │   ├── subdirectory.bzl          # Access subdirectory metadata
│   │   ├── providers.bzl             # DirectoryInfo provider definition
│   │   └── private/                  # Internal implementation
│   │       ├── directory.bzl
│   │       └── glob.bzl
│   │
│   └── private/                      # Internal implementations (NOT PUBLIC)
│       ├── bzl_library.bzl           # bzl_library rule implementation
│       ├── copy_file_private.bzl     # Platform-specific copy logic
│       ├── copy_directory_private.bzl
│       ├── write_file_private.bzl
│       ├── copy_common.bzl           # Shared copy utilities
│       └── maprule_util.bzl          # Batch processing utilities
│
├── tests/                            # Test suite
│   ├── collections_test.bzl          # Unit tests for collections module
│   ├── dicts_test.bzl                # Unit tests for dicts module
│   ├── paths_test.bzl                # Unit tests for paths module
│   ├── shell_test.bzl                # Unit tests for shell module
│   ├── sets_test.bzl                 # Unit tests for sets module
│   ├── types_test.bzl                # Unit tests for types module
│   ├── partial_test.bzl              # Unit tests for partial module
│   ├── selects_test.bzl              # Unit tests for selects module
│   ├── structs_test.bzl              # Unit tests for structs module
│   ├── versions_test.bzl             # Unit tests for versions module
│   ├── unittest_test.bzl             # Meta-tests for testing framework
│   ├── copy_file_test.bzl            # Tests for copy_file rule
│   ├── diff_test_test.bzl            # Tests for diff_test rule
│   ├── write_file_test.bzl           # Tests for write_file rule
│   ├── expand_template_test.bzl      # Tests for expand_template rule
│   ├── run_binary_test.bzl           # Tests for run_binary rule
│   ├── common_settings_test.bzl      # Tests for build settings
│   ├── BUILD                         # Test targets
│   └── directory/                    # Tests for directory rules
│
├── gazelle/                          # Gazelle language extension
│   └── bzl/                          # .bzl file analysis plugin
│       ├── README.md                 # Plugin documentation
│       ├── BUILD.bazel               # Gazelle plugin targets
│       └── testdata/                 # Test fixtures for Gazelle
│           ├── simple/               # Basic test case
│           ├── has_deps/             # Dependency tracking test
│           ├── has_test/             # Test file handling
│           └── fix_deps/             # Dependency fixing test
│
├── toolchains/                       # Toolchain definitions
│   └── unittest/                     # Test execution toolchains
│       ├── BUILD                     # Toolchain registration
│       ├── defs.bzl                  # Toolchain definitions
│       ├── cmd.bat.tpl               # Windows batch template
│       └── bash.sh.tpl               # Unix shell template
│
├── docs/                             # Generated documentation
│   ├── bzl_library_doc.md            # bzl_library API docs
│   ├── collections_doc.md            # collections module docs
│   ├── dicts_doc.md                  # dicts module docs
│   ├── paths_doc.md                  # paths module docs
│   ├── shell_doc.md                  # shell module docs
│   ├── sets_doc.md                   # sets module docs
│   ├── partial_doc.md                # partial module docs
│   ├── selects_doc.md                # selects module docs
│   ├── structs_doc.md                # structs module docs
│   ├── types_doc.md                  # types module docs
│   ├── unittest_doc.md               # unittest module docs
│   ├── versions_doc.md               # versions module docs
│   ├── copy_file_doc.md              # copy_file rule docs
│   ├── copy_directory_doc.md         # copy_directory rule docs
│   ├── write_file_doc.md             # write_file rule docs
│   ├── run_binary_doc.md             # run_binary rule docs
│   ├── diff_test_doc.md              # diff_test rule docs
│   ├── build_test_doc.md             # build_test rule docs
│   ├── expand_template_doc.md        # expand_template rule docs
│   ├── native_binary_doc.md          # native_binary rule docs
│   ├── common_settings_doc.md        # common_settings rules docs
│   └── maintainers_guide.md          # Release and maintenance guide
│
├── distribution/                     # Release packaging
│   ├── BUILD                         # Distribution targets
│   └── *.bzl                         # Packaging utilities
│
├── .bcr/                             # Bazel Central Registry config
│   ├── metadata.json                 # BCR metadata
│   ├── presubmit.yml                 # BCR presubmit tests
│   └── source.json                   # Source configuration
│
├── .bazelci/                         # Buildkite CI configuration
│   └── presubmit.yml                 # CI job definitions
│
├── .github/                          # GitHub configuration
│   ├── workflows/                    # GitHub Actions
│   └── ISSUE_TEMPLATE/               # Issue templates
│
├── lib.bzl                           # DEPRECATED: Old unified loader
├── bzl_library.bzl                   # Public bzl_library wrapper
├── skylark_library.bzl               # Alternative library aggregation
├── workspace.bzl                     # WORKSPACE setup utilities
├── version.bzl                       # Version constant (1.8.2)
│
├── MODULE.bazel                      # bzlmod configuration
├── WORKSPACE                         # Legacy WORKSPACE file
├── WORKSPACE.bzlmod                  # Minimal bzlmod workspace
├── BUILD                             # Root BUILD file
│
├── README.md                         # Main documentation
├── CHANGELOG.md                      # Release history
├── LICENSE                           # Apache 2.0
├── AUTHORS                           # Author list
├── CONTRIBUTORS                      # Contributor list
├── CONTRIBUTING.md                   # Contribution guidelines
└── CODEOWNERS                        # Code ownership
```

## Module Organization Patterns

### Public API Boundary
- **lib/*.bzl**: All files are public API, each exports a struct
- **rules/*.bzl**: All top-level files are public rules
- **rules/private/**: Internal implementation, DO NOT import directly
- **rules/directory/private/**: Internal directory rule implementation

### Module Export Pattern
Each lib/ module exports a struct containing related functions:
```starlark
# Example: lib/paths.bzl
paths = struct(
    basename = _basename,
    dirname = _dirname,
    join = _join,
    normalize = _normalize,
    # ... more functions
)
```

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Code                             │
├─────────────────────────────────────────────────────────┤
│  Public API: lib/*.bzl, rules/*.bzl, bzl_library.bzl    │
├─────────────────────────────────────────────────────────┤
│  Private Implementation: rules/private/*.bzl            │
├─────────────────────────────────────────────────────────┤
│  Platform Toolchains: toolchains/unittest/              │
├─────────────────────────────────────────────────────────┤
│  Bazel Native: ctx.actions, native.*, etc.              │
└─────────────────────────────────────────────────────────┘
```

## Key Files and Their Roles

### Entry Points
| File | Purpose |
|------|---------|
| `lib/*.bzl` | Individual utility modules - primary entry point |
| `rules/*.bzl` | Individual build rules |
| `bzl_library.bzl` | Rule for aggregating Starlark sources |
| `workspace.bzl` | WORKSPACE setup (toolchain registration) |
| `MODULE.bazel` | bzlmod dependency configuration |

### Configuration Files
| File | Purpose |
|------|---------|
| `MODULE.bazel` | bzlmod module definition, version 1.8.2 |
| `WORKSPACE` | Legacy workspace configuration |
| `version.bzl` | Version constant export |
| `.bazelversion` | Required Bazel version |
| `.bazelignore` | Directories excluded from Bazel |

### Deprecated Files
| File | Status |
|------|--------|
| `lib.bzl` | DEPRECATED - bulk import no longer works |
| `lib/old_sets.bzl` | DEPRECATED - use new_sets.bzl |

## Code Organization Patterns

### Platform-Specific Implementation
Rules like copy_file, diff_test automatically handle platform differences:
```
rules/copy_file.bzl (public API)
    └── rules/private/copy_file_private.bzl (implementation)
        ├── _bash_copy_file() for Unix
        └── _bat_copy_file() for Windows
```

### Testing Organization
Each module has corresponding tests:
```
lib/paths.bzl       →  tests/paths_test.bzl
lib/shell.bzl       →  tests/shell_test.bzl
rules/copy_file.bzl →  tests/copy_file_test.bzl
```

### Documentation Generation
Stardoc generates docs from source:
```
lib/paths.bzl       →  docs/paths_doc.md
rules/copy_file.bzl →  docs/copy_file_doc.md
```

## Separation of Concerns

| Concern | Location |
|---------|----------|
| Data structures | lib/collections.bzl, lib/dicts.bzl, lib/new_sets.bzl |
| Path handling | lib/paths.bzl |
| Shell safety | lib/shell.bzl |
| Type checking | lib/types.bzl |
| Testing | lib/unittest.bzl |
| Version compat | lib/versions.bzl |
| Configuration | lib/selects.bzl, rules/common_settings.bzl |
| File operations | rules/copy_file.bzl, rules/write_file.bzl |
| Build validation | rules/build_test.bzl, rules/diff_test.bzl |
| Execution | rules/run_binary.bzl, rules/native_binary.bzl |

## File Naming Conventions

- `*_test.bzl`: Test files
- `*_doc.md`: Generated documentation
- `*_private.bzl`: Internal implementation files
- `*.bzl`: Starlark source files
- `*.md`: Documentation
- `*.tpl`: Template files (toolchains)
