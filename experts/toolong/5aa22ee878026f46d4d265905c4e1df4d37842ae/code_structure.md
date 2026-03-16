# Toolong — Code Structure

## Directory Tree (Annotated)

```
toolong/                         # Repository root
├── LICENSE                      # MIT license
├── README.md                    # Project overview, usage, screenshots
├── pyproject.toml               # Poetry package config, deps, entry point
├── poetry.lock                  # Locked dependency tree
└── src/
    └── toolong/                 # Main Python package (src layout)
        ├── __init__.py          # Package marker (empty)
        ├── __main__.py          # Enables `python -m toolong`
        ├── cli.py               # Click CLI entry point (`tl` command)
        ├── ui.py                # Top-level Textual App + LogScreen
        ├── log_view.py          # LogView container + LogFooter + InfoOverlay
        ├── log_lines.py         # LogLines ScrollView (core rendering/scanning)
        ├── log_file.py          # LogFile: file I/O, mmap scanning, compression
        ├── format_parser.py     # Log format detection + line parsing
        ├── timestamps.py        # Timestamp scanning + format definitions
        ├── highlighter.py       # LogHighlighter (Rich RegexHighlighter)
        ├── watcher.py           # WatcherBase abstract + get_watcher() factory
        ├── poll_watcher.py      # PollWatcher (Linux/Windows file watcher)
        ├── selector_watcher.py  # SelectorWatcher (macOS, event-driven)
        ├── find_dialog.py       # FindDialog docked search widget
        ├── line_panel.py        # LinePanel + LineDisplay (detail side panel)
        ├── goto_screen.py       # GotoScreen modal (jump to line number)
        ├── scan_progress_bar.py # ScanProgressBar widget (loading indicator)
        ├── messages.py          # Textual Message dataclasses (app events)
        └── help.py              # HelpScreen modal (F1 help)
```

## Module and Package Organization

The package uses a **`src` layout** (`src/toolong/`), which keeps the importable package separate from project-level files. This prevents accidental imports from the working directory during development.

There is no sub-package nesting; all modules are flat within `src/toolong/`. Each module has a focused responsibility with minimal cross-cutting concerns.

## Key Files and Their Roles

### `cli.py` — CLI Entry Point
The `run()` function is the `tl` console script registered in `pyproject.toml`. It uses Click to parse arguments (`files`, `--merge`, `--output-merge`). When stdin is a TTY, it directly instantiates `UI` and calls `ui.run()`. When stdin is a pipe, it spawns a **subprocess** for the UI while the parent process copies piped data to a temporary file — this clever approach allows `tl` to work as a pipe target while still rendering an interactive TUI.

### `ui.py` — Textual App + Screen
- **`UI(App)`** — the top-level Textual application. Stores `file_paths`, `merge`, `save_merge`, and a `watcher` instance. Sorts file paths using `CompareTokens` (natural sort). On mount, pushes `LogScreen` and starts the watcher thread.
- **`LogScreen(Screen)`** — the main screen. Composes `TabbedContent` with one `TabPane` per file (or a single merged tab). Uses `Lazy()` to defer `LogView` instantiation.
- **`CompareTokens`** — a comparison key class for natural-sorting filenames (handles numeric tokens within dotted filenames).

### `log_view.py` — LogView Container
- **`LogView(Horizontal)`** — the main per-file widget. Composes `LogLines`, `LinePanel`, `FindDialog`, `InfoOverlay`, and `LogFooter`. Handles reactive data-binding between child widgets. Manages `show_find`, `show_panel`, `tail`, and `can_tail` states. Routes messages (TailFile, PointerMoved, PendingLines, ScanProgress, ScanComplete, DismissOverlay, FindDialog events).
- **`LogFooter(Widget)`** — bottom status bar. Shows filename, current line number, timestamp, key binding hints, and a TAIL indicator. Dynamically mounts `FooterKey` labels. Updates via reactive watchers.
- **`InfoOverlay(Widget)`** — floating overlay above the footer showing "+N lines" when new content arrives while user is scrolled up from the tail. Clickable to resume tailing.
- **`FooterKey(Label)`** — clickable key-binding label in the footer.
- **`MetaLabel(Label)`** — clickable meta info label that posts a `Goto` message.

