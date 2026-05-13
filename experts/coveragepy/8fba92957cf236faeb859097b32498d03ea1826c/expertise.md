### Core Architecture

- Three tracing cores selected by `Core` class (`coverage/core.py`): `CTracer` (C extension in `coverage/ctracer/`), `PyTracer` (pure Python in `coverage/pytracer.py`), `SysMonitor` (Python 3.12+ `sys.monitoring` in `coverage/sysmon.py`)
- `CTracer` (`coverage.tracer` C extension) offers fastest performance, `supports_plugins=True`, `packed_arcs=True`
- `PyTracer` is a pure-Python fallback using `sys.settrace`, `supports_plugins=False`, `packed_arcs=False`
- `SysMonitor` uses PEP 669 `sys.monitoring` callbacks, fastest option, no plugin support, only available on Python 3.12+
- Core selection logic: checks `PYBEHAVIOR.pep669`, `PYBEHAVIOR.branch_right_left`, dynamic context support, concurrency library compatibility, `COVERAGE_CORE` env var, `config.core`, `config.timid`, `env.SYSMON_DEFAULT`
- `collector.py` `Collector` class manages per-thread `Tracer` instances, maintains a stack of active collectors, handles pause/resume when nested `Coverage` objects are active
- `Collector` orchestrates concurrency libraries: thread, greenlet, eventlet, gevent, multiprocessing
- `multiproc.py` `patch_multiprocessing()` monkey-patches `multiprocessing.process.BaseProcess._bootstrap` with `ProcessWithCoverage`
- `multiproc.py` `Stowaway` class is a pickleable object that re-applies the monkey-patch in spawn-based subprocesses
- `pth_file.py` contains the code injected into `a1_coverage.pth` to auto-start coverage when `COVERAGE_PROCESS_START` is set
- `setup.py` `make_pth_file()` minifies `pth_file.py` into `a1_coverage.pth` during installation
- `EditableWheelWithPth` extends `editable_wheel` to inject the `.pth` file into editable install wheels

### Data Storage

- `CoverageData` class (implemented in `coverage/sqldata.py`, schema version 7) uses SQLite for persistent storage
- Database schema: `coverage_schema` (one version row), `meta` (key-value metadata: has_arcs, sys_argv, version, when, hash), `file` (id+path per measured file), `context` (id+context string), `line_bits` (file_id + context_id → numbits blob of executed lines), `arc` (file_id + context_id + fromno + tono for branch arcs)
- `numbits.py` provides `nums_to_numbits()` (pack integers to bit-packed bytes) and `numbits_to_nums()` (unpack back to integer list), plus `numbits_union()` for combining data
- `sqlitedb.py` `SqliteDb` class wraps `sqlite3` with thread safety, optimized pragmas (WAL mode, synchronous=OFF, mmap_size), and context managers
- `data.py` `combine_parallel_data()` merges multiple SQLite data files into one using path aliases
- `data.py` `add_data_to_hash()` contributes file coverage data to a `Hasher` for data integrity verification
- `data.py` `combinable_files()` discovers data files matching a base name pattern for combination
- `CoverageData.read()` reads from disk, `write()` writes to disk, `erase()` deletes, `close()` with `force=True` deletes empty files
- Line data stored as `numbits` blobs per (file_id, context_id) pair; arc data stored as individual (file_id, context_id, fromno, tono) rows

### Public API

