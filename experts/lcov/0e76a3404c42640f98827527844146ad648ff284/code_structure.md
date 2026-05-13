# LCOV Code Structure

## Top-Level Layout

```
lcov/
├── bin/                  # Executable scripts — the main LCOV tools
├── lib/                  # Shared Perl library
├── scripts/              # User-supplied callback scripts (VCS integration, criteria, etc.)
├── man/                  # Man pages (sections 1 and 5)
├── example/              # Example C program with differential coverage demo
├── tests/                # Regression test suite
├── rpm/                  # RPM packaging spec file
├── lcovrc                # Default system-wide configuration file
├── Makefile              # Build, install, test, and release automation
├── README                # Comprehensive project documentation
├── COPYING               # GPLv2 license
├── CONTRIBUTING          # Contribution guidelines (coding style, signed-off-by)
├── .perltidyrc           # Perl code formatting rules (perltidy configuration)
├── .editorconfig         # Editor configuration (indentation, line endings)
├── .gitignore            # Git ignore rules
├── .gitattributes        # Git attributes
└── .github/              # GitHub configuration (dependabot.yml)
```

## `bin/` — Main Executable Tools

The `bin/` directory contains all the primary LCOV executables. Each is a standalone script that sources the shared `lcovutil.pm` library from `../lib/`.

| File | Lines | Language | Purpose |
|------|-------|----------|---------|
| `lcov` | 2,058 | Perl | Main front-end: captures coverage data, combines tracefiles, lists/extracts/removes data, kernel coverage support |
| `geninfo` | 4,182 | Perl | Internal tool that calls gcov/llvm-cov and generates `.info` tracefiles from `.gcno`/`.gcda` or JSON intermediate format |
| `genhtml` | 14,293 | Perl | Generates interactive HTML coverage reports with differential analysis, date/owner binning, navigation, and hierarchical views |
| `genpng` | 398 | Perl | Generates PNG overview images of source files (requires GD.pm), used with `--frames` option |
| `gendesc` | 190 | Perl | Converts test name/description text files into description format consumed by genhtml |
| `perl2lcov` | 444 | Perl | Translates Perl Devel::Cover coverage databases to `.info` format |
| `py2lcov` | 212 | Python | Translates Python Coverage.py data to `.info` format (via intermediate XML or direct Coverage.py Python API) |
| `xml2lcov` | 110 | Python | Translates Cobertura-style XML coverage data to `.info` format |
| `xml2lcovutil.py` | 499 | Python | Shared Python module used by both `py2lcov` and `xml2lcov`; contains `ProcessFile` class |
| `llvm2lcov` | 545 | Perl | Translates LLVM `llvm-cov export -format=text` JSON output to `.info` format |
| `fix.pl` | small | Perl | Post-install fixup script that rewrites version strings, library paths, and binary paths in installed files |
| `copy_dates.sh` | small | Shell | Copies file timestamps for distribution tarballs |
| `get_changes.sh` | small | Shell | Generates CHANGES file from git log |
| `get_version.sh` | small | Shell | Extracts version strings from the repository |
| `checkstyle.sh` | small | Shell | Runs `perltidy` in check mode against source files |

## `lib/` — Core Shared Library

| File | Lines | Language | Purpose |
|------|-------|----------|---------|
| `lcovutil.pm` | 10,016 | Perl | The monolithic shared library for all Perl-based LCOV tools. Provides: error type definitions (30+ named error codes with `$ERROR_*` variables), configuration parameter parsing (`parseOptions`, `apply_rc_params`), coverage filter definitions (`$FILTER_BRANCH_NO_COND`, `$FILTER_LINE_CLOSE_BRACE`, `$FILTER_BLANK_LINE`, etc. — 14 filter types), parallel execution framework (`init_parallel_params`, `report_parallel_error`, fork/join management), callback infrastructure (`configure_callback`, `cleanup_callbacks`), file path substitution (`subst_file_name`, `strip_directories`), message/warning/error handling (`define_errors`, `ignorable_error`, `ignorable_warning`, `warn_once`), color palettes for HTML/PNG output (`%normal_palette`, `%dark_palette`, `%tlaColor`, `%tlaTextColor`), coverage rate computation (`rate`, `get_overall_line`), C++ demangling support, external file classification (`is_external`), file extension mappings (`%languageExtensions`), version caching, checksum computation, and utility functions (`system_no_output`, `create_temp_dir`, `temp_cleanup`, `transform_pattern`, `munge_file_patterns`). |

The library exports over 100 symbols used by the main tools. It is imported via `use lib "$FindBin::RealBin/../lib"; use lcovutil qw(...)`.

## `scripts/` — Callback Scripts

These are user-supplied scripts that plug into LCOV's callback infrastructure. They are installed to `$PREFIX/share/lcov/support-scripts/`.

