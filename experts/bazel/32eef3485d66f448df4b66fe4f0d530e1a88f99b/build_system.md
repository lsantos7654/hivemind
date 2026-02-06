# Bazel Build System Architecture

## Build System Type and Configuration

Bazel is a **self-hosting build system** that uses Bazel itself (via Bzlmod) for dependency management. The repository uses a bootstrap process to compile Bazel without requiring an existing Bazel installation, solving the chicken-and-egg problem.

### Build System Overview

- **Type**: Self-hosted artifact-based build system
- **Primary Language**: Java (build system core), C++ (native client), Starlark (rules)
- **Dependency Management**: Bzlmod (MODULE.bazel) for modern dependency resolution
- **Build Definition**: BUILD files throughout the repository define build targets
- **Configuration**: .bazelrc provides default build options

## Configuration Files

### MODULE.bazel - Module Definition

The MODULE.bazel file (463 lines) defines Bazel as a Bzlmod module with all external dependencies.

**Module Declaration:**
```starlark
module(
    name = "bazel",
    version = "9.0.0-prerelease",
    repo_name = "io_bazel",
)
```

**Key Dependencies:**

| Dependency | Version | Purpose |
|------------|---------|---------|
| abseil-cpp | 20250814.1 | C++ utility libraries |
| bazel_skylib | 1.8.2 | Starlark utility functions |
| protobuf | 33.4 | Protocol buffer support |
| grpc | 1.76.0.bcr.1 | gRPC for remote execution |
| rules_java | 9.1.0 | Java build rules |
| rules_cc | 0.2.16 | C++ build rules |
| rules_python | 1.7.0 | Python build rules |
| rules_go | 0.59.0 | Go build rules |
| googletest | 1.17.0.bcr.2 | C++ testing framework |
| re2 | 2025-11-05.bcr.1 | Regular expression library |
| zlib | 1.3.1.bcr.7 | Compression library |

The file also includes single_version_override directives for applying patches to dependencies like rules_graalvm, googleapis, and zstd-jni.

### .bazelrc - Build Configuration

Default build options for the Bazel repository, including:
- Compiler flags and optimization settings
- Platform-specific configurations
- Remote execution settings
- Test configurations

### BUILD Files

The root BUILD file defines:
- Source filegroups (`srcs`)
- Bootstrap JAR packaging (`bootstrap-jars`)
- Distribution targets
- License declarations

## External Dependencies and Management

### Bzlmod Dependency Resolution

Bazel uses Bzlmod (MODULE.bazel) for deterministic, version-aware dependency management:

1. **Module Resolution**: Bzlmod resolves all transitive dependencies using Minimal Version Selection (MVS)
2. **Lock File**: MODULE.bazel.lock pins exact resolved versions
3. **Central Registry**: Dependencies are fetched from the Bazel Central Registry (BCR)
4. **Module Extensions**: Custom logic for complex dependency patterns

### Third-party Dependencies

The `third_party/` directory contains:
- Patches for external dependencies
- Vendored code that cannot be fetched externally
- gRPC protocol definitions
- Build file templates

### Repository Rules

External dependencies are managed through repository rules defined in:
- `repositories.bzl` - Legacy workspace-style repository definitions
- `distdir.bzl` - Distribution directory management
- `extensions.bzl` - Bzlmod module extensions

## Build Targets and Commands

### Primary Build Targets

**src:bazel** - Main Bazel binary
```bash
bazel build //src:bazel
```
Produces the complete Bazel binary with embedded JDK.

**src:bazel_nojdk** - Bazel binary without embedded JDK
```bash
bazel build //src:bazel_nojdk
```
Lighter binary that uses system JDK.

**src:bazel_bootstrap_jar** - Core Bazel JAR
```bash
bazel build //src:bazel_bootstrap_jar
```
The Java server implementation without native wrapper.

**scripts/packages:package-bazel** - Distribution packages
```bash
bazel build //scripts/packages:package-bazel
```
Creates distribution packages (tar.gz, deb, rpm, etc.)

### Test Targets

**Run all tests:**
```bash
bazel test //src/test/...
```

**Java unit tests:**
```bash
bazel test //src/test/java/...
```

**Shell integration tests:**
```bash
bazel test //src/test/shell/...
```

**Specific test suites:**
```bash
bazel test //src/test/java/com/google/devtools/build/lib/...:all
bazel test //src/test/shell/bazel:bazel_rules_test
```

### Query Targets

**List all Java libraries:**
```bash
bazel query 'kind(java_library, //src/...)'
```

**Find dependencies:**
```bash
bazel query 'deps(//src:bazel)'
```

**Reverse dependencies:**
```bash
bazel query 'rdeps(//src/..., //src/main/java/com/google/devtools/build/lib/actions:actions)'
```

## Bootstrap Process

The bootstrap process compiles Bazel from source without requiring an existing Bazel installation.

### compile.sh - Bootstrap Compilation

The `compile.sh` script (80 lines) orchestrates the bootstrap:

**Phase 1: Environment Setup**
```bash
source scripts/bootstrap/buildenv.sh
```
- Detects platform (Linux, macOS, Windows)
- Verifies required tools (Java, C++ compiler, protoc)
- Sets build environment variables

**Phase 2: Initial Binary Creation**
If no existing Bazel binary is provided:
```bash
source scripts/bootstrap/compile.sh
```
- Compiles Java sources directly with javac
- Generates protobuf code
- Creates bootstrap JAR
- Compiles native launcher (C++)
- Produces initial `bazel` binary