- `coverage.Coverage` is the main programmatic class (`coverage/control.py`), supporting `start()`, `stop()`, `collect()` context manager (7.3+), `save()`, `load()`, `erase()`, `combine()`, `get_data()`
- `Coverage.__init__()` parameters: `data_file`, `data_suffix`, `cover_pylib`, `auto_data`, `timid`, `branch`, `config_file`, `source`, `source_pkgs`, `source_dirs`, `omit`, `include`, `debug`, `concurrency`, `check_preimported`, `context`, `messages`, `plugins`
- `Coverage.report()` generates text/markdown/total summaries; parameters: `morfs`, `show_missing`, `ignore_errors`, `file`, `omit`, `include`, `skip_covered`, `contexts`, `skip_empty`, `precision`, `sort`, `output_format`
- `Coverage.html_report()` generates multi-file HTML report via `HtmlReporter`; parameters: `directory`, `extra_css`, `title`, `show_contexts`
- `Coverage.xml_report()` generates Cobertura-compatible XML via `XmlReporter`; parameter: `outfile` (use "-" for stdout)
- `Coverage.json_report()` generates JSON (format v3, with region data) via `JsonReporter`; parameters: `pretty_print`, `show_contexts`
- `Coverage.lcov_report()` generates LCOV tracefiles via `LcovReporter`
- `Coverage.annotate()` generates `.py,cover` annotated source files via `AnnotateReporter`
- `Coverage.analysis2(morf)` returns 5-tuple: (filename, executable statements, excluded lines, missing lines, formatted missing)
- `Coverage.branch_stats(morf)` returns `dict[int, tuple[int, int]]` mapping line numbers to (total_exits, taken_exits)
- `Coverage.get_option()` / `set_option()` use colon-separated section:option names (e.g., `"run:branch"`)
- `Coverage.switch_context(name)` dynamically changes the context label during measurement
- `Coverage.exclude(regex, which="exclude"|"partial")` and `clear_exclude(which)` manage exclusion regexes
- `Coverage.sys_info()` returns diagnostic `(key, value)` pairs about the coverage installation
- `Coverage.current()` class method returns the most recently started `Coverage` instance
- `coverage.process_startup()` reads `COVERAGE_PROCESS_START` env var to auto-start measurement in subprocesses
- `coverage.CoverageException` is the base exception; `coverage.exceptions` also defines `CoverageWarning`, `ConfigError`, `DataError`, `NoDataError`, `NoSource`, `NotPython`, `PluginError`
- Backward-compatibility alias: `coverage.coverage = Coverage`

### Configuration System

- `CoverageConfig` class (`coverage/config.py`, ~730 lines) handles all configuration parsing
- `read_coverage_config()` discovers and reads `.coveragerc`, `setup.cfg`, `tox.ini`, `pyproject.toml`
- `HandyConfigParser` extends `configparser.ConfigParser` with `coverage:` section prefix detection
- `TomlConfigParser` (`coverage/tomlconfig.py`) reads `[tool.coverage.*]` sections from `pyproject.toml`
- Configuration sections: `[run]`, `[report]`, `[html]`, `[xml]`, `[json]`, `[lcov]`, `[paths]`
- `[run]` options: `branch`, `source`, `source_pkgs`, `source_dirs`, `include`, `omit`, `parallel`, `concurrency`, `timid`, `debug`, `data_file`, `dynamic_context`, `context`, `disable_warnings`, `plugins`, `sigterm`, `relative_files`, `command_line`, `include_namespace_packages`, `core`
- `[report]` options: `exclude_lines`, `partial_branches`, `include`, `omit`, `sort`, `ignore_errors`, `show_missing`, `skip_covered`, `skip_empty`, `precision`, `contexts`, `format`, `fail_under`
- `[html]` options: `directory`, `title`, `skip_covered`, `skip_empty`, `show_contexts`, `extra_css`
- `[xml]`, `[json]`, `[lcov]` sections each support `output`; JSON adds `pretty_print` and `show_contexts`
- `[paths]` maps source paths for cross-machine data combination (e.g., CI worker paths → local paths)
- `override_config()` context manager in `control.py` temporarily modifies a Coverage instance's configuration
- Environment variables: `COVERAGE_PROCESS_START`, `COVERAGE_CORE`, `COVERAGE_DEBUG`, `COVERAGE_DEBUG_FILE`, `COVERAGE_RCFILE`, `COVERAGE_DISABLE_EXTENSION`, `COVERAGE_NO_AUTO_INIT`
- Config file selection: `True` tries `.coveragerc`, `setup.cfg`, `tox.ini`; string is explicit path; `False` disables config

