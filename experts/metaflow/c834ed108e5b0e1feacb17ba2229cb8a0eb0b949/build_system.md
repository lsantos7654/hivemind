# Metaflow Build System

## Build System Type and Configuration Files

Metaflow uses **setuptools** as its primary build system, configured through traditional Python packaging files:

**Primary Configuration**:
- `setup.py`: Main setuptools configuration script
- `setup.cfg`: Additional setuptools metadata
- `MANIFEST.in`: Specifies additional files to include in distribution
- `tox.ini`: Test automation configuration (minimal configuration)

**Supporting Files**:
- `.pre-commit-config.yaml`: Pre-commit hooks for code quality
- `.gitignore`: Source control exclusions
- `metaflow/version.py`: Single source of truth for version information

The build system is deliberately simple and standards-based, avoiding modern alternatives like pyproject.toml to maintain broad compatibility across Python versions 3.6-3.13.

## External Dependencies and Management

**Core Runtime Dependencies** (from `setup.py`):
```python
install_requires = ["requests", "boto3"]
```

Metaflow has a minimal dependency footprint by design. Only two external packages are required:
- **requests**: HTTP client for communicating with metadata services and APIs
- **boto3**: AWS SDK for cloud integration (S3, Batch, Step Functions)

**Optional Dependencies**:
```python
extras_require = {
    "stubs": ["metaflow-stubs==%s" % version],
}
```

The `stubs` extra provides type hints for IDE support, distributed as a separate package.

**Vendored Dependencies**: To minimize external dependencies and ensure compatibility, Metaflow vendors several packages in `metaflow/_vendor/`:
- **click**: CLI framework (version 7.x vendored for stability)
- **yaml** (PyYAML): Configuration file parsing
- **packaging**: Python package version handling
- **importlib_metadata**: Package metadata utilities with Python 3.6/3.7 compatibility shims
- **typeguard**: Runtime type checking
- **typing_extensions**: Backported type hints for older Python versions
- **imghdr**: Image format detection

Vendoring these dependencies eliminates version conflicts and ensures consistent behavior across environments.

**Cloud and Plugin Dependencies**: Metaflow does not explicitly declare cloud-specific dependencies (kubernetes client, Azure SDK, GCP client) in setup.py. These are optional and installed separately based on deployment needs. The decorators gracefully handle missing dependencies with informative error messages.

**Development Dependencies**: Not specified in setup.py but typically include:
- pytest: Testing framework
- black/isort: Code formatting
- mypy: Type checking
- pre-commit: Git hooks

## Build Targets and Commands

**Standard Python Installation**:
```bash
# Install from PyPI
pip install metaflow

# Install from source (development mode)
pip install -e .

# Install with type stubs
pip install metaflow[stubs]
```

**Conda Installation**:
```bash
conda install -c conda-forge metaflow
```

**Build Distribution Packages**:
```bash
# Build source distribution and wheel
python setup.py sdist bdist_wheel

# Modern alternative using build
python -m build
```

**Key Build Artifacts**:
- **Console Scripts**: Two entry points are registered:
  - `metaflow`: Main CLI command (`metaflow.cmd.main_cli:start`)
  - `metaflow-dev`: Development wrapper utility (`metaflow.cmd.make_wrapper:main`)

- **Package Data**: Specific non-Python files are included in the package:
  ```python
  package_data = {
      "metaflow": [
          "tutorials/*/*",                      # Tutorial files
          "plugins/env_escape/configurations/*/*",  # Environment configs
          "py.typed",                           # PEP 561 type marker
          "**/*.pyi",                          # Type stub files
      ]
  }
  ```

- **Data Files**: Development tools are installed separately:
  ```python
  data_files = [("share/metaflow/devtools", find_devtools_files())]
  ```

**Version Management**: Version is extracted from `metaflow/version.py`:
```python
with open("metaflow/version.py", mode="r") as f:
    version = f.read().splitlines()[0].split("=")[1].strip(" \"'")
```

This single-source-of-truth approach ensures consistency across package metadata, __version__ attributes, and release artifacts.

## How to Build, Test, and Deploy

### Building the Project

**From Source**:
```bash
# Clone the repository
git clone https://github.com/Netflix/metaflow.git
cd metaflow

# Install in development mode
pip install -e .

# Or build distribution packages
python setup.py sdist bdist_wheel
```

