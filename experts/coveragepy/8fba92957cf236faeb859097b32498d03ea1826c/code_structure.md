# Coverage.py — Code Structure

## Annotated Directory Tree

```
coveragepy/
├── __main__.py                  # Root-level entry: runs coverage.cmdline. if __name__ == '__main__'
├── setup.py                     # setuptools build: C extension (coverage/tracer), .pth file, entry points
├── pyproject.toml               # build-system (setuptools), mypy, pylint, pytest, ruff, scriv config
├── tox.ini                      # Multi-Python test envs (3.10-3.15, pypy3), lint, mypy, doc, gh matrix
├── Makefile                     # Dev targets: venv, install, test, lint, mypy, kit, upgrade, css, cogdoc
├── igor.py                      # Build/test helper: zip_mods, clean_for_core, test_with_core, release mgmt
├── metacov.ini                  # Meta-coverage config (measuring coverage.py with itself)
├── howto.txt                    # Release process instructions
├── MANIFEST.in                  # sdist manifest
├── requirements/                # pip-compile managed dependencies (*.in → *.pip with hashes)
│   ├── dev.in / dev.pip         # Dev tools: pylint, ruff, pre-commit, cogapp, check-manifest, etc.
│   ├── pip.in / pip.pip         # Core pip deps for test envs
│   ├── pytest.in / pytest.pip   # Pytest + Hypothesis + xdist + flaky
│   ├── mypy.in / mypy.pip       # Mypy type checker
│   ├── kit.in / kit.pip         # Build/packaging: build, cibuildwheel
│   ├── tox.in / tox.pip         # tox and tox-gh
│   ├── light-threads.in/.pip    # Greenlet, eventlet, gevent concurrency libs
│   └── pins.pip                 # Manual pins for packages with issues
│
├── coverage/                    # Main package
│   ├── __init__.py              # Public API exports: Coverage, CoverageData, CoveragePlugin, etc.
│   ├── __main__.py              # `python -m coverage` entry point
│   ├── version.py               # Version tuple + __url__, exec'd by setup.py to avoid imports
│   ├── control.py               # Coverage class: start/stop/collect, report generators, state machine
│   ├── core.py                  # Core: selects tracer (ctrace/pytrace/sysmon) based on env + config
│   ├── config.py                # CoverageConfig: reads .coveragerc, setup.cfg, tox.ini, pyproject.toml
│   ├── collector.py             # Collector: manages per-thread Tracer instances, concurrency orchestration
│   ├── data.py                  # CoverageData re-export from sqldata, combine logic, line_counts
│   ├── sqldata.py               # CoverageData implementation: SQLite-backed, schema v7, ARC/file storage
│   ├── sqlitedb.py              # SqliteDb: thread-safe SQLite connection wrapper with pragmas
│   ├── numbits.py               # nums_to_numbits / numbits_to_nums: packed binary line number encoding
│   ├── parser.py                # PythonParser: AST + bytecode static analysis, statement/arc/exclude finding
│   ├── python.py                # PythonFileReporter: source reading (.py/.pyw/zip), line/arc/exit_counts
│   ├── bytecode.py              # ByteParser: disassembles .pyc bytecode, branch trail analysis
│   ├── phystokens.py            # generate_tokens: physical source tokenization (tokenize wrapper)
│   ├── results.py               # Analysis dataclass and Numbers: coverage statistics computation
│   ├── report.py                # SummaryReporter: text/markdown/total format console reports
│   ├── report_core.py           # render_report(), get_analysis_to_report(): shared reporter infrastructure
│   ├── html.py                  # HtmlReporter: multi-file HTML report with index, per-file source pages
│   ├── xmlreport.py             # XmlReporter: Cobertura-compatible XML output
│   ├── jsonreport.py            # JsonReporter: JSON output (format v3, with region data)
│   ├── lcovreport.py            # LcovReporter: LCOV tracefile format for gcov-compatible tools
│   ├── annotate.py              # AnnotateReporter: annotated .py,cover source files
│   ├── cmdline.py               # CLI: optparse-based command-line interface, all subcommands
│   ├── execfile.py              # PyRunner: run Python files/modules with coverage, find_module helpers
│   ├── plugin.py                # CoveragePlugin, FileTracer, FileReporter, CodeRegion base classes
│   ├── plugin_support.py        # Plugins: load/register plugin modules, manage file_tracers/configurers
│   ├── multiproc.py             # patch_multiprocessing(): monkey-patches multiprocessing.Process._bootstrap
│   ├── pth_file.py              # .pth file source: auto-starts coverage in subprocesses via sitecustomize
│   ├── inorout.py               # InOrOut: decides which files to trace/report based on source/include/omit
│   ├── disposition.py           # FileDisposition: dataclass recording per-file trace decisions
│   ├── files.py                 # File utilities: PathAliases, GlobMatcher, canonical_filename, etc.
│   ├── context.py               # Dynamic context detection: should_start_context_test_function, qualname
│   ├── misc.py                  # Utilities: Hasher, human_sorted, join_regex, isolate_module, etc.
│   ├── env.py                   # Environment detection: platform, PYBEHAVIOR capabilities dict
│   ├── debug.py                 # DebugControl: timed debug output, short_stack, info formatting
│   ├── exceptions.py            # CoverageException hierarchy, CoverageWarning
│   ├── regions.py               # code_regions(): AST walk to find function/class/statement regions
│   ├── patch.py                 # apply_patches(): optional monkey-patching for stdlib compatibility
│   ├── types.py                 # Protocol types: Tracer, TConfigurable, TFileDisposition, TLineNo, TArc
│   ├── tomlconfig.py            # TomlConfigParser: reads [tool.coverage] from pyproject.toml
│   ├── templite.py              # Templite: lightweight template engine for HTML report generation
│   ├── sysmon.py                # SysMonitor: sys.monitoring-based tracer for Python 3.12+
│   ├── pytracer.py              # PyTracer: pure-Python sys.settrace-based tracer
│   │
│   ├── ctracer/                 # C extension tracer source
│   │   ├── module.c             # Python module init, CTracer + CFileDisposition types
│   │   ├── tracer.c / tracer.h  # CTracer: C-level sys.settrace trace function, arc collection
│   │   ├── filedisp.c / filedisp.h # CFileDisposition: C struct mirroring FileDisposition
│   │   ├── datastack.c / datastack.h # DataStack: thread-safe stack allocator for trace data
│   │   ├── stats.h              # Per-tracer statistics struct
│   │   └── util.h               # Shared utility macros
│   │
│   └── htmlfiles/               # Static assets for HTML reports
│       ├── style.scss / style.css # SCSS-compiled CSS stylesheet
│       ├── index.html           # Templite template for index page
│       ├── pyfile.html          # Templite template for per-file source page
│       ├── coverage_html.js     # Client-side JS: filtering, sorting, keyboard nav
│       ├── jquery*.js           # Bundled jQuery for HTML report interactivity
│       ├── keybd_*.png          # Keyboard shortcut icons
│       └── favicon_32.png       # Favicon
│
├── tests/                       # Comprehensive test suite (~70+ test files)
│   ├── conftest.py              # Pytest fixtures, markers, test configuration
│   ├── coveragetest.py          # CoverageTest base class with assertion helpers
│   ├── helpers.py               # Test utility functions
│   ├── goldtest.py              # Gold-file comparison testing (compare actual vs expected dirs)
│   ├── test_*.py                # Per-module tests: test_coverage, test_config, test_parser, etc.
│   ├── gold/                    # Gold-file expected outputs for regression testing
│   │   ├── html/                # Expected HTML report output for various configurations
│   │   ├── testing/             # Expected testing utility output
│   │   └── xml/                 # Expected XML/Cobertura report output
│   ├── modules/                 # Test fixture Python modules/packages
│   ├── mixins.py                # Mixin classes for test composition
│   └── strategies.py            # Hypothesis property-based testing strategies
│
├── doc/                         # Sphinx documentation source
│   ├── conf.py                  # Sphinx configuration
│   ├── *.rst                    # ReStructuredText documentation pages
│   └── cog_helpers.py           # Cog code-generation helpers for docs
│
├── ci/                          # CI helper scripts
│   ├── session.py               # GitHub Actions session management
│   ├── trigger_action.py        # Trigger GitHub Actions workflows via API
│   ├── update_rtfd.py           # Update Read the Docs version visibility
│   └── comment_on_fixes.py      # Auto-comment on fixed GitHub issues
│
├── lab/                         # Experimental/research scripts (not shipped)
│   ├── parser.py                # Visualize parser output
│   ├── branches.py              # Experiment with branch detection
│   ├── run_trace.py             # Low-level trace function experiments
│   └── notes/                   # Research notes (arcs-to-branches, pypy issues, etc.)
│
└── .github/                     # GitHub CI/CD
    ├── workflows/
    │   ├── testsuite.yml        # Main test matrix (OS × Python version × core)
    │   ├── quality.yml          # Lint, mypy, docs, code quality checks
    │   ├── coverage.yml         # Metacov: measure coverage.py with itself
    │   ├── kit.yml              # cibuildwheel: build wheels for all platforms
    │   ├── publish.yml          # PyPI publish workflow
    │   ├── python-nightly.yml   # Test against nightly CPython
    │   ├── codeql-analysis.yml  # GitHub CodeQL security analysis
    │   └── dependency-review.yml # Dependency vulnerability review
    ├── dependabot.yml           # Automated dependency PRs
    └── zizmor.yml               # Static analysis for CI workflows
```

