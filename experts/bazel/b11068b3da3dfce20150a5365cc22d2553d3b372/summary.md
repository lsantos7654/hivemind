# Bazel: Open-Source Build and Test System

## Repository Purpose and Goals

Bazel is an open-source, multi-language build and test tool developed by Google and released under the Apache 2.0 license. It is the open-source version of Google's internal Blaze build system, which has been used to build Google's server software for years. Bazel solves the fundamental problem of enabling fast, correct, and scalable builds across large organizations and codebases.

**Core Design Goals:**
- **Reproducibility**: Same source code always produces identical binaries, eliminating skew between local and CI builds
- **Scalability**: Handles codebases with 100k+ source files and teams in the tens of thousands
- **Incrementality**: Rebuilds only what is necessary by tracking file content and build command changes
- **Correctness**: Enforces hermetic builds and explicit dependency declarations
- **Performance**: Achieves 99%+ cache hit rates through multi-layered caching (in-memory, disk, remote)

**Target Users:** Enterprise organizations with large monorepos, polyglot projects requiring multi-language support, teams that need reproducible and distributable builds, and projects requiring CI/CD integration at scale.

## Key Features and Capabilities

**Artifact-Based Build System**: Unlike task-based systems (Make, Gradle), Bazel operates declaratively—engineers specify *what* to build, and Bazel determines *how* to build it. This enables the system to make stronger guarantees about parallelism and correctness.

**Remote Execution and Caching**: Bazel supports distributed build execution through gRPC protocols compliant with the open-source Remote Execution API specification. Actions can be offloaded to remote build farms, with results cached and reused across teams.

**Incremental Builds**: The Skyframe evaluation framework tracks dependency relationships at the file level, enabling perfect incrementality. Only the minimum set of affected targets are rebuilt when inputs change.

**Multi-Language Support**: Native support for C++, Java, Python, Go, Rust, Android, iOS, and many others. Rules for each language are maintained in dedicated repositories (rules_cc, rules_python, rules_java, rules_go, rules_rust, rules_apple, rules_android).

**Hermetic Builds**: Actions run in filesystem sandboxes (using LXC on Linux, similar to Docker), isolating them from each other and the host system. Tools are treated as dependencies and versioned explicitly.

**Query and Analysis Capabilities**: Three complementary query languages—`bazel query` (dependency analysis), `cquery` (configured query), and `aquery` (action query)—enable deep introspection of the build graph.

**Module System (Bzlmod)**: Modern external dependency management replacing the legacy WORKSPACE system. Bazel 9 will remove WORKSPACE entirely, requiring Bzlmod for all external dependencies. The Bazel Central Registry (BCR) now hosts 650+ modules.

## Primary Use Cases

- **Large-Scale Monorepos**: Google-style development with single repository containing server software, mobile apps, and supporting tools
- **Cross-Platform Builds**: Simultaneously building for Linux, macOS, Windows, Android, and iOS from the same BUILD files
- **Multi-Language Projects**: Backend (Java/Go), frontend (TypeScript/Python), mobile apps all in one coherent build
- **CI/CD Integration**: Reproducible builds that work identically on developer machines and CI systems
- **Distributed Teams**: Remote execution enables developers anywhere to leverage shared build farms and caches

## High-Level Architecture Overview

**Three-Phase Build Process:**

1. **Loading Phase**: All BUILD and .bzl files are loaded and evaluated. Starlark macros execute, and targets are instantiated into a graph
2. **Analysis Phase**: Rule implementation functions execute, analyzing target dependencies and generating an action graph
3. **Execution Phase**: Actions execute in parallel (locally or remotely), producing build outputs

**Skyframe Evaluation Framework**: The core incremental evaluation engine that powers Bazel's performance. It represents the build as a directed acyclic graph of `SkyValue` nodes, where each node depends on others through `SkyKey` references. Skyframe enables:
- Perfect incrementality through bottom-up and top-down invalidation strategies
- Parallel evaluation of independent nodes
- Hermeticity through explicit dependency registration

**Core Architecture Components:**

- **com.google.devtools.build.lib**: Main build system library including analysis, repository rules, query engine
- **com.google.devtools.build.skyframe**: Incremental evaluation framework
- **Starlark**: A Python-like domain-specific language for writing BUILD files and extension rules
- **Native Rules**: Minimal built-in rules (genrule, filegroup) with most language support in external repositories

**Client-Server Model**: Bazel operates with a persistent server mode, where the bazel binary communicates with a running daemon process to maintain caches between invocations.

**Extensibility via Starlark**: Rules, macros, and aspects are written in Starlark, enabling the community to extend Bazel for any language or use case without modifying core code.

## Related Projects and Dependencies

**Remote Execution**: Bazel implements the open-source Remote Execution API (defined in googleapis/googleapis), enabling integration with services like Bazel Remote Execution (BRE), RBE, Buildkite, and others.

**Language-Specific Rules Repositories:**
- rules_cc (C++)
- rules_java (Java)
- rules_python (Python)
- rules_go (Go)
- rules_rust (Rust)
- rules_apple (iOS, macOS)
- rules_android (Android)
- rules_proto (Protocol Buffers)
- And 640+ more in the Bazel Central Registry

**Bazel Central Registry (BCR)**: Centralized module repository for deterministic version resolution using MVS (Minimal Version Selection), replacing WORKSPACE configuration patterns.

**Buildtools Ecosystem**: Supporting tools including:
- Buildifier: Code formatter and linter for BUILD files
- Stardoc: Documentation generator for rules
- Gazelle: Build file generator for Go projects

**Build Event Protocol (BEP)**: Standardized streaming protocol for build and test results, enabling integration with external tools and dashboards.

**Key Dependencies** (from MODULE.bazel):
- Protobuf (v33.1) for RPC definitions
- gRPC (v1.76.0) for remote execution
- abseil-cpp (v20250814.1) for utilities
- rules_jvm_external, rules_python, rules_cc, rules_shell for language support

## Strategic Direction (Bazel 9 Roadmap)

**Planned for 2025:**
- Complete removal of legacy WORKSPACE system; Bzlmod becomes mandatory
- Migration of C++, Android, Java, Python, and Proto rules from Bazel into dedicated Starlark repositories
- Lazy evaluation of symbolic macros for performance improvements
- Experimental Starlark type system (similar to Python type annotations)
- Enhanced project configuration model reducing build flag complexity
- Asynchronous remote execution support
- SLSA attestation support in BCR for supply chain security

This evolution reflects Bazel's philosophy of decoupling language-specific functionality from the core engine, enabling faster innovation and community-driven rule development while keeping Bazel's foundation focused on artifact-based, incremental builds.
