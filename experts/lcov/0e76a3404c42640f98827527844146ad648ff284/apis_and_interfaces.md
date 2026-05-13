# LCOV APIs and Interfaces

LCOV is primarily a suite of command-line tools, not a library with a programmatic API. Its interfaces are: CLI arguments, the `.info` tracefile format, the `lcovrc` configuration file, in-source exclusion markers, and callback scripts.

---

## CLI Tools and Their Primary Operations

### `lcov` — Coverage Data Front-End

```
lcov --capture --directory <dir> --output-file <file>           # Capture coverage
lcov --zerocounters                                              # Reset gcov counters
lcov --add-tracefile <pattern> --output-file <file>             # Combine tracefiles
lcov --extract <file> <pattern> --output-file <file>            # Extract subset
lcov --remove <file> <pattern> --output-file <file>             # Remove subset
lcov --list <file>                                               # List contents
lcov --summary <file>                                            # Show summary statistics
lcov --intersect <glob> <glob> --output-file <file>             # Intersect files
lcov --subtract <glob> <glob> --output-file <file>              # Subtract files
lcov --prune-tests --add-tracefile <pattern> --output-file <file>  # Prune redundant tests
```

Key options shared across tools:
- `--rc <key>=<value>` — Override configuration parameter
- `--config-file <file>` — Specify alternative config file
- `--ignore-errors <types>` — Suppress specific error types (source, mismatch, empty, graph, etc.)
- `--keep-going` — Continue on error
- `--filter <type,...>` — Apply coverage filters (branch, brace, blank, region, function, etc.)
- `--exclude <pattern>` / `--include <pattern>` — Glob file inclusion/exclusion
- `--substitute <s/pat/repl/>` — Path substitution regex
- `--omit-lines <regexp>` — Exclude lines matching pattern
- `--erase-functions <regexp>` — Remove functions matching pattern
- `--demangle-cpp [tool]` — C++ name demangling (default: c++filt)
- `--branch-coverage` — Enable branch coverage collection
- `--mcdc-coverage` — Enable MC/DC coverage collection
- `--checksum` / `--no-checksum` — Line checksum computation
- `--parallel [N]` / `-j [N]` — Enable parallel processing (N cores)
- `--memory <Mb>` — Memory limit for parallel throttling
- `--version-script <script>` — Version extraction callback
- `--criteria-script <script>` — Coverage criteria callback
- `--resolve-script <script>` — File path resolution callback
- `--context-script <script>` — Environment/context tracking callback
- `--history-script <script>` — Load balancing history callback
- `--comment <string>` — Add comment to output

### `geninfo` — Tracefile Generator

Internal tool that reads gcov data (`.gcno`/`.gcda` files) and produces `.info` files. Key options:

```
geninfo <directory> --output-filename <file>          # Capture from directory
geninfo --initial <directory> --output-filename <file> # Capture initial/compile-time data only
geninfo --all <directory> --output-filename <file>     # Capture all including compile-time-only
geninfo --gcov-tool <tool>                             # Specify gcov executable
geninfo --compat <mode>=on|off|auto                    # Compatibility mode (libtool, hammer, split_crc)
geninfo --external / --no-external                     # Control external file capture
geninfo --large-file <regexp>                          # Mark large files for sequential processing
geninfo --derive-func-data                             # Derive function data from line coverage
geninfo --no-markers                                   # Ignore LCOV exclusion markers in source
```

Compatibility modes:
- `libtool` — Handle libtool wrapper scripts in build directories (default: on)
- `hammer` — Handle gcc 3.3 era split checksums (default: auto)
- `split_crc` — Handle Android 4.4.0 split CRC format (default: auto)

### `genhtml` — HTML Report Generator

```
genhtml <info-file>... --output-directory <dir>                # Generate HTML report
genhtml --baseline-file <baseline> <current>... --output-directory <dir>  # Differential report
```

