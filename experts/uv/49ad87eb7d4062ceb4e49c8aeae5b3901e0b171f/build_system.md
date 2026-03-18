# uv - Build System

## Build System Type and Configuration Files

uv uses **Cargo** as its primary build system since it's a Rust project. Additionally, it uses **maturin** to package the Rust binary as a Python package for distribution via PyPI. This dual-build approach allows uv to be distributed both as a standalone binary and as a Python package installable with pip.

### Primary Build Configuration Files

**`Cargo.toml` (Workspace Manifest)**:
- Defines a Cargo workspace with 67 member crates
- Centralizes dependency versions across all workspace members
- Configures build profiles (release, profiling, dev variants)
- Sets workspace-wide metadata (edition, rust-version, license)
- Manages workspace-level lints and compiler settings

**`pyproject.toml` (Python Package)**:
- Specifies maturin as the build backend (`build-system.requires`)
- Defines Python package metadata (name, version, description, authors)
- Lists supported Python versions (3.8-3.15)
- Configures maturin build settings (bindings = "bin", manifest path)
- Contains rooster changelog generation configuration

**`rust-toolchain.toml`**:
- Pins the exact Rust toolchain version
- Ensures consistent builds across development environments
- Currently requires Rust 1.92.0 or later

**`clippy.toml`**:
- Configures Clippy linter rules
- Enables pedantic warnings with selective allows
- Enforces code quality standards

**`.cargo/config.toml`**:
- Platform-specific build configuration
- Target-specific compiler flags and settings
- Linker configurations

## External Dependencies and Management

### Rust Dependencies

uv has extensive Rust dependencies managed through Cargo. The workspace defines ~100+ external dependencies in `[workspace.dependencies]` with version constraints.

**Core Infrastructure Dependencies:**
```toml
tokio = "1.40.0"          # Async runtime
reqwest = "0.12.22"        # HTTP client
serde = "1.0.210"          # Serialization
anyhow = "1.0.89"          # Error handling
clap = "4.5.17"            # CLI parsing
thiserror = "2.0.0"        # Error derive macros
tracing = "0.1.40"         # Structured logging
```

**Python Ecosystem Dependencies:**
```toml
pubgrub = "0.3.3"                    # Dependency resolution (forked as astral-pubgrub)
version-ranges = "0.1.3"             # Version range handling
pep440_rs = via uv-pep440           # PEP 440 implementation
pep508_rs = via uv-pep508           # PEP 508 implementation
```

**Performance-Critical Dependencies:**
```toml
rkyv = "0.8.14"                      # Zero-copy deserialization for cache
rustc-hash = "2.0.0"                 # Fast hash algorithm
dashmap = "6.1.0"                    # Concurrent hash map
rayon = "1.10.0"                     # Data parallelism
boxcar = "0.2.5"                     # Lock-free data structures
```

**Filesystem and Archive Handling:**
```toml
fs-err = "3.2.2"                     # Better filesystem errors
tempfile = "3.14.0"                  # Temporary file creation
walkdir = "2.5.0"                    # Directory traversal
globset = "0.4.15"                   # Glob pattern matching
zip = "8.1.0"                        # ZIP archive handling
tar = "0.4.43"                       # TAR archive handling
async_zip = "0.0.17"                 # Async ZIP (astral fork)
flate2 = "1.0.33"                    # Compression (using zlib-rs)
zstd = "0.13.3"                      # Zstandard compression
xz2 = "0.1.7"                        # XZ/LZMA compression
```

**Network and HTTP:**
```toml
reqwest-middleware = "0.4.2"         # Request middleware (astral fork)
reqwest-retry = "0.8.0"              # Retry logic (astral fork)
async_http_range_reader = "0.9.1"   # HTTP range requests (astral fork)
h2 = "0.4.7"                         # HTTP/2 implementation
```

**Parsing and Data Formats:**
```toml
toml = "0.9.2"                       # TOML parsing
toml_edit = "0.24.0"                 # TOML editing
serde_json = "1.0.128"               # JSON serialization
csv = "1.3.0"                        # CSV parsing
regex = "1.10.6"                     # Regular expressions
pest = via dependencies               # PEG parser generator
```

**Cryptography and Security:**
```toml
sha2 = "0.10.8"                      # SHA-2 hashing
md-5 = "0.10.6"                      # MD5 hashing
blake2 = "0.10.6"                    # BLAKE2 hashing
hex = "0.4.3"                        # Hex encoding
base64 = "0.22.1"                    # Base64 encoding
```

