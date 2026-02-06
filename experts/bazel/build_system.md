# Bazel's Build System Architecture

## 1. Build System Type and Bootstrapping

Bazel is a **self-hosting build system** that uses a bootstrap process for initial compilation. This approach solves the chicken-and-egg problem where Bazel needs to build itself using Bazel.

### Bootstrap Sequence

The bootstrap process is orchestrated through **`compile.sh`** at the repository root:

**Phase 1: Non-Bazel Compilation** (`compile.sh`)
- Direct Java compilation using `javac` without requiring Bazel
- Compiles core Java sources from `src/main/java` and `src/tools/starlark/java`
- Generates protocol buffer Java files from `.proto` sources using system `protoc` and `grpc-java-plugin`
- Creates JAR files from Netty, Protobuf, and Maven dependencies
- Builds Windows-specific JNI library (`windows_jni.dll`) on Windows platform
- Produces `libblaze.jar` containing the minimal Bazel runtime

**Phase 2: Bazel Self-Hosting** (`bootstrap.sh`)
- Uses the freshly compiled `libblaze.jar` to run the Bazel build process
- Builds the final release binary (`//src:bazel_nojdk` or with JDK variants)
- Creates the embedded tools repository (`bazel_tools`) containing build rules
- Generates distribution artifacts for packaging

### Bootstrap Helper Scripts

Located in `scripts/bootstrap/`:
- **`buildenv.sh`** - Environment setup, tool verification, platform detection
- **`compile.sh`** - Java compilation and JAR packaging logic
- **`bootstrap.sh`** - Bazel build phase using the bootstrapped compiler

## 2. Configuration Files

### MODULE.bazel (463 lines)

Modern Bzlmod configuration declaring all dependencies:

```starlark
module(
    name = "bazel",
    version = "9.0.0-prerelease",
)
```

**Core Dependencies:**
| Dependency | Version | Purpose |
|------------|---------|---------|
| `rules_java` | 9.1.0 | Java compilation rules |
| `rules_python` | 1.7.0 | Python rules |
| `rules_cc` | 0.2.14 | C++ rules |
| `protobuf` | 33.1 | Protocol buffers |
| `grpc` | 1.76.0 | gRPC C++ library |
| `grpc-java` | 1.71.0 | gRPC Java bindings |
| `bazel_skylib` | 1.8.2 | Utility macros |
| `platforms` | 1.0.0 | Platform definitions |
| `rules_pkg` | 1.1.0 | Packaging rules |
| `googletest` | 1.17.0 | C++ testing |
| `rules_testing` | 0.9.0 | Testing rules |
| `rules_fuzzing` | 0.6.0 | Fuzzing support |
| `rules_graalvm` | 0.11.1 | GraalVM support |

### .bazelrc (102 lines)

Default build configuration:

```bash
# Java configuration
build --java_language_version=21
build --java_runtime_version=remotejdk_25

# Platform support
build:macos --macos_minimum_os=10.13
build:windows_arm64 --cpu=arm64_windows

# Remote Building (RBE)
build:ubuntu2004 --extra_execution_platforms=//platforms:rbe_ubuntu2004
build:ubuntu2004 --remote_executor=grpcs://remotebuildexecution.googleapis.com

# CI configurations
build:ci-linux --disk_cache=~/.cache/bazel-disk-cache
build:ci-macos --disk_cache=~/.cache/bazel-disk-cache
build:ci-windows --disk_cache=C:/bazel-disk-cache

# Dependency enforcement
build --check_direct_dependencies=error
```

### .bazelversion

Version pinning: `8.5.0` (current Bazel used to build the repository)

## 3. External Dependencies Architecture

### Java Dependency Management

Bazel uses **rules_jvm_external** for Maven dependency management:

- Downloads artifacts from Maven Central
- Generates `maven_install.json` lockfile (121KB)
- Creates `@maven` repository with BUILD files for each JAR
- Resolves version conflicts automatically

**Maven Dependencies** (70+ artifacts):