Key genhtml-only options:
- `--baseline-file <file>` — Baseline for differential coverage
- `--diff-file <file>` — External diff for differential analysis
- `--baseline-title <title>` / `--baseline-date <date>` — Differential report labels
- `--show-details` / `-s` — Show detailed source view (default for non-differential)
- `--frames` — Generate frames-based navigation (requires genpng)
- `--dark-mode` — Dark color scheme output
- `--flat` / `--hierarchical` — Report layout: flat file list or directory hierarchy
- `--show-navigation` — Hyperlinks to first/next uncovered region
- `--show-owners` — Show code author column in source view
- `--show-noncode` — Show authors for non-code lines (comments)
- `--show-proportion` — Show proportion of lines/branches exercised within functions
- `--suppress-aliases` — Hide function alias list
- `--annotate-script <script>` — Blame annotation callback
- `--select-script <script>` — Subset selection callback
- `--simplify-script <script>` — C++ name simplification callback
- `--date-bins <days>` — Date binning cutpoints
- `--date-labels <labels>` — Labels for date bins
- `--html-prolog <file>` / `--html-epilog <file>` — Custom HTML header/footer
- `--css-file <file>` — External CSS stylesheet
- `--html-extension <ext>` — Custom page extension (default: html)
- `--html-gzip` — Compress output with gzip
- `--desc-file <file>` / `--keep-descriptions` — Test case descriptions
- `--legend` — Include color legend
- `--no-source` — Skip source code view pages
- `--no-html` — Skip HTML, only write coverage DB (used with `--save`)
- `--highlight` — Syntax highlight source code
- `--precision <N>` — Coverage rate decimal precision (default: 1)
- `--missed` — Show missed counts instead of hit counts
- `--new-file-as-baseline` — Treat files absent in baseline as covered
- `--elide-path-mismatch` — Suppress path mismatch errors in differential mode
- `--synthesize-missing` — Generate fake source for missing files
- `--unreachable-script <script>` — Mark branches/conditions as unreachable
- `--fail-under-lines <N>` / `--fail-under-branches <N>` — Exit with error if below threshold
- `--trivial-function-threshold <N>` — Max lines for `--filter trivial`

### `perl2lcov` — Perl Coverage Translator

Translates a Devel::Cover coverage database directory to `.info` format.

```
perl2lcov --output <file> [--testname <name>] <cover_db_dir> [...]
perl2lcov [shared options] --output perlcov.info cover_db
```

### `py2lcov` — Python Coverage Translator

Translates Python Coverage.py data to `.info` format.

```
py2lcov --output <file> [--test-name <name>] [--checksum] [--version-script <script>] <coverage.dat> [...]
py2lcov --input <xml> --output <file>   # Deprecated XML path
py2lcov --cmd <coverage_executable>     # Use custom coverage command
py2lcov --no-functions                  # Skip function derivation
```

### `xml2lcov` — XML Coverage Translator

Translates Cobertura-style XML to `.info` format.

```
xml2lcov --output <file> [--test-name <name>] [--checksum] [--version-script <script>] <coverage.xml> [...]
```

### `llvm2lcov` — LLVM Coverage Translator

Translates LLVM `llvm-cov export -format=text` JSON to `.info` format.

```
llvm2lcov --output <file> [--testname <name>] [--branch-coverage] [--mcdc-coverage] <file.json> [...]
```

### `gendesc` — Test Description Generator

```
gendesc --output-filename <file> <descriptions.txt>
```

Input format: `<test name><whitespace><description>` (one per test, multi-line descriptions allowed).

### `genpng` — PNG Overview Generator

```
genpng <source-file> --output-filename <file>
```

Creates a PNG where each source character maps to a colored pixel, used by genhtml's `--frames` option for overview navigation. Requires GD.pm.

---

## `.info` Tracefile Format

The `.info` file is a plain-text format documented in `geninfo(1)`. It consists of:

```
TN:<test name>               # Test name record
SF:<absolute source path>    # Source file record
DA:<line>,<hit count>        # Line coverage data
DA:<line>,<hit count>,<checksum>  # With optional MD5 checksum
BRDA:<line>,<block>,<branch>,<taken>  # Branch coverage data (optional)
BRF:<total branches>         # Branch summary
BRH:<hit branches>           # Branch hit summary
FNDA:<hit count>,<fn name>   # Function data (optional)
FNF:<total functions>        # Function summary
FNH:<hit functions>          # Function hit summary
BA:<line>,<fn name>          # Branch expression alias (genhtml internal)
DA:<line>,<hit count>,<mcdc_hash>  # MC/DC data (optional)
LF:<total lines>             # Lines found summary
LH:<hit lines>               # Lines hit summary
end_of_record                # Record terminator
```

Comments (`#`) are supported. Multiple files can be concatenated. The format supports merging via union (addition of hit counts) or intersection (minimum of hit counts).

---

## `lcovrc` Configuration File

The configuration file (system `/etc/lcovrc`, user `~/.lcovrc`) uses a simple `key = value` format with `#` comments. All LCOV tools read it. Key configuration sections:

**Coverage thresholds:**
- `genhtml_hi_limit`, `genhtml_med_limit` — Global rate limits (default: 90/75)
- `genhtml_line_hi_limit`, `genhtml_line_med_limit` — Line-specific limits
- `genhtml_branch_hi_limit`, `genhtml_branch_med_limit` — Branch-specific limits
- `genhtml_function_hi_limit`, `genhtml_function_med_limit` — Function-specific limits
- `genhtml_mcdc_hi_limit`, `genhtml_mcdc_med_limit` — MC/DC-specific limits
- `fail_under_lines`, `fail_under_branches` — Exit with error below threshold

**Error handling:**
- `ignore_errors = source,mismatch,empty,...` — Default ignored errors
- `max_message_count = N` — Stop after N messages (default: 100)
- `stop_on_error = 0|1` — Stop or keep going on error (default: 1)
- `treat_warning_as_error = 0|1` — Escalate warnings to errors (default: 0)

**Parallel execution:**
- `parallel = N` — Number of parallel workers (default: 1/sequential)
- `memory = N` — Max memory in Mb before stopping forks (default: 0/unlimited)
- `memory_percentage = N` — Max memory as % of system RAM
- `max_tasks_per_core = N` — Files per parallel thread (default: 20)
- `max_fork_fails = N` — Consecutive fork failures before give up (default: 5)
- `fork_fail_timeout = N` — Seconds to wait after fork failure (default: 10)

**Coverage types:**
- `function_coverage = 0|1` — Enable/disable function coverage (default: 1)
- `branch_coverage = 0|1` — Enable/disable branch coverage (default: 0)
- `mcdc_coverage = 0|1` — Enable/disable MC/DC coverage (default: 0)

**Exclusion patterns:**
- `include = <glob>` / `exclude = <glob>` — File inclusion/exclusion
- `substitute = s#pat#repl#g` — Path substitution
- `omit_lines = <regexp>` — Line exclusion patterns
- `erase_functions = <regexp>` — Function exclusion patterns

**Navigation and display:**
- `genhtml_overview_width`, `genhtml_nav_resolution`, `genhtml_nav_offset` — Overview image params
- `genhtml_line_field_width`, `genhtml_branch_field_width`, `genhtml_mcdc_field_width` — Column widths
- `genhtml_dark_mode = 0|1` — Dark color scheme
- `genhtml_hierarchical = 0|1` — Hierarchical directory view
- `genhtml_flat_view = 0|1` — Flat file list view
- `genhtml_show_navigation = 0|1` — Navigation hyperlinks

**External tool paths:**
- `geninfo_gcov_tool = gcov` — Path to gcov
- `demangle_cpp = c++filt` — C++ demangler (repeatable with args)
- `lcov_insmod_tool`, `lcov_modprobe_tool`, `lcov_rmmod_tool` — Kernel module tools
- `lcov_gcov_dir = /proc/gcov` — Kernel gcov data directory
- `lcov_json_module = auto` — JSON module selection

---

## Source Code Exclusion Markers

LCOV recognizes special comment markers in source code to exclude regions, lines, or branches from coverage:

```
LCOV_EXCL_START      — Begin excluded region (all coverage types)
LCOV_EXCL_STOP       — End excluded region
LCOV_EXCL_LINE       — Exclude this line from all coverage
LCOV_EXCL_BR_START   — Begin branch-excluded region
LCOV_EXCL_BR_STOP    — End branch-excluded region
LCOV_EXCL_BR_LINE    — Exclude this line's branches only
LCOV_EXCL_EXCEPTION_BR_START  — Begin exception-branch-excluded region
LCOV_EXCL_EXCEPTION_BR_STOP   — End exception-branch-excluded region
LCOV_EXCL_EXCEPTION_BR_LINE   — Exclude exception branches on this line
LCOV_UNREACHABLE_START   — Begin unreachable region (error if hit)
LCOV_UNREACHABLE_STOP    — End unreachable region
LCOV_UNREACHABLE_LINE    — Mark this line as unreachable
```

These can be overridden via lcovrc: `lcov_excl_line`, `lcov_excl_br_line`, etc. The `--no-markers` flag suppresses all marker processing. The `--filter region`, `--filter branch_region`, and `--filter exception` options control whether these exclusions are applied during HTML generation.

---

## Callback Interfaces

LCOV supports pluggable callbacks for integration with external systems. Callbacks can be executables (slower, invoked per-file) or Perl modules (faster, loaded once). They are invoked via `--<type>-script <script>` flags.

### Standard Callback Interface

All callbacks receive their parameters as command-line arguments and return results to stdout/stderr with exit codes:
- Exit 0: success
- Exit 1 (or higher): specific failure

### Version Script (`--version-script`)
Called to determine a source file's version ID. Used to detect mismatches before aggregation.
```
<script> <source_file_path>
```

