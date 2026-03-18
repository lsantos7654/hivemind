# uv - APIs and Interfaces

## Public APIs and Entry Points

### Command-Line Interface (Primary API)

uv's primary public interface is its command-line tool. The CLI is defined in `crates/uv-cli/src/lib.rs` using the clap library and consists of several major command namespaces:

**Top-Level Command Structure:**
```rust
pub enum Commands {
    Auth(AuthNamespace),        // Authentication management
    Project(ProjectCommand),    // Project lifecycle (flattened subcommands)
    Tool(ToolNamespace),        // Tool installation and execution
    Python(PythonNamespace),    // Python version management
    Pip(PipNamespace),          // pip-compatible interface
    Venv(VenvArgs),             // Virtual environment creation
    Build(BuildArgs),           // Package building
    Publish(PublishArgs),       // Package publishing
    Workspace(WorkspaceNamespace), // Workspace inspection
    Cache(CacheNamespace),      // Cache management
    Self_(SelfNamespace),       // uv self-management
    // ... and several hidden commands
}
```

### Project Management Commands

**`uv init [path]`** - Initialize a new Python project
```bash
# Create new project with default structure
uv init my-project

# Initialize in current directory
uv init

# With specific Python version
uv init --python 3.12
```
Implementation: `crates/uv/src/commands/project/init.rs`
- Creates `pyproject.toml` with project metadata
- Sets up basic directory structure (`src/`, `README.md`)
- Initializes `.python-version` if specified
- Can create applications or libraries

**`uv add <package>...`** - Add dependencies to project
```bash
# Add package to dependencies
uv add requests

# Add development dependency
uv add --dev pytest

# Add optional dependency group
uv add --optional database psycopg2

# Add with version constraint
uv add "django>=4.0,<5.0"

# Add from git
uv add git+https://github.com/user/repo.git

# Add with extra features
uv add "celery[redis]"
```
Implementation: `crates/uv/src/commands/project/add.rs` (54KB)
- Modifies `pyproject.toml` to add dependency
- Resolves new dependency tree
- Updates lockfile (`uv.lock`)
- Installs to virtual environment if present
- Supports multiple dependency groups (dev, optional, etc.)

**`uv remove <package>...`** - Remove dependencies
```bash
uv remove requests
uv remove --dev pytest
```
Implementation: `crates/uv/src/commands/project/remove.rs`

**`uv lock`** - Create or update lockfile
```bash
# Generate/update uv.lock
uv lock

# Lock with specific Python version
uv lock --python-version 3.12

# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package requests
```
Implementation: `crates/uv/src/commands/project/lock.rs` (62KB)
- Resolves all dependencies with PubGrub algorithm
- Creates universal lockfile (cross-platform)
- Supports workspace lockfiles
- Handles optional dependencies and extras

**`uv sync`** - Synchronize environment with lockfile
```bash
# Install exact versions from lockfile
uv sync

# Sync without dev dependencies
uv sync --no-dev

# Sync only specific groups
uv sync --only-dev

# Sync with all extras
uv sync --all-extras
```
Implementation: `crates/uv/src/commands/project/sync.rs` (49KB)
- Reads `uv.lock` file
- Installs/uninstalls to match lockfile exactly
- Creates virtual environment if missing
- Handles dependency groups and extras

**`uv run <command>`** - Run command in project environment
```bash
# Run Python script
uv run python script.py

# Run installed command
uv run pytest

# Run with specific extras
uv run --extra dev -- pytest

# Run with inline dependencies
uv run --with requests -- python -c "import requests; print(requests.__version__)"
```
Implementation: `crates/uv/src/commands/project/run.rs` (78KB)
- Automatically syncs environment
- Activates virtual environment for command
- Supports PEP 723 inline script dependencies
- Can add temporary dependencies with `--with`

**`uv export`** - Export project dependencies
```bash
# Export to requirements.txt
uv export --format requirements-txt > requirements.txt

# Export for specific Python/platform
uv export --python-version 3.12 --python-platform linux
```
Implementation: `crates/uv/src/commands/project/export.rs`

**`uv tree`** - Display dependency tree
```bash
# Show dependency tree
uv tree

# Show with specific depth
uv tree --depth 2

# Invert tree (show dependents)
uv tree --invert
```
Implementation: `crates/uv/src/commands/project/tree.rs`