| File | Language | Purpose |
|------|----------|---------|
| `gitblame` | Perl | Wrapper executable for `gitblame.pm` — calls git blame and formats output per LCOV annotation spec |
| `gitblame.pm` | Perl | Perl module implementing git blame annotation; supports `--p4` (Perforce mapping), `--cache` (performance caching), `--prefix`, and `--abbrev` flags |
| `gitdiff` | Perl | Generates unified diffs between two git SHAs for differential coverage baselines |
| `gitversion` | Perl | Wrapper executable for `gitversion.pm` — extracts file version from git |
| `gitversion.pm` | Perl | Perl module implementing git version extraction callbacks |
| `batchGitVersion.pm` | Perl | Batch version extraction for multiple files (optimized git log invocation) |
| `p4annotate` | Perl | Wrapper for `p4annotate.pm` — Perforce blame annotation |
| `p4annotate.pm` | Perl | Perforce annotation module |
| `p4udiff` | Perl | Generates unified diffs from Perforce for baseline coverage |
| `P4version.pm` | Perl | Perforce version extraction module |
| `getp4version` | Perl | Wrapper for Perforce version extraction |
| `criteria` | Perl | Wrapper for `criteria.pm` — enforces coverage criteria (e.g., UNC + LBC + UIC == 0) |
| `criteria.pm` | Perl | Coverage criteria enforcement module; checks JSON summary data and returns non-zero exit on violation |
| `select.pm` | Perl | Subset selection callback — filters coverage data to show only specific changes/commits |
| `simplify.pm` | Perl | C++ symbol simplification — shortens long template/function names in the function detail table |
| `context.pm` | Perl | Environment/context tracking callback for debugging complex use cases |
| `history.pm` | Perl | Load-balancing history callback — uses prior execution data to improve parallel scheduling |
| `threshold.pm` | Perl | Threshold checking utility |
| `unreach.pm` | Perl | Marks branch expressions/MC/DC conditions as unreachable to exclude from coverage DB |
| `annotateutil.pm` | Perl | Shared utilities used by `gitblame.pm` and `p4annotate.pm` for caching and repo checks |
| `spreadsheet.py` | Python | Generates Excel spreadsheet reports from JSON profile data using xlsxwriter |
| `analyzeInfoFiles` | Shell? | Utility to analyze `.info` file contents |
| `get_signature` | Script | File signature extraction callback |

## `tests/` — Regression Test Suite

```
tests/
├── Makefile              # Test driver — includes common.mak, runs all test categories
├── common.mak            # Shared Makefile variables and rules for all test categories
├── common.tst            # Shared test infrastructure (bash test framework)
├── lcovrc                # Test-specific lcovrc configuration
├── README.md             # Test suite documentation
├── genhtml/              # Tests for genhtml (HTML report generation, demangling, differential)
│   ├── Makefile, full.sh, part2.sh, zero.sh, target.sh, demangle.sh
│   └── lambda/           # Lambda/C++11 coverage tests
├── lcov/                 # Tests for lcov (capture, aggregation, extraction, filtering)
├── gendiffcov/           # Tests for differential coverage functionality
├── llvm2lcov/            # Tests for LLVM coverage translation
│   ├── Makefile, llvm2lcov.sh, main.cpp, test.h
├── py2lcov/              # Tests for Python coverage translation
│   ├── Makefile, py2lcov.sh, test.py, localmodule.py
├── perl2lcov/            # Tests for Perl coverage translation
├── xml2lcov/             # Tests for XML/Cobertura coverage translation
├── profiles/             # Performance profiling test data
└── bin/                  # Test helper binaries
```

Tests are driven by `make check LCOV_HOME=/path/to/lcov`. Self-coverage measurement is supported via `COVERAGE=1` which runs the test suite under Devel::Cover and generates an HTML coverage report of LCOV's own code.

## `example/` — Demonstration

```
example/
├── Makefile              # Builds example and runs coverage demo (including differential coverage)
├── README                # Example documentation
├── example.c             # Main example program
├── example_mod.c         # Additional module
├── gauss.h               # Gauss algorithm header
├── iterate.h             # Iteration algorithm header
├── methods/              # Alternative algorithm implementations
│   └── *.c               # (iterative.c, gauss.c, etc.)
└── descriptions.txt      # Test case descriptions
```

## `man/` — Man Pages

| File | Content |
|------|---------|
| `lcov.1` | Main lcov tool — capture, combine, extract, remove, list, summary, kernel coverage |
| `genhtml.1` | HTML report generator — full option reference including differential, binning, navigation |
| `geninfo.1` | Tracefile generator — gcov invocation, intermediate format, filters, compatibility modes |
| `genpng.1` | PNG overview image generator |
| `gendesc.1` | Test description file generator |
| `lcovrc.5` | Configuration file format reference — all lcovrc options documented |

## Code Organization Patterns

- **Shared-library architecture**: All Perl tools share a single `lcovutil.pm` module that provides every common facility. New tools (e.g., `llvm2lcov`) follow the same pattern: `use lib "$FindBin::RealBin/../lib"; use lcovutil;` and inherit error handling, configuration, parallelism, and filtering for free.
- **Callback pattern**: Integration with external systems (VCS, criteria, versioning) uses a callback mechanism where users supply scripts/modules implementing a standard interface. Callbacks can be standalone executables or Perl modules (preferred for performance).
- **Pipeline design**: Coverage flow is `raw data → geninfo/lcov (capture) → .info file → lcov (manipulate) → genhtml (report)`. Translators (`perl2lcov`, `py2lcov`, `xml2lcov`, `llvm2lcov`) feed into the same pipeline via the `.info` format.
- **Filter architecture**: Coverage filters are defined with flag variables in `lcovutil.pm`, mapped via a `%COVERAGE_FILTERS` hash from string names to references, and applied uniformly across all tools through `parse_cov_filters`/`summarize_cov_filters`.
- **Parallel execution**: The `lcovutil.pm` module implements a fork/join framework with memory-aware throttling (`--memory`, `--parallel`, `max_tasks_per_core`, `memory_percentage`) and load-balancing history callbacks.
- **RC file layering**: Configuration is loaded from system `/etc/lcovrc`, user `~/.lcovrc`, and command-line `--rc key=value` overrides, with `parseOptions` merging them in priority order.
