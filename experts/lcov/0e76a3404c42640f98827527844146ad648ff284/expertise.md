### Core Architecture
- Monolithic shared library `lib/lcovutil.pm` (~10,016 lines) — single Perl module providing all common infrastructure for the LCOV tool suite
- Pipeline architecture: raw coverage data → `.info` tracefile → HTML report
- Five main Perl tools (`lcov`, `geninfo`, `genhtml`, `genpng`, `gendesc`) all import `lcovutil.pm` via `use lib "$FindBin::RealBin/../lib"`
- Four translator tools (`perl2lcov`, `py2lcov`, `xml2lcov`, `llvm2lcov`) feed into the same `.info` pipeline
- `bin/py2lcov` and `bin/xml2lcov` share a common Python module `bin/xml2lcovutil.py` with class `ProcessFile`
- Callback system with 8 pluggable script types: annotate, criteria, version, select, resolve, context, history, simplify, unreachable
- Parallel execution model: fork/join with memory-aware throttling, load-balancing history, and profile data collection
- Three coverage types: line, function, and branch — plus MC/DC (Modified Condition/Decision Coverage) requiring GCC 14.2+ or LLVM 18+
- `lcovutil.pm` exports ~120+ symbols; key imports include `$tool_name`, `$tool_dir`, `$lcov_version`, `$lcov_url`, all `$ERROR_*` constants, all `$FILTER_*` constants, `@cov_filter`, `rate`, `get_overall_line`, `parseOptions`, `strip_directories`, `define_errors`, `parse_ignore_errors`, `ignorable_error`, `ignorable_warning`

### Main Tools
- `bin/lcov` — 2,058 lines; front-end wrapper: `--capture`, `--zerocounters`, `--add-tracefile`, `--extract`, `--remove`, `--list`, `--summary`, `--intersect`, `--subtract`, `--prune-tests`, `--to-package`, `--from-package`, kernel coverage via `--kernel-directory`, `lcov_geninfo()` internal function
- `bin/geninfo` — 4,182 lines; reads `.gcno`/`.gcda` files, supports intermediate JSON format (GCC 9+), `compat` modes (libtool, hammer, split_crc), `.gcno` graph parsing functions (`read_gcno`, `graph_from_bb`, `read_gcno_function_record`), gcov version detection (`get_gcov_version`, `GCOV_VERSION_4_2_0`, `GCOV_VERSION_4_7_0`, `GCOV_VERSION_8_0_0`)
- `bin/genhtml` — 14,293 lines; HTML report generation, differential coverage categorization, date/owner binning, hierarchical/flat display, `%tlaColor`/`%tlaTextColor` dictionary (UBC, GBC, LBC, CBC, GNC, UNC, ECB, EUB, GIC, UIC), `FileDetails` data structure, `--save` mode for serializable coverage DB
- `bin/genpng` — 398 lines; source file to PNG image, requires GD.pm, one-pixel-per-character mapping with coverage coloring
- `bin/gendesc` — 190 lines; test description file parser and formatter
- `bin/perl2lcov` — 444 lines; uses `Devel::Cover::DB` and `Devel::Cover::Truth_Table`, maps Perl statement/branch/condition/subroutine coverage to `.info`
- `bin/py2lcov` — 212 lines; uses `xml2lcovutil.ProcessFile`, supports `--no-functions`, `--cmd` for custom coverage executable, reads Python `.dat` files or intermediate XML
- `bin/xml2lcov` — 110 lines; reads Cobertura XML, delegates to `xml2lcovutil.ProcessFile`
- `bin/xml2lcovutil.py` — 499 lines; class `ProcessFile` with `line_hash()` for MD5+base64 checksum, XML parsing via `xml.etree.ElementTree`, branch-to-four-tuple mapping, function derivation for Python
- `bin/llvm2lcov` — 545 lines; reads `llvm-cov export -format=text` JSON output, supports MC/DC from LLVM 18+ and LLVM 21+ improved format
- `bin/fix.pl` — post-install rewrite of version strings, library paths (`--fixlibdir`), and binary paths (`--fixbindir`)
- `bin/checkstyle.sh` — perltidy wrapper for code style enforcement
- `bin/get_version.sh` — extracts version/release strings; `bin/get_changes.sh` — git log to CHANGES; `bin/copy_dates.sh` — timestamp preservation