**Platform-Specific:**
```toml
# Windows
windows = "0.61.0"                   # Windows API bindings
windows-registry = "0.5.0"           # Registry access
junction = "1.4.2"                   # Junction point handling

# Unix/Linux
nix = "0.31.2"                       # Unix system calls
procfs = "0.18.0"                    # /proc filesystem access

# macOS
security-framework = "3"             # Keychain access
```

**Testing Dependencies:**
```toml
insta = "1.46.0"                     # Snapshot testing
assert_cmd = "2.0.16"                # CLI testing
assert_fs = "1.1.2"                  # Filesystem assertions
wiremock = "0.6.4"                   # HTTP mocking
test-case = "3.3.1"                  # Parameterized tests
predicates = "3.1.2"                 # Boolean predicates
```

### Python Dependencies (for tooling and docs)

uv itself is written in Rust and has no runtime Python dependencies, but development dependencies include:

```toml
[dependency-groups]
docs = [
    "black>=23.10.0",                # Code formatting in docs
    "mkdocs>=1.5.0",                 # Documentation generator
    "mkdocs-material>=9.1.18",       # Material theme
    "mkdocs-redirects>=1.2.2",       # Redirect handling
    # ... other doc dependencies
]
```

### Dependency Management Strategy

1. **Version Pinning**: All workspace dependencies pinned to specific versions in workspace `Cargo.toml`
2. **Workspace Dependencies**: Path dependencies for internal crates (e.g., `uv-cache = { workspace = true }`)
3. **Feature Flags**: Selective features enabled per dependency (e.g., `tokio = { features = ["fs", "io-util"] }`)
4. **Astral Forks**: Several dependencies forked and maintained by Astral (pubgrub, reqwest-middleware, async_zip)
5. **Lock Files**: Both `Cargo.lock` and `uv.lock` committed to ensure reproducible builds
6. **Minimal Dependencies**: Feature `default-features = false` used to minimize dependency bloat

## Build Targets and Commands

### Development Builds

**Standard Debug Build:**
```bash
cargo build
# Output: target/debug/uv
```

**Run Without Building:**
```bash
cargo run -- <uv-args>
# Example: cargo run -- pip install requests
```

**Optimized Dev Build (faster than debug, smaller than release):**
```bash
cargo build --profile fast-build
# Uses profile.fast-build: opt-level=1, debug=0
```

### Release Builds

**Standard Release Build:**
```bash
cargo build --release
# Output: target/release/uv
# Uses: lto="fat", strip=true, opt-level=3 (implicit)
```

**Profiling Build (for benchmarks):**
```bash
cargo build --profile profiling
# Similar to release but: lto=false, debug="full", strip=false
# Faster compile times, includes debug info for profiling
```

**Minimal Size Build (for uv-build):**
```bash
cargo build --profile minimal-size
# Uses: opt-level="z", panic="abort", codegen-units=1
```

**Distribution Build (for releases):**
```bash
cargo build --profile dist
# Inherits from release profile
# Used by cargo-dist for official releases
```

### Testing

**Run All Tests:**
```bash
cargo test
# Or with nextest (recommended):
cargo nextest run
```

**Run Specific Test:**
```bash
cargo nextest run -E 'test(test_name)'
```

**Snapshot Testing with insta:**
```bash
# Run tests and update snapshots
cargo insta test --accept --test-runner nextest

# Review snapshot changes
cargo insta review
```

**Run Tests for Specific Package:**
```bash
cargo test -p uv-resolver
```

**Feature-Gated Tests:**
```bash
# Some tests require specific features
cargo test --all-features
# Or disable certain features:
cargo test --no-default-features
```

### Linting and Formatting

**Format Code:**
```bash
cargo fmt --all
```

**Check Formatting:**
```bash
cargo fmt --all -- --check
```

**Run Clippy:**
```bash
cargo clippy --all-targets --all-features
```

**Fix Clippy Warnings:**
```bash
cargo clippy --fix --all-targets --all-features
```

### Python Package Build (maturin)

**Build Python Wheel:**
```bash
# Install maturin
pip install maturin

# Build wheel
maturin build --release
# Output: target/wheels/uv-*.whl
```

**Develop Install (editable):**
```bash
maturin develop
# Installs current code in editable mode
```

**Build and Publish to PyPI:**
```bash
maturin publish
# Requires PyPI credentials
```

### Documentation

**Build Rust API Docs:**
```bash
cargo doc --no-deps --open
# Opens: target/doc/uv/index.html
```

**Build User Documentation (MkDocs):**
```bash
# Install dependencies
uv sync --group docs

# Serve locally
mkdocs serve
# View at: http://127.0.0.1:8000

# Build static site
mkdocs build
# Output: site/
```

### Benchmarking

**Run Benchmarks:**
```bash
cargo bench
# Or with the profiling profile:
cargo build --profile profiling -p uv
```

