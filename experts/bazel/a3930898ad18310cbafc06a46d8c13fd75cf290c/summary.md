# Bazel Build System - Repository Summary

## Repository Purpose and Goals

Bazel is Google's open-source build and test system designed around the motto "{Fast, Correct} - Choose two". Bazel's primary purpose is to build and test software of any size, quickly and reliably, handling everything from small projects to massive monorepos with millions of lines of code. The system emphasizes speed through advanced caching (both local and distributed), optimized dependency analysis, and parallel execution. It rebuilds only what is necessary based on precise incremental build analysis.

Bazel provides a unified build tool that supports multiple programming languages including Java, C++, Android, iOS, Go, Python, and many others through an extensible rule system. The build system runs cross-platform on Windows, macOS, and Linux, providing consistent build behavior across all platforms. This cross-platform consistency is crucial for large organizations with diverse development environments.

## Key Features and Capabilities

**Incremental Builds and Caching**: Bazel tracks file-level dependencies with extreme precision, ensuring it only rebuilds what has changed. The system supports both local disk caching and distributed remote caching, allowing build results to be shared across teams and CI systems. This dramatically reduces build times in large projects.

**Hermetic and Reproducible Builds**: Bazel enforces hermetic builds where all inputs are explicitly declared. This ensures builds are reproducible across different machines and time periods. The system sandboxes build actions to prevent undeclared dependencies from sneaking in.

**Remote Execution**: Bazel supports the Remote Execution API (REAPI), allowing build actions to be distributed across a cluster of machines. This enables massive parallelization for large builds, with actions executed on remote workers while results are cached centrally.

**Skyframe Evaluation Framework**: The core of Bazel's incremental analysis is Skyframe, a parallel evaluation framework based on a directed acyclic graph (DAG). Skyframe tracks dependencies at a fine granularity and efficiently recomputes only affected values when inputs change.

**Starlark Extension Language**: Bazel uses Starlark (formerly Skylark), a Python-like domain-specific language, for defining build rules, macros, and repository rules. This allows users to extend Bazel with custom build logic while maintaining determinism and security through language restrictions.

**Multi-Language Support**: Bazel provides native rules for numerous languages and can be extended for new languages. The rules system is modular, with built-in support for Java, C++, Python, Go, Android, Objective-C, and protocol buffers, among others.

**Query and Analysis Tools**: Bazel includes powerful query languages (query, cquery, aquery) for analyzing build graphs, dependencies, and configured targets. These tools are essential for understanding and debugging complex build graphs.

**Bzlmod Module System**: Bazel features a modern dependency management system called Bzlmod, which uses MODULE.bazel files to declare external dependencies with version resolution, similar to package managers in other ecosystems.

## Primary Use Cases and Target Audience

**Enterprise Monorepos**: Bazel excels at managing massive monorepos containing millions of lines of code across multiple languages. Companies like Google, Uber, LinkedIn, and many others use Bazel to manage their entire codebase in a single repository.

**Multi-Language Projects**: Projects that combine multiple programming languages (e.g., Java backend, C++ services, Python tools, JavaScript frontend) benefit from Bazel's unified build model where dependencies can cross language boundaries seamlessly.

**Mobile Development**: Android and iOS projects benefit from Bazel's fast incremental builds and accurate dependency tracking, particularly important for mobile apps with long build times.

**Distributed Development**: Teams distributed across different offices and time zones benefit from remote caching and remote execution, allowing developers to leverage shared build artifacts and distributed compute resources.

**Continuous Integration**: Bazel's hermetic builds and remote caching make it ideal for CI systems, where build reproducibility and speed are critical. CI systems can share a remote cache, dramatically reducing redundant computation.

The target audience includes build engineers, release engineers, and development teams working on large-scale software projects that require fast, reliable, and reproducible builds. The system is particularly valuable for organizations that have outgrown traditional build tools like Make, Maven, or Gradle in terms of scale and performance requirements.

## High-Level Architecture Overview

**Client-Server Architecture**: Bazel operates as a client-server system. The `bazel` command-line client communicates with a persistent Bazel server process that maintains build state in memory. This architecture enables faster repeated builds by keeping analyzed build graphs and cached data in memory between invocations.

**Core Components**:
- **C++ Client Layer** (src/main/cpp): The client launcher written in C++ that bootstraps the server, processes startup options, and manages the client-server communication.
- **Java Server Core** (src/main/java): The main Bazel server implementation in Java, containing the core build logic, analysis, execution, and caching infrastructure.
- **Skyframe** (skyframe package): The parallel evaluation framework that serves as Bazel's incremental computation engine. All build analysis goes through Skyframe.
- **Starlark Runtime** (net/starlark/java): The interpreter for Starlark, Bazel's extension language, including syntax parsing, evaluation, and built-in functions.
- **Package Loading** (packages package): Responsible for parsing BUILD files, evaluating Starlark code, and constructing the package and target graph.
- **Analysis Phase** (analysis package): Performs configured target analysis, resolving dependencies, and constructing the action graph.
- **Execution Framework** (exec package): Manages action execution, including local execution, remote execution, sandboxing, and worker processes.
- **Remote Execution Module** (remote package): Implements the Remote Execution API client for distributed builds and caching.
- **VFS Abstraction** (vfs package): A virtual file system layer that abstracts file operations and enables features like in-memory file systems and overlay file systems.

**Build Phases**: A typical Bazel invocation proceeds through several phases:
1. **Loading Phase**: Parse BUILD files and construct the target graph
2. **Analysis Phase**: Resolve configurations and dependencies, create the action graph
3. **Execution Phase**: Execute actions (compile, link, etc.) to produce outputs
4. **Completion Phase**: Report results and clean up

**Module System**: Bazel has a plugin architecture based on BlazeModule. Modules extend Bazel's functionality by hooking into various extension points throughout the build lifecycle. Over 50 modules provide features like remote execution, coverage reporting, profiling, and platform-specific functionality.

## Related Projects and Dependencies

**Core Dependencies**:
- **Protocol Buffers** (protobuf): Used extensively for serialization, particularly in the Remote Execution API and build event protocol.
- **gRPC**: Provides the RPC framework for remote execution and build event streaming.
- **Abseil** (abseil-cpp): Google's C++ common libraries used in the C++ client code.
- **Guava**: Google's Java core libraries used throughout the Java server implementation.

**Build Rules and Extensions**:
- **rules_java**: Java build rules (though many are built into Bazel core)
- **rules_cc**: C/C++ build rules
- **rules_python**: Python build rules
- **rules_go**: Go language support
- **rules_apple**: iOS and macOS build rules
- **rules_android**: Android application build rules
- **rules_proto**: Protocol buffer support

**Infrastructure Projects**:
- **Bazel Remote APIs**: The specification for remote execution and caching APIs
- **Bazel Central Registry (BCR)**: The central repository of Bazel modules for Bzlmod
- **Buildtools**: Additional tools for working with BUILD files (buildifier, buildozer)
- **Bazelisk**: A version manager and launcher for Bazel

**Development Tools**:
- **Stardoc**: Documentation generator for Starlark rules
- **Skyframe Debugger**: Tools for debugging Skyframe evaluation
- **rules_testing**: Testing framework for Bazel rules

The Bazel ecosystem is large and active, with hundreds of community-maintained rule sets for various languages, platforms, and tools. The project maintains strong backward compatibility while evolving the platform through careful deprecation policies and feature flags.