**Phase 3: Self-hosted Build**
```bash
source scripts/bootstrap/bootstrap.sh
```
- Uses bootstrap binary to build final Bazel
- Executes: `bazel build src:bazel_nojdk`
- Copies result to `output/bazel`

### Bootstrap Build Modes

**Clean bootstrap (no existing Bazel):**
```bash
./compile.sh
```

**Use existing Bazel binary:**
```bash
BAZEL=/path/to/bazel ./compile.sh
```

**With custom label:**
```bash
EMBED_LABEL="custom-version" ./compile.sh
```

## Building and Testing Bazel

### Development Build

**Standard development build:**
```bash
bazel build //src:bazel
./bazel-bin/src/bazel version
```

**Fast iterative builds:**
```bash
bazel build -c fastbuild //src:bazel_nojdk
```

**Optimized release build:**
```bash
bazel build -c opt //src:bazel
```

### Running Tests

**All tests (can take hours):**
```bash
bazel test //...
```

**Fast unit tests only:**
```bash
bazel test --test_tag_filters=-slow //src/test/java/...
```

**Specific subsystem tests:**
```bash
bazel test //src/test/java/com/google/devtools/build/lib/skyframe/...
```

**With test output:**
```bash
bazel test --test_output=all //src/test/java/com/google/devtools/build/lib/analysis:RuleContextTest
```

### Code Generation

**Generate protocol buffers:**
```bash
bazel build //src/main/protobuf:all
```

**Build documentation:**
```bash
bazel build //src/main/java/com/google/devtools/build/docgen:docgen
```

**Generate Starlark documentation:**
```bash
bazel build //src/main/java/com/google/devtools/build/skydoc:skydoc
```

## Deployment and Distribution

### Creating Distribution Packages

**Tar archive:**
```bash
bazel build //scripts/packages:bazel-bin.tar
```

**Debian package:**
```bash
bazel build //scripts/packages:bazel-debian.deb
```

**RPM package:**
```bash
bazel build //scripts/packages:bazel.rpm
```

**Windows installer:**
```bash
bazel build //scripts/packages:bazel-installer.msi
```

### Release Process

The release process is documented in `scripts/release/`:

1. **Version Update**: Update version in MODULE.bazel and related files
2. **Changelog**: Update CHANGELOG.md with release notes
3. **Build Artifacts**: Run release build script
4. **Create Distribution**: Package for all platforms
5. **Upload**: Upload to GitHub releases
6. **Announce**: Publish release notes

### Platform-specific Builds

**Linux:**
```bash
bazel build --platforms=@platforms//os:linux //src:bazel
```

**macOS:**
```bash
bazel build --platforms=@platforms//os:macos //src:bazel
```

**Windows:**
```bash
bazel build --platforms=@platforms//os:windows //src:bazel.exe
```

## CI/CD Integration

### Bazel CI (.bazelci/)

The `.bazelci/` directory contains configuration for Bazel's continuous integration:

- **presubmit.yml**: Tests run on every pull request
- **postsubmit.yml**: Additional tests after merge
- **Buildkite pipelines**: Configuration for Buildkite CI

### GitHub Actions (.github/workflows/)

GitHub Actions are used for:
- Pull request validation
- Issue management
- Release automation
- Documentation deployment

### Test Execution in CI

CI runs extensive test suites across platforms:
- **Linux**: Ubuntu latest, various configurations
- **macOS**: Multiple macOS versions
- **Windows**: Windows Server
- **Multiple JDK versions**: JDK 11, 17, 21

### Performance Testing

Bazel CI includes performance benchmarks:
- Build time measurements
- Memory usage profiling
- Cache hit rate analysis
- Incremental build performance

## Build Optimization

### Local Caching

Bazel automatically caches build outputs in:
- **Output base**: `~/.cache/bazel/_bazel_$USER/`
- **Repository cache**: `~/.cache/bazel/_bazel_$USER/cache/repos/`

### Remote Caching

Configure remote cache for the Bazel repository:
```bash
bazel build --remote_cache=grpc://cache.example.com:9092 //src:bazel
```

### Build Performance Tips

**Use remote execution:**
```bash
bazel build --remote_executor=grpc://rbe.example.com:443 //src:bazel
```

**Limit parallelism:**
```bash
bazel build --jobs=8 //src:bazel
```

**Profile builds:**
```bash
bazel build --profile=profile.json //src:bazel
bazel analyze-profile profile.json
```

**Clean selectively:**
```bash
bazel clean  # Clean output
bazel clean --expunge  # Also remove cache
```

## Development Workflow

### Typical Development Cycle

1. **Make code changes** in `src/main/java/` or other source directories
2. **Build incrementally**: `bazel build //src:bazel_nojdk`
3. **Run affected tests**: `bazel test //src/test/java/com/google/devtools/build/lib/...`
4. **Verify with integration test**: `./bazel-bin/src/bazel_nojdk build //examples/...`
5. **Run full test suite** before submitting (optional but recommended)

### Debugging Builds

**Verbose output:**
```bash
bazel build -s //src:bazel  # Show all commands
```

**Debug logging:**
```bash
bazel --host_jvm_args=-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005 build //src:bazel
```

**Inspect action outputs:**
```bash
bazel aquery //src:bazel
```

This build system architecture demonstrates Bazel's self-hosting capability and provides multiple entry points for building, testing, and deploying Bazel itself.