| Category | Dependencies |
|----------|--------------|
| Networking | Netty 4.1.119 (all platform variants) |
| Serialization | Protobuf, gRPC, Gson |
| Google APIs | Google Auth, API Client, googleapis protos |
| Code generation | Error Prone, AutoValue, AutoService, Turbine |
| Testing | JUnit 4.13.2, Mockito, Truth, Hamcrest |
| Utilities | Guava 33.5.0, Apache Commons, Caffeine |

### Protobuf and gRPC

- **Protobuf 33.1** - Custom patches for lite runtime exposure
- **gRPC 1.76.0** - C++ library with Java bindings
- **gRPC-Java 1.71.0** - Multiple patches for compatibility

Proto file locations:
- `src/main/protobuf/` - Core protos
- `third_party/remoteapis/` - Remote Execution API
- `third_party/pprof/` - CPU profiling protos

### Third-Party Components

| Component | Purpose |
|-----------|---------|
| protobuf, grpc, grpc-java | Core RPC infrastructure |
| googleapis | Google API definitions with patches |
| chicory | WebAssembly runtime support |
| remoteapis | Remote Execution and Caching (REC) |
| ijar, jarjar | Java archive tools |
| asm | Java bytecode manipulation |

## 4. Build Targets and Commands

### Primary Build Targets

**Production Binary:**
```bash
# Build Bazel without embedded JDK
bazel build //src:bazel_nojdk
```

Target details:
- Main class: `com.google.devtools.build.lib.bazel.Bazel`
- Located in `//src/main/java/com/google/devtools/build/lib/bazel:BazelServer`
- Runtime dependencies include server utilities and logging handlers

**Embedded Tools:**
```bash
//src:embedded_tools_nojdk        # Minimal bazel_tools repository
//src:embedded_tools_jdk_minimal  # With minimal JDK
//src:embedded_tools_jdk_allmodules  # Full JDK modules
```

**Distribution Artifacts:**
```bash
//src:bazel-distfile      # ZIP archive with sources and bootstrap JARs
//src:bazel-distfile-tar  # TAR archive for distribution
//src:install_base_key    # MD5 hash for cache invalidation
```

### Test Targets

```bash
# Unit tests (JUnit 4)
bazel test //src/test/java/...

# Integration tests (Bash)
bazel test //src/test/shell/bazel/...

# End-to-end tests
bazel test //src/test/shell/integration/...

# Specific test suite
bazel test //src/test/shell/bazel:bazel_invocation_test
```

## 5. Build, Test, and Deploy Workflow

### Development Build

```bash
# From distribution archive with pre-generated files
./compile.sh

# Direct development build with Bazel installed
bazel build //src:bazel

# Build with specific JDK
bazel build //src:bazel --java_runtime_version=remotejdk_21
```

### Testing

```bash
# Run all Java unit tests
bazel test //src/test/java/...

# Run specific package tests
bazel test //src/test/java/com/google/devtools/build/lib/analysis/...

# Run integration tests
bazel test //src/test/shell/...

# Run with verbose output
bazel test --test_output=all //src/test/...
```

### Bootstrap Cache Management

`extensions.bzl` manages `bootstrap_repo_cache`:
- Pre-downloaded artifacts for offline builds
- Avoids network access during CI/release builds
- Contains Maven artifacts, SDK distributions, and tools

### Release Workflow

**Scripts** (`scripts/release/`):
- `release.sh` - Manages release branches and tags
- `relnotes.sh` - Generates changelog entries
- `common.sh` - Shared release utilities
- `build_bazel_binaries.yml` - BazelCI multi-platform builds

**Release Process:**
1. Create release branch from master
2. Run full test suite on all platforms
3. Build distribution artifacts
4. Generate release notes from changelog
5. Tag and push release
6. Upload artifacts to GitHub releases

## 6. Platform-Specific Considerations

### Windows
- JNI Windows filesystem library (`windows_jni.dll`)
- MSVC protobuf support via `--define=protobuf_allow_msvc=true`
- Path length limitations (259 chars) during bootstrap
- MinGW/Cygwin support in bootstrap scripts

