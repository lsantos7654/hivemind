# Bazel Central Registry - APIs and Interfaces

## Public APIs and Entry Points

The Bazel Central Registry provides multiple interfaces for interaction:

1. **Registry API** (Python library): `tools/registry.py` - Core programmatic interface
2. **Command-Line Tools**: Python scripts in `tools/` for module management
3. **MCP Server**: Model Context Protocol server for AI agents
4. **HTTP Registry**: Standard Bazel registry served at https://bcr.bazel.build/
5. **Git Repository**: Direct git access for contributions

## Core Python API: registry.py

The `registry.py` module (594 lines) provides the fundamental `Registry` class for all registry operations.

### Registry Class

**Initialization:**
```python
from tools.registry import Registry

# Default: current working directory
registry = Registry()

# Specify custom registry path
registry = Registry(registry_path="/path/to/bazel-central-registry")
```

**Key Methods:**

**Module Discovery:**
```python
# List all modules
modules = registry.get_all_modules()
# Returns: list of module names (strings)

# Check if module exists
exists = registry.module_exists("rules_python")
# Returns: bool
```

**Version Management:**
```python
# Get all versions of a module
versions = registry.get_module_versions("rules_python")
# Returns: list of version strings ["1.8.3", "1.8.2", ...]

# Get latest version
latest = registry.get_latest_version("rules_python")
# Returns: string (e.g., "1.8.3")

# Check if version exists
exists = registry.version_exists("rules_python", "1.8.3")
# Returns: bool
```

**Metadata Access:**
```python
# Get module metadata
metadata = registry.get_metadata("rules_python")
# Returns: dict with keys: homepage, maintainers, repository, versions, yanked_versions

# Get source information for a version
source = registry.get_source("rules_python", "1.8.3")
# Returns: dict with keys: url, integrity, strip_prefix, patches (optional), patch_strip (optional)

# Get MODULE.bazel content
module_bazel = registry.get_module_bazel("rules_python", "1.8.3")
# Returns: string (file contents)

# Get presubmit configuration
presubmit = registry.get_presubmit("rules_python", "1.8.3")
# Returns: dict (parsed YAML) or None if not present
```

**File Path Resolution:**
```python
# Get path to module directory
path = registry.get_module_path("rules_python")
# Returns: Path object

# Get path to version directory
path = registry.get_version_path("rules_python", "1.8.3")
# Returns: Path object

# Get path to specific file
path = registry.get_source_json_path("rules_python", "1.8.3")
path = registry.get_module_bazel_path("rules_python", "1.8.3")
path = registry.get_metadata_path("rules_python")
# Returns: Path object
```

**Version Parsing:**
```python
from tools.registry import Version

# Parse version string
version = Version("1.8.3")
print(version.major)  # 1
print(version.minor)  # 8
print(version.patch)  # 3

# Compare versions
v1 = Version("1.8.3")
v2 = Version("1.9.0")
print(v1 < v2)  # True

# Handle special versions
v_bcr = Version("1.2.3.bcr.1")  # BCR-specific patch
v_pseudo = Version("1.19.1-20250305-abcdef")  # Pseudo-version
v_date = Version("20260107.0")  # Date-based version
```

## Command-Line Tools API

### add_module.py - Interactive Module Addition

**Usage:**
```bash
bazel run //tools:add_module
```

**Interactive Prompts:**
1. Module name (validates against existing modules)
2. Module version (validates format)
3. Source URL (validates accessibility and format)
4. Homepage URL (module website)
5. Maintainer information:
   - GitHub username
   - Name (optional)
   - Email (optional)
6. Build targets for presubmit
7. Test targets for presubmit (optional)
8. Platforms to test on

**Generated Files:**
- `modules/<name>/metadata.json`
- `modules/<name>/<version>/MODULE.bazel`
- `modules/<name>/<version>/source.json`
- `modules/<name>/<version>/presubmit.yml`