### .info Tracefile Format
- Record types: `TN:` (test name), `SF:` (source file), `DA:` (line coverage with optional checksum), `BRDA:` (branch coverage: line, block, branch, taken), `FNDA:` (function hit count and name), `BRF:`/`BRH:` (branch found/hit summaries), `FNF:`/`FNH:` (function found/hit summaries), `LF:`/`LH:` (line found/hit summaries), `BA:` (branch alias), `end_of_record`
- MC/DC data: extended `DA:` records with MC/DC hash suffix
- Comments: `#` prefix lines
- Multi-file concatenation supported; merging via union (addition) or intersection (minimum) of hit counts
- File matching glob patterns: `*.info` default via `info_file_pattern`

### Configuration System (`lcovrc`)
- System default: `/etc/lcovrc`; user override: `~/.lcovrc`; command-line override: `--rc key=value`
- `lcovrc` file: 532-line reference with all documented options and extensive comments
- Rate limit thresholds: `genhtml_hi_limit` (90), `genhtml_med_limit` (75), plus per-type `genhtml_line_hi_limit`, `genhtml_branch_hi_limit`, `genhtml_function_hi_limit`, `genhtml_mcdc_hi_limit`
- Fail-under: `fail_under_lines`, `fail_under_branches` — exit with non-zero if below threshold
- Coverage type toggles: `function_coverage` (default 1), `branch_coverage` (default 0), `mcdc_coverage` (default 0)
- Error handling: `ignore_errors`, `max_message_count` (100), `stop_on_error` (1), `treat_warning_as_error` (0), `warn_once_per_file` (1)
- Parallelism: `parallel` (1), `memory` (0/unlimited), `memory_percentage`, `max_fork_fails` (5), `fork_fail_timeout` (10), `max_tasks_per_core` (20)
- File patterns: `include`, `exclude`, `substitute`, `omit_lines`, `erase_functions`
- Display: `genhtml_dark_mode`, `genhtml_hierarchical`, `genhtml_flat_view`, `genhtml_show_navigation`, `genhtml_show_owners`, `genhtml_show_noncode_owners`, `genhtml_show_function_proportion`, `genhtml_precision`
- Column widths: `genhtml_line_field_width` (12), `genhtml_branch_field_width` (16), `genhtml_mcdc_field_width` (16), `genhtml_owner_field_width` (20), `genhtml_age_field_width` (5)
- External tools: `geninfo_gcov_tool`, `demangle_cpp`, `lcov_insmod_tool`, `lcov_modprobe_tool`, `lcov_rmmod_tool`
- JSON module selection: `lcov_json_module = auto` (prefers JSON::XS, falls back to Cpanel::JSON::XS, JSON::PP, JSON)
- Forwarding: `geninfo_intermediate = auto` (intermediate gcov format), `geninfo_auto_base = 1`, `geninfo_external`, `geninfo_adjust_src_path`
- Callback scripts: `genhtml_annotate_script`, `genhtml_annotate_tooltip`, `criteria_script`, `criteria_callback_data`, `criteria_callback_levels`, `version_script`, `select_script`, `num_context_lines`, `resolve_script`, `history_script`
- Exclusion markers overridable: `lcov_excl_line`, `lcov_excl_br_line`, `lcov_excl_start`, `lcov_excl_stop`, `lcov_excl_br_start`, `lcov_excl_br_stop`, `lcov_excl_exception_br_start`, `lcov_excl_exception_br_stop`
- Unreachable markers: `lcov_unreachable_line`, `lcov_unreachable_start`, `lcov_unreachable_stop`
- Source filtering: `filter_lookahead` (10), `filter_bitwise_conditional` (0), `filter_blank_aggressive` (0)
- Misc: `lcov_list_full_path`, `lcov_list_width` (80), `lcov_list_truncate_max` (20), `info_file_pattern` (`*.info`), `split_char` (`,`), `case_insensitive` (0), `sort_input` (1)
- File extensions: `c_file_extensions`, `rtl_file_extensions`, `java_file_extensions`, `perl_file_extensions`, `python_file_extensions`

