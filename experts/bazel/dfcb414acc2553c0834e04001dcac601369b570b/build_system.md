# Bazel Build System

## Build System Type

Bazel uses **itself** as its build system. This creates a bootstrapping scenario: to build Bazel from source, you either need an existing Bazel binary or must use the bootstrap compilation process.

The repository uses **Bzlmod** (Bazel Modules) as the modern dependency management system, defined in MODULE.bazel. This replaces the older WORKSPACE-based dependency management. The build is configured through:

- **MODULE.bazel**: Module definition and external dependencies
- **BUILD** files: Build rule definitions throughout the source tree
- **.bazelrc**: Default build configuration and flags
- **Starlark (.bzl) files**: Reusable build logic and macros

## Build Configuration Files

### MODULE.bazel (Primary Dependency Declaration)

Located at the repository root, this ~18KB file declares Bazel version 9.0.0-prerelease and lists approximately 40 direct dependencies:

```starlark
module(
    name = "bazel",
    version = "9.0.0-prerelease",
    repo_name = "io_bazel",
)

bazel_dep(name = "abseil-cpp", version = "20250814.1")
bazel_dep(name = "bazel_skylib", version = "1.8.2")
bazel_dep(name = "protobuf", version = "33.4", repo_name = "com_google_protobuf")
bazel_dep(name = "grpc", version = "1.76.0.bcr.1", repo_name = "com_github_grpc_grpc")
bazel_dep(name = "grpc-java", version = "1.71.0")
bazel_dep(name = "rules_java", version = "9.1.0")
bazel_dep(name = "rules_python", version = "1.7.0")
bazel_dep(name = "rules_go", version = "0.59.0")
# ... and many more
```

The file also defines module extensions for loading build-time dependencies like embedded JDKs and GraalVM.

### BUILD Files

The root BUILD file defines:
- Source file groups for distribution
- Bootstrap JAR packaging
- Distribution artifact generation (bazel-distfile.zip, bazel-distfile.tar)
- Platform definitions for remote execution
- Licensing information

Example targets:
```python
pkg_tar(
    name = "bazel-srcs",
    srcs = [":dist-srcs", ":generated_resources"],
)

genrule(
    name = "bazel-distfile",
    srcs = [":bazel-srcs", ":bootstrap-jars", ":maven-srcs", ...],
    outs = ["bazel-distfile.zip"],
    cmd = "$(location :combine_distfiles) $@ $(SRCS)",
)
```

### .bazelrc (Build Configuration)

Defines common build configurations:
- Remote execution settings (RBE on Google Cloud)
- Platform-specific flags for Linux, macOS, Windows
- Compiler warning suppressions for external dependencies
- Module dependency checking
- Download mirrors and caching

### .bazelversion

Specifies the exact Bazel version required to build Bazel itself (for bootstrapping with an existing binary).

## External Dependencies and Management

### Core Dependencies

**Protocol Buffers (protobuf v33.4)**: Used for:
- Internal data structures
- Remote Execution API definitions
- Build event protocol
- Action caching

**gRPC (C++ v1.76.0, Java v1.71.0)**: Powers:
- Remote execution protocol
- Remote caching
- Build event streaming
- Client-server communication

**Abseil (abseil-cpp v20250814.1)**: Common C++ and Java libraries providing:
- Enhanced standard library functionality
- Containers, algorithms, utilities
- Time handling

**Bazel Skylib (v1.8.2)**: Standard library of Starlark functions and rules.

**Language Rule Dependencies**:
- rules_java v9.1.0 - Java build rules
- rules_python v1.7.0 - Python build rules  
- rules_go v0.59.0 - Go build rules
- rules_cc v0.2.16 - C++ build rules
- apple_support v1.24.5 - Apple platform support

**Build and Test Tools**:
- googletest v1.17.0 - C++ testing framework
- rules_testing v0.9.0 - Test rule framework
- stardoc v0.8.0 - Documentation generation

**Additional Libraries**:
- blake3 v1.8.2 - Fast hashing
- re2 v2025-11-05 - Regular expressions
- zlib v1.3.1 - Compression
- zstd-jni v1.5.6-9 - Compression

### Dependency Management

**Bzlmod System**: Modern module-based dependency resolution with:
- Semantic versioning
- Automatic transitive dependency resolution
- Module extensions for custom repository rules
- Lockfile (MODULE.bazel.lock) for reproducible builds

**Maven Dependencies**: Java libraries managed through rules_jvm_external:
- Declared in maven_install.json (121KB)
- Includes gRPC Java, Netty, Guava, and other libraries
- Pinned versions for reproducibility

