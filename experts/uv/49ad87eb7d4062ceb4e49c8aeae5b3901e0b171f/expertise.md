This expert provides deep knowledge in the following areas:

### Core Package Management
- **Dependency Resolution**: PubGrub algorithm implementation, version constraint solving, conflict resolution, fork strategies
- **Package Installation**: Wheel installation, source distribution building, editable installations, reinstall logic
- **Lockfile Management**: Universal lockfile format, cross-platform resolution, lockfile generation and updates
- **Cache System**: Global cache architecture, cache key generation, reflink/hardlink strategies, cache pruning
- **Index Interaction**: PyPI API client, multiple index support, find-links, authentication, trusted hosts

### CLI Commands and Workflows
- **Project Commands**: init, add, remove, lock, sync, run, export, tree, audit
- **pip Interface**: pip install, compile, sync, list, show, freeze, uninstall, tree
- **Python Management**: python install, list, find, pin, uninstall
- **Tool Management**: tool run (uvx), install, list, uninstall, upgrade
- **Venv Management**: venv creation, activation, Python version selection
- **Build and Publish**: build (sdist/wheel), publish to PyPI, trusted publishing
- **Cache Management**: cache clean, prune, dir, size
- **Authentication**: auth login, logout, credential storage

### Rust Architecture and Implementation
- **Workspace Structure**: 67-crate workspace organization, path dependencies, feature flags
- **Modular Design**: Clear separation of concerns, trait-based architecture, async operations
- **Build System**: Cargo profiles, maturin integration, cross-compilation, release optimization
- **Key Crates**:
  - `uv-resolver`: PubGrub implementation, resolution graph, candidate selection
  - `uv-installer`: Installation orchestration, parallel downloads, integrity verification
  - `uv-distribution`: Metadata extraction, wheel/sdist handling, build frontend
  - `uv-python`: Interpreter discovery, version management, environment detection
  - `uv-cache`: Cache architecture, storage strategies, deduplication
  - `uv-client`: HTTP client, retry logic, authentication
  - `uv-cli`: Clap-based CLI, argument parsing, subcommand structure
  - `uv-settings`: Configuration resolution, precedence rules, environment variables

### Python Standards Implementation
- **PEP 440**: Version parsing and comparison, version specifiers, normalization
- **PEP 508**: Dependency specifier parsing, marker evaluation, extras handling
- **PEP 517**: Build frontend/backend separation, build hooks, metadata extraction
- **PEP 425**: Platform tag generation, wheel compatibility checking
- **PEP 621**: pyproject.toml project metadata
- **PEP 723**: Inline script metadata for single-file scripts

### Configuration and Settings
- **Configuration Files**: pyproject.toml [tool.uv], uv.toml, user config, workspace config
- **Environment Variables**: UV_* environment variables, precedence, scoping
- **Settings Resolution**: CLI args > env vars > project config > user config > defaults
- **Workspace Configuration**: Multi-package projects, member selection, exclusions
- **Index Configuration**: Primary index, extra indexes, find-links, index strategy

### Virtual Environments
- **Pure Rust Implementation**: No Python dependency for venv creation
- **Activation**: Shell detection, PATH manipulation, environment variable setting
- **Python Selection**: Version discovery, interpreter compatibility, managed vs system Python
- **Seed Packages**: Optional pip/setuptools installation
- **Filesystem Optimizations**: Reflinks on macOS, hardlinks on Linux, symbolic links

### Dependency Resolution
- **PubGrub Algorithm**: Version SAT solving, backtracking, conflict analysis
- **Resolution Strategies**: Highest, lowest, lowest-direct
- **Fork Handling**: Platform forks, Python version forks, extra forks
- **Prerelease Handling**: Disallow, allow, if-necessary modes
- **Overrides**: Version overrides, dependency overrides, exclusions
- **Markers**: Environment marker evaluation, platform-specific dependencies

### Build Backend
- **PEP 517 Frontend**: Build isolation, backend invocation, metadata hooks
- **PEP 517 Backend**: uv's own build backend implementation
- **Build Configuration**: Config settings, backend-path, build environment
- **Source Builds**: Automatic sdist building, wheel from sdist, build caching
- **Build Tools**: Integration with setuptools, hatchling, maturin, pdm-backend

### Performance Optimizations
- **Parallel Operations**: Async downloads, parallel builds, concurrent resolution
- **Filesystem Optimizations**: Reflinks, hardlinks, sparse checkouts
- **Caching Strategies**: Metadata cache, wheel cache, git cache, HTTP cache
- **Zero-Copy Deserialization**: rkyv for cache performance
- **Memory Allocators**: Custom allocators for release builds
- **Benchmarking**: Comparison with pip, poetry, pdm; warm/cold cache scenarios

### Platform Support
- **Operating Systems**: Linux (x86_64, aarch64, armv7), macOS (Intel, Apple Silicon), Windows (x64)
- **Filesystem Capabilities**: Platform-specific installation strategies
- **Python Implementations**: CPython, PyPy, GraalPy detection and support
- **Architecture Detection**: Platform tags, libc detection, ABI compatibility

### Integration Points
- **CI/CD**: GitHub Actions, GitLab CI, pre-commit hooks, Docker integration
- **Editors**: VS Code, PyCharm, Vim/Neovim integration points
- **Build Systems**: Integration with cargo, npm, make
- **Cloud Platforms**: AWS Lambda, Google Cloud Functions, Coiled
- **Frameworks**: FastAPI, Django, Flask project setup

### Testing Infrastructure
- **Snapshot Testing**: insta crate integration, snapshot review workflow
- **Integration Tests**: End-to-end command testing, multi-platform tests
- **Fixture Management**: Test project templates, mock servers (wiremock)
- **Performance Testing**: Benchmark suite, hyperfine integration, comparison scripts
- **Feature Gating**: Test-only features, platform-specific tests

### Advanced Features
- **Workspaces**: Monorepo support, inter-package dependencies, workspace lockfiles
- **Script Execution**: Inline dependencies (PEP 723), ephemeral environments
- **Tool Isolation**: Per-tool environments, global tool installation
- **Trusted Publishing**: OIDC authentication, GitHub Actions integration
- **Security**: Audit command, hash verification, keyring integration
- **Offline Mode**: No network operation, local-only resolution

### Migration and Compatibility
- **pip Compatibility**: Drop-in replacement, command parity, behavior differences
- **poetry Migration**: pyproject.toml compatibility, lockfile conversion
- **pdm Migration**: Similar project structure, lockfile format differences
- **requirements.txt**: Full support, constraints files, editable installations
- **Backwards Compatibility**: Version policy, breaking change handling

### Error Handling and Diagnostics
- **Error Messages**: User-friendly errors, resolution conflict reporting
- **Diagnostics**: Verbose logging, trace output, show-settings debug mode
- **Conflict Resolution**: Dependency conflict explanations, resolution hints
- **Build Failures**: Build error capture, dependency installation failures

### Documentation and Help
- **CLI Help**: Extensive help text, command examples, option documentation
- **Online Documentation**: docs.astral.sh/uv, API reference, guides
- **Changelog**: CHANGELOG.md, version history, migration guides
- **Contributing**: CONTRIBUTING.md, development setup, testing guidelines
