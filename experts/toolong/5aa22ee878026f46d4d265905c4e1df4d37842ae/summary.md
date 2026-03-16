# Toolong — Repository Summary

## Purpose and Goals

Toolong (`tl`) is a terminal-based log file viewer, tailer, and analyzer built by Will McGugan (Textualize). Version 1.5.0. It aims to replace the traditional `tail` + `less` + `grep` workflow with a single, interactive TUI that opens log files — including multi-gigabyte ones — instantaneously, supports live tailing, full-text and regex search, JSONL pretty-printing, and timestamp-aware merging of multiple log files.

The project was motivated by the author's past as a web developer who frequently analyzed logs on remote servers via SSH. The goal is a tool that is snappy, requires minimal friction, and handles the grunt work automatically.

## Key Features and Capabilities

- **Instant open** — even multi-GB files open immediately. The app scans for line breaks in the background using `mmap` while the UI remains responsive.
- **Live tailing** — watches a file for new content using OS-appropriate mechanisms (`selectors`-based on macOS, polling on other platforms). Shows a "pending lines" overlay when new content arrives while the user is scrolled up.
- **Syntax highlighting** — auto-detects log formats (JSON, Common Log Format, Combined Log Format, or generic) and applies Rich-based syntax highlighting. HTTP status codes are colour-coded by class (2xx green, 4xx red, 5xx reverse-red, etc.). IP addresses, UUIDs, numbers, and strings are highlighted via `LogHighlighter`.
- **JSONL support** — lines are detected as JSON and pretty-printed with Rich's `JSONHighlighter`; the detail panel renders with `JSON.from_data`.
- **Compressed file support** — `.gz` (gzip) and `.bz2` (bzip2) files are transparently decompressed into a temporary file on open.
- **Multi-file tabs** — multiple files open in tabbed panes; tabs are hidden when only one file is present.
- **Merge mode** — `tl file1.log file2.log --merge` chronologically merges files by auto-detecting timestamps in each line, then sorts the combined view by timestamp. Supports saving the merged output with `--output-merge PATH`.
- **Pointer mode** — click or press Enter on any line to enter pointer mode; pressing Enter again or clicking again opens a detail panel showing the raw line (pretty-printed if JSON).
- **Find dialog** — `Ctrl+F` or `/` opens a docked find dialog with plain-text and regex modes, case-sensitive toggle, and autocomplete suggestions derived from words seen in the current view.
- **Timestamp navigation** — `m`/`M` jump ±1 minute, `o`/`O` jump ±1 hour, `d`/`D` jump ±1 day, using detected timestamps in each line.
- **Go-to line** — `Ctrl+G` opens a modal input to jump directly to a line number.
- **Piping support** — when stdin is not a TTY, data is written to a temp file while a subprocess renders the UI against that file.
- **Line numbers** — `Ctrl+L` toggles line numbers in the gutter.

## Primary Use Cases and Target Audience

- **DevOps / SRE / web developers** monitoring web server access logs, application logs, or system logs.
- Anyone who would previously reach for `tail -f`, `less`, or `grep` on log files.
- Engineers who need to correlate events across multiple log files chronologically.
- Users who want a more ergonomic, terminal-native log viewer that supports large files without loading them fully into memory.

## High-Level Architecture Overview

Toolong is built on two key libraries:

- **[Textual](https://github.com/Textualize/textual)** (≥0.58.0) — the reactive TUI framework that drives the entire UI.
- **[Click](https://click.palletsprojects.com/)** (≥8.1.7) — the CLI entry point and argument parsing layer.
- **[Rich](https://github.com/Textualize/rich)** — syntax highlighting, text rendering, and JSON display (transitively through Textual).

The application is structured around a `UI` Textual `App` that pushes a `LogScreen` containing `TabbedContent`. Each tab holds a `LogView` (a `Horizontal` container) which composes:

1. `LogLines` — the core `ScrollView` that renders log lines, manages line-break indices, handles scanning, tailing, searching, and pointer navigation.
2. `LinePanel` — a side panel showing detail for the selected line.
3. `FindDialog` — a docked search widget.
4. `InfoOverlay` — an overlay showing pending new lines count.
5. `LogFooter` — a status bar with filename, timestamp, line number, and key bindings.

File I/O is isolated in `LogFile`, which uses `mmap` for fast scanning and `os.pread` (or lseek+read on Windows) for random-access line reads. Watching for changes is abstracted via `WatcherBase` with two implementations: `SelectorWatcher` (macOS, event-driven) and `PollWatcher` (other platforms).

Log format detection and timestamp parsing are handled by `FormatParser` and `TimestampScanner` respectively, both using a priority-reordering optimization (the most recently matched format is tried first).

## Related Projects and Dependencies

- **Textual** (`textual>=0.58.0`) — TUI framework from Textualize; the entire UI layer is built on it.
- **Click** (`click>=8.1.7`) — CLI framework for the `tl` command.
- **typing-extensions** (`>=4.9.0`) — backports for `TypeAlias` and similar typing constructs.
- **Rich** — rendering engine (pulled in by Textual); used for `Text`, `JSON`, `JSONHighlighter`, `RegexHighlighter`, terminal themes.
- **[LogMerger](https://github.com/ptmcg/logmerger)** — inspired the merge feature; timestamp regex patterns were borrowed from this project.
- **[lnav](https://lnav.org/)** — a more mature alternative TUI log viewer mentioned as a reference.
- **textual-dev** (`>=1.4.0`) — dev dependency for Textual development tools.
- Build tool: **Poetry** with `poetry-core` backend.
