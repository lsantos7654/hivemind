# rules_testing - Bazel Starlark Testing Framework

## Repository Purpose and Goals

`rules_testing` is an official Bazel project that provides comprehensive frameworks and utilities for testing Starlark code and Bazel rules. The repository aims to make testing Bazel build logic as easy and pleasant as writing application tests, bringing modern testing patterns to the Bazel ecosystem. It addresses the fundamental challenge that testing build rules requires special tooling since rules execute during Bazel's analysis phase, not at runtime like normal programs.

The project's primary goal is to provide a fluent, expressive testing API that produces clear error messages and makes it easy to write maintainable tests. It accomplishes this through two main components: an analysis test framework for testing rule behavior, and a Truth-style assertion library for making fluent, type-aware assertions.

## Key Features and Capabilities

**Analysis Testing Framework**: The core feature is the `analysis_test` function, which allows developers to test rule behavior during Bazel's analysis phase. This enables verification of provider outputs, action generation, flag handling, runfiles configuration, and other analysis-time behaviors that are invisible to regular tests. The framework supports testing multiple targets simultaneously with different configuration settings, allowing developers to verify cross-platform behavior and configuration-dependent logic.

**Truth-Style Assertions**: The library includes a comprehensive Truth-style assertion framework inspired by Google's Truth library. This provides type-specific "subject" objects that wrap values and offer ergonomic assertion methods. For example, `TargetSubject` wraps Bazel targets, `ActionSubject` wraps actions, `FileSubject` wraps files, and so on. Each subject provides methods tailored to its type, resulting in more readable tests and better error messages.

**Unit Testing Support**: Beyond analysis tests, the library provides `unit_test` for testing generic Starlark code that doesn't require instantiating rules or the analysis phase. This is useful for testing utility functions, custom predicates, and other pure Starlark logic.

**Test Organization**: The `test_suite` function aggregates multiple test functions into a single Bazel target, simplifying BUILD file declarations and making it easy to run entire test suites with a single command.

**Custom Matchers**: The `matching` module provides predicate-based matching for scenarios where simple equality checks aren't sufficient, such as ignoring platform-specific file extensions or matching glob patterns. Users can implement custom matchers using `matching.custom_matcher`.

**Extensibility**: The framework is designed for extension, allowing users to write custom subject classes for their own providers and data types, and to define custom attributes for tests that need special setup.

## Primary Use Cases and Target Audience

The target audience is Bazel rule authors and maintainers who need to test their custom rules, macros, and aspects. This includes:

1. **Rule Developers**: Engineers writing custom Bazel rules who need to verify that their rules produce correct outputs, generate appropriate actions, handle flags correctly, and work across different platforms and configurations.

2. **Repository Maintainers**: Maintainers of language-specific Bazel rules (e.g., rules_python, rules_go) who need comprehensive test coverage to ensure backwards compatibility and prevent regressions.

3. **Build Tool Authors**: Developers creating build tooling on top of Bazel who need to test aspects, toolchains, and other advanced Bazel features.

4. **Enterprise Build Teams**: Organizations with complex, custom build infrastructure that requires thorough testing to maintain reliability.

Common use cases include verifying that a rule correctly propagates providers to dependents, testing that compiler flags are constructed properly for different platforms, ensuring runfiles are assembled correctly, validating aspect behavior, and checking that configuration transitions work as expected.

## High-Level Architecture Overview

The architecture consists of several layers:

**Public API Layer** (`lib/*.bzl`): Entry points include `analysis_test.bzl`, `unit_test.bzl`, `truth.bzl`, and `test_suite.bzl`. These provide the high-level functions that test authors interact with.

**Subject Layer** (`lib/private/*_subject.bzl`): Type-specific wrapper classes that provide assertion methods. Each subject wraps a particular type (Target, Action, File, etc.) and provides methods for asserting on that type's properties. Subjects are hierarchical—for example, `TargetSubject` can return a `RunfilesSubject` for asserting on a target's runfiles.

**Assertion Infrastructure** (`lib/private/expect*.bzl`, `lib/private/check_util.bzl`, `lib/private/compare_util.bzl`): The `Expect` class is the entry point for creating subjects, while `ExpectMeta` tracks assertion context for error reporting. Utility modules handle comparison logic and error message formatting.

**Test Framework** (`lib/private/analysis_test.bzl`): Implements the actual test rule that runs during the analysis phase. It manages test environment setup, applies aspects to collect target information, runs user-provided test implementation functions, and reports failures.

**Utility Layer** (`lib/util.bzl`, `lib/private/util.bzl`): Helper functions for common testing patterns like creating helper targets, working with runfiles, and managing test aspects.

The execution flow is: test macro (loading phase) → analysis_test rule (analysis phase) → user impl function → Expect → Subjects → assertions/failures → test result.

## Related Projects and Dependencies

**Core Dependencies**:
- **bazel_skylib**: Provides foundational Starlark utilities for path manipulation, type checking, and common operations. The testing library builds on skylib's utilities.
- **platforms**: Used for platform-specific testing and configuration.
- **rules_license**: For license compliance.

**Development Dependencies**:
- **stardoc**: Used for generating API documentation from Starlark code.
- **rules_python**: For documentation generation tooling (Sphinx).
- **rules_shell**: For shell script support in development workflows.

**Related Bazel Projects**:
- **skylib's unittest.bzl**: The older, more basic testing framework that rules_testing aims to supersede. rules_testing provides a compatibility layer.
- **rules_proto, rules_java, rules_cc, etc.**: Language-specific rule sets that can use rules_testing for their test suites.
- **Bazel core**: rules_testing is developed by the Bazel team and closely tracks Bazel's analysis-phase APIs.

The library is designed to be a drop-in improvement over skylib's unittest, offering more features while maintaining some backwards compatibility. It represents the modern approach to Bazel rule testing and is intended to become the standard testing framework for the Bazel ecosystem.

**Repository Information**:
- GitHub: https://github.com/bazelbuild/rules_testing
- Documentation: https://rules-testing.readthedocs.io
- Bazel Central Registry: Available as `rules_testing` module for bzlmod users
- License: Apache 2.0