## Module Organization Patterns

The `coverage/` package follows a layered architecture:

1. **Configuration Layer** (`config.py`, `tomlconfig.py`): `CoverageConfig` reads settings from `.coveragerc`, `setup.cfg`, `tox.ini`, `pyproject.toml`, and environment variables. `HandyConfigParser` extends `configparser.ConfigParser` with `coverage:` section prefix support.

2. **Core/Tracer Layer** (`core.py`, `ctracer/`, `pytracer.py`, `sysmon.py`): The `Core` class selects the tracing backend at initialization. Three implementations exist:
   - `CTracer` (C): fast, `packed_arcs=True`, `supports_plugins=True`
   - `PyTracer` (Python): slow, `packed_arcs=False`, `supports_plugins=False`
   - `SysMonitor` (Python 3.12+): fastest, `packed_arcs=False`, `supports_plugins=False`

3. **Collection Layer** (`collector.py`): `Collector` creates per-thread Tracer instances. It manages a stack of active collectors, handles concurrency libraries (thread, greenlet, eventlet, gevent), and orchestrates `should_trace`, `check_include`, and `should_start_context` callbacks.

4. **Data Layer** (`sqldata.py`, `sqlitedb.py`, `numbits.py`): `CoverageData` stores coverage in a SQLite database with tables `coverage_schema`, `meta`, `file`, `context`, `line_bits` (per-file/per-context numbits blobs), and `arc` (per-context from→to arcs). Schema is at version 7. The `numbits` module provides a compact bit-packed encoding for sets of line numbers.