### Static Analysis

- `PythonParser` (`coverage/parser.py`, ~1150 lines) performs dual-pass analysis: AST walk + bytecode inspection
- `PythonParser.parse_source()` is the main entry: tokenizes, builds AST, visits statements, cross-references with bytecode
- `PythonParser.statements` returns set of executable line numbers (normalized to first lines, exclusions removed)
- `PythonParser.arcs()` returns set of `(from_line, to_line)` branch arc possibilities
- `PythonParser.arc_misses()` identifies which arcs are missing given a set of executed arcs
- `PythonParser.exit_counts()` returns `dict[int, int]` — per-line count of possible branch exits
- `ByteParser` (`coverage/bytecode.py`) disassembles bytecode to find line number tables, basic block transitions, branch/jump targets
- `branch_trails()` computes all possible code paths through bytecode for branch coverage analysis
- `always_jumps()` identifies unconditional jumps in bytecode
- `source_token_lines()` in `phystokens.py` tokenizes source using `tokenize.generate_tokens()`
- `source_encoding()` detects source file encoding from PEP 263 encoding declarations
- `PythonFileReporter` (`coverage/python.py`) implements `FileReporter` for Python files, wraps `PythonParser`
- `PythonFileReporter` reads source from `.py`, `.pyw`, or zip files (via `zipimport`)
- `get_python_source()` handles alternate file extensions (`.pyw` on Windows) and zip imports
- `code_regions()` (`coverage/regions.py`) walks the AST to find function/class/method boundaries for JSON report region data
- `NoSource` exception raised when source file can't be found; `NotPython` raised when a file isn't valid Python

### Reporting

- `SummaryReporter` (`coverage/report.py`) generates terminal text reports with `--show-missing` detail
- `HtmlReporter` (`coverage/html.py`, ~860 lines) generates multi-page HTML reports with CSS, JS, and context filtering
- `HtmlReporter` uses `Templite` (`coverage/templite.py`) template engine to render `htmlfiles/index.html` and `htmlfiles/pyfile.html`
- `coverage_html.js` provides client-side filtering, sorting, keyboard navigation, and context toggle
- `HtmlReporter` computes per-file hashes via `add_data_to_hash()` for cache-busting file URLs
- `XmlReporter` (`coverage/xmlreport.py`) produces Cobertura-compatible XML with `PackageData` grouping
- `JsonReporter` (`coverage/jsonreport.py`) outputs JSON format v3 with `meta`, `files`, `totals` sections
- `LcovReporter` (`coverage/lcovreport.py`) outputs LCOV tracefile format with TN, SF, DA, BRDA, LF, LH records
- `AnnotateReporter` (`coverage/annotate.py`) writes annotated source copies with `>`, `!`, `-` margin markers
- `render_report()` (`coverage/report_core.py`) manages output file creation/cleanup for single-file reporters
- `get_analysis_to_report()` yields filtered `(FileReporter, Analysis)` pairs respecting include/omit patterns
- `Analysis` dataclass (`coverage/results.py`) holds all computed coverage stats for a single file
- `Numbers` class (`coverage/results.py`) accumulates and formats coverage percentage statistics
- `analysis_from_file_reporter()` bridges `CoverageData` + `FileReporter` → `Analysis`
- `should_fail_under()` compares total coverage against `fail_under` threshold
- `AnalysisNarrower` (`coverage/results.py`) filters analysis results to specific contexts

### Plugin System