### Coverage Filters
- 14 filter types defined in `lcovutil.pm` via `%COVERAGE_FILTERS` hash mapping strings to variable references
- `branch` (`$FILTER_BRANCH_NO_COND`): suppress branches on lines with no conditional expressions
- `brace` (`$FILTER_LINE_CLOSE_BRACE`): suppress closing brace lines when predecessor has same hit count
- `blank` (`$FILTER_BLANK_LINE`): suppress coverage for blank/whitespace-only lines
- `region` (`$FILTER_EXCLUDE_REGION`): honor `LCOV_EXCL_START`/`LCOV_EXCL_STOP` markers
- `branch_region` (`$FILTER_EXCLUDE_BRANCH`): honor `LCOV_EXCL_BR_START`/`LCOV_EXCL_BR_STOP`
- `function` (`$FILTER_FUNCTION_ALIAS`): merge duplicate function names on same file/line
- `line` (`$FILTER_LINE`): backward-compat alias for `blank` + `brace`
- `directive` (`$FILTER_DIRECTIVE`): suppress LLVM compiler directive lines
- `range` (`$FILTER_LINE_RANGE`): suppress lines beyond file end
- `initializer` (`$FILTER_INITIALIZER_LIST`): suppress initializer list artifacts
- `missing` (`$FILTER_MISSING_FILE`): suppress errors for missing source files
- `exception` (`$FILTER_EXCEPTION_BRANCH`): suppress exception handling branches
- `orphan` (`$FILTER_ORPHAN_BRANCH`): suppress solitary branches in a block
- `mcdc` (`$FILTER_MCDC_SINGLE`): suppress MC/DC expressions that reduce to simple branch
- `trivial` (`$FILTER_TRIVIAL_FUNCTION`): suppress functions below `trivial_function_threshold` lines
- Filter control: `parse_cov_filters()`, `summarize_cov_filters()`, `disable_cov_filters()`, `reenable_cov_filters()`, `is_filter_enabled()`
- Also tracked: `%excluded_files` for `--exclude`/`--include` glob patterns, `@omit_line_patterns`, `@exclude_function_patterns`

### Error System
- 30+ named error types with `$ERROR_*` scalar variables and a `@lcovErrs` array mapping string names to references
- `$ERROR_GCOV`, `$ERROR_SOURCE`, `$ERROR_GRAPH`, `$ERROR_MISMATCH`, `$ERROR_EMPTY`, `$ERROR_FORMAT`, `$ERROR_VERSION`, `$ERROR_UNUSED`
- `$ERROR_BRANCH`, `$ERROR_PACKAGE`, `$ERROR_CORRUPT`, `$ERROR_NEGATIVE`, `$ERROR_COUNT`, `$ERROR_UNSUPPORTED`, `$ERROR_DEPRECATED`
- `$ERROR_PARALLEL`, `$ERROR_PARENT`, `$ERROR_CHILD`, `$ERROR_FORK`, `$ERROR_EXCESSIVE_COUNT`, `$ERROR_MISSING`, `$ERROR_UNREACHABLE`
- `$ERROR_CALLBACK`, `$ERROR_INCONSISTENT_DATA`, `$ERROR_RANGE`, `$ERROR_UTILITY`, `$ERROR_USAGE`, `$ERROR_PATH`, `$ERROR_INTERNAL`
- `$ERROR_UNMAPPED_LINE`, `$ERROR_UNKNOWN_CATEGORY`, `$ERROR_ANNOTATE_SCRIPT` (genhtml-specific)
- Ignorable errors mechanism: `--ignore-errors <csv_list>`, `ignorable_error()`, `ignorable_warning()`, `is_ignored()`
- Message counting: `@message_count`, `@expected_message_count`, `--expect-message-count` option, `summarize_messages()`
- `$stop_on_error` flag controls whether tool stops or continues after ignorable error