### `log_lines.py` — Core Log Renderer (most complex module)
- **`LogLines(ScrollView)`** — the core widget. Renders log lines on demand using a virtual scroll model. Manages:
  - `_line_breaks: dict[LogFile, list[int]]` — byte offsets of line breaks per file.
  - `_line_cache: LRUCache` — cached decoded line strings.
  - `_text_cache: LRUCache` — cached parsed `(str, Text, datetime|None)` tuples.
  - `_render_line_cache: LRUCache` — cached rendered `Strip` objects.
  - `_merge_lines: list[tuple[float, int, LogFile]]` — sorted `(timestamp, line_no, file)` for merged view.
  - `_search_index: LRUCache` — word prefix index for autocomplete in `FindDialog`.
  - `_line_reader: LineReader` — background thread for async line reads.
  - Scanning is kicked off by `run_scan()` (a `@work(thread=True)` Textual worker).
  - Implements `render_line(y)` and `render_lines(crop)` for custom strip-based rendering.
  - Handles timestamp navigation (`action_navigate`), pointer mode, find/search, and scroll events.
- **`LineReader(Thread)`** — background thread that processes a `Queue` of `(LogFile, index, start, end)` read requests and posts `LineRead` messages back to `LogLines`.
- **`SearchSuggester(Suggester)`** — Textual `Suggester` implementation backed by the `_search_index` LRU cache. Provides word completions in the `FindDialog` input.

### `log_file.py` — File I/O Layer
- **`LogFile`** — wraps a single file path. Handles opening (plain, gzip, bzip2), size detection, thread-safe raw byte reads (`get_raw` using `os.pread` on POSIX or lseek+read on Windows), and line decoding (`get_line`). Provides two generators:
  - `scan_line_breaks()` — scans backwards using `mmap.rfind(b"\n")`, yielding batches of break positions.
  - `scan_timestamps()` — scans forward with `mmap.readline()` + `TimestampScanner`, yielding `(line_no, position, timestamp_float)` batches.
- **`LogError`** — exception class for log-related errors.

### `format_parser.py` — Log Format Detection
- **`FormatParser`** — maintains a list of `LogFormat` instances in priority order. The `parse()` method tries each format in order; on a match it promotes that format to the front (adaptive optimization). Falls back to `DefaultLogFormat`.
- **`LogFormat`** (abstract base) — defines `parse(line) -> ParseResult | None`.
- **`RegexLogFormat`** — base for regex-based formats. Applies `LogHighlighter`, highlights HTTP methods, and colour-codes HTTP status codes.
- **`CommonLogFormat`** — NCSA Common Log Format regex.
- **`CombinedLogFormat`** — Apache Combined Log Format regex (adds referrer, user-agent, session, generation time, virtual host).
- **`JSONLogFormat`** — detects JSON lines; applies `JSONHighlighter` from Rich.
- **`DefaultLogFormat`** — fallback; applies `LogHighlighter` only.
- `ParseResult` type alias: `tuple[Optional[datetime], str, Text]`.

### `timestamps.py` — Timestamp Detection
- **`TimestampScanner`** — scans a log line for any recognized timestamp format using an ordered list of `TimestampFormat` entries. Uses the same adaptive reordering as `FormatParser` to prioritize the most recently matched format.
- **`TIMESTAMP_FORMATS`** — 17 timestamp format patterns covering ISO 8601 variants (with/without milliseconds, T-separator, timezone offsets), syslog (`Jan  1 12:34:56`), Apache CLF (`29/Jan/2024:13:48:00 +0000`), and Unix epoch (10-digit float, 13-digit milliseconds).
- **`parse(line)`** — module-level function returning `(TimestampFormat|None, datetime|None)`.

### `watcher.py` — File Change Watching
- **`WatcherBase(ABC)`** — abstract base class for file watchers. Manages `_file_descriptors: dict[int, WatchedFile]`, a background `Thread`, and an `Event` for clean shutdown. `add()` registers a file descriptor with size-change and error callbacks. `scan_chunk()` is a class method that finds newline positions in a binary chunk.
- **`WatchedFile`** — dataclass holding `LogFile`, a `callback`, and an `error_callback`.
- **`get_watcher()`** — factory function: returns `SelectorWatcher` on Darwin (macOS), `PollWatcher` otherwise.

