# Bazel Build System Configuration and Dependencies

## Build System Type and Configuration

Bazel is a self-hosting build system - it uses itself to build itself. The repository uses modern Bzlmod (MODULE.bazel) for dependency management while maintaining some legacy WORKSPACE support for backward compatibility.

### Primary Build Files

**MODULE.bazel**: The main module definition file declares Bazel's identity and dependencies using the Bzlmod system. Key aspects:

```starlark
module(
    name = "bazel",
    version = "8.5.1",
    repo_name = "io_bazel",
)
```

The module declares approximately 40+ direct dependencies including:
- Core infrastructure: bazel_skylib, platforms, rules_license
- Build rules: rules_java, rules_cc, rules_python, rules_proto, rules_go
- Remote execution: grpc, grpc-java, googleapis, remoteapis
- Compression: zstd-jni, zlib, blake3
- Language support: protobuf, abseil-cpp, googletest
- Documentation: stardoc
- Platform support: apple_support, rules_graalvm

**BUILD**: The root BUILD file defines top-level targets:
- File groups for source distribution
- License declarations
- Packaging targets for creating release artifacts
- Generation of the MODULE.bazel.lock.dist file for reproducible builds

**.bazelrc**: Default configuration for building Bazel includes:
- Compiler flags for C++ (C++17 standard)
- Java compilation settings
- Test configuration
- Platform-specific settings for Windows, macOS, Linux
- Remote execution configuration options

### Bootstrap Build Process

Bazel has a sophisticated bootstrap process since it needs a working Bazel to build itself:

**Phase 1 - Bootstrap Compilation (scripts/bootstrap/compile.sh)**:
- Compiles minimal Java source files directly with javac
- Uses embedded libraries from third_party
- Produces a basic "bootstrap" Bazel binary
- Does not require any pre-existing Bazel installation

**Phase 2 - Self-Build (compile.sh)**:
- Uses the bootstrap Bazel to build a full Bazel binary
- Includes all optimizations and features
- Produces the final bazel binary at output/bazel

The bootstrap process handles:
- Extracting embedded tools and JDK
- Building native C++ launcher
- Compiling Java server code
- Packaging everything into a self-contained executable

## External Dependencies Management

### Bzlmod Dependencies

Bazel uses Bzlmod for modern dependency management with semantic versioning and transitive dependency resolution. Key dependencies include:

**Build Infrastructure**:
- `bazel_skylib` (1.7.1): Starlark utility functions and rules
- `platforms` (1.0.0): Platform definitions for cross-compilation
- `rules_license` (1.0.0): License checking and compliance
- `rules_pkg` (1.0.1): Packaging rules for creating distributions

**RPC and Serialization**:
- `grpc` (1.66.0): gRPC framework for remote execution API
- `grpc-java` (1.66.0): Java gRPC implementation
- `protobuf` (29.0): Protocol buffer compiler and runtime
- `googleapis` (0.0.0-20240819): Google API protocol definitions

**Language Toolchains**:
- `rules_java` (8.14.0): Java compilation and runtime support
- `rules_cc` (0.1.1): C++ build rules
- `rules_python` (0.40.0): Python rules and toolchains
- `rules_proto` (7.0.2): Protocol buffer build rules
- `rules_go` (0.48.0): Go language support

**Platform Support**:
- `apple_support` (1.23.1): Apple platform toolchains (iOS, macOS)
- `rules_graalvm` (0.11.1): GraalVM native image support

**Testing and Quality**:
- `rules_testing` (0.6.0): Testing framework for Bazel rules
- `googletest` (1.15.2): C++ testing framework

**Utilities**:
- `zstd-jni` (1.5.6-9): Zstandard compression
- `blake3` (1.5.1): BLAKE3 hashing algorithm
- `zlib` (1.3.1): Compression library
- `chicory` (1.1.0): WebAssembly runtime

### Dependency Patches

Bazel applies patches to some dependencies to fix issues or add features:

```python
single_version_override(
    module_name = "rules_jvm_external",
    patch_strip = 1,
    patches = ["//third_party:rules_jvm_external_6.0.patch"],
    version = "6.0",
)

single_version_override(
    module_name = "rules_graalvm",
    patches = [
        "//third_party:rules_graalvm_fix.patch",
        "//third_party:rules_graalvm_unicode.patch",
    ],
)
```

### Third-Party Dependencies

The `third_party/` directory contains:

**Java Libraries**:
- ASM: Java bytecode manipulation
- JarJar: Java package renaming
- Proguard: Java obfuscation and optimization
- Android tools: DEX compiler, SDK tools

**Build Tools**:
- ijar: Creates interface JARs (headers only)
- def_parser: Windows DEF file parser

**Local Overrides**:
- remoteapis: Local copy of Remote Execution API definitions

### Maven Dependencies

Bazel uses rules_jvm_external for Maven dependency management, configured in maven_install.json. This includes:
- Auto Value: Code generation for value types
- Error Prone: Java static analysis
- JUnit: Testing framework
- Mockito: Mocking framework
- Various Google and Apache libraries

## Build Targets and Commands

### Primary Build Targets

**Main Binary**:
```bash
bazel build //src:bazel          # Full Bazel with embedded JDK
bazel build //src:bazel_nojdk    # Bazel without embedded JDK
```

**Platform-Specific Variants**:
- `//src:bazel_windows`: Windows-specific build with .exe extension
- `//src:bazel_dev`: Development build with additional debugging

**Distribution Archives**:
```bash
bazel build //src:bazel-distfile       # Source distribution
bazel build //:embedded_jdk_allmodules # Embedded JDK for distribution
```

