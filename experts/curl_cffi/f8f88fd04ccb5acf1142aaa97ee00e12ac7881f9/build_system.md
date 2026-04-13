# curl_cffi — Build System

## Build System Type and Configuration Files

`curl_cffi` uses **setuptools** with a **CFFI** extension as its build backend, supplemented by a `Makefile` for developer workflow tasks and `cibuildwheel` for CI binary wheel publishing.

Key configuration files:

| File | Role |
|---|---|
| `pyproject.toml` | PEP 517/518 project metadata, dependencies, cibuildwheel config, pytest/ruff/mypy settings |
| `setup.py` | Minimal: declares `cffi_modules` pointing at `scripts/build.py:ffibuilder`; custom `bdist_wheel_abi3` tag |
| `scripts/build.py` | Core CFFI builder: detects architecture, downloads `libcurl-impersonate`, configures `ffibuilder` |
| `libs.json` | Architecture matrix: maps (system, machine, pointer_size, libc) → download URL and link strategy |
| `Makefile` | Developer targets: `preprocess`, `build`, `test`, `lint`, `format`, `clean`, `gen-const` |
| `ffi/cdef.c` | CFFI C declarations consumed by `ffibuilder.cdef()` |
| `ffi/shim.c` / `ffi/shim.h` | C shim that wraps `curl_easy_setopt`'s varargs into a single `void*` parameter |

## External Dependencies

### Runtime (from `pyproject.toml`)

```
cffi>=2.0.0        — C FFI layer; required at runtime for the compiled _wrapper extension
certifi>=2024.2.2  — Default CA bundle (overridden by SSL_CERT_FILE / CURL_CA_BUNDLE)
```

### Optional extras

```
[cli]   rich                    — Coloured CLI output
[extra] readability-lxml, markdownify, lxml_html_clean  — Response.markdown()
[dev]   charset_normalizer, coverage, cryptography, httpx==0.23.1,
        mypy, pytest, pytest-asyncio, pytest-trio, ruff, trio,
        trustme, uvicorn, websockets, typing_extensions
[test]  charset_normalizer, cryptography, litestar, httpx==0.23.1,
        proxy.py, pytest, pytest-asyncio, pytest-trio,
        python-multipart, trio, trustme, uvicorn, websockets,
        typing_extensions
[build] cibuildwheel, wheel
```

### Native / C dependencies

The extension links against **`libcurl-impersonate`** — a patched fork of libcurl that adds `curl_easy_impersonate()`. This library is **not installed from PyPI**; it is downloaded automatically during the build:

- On Linux/macOS: a static archive (`libcurl-impersonate.a`) is statically linked into `_wrapper.so`, resulting in a self-contained wheel with no system curl dependency.
- On Windows: a DLL (`libcurl-impersonate.dll`) is bundled using `delvewheel` during the wheel repair step.

The download URL is constructed by `scripts/build.py` from the architecture detected in `libs.json`:
```
https://github.com/lexiforest/curl-impersonate/releases/download/v{VERSION}/
    libcurl-impersonate-v{VERSION}.{arch}-{sysname}.tar.gz
```
Current bundled version: **curl-impersonate 1.5.2** / libcurl 8.15.0.

## Build Targets and Commands

### Preprocessing (required before any source build)

```bash
make preprocess
```

This target:
1. Downloads the curl source (`curl-8_15_0.zip`).
2. Downloads `curl-impersonate` patches.
3. Applies the impersonate patch (`curl.patch`) to the curl source.
4. Runs `autoreconf -fi` to regenerate the configure script.
5. Copies patched `include/curl/` headers into the repo root's `include/` directory.
6. Creates a `.preprocessed` sentinel file.

The patched headers are needed so that `ffi/cdef.c` can declare `curl_easy_impersonate()` and other non-upstream functions.

### Building a wheel

```bash
make build
# Equivalent to:
make preprocess
pip install build
python -m build --wheel
```

Output goes to `dist/`.

### Installing in editable mode (development)

```bash
pip install -e .[dev]
# or just:
make install-editable
```