### Annotate Script (`--annotate-script`)
Called to get git-blame-like annotation for each line. Used for owner/date binning.
```
<script> <source_file_path>
```
Returns tab-separated lines: `<commit_id>\t<author>\t<date>\t<line_num>`

### Criteria Script (`--criteria-script`)
Called with JSON summary data to check coverage criteria.
```
<script> <level> <json_summary_string>
```
Returns exit 0 if criteria met, non-zero otherwise. Level is "top", "directory", or "file".

### Select Script (`--select-script`)
Filters coverage data to show only specific changes.
```
<script> <file_path> <line_number>
```
Returns exit 0 to include the line, non-zero to exclude.

### Resolve Script (`--resolve-script`)
Resolves source file pathnames in complex build environments.
```
<script> <file_path>
```
Returns resolved path to stdout.

### History Script (`--history-script`)
Called before and after parallel execution to improve load balancing.
```
<script> --start  # Called at start of child process
<script> --done <json_profile_data>  # Called after child completes
```

### Simplify Script (`--simplify-script`)
Shortens C++ template/function names for display.
```
<script> <long_function_name>
```
Returns simplified name to stdout.

### Unreachable Script (`--unreachable-script`)
Marks specific branch expressions as unreachable.
```
<script> <file_path> <line_number> <branch_expression>
```
Returns exit 0 if unreachable, non-zero otherwise.

## Coverage Filter Types

Available via `--filter <type,...>`:

| Filter | Variable | Purpose |
|--------|----------|---------|
| `branch` | `$FILTER_BRANCH_NO_COND` | Remove branches on lines with no conditional expressions |
| `brace` | `$FILTER_LINE_CLOSE_BRACE` | Remove line coverage for closing braces with same count as predecessor |
| `blank` | `$FILTER_BLANK_LINE` | Remove coverage for blank lines |
| `directive` | `$FILTER_DIRECTIVE` | Remove LLVM compiler directive lines |
| `range` | `$FILTER_LINE_RANGE` | Remove lines beyond end of file |
| `line` | `$FILTER_LINE` | Backward-compat: blank + brace |
| `initializer` | `$FILTER_INITIALIZER_LIST` | Remove initializer list artifacts |
| `function` | `$FILTER_FUNCTION_ALIAS` | Merge duplicate functions on same file/line |
| `missing` | `$FILTER_MISSING_FILE` | Suppress errors for missing source files |
| `region` | `$FILTER_EXCLUDE_REGION` | Honor LCOV_EXCL_START/STOP regions |
| `branch_region` | `$FILTER_EXCLUDE_BRANCH` | Honor LCOV_EXCL_BR_START/STOP regions |
| `exception` | `$FILTER_EXCEPTION_BRANCH` | Remove exception handling branches |
| `orphan` | `$FILTER_ORPHAN_BRANCH` | Remove lone branches in a block |
| `mcdc` | `$FILTER_MCDC_SINGLE` | Remove MC/DC with single expression (identical to branch) |
| `trivial` | `$FILTER_TRIVIAL_FUNCTION` | Remove functions below threshold line count |

## Error Types

Tools share 30+ error types (defined in `lcovutil.pm`). Common ones:

| Error | Variable | Meaning |
|-------|----------|---------|
| `source` | `$ERROR_SOURCE` | Cannot read/find source file |
| `mismatch` | `$ERROR_MISMATCH` | Source file checksum mismatch |
| `empty` | `$ERROR_EMPTY` | No coverage records found |
| `gcov` | `$ERROR_GCOV` | gcov tool execution error |
| `graph` | `$ERROR_GRAPH` | `.gcno` file parsing error |
| `branch` | `$ERROR_BRANCH` | Invalid branch numbering |
| `corrupt` | `$ERROR_CORRUPT` | Corrupt input file |
| `format` | `$ERROR_FORMAT` | Bad `.info` file record |
| `negative` | `$ERROR_NEGATIVE` | Negative hit count |
| `version` | `$ERROR_VERSION` | Source version mismatch |
| `unsupported` | `$ERROR_UNSUPPORTED` | Unsupported feature/usage |
| `inconsistent` | `$ERROR_INCONSISTENT_DATA` | Inconsistent coverage data |
| `callback` | `$ERROR_CALLBACK` | Callback script error |
| `parallel` | `$ERROR_PARALLEL` | Parallel execution error |
| `child` | `$ERROR_CHILD` | Child process error |
| `fork` | `$ERROR_FORK` | Fork failure |
| `excessive` | `$ERROR_EXCESSIVE_COUNT` | Suspiciously high hit count |
| `unreachable` | `$ERROR_UNREACHABLE` | Coverpoint hit in unreachable region |