**Example Session:**
```
$ bazel run //tools:add_module
INFO: Getting module information from user input...
ACTION: Please enter the module name:
> my_awesome_lib

ACTION: Please enter the module version:
> 1.0.0

ACTION: Please enter the source URL (e.g., GitHub release archive):
> https://github.com/myorg/my_awesome_lib/archive/v1.0.0.tar.gz

Downloading source archive...
Calculating integrity hash...
Integrity: sha256-abc123...

ACTION: Please enter the homepage URL:
> https://github.com/myorg/my_awesome_lib

ACTION: Please enter your GitHub username:
> myusername

ACTION: Build targets to test (comma-separated):
> @my_awesome_lib//:my_awesome_lib

ACTION: Platforms (comma-separated) [debian11,macos,ubuntu2204,windows]:
> debian11,macos,windows

Creating module structure...
SUCCESS: Module my_awesome_lib@1.0.0 created!
Please review the generated files and submit a PR.
```

### bcr_validation.py - Module Validation

**Usage:**
```bash
# Validate specific version
bazel run //tools:bcr_validation -- --check foo@1.0.0

# Validate all versions of module
bazel run //tools:bcr_validation -- --check foo

# Validate all modules
bazel run //tools:bcr_validation -- --check_all

# Check metadata only
bazel run //tools:bcr_validation -- --check_metadata foo

# Fix issues automatically
bazel run //tools:bcr_validation -- --check_metadata foo --fix

# Skip specific validations
bazel run //tools:bcr_validation -- --check foo@1.0.0 --skip_validation url_stability
bazel run //tools:bcr_validation -- --check foo@1.0.0 --skip_validation source_repo
```

**Validation Checks:**
1. Version exists in metadata.json
2. Source URL matches repository allowlist in metadata.json
3. Source URL stability (GitHub archives)
4. Integrity values correct for source and patches
5. Checked-in MODULE.bazel matches extracted source
6. compatibility_level consistency with previous versions
7. presubmit.yml format and content

**Exit Codes:**
- 0: All validations passed
- Non-zero: Validation failures

### calc_integrity.py - Integrity Hash Calculator

**Usage:**
```bash
# Calculate from URL
bazel run //tools:calc_integrity -- https://example.com/archive.tar.gz

# Calculate from local file
bazel run //tools:calc_integrity -- /path/to/archive.tar.gz
```

**Output:**
```
sha256-woVpUbvzDjCGGs43ZVldhroT8s8BJ52QH2xiJYxX9P8=
```

**Integration Example:**
```python
from tools.calc_integrity import calculate_integrity

# Calculate from URL
integrity = calculate_integrity("https://example.com/archive.tar.gz")

# Calculate from file
integrity = calculate_integrity("/path/to/archive.tar.gz")
```

### update_integrity.py - Update source.json Integrity

**Usage:**
```bash
# Update latest version
bazel run //tools:update_integrity -- module_name

# Update specific version
bazel run //tools:update_integrity -- --version 1.2.3 module_name
```

**What It Does:**
1. Downloads source archive from URL in source.json
2. Calculates new integrity hash
3. Updates source.json with new hash
4. Downloads and updates patch file hashes if present

**Example:**
```bash
$ bazel run //tools:update_integrity -- rules_python
Downloading https://github.com/bazel-contrib/rules_python/releases/download/1.8.3/rules_python-1.8.3.tar.gz...
Calculating integrity...
Updating modules/rules_python/1.8.3/source.json...
Updated integrity: sha256-lKK0xdnEUyOpc3+N6PhBkju2KMrOHo5R/sVSXtnM+y0=
```

### module_selector.py - Module Pattern Selection

**Usage:**
```bash
# Select specific version
bazel run //tools:module_selector -- --select "zlib@latest"

# Select with version comparison
bazel run //tools:module_selector -- --select "protobuf@>=27"

# Select with wildcards
bazel run //tools:module_selector -- --select "rules_*@latest"

# Select all latest
bazel run //tools:module_selector -- --select "*@latest"

# Multiple patterns
bazel run //tools:module_selector -- \
  --select "rules_*@latest" \
  --select "boost.*@>=1.80.0"

# Random sampling
bazel run //tools:module_selector -- \
  --select "rules_*@latest" \
  --random-percentage 20
```