- `CoveragePlugin` base class (`coverage/plugin.py`) with override points: `file_tracer()`, `file_reporter()`, `configure()`, `dynamic_context()`, `sys_info()`
- `FileTracer` abstract class: `source_filename()`, `line_number_range()`, `has_dynamic_source_filename()`
- `FileReporter` abstract class: `lines()`, `excluded_lines()`, `translate_lines()`, `arcs()`, `exit_counts()`, `no_branch_lines()`, `source()`, `source_token_lines()`, `should_be_python()`
- `CodeRegion` dataclass: `kind`, `name`, `start`, `end`, `namespace` fields for region reporting
- Plugin registration via `coverage_init(reg, options)` function in the plugin module
- `Plugins` class (`coverage/plugin_support.py`) manages the plugin registry: `add_file_tracer()`, `add_configurer()`, `add_dynamic_context()`
- `Plugins.load_from_config()` imports plugin modules and calls their `coverage_init()`
- `Plugins.load_from_callables()` registers plugins from function objects (used when `plugins=` kwarg passed to `Coverage()`)
- Three plugin types: file tracers (non-Python files), configurers (programmatic config), dynamic context switchers
- Plugin discovery chain: list plugin names in `[run] plugins` config option; each module must define `coverage_init()`

### Concurrency Support

- `concurrency` parameter accepts: `"thread"`, `"greenlet"`, `"eventlet"`, `"gevent"`, `"multiprocessing"` (any combination)
- Thread support is default and built into `Collector` via per-thread `Tracer` instances
- Greenlet/eventlet/gevent support via `Collector` greenlet-switch-aware tracer data tracking
- Multiprocessing support via `patch_multiprocessing()` which replaces `multiprocessing.process.BaseProcess._bootstrap`
- `ProcessWithCoverage._bootstrap()` starts/stops/saves coverage in each child process
- `Stowaway` pickled into multiprocessing spawn data to re-apply monkey-patch in spawned processes
- `COVERAGE_RCFILE` environment variable set by `patch_multiprocessing()` to propagate config to children

### File Classification (InOrOut)

- `InOrOut` class (`coverage/inorout.py`, ~650 lines) decides which files to trace and report
- `InOrOut.should_trace(filename, frame)` returns a `FileDisposition` indicating whether to trace
- `InOrOut.check_include_omit_etc()` applies include/omit patterns to a filename
- Source matching: `source`, `source_pkgs`, `source_dirs` define which code trees to measure
- `ModuleMatcher` matches filenames to package names for `source`/`source_pkgs` configuration
- `TreeMatcher` matches filenames against directory trees for `source_dirs` configuration
- `GlobMatcher` applies glob patterns for `include`/`omit` configuration
- `warn_unimported_source()` warns about configured source packages that were never imported
- `warn_already_imported_files()` warns about files imported before coverage started
- `find_possibly_unexecuted_files()` discovers files in source trees that had zero coverage

### Dynamic Contexts

- `context.py` provides context detection for grouping coverage data by test/caller
- `should_start_context_test_function(frame)` detects frames calling test functions (name starts with "test" or equals "runTest")
- `qualname_from_frame(frame)` computes qualified name like `module.ClassName.method` from a frame
- `combine_context_switchers(switchers)` composes multiple context switcher functions into one
- Static contexts set via `Coverage(context="label")` or command-line `--context=LABEL`
- Dynamic contexts enabled via `[run] dynamic_context = test_function` or custom plugin context switchers
- Static and dynamic contexts combined with pipe separator (`static_context|dynamic_context`) when both active

### Command-Line Interface

- `coverage/cmdline.py` (~1200 lines) implements the full CLI using `optparse`
- Subcommands: `run`, `combine`, `report`, `html`, `xml`, `json`, `lcov`, `annotate`, `erase`, `debug`
- `coverage run` accepts: `--branch`, `--source`, `--omit`, `--include`, `--concurrency`, `--context`, `--parallel`, `--data-file`, `--append`, `-m` (module mode), `--timid`, `--debug`
- `coverage report` accepts: `-m` (show missing), `--include`, `--omit`, `--skip-covered`, `--skip-empty`, `--contexts`, `--precision`, `--sort`, `--fail-under`, `--format` (text/markdown/total)
- `coverage html` accepts: `-d`/`--directory`, `--title`, `--skip-covered`, `--skip-empty`, `--show-contexts`
- `coverage xml` / `json` / `lcov` accept: `-o` output path, `-` for stdout
- `coverage combine` accepts: `--keep`, `--data-file`, positional data directory paths
- `coverage debug` subcommands: `sys`, `data`, `config`, `pathmap`, `pybehave`
- `coverage json --pretty-print` and `--show-contexts` for detailed JSON output
- `PyRunner` class (`coverage/execfile.py`) executes Python files or modules (`-m`) under coverage
- `execfile.py` `find_module()` uses `importlib.util.find_spec()` for module resolution
- `_ExceptionDuringRun` wraps exceptions from user code to distinguish from coverage errors

