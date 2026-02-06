# rules_multirun Summary

## Overview

rules_multirun is a Bazel rules repository that provides a simple, efficient interface for running multiple commands in a single `bazel run` invocation. This ruleset is particularly valuable for workflows that require running multiple tools such as linters, formatters, or deployment scripts, where executing each separately would be time-consuming and inefficient.

## Purpose and Goals

The primary purpose of rules_multirun is to compose multiple executable targets into a single runnable target that can execute them either sequentially or in parallel. This addresses the common problem in build systems where developers need to run multiple independent commands but don't want to execute separate `bazel run` invocations for each one. The rules are designed to be lightweight, simple to use, and to provide significant performance improvements for common development workflows.

The project is a fork of the original multirun rules from ash2k/bazel-tools, but removes the golang dependency in favor of a Python-based execution engine, making it more accessible for projects that don't already use Go.

## Key Features and Capabilities

**Parallel Execution**: Commands can be executed in parallel by setting `jobs = 0`, which allows unlimited concurrency. This is particularly useful for running independent linters or formatters that don't interfere with each other.

**Sequential Execution**: Commands can also run sequentially (the default behavior), with optional `keep_going` support to continue executing subsequent commands even if earlier ones fail.

**Command Wrapping**: The `command` rule provides a wrapper around any executable target, allowing you to customize execution with specific arguments, environment variables, and runtime data dependencies.

**Output Control**: Options for buffering output (in parallel mode), printing commands before execution, and forwarding stdin to commands provide fine-grained control over execution behavior.

**Configuration Transitions**: Support for custom Bazel configuration transitions through `command_with_transition` and `multirun_with_transition` enables advanced use cases like forcing optimization mode for tools or transitioning to specific platforms for deployment.

**Location Expansion**: Both `arguments` and `environment` attributes support `$(location)` expansion, making it easy to reference other Bazel targets and runfiles in command configurations.

**Workspace Root Execution**: Commands can optionally be run from the workspace root instead of the execution root via the `run_from_workspace_root` attribute.

## Primary Use Cases and Target Audience

**Development Workflow Automation**: The most common use case is running multiple linters, formatters, or code quality tools in a single command. For example, `bazel run //:lint` might execute ESLint, Prettier, and Black all at once.

**Multi-Environment Deployments**: Teams can create multirun targets that deploy to multiple environments or regions in parallel, significantly reducing deployment time.

**Test and Build Orchestration**: While not a replacement for Bazel's native test framework, multirun can coordinate running multiple build validation tools or deployment verification scripts.

**CI/CD Pipelines**: Continuous integration workflows benefit from the ability to run multiple checks in parallel while maintaining proper dependency management through Bazel.

The target audience includes:
- Bazel users seeking to streamline their development workflows
- Teams using multiple code quality tools that can run independently
- DevOps engineers orchestrating complex multi-step deployments
- Projects migrating from Makefiles or shell scripts to Bazel

## High-Level Architecture

The architecture consists of three main components:

**Starlark Rule Implementation**: The core logic is implemented in Starlark (.bzl files) and defines the `command` and `multirun` rules, along with their transition variants. These rules handle dependency resolution, runfiles merging, and script generation.

**Python Execution Engine**: A Python script (`internal/multirun.py`) serves as the runtime executor, handling parallel or sequential execution, output buffering, stdin forwarding, and signal handling. It uses the Python runfiles library to locate executables.

**Bash Wrapper Scripts**: Generated bash scripts provide the entry point for both `command` and `multirun` targets, initializing the Bazel runfiles environment and delegating to the appropriate executable.

The rules integrate with Bazel's runfiles mechanism to ensure all dependencies are available at runtime, and use JSON-encoded instruction files to pass execution configuration from the analysis phase to the execution phase.

## Related Projects and Dependencies

**Core Dependencies**:
- **bazel_skylib** (1.4.2+): Provides essential Starlark utilities, particularly the shell.bzl library for safe shell quoting
- **rules_python** (0.36.0+): Required for the Python execution engine and runfiles library
- **rules_shell** (0.4.1+): Used for shell binary rules in tests and examples

**Related Projects**:
- **ash2k/bazel-tools**: The original multirun implementation that this project forked from, which used Go instead of Python
- **Bazel's native test framework**: While multirun can orchestrate multiple executables, it's not a replacement for `bazel test`

**Development Dependencies**:
- **stardoc** (0.7.2): Used to generate the API documentation in the doc/ directory

The project is registered in the Bazel Central Registry (BCR) and supports both Bzlmod and WORKSPACE-based dependency management, with the MODULE.bazel file defining the Bzlmod configuration.