**Output Format:**
```
rules_python@1.8.3
rules_go@0.50.1
rules_jvm_external@6.5
rules_kotlin@2.1.0
```

**Version Pattern Syntax:**
- `latest`: Most recent version
- `1.2.3`: Exact version
- `>=1.0.0`: Greater than or equal
- `<2.0.0`: Less than
- `>=1.0.0,<2.0.0`: Range (comma-separated)

### module_analyzer.py - Module Importance Analysis

**Usage:**
```bash
# Top 50 modules (default)
bazel run //tools:module_analyzer

# Top N modules
bazel run //tools:module_analyzer -- --top_n 10

# Exclude dev dependencies
bazel run //tools:module_analyzer -- --exclude-dev-deps

# Module names only (no scores)
bazel run //tools:module_analyzer -- --name-only

# Combined options
bazel run //tools:module_analyzer -- --top_n 20 --exclude-dev-deps --name-only
```

**Output Format (with scores):**
```
1. bazel_skylib: 0.0456
2. platforms: 0.0423
3. rules_python: 0.0391
4. rules_cc: 0.0367
5. protobuf: 0.0289
...
```

**Output Format (name-only):**
```
bazel_skylib
platforms
rules_python
rules_cc
protobuf
```

**Algorithm:** Uses PageRank on the dependency graph to determine module importance based on:
- Number of modules depending on it
- Importance of dependent modules
- Whether to include dev dependencies

### migrate_to_bzlmod.py - WORKSPACE Migration

**Usage:**
```bash
# In your project directory
/path/to/bcr/tools/migrate_to_bzlmod.py --target //foo:bar

# With options
./migrate_to_bzlmod.py \
  --target //foo:bar \
  --target //baz:qux \
  --interactive \
  --force

# Sync all dependencies
./migrate_to_bzlmod.py --sync --target //foo:bar
```

**Options:**
- `-t, --target`: Build targets to migrate (repeatable)
- `-s, --sync`: Use `bazel sync` instead of `bazel build --nobuild`
- `-f, --force`: Ignore previously generated dependencies
- `-i, --interactive`: Ask user interactively

**Workflow:**
1. Analyzes WORKSPACE dependencies for specified targets
2. Searches BCR for matching Bzlmod modules
3. Generates MODULE.bazel with bazel_dep declarations
4. Tests the migration
5. Reports missing dependencies

### setup_presubmit_repos.py - Presubmit Environment Setup

**Usage:**
```bash
bazel run //tools:setup_presubmit_repos -- --module foo@1.2.0
```

**Output:**
```
Setting up presubmit environment for foo@1.2.0...

Extracted source to: /tmp/bcr_presubmit_foo_1.2.0/source
Created test module at: /tmp/bcr_presubmit_foo_1.2.0/test

Run the following commands to test:

# Anonymous module test
cd /tmp/bcr_presubmit_foo_1.2.0/anonymous
bazel build @foo//:target

# Test module
cd /tmp/bcr_presubmit_foo_1.2.0/test
bazel test //...
```

### print_all_src_urls.py - Export Source URLs

**Usage:**
```bash
bazel run //tools:print_all_src_urls > all_urls.txt
```

**Output:**
```
https://github.com/abseil/abseil-cpp/archive/20260107.0.tar.gz
https://github.com/bazel-contrib/rules_python/releases/download/1.8.3/rules_python-1.8.3.tar.gz
https://github.com/bazelbuild/rules_go/archive/v0.50.1.tar.gz
...
```

**Use Case:** Creating mirrors for offline or internal usage.

## MCP Server API

The MCP (Model Context Protocol) server provides AI agent integration.

**Start Server:**
```bash
bazel run //tools:mcp_server
```

**Available MCP Tools:**