5. **Analysis Layer** (`parser.py`, `bytecode.py`, `python.py`, `phystokens.py`): `PythonParser` performs dual-pass static analysis: AST traversal identifies statement boundaries, while bytecode disassembly (`ByteParser`) finds executable line numbers and branch arcs. `PythonFileReporter` wraps this with source reading (from `.py`, `.pyw`, or zip files).

6. **Reporting Layer** (`report.py`, `html.py`, `xmlreport.py`, `jsonreport.py`, `lcovreport.py`, `annotate.py`, `report_core.py`): Each reporter follows a common pattern: `get_analysis_to_report()` yields `(FileReporter, Analysis)` pairs, then the reporter generates output. `render_report()` provides shared output file management for single-file reporters.

7. **Plugin Layer** (`plugin.py`, `plugin_support.py`): Three plugin types (file tracers, configurers, dynamic context switchers) registered via `coverage_init()` functions. `Plugins` class manages registration, loading from config or callables.

8. **Support/Utility Layer** (`files.py`, `misc.py`, `debug.py`, `env.py`, `exceptions.py`, `types.py`, `disposition.py`, `context.py`, `multiproc.py`, `pth_file.py`, `patch.py`, `regions.py`, `templite.py`, `inorout.py`): Cross-cutting utilities used throughout.