**Third-party Code**: The third_party/ directory contains:
- Source code for vendored dependencies
- Patches applied to upstream projects
- Custom build definitions for dependencies without Bazel support

## Build Targets and Commands

### Building Bazel from Source

**Bootstrap Process** (without existing Bazel):
```bash
./compile.sh
```

This script:
1. Compiles a minimal Bazel using javac and native compilers
2. Uses this minimal Bazel to build the full Bazel binary
3. Outputs the result to `output/bazel`

**With Existing Bazel**:
```bash
bazel build //src:bazel
```

### Key Build Targets

**Main Binary**:
- `//src:bazel` - Complete Bazel binary with embedded JDK
- `//src:bazel_nojdk` - Bazel binary without embedded JDK

**Distribution Artifacts**:
- `//:bazel-distfile` - Complete distribution ZIP
- `//:bazel-distfile-tar` - Complete distribution tarball
- `//:bazel-srcs` - Source code archive
- `//:bootstrap-jars` - Pre-built JAR dependencies

**Java Tools**:
- `//src/java_tools/buildjar:JavaBuilder` - Java compilation tool
- `//src/java_tools/singlejar:SingleJar` - JAR merging tool
- `//src/java_tools/junitrunner:Runner` - JUnit test execution

**Native Tools**:
- `//src/main/cpp:client` - C++ client binary
- `//src/tools/launcher:launcher` - Windows launcher
- `//src/tools/singlejar:singlejar` - Native singlejar implementation

### Testing

**Run All Tests**:
```bash
bazel test //...
```

**Test Categories**:
- `//src/test/java/...` - Java unit tests
- `//src/test/cpp/...` - C++ unit tests
- `//src/test/shell/...` - Shell integration tests
- `//src/test/py/...` - Python tests

**Specific Test Suites**:
```bash
bazel test //src/test/java/com/google/devtools/build/lib/...
bazel test //src/test/shell/bazel:bazel_integration_test
```

## Building, Testing, and Deploying

### Build Process

1. **Dependency Resolution**: Bzlmod resolves module dependencies and creates repository rules
2. **Loading Phase**: Parses BUILD files and evaluates Starlark code
3. **Analysis Phase**: Constructs action graph from target graph
4. **Execution Phase**: Executes actions to produce artifacts
5. **Packaging**: Combines outputs into distributable formats

### Development Workflow

**Incremental Development**:
```bash
# Build after making changes
bazel build //src:bazel

# Run specific tests
bazel test //src/test/java/com/google/devtools/build/lib/analysis:AnalysisTests

# Use local Bazel binary
./bazel-bin/src/bazel build //...
```

**Remote Execution** (for Bazel contributors):
```bash
bazel build --config=remote //src:bazel
```

Uses Google's Remote Build Execution (RBE) infrastructure.

### Deployment Process

**Creating a Release**:
1. Generate distribution artifacts:
   ```bash
   bazel build //:bazel-distfile
   ```

2. The distfile includes:
   - All source code
   - Pre-built bootstrap JARs
   - Maven dependencies
   - Embedded JDK (platform-specific)

3. Users can build from distfile without internet access:
   ```bash
   unzip bazel-distfile.zip
   cd bazel-*
   ./compile.sh
   ```

**Installation Methods**:
- Binary releases: Pre-built binaries for major platforms
- Package managers: apt, homebrew, chocolatey
- Bazelisk: Version manager that auto-downloads correct version
- From source: Using distfile or git repository

### Continuous Integration

The repository uses Bazel CI (Buildkite-based) configured in `.bazelci/`:
- `presubmit.yml` - Pre-merge testing
- `postsubmit.yml` - Post-merge validation
- `build_bazel_binaries.yml` - Binary artifact creation

Tests run on:
- Linux (Ubuntu, multiple versions)
- macOS (multiple versions)
- Windows (multiple versions)
- Various architectures (x86_64, arm64)

### Performance Optimization

**Build Flags**:
```bash
# Optimize for speed
bazel build -c opt //src:bazel

# Enable remote caching
bazel build --remote_cache=grpcs://remote.cache.com //...

# Parallel execution
bazel build --jobs=50 //...

# Resource limits
bazel build --local_ram_resources=HOST_RAM*0.8 //...
```

The Bazel build system demonstrates "eating your own dog food" - using Bazel to build Bazel ensures the tool can handle complex, large-scale builds with multiple languages and deep dependency graphs.
