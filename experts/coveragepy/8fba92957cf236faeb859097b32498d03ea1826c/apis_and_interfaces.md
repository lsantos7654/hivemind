# Coverage.py — APIs and Interfaces

## Public API (Top-Level Package)

The `coverage` package exports these symbols (from `coverage/__init__.py`):

```python
from coverage import Coverage, CoverageData, CoverageException
from coverage import CoveragePlugin, FileReporter, FileTracer, CodeRegion
from coverage import process_startup, coverage  # coverage is a backward-compat alias
```

### `coverage.Coverage` — The Main Class

The primary programmatic interface. Full lifecycle:

```python
import coverage

# Construction with all available options (most default from config file)
cov = coverage.Coverage(
    data_file=".coverage",          # Base data file name, None = no disk file
    data_suffix=True,               # Append .machine.pid.random for parallel runs
    cover_pylib=False,              # Measure Python stdlib?
    auto_data=False,                # Auto-load existing data, auto-save on stop
    timid=False,                    # Use slower PyTracer instead of CTracer
    branch=True,                    # Measure branch coverage in addition to lines
    config_file=True,               # Config file path, True=auto-search, False=no config
    source=["my_package"],          # Only measure code in these paths/packages
    source_pkgs=["my_pkg"],         # Like source but always interpreted as packages
    source_dirs=["my_project/"],    # Like source but raises if path missing, never package
    omit=["*/tests/*"],             # File patterns to exclude from measurement
    include=["*/src/*"],            # File patterns to include in measurement
    debug=["trace", "config"],      # Enable debug output categories
    concurrency="multiprocessing",  # Concurrency: thread, greenlet, eventlet, gevent, multiprocessing
    check_preimported=True,         # Warn about modules imported before coverage start
    context="my_label",             # Static context label for this run
    messages=True,                  # Print status messages to stdout
    plugins=[my_plugin_func],       # Override config-file plugins with callables
)

# Lifecycle
cov.start()                         # Begin measurement
# ... run your code ...
cov.stop()                          # Stop measurement

# Context manager (since 7.3):
with cov.collect():
    # ... run your code ...

# Data management
cov.save()                          # Write data to disk
cov.load()                          # Load previously collected data
cov.erase()                         # Delete all collected data (memory + disk)
cov.combine(data_paths=["dir1/"])   # Combine parallel data files
cov.get_data()                      # Returns CoverageData object

# Reporting
cov.report(morfs=None, show_missing=True, ignore_errors=False,
           file=sys.stdout, output_format="text")  # Returns float (total covered %)
cov.html_report(directory="htmlcov", skip_covered=False, title="My Report")
cov.xml_report(outfile="coverage.xml")
cov.json_report(outfile="coverage.json", pretty_print=True)
cov.lcov_report(outfile="coverage.lcov")
cov.annotate(directory="annotated")

# Analysis
cov.analysis2(morf)                 # Returns (filename, statements, excluded, missing, formatted)
cov.branch_stats(morf)              # Returns dict[TLineNo, tuple[total_exits, taken_exits]]

# Configuration
cov.get_option("run:branch")        # Read config option
cov.set_option("run:branch", True)  # Set config option

# Other
cov.switch_context("new_context")   # Switch dynamic context during measurement
cov.exclude(r"pragma: no cover")    # Add regex to exclusion list
cov.clear_exclude()                 # Clear exclusion list
cov.sys_info()                      # Return list of (key, value) system info pairs
Coverage.current()                  # Class method: get latest started Coverage instance
```

### `coverage.CoverageData`

The data storage class. Key methods:

```python
data = CoverageData(basename=".coverage", suffix=True, warn=my_warn, debug=debug_ctl)
data.read()                         # Read data from disk
data.write()                        # Write data to disk
data.erase()                        # Erase all data

# Query methods
data.measured_files()               # List of measured file paths
data.lines(filename)                # Set of executed line numbers for a file
data.arcs(filename)                 # Set of (from, to) arc tuples for a file (if branches)
data.has_arcs()                     # Whether branch/arc data is present
data.file_tracer(filename)          # Which plugin handled a file
data.run_infos()                    # List of run metadata dicts
data.contexts_by_lineno(filename)   # Map line numbers to list of context strings
```

### `coverage.process_startup`

Called from `.pth` files to auto-start coverage in subprocesses. Reads `COVERAGE_PROCESS_START` environment variable.

## Plugin System

### `coverage.CoveragePlugin` (Base Class)

Subclass to implement plugins. Must be registered via a `coverage_init(reg, options)` function in the plugin module.

```python
class MyPlugin(coverage.CoveragePlugin):
    # File tracer plugin:
    def file_tracer(self, filename: str) -> FileTracer | None: ...
    def file_reporter(self, filename: str) -> FileReporter | None: ...

    # Configurer plugin:
    def configure(self, config: TConfigurable) -> None: ...

    # Dynamic context switcher plugin:
    def dynamic_context(self, frame: FrameType) -> str | None: ...

    # Optional debugging info:
    def sys_info(self) -> Iterable[tuple[str, Any]]: ...

# Registration in plugin module:
def coverage_init(reg, options):
    reg.add_file_tracer(MyPlugin())
    # or: reg.add_configurer(MyPlugin())
    # or: reg.add_dynamic_context(MyPlugin())
```

### `coverage.FileTracer`

Returned by `CoveragePlugin.file_tracer()`. Must implement:
- `source_filename()` — returns path to the source file
- `line_number_range(frame)` — returns (first_line, last_line) for a frame
- `has_dynamic_source_filename()` (optional) — if filename can change per-frame

### `coverage.FileReporter`