**`uv audit`** - Check for security vulnerabilities
```bash
# Audit project dependencies
uv audit

# Output as JSON
uv audit --output-format json
```
Implementation: `crates/uv/src/commands/project/audit.rs`

### pip-Compatible Interface

**`uv pip install <package>...`** - Install packages
```bash
# Install package
uv pip install requests

# Install from requirements file
uv pip install -r requirements.txt

# Install with constraints
uv pip install -c constraints.txt requests

# Install editable package
uv pip install -e .

# Install from URL
uv pip install https://github.com/user/repo/archive/main.zip

# Install with index URL
uv pip install --index-url https://pypi.org/simple requests
```
Implementation: `crates/uv/src/commands/pip/install.rs` (24KB)
- Resolves dependencies
- Downloads wheels/sdists
- Builds source distributions if needed
- Installs into active/specified virtual environment

**`uv pip compile <input>`** - Compile requirements
```bash
# Compile requirements.in to requirements.txt
uv pip compile requirements.in -o requirements.txt

# Universal resolution (cross-platform)
uv pip compile --universal requirements.in

# Pin all dependencies
uv pip compile --generate-hashes requirements.in

# Upgrade specific package
uv pip compile --upgrade-package requests requirements.in
```
Implementation: `crates/uv/src/commands/pip/compile.rs` (32KB)
- Resolves dependency tree
- Outputs pinned versions
- Supports multiple output formats
- Can generate hashes for verification

**`uv pip sync <requirements>`** - Sync environment
```bash
# Sync to exact requirements
uv pip sync requirements.txt

# Dry run
uv pip sync --dry-run requirements.txt
```
Implementation: `crates/uv/src/commands/pip/sync.rs` (20KB)
- Installs/uninstalls to match requirements exactly
- Faster alternative to `pip install -r` + uninstall extras

**`uv pip list`** - List installed packages
```bash
# List all packages
uv pip list

# List in freeze format
uv pip list --format freeze

# List as JSON
uv pip list --format json

# Exclude editable packages
uv pip list --exclude-editable
```
Implementation: `crates/uv/src/commands/pip/list.rs`

**`uv pip show <package>`** - Show package information
```bash
uv pip show requests
```
Implementation: `crates/uv/src/commands/pip/show.rs`

**`uv pip freeze`** - Output installed packages in requirements format
```bash
uv pip freeze > requirements.txt
uv pip freeze --exclude-editable
```
Implementation: `crates/uv/src/commands/pip/freeze.rs`

**`uv pip uninstall <package>...`** - Uninstall packages
```bash
uv pip uninstall requests
uv pip uninstall -r requirements.txt
```
Implementation: `crates/uv/src/commands/pip/uninstall.rs`

**`uv pip tree`** - Display dependency tree
```bash
uv pip tree
uv pip tree --package requests
```
Implementation: `crates/uv/src/commands/pip/tree.rs`

### Python Version Management

**`uv python install <version>...`** - Install Python versions
```bash
# Install specific version
uv python install 3.12

# Install multiple versions
uv python install 3.11 3.12 3.13

# Install with variant
uv python install 3.13t  # Free-threaded

# Install from specific source
uv python install cpython@3.12.3
```
Implementation: `crates/uv/src/commands/python/install.rs`
- Downloads prebuilt Python binaries
- Installs to uv-managed location
- Supports CPython, PyPy, GraalPy

**`uv python list`** - List available Python installations
```bash
# List all available
uv python list

# List only installed
uv python list --only-installed

# Output as JSON
uv python list --format json
```

**`uv python find <version>`** - Find Python installation
```bash
uv python find 3.12
uv python find ">=3.10"
```

**`uv python pin <version>`** - Pin Python version
```bash
# Pin to specific version
uv python pin 3.12

# Creates/updates .python-version file
```

**`uv python uninstall <version>`** - Uninstall Python version
```bash
uv python uninstall 3.11
```

### Tool Management (pipx-like)

