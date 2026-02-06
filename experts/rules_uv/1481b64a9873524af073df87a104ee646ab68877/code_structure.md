# rules_uv - Code Structure

## Complete Directory Tree

```
rules_uv/
├── .bazelignore                 # Bazel ignore patterns
├── .bazelrc                     # Bazel configuration flags
├── .bazelversion                # Pin Bazel version
├── .gitattributes               # Git attribute configuration
├── .gitignore                   # Git ignore patterns
├── BUILD.bazel                  # Root build file
├── LICENSE                      # Apache 2.0 license
├── MODULE.bazel                 # Bzlmod module definition
├── WORKSPACE.bazel              # Legacy workspace (empty, uses bzlmod)
├── readme.md                    # User documentation
│
├── .bcr/                        # Bazel Central Registry configuration
│   └── README.md                # BCR publishing documentation
│
├── .github/                     # GitHub automation
│   └── workflows/
│       ├── automation-autorelease.yml  # Auto-release workflow
│       ├── ci.bazelrc           # CI-specific Bazel config
│       ├── ci.yml               # Continuous integration
│       ├── periodic-update-multitool.yml  # Update uv versions
│       ├── publish-to-bcr.yml   # BCR publishing workflow
│       ├── release.yml          # Release automation
│       └── release_prep.sh      # Release preparation script
│
├── dev/                         # Development tooling
│   └── BUILD.bazel              # Development build targets
│
├── uv/                          # Main ruleset implementation
│   ├── BUILD.bazel              # Visibility and exports
│   ├── pip.bzl                  # Public pip_compile API
│   ├── venv.bzl                 # Public venv creation API
│   │
│   └── private/                 # Private implementation details
│       ├── BUILD.bazel          # Private target definitions
│       ├── create_venv.sh       # Venv creation script template
│       ├── interpreter_path.bzl # Python interpreter helpers
│       ├── pip.bzl              # pip_compile implementation
│       ├── pip_compile.sh       # Compilation script template
│       ├── pip_compile_test.sh  # Diff test script template
│       ├── sync_venv.sh         # Venv sync script template
│       ├── transition_to_target.bzl  # Platform transition logic
│       ├── uv.lock.json         # rules_multitool lockfile for uv binaries
│       └── venv.bzl             # Venv implementation rules
│
└── examples/                    # Usage examples
    ├── multiple-inputs/         # Example with multiple requirements files
    │   ├── BUILD.bazel
    │   ├── MODULE.bazel
    │   ├── WORKSPACE.bazel
    │   ├── requirements.in
    │   ├── requirements.test.in
    │   └── requirements.txt
    │
    ├── multiple-pyruntimes/     # Example with multiple Python versions
    │   ├── BUILD.bazel
    │   ├── MODULE.bazel
    │   ├── WORKSPACE.bazel
    │   ├── requirements.in
    │   ├── requirements.txt
    │   ├── requirements_3_10.txt
    │   └── requirements_3_11.txt
    │
    └── typical/                 # Typical usage example
        ├── BUILD.bazel
        ├── MODULE.bazel
        ├── WORKSPACE.bazel
        ├── requirements.in
        ├── requirements.txt
        ├── requirements_linux.txt
        ├── requirements_twine.txt
        └── site_packages_extra/
            └── sitecustomize.py
```

## Module and Package Organization

### Public API Modules (`uv/`)

The `uv` directory contains the public-facing API that users import in their BUILD files:

**`uv/pip.bzl`** (106 lines):
- Exports the `pip_compile` macro
- High-level interface for requirements compilation
- Automatically creates three targets per invocation:
  - `[name]`: Runnable target to update requirements.txt
  - `[name].update`: Alias for compatibility with rules_python
  - `[name]_test`: Test target to validate requirements are current
- Handles inline requirements (list of strings) by generating temporary files
- Provides sensible defaults (`//:requirements.in`, `//:requirements.txt`)

**`uv/venv.bzl`** (6 lines):
- Minimal re-export module
- Exposes `create_venv` and `sync_venv` macros
- Acts as a stable public API facade

### Private Implementation (`uv/private/`)

The `private` directory contains the actual rule implementations and templates:

**`uv/private/pip.bzl`** (149 lines):
- Core pip compilation logic
- Defines two Bazel rules:
  - `pip_compile`: Creates executable for updating requirements
  - `pip_compile_test`: Creates test for validating requirements
- Manages Python toolchain integration via `PyRuntimeInfo`
- Handles template expansion with proper substitutions
- Implements runfiles collection for hermetic execution
- Default arguments: `--generate-hashes`, `--emit-index-url`, `--no-strip-extras`

**`uv/private/venv.bzl`** (75 lines):
- Virtual environment creation and synchronization
- Defines internal `_venv` rule with template-based approach
- Two public functions:
  - `create_venv`: Fresh venv creation
  - `sync_venv`: Atomic venv synchronization
- Supports custom destination folders and site-packages injection
- Manages Python runtime files in runfiles tree

**`uv/private/interpreter_path.bzl`** (6 lines):
- Helper function to abstract Python interpreter location
- Handles both hermetic (bundled) and system Python toolchains
- Returns either `interpreter.short_path` or `interpreter_path` depending on toolchain type

**`uv/private/transition_to_target.bzl`** (16 lines):
- Bazel configuration transition
- Ensures uv binary is built for target platform, not exec platform
- Critical for cross-compilation scenarios
- Converts `--platforms` to `--extra_execution_platforms`

**`uv/private/uv.lock.json`** (55 lines):
- rules_multitool lockfile
- Defines uv binary downloads for all supported platforms:
  - Linux: x86_64, arm64 (musl/gnu)
  - macOS: x86_64, arm64
  - Windows: x86_64, arm64
