# LCOV Build System

## Build System Type

LCOV uses **GNU Make** as its build system. There is no compilation step — LCOV tools are Perl and Python scripts installed directly. The Makefile handles installation, packaging, testing, code style checking, and release management.

## Build Configuration File

The primary build file is the top-level `Makefile` (330 lines). There is no `configure` or `CMakeLists.txt` — the project is a simple script-based tool with no native compilation.

### Key Makefile Variables

```makefile
VERSION    := $(shell bin/get_version.sh --version)    # e.g., "2.4.1"
RELEASE    := $(shell bin/get_version.sh --release)    # e.g., "1"
FULL       := $(shell bin/get_version.sh --full)       # e.g., "2.4.1-1"
PREFIX     := /usr/local                                # Install prefix
CFG_DIR    := $(PREFIX)/etc                             # Config file destination
BIN_DIR    := $(PREFIX)/bin                             # Executable destination
LIB_DIR    := $(PREFIX)/lib/lcov                        # Perl library destination
MAN_DIR    := $(PREFIX)/share/man                       # Man page destination
SHARE_DIR  := $(PREFIX)/share/lcov/                     # Data/shared files destination
SCRIPT_DIR := $(SHARE_DIR)/support-scripts              # Callback scripts destination
LCOV_PERL_PATH   := /usr/bin/perl                        # Overridable Perl path
LCOV_PYTHON_PATH := /usr/bin/python3                     # Overridable Python path
```

Install destinations can be customized via `make install PREFIX=/custom/path`.

## Make Targets

| Target | Description |
|--------|-------------|
| `all` / `info` | Prints available targets (default) |
| `install` | Installs all tools, libraries, scripts, man pages, examples, tests, and config to `$(DESTDIR)$(PREFIX)` |
| `uninstall` | Removes all installed files from `$(DESTDIR)$(PREFIX)` |
| `dist` | Creates distribution artifacts: `lcov-$(VERSION).tar.gz` and RPM packages |
| `check` / `test` | Runs the regression test suite via `tests/Makefile` |
| `clean` | Removes generated files — tarballs, RPMs, Python cache, perltidy backups |
| `checkstyle` | Runs `perltidy` on all Perl source files to verify/enforce coding style. `MODE=full` checks all files; `MODE=diff` checks only changes. `UPDATE=1` auto-fixes |
| `release` | Finalizes a release: updates version strings, commits, and creates a git tag (`v$(VERSION)`) |

## Installation Process

The `install` target performs the following steps:

1. Creates destination directories (`bin`, `lib`, `share`, `man`, `etc`)
2. Installs each executable from `bin/` with mode 755, then runs `bin/fix.pl` on it to set the correct version string, library path (`--fixlibdir`), and binary path (`--fixbindir`)
3. Installs callback scripts from `scripts/` with version fixup
4. Installs `lib/lcovutil.pm` with mode 644
5. Installs man pages from `man/` to the appropriate `man1/` and `man5/` directories
6. Copies `example/` and `tests/` directories to `$(SHARE_DIR)` for user reference
7. Installs `lcovrc` configuration file to `$(CFG_DIR)`

The `fix.pl` post-processing script is critical — it rewrites embedded Perl library paths in scripts from `../lib` to the actual installed `$LIB_DIR`, replaces version placeholders, and updates script directory references.

## External Dependencies

### Required Perl Modules
- Capture::Tiny — output capture
- DateTime — date/time handling for binning
- Digest::MD5 — line checksums
- File::Spec — cross-platform path handling
- At least one JSON module (preferred order: JSON::XS, Cpanel::JSON::XS, JSON::PP, JSON)
- Memory::Process — memory measurement for parallel throttling
- Module::Load::Conditional — dynamic module loading
- Scalar::Util — utility functions
- Time::HiRes — high-resolution timing for profiling
- TimeDate (Date::Parse) — date parsing

### Required for Specific Features
- Devel::Cover — required for Perl coverage measurement and `perl2lcov`
- GD — required for `genpng` PNG image generation
- perltidy — required for code style checking (`make checkstyle`)
- Coverage.py (Python) — required for Python coverage measurement and `py2lcov`
- xlsxwriter (Python) — required for spreadsheet/profile reports via `spreadsheet.py`

### System Requirements
- Perl 5.8.8 or newer (required by RPM spec; effectively Perl 5.10+ for modern features)
- Python 3.x for `py2lcov`, `xml2lcov`, and `xml2lcovutil.py`
- gcov (from GCC) or llvm-cov (from LLVM) for C/C++ coverage capture
- A POSIX-compatible shell for helper scripts

## Testing

### Running Tests

```bash
make test                                    # Run the full regression suite
make COVERAGE=1 test                         # Run tests and measure LCOV's own coverage
make COVERAGE=1 TESTCASE_ARGS=--keep-going test  # Continue past coverage measurement crashes
```

Tests are driven by `tests/Makefile` which includes `tests/common.mak` (shared test infrastructure) and dispatches to sub-directories:

```makefile
TESTS := genhtml lcov gendiffcov llvm2lcov py2lcov perl2lcov xml2lcov
```

When `COVERAGE=1`:
- Tests run twice — once with `LCOV_FORCE_PARALLEL=1` (parallel execution) and once without
- Perl coverage data is collected via Devel::Cover to `tests/cover_db/`
- Python coverage data is collected to `tests/pycov.dat`
- An HTML report is generated to `tests/lcov_coverage/index.html`
- `perl2lcov` and `py2lcov` translate self-coverage data, then `genhtml` produces the final report

### Test Framework Conventions

- `common.tst` provides a bash-based test framework
- `common.mak` defines shared variables (`LCOV_HOME`, `BINDIR`, `SCRIPTDIR`, etc.)
- Each test category has its own `Makefile` plus individual `.sh` test scripts
- Each test generates actual coverage data, runs LCOV tools, and compares output against expected results

## Distribution and Packaging

```bash
make dist       # Creates lcov-$(VERSION).tar.gz, .noarch.rpm, and .src.rpm
```

The `dist` target:
1. Copies source tree to a temp directory
2. Runs `bin/fix.pl` to hardcode version strings in all files
3. Generates a `CHANGES` file from git history
4. Creates a tarball with `tar cfz`
5. Builds RPM packages using `rpmbuild` from `rpm/lcov.spec`

The RPM spec (`rpm/lcov.spec`) declares LCOV as a `noarch` package requiring Perl >= 5.8.8, excludes internal Perl modules from automatic dependency resolution, and installs to `/usr` prefix with config in `/etc`.

## Release Process

```bash
make release VERSION=2.5.0     # Finalizes and tags a new release
```

Requires a clean working tree and no existing tag for the version. Steps: checkout master → update version/date strings → commit → create and sign git tag (`v2.5.0`).

## Code Style

Enforced via `.perltidyrc` (153 lines of perltidy configuration) and `.editorconfig`. Perl code uses 4-space indentation, 80-char max line length, specific brace/paren tightness rules, and operator spacing conventions. Shell scripts and Makefiles use tabs. Check with:

```bash
make checkstyle MODE=full           # Check all files
make checkstyle MODE=full UPDATE=1  # Auto-fix all files
```