**Development Setup**:
```bash
# Install with editable mode and dev tools
pip install -e .
pip install pytest black mypy pre-commit

# Set up pre-commit hooks
pre-commit install
```

### Testing

**Test Structure**: Tests are organized in the `test/` directory:
- `test/core/`: Core framework tests
- `test/data/`: Data handling tests
- `test/env_escape/`: Environment isolation tests
- `test/extensions/`: Extension system tests
- `test/parallel/`: Parallel execution tests
- `test/unit/`: Unit tests

**Running Tests**:
```bash
# Run test runner script
./test_runner

# Or use pytest directly
pytest test/

# Run specific test categories
pytest test/core/
pytest test/unit/
```

**Test Automation**: The `tox.ini` file provides minimal configuration for tox-based testing, though the primary test runner is the custom `test_runner` script.

**Type Checking**: The project includes type stubs in `stubs/` directory:
```bash
# Test type stubs
python stubs/test/test_stubs.yml

# Run mypy
mypy metaflow/
```

**Pre-commit Checks**: Code quality is enforced through pre-commit hooks configured in `.pre-commit-config.yaml`. These run automatically before commits and include formatting, linting, and basic validation.

### Deploying

**Publishing to PyPI**:
```bash
# Build distributions
python setup.py sdist bdist_wheel

# Upload to PyPI (maintainers only)
twine upload dist/*
```

**User Installation**:
```bash
# Latest stable version
pip install metaflow

# Specific version
pip install metaflow==2.x.x

# With optional dependencies
pip install metaflow[stubs]

# Via conda
conda install -c conda-forge metaflow
```

**Configuration After Installation**:
```bash
# Configure Metaflow
metaflow configure aws
metaflow configure kubernetes

# Verify installation
metaflow status

# Access tutorials
metaflow tutorials pull
```

**Cloud Infrastructure Setup**: Metaflow flows require infrastructure for production use:
- **AWS**: S3 for storage, Batch for compute, Step Functions for orchestration
- **Kubernetes**: K8s cluster with configured namespaces and service accounts
- **Metadata Service**: Optional service for centralized metadata tracking

The configuration process is documented at https://outerbounds.com/engineering/welcome/ and varies by cloud provider.

**Extension Installation**: Users can install extensions separately:
```bash
pip install metaflow-aws
pip install metaflow-card-*  # Various card types
```

Extensions are automatically discovered through the `metaflow_extensions` package namespace and loaded at import time.

## Package Distribution

**Package Name**: `metaflow` on PyPI
**License**: Apache Software License 2.0
**Python Versions**: 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
**Operating Systems**: macOS, Linux (POSIX)

**Package Metadata** (from `setup.py`):
```python
setup(
    name="metaflow",
    version=version,
    description="Metaflow: More AI and ML, Less Engineering",
    author="Metaflow Developers",
    author_email="help@metaflow.org",
    license="Apache Software License",
    project_urls={
        "Source": "https://github.com/Netflix/metaflow",
        "Issues": "https://github.com/Netflix/metaflow/issues",
        "Documentation": "https://docs.metaflow.org",
    },
)
```

**Release Process**: The project uses semantic versioning and maintains release notes at https://github.com/Netflix/metaflow/releases. Each release includes:
- Source distribution (.tar.gz)
- Wheel distribution (.whl)
- GitHub release with changelog
- Synchronized conda-forge package

**Development Status**: Production/Stable (Development Status 5)

## Special Build Considerations

**R Integration**: The `R/` directory contains R language bindings that are packaged separately as an R package, not through setup.py.

**UI Components**: The Cards UI (`metaflow/plugins/cards/ui/`) is a React/TypeScript application with its own build system (npm/package.json). Built artifacts are included in the Python package.

**Platform-Specific Code**: While Metaflow supports macOS and Linux, Windows support is limited. Some platform-specific code paths exist for:
- Process management (subprocess vs multiprocessing)
- File path handling
- Signal handling

**Compatibility Shims**: The `metaflow/_vendor/v3_6/` and `metaflow/_vendor/v3_7/` directories contain version-specific shims for older Python versions, ensuring consistent behavior across 3.6-3.13.

**Extension Loading**: The `metaflow/extension_support/` module implements dynamic extension loading at import time. Extensions can override core behavior through well-defined hooks without modifying core code.