Returned by `CoveragePlugin.file_reporter()`. Must implement:
- `lines()` — set of executable line numbers
- `excluded_lines()` — set of excluded line numbers
- `translate_lines(lines)` — map plugin line numbers to source line numbers
- `arcs()` — set of possible branch arcs (if branches)
- `exit_counts()` — dict of line→exit_count for branch tracking
- `no_branch_lines()` — set of lines that shouldn't have branches counted
- `source_token_lines()` — tokenized source lines for display
- `source()` — source code string
- `should_be_python()` — should this file be parsed with PythonParser?

### `coverage.CodeRegion`

Dataclass for reporting code regions (functions, classes, etc.):

```python
@dataclass
class CodeRegion:
    kind: str           # "function", "class", "method", etc.
    name: str           # The name of the region
    start: int          # Starting line number
    end: int            # Ending line number
    namespace: str      # The containing module/class namespace
```

## Configuration

### File-Based Configuration

Configuration is read from (in order) using `CoverageConfig` class:
- `.coveragerc` — INI-style, sections: `[run]`, `[report]`, `[html]`, `[xml]`, `[json]`, `[lcov]`, `[paths]`
- `setup.cfg` — same INI syntax, under `[coverage:run]`, etc.
- `tox.ini` — same as setup.cfg
- `pyproject.toml` — TOML format under `[tool.coverage.run]`, etc.

### `[run]` Section

Key options: `branch`, `source`, `source_pkgs`, `source_dirs`, `include`, `omit`, `parallel`, `concurrency` (thread/gevent/greenlet/eventlet/multiprocessing), `timid`, `debug`, `data_file`, `dynamic_context`, `context`, `disable_warnings`, `plugins`, `sigterm`, `relative_files`, `command_line`, `include_namespace_packages`

### `[report]` Section

Key options: `exclude_lines` (multi-line regex list), `partial_branches`, `include`, `omit`, `sort`, `ignore_errors`, `show_missing`, `skip_covered`, `skip_empty`, `precision`, `contexts`, `format` (text/markdown/total), `fail_under`

### `[html]` Section

Key options: `directory`, `title`, `skip_covered`, `skip_empty`, `show_contexts`, `extra_css`

### `[xml]` / `[json]` / `[lcov]` Sections

All accept `output` for file path. JSON also supports `pretty_print` and `show_contexts`.

### `[paths]` Section

Path remapping for combining data from different machines:
```ini
[paths]
source =
    src/
    /opt/jenkins/build/src/
```

### Environment Variables

- `COVERAGE_PROCESS_START` — .rcfile path for auto-starting subprocess coverage
- `COVERAGE_CORE` — force tracer: `sysmon`, `ctrace`, `pytrace`
- `COVERAGE_DEBUG` — enable debug output categories
- `COVERAGE_DEBUG_FILE` — file path for debug output
- `COVERAGE_RCFILE` — override config file (set internally by multiprocessing)
- `COVERAGE_DISABLE_EXTENSION` — disable C extension build

### Excluding Code from Coverage

Lines can be excluded via regex patterns in `[report] exclude_lines`. Common patterns:
```ini
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

## Command-Line Interface

```
coverage run [--branch] [--source=SRC] [--concurrency=LIB] [--context=LABEL]
             [--parallel] [--data-file=FILE] script.py [args...]

coverage run -m module_name [args...]

coverage combine [--keep] [--data-file=FILE] [data_dir...]

coverage report [-m] [--include=PAT] [--omit=PAT] [--skip-covered]
                [--skip-empty] [--contexts=REGEX1,REGEX2]
                [--precision=N] [--sort=SORT] [--fail-under=N]
                [--format=text|markdown|total]

coverage html [-d DIR] [--title=TITLE] [--skip-covered] [--skip-empty]
              [--show-contexts]

coverage xml [-o OUT.xml] [--skip-empty]

coverage json [-o OUT.json] [--pretty-print] [--show-contexts]

coverage lcov [-o OUT.lcov]

coverage annotate [-d DIR] [--ignore-errors]

coverage erase

coverage debug sys|data|config|pathmap|pybehave

coverage json --pretty-print -o -   # output to stdout
```

## Integration Patterns

### With pytest (via pytest-cov)

`pytest-cov` wraps `coverage.Coverage` — it calls `cov.start()` in a pytest sessionstart hook and `cov.stop()` + `cov.html_report()` in sessionfinish.

### With multiprocessing

Set `concurrency=multiprocessing` in config or pass to Coverage constructor. Coverage monkey-patches `multiprocessing.Process._bootstrap` to auto-start coverage in child processes, and injects a `Stowaway` pickleable object to propagate the patch through spawn-based multiprocessing.

### Subprocess Coverage

Set `COVERAGE_PROCESS_START=/path/to/.coveragerc` to auto-measure any Python subprocess. The `a1_coverage.pth` file (installed alongside coverage) executes `process_startup()` which reads this env var and creates a Coverage instance with `data_suffix=True, auto_data=True`.

### Dynamic Contexts

Set `[run] dynamic_context = test_function` to automatically group coverage by test function. During collection, when a frame's function name starts with `test` or equals `runTest`, a new context is created. Use `coverage report --contexts=test_feature` or `coverage html --show-contexts` to filter/display by context. Programmatic control via `cov.switch_context("name")`.

### Script-based Configuration (Plugins)

```python
# my_cov_config.py
def coverage_init(reg, options):
    class MyConfigurer(coverage.CoveragePlugin):
        def configure(self, config):
            config["run:branch"] = True
            config["html:title"] = "My Project"
    reg.add_configurer(MyConfigurer())

# In .coveragerc:
# [run]
# plugins = my_cov_config
```