# Bazel Central Registry - Code Structure

## Complete Directory Tree

```
bazel-central-registry/
├── .agent/                          # Agent workflow definitions
│   └── workflows/
│       ├── add_module_scaffolding.md
│       ├── validate_module.md
│       └── verify_module_build.md
├── .bazelci/                        # Bazel CI configuration
├── .gemini/                         # Gemini-specific configurations
│   └── styleguide.md
├── .github/                         # GitHub Actions workflows and config
│   └── workflows/
│       ├── dismiss_approvals.yml    # Auto-dismiss stale approvals
│       ├── enforce_tooling_sync.yml # Ensure tooling consistency
│       ├── generate_module_diff.yml # Show module version changes
│       ├── handle_comment.yml       # Process PR comments
│       ├── notify_maintainers.yml   # Ping module maintainers
│       ├── pre-commit.yml           # Pre-commit hook validation
│       ├── review_prs.yml           # Automated PR review logic
│       ├── skip_check.yml           # Handle @bazel-io skip_check commands
│       ├── stale.yml                # Stale PR management
│       ├── trigger_bcr_frontend_rebuild.yml
│       ├── trigger_bcr_ui_rebuild.yml
│       └── update_requirements.yml  # Python dependency updates
├── docs/                            # Documentation
│   ├── README.md                    # Contribution guidelines
│   ├── attestations.md              # Build attestation documentation
│   ├── bcr-policies.md              # Registry policies and maintainer info
│   ├── code-of-conduct.md           # Community code of conduct
│   ├── contributing.md              # How to contribute
│   ├── mcp.md                       # MCP server documentation
│   └── stardoc.md                   # Stardoc API documentation
├── modules/                         # All Bazel modules (977+ modules)
│   ├── <module-name>/               # One directory per module
│   │   ├── metadata.json            # Module metadata (maintainers, versions, etc.)
│   │   └── <version>/               # One directory per version (e.g., 1.8.3/)
│   │       ├── MODULE.bazel         # Module definition with dependencies
│   │       ├── source.json          # Source archive URL and integrity hash
│   │       ├── presubmit.yml        # CI/CD test configuration
│   │       ├── attestations.json    # [Optional] Build attestations
│   │       ├── patches/             # [Optional] Source code patches
│   │       │   └── *.patch
│   │       └── overlay/             # [Optional] Additional BUILD files
│   │           ├── BUILD.bazel
│   │           └── MODULE.bazel
│   ├── abseil-cpp/                  # Example: Google Abseil C++ library
│   │   ├── metadata.json
│   │   ├── 20260107.0/
│   │   │   ├── MODULE.bazel
│   │   │   ├── presubmit.yml
│   │   │   └── source.json
│   │   └── ... (21 versions)
│   ├── rules_python/                # Example: Python rules for Bazel
│   │   ├── metadata.json
│   │   ├── 1.8.3/
│   │   │   ├── MODULE.bazel
│   │   │   ├── presubmit.yml
│   │   │   ├── source.json
│   │   │   └── patches/
│   │   │       └── module_dot_bazel_version.patch
│   │   └── ... (89 versions)
│   └── [974+ more modules]
├── tools/                           # Helper scripts and utilities
│   ├── bcr-mirror/                  # BCR mirror tooling
│   │   └── README.md
│   ├── bzlmod_migration_test_examples/  # Migration examples
│   │   ├── go_extension/
│   │   ├── maven_extensions/
│   │   ├── module_extension/
│   │   ├── py_extension/
│   │   └── simple_module_deps/
│   ├── code-agent/                  # Code agent integration
│   │   └── README.md
│   ├── add_module.py                # Interactive module addition tool
│   ├── attestations.py              # Attestation handling library
│   ├── bazel-vet                    # Bazel vetting script
│   ├── bcr_validation.py            # Module validation (core tool)
│   ├── BUILD                        # Bazel build definitions for tools
│   ├── calc_integrity.py            # Calculate integrity hashes
│   ├── mcp_server.py                # MCP server implementation
│   ├── migrate_to_bzlmod.py         # WORKSPACE to Bzlmod migration
│   ├── module_analyzer.py           # Module importance analysis (PageRank)
│   ├── module_selector.py           # Module selection with patterns
│   ├── module_selector_test.py      # Tests for module selector
│   ├── package.json                 # npm package configuration
│   ├── pnpm-lock.yaml               # npm dependency lockfile
│   ├── print_all_src_urls.py        # Export all source URLs
│   ├── README.md                    # Tools documentation
│   ├── registry.py                  # Core registry library (594 lines)
│   ├── requirements.in              # Python dependencies (unpinned)
│   ├── requirements_lock.txt        # Python dependencies (pinned)
│   ├── setup_presubmit_repos.py     # Presubmit environment setup
│   ├── slsa.py                      # SLSA attestation verification
│   ├── sync_to_gcs.sh               # Google Cloud Storage sync
│   ├── update_integrity.py          # Update integrity hashes
│   ├── update_integrity_test.sh     # Test integrity updates
│   ├── verify_stable_archives.py    # Verify GitHub archive stability
│   └── version_test.py              # Version parsing tests
├── .bazelignore                     # Bazel ignore patterns
├── .bazelversion                    # Required Bazel version
├── .editorconfig                    # Editor configuration
├── .git-blame-ignore-revs           # Git blame ignore list
├── .gitattributes                   # Git attributes
├── .gitignore                       # Git ignore patterns
├── .pre-commit-config.yaml          # Pre-commit hook configuration
├── .ruff.toml                       # Ruff Python linter config
├── AUTHORS                          # Project authors
├── BUILD                            # Root BUILD file (metadata validation)
├── CODEOWNERS                       # GitHub code owners
├── GEMINI.md                        # Gemini AI integration docs
├── LICENSE                          # Apache 2.0 license
├── MODULE.bazel                     # Root module definition for BCR itself
├── README.md                        # Main repository documentation
├── WORKSPACE                        # Empty (BCR uses Bzlmod exclusively)
├── bazel_registry.json              # Registry configuration (mirrors)
├── incompatible_flags.yml           # Incompatible flags for testing
└── metadata.schema.json             # JSON schema for metadata validation
```