**Compare Against Other Tools:**
```bash
cd scripts/benchmark
uv run resolver --uv-project --poetry --pdm --pip-compile \
    --benchmark resolve-warm --benchmark resolve-cold \
    --json ../requirements/trio.in
```

### Platform-Specific Builds

**Cross-Compilation:**
```bash
# Install cargo-zigbuild for cross-compilation
cargo install cargo-zigbuild

# Build for specific target
cargo zigbuild --target x86_64-unknown-linux-gnu --release
```

**Docker Build:**
```bash
docker build -t uv .
# Uses multi-stage build from Dockerfile
```

### Development Utilities

**Check Compilation Without Building:**
```bash
cargo check
cargo check --all-features
```

**Clean Build Artifacts:**
```bash
cargo clean
```

**Update Dependencies:**
```bash
cargo update
```

**Audit Dependencies for Security Issues:**
```bash
cargo audit
# Requires: cargo install cargo-audit
```

**Check for Unused Dependencies:**
```bash
cargo udeps
# Requires: cargo install cargo-udeps --locked
```

## How to Build, Test, and Deploy

### Local Development Setup

1. **Prerequisites:**
   ```bash
   # Install Rust (via rustup)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

   # Install C compiler (Ubuntu/Debian)
   sudo apt install build-essential

   # Install nextest (recommended)
   cargo install cargo-nextest --locked

   # Install insta for snapshot testing
   cargo install cargo-insta --locked
   ```

2. **Clone and Build:**
   ```bash
   git clone https://github.com/astral-sh/uv.git
   cd uv
   cargo build --release
   ```

3. **Install Python Versions for Testing:**
   ```bash
   cargo run python install
   # Installs Python versions needed for tests
   ```

4. **Run Tests:**
   ```bash
   cargo nextest run
   cargo insta test --accept --test-runner nextest
   ```

### CI/CD Pipeline

uv uses GitHub Actions for continuous integration and deployment:

1. **Testing Workflow** (`.github/workflows/ci.yml`):
   - Runs on every push and PR
   - Tests on Linux, macOS, Windows
   - Multiple Python versions
   - Cargo test, clippy, fmt checks
   - Snapshot validation

2. **Release Workflow**:
   - Triggered by version tags
   - Builds binaries for all platforms
   - Creates Python wheels via maturin
   - Publishes to PyPI
   - Creates GitHub release with artifacts
   - Uses cargo-dist for distribution

3. **Benchmark Workflow**:
   - Runs performance benchmarks on main branch
   - Compares against pip, poetry, pdm
   - Updates benchmark charts in README

### Deployment Process

**Official Releases:**

1. **Version Bump:**
   - Update version in `Cargo.toml`, `pyproject.toml`, and `crates/uv-version/Cargo.toml`
   - Update `CHANGELOG.md` using rooster tool
   - Commit changes

2. **Create Release Tag:**
   ```bash
   git tag v0.10.11
   git push origin v0.10.11
   ```

3. **Automated Build and Publish:**
   - GitHub Actions builds binaries for all platforms
   - Maturin builds Python wheels
   - cargo-dist creates installers (shell script, PowerShell)
   - Artifacts uploaded to GitHub release
   - Python wheels published to PyPI
   - Docker images built and pushed

4. **Distribution Channels:**
   - PyPI: `pip install uv`
   - Standalone installer: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Homebrew: `brew install uv`
   - Docker: `docker pull ghcr.io/astral-sh/uv`
   - GitHub releases: Direct binary downloads

**Self-Update Mechanism:**
```bash
uv self update
# Uses axoupdater to fetch and install latest release
# Only available in builds with self-update feature flag
```

### Build Performance Notes

- **Incremental Builds**: Cargo caches compiled dependencies, typical rebuild <30s
- **Full Clean Build**: ~5-10 minutes depending on hardware
- **LTO Impact**: Full LTO (release profile) adds significant compile time but reduces binary size and improves runtime
- **Profiling Profile**: Trades LTO for faster iteration (53s vs 3m47s with full LTO)
- **Parallel Compilation**: Cargo parallelizes by default, benefits from multi-core CPUs
- **Release Binary Size**: ~15-25 MB after stripping (varies by platform)

### Platform Support

**Tier 1 Platforms** (tested in CI):
- Linux: x86_64, aarch64
- macOS: x86_64 (Intel), aarch64 (Apple Silicon)
- Windows: x86_64

**Tier 2 Platforms** (built but not extensively tested):
- Linux: armv7, s390x, powerpc64le
- FreeBSD: x86_64

See `docs/reference/platforms.md` for full platform support matrix.