### Utility Modules

- `coverage/files.py`: `PathAliases` (path remapping for combine), `GlobMatcher`, `ModuleMatcher`, `TreeMatcher`, `canonical_filename()`, `relative_filename()`, `abs_file()`, `flat_rootname()`, `find_python_files()`, `prep_patterns()`
- `coverage/misc.py`: `Hasher` (streaming hash with JSON-safe data), `human_sorted()`, `human_sorted_items()`, `join_regex()`, `isolate_module()` (save module globals from mocking), `substitute_variables()` (env var expansion), `ensure_dir()`/`ensure_dir_for_file()`, `file_be_gone()`, `plural()`, `nice_pair()`, `format_local_datetime()`
- `coverage/debug.py`: `DebugControl` with timed output, `short_stack()`, `short_filename()`, `info_header()`, `write_formatted_info()`, `relevant_environment_display()`
- `coverage/env.py`: platform detection (`WINDOWS`, `PYPY`, etc.), `PYBEHAVIOR` dict of version-dependent capabilities (pep669, branch_right_left, etc.), `SHIPPING_WHEELS`, `METACOV`, `SYSMON_DEFAULT`
- `coverage/exceptions.py`: `CoverageException` base, `CoverageWarning`, `ConfigError`, `DataError`, `NoDataError`, `NoSource` (with `slug`), `NotPython`, `PluginError`, `NoCode`, `_ExceptionDuringRun`
- `coverage/disposition.py`: `FileDisposition` dataclass (original_filename, canonical_filename, source_filename, trace, reason, file_tracer, has_dynamic_filename)
- `coverage/types.py`: Protocol types: `Tracer`, `TTraceFn`, `TFileDisposition`, `TConfigurable`, `TPluginConfig`, `TWarnFn`, `TDebugCtl`; type aliases: `TLineNo`, `TArc`, `TMorf`, `TMorfs`, `TTraceData`, `FilePath`

### Build and Test Infrastructure

- `setup.py` (272 lines): setuptools build with `ve_build_ext` (handles `BuildFailed` fallback), C extension compilation, `.pth` file generation, entry points
- C extension sources: `coverage/ctracer/module.c`, `tracer.c`, `filedisp.c`, `datastack.c` with headers `tracer.h`, `filedisp.h`, `datastack.h`, `util.h`, `stats.h`
- `tox.ini` test matrix: `py310-py315`, `py313t-py315t` (free-threading), `pypy3`, plus `doc`, `lint`, `mypy`
- Each tox environment runs tests with all three cores (ctrace, pytrace, sysmon on 3.12+) via `igor.py`
- `igor.py` is the build/test orchestration tool: `zip_mods`, `clean_for_core`, `test_with_core`, `combine_html`, `release_version`, `edit_for_release`, `bump_version`, `cheats`
- `pyproject.toml` pytest config: `-n auto --dist loadgroup -p no:legacypath --no-flaky-report -rfEX --failed-first`, strict mode
- `pyproject.toml` mypy config: strict checking with `disallow_untyped_defs`, `disallow_incomplete_defs`, etc.
- `pyproject.toml` ruff config: formatting only (linting disabled), `target-version = "py310"`, `line-length = 100`
- `Makefile`: targets for `venv`, `install`, `test`, `lint`, `mypy`, `precommit`, `kit`, `upgrade`, `upgrade_one`, `metacov`, `metahtml`, `css` (SCSS compilation), `cogdoc` (cog code generation), `dochtml`, `publish`, `tag`, `build_kits`, `pypi_upload`, `release_version`
- Meta-coverage (`metacov.ini`): coverage.py measures itself during its own test suite
- Test framework: pytest with `CoverageTest` base class (`tests/coveragetest.py`), gold-file comparison (`tests/goldtest.py`), Hypothesis property-based tests (`tests/strategies.py`)
- Test fixtures: `tests/modules/` (Python module packages for import testing), `tests/gold/` (expected output directories for html/xml/testing)
- `requirements/dev.in` → `requirements/dev.pip`: developer tools (pylint, ruff, pre-commit, cogapp, check-manifest, etc.)

