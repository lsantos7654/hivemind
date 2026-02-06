# Bazel: A Fast and Scalable Build System

## Overview

Bazel is an open-source build and test tool developed by Google for building software of any size, quickly and reliably. The tagline "{Fast, Correct} - Choose two" encapsulates its core promise: delivering both speed and correctness without compromise. Bazel uses a high-level, human-readable build language (Starlark) and operates on abstract concepts like libraries, binaries, scripts, and data sets, shielding developers from the complexity of low-level compiler and linker invocations.

The repository at commit `dfcb414acc2553c0834e04001dcac601369b570b` represents version 9.0.0-prerelease of Bazel, containing approximately 2.5 million lines of code across Java, C++, Starlark, and other languages.

## Key Features and Capabilities

**Incremental and Parallel Builds**: Bazel excels at rebuilding only what's necessary by tracking changes to both file content and build commands. It caches all previously completed work and uses advanced dependency analysis to minimize rebuild times. The system supports highly parallel execution, enabling efficient utilization of multi-core processors and distributed build infrastructure.

**Multi-Language Support**: Bazel supports building and testing projects in multiple languages including Java, C++, Python, Go, Android, iOS, and many others. Language support is provided through built-in rules and extensible rule sets. The architecture allows community-contributed language rules to integrate seamlessly.

**Multi-Platform Builds**: Bazel runs on Linux, macOS, and Windows, and can build binaries and deployable packages for multiple target platforms from the same project. The system includes sophisticated cross-compilation support and platform-aware toolchain selection.

**Remote Execution and Caching**: Bazel supports distributed builds through remote execution protocols (Remote Execution API v2), allowing build actions to execute on remote workers. Remote caching enables sharing build artifacts across teams, dramatically reducing redundant compilation work in CI/CD environments.

**Hermetic and Reproducible Builds**: Bazel enforces hermeticity by isolating build actions from the host environment through sandboxing. This ensures that builds are reproducible across different machines and times, which is critical for debugging, security, and compliance.

**Scalability**: Bazel is designed to handle extremely large codebases, including monorepos with hundreds of thousands of source files and dependency relationships. It's used internally at Google and by major companies like Uber, Dropbox, and Twitter to build massive projects.

**Extensibility**: The Starlark build language allows developers to define custom rules, macros, and build logic. The module system (Bzlmod) enables sharing and reusing build definitions across projects and organizations.

## Primary Use Cases and Target Audience

**Enterprise Engineering Teams**: Organizations with large, complex codebases benefit from Bazel's scalability, caching, and remote execution capabilities. Teams managing monorepos or multiple interconnected repositories find particular value in Bazel's dependency management and incremental build capabilities.

**Polyglot Projects**: Projects combining multiple programming languages (e.g., a backend in Java/Go with mobile apps in Kotlin/Swift) benefit from Bazel's unified build model and cross-language dependency tracking.

**CI/CD Pipelines**: DevOps teams leverage Bazel's caching and remote execution to accelerate continuous integration builds. The deterministic nature of Bazel builds ensures consistent results across development and production environments.

**Open Source Projects**: The Bazel ecosystem includes numerous open-source projects using it as their build system, particularly in the TensorFlow, Kubernetes, and gRPC communities.

## High-Level Architecture

**Client-Server Model**: Bazel uses a client-server architecture where a persistent server process (the Bazel daemon) maintains build state across invocations, while lightweight client processes handle command-line interactions.

**Core Components**:
- **Blaze Runtime**: The main execution framework managing the entire build lifecycle
- **Skyframe**: A parallel evaluation framework implementing incremental computation through a dependency graph
- **Action Execution**: Strategies for executing build actions (local, sandboxed, remote, worker-based)
- **Package Loading**: System for parsing BUILD files and constructing the target graph
- **Analysis Phase**: Converts the target graph into an action graph
- **Execution Phase**: Executes actions to produce output artifacts

**Starlark Language Runtime**: The embedded Starlark interpreter (in `net.starlark.java`) provides the language foundation for BUILD files, .bzl files, and rule definitions.

## Related Projects and Dependencies

Bazel relies on and integrates with several key technologies:

- **Protocol Buffers**: Used for internal data structures and Remote Execution API
- **gRPC**: Powers remote execution and caching protocols
- **Abseil**: Common libraries (C++ and Java versions)
- **GraalVM**: Optional native image compilation for improved startup time
- **Remote Execution API**: Industry standard for distributed builds
- **Buildkite, Jenkins, GitHub Actions**: Common CI platforms integrating with Bazel

The Bazel ecosystem includes related projects:
- **Bazelisk**: Version manager and launcher
- **Buildifier/Buildozer**: Formatting and refactoring tools
- **rules_* repositories**: Language-specific rule sets (e.g., rules_go, rules_python, rules_docker)
- **Bazel Central Registry (BCR)**: Module repository for Bzlmod dependency management

Bazel's architecture emphasizes correctness, performance, and extensibility, making it suitable for projects ranging from small applications to massive enterprise monorepos.