The first time, CFFI compiles `_wrapper.so` in-place. Subsequent runs skip compilation unless C sources change.

### Generating `const.py` (after updating libcurl headers)

```bash
make gen-const
# Runs:
python3 scripts/generate_consts.py curl-8_15_0
```

This reads the patched curl headers and regenerates `curl_cffi/const.py`.

### Running tests

```bash
make test                              # unit tests only (fast, no network)
python -m pytest tests/unittest        # same
python -m pytest tests/integration    # integration tests (needs test servers)
python -m pytest tests/threads        # threading tests
```

Unit tests (`tests/unittest/`) spin up local `litestar`/`uvicorn` servers and test against them; they do not need external network access. Integration tests may require additional infrastructure.

Test configuration in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Linting and formatting

```bash
make lint      # ruff check --exclude issues
make format    # ruff format --exclude issues
```

Ruff configuration:
```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "UP", "B", "SIM"]
ignore = ["UP007", "UP045"]
```

### Cleaning

```bash
make clean
# Removes: build/, dist/, *.egg-info/, curl source dirs, generated .c/.so files, .preprocessed, include/
```

## CI/CD — cibuildwheel

The project uses **cibuildwheel** for publishing binary wheels. Configuration is in `pyproject.toml` under `[tool.cibuildwheel]`.

### Platforms and architectures built

| Platform | Architectures |
|---|---|
| Linux (glibc) | x86_64, aarch64, riscv64, i686, armv7l |
| Linux (musl) | x86_64, aarch64 |
| macOS | x86_64, arm64 |
| Windows | AMD64, ARM64 |
| Android | arm64_v8a, x86_64 |

### Free-threaded wheels

Special `cp314t-*` builds are included for Python 3.14 free-threaded (PEP 703) variants on major platforms.

### ABI3 wheel tagging

`setup.py` overrides `bdist_wheel` with `bdist_wheel_abi3` to tag all CPython wheels as `cp310.abi3` (compatible back to Python 3.10). Free-threaded and Android builds are exempt and keep their original tags.

### Build workflow steps

```yaml
before-all: make preprocess     # Linux/Windows
before-all: gmake preprocess    # macOS (Homebrew make)
before-build: pip install delvewheel   # Windows only
repair-wheel-command: delvewheel repair --add-path ./lib64;./lib32;./libarm64 ...
```

`cibuildwheel` then runs the unit tests inside each wheel:
```toml
test-requires = "pytest"
test-command = "python -bb -m pytest {project}/tests/unittest"
test-extras = ["test"]
```

Skipped test targets (missing `trustme` support):
- `cp310-manylinux_i686`, `cp310-win_arm64`, `cp314t-win_arm64`, `cp310-manylinux_armv7l`, `cp310-manylinux_riscv64`

## How the CFFI Extension Is Compiled

`scripts/build.py` creates one `FFI` instance (`ffibuilder`) which:

1. Calls `ffibuilder.set_source("curl_cffi._wrapper", ...)` with:
   - Source file: `ffi/shim.c` (the `_curl_easy_setopt` vararg shim).
   - Include dirs: repo `include/` (patched curl headers), `ffi/`, arch-specific lib `include/`.
   - Link strategy: static link on Linux/macOS via `--whole-archive`/`-force_load`; dynamic on Windows.
   - C++ stdlib (`-lstdc++` / `-lc++`) for the libcurl static archive.

2. Calls `ffibuilder.cdef(cdef_content)` with the declarations from `ffi/cdef.c`.

The resulting `_wrapper.so` exposes `ffi` and `lib` objects. `lib` contains all C functions declared in `cdef.c`; `ffi` provides Python↔C type coercion and `@ffi.def_extern()` callback registration.

## Homebrew Distribution

A formula is included at `Formula/curl-cffi.rb` and tracked in the `lexiforest/curl_cffi` tap, allowing installation via:
```bash
brew tap lexiforest/curl_cffi
brew install curl-cffi
```

`scripts/homebrew.py` helps generate updated formula versions on release.
