# Bazel Build System Summary

## Overview

Bazel is Google's open-source build and test tool designed for building and testing software of any size, quickly and reliably. It is the open-source version of Google's internal build tool, Blaze, and embodies the philosophy of "{Fast, Correct} - Choose two." Bazel is engineered for massive-scale software development with advanced caching, incremental builds, parallel execution, and support for multiple languages and platforms.

## Purpose and Goals

Bazel addresses the fundamental challenges of building large-scale software systems by providing a fast, correct, and scalable build system. Its core goals are:

1. **Speed**: Bazel rebuilds only what is necessary, leveraging advanced local and distributed caching, optimized dependency analysis, and parallel execution to deliver fast and incremental builds
2. **Correctness**: Through hermetic builds and sandboxing, Bazel ensures reproducible builds that minimize skew and maximize reliability
3. **Scalability**: Bazel handles codebases of any size, supporting both multiple repositories and huge monorepos with tens of thousands of users
4. **Multi-language Support**: Build and test Java, C++, Android, iOS, Go, Python, and many other language platforms with a single tool
5. **Cross-platform**: Runs on Windows, macOS, and Linux, and can build binaries for multiple platforms from the same project

## Key Features and Capabilities

### Build System Architecture

- **Three-phase Build Process**: Bazel separates builds into Loading (parse BUILD files), Analysis (create action graph), and Execution (run actions) phases, enabling intelligent caching and parallelization
- **Action Graph**: Represents build artifacts, their relationships, and build actions, allowing Bazel to track changes to both file content and build commands
- **Skyframe**: A sophisticated incremental computation framework that powers Bazel's dependency tracking and enables fine-grained invalidation and recomputation
- **Starlark Language**: Uses a Python-like, high-level, human-readable build language for BUILD files and .bzl extensions, operating on concepts like libraries, binaries, and data sets rather than low-level tool invocations

### Performance Optimizations

- **Incremental Builds**: Only rebuilds changed targets and their dependencies
- **Local and Distributed Caching**: Stores build artifacts and reuses them across builds and machines
- **Remote Execution**: Supports distributed build execution for massive parallelization
- **Persistent Server**: Keeps build state in memory between invocations for faster subsequent builds
- **Action Cache**: Avoids re-executing actions when inputs haven't changed

### Extensibility

- **Macros**: Reusable functions that instantiate rules (symbolic macros in Bazel 8+, legacy macros for older versions)
- **Rules**: Define how to build targets, with full control over the build process
- **Aspects**: Cross-cutting concerns that can analyze dependencies
- **Repository Rules**: Manage external dependencies and define workspaces
- **Toolchains**: Abstract platform-specific tools and configurations

### Multi-language and Platform Support

- Native support for Java, C++, Python, Go, Objective-C, Android, iOS, and more
- Extensible rule system allows community-maintained support for additional languages
- Cross-compilation support for building on one platform and targeting another
- Platform-aware builds with automatic toolchain selection

### Build Correctness

- **Sandboxing**: Isolates build actions to prevent undeclared dependencies
- **Hermeticity**: Ensures builds are reproducible by controlling the build environment
- **Dependency Analysis**: Explicit dependency declarations prevent implicit dependencies
- **Visibility Controls**: Package-level visibility rules enforce proper layering

## Primary Use Cases and Target Audience

### Target Audience

1. **Large Organizations**: Companies with massive codebases (100k+ source files) and large engineering teams
2. **Monorepo Users**: Teams maintaining all code in a single repository
3. **Multi-language Projects**: Projects combining Java, C++, Go, Python, and other languages
4. **Mobile Developers**: Android and iOS developers needing fast, reliable builds
5. **DevOps Teams**: Organizations requiring reproducible, cacheable builds for CI/CD pipelines

### Use Cases

- **Large-scale Software Development**: Building Google-scale applications with millions of lines of code
- **Cross-platform Mobile Development**: Building Android apps with native dependencies
- **Multi-language Microservices**: Coordinating builds across services in different languages
- **Continuous Integration**: Fast, cached, and distributed builds for CI systems
- **Reproducible Builds**: Ensuring consistent build outputs for security and reliability

## High-level Architecture

### Core Components

1. **Bazel Binary** (src/main/cpp): Native C++ launcher and client that manages the Bazel server process
2. **Server Process** (src/main/java): Long-running Java server that executes build commands and maintains state
3. **Skyframe** (src/main/java/com/google/devtools/build/skyframe): Incremental computation framework for dependency tracking
4. **Analysis Engine** (src/main/java/com/google/devtools/build/lib/analysis): Evaluates build rules and creates the action graph
5. **Execution Engine** (src/main/java/com/google/devtools/build/lib/exec): Executes actions, manages caching, and coordinates remote execution
6. **Starlark Interpreter** (src/main/java/net/starlark): Evaluates BUILD files and .bzl extensions
7. **Package Loading** (src/main/java/com/google/devtools/build/lib/packages): Parses and loads BUILD files
8. **Rule Implementations** (src/main/java/com/google/devtools/build/lib/rules): Built-in rules for Java, C++, Python, etc.
9. **Query Engine** (src/main/java/com/google/devtools/build/lib/query2): Analyzes build graphs and dependencies
10. **Remote Execution Client** (src/main/java/com/google/devtools/build/lib/remote): Integrates with remote execution services

### Architecture Patterns

- **Client-Server Model**: Lightweight client communicates with persistent server process
- **Incremental Computation**: Skyframe tracks dependencies and recomputes only what changed
- **Action Graph Parallelism**: Independent actions execute in parallel
- **Layered Architecture**: Clear separation between loading, analysis, and execution phases
- **Plugin System**: Extensible through modules, rules, aspects, and repository rules

## Related Projects and Dependencies

### Key Dependencies

- **Protobuf** (v33.4): Used for build event protocol, remote execution API, and internal data structures
- **gRPC** (v1.76.0): Powers remote execution and build event streaming
- **Abseil-cpp** (v20250814.1): Google's common C++ libraries for core utilities
- **Guava**: Google's Java core libraries
- **bazel_skylib** (v1.8.2): Standard library of Starlark utilities
- **rules_java** (v9.1.0), **rules_cc** (v0.2.16), **rules_python** (v1.7.0): Official rule sets for language support

### Ecosystem Projects

- **Bazel Central Registry (BCR)**: Central repository for Bazel modules with 650+ packages
- **rules_apple**: iOS, macOS, tvOS, and watchOS build rules
- **rules_android**: Android build rules
- **rules_go**: Go build rules
- **rules_docker**: Docker container build rules
- **Buildtools**: Tools for formatting and linting BUILD files (Buildifier, Buildozer)
- **Stardoc**: Documentation generator for Starlark rules
- **Remote Execution Services**: Compatible services like BuildBuddy, BuildGrid, Buildbarn

### Integration Points

- **IDEs**: IntelliJ, CLion, VS Code, Android Studio extensions for Bazel projects
- **CI Systems**: GitHub Actions, GitLab CI, Jenkins, Buildkite plugins
- **Package Managers**: Integration with Maven, npm, pip through rules_jvm_external and similar
- **Remote Caching**: Compatible with any HTTP cache or gRPC remote cache service

## Version and Status

**Current version**: 9.0.0-prerelease (as of commit 32eef3485d66f448df4b66fe4f0d530e1a88f99b)

Bazel is production-ready and used at Google and thousands of other organizations worldwide including LinkedIn, Uber, Dropbox, Airbnb, and many others. It follows semantic versioning with regular releases and long-term support (LTS) versions for stability. The project is actively developed with contributions from Google and the open-source community.

**Licensing**: Apache License 2.0