1. **list_modules()**: List all module names
2. **search_modules(pattern)**: Regex search for modules
3. **list_versions(module, include_yanked=False)**: List versions
4. **get_metadata(module)**: Get metadata.json
5. **get_source(module, version)**: Get source.json
6. **get_patch_file(module, version, patch_name)**: Get patch content
7. **get_module_bazel(module, version)**: Get MODULE.bazel
8. **get_presubmit_yaml(module, version)**: Get presubmit.yml
9. **get_attestations(module, version)**: Get attestations.json
10. **get_registry_info()**: Get bazel_registry.json

**Example MCP Client Integration (Python):**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP server
server_params = StdioServerParameters(
    command="bazel",
    args=["run", "//tools:mcp_server"],
    cwd="/path/to/bazel-central-registry"
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # List all modules
        result = await session.call_tool("list_modules")
        modules = result.content

        # Get module metadata
        result = await session.call_tool("get_metadata", {"module": "rules_python"})
        metadata = result.content

        # Get latest source.json
        versions = await session.call_tool("list_versions", {"module": "rules_python"})
        latest = versions.content[0]
        source = await session.call_tool("get_source", {
            "module": "rules_python",
            "version": latest
        })
```

**Gemini CLI Configuration:**
```json
{
  "mcpServers": {
    "BCR": {
      "command": "bazel",
      "args": ["run", "//tools:mcp_server"],
      "cwd": "/path/to/bazel-central-registry",
      "timeout": 5000,
      "trusted": true
    }
  }
}
```

## HTTP Registry API

The BCR is served as a standard Bazel registry at https://bcr.bazel.build/.

**Registry Structure:**
```
https://bcr.bazel.build/
├── bazel_registry.json              # Registry metadata
├── modules/
│   └── <module>/
│       ├── metadata.json            # Module metadata
│       └── <version>/
│           ├── MODULE.bazel         # Module definition
│           ├── source.json          # Source location
│           └── MODULE.bazel.intoto.jsonl  # [Optional] Attestation
```

**Accessing via HTTP:**
```bash
# Get registry info
curl https://bcr.bazel.build/bazel_registry.json

# Get module metadata
curl https://bcr.bazel.build/modules/rules_python/metadata.json

# Get version source info
curl https://bcr.bazel.build/modules/rules_python/1.8.3/source.json

# Get MODULE.bazel
curl https://bcr.bazel.build/modules/rules_python/1.8.3/MODULE.bazel
```

**Bazel Integration:**
```starlark
# In MODULE.bazel
bazel_dep(name = "rules_python", version = "1.8.3")
```

Bazel automatically fetches from the BCR:
1. Reads metadata.json to verify version exists
2. Downloads source.json to get archive URL and integrity
3. Downloads MODULE.bazel to get dependencies
4. Downloads and verifies source archive
5. Applies patches if specified
6. Builds using MODULE.bazel from extracted source

**Custom Registry:**
```bash
# Use local registry
bazel build --registry=file:///path/to/local-registry //...

# Layer custom registry on top of BCR
bazel build \
  --registry=https://my.company.com/registry \
  --registry=https://bcr.bazel.build \
  //...
```

## Configuration Options and Extension Points

### Module Configuration: metadata.json

**Required Fields:**
```json
{
  "homepage": "https://project.example.com",
  "maintainers": [
    {
      "github": "username",
      "github_user_id": 123456,
      "name": "Full Name",
      "email": "email@example.com",
      "do_not_notify": false
    }
  ],
  "repository": [
    "github:org/repo",
    "https://allowed.source.com/prefix/"
  ],
  "versions": ["1.0.0", "1.1.0"]
}
```

**Optional Fields:**
```json
{
  "yanked_versions": {
    "1.0.0": "Reason for yanking"
  },
  "deprecated": "Reason for deprecation"
}
```

### Source Configuration: source.json

**Archive Source:**
```json
{
  "type": "archive",
  "url": "https://github.com/org/repo/archive/v1.0.0.tar.gz",
  "integrity": "sha256-base64encodedvalue=",
  "strip_prefix": "repo-1.0.0",
  "patches": {
    "fix.patch": "sha256-patchhash="
  },
  "patch_strip": 1
}
```

**Git Source:**
```json
{
  "type": "git_repository",
  "url": "https://github.com/org/repo.git",
  "commit": "abcdef1234567890",
  "strip_prefix": "subdir"
}
```

### Presubmit Configuration: presubmit.yml

**Anonymous Module Test:**
```yaml
matrix:
  platform: [debian11, macos, ubuntu2204, windows]
  bazel: [7.*, 8.*, 9.*]
tasks:
  verify_targets:
    name: Verify build targets
    platform: ${{ platform }}
    bazel: ${{ bazel }}
    build_flags:
      - "--keep_going"
      - "--cxxopt=-std=c++17"
    build_targets:
      - "@my_module//:target1"
      - "@my_module//:target2"
    test_targets:
      - "@my_module//:test_target"
```

**Test Module:**
```yaml
bcr_test_module:
  module_path: "examples/bzlmod"
  matrix:
    platform: [debian11, macos, windows]
    bazel: [7.*, 8.*]
  tasks:
    run_tests:
      name: Run test module
      platform: ${{ platform }}
      bazel: ${{ bazel }}
      build_targets: ["//..."]
      test_targets: ["//..."]
```

**Incompatible Flags Override:**
```yaml
incompatible_flags:
  "--incompatible_config_setting_private_default_visibility":
    - 7.x
    - 8.x
```

### Attestation Configuration: attestations.json

```json
{
  "mediaType": "application/vnd.build.bazel.registry.attestation+json;version=1.0.0",
  "attestations": {
    "source.json": {
      "url": "https://github.com/org/repo/releases/download/v1.0.0/source.json.intoto.jsonl",
      "integrity": "sha256-hash="
    },
    "MODULE.bazel": {
      "url": "https://github.com/org/repo/releases/download/v1.0.0/MODULE.bazel.intoto.jsonl",
      "integrity": "sha256-hash="
    },
    "archive.tar.gz": {
      "url": "https://github.com/org/repo/releases/download/v1.0.0/archive.tar.gz.intoto.jsonl",
      "integrity": "sha256-hash="
    }
  }
}
```

## Integration Patterns and Workflows

### Workflow 1: Contributing a New Module Version

```bash
# 1. Clone BCR
git clone https://github.com/bazelbuild/bazel-central-registry.git
cd bazel-central-registry

# 2. Create new version using tool
bazel run //tools:add_module

# 3. Validate locally
bazel run //tools:bcr_validation -- --check mymodule@1.0.0

# 4. Test locally
bazel run //tools:setup_presubmit_repos -- --module mymodule@1.0.0
# Follow instructions to run tests

# 5. Commit and push
git checkout -b add-mymodule-1.0.0
git add modules/mymodule
git commit -m "Add mymodule 1.0.0"
git push origin add-mymodule-1.0.0

# 6. Create PR on GitHub
# CI will automatically run presubmit
# Maintainers will be notified
```

### Workflow 2: Automated Publishing with publish-to-bcr

**GitHub Action Configuration (.github/workflows/bcr.yml):**
```yaml
name: Publish to BCR
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: bazel-contrib/publish-to-bcr@v1
        with:
          module_name: my_module
          version: ${{ github.event.release.tag_name }}
          integrity: ${{ secrets.BCR_INTEGRITY }}
```

This automatically creates a PR to the BCR when you publish a GitHub release.

### Workflow 3: Migrating from WORKSPACE to Bzlmod

```bash
# 1. In your project
/path/to/bcr/tools/migrate_to_bzlmod.py \
  --target //main:app \
  --target //lib:all \
  --interactive

# 2. Review generated MODULE.bazel

# 3. Test migration
bazel test --enable_bzlmod //...

# 4. Gradually migrate
# Keep both WORKSPACE and MODULE.bazel during transition
```

### Workflow 4: Using Custom Registry with BCR Fallback

```bash
# In .bazelrc
common --registry=https://my.company.registry.com
common --registry=https://bcr.bazel.build

# Or via command line
bazel build \
  --registry=https://my.company.registry.com \
  --registry=https://bcr.bazel.build \
  //...
```

The BCR provides a comprehensive, well-documented API for module management, making it straightforward to contribute, consume, and extend the registry for various use cases.