### Callback Scripts and VCS Integration
- `scripts/gitblame.pm` — git blame with `--p4` (Perforce mapping), `--cache` (performance caching via `annotateutil.pm`), `--prefix`, `--abbrev`; used as `--annotate-script`
- `scripts/gitblame` — executable wrapper for `gitblame.pm`
- `scripts/gitdiff` — unified diff between two git SHAs; supports `--exclude`, `--include`, `--no-unchanged`, `--prefix`, `--blank` (ignore whitespace)
- `scripts/gitversion.pm` — git version extraction callback; `scripts/gitversion` — wrapper
- `scripts/batchGitVersion.pm` — batch git version extraction for multiple files
- `scripts/p4annotate.pm` — Perforce blame annotation; `scripts/p4annotate` — wrapper
- `scripts/p4udiff` — Perforce unified diff generation
- `scripts/P4version.pm` — Perforce version extraction; `scripts/getp4version` — wrapper
- `scripts/criteria.pm` — coverage criteria enforcement; checks `UNC + LBC + UIC == 0` on JSON summary; supports `--signoff`, `--function`, `--branch`, `--mcdc` flags
- `scripts/criteria` — wrapper for criteria.pm
- `scripts/select.pm` — subset selection callback; filters lines/commits for focused review
- `scripts/simplify.pm` — shortens C++ template and function names for display readability
- `scripts/context.pm` — environment/context tracking for infrastructure debugging
- `scripts/history.pm` — load-balancing optimization via prior execution profile data
- `scripts/unreach.pm` — marks branch expressions as unreachable to exclude from DB
- `scripts/threshold.pm` — threshold checking utility
- `scripts/annotateutil.pm` — shared utilities: `not_in_repo()`, `resolve_cache_dir()`, `find_in_cache()`, `store_in_cache()`
- `scripts/spreadsheet.py` — Excel report generation from JSON profile data via xlsxwriter
- `scripts/analyzeInfoFiles` — utility for inspecting `.info` file contents
- `scripts/get_signature` — file signature extraction callback
- Callback lifecycle: `configure_callback()`, `cleanup_callbacks()`, `@callback_save_restore`, `@callback_finalize`, `@callback_start_list`, `@callback_state`

### Build System and Testing
- Top-level `Makefile` (330 lines): targets `install`, `uninstall`, `dist`, `check`/`test`, `clean`, `checkstyle`, `release`
- Version extraction via `bin/get_version.sh --version`/`--release`/`--full`
- `make install PREFIX=/usr/local`; custom prefix support: `make PREFIX=$HOME/my_lcov install`
- `make dist`: creates `lcov-$(VERSION).tar.gz` and RPM packages via `rpmbuild`
- `make checkstyle MODE=full UPDATE=1`: enforces perltidy formatting (`.perltidyrc` — 153 lines of rules)
- `make COVERAGE=1 test`: runs test suite under Devel::Cover, generates LCOV's own coverage report
- `tests/Makefile`: dispatches to `genhtml`, `lcov`, `gendiffcov`, `llvm2lcov`, `py2lcov`, `perl2lcov`, `xml2lcov`
- `tests/common.mak`: shared make variables (`LCOV_HOME`, `BINDIR`, `SCRIPTDIR`, `VERSION_SCRIPT`, `ANNOTATE_SCRIPT`, `SPREADSHEET_TOOL`)
- `tests/common.tst`: bash test framework with common test routines
- `tests/lcovrc`: test-specific configuration
- Self-coverage: `COVER_DB` → `perl2lcov` → `perlcov.info`; `PYCOV_DB` → `py2lcov` → `pycov.info`; combined via `genhtml` → `lcov_coverage/index.html`
- `make release VERSION=2.5.0`: commits version updates and creates git tag `v2.5.0`
- `.editorconfig`: 4-space indent, LF line endings, UTF-8; tabs for shell scripts and Makefiles

### Color System and Display
- Two palettes: `%normal_palette` (light background) and `%dark_palette` (dark background), each with `COLOR_00` through `COLOR_20`
- Three-letter acronym (TLA) colors in `%tlaColor`: UBC (Uncovered Baseline Code), GBC (Gained Baseline Code), LBC (Lost Baseline Code), CBC (Covered Baseline Code), GNC (Gained New Code), UNC (Uncovered New Code), ECB (Excluded Covered Branch), EUB (Excluded Uncovered Branch), GIC (Gained Indirectly Covered), UIC (Uncovered Indirectly Covered), EUC (Excluded Uncovered Code), ECC (Excluded Covered Code)
- `%tlaTextColor` for text color on TLA background; `%pngChar` for PNG character mapping; `%pngMap` for character-to-TLA mapping
- Coverage rate limit buckets: HI (green, rate >= hi_limit), MED (orange, med_limit <= rate < hi_limit), LO (red, rate < med_limit)
- Width constants: `$overview_width` (80), `$nav_resolution` (4), `$nav_offset` (10), `$func_offset` (2)
- `genhtml --dark-mode` toggles between `%dark_palette` and `%normal_palette`