**`uv tool run <command>` / `uvx <command>`** - Run tool in ephemeral environment
```bash
# Run tool once
uvx ruff check .

# Run with specific version
uvx ruff@0.1.0 check .

# Run from URL
uvx --from git+https://github.com/user/tool.git tool-command
```
Implementation: `crates/uv/src/commands/tool/run.rs`
- Creates temporary isolated environment
- Installs tool and dependencies
- Executes command
- Cleans up after execution

**`uv tool install <package>`** - Install tool globally
```bash
# Install tool
uv tool install ruff

# Install with specific version
uv tool install ruff==0.1.0

# Install with extras
uv tool install "black[jupyter]"
```
Implementation: `crates/uv/src/commands/tool/install.rs`
- Installs to `~/.local/bin` (or platform equivalent)
- Creates isolated environment per tool
- Makes executables available in PATH

**`uv tool list`** - List installed tools
```bash
uv tool list
uv tool list --show-paths
```

**`uv tool uninstall <tool>`** - Uninstall tool
```bash
uv tool uninstall ruff
```

**`uv tool upgrade <tool>`** - Upgrade tool
```bash
uv tool upgrade ruff
uv tool upgrade --all
```

### Virtual Environment Management

**`uv venv [path]`** - Create virtual environment
```bash
# Create .venv in current directory
uv venv

# Create at specific path
uv venv /path/to/venv

# Use specific Python version
uv venv --python 3.12

# Create with seed packages
uv venv --seed
```
Implementation: `crates/uv/src/commands/venv.rs`
Location: `crates/uv-virtualenv/` for core implementation
- Pure Rust implementation (no Python required)
- Faster than Python's venv module
- Compatible with standard virtual environments
- Supports different Python implementations

### Package Building and Publishing

**`uv build [path]`** - Build distributions
```bash
# Build both sdist and wheel
uv build

# Build only wheel
uv build --wheel

# Build only sdist
uv build --sdist

# Build from specific directory
uv build /path/to/project

# Build from sdist
uv build --wheel dist/package-1.0.tar.gz
```
Implementation: `crates/uv/src/commands/build_frontend.rs`
- Implements PEP 517 build frontend
- Supports any PEP 517-compliant build backend
- Can build wheels from sdists

**`uv publish [files]`** - Publish to package index
```bash
# Publish all distributions in dist/
uv publish

# Publish specific files
uv publish dist/package-1.0-py3-none-any.whl

# Publish to specific index
uv publish --publish-url https://test.pypi.org/legacy/

# Use trusted publishing (GitHub Actions)
uv publish --trusted-publishing always
```
Implementation: `crates/uv/src/commands/publish.rs`
- Uploads to PyPI or private indexes
- Supports username/password authentication
- Supports token authentication
- Supports trusted publishing (OIDC)

### Cache Management

**`uv cache clean [package]`** - Clean cache
```bash
# Clean entire cache
uv cache clean

# Clean specific package
uv cache clean requests

# Dry run
uv cache clean --dry-run
```

**`uv cache prune`** - Remove unused cache entries
```bash
uv cache prune
uv cache prune --ci  # Aggressive pruning for CI
```

**`uv cache dir`** - Show cache directory
```bash
uv cache dir
# Outputs: /home/user/.cache/uv (or platform-specific path)
```

**`uv cache size`** - Show cache size
```bash
uv cache size
```

### Authentication Management

**`uv auth login <host>`** - Configure authentication
```bash
# Configure credentials for private index
uv auth login pypi.company.com

# With specific username
uv auth login --username user pypi.company.com
```

**`uv auth logout <host>`** - Remove credentials
```bash
uv auth logout pypi.company.com
```

### Self-Management

**`uv self update`** - Update uv itself
```bash
uv self update
```
Note: Only available in standalone installations, not pip-installed versions

## Key Classes, Functions, and Macros

### Core Resolver API (`uv-resolver`)

**`Resolver` struct** - Main dependency resolution engine
```rust
// From: crates/uv-resolver/src/resolver/mod.rs
pub struct Resolver<Provider: ResolverProvider, InstalledPackages: InstalledPackagesProvider> {
    // Internal PubGrub state
    // Package selection strategy
    // Dependency manifest
}

impl Resolver {
    pub async fn resolve(
        &mut self,
        requirements: &[Requirement],
    ) -> Result<ResolutionGraph> {
        // Implements PubGrub resolution algorithm
        // Returns directed acyclic graph of dependencies
    }
}
```