- Currently pins uv version 0.8.12
- Each entry includes URL, SHA256 hash, and platform constraints

### Execution Templates (`uv/private/*.sh`)

Shell script templates that get expanded with Bazel substitutions:

**`pip_compile.sh`** (14 lines):
- Simple wrapper for `uv pip compile`
- Takes requirements_in and produces requirements_txt
- Passes through additional arguments from Bazel
- Template variables: `{{uv}}`, `{{requirements_in}}`, `{{requirements_txt}}`, `{{args}}`

**`pip_compile_test.sh`** (30 lines):
- Creates temporary copy of requirements.txt
- Runs uv pip compile to generate fresh version
- Diffs against checked-in version
- Exits with error and helpful message if out of sync
- Uses `--quiet` and `--no-cache` for test reliability

**`create_venv.sh`** (52 lines):
- Creates new virtual environment with `uv venv`
- Installs packages from requirements.txt with `uv pip install`
- Handles custom venv paths (defaults to `venv`)
- Validates venv target path for safety
- Copies site_packages_extra_files if specified
- Makes copied files writable (handles write-protected inputs)
- Provides activation instructions to user

**`sync_venv.sh`** (48 lines):
- Similar to create_venv but uses `uv pip sync`
- `--allow-existing` flag permits updating existing venvs
- Ensures venv exactly matches requirements (removes extras)
- More deterministic for CI/CD workflows

## Main Source Directories and Purposes

### `/uv/` - Public API Surface
**Purpose**: Provides stable, documented interfaces for end users

**Key Responsibilities**:
- Macro definitions with parameter validation
- Default value management
- Target naming conventions
- User-facing documentation via docstrings

**Design Pattern**: Facade pattern - simple interfaces hiding complex implementations

### `/uv/private/` - Implementation Details
**Purpose**: Contains all implementation logic that users shouldn't directly depend on

**Key Responsibilities**:
- Bazel rule definitions with full attribute specifications
- Provider implementations (DefaultInfo, RunEnvironmentInfo, PyRuntimeInfo)
- Toolchain resolution and integration
- Template management and expansion
- Runfiles tree construction
- Platform and configuration transitions

**Design Pattern**: Separation of concerns - implementation can change without breaking user code

### `/examples/` - Reference Implementations
**Purpose**: Demonstrates real-world usage patterns

**Categories**:
- **typical**: Standard single-platform or multi-platform setup
- **multiple-inputs**: Using data attribute for additional requirements files
- **multiple-pyruntimes**: Generating requirements for different Python versions

Each example is a complete, runnable Bazel workspace with MODULE.bazel and BUILD files.

## Key Files and Their Roles

### Configuration Files

**`MODULE.bazel`** (19 lines):
- Defines rules_uv as a bzlmod module
- Declares dependencies: bazel_skylib, platforms, rules_multitool, rules_python
- Configures rules_multitool extension with uv.lock.json
- Compatibility level: 1

**`.bazelversion`**:
- Pins Bazel version for consistency
- Ensures all developers use compatible Bazel version

**`.bazelrc`**:
- Shared Bazel configuration flags
- Sets up common options for all builds

### Core Rule Files

**`uv/pip.bzl`** and **`uv/private/pip.bzl`**:
- Together implement the pip_compile functionality
- Public file provides macro, private file provides rule
- Macro layer adds convenience (default values, test creation)
- Rule layer provides Bazel integration (toolchains, actions, providers)

**`uv/venv.bzl`** and **`uv/private/venv.bzl`**:
- Parallel structure for venv functionality
- Both create_venv and sync_venv use same underlying `_venv` rule
- Differentiated only by shell script template

### Binary Management

**`uv/private/uv.lock.json`**:
- Critical for reproducibility
- Pins exact uv version and checksums
- Managed by rules_multitool
- Updated via GitHub Actions workflow (`periodic-update-multitool.yml`)

### Build Files

**Root `BUILD.bazel`**:
- Defines package-level settings
- Exports files for use by rules
- Visibility declarations

**`uv/BUILD.bazel`**:
- Exports public API files (pip.bzl, venv.bzl)
- Makes private directory visible to subpackages only

**`uv/private/BUILD.bazel`**:
- Exports shell script templates as filegroups
- Makes templates available to rule implementations

## Code Organization Patterns

### Layered Architecture
1. **User Macros** (pip.bzl, venv.bzl) - high-level, convenient, opinionated
2. **Rule Implementations** (private/*.bzl) - low-level, flexible, complete
3. **Execution Scripts** (private/*.sh) - runtime, portable, minimal

### Template-Based Execution
Rules use template expansion rather than inline script generation:
- Templates are checked into source control
- Easy to test and iterate independently
- Clear separation between Bazel logic and shell logic
- Substitution variables like `{{uv}}` are replaced at analysis time

### Hermetic Binary Management
Rather than requiring uv on PATH:
- rules_multitool downloads platform-specific binaries
- Binaries become part of runfiles
- Scripts use `{{uv}}` substitution for binary path
- Works identically across all developer machines and CI

### Python Toolchain Integration
Deep integration with rules_python:
- Uses `@bazel_tools//tools/python:toolchain_type`
- Resolves PyRuntimeInfo for interpreter path
- Supports both hermetic and system Python toolchains
- Respects Python version from toolchain configuration

### Multi-Target Macros
The pip_compile macro creates three related targets:
- Primary target (executable) for updating
- `.update` alias for rules_python compatibility
- `_test` target for validation
This pattern provides discoverability and convenience.