## Module and Package Organization

### Root Level Organization

The repository is organized into four primary functional areas:

1. **Module Storage** (`modules/`): The core data structure containing all Bazel modules
2. **Tooling** (`tools/`): Management and validation utilities
3. **Documentation** (`docs/`): Policies, guides, and integration docs
4. **Automation** (`.github/workflows/`): CI/CD and automated workflows

### Module Directory Structure

Each module follows a standardized two-level hierarchy:

```
modules/<module-name>/
├── metadata.json                    # Required: Module-level metadata
└── <version>/                       # One directory per published version
    ├── MODULE.bazel                 # Required: Module definition
    ├── source.json                  # Required: Source archive location
    ├── presubmit.yml                # Required: Testing configuration
    ├── patches/                     # Optional: Source code modifications
    ├── overlay/                     # Optional: Additional Bazel files
    └── attestations.json            # Optional: Build attestations
```

**Key Files in Module Versions:**

- **MODULE.bazel**: Defines module name, version, compatibility level, dependencies (bazel_dep), and module extensions
- **source.json**: Specifies source archive URL, integrity hash (SHA-256), strip_prefix, patches with their hashes, and patch_strip level
- **presubmit.yml**: CI configuration following Bazel CI syntax with matrix (platforms, Bazel versions), tasks (build_targets, test_targets), and bcr_test_module specifications
- **patches/**: Unified diff patches applied to source archives before building
- **overlay/**: Complete directory trees overlaid onto extracted sources, typically providing BUILD files for non-Bazel projects

### Tools Directory Structure

The `tools/` directory contains the core implementation of registry management:

**Core Libraries:**
- `registry.py` (594 lines): Central library providing Registry class with methods for module metadata access, version parsing, and file path resolution
- `attestations.py`: Attestation file handling
- `slsa.py`: SLSA provenance verification
- `verify_stable_archives.py`: GitHub archive stability checks

**Command-Line Tools:**
- `add_module.py`: Interactive wizard for adding modules (depends on registry.py, bcr_validation.py)
- `bcr_validation.py`: Comprehensive validation suite (47KB, executable)
- `calc_integrity.py`: Integrity hash calculator for URLs and local files
- `update_integrity.py`: Update source.json integrity values
- `migrate_to_bzlmod.py`: WORKSPACE to MODULE.bazel migration assistant (43KB)
- `module_selector.py`: Pattern-based module selection with wildcards
- `module_analyzer.py`: PageRank-based module importance analysis
- `setup_presubmit_repos.py`: Local presubmit environment reproduction
- `print_all_src_urls.py`: Export all source URLs for mirroring

**Integration Tools:**
- `mcp_server.py`: FastMCP-based server for AI agent integration
- `bazel-vet`: Bazel vetting utility

### Main Source Directories

**`modules/`**: Contains 977+ modules including:
- **Native Bazel Rulesets**: rules_python, rules_go, rules_jvm_external, rules_docker, rules_kotlin, rules_rust, rules_swift, etc.
- **Aspect Rules**: aspect_rules_js, aspect_rules_ts, aspect_rules_lint, aspect_rules_py, etc.
- **C/C++ Libraries**: abseil-cpp, boost (modular), protobuf, grpc, opencv, fmt, spdlog, etc.
- **Build Tools**: buildifier, buildozer, gazelle variants
- **Specialized Libraries**: rules for various languages and frameworks

**`docs/`**: Comprehensive documentation including contribution guidelines, BCR policies, attestation specifications, and MCP server usage.

**`.github/workflows/`**: 12 GitHub Actions workflows handling PR lifecycle, maintainer notifications, presubmit execution, and registry synchronization.

## Key Files and Their Roles

### Registry Configuration

- **bazel_registry.json**: Defines mirror URLs for source archives (currently empty array, but supports adding mirrors)
- **metadata.schema.json**: JSON Schema validating module metadata.json files with required fields (homepage, versions, maintainers, repository) and optional fields (yanked_versions, deprecated)
- **incompatible_flags.yml**: Lists incompatible flags for Bazel forward-compatibility testing, mapping flags to applicable Bazel version ranges

### Root Build Configuration

- **MODULE.bazel**: Defines the BCR repository itself as a Bazel module with dependencies on rules_python (1.8.3), rules_nodejs (6.7.3), aspect_rules_js (2.9.2), buildozer (8.2.1), rules_shell (0.6.1), and aspect_bazel_lib (2.22.5). Configures Python 3.11 toolchain and npm dependencies.
- **BUILD**: Defines ajv_test rules for all module metadata.json files, validating against metadata.schema.json using the ajv CLI tool from npm
- **tools/BUILD**: Defines py_binary targets for all tools, py_library targets for shared code, and test targets (update_integrity_test, version_test, module_selector_test)

### Documentation Files

- **README.md**: Overview, disclaimer about infrastructure reliability, and instructions for self-hosting/mirroring
- **docs/README.md**: Comprehensive contribution guide (246 lines) covering registry structure, module contribution, presubmit, validations, approval process, versioning conventions, and yanking
- **docs/bcr-policies.md**: Policies for BCR and module maintainers, responsibilities, review guidelines, and communication channels

## Code Organization Patterns

### Validation Pipeline

The BCR uses a multi-stage validation pipeline:

1. **Schema Validation**: `metadata.schema.json` + ajv validates all metadata.json files
2. **Pre-commit Hooks**: `.pre-commit-config.yaml` runs ruff (Python linting) and custom checks
3. **Python Validation**: `bcr_validation.py` performs deep validation (URL stability, integrity hashes, MODULE.bazel matching, compatibility_level)
4. **Presubmit Execution**: `bcr_presubmit.py` (from bazelbuild/continuous-integration) runs module-specific tests across platforms and Bazel versions
5. **GitHub Actions**: Workflows enforce additional policies (maintainer reviews, first-time contributor approval)

### Module Version Immutability

The add-only policy is enforced through:
- Git history preservation
- Presubmit checks preventing modification of checked-in files
- Version incrementing conventions (.bcr.1, .bcr.2 for fixes)
- Yanked versions list instead of deletion

### Tooling Dependencies

The tools form a dependency hierarchy:
```
registry.py (core library)
├── add_module.py (depends on registry.py, bcr_validation.py)
├── bcr_validation.py (depends on registry.py, attestations.py, slsa.py, verify_stable_archives.py)
├── calc_integrity.py (depends on registry.py)
├── migrate_to_bzlmod.py (depends on registry.py)
├── update_integrity.py (depends on registry.py)
├── module_selector.py (depends on registry.py)
├── module_analyzer.py (depends on module_selector.py)
├── mcp_server.py (depends on registry.py)
└── print_all_src_urls.py (depends on registry.py)
```

The registry.py library provides the Registry class as the central abstraction for all module operations, ensuring consistency across tools.