**`ResolutionGraph`** - Resolved dependency graph
```rust
pub struct ResolutionGraph {
    // Package versions and dependencies
    // Distribution metadata
    // Extras and markers evaluation
}

impl ResolutionGraph {
    pub fn packages(&self) -> impl Iterator<Item = &Package>;
    pub fn dependencies(&self, package: &Package) -> &[Dependency];
}
```

### Installer API (`uv-installer`)

**`Installer`** - Package installation orchestrator
```rust
// From: crates/uv-installer/src/installer.rs
pub struct Installer<'a> {
    // Virtual environment path
    // Download client
    // Cache reference
}

impl Installer {
    pub async fn install(
        &mut self,
        resolution: &ResolutionGraph,
    ) -> Result<Vec<CachedDist>> {
        // Download distributions
        // Build source distributions
        // Install wheels into venv
    }
}
```

### Distribution API (`uv-distribution`)

**`DistributionDatabase`** - Distribution metadata and download
```rust
// From: crates/uv-distribution/src/lib.rs
pub struct DistributionDatabase<'a, Context: BuildContext> {
    // HTTP client
    // Cache
    // Build dispatcher
}

impl DistributionDatabase {
    pub async fn get_or_build_wheel_metadata(
        &self,
        dist: &Dist,
    ) -> Result<Metadata> {
        // Fetch wheel metadata
        // Or build wheel and extract metadata
    }
}
```

### Python Interpreter API (`uv-python`)

**`PythonEnvironment`** - Represents Python installation
```rust
// From: crates/uv-python/src/environment.rs
pub struct PythonEnvironment {
    pub root: PathBuf,         // Venv or system Python root
    pub interpreter: Interpreter,
}

impl PythonEnvironment {
    pub fn from_root(root: &Path) -> Result<Self>;
    pub fn from_virtualenv(cache: &Cache) -> Result<Self>;
}
```

**`Interpreter`** - Python interpreter metadata
```rust
pub struct Interpreter {
    pub platform: Platform,
    pub python_version: Version,
    pub implementation_name: ImplementationName,
    pub implementation_version: Version,
}
```

### Cache API (`uv-cache`)

**`Cache`** - Global cache management
```rust
// From: crates/uv-cache/src/lib.rs
pub struct Cache {
    root: PathBuf,  // Cache directory root
}

impl Cache {
    pub fn from_settings(cache_dir: Option<PathBuf>) -> Result<Self>;
    pub fn bucket(&self, name: &str) -> CacheBucket;
    pub fn wheel(&self, wheel: &WheelFilename) -> CachedWheel;
}
```

### PEP 508 Parser (`uv-pep508`)

**`Requirement`** - Dependency requirement
```rust
// From: crates/uv-pep508/src/lib.rs
pub struct Requirement {
    pub name: PackageName,
    pub extras: Vec<ExtraName>,
    pub version_or_url: Option<VersionOrUrl>,
    pub marker: Option<MarkerTree>,
}

impl FromStr for Requirement {
    // Parse PEP 508 requirement string
    fn from_str(s: &str) -> Result<Self>;
}
```
Example:
```rust
let req: Requirement = "requests[security]>=2.28.0; python_version >= '3.8'".parse()?;
```

### PEP 440 Version Handling (`uv-pep440`)

**`Version`** - Python version
```rust
// From: crates/uv-pep440/src/lib.rs
pub struct Version {
    epoch: u32,
    release: Vec<u32>,
    pre: Option<Prerelease>,
    // ...
}

impl Version {
    pub fn from_str(s: &str) -> Result<Self>;
    pub fn contains(&self, specifier: &VersionSpecifier) -> bool;
}
```

### Settings and Configuration (`uv-settings`)

**`Settings`** - Aggregated configuration
```rust
// From: crates/uv-settings/src/lib.rs
pub struct Settings {
    pub index_url: Option<IndexUrl>,
    pub extra_index_url: Vec<IndexUrl>,
    pub find_links: Vec<FlatIndexLocation>,
    pub python_downloads: PythonDownloads,
    // ... many more settings
}
```