### macOS
- Minimum OS: 10.13 (per `.bazelrc`)
- Xcode SDK detection for iOS simulator testing
- ARM64 (Apple Silicon) and x86_64 support

### Linux
- Multi-architecture: x86_64, ARM64, s390x, PowerPC, RISC-V
- Netty native transports: epoll (Linux) vs kqueue (macOS)
- glibc version requirements for distribution

## 7. Dependency Graph Overview

### RPC & Networking Layer
```
gRPC 1.76.0 ← protobuf 33.1 ← abseil-cpp
grpc-java 1.71.0 → netty 4.1.119 (with platform natives)
googleapis (API definitions) ← protobuf
```

### Build Rules & Tools
```
rules_java 9.1.0 ← rules_cc 0.2.14 ← apple_support 1.24.5
rules_python 1.7.0
bazel_skylib 1.8.2 (utility macros)
rules_pkg 1.1.0 (packaging)
```

### Testing Infrastructure
```
googletest 1.17.0 (C++ testing)
rules_fuzzing 0.6.0
rules_testing 0.9.0
```

### Serialization & Data Processing
```
protobuf 33.1 ← protoc compiler
zlib 1.3.1 (compression)
blake3 1.8.2 (hashing)
re2 2025-11-05 (regex engine)
```

### Internal Package Dependencies

Core modules with explicit visibility constraints:
- `//src/main/java/com/google/devtools/build/lib/` - Core build logic
- `//src/main/java/com/google/devtools/build/lib/bazel/` - Bazel-specific modules
- `//src/main/java/com/google/devtools/build/lib/skyframe/` - Incremental computation
- `//src/main/java/com/google/devtools/build/lib/analysis/` - Build analysis

## 8. Version Management

### Semantic Versioning
- Current development version: **9.0.0-prerelease**
- Pinned Bazel version for builds: **8.5.0** (`.bazelversion`)
- Long-term support versions maintained separately

### Java Compatibility

| Setting | Value |
|---------|-------|
| Compilation | Java 21 language features |
| Runtime | Remote JDK 25 as target |
| Available JDKs | remotejdk11, remotejdk17, remotejdk21, remotejdk25 |

Configuration:
```bash
--java_language_version=21
--java_runtime_version=remotejdk_25
--jvmopt=--sun-misc-unsafe-memory-access=allow
```

### Dependency Version Pinning

Single-version overrides enforce consistent dependency resolution:
```starlark
single_version_override(
    module_name = "grpc-java",
    version = "1.71.0",
    patches = [
        "//third_party/grpc-java:grpc-java-v1.71.0-PR-12148.patch",
        "//third_party/grpc-java:grpc-java-v1.71.0-PR-12207.patch",
    ],
)
```

### CI Configuration

**Lockfile enforcement:**
```bash
build:ci --lockfile_mode=error
```

**Platform-specific CI:**
- `.bazelci/` - Bazel CI configuration
- `.github/workflows/` - GitHub Actions for PR testing
- `build_bazel_binaries.yml` - Multi-platform release builds

## 9. Quick Reference

### Common Build Commands

```bash
# Build Bazel binary
bazel build //src:bazel

# Build with debug info
bazel build -c dbg //src:bazel

# Build for specific platform
bazel build --platforms=//platforms:linux_x86_64 //src:bazel

# Clean build
bazel clean --expunge && bazel build //src:bazel

# Query dependencies
bazel query "deps(//src:bazel)" --output=graph
```

### Common Test Commands

```bash
# Run all tests
bazel test //...

# Run tests with coverage
bazel coverage //src/test/java/...

# Run flaky tests multiple times
bazel test --runs_per_test=10 //src/test/...

# Debug test failures
bazel test --test_output=errors //src/test/...
```

### Useful Flags

```bash
--disk_cache=~/.cache/bazel  # Enable disk cache
--remote_cache=grpcs://...    # Enable remote cache
--jobs=16                     # Parallel jobs
--keep_going                  # Continue on errors
--verbose_failures            # Show command lines
--sandbox_debug               # Debug sandbox issues
```