**Java Tools**:
```bash
bazel build //src/java_tools/...       # Java compilation tools
bazel build //src/java_tools/buildjar  # Fast Java builder
bazel build //src/java_tools/singlejar # JAR merging tool
```

**Development Tools**:
```bash
bazel build //src/tools/...            # Developer tools
bazel build //src/tools/remote         # Remote execution test tools
```

### Common Build Commands

**Standard Build**:
```bash
# Build Bazel from source using bootstrap
./compile.sh

# Build with existing Bazel
bazel build //src:bazel

# Build and test
bazel test //src/test/...
```

**Testing**:
```bash
# Run all tests
bazel test //src/test/...

# Run specific test suite
bazel test //src/test/java/com/google/devtools/build/lib/...

# Run shell integration tests
bazel test //src/test/shell/...

# Run with specific test filters
bazel test //src/test/... --test_filter=SkyframeTest
```

**Development Workflow**:
```bash
# Build with compilation mode
bazel build -c dbg //src:bazel    # Debug build
bazel build -c opt //src:bazel    # Optimized build
bazel build -c fastbuild //src:bazel  # Fast development build

# Run with flags
bazel run //src:bazel -- build //my:target

# Query dependencies
bazel query 'deps(//src:bazel)'
bazel cquery 'deps(//src:bazel)' --output=graph
```

## How to Build, Test, and Deploy

### Building from Source

**Prerequisites**:
- JDK 11 or later
- C++ compiler (GCC, Clang, or MSVC)
- Python 3 (for some build scripts)
- Git

**Bootstrap Build (No Bazel Required)**:
```bash
# Clone the repository
git clone https://github.com/bazelbuild/bazel.git
cd bazel

# Bootstrap build - produces output/bazel
./compile.sh

# The resulting binary is self-contained
./output/bazel version
```

**Building with Existing Bazel**:
```bash
# Much faster if you already have Bazel installed
export BAZEL=/usr/local/bin/bazel
./compile.sh

# Or directly
bazel build //src:bazel_nojdk
```

**Platform-Specific Notes**:

*Windows*:
```bash
# Use MSYS2 or Visual Studio environment
./compile.sh
# Requires Visual C++ Build Tools
```

*macOS*:
```bash
# Requires Xcode Command Line Tools
xcode-select --install
./compile.sh
```

*Linux*:
```bash
# Requires GCC or Clang
sudo apt-get install build-essential  # Debian/Ubuntu
./compile.sh
```

### Testing

**Unit Tests**:
```bash
# Run all Java unit tests
bazel test //src/test/java/...

# Run C++ tests
bazel test //src/test/cpp/...

# Run Starlark tests
bazel test //src/test/starlark/...
```

**Integration Tests**:
```bash
# Shell-based integration tests
bazel test //src/test/shell/bazel/...

# Specific test scenarios
bazel test //src/test/shell/bazel:bazel_rules_test
```

**Test Coverage**:
```bash
# Generate coverage report
bazel coverage //src/test/java/...
```

**Performance Testing**:
```bash
# Run with profiling
bazel test --profile=/tmp/profile.json //src/test/...
bazel analyze-profile /tmp/profile.json
```

### Deployment and Distribution

**Creating a Release**:
```bash
# Build distribution archive
bazel build //:bazel-distfile

# The archive contains everything needed for offline build
# Located at bazel-bin/bazel-<version>-dist.zip
```

**Building Release Binaries**:
```bash
# Create binaries for distribution
scripts/packages/build_release.sh

# Produces:
# - bazel-<version>-linux-x86_64
# - bazel-<version>-darwin-x86_64
# - bazel-<version>-darwin-arm64
# - bazel-<version>-windows-x86_64.exe
```

**Installation**:
```bash
# From source build
sudo cp output/bazel /usr/local/bin/

# From release binary
chmod +x bazel-<version>-linux-x86_64
sudo mv bazel-<version>-linux-x86_64 /usr/local/bin/bazel
```

**Embedded JDK Builds**:
```bash
# Build with embedded JDK for distribution
bazel build --define=EMBEDDED_JDK=1 //src:bazel

# This creates a larger binary that includes Java runtime
# Users don't need separate JDK installation
```

### Continuous Integration

Bazel uses Buildkite for CI, configured in `.bazelci/`:

**CI Pipeline**:
- Builds on Linux (Ubuntu, Debian, Fedora)
- Builds on macOS (x64 and ARM64)
- Builds on Windows
- Runs full test suite on all platforms
- Performance benchmarks
- Integration tests with external projects

**Presubmit Checks**:
- Code formatting (buildifier)
- Linting
- Unit tests
- Integration tests
- Build performance regression tests

### Development Tips

**Faster Development Builds**:
```bash
# Use local caching
bazel build --disk_cache=/tmp/bazel-cache //src:bazel

# Parallel builds
bazel build --jobs=8 //src:bazel

# Reuse repository cache
bazel build --repository_cache=/tmp/bazel-repo-cache //src:bazel
```

**Debugging**:
```bash
# Build with debug info
bazel build -c dbg //src:bazel

# Verbose output
bazel build --subcommands //src:bazel

# Profile build
bazel build --profile=/tmp/profile.json //src:bazel
```

**Incremental Development**:
Bazel's incremental build is very efficient - most code changes result in fast rebuilds (seconds to minutes depending on what changed). Changes to:
- Single Java file: ~10-30 seconds
- Starlark builtins: ~30-60 seconds
- C++ client: ~30-90 seconds
- Protocol buffers: ~60-120 seconds (affects many files)

The Bazel team dogfoods Bazel extensively, so the development experience is highly optimized for rapid iteration.