### HTML Report Details

- `coverage/htmlfiles/`: static assets bundled with the package (`package_data` in `setup.py`)
- `index.html` / `pyfile.html`: Templite templates rendered by `HtmlReporter`
- `style.scss` compiled to `style.css` via `pysassc` (`make css`)
- `coverage_html.js`: client-side logic for filtering (search box), sorting (column headers), keyboard shortcuts (n/p/j/k navigation), context toggle
- `jquery.min.js`, `jquery.ba-throttle-debounce.min.js`, `jquery.hotkeys.js`, `jquery.isonscreen.js`: bundled jQuery plugins
- `keybd_closed.png`, `keybd_open.png`: keyboard shortcut indicator icons
- `status.json` written alongside HTML for programmatic consumption (contains version, timestamp, totals)
- `HtmlReporter._file_html()` generates per-file annotated source pages with line-by-line coloring
- `LineData` dataclass holds per-line render data: tokens, category (run/mis/exc/par), contexts, annotations
- File hashes in filenames (e.g., `d_12345abc.html`) for cache busting when source changes

### Key Implementation Details

- `Coverage._instances` class-level stack enables `Coverage.current()` and nested Coverage objects
- `Collector._collectors` class-level stack enables pausing/resuming tracers when nested collectors are active
- `isolate_module()` protects against aggressive mocking in test environments by saving original module references
- Data suffix mode: when `parallel=True` or `data_suffix=True`, data files get `.machine.pid.random` suffix
- `atexit.register(self._atexit)` ensures data is saved on normal process exit
- `signal.SIGTERM` handler (`_on_sigterm`) saves data on SIGTERM before re-raising
- `apply_patches()` in `patch.py` applies optional monkey-patches for stdlib compatibility
- `CoverageConfig` includes `_crash` test hook: setting `[run] _crash` to a function name raises RuntimeError when that function is in the call stack
- Exclusion regexes compiled via `join_regex()` (joins multiple patterns with `|` and compiles)
- `WAL` journal mode and `synchronous=OFF` pragmas on SQLite for performance during data collection
- `CoverageData.sys_info()` returns SQLite version and compile options for debugging
- `CTRACER_FILE` tracks whether C extension is available; `IMPORT_ERROR` string captures failure reason
- `PYBEHAVIOR` dict in `env.py` provides runtime capability detection for version-dependent features (PEP 669 availability, PyPy quirks, free-threading support)

### Documentation System

- Sphinx documentation in `doc/` with `conf.py`, built via `make dochtml`
- Cog code generation (`cogapp`) used in doc RST files and CI workflow YAML to keep version lists and config defaults in sync
- `doc/cog_helpers.py` provides Python helpers for cog directives
- `doc/conf.py` Sphinx configuration with intersphinx, autodoc, readthedocs theme
- Read the Docs hosting at `https://coverage.readthedocs.io/`
- `make docspell` runs Sphinx spelling checker with PyEnchant
- `make docdev` runs `sphinx-autobuild` for live-reload doc editing
- Doc quality checks: `doc8` (style), `sphinx-lint` (RST linting), `rediraffecheckdiff` (redirect validation)