### Kernel Coverage Support
- `bin/lcov` kernel coverage constants: `$GKV_PROC` (0, external /proc patch), `$GKV_SYS` (1, upstream /sys in 2.6.31+)
- `setup_gkv()` auto-detects kernel gcov version
- `kernel_reset()`, `kernel_capture()`, `kernel_capture_initial()` functions in `bin/lcov`
- Kernel module tools: `lcov_insmod_tool`, `lcov_modprobe_tool`, `lcov_rmmod_tool`
- `--kernel-directory` flag for capturing specific kernel subdirectories

### Package Support
- `bin/lcov` package operations: `--to-package <package>`, `--from-package <package>`
- `create_package()` function bundles coverage data for transfer
- `package_capture()` reads coverage from a package
- Package metadata files: `.gcov_kernel_version`, `.build_directory`

### Parallel Execution Framework
- `bin/lcovutil.pm`: `init_parallel_params()`, `current_process_size()`, `report_parallel_error()`
- `report_exit_status()`, `check_parent_process()`, `report_unknown_child()`
- `save_profile()`, `merge_child_profile()` — profiling data collection and merging
- `ChildProcessMgr` module and `WorkDispatcher` module used in `bin/geninfo` and `bin/genhtml`
- `--profile [file]` for emitting JSON profile data; `spreadsheet.py` for viewing
- `close_on_exec()` semantics for child process isolation
- `$maxParallelism`, `$maxMemory`, `$memoryPercentage`, `$max_fork_fails`, `$fork_fail_timeout`

### Compatibility Modes (geninfo)
- Three compatibility modes: `COMPAT_MODE_LIBTOOL` (handles libtool wrappers), `COMPAT_MODE_HAMMER` (gcc 3.3 era), `COMPAT_MODE_SPLIT_CRC` (Android 4.4.0)
- Three values per mode: `COMPAT_VALUE_OFF`, `COMPAT_VALUE_ON`, `COMPAT_VALUE_AUTO`
- `--compat libtool=on,hammer=auto,split_crc=auto` CLI syntax; config: `geninfo_compat`
- Auto-detection routines for hammer and split_crc modes

### File Handling and Path Resolution
- `@file_subst_patterns`, `subst_file_name()` — path substitution (e.g., `/tmp/build` → `/usr/src`)
- `strip_directories()` — removes common directory prefixes
- `--build-directory` search path for `.gcno` files; `--source-directory` for source files
- `is_external()`, `@internal_dirs`, `$opt_no_external` — external file classification
- `--resolve-script` callback for complex path resolution environments
- File extension maps: `$c_file_extensions`, `$rtl_file_extensions`, etc.
- `case_insensitive` toggle for glob matching
- `sort_inputs` to reduce processing order dependencies

### Differential Coverage
- Baseline-vs-current comparison produces categorized coverage change analysis
- TLA categories distinguish: unchanged code (maintained/added/lost coverage), new code (covered/uncovered), deleted code
- `--baseline-file`, `--diff-file` options for baseline specification
- `--baseline-title`, `--baseline-date`, `--current-date`, `--new-file-as-baseline`, `--elide-path-mismatch`
- Date binning: `--date-bins N` and `--date-labels`
- Owner binning: `--annotate-script`, `--show-owners`, `--show-noncode`, `--owner-table-entries`, `--truncate-owner-table`

### Dependency Tree
- Required Perl: Capture::Tiny, DateTime, Digest::MD5, File::Spec, JSON::XS (preferred), Memory::Process, Module::Load::Conditional, Scalar::Util, Time::HiRes, TimeDate/Date::Parse
- Required Python: Coverage.py (for py2lcov), xlsxwriter (optional, for spreadsheet.py)
- Optional: GD.pm (for genpng), Devel::Cover (for perl2lcov + self-coverage), perltidy (for checkstyle)
- External tools: gcov (GCC), llvm-cov (LLVM), c++filt (demangling), git, p4 (Perforce)
