# Bazel Central Registry - Summary

## Repository Purpose

The Bazel Central Registry (BCR) is the official, default registry for Bazel's external dependency management system called "Bzlmod" (Bazel modules). It serves as a centralized repository hosting metadata, source archive information, and build configurations for Bazel modules, enabling reproducible and versioned dependency management across the Bazel ecosystem. The registry is hosted at https://bcr.bazel.build/ and backs the searchable web interface at https://registry.bazel.build/.

## Key Features and Capabilities

The BCR provides several critical capabilities for the Bazel ecosystem:

**Module Hosting**: Contains metadata and source information for 977+ Bazel modules, including both native Bazel rulesets (like rules_python, rules_go) and third-party C/C++ projects without upstream Bazel support (like abseil-cpp, boost, protobuf).

**Version Management**: Implements a strict add-only policy ensuring reproducible builds. Once published, module versions cannot be modified. The registry supports flexible versioning schemes including semantic versions, date-based versions (20260107.0), pseudo-versions for unreleased commits, and BCR-specific patches (1.2.3.bcr.1).

**Quality Assurance**: Every module version must pass comprehensive presubmit validation including:
- Automated builds and tests across multiple platforms (Linux, macOS, Windows)
- Multiple Bazel version compatibility testing (6.x, 7.x, 8.x, 9.x)
- Integrity verification for source archives and patches
- Module metadata validation against JSON schemas
- Incompatible flag migration testing for future Bazel versions

**Security Features**: Experimental support for build attestations using SLSA provenance and verification through slsa-verifier. Modules can provide signed attestations for source.json, MODULE.bazel, and source archives.

**Extensibility**: Supports patches and overlays for modules that require modifications to work with Bazel. Patches apply fixes to upstream sources, while overlays provide complete BUILD files for projects without native Bazel support.

**Developer Tooling**: Comprehensive Python-based tools for module management including interactive module addition (add_module.py), integrity calculation (calc_integrity.py), validation (bcr_validation.py), WORKSPACE-to-Bzlmod migration (migrate_to_bzlmod.py), and module analysis (module_analyzer.py, module_selector.py).

**Integration Support**: Provides an MCP (Model Context Protocol) server for programmatic access by AI coding agents, enabling automated module queries, updates, and dependency management.

## Primary Use Cases and Target Audience

**Bazel Users**: Developers using Bazel 8+ (where Bzlmod is default) automatically consume the BCR for dependency resolution. Users can add dependencies by simply declaring `bazel_dep(name = "module_name", version = "1.0.0")` in their MODULE.bazel file.

**Module Maintainers**: Open-source project owners who maintain specific modules in the registry. They review PRs, publish new versions, and serve as contact points for issues. Module maintainers have approval rights through GitHub's PR review system.

**BCR Maintainers**: Community volunteers who review and accept contributions, assess registry health, appoint module maintainers, and triage issues. They ensure modules follow BCR policies and pass presubmit checks.

**Enterprise Users**: Organizations can mirror the entire BCR infrastructure to avoid external dependencies while still leveraging the module metadata, using the `--registry` flag to point to their own mirrors.

**Rules Authors**: Developers creating new Bazel rulesets can publish them to the BCR, making them discoverable and easily consumable by the broader Bazel community.

## High-Level Architecture

The BCR follows the standard Bazel registry format with enhanced metadata requirements:

**Registry Root**: Contains bazel_registry.json (mirror configuration), metadata.schema.json (validation schema), and incompatible_flags.yml (breaking change flags for testing).

**Module Structure**: Each module has a top-level directory under `modules/` containing:
- metadata.json: Homepage, maintainers, repository allowlist, version list, yanked versions
- Version directories (e.g., 1.8.3/): Each containing MODULE.bazel, source.json, presubmit.yml, optional patches/, overlay/, and attestations.json

**Tooling Infrastructure**: Python-based validation and management tools under `tools/`, along with Bazel BUILD files for building and testing. The registry itself uses Bzlmod with dependencies on rules_python, rules_nodejs, aspect_rules_js, and buildozer.

**CI/CD Pipeline**: GitHub Actions workflows handle PR validation, maintainer notifications, automated approval through the bazel-io bot, presubmit execution, and registry synchronization to Google Cloud Storage.

**Presubmit System**: Powered by bcr_presubmit.py from the bazelbuild/continuous-integration repository, executing tasks defined in each module's presubmit.yml across Bazel CI infrastructure. Tests include anonymous module tests (verify exposed targets build correctly) and test module tests (comprehensive examples with dev dependencies).

## Related Projects and Dependencies

**Bazel**: The build system itself (bazel.build), specifically Bzlmod (the external dependency system). The BCR is the official default registry for Bazel 8+.

**Bazel CI**: The continuous-integration infrastructure (github.com/bazelbuild/continuous-integration) that runs BCR presubmit checks across multiple platforms and Bazel versions.

**publish-to-bcr**: GitHub action (github.com/bazel-contrib/publish-to-bcr) for automated BCR PR creation on release, enabling project owners to seamlessly publish new versions.

**Dependencies**: The BCR repository itself depends on:
- rules_python (1.8.3): For Python tooling and validation scripts
- rules_nodejs (6.7.3) and aspect_rules_js (2.9.2): For npm-based tooling (ajv JSON schema validation)
- buildozer (8.2.1): For automated BUILD file modifications
- rules_shell (0.6.1): For shell-based testing

**Frontend**: The registry-frontend project provides the searchable web UI at registry.bazel.build, automatically rebuilding when the registry changes.

The BCR represents critical infrastructure for the Bazel ecosystem, enabling decentralized module publishing with centralized discoverability, versioning, and quality assurance.