### `poll_watcher.py` — Polling Watcher
- **`PollWatcher(WatcherBase)`** — polls all watched file descriptors in a tight loop. Reads 64 KB chunks, scans for newlines, invokes callbacks. Sleeps 50ms when no data is available.

### `selector_watcher.py` — Selector Watcher (macOS)
- **`SelectorWatcher(WatcherBase)`** — uses `selectors.DefaultSelector` (kqueue on macOS) to wait for `EVENT_READ` events on file descriptors. Reads 64 KB chunks on each event and invokes callbacks. More efficient than polling; avoids busy-waiting.

### `find_dialog.py` — Search Widget
- **`FindDialog(Widget)`** — docked find bar with a text input (plain) or regex input, case-sensitive checkbox, and regex checkbox. Posts `Update`, `Dismiss`, `MovePointer`, and `SelectLine` messages. Accepts a `Suggester` instance for autocomplete.
- **`Regex(Validator)`** — Textual validator that checks regex compilability.

### `line_panel.py` — Line Detail Panel
- **`LinePanel(ScrollableContainer)`** — right-side panel displayed when a line is selected. Calls `update(line, text, timestamp)` to replace content.
- **`LineDisplay(Widget)`** — renders a single line. If the line is valid JSON, renders `JSON.from_data()`; otherwise renders the highlighted `Text`. Handles escaped newlines (`\\n`) by splitting and joining with real newlines.

### `goto_screen.py` — Go-To Line Modal
- **`GotoScreen(ModalScreen)`** — bottom-right modal with a number input. As the user types, updates `log_lines.pointer_line` in real-time and scrolls to center.

### `scan_progress_bar.py` — Scanning Indicator
- **`ScanProgressBar(Vertical)`** — docked progress indicator shown while a file is being scanned. Has `message` and `complete` reactives. Hidden by default; shown via `-has-content` class when a message is set.

### `messages.py` — Internal Message Bus
All internal communication between widgets is done via Textual messages:
- `Goto` — triggers "go to line" action.
- `SizeChanged` — file size changed (replaceable).
- `FileError` — error watching a file.
- `PendingLines` — count of new lines not yet shown (replaceable).
- `NewBreaks` — new line-break offsets discovered.
- `DismissOverlay` — request to dismiss current overlay/pointer.
- `TailFile` — set tail state on/off.
- `ScanProgress` — scanning progress update (message + float completion).
- `ScanComplete` — scanning finished (size + scan_start offset).
- `PointerMoved` — pointer line changed (replaceable).

### `help.py` — Help Screen
- **`HelpScreen(ModalScreen)`** — F1 help overlay. Renders a Markdown document with navigation keys and usage instructions. Provides key bindings to open external URLs (author, Textual, repository, LogMerger).

### `highlighter.py` — Log Syntax Highlighter
- **`LogHighlighter(RegexHighlighter)`** — a Rich `RegexHighlighter` that applies `repr.*` styles to: IPv4/IPv6 addresses, EUI-48/EUI-64 MAC addresses, UUIDs, booleans, `None`, numbers, strings (single/double/triple-quoted), and bracket-delimited paths. Skips lines ≥10,000 characters for performance.

## Code Organization Patterns

1. **Textual widget hierarchy** — the app is a tree of Textual widgets communicating via message passing (`post_message` / `@on` decorators). No direct parent references between siblings.
2. **Reactive data binding** — `LogView` uses `.data_bind()` to keep `LogLines`, `LogFooter`, and `InfoOverlay` in sync with its own reactive attributes.
3. **Adaptive format/timestamp detection** — both `FormatParser` and `TimestampScanner` move the most recently matched item to the front of their list, providing O(1) amortized detection for consistent log files.
4. **LRU caches** — multiple levels of caching (`_line_cache`, `_text_cache`, `_render_line_cache`) prevent redundant I/O and re-parsing.
5. **Worker threads** — file scanning (`run_scan`), line reading (`LineReader`), and file saving (`save`) all run on background threads to keep the UI responsive.
6. **Platform branching** — `IS_WINDOWS` flag in `log_file.py` selects between `os.pread` and lseek+read; `get_watcher()` selects the watcher implementation.