Settings are loaded from:
1. Command-line arguments (highest priority)
2. Environment variables
3. `pyproject.toml` `[tool.uv]` section
4. `uv.toml` configuration file
5. User-level config (`~/.config/uv/uv.toml`)
6. Defaults (lowest priority)

## Usage Examples with Code Snippets

### Example 1: Create and Setup New Project
```bash
# Initialize new project
uv init my-app
cd my-app

# Add dependencies
uv add fastapi uvicorn

# Add dev dependencies
uv add --dev pytest pytest-asyncio

# Pin Python version
uv python pin 3.12

# Run application
uv run uvicorn main:app --reload
```

### Example 2: pip-Compatible Workflow
```bash
# Create virtual environment
uv venv

# Activate (optional with uv, but traditional)
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install from requirements
uv pip install -r requirements.txt

# Compile new requirements
uv pip compile requirements.in -o requirements.txt

# Sync environment
uv pip sync requirements.txt
```

### Example 3: Tool Installation and Usage
```bash
# Install tool globally
uv tool install ruff

# Use installed tool
ruff check .

# Or run without installing
uvx black .

# Run specific version
uvx ruff@0.1.0 check .
```

### Example 4: Multi-Python Testing
```bash
# Install multiple Python versions
uv python install 3.10 3.11 3.12

# Create venv with specific version
uv venv --python 3.10 .venv-310
uv venv --python 3.11 .venv-311
uv venv --python 3.12 .venv-312

# Run tests against each
uv run --python 3.10 pytest
uv run --python 3.11 pytest
uv run --python 3.12 pytest
```

### Example 5: Workspace Management
```bash
# Create workspace with multiple packages
mkdir my-workspace && cd my-workspace

# Initialize root
uv init

# Create workspace members
uv init --lib packages/core
uv init --lib packages/utils

# Add workspace configuration to root pyproject.toml
cat >> pyproject.toml << EOF
[tool.uv.workspace]
members = ["packages/*"]
EOF

# Add inter-workspace dependencies
cd packages/core
uv add --editable ../utils

# Lock entire workspace
cd ../..
uv lock

# Sync all workspace members
uv sync --all-packages
```

## Integration Patterns and Workflows

### CI/CD Integration Pattern

**GitHub Actions Example:**
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest

      - name: Run linter
        run: uv run ruff check .
```

### Docker Integration Pattern

**Dockerfile Example:**
```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no venv in Docker)
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

# Run application
CMD ["uv", "run", "python", "-m", "myapp"]
```

### Pre-commit Hook Integration

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.10.11
    hooks:
      - id: uv-lock
      - id: uv-export
```

## Configuration Options and Extension Points

### pyproject.toml Configuration
```toml
[project]
name = "my-package"
version = "0.1.0"
dependencies = [
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
# Package index configuration
index-url = "https://pypi.org/simple"
extra-index-url = ["https://download.pytorch.org/whl/cpu"]

# Dependency resolution
resolution = "highest"  # or "lowest", "lowest-direct"
prerelease = "disallow"  # or "allow", "if-necessary"

# Python version constraints
python-version = "3.12"
python-downloads = "automatic"  # or "manual", "never"

# Workspace configuration
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]

# Development overrides
[tool.uv.sources]
my-local-package = { path = "../my-local-package", editable = true }
my-git-package = { git = "https://github.com/user/repo", tag = "v1.0" }
```

### uv.toml Configuration
```toml
# Separate uv-specific configuration file
index-url = "https://pypi.org/simple"
no-cache = false
python-downloads = "automatic"

[pip]
index-url = "https://pypi.org/simple"
find-links = ["https://download.pytorch.org/whl/cpu"]
```

### Environment Variables

Key environment variables for configuration:
```bash
# Cache location
export UV_CACHE_DIR=/custom/cache

# Python preference
export UV_PYTHON_PREFERENCE=managed  # or "system", "only-managed"

# Index URL
export UV_INDEX_URL=https://pypi.org/simple

# Offline mode
export UV_OFFLINE=1

# Disable color
export UV_NO_COLOR=1

# Working directory
export UV_PROJECT=/path/to/project

# Custom config file
export UV_CONFIG_FILE=/path/to/uv.toml
```

See `crates/uv-static/src/env_vars.rs` for complete list.
