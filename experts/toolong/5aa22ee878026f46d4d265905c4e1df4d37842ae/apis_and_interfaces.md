# Toolong — APIs and Interfaces

## Public Entry Points

### CLI: `tl` command (`src/toolong/cli.py`)

```python
@click.command()
@click.version_option(version("toolong"))
@click.argument("files", metavar="FILE1 FILE2", nargs=-1)
@click.option("-m", "--merge", is_flag=True, help="Merge files.")
@click.option("-o", "--output-merge", metavar="PATH", nargs=1,
              help="Path to save merged file (requires -m).")
def run(files: list[str], merge: bool, output_merge: str) -> None:
```

**Usage examples:**
```bash
tl myapp.log                          # View single file
tl access.log error.log               # View multiple files in tabs
tl access.log.* --merge               # Merge files chronologically
tl access.log.* --merge -o merged.log # Merge and save output
echo "data" | tl                      # Pipe data in
tree / | tl                           # Pipe arbitrary command output
tl --version                          # Print version
```

When stdin is not a TTY, `cli.py` handles piping by writing stdin to a `NamedTemporaryFile` and launching a subprocess (`tl <tmpfile>`) with `/dev/tty` as stdin for the UI.

### Python module: `python -m toolong`

The `__main__.py` makes the package runnable as:
```bash
python -m toolong myfile.log
```

---

## Core Classes and Functions

### `UI(App)` — `src/toolong/ui.py:105`

The top-level Textual application class.

```python
class UI(App):
    def __init__(
        self,
        file_paths: list[str],
        merge: bool = False,
        save_merge: str | None = None,
    ) -> None: ...

    @classmethod
    def sort_paths(cls, paths: list[str]) -> list[str]: ...
```

**Key attributes:**
- `file_paths: list[str]` — sorted file paths (natural sort via `CompareTokens`)
- `merge: bool` — whether to merge files into a single view
- `save_merge: str | None` — path to save merged output
- `watcher: WatcherBase` — the platform-appropriate file watcher

**Usage:**
```python
from toolong.ui import UI

ui = UI(["access.log", "error.log"], merge=True, save_merge="merged.log")
ui.run()
```

---

### `LogFile` — `src/toolong/log_file.py:27`

Abstracts a single log file with mmap-based scanning.

```python
@rich.repr.auto(angular=True)
class LogFile:
    def __init__(self, path: str) -> None: ...

    @property
    def is_open(self) -> bool: ...

    @property
    def is_compressed(self) -> bool: ...

    def open(self, exit_event: Event) -> bool: ...
    def close(self) -> None: ...

    def get_raw(self, start: int, end: int) -> bytes: ...
    def get_line(self, start: int, end: int) -> str: ...

    def scan_line_breaks(
        self, batch_time: float = 0.25
    ) -> Iterable[tuple[int, list[int]]]: ...

    def scan_timestamps(
        self, batch_time: float = 0.25
    ) -> Iterable[list[tuple[int, int, float]]]: ...

    def parse(self, line: str) -> ParseResult: ...
```

**Key details:**
- `open()` detects gzip/bzip2 via `mimetypes.guess_type` and decompresses to a `TemporaryFile`. Returns `False` if cancelled via `exit_event`.
- `get_raw(start, end)` uses `os.pread` on POSIX for thread-safe access without seeking.
- `scan_line_breaks()` yields `(position, [offsets])` batches scanning backwards from EOF. Used during initial file scan.
- `scan_timestamps()` yields `[(line_no, position, timestamp_float), ...]` batches. Used during merge mode.

---

### `FormatParser` — `src/toolong/format_parser.py:116`

Detects log line format and parses a line into a `(datetime|None, str, Text)` tuple.

```python
class FormatParser:
    def __init__(self) -> None: ...

    def parse(self, line: str) -> ParseResult: ...
    # ParseResult = tuple[Optional[datetime], str, Text]
```

The parser tries formats in priority order. On a match, the matched format is moved to the front (adaptive optimization). Lines longer than 10,000 characters are truncated before parsing.

**Built-in formats (tried in order):**
1. `JSONLogFormat` — valid JSON lines
2. `CommonLogFormat` — NCSA Common Log Format
3. `CombinedLogFormat` — Apache Combined Log Format
4. `DefaultLogFormat` — fallback with generic highlighting

**ParseResult type:**
```python
ParseResult = tuple[Optional[datetime], str, Text]
# (timestamp_or_None, original_line_string, rich_Text_with_highlights)
```

---

### `TimestampScanner` — `src/toolong/timestamps.py:111`

Scans a log line for a timestamp using 17 pre-defined patterns.

```python
class TimestampScanner:
    def __init__(self) -> None: ...

    def scan(self, line: str) -> datetime | None: ...
```

Uses adaptive reordering: the most recently matched format is tried first. Lines > 10,000 chars are truncated.

**Module-level `parse()` function:**
```python
def parse(line: str) -> tuple[TimestampFormat | None, datetime | None]: ...
```

**Supported timestamp formats:**
- ISO 8601: `YYYY-MM-DD HH:MM:SS[.mmm][±HHMM]` and `YYYY-MM-DDTHH:MM:SS[.mmm][±HHMM]`
- Syslog: `Jan  1 12:34:56`
- Apache CLF: `29/Jan/2024:13:48:00 +0000`
- Unix epoch float: `1706535600.123` (10-digit)
- Unix epoch milliseconds: `1706535600123` (13-digit)

---

### `LogLines(ScrollView)` — `src/toolong/log_lines.py:130`

The core log rendering widget. Manages the virtual scroll model, line caches, scanning, and search.

```python
class LogLines(ScrollView, inherit_bindings=False):
    show_find: reactive[bool]
    find: reactive[str]
    case_sensitive: reactive[bool]
    regex: reactive[bool]
    show_gutter: reactive[bool]
    pointer_line: reactive[int | None]
    tail: reactive[bool]
    can_tail: reactive[bool]
    show_line_numbers: reactive[bool]

    def __init__(self, watcher: WatcherBase, file_paths: list[str]) -> None: ...

    @property
    def line_count(self) -> int: ...

    def get_text(
        self,
        line_index: int,
        abbreviate: bool = False,
        block: bool = False,
        max_line_length: int = MAX_LINE_LENGTH,
    ) -> tuple[str, Text, datetime | None]: ...

    def get_timestamp(self, line_index: int) -> datetime | None: ...
    def advance_search(self, direction: int = 1) -> None: ...
    def scroll_pointer_to_center(self, animate: bool = True) -> None: ...
```

**Key bindings (inherited by the widget):**
| Key | Action |
|-----|--------|
| `up/w/k` | Scroll up (or advance search pointer) |
| `down/s/j` | Scroll down (or advance search pointer) |
| `left/h` | Scroll left |
| `right/l` | Scroll right |
| `home/G` | Scroll to start |
| `end/g` | Scroll to end (enables tail if already at end) |
| `pageup/b` | Page up |
| `pagedown/space` | Page down |
| `enter` | Select line (toggle pointer mode) |
| `escape` | Dismiss overlay / cancel scan |
| `m/M` | Navigate ±1 minute by timestamp |
| `o/O` | Navigate ±1 hour by timestamp |
| `d/D` | Navigate ±1 day by timestamp |

---

### `LogView(Horizontal)` — `src/toolong/log_view.py:256`

Container widget that assembles the complete log-viewing experience.

```python
class LogView(Horizontal):
    show_find: reactive[bool]
    show_panel: reactive[bool]
    show_line_numbers: reactive[bool]
    tail: reactive[bool]
    can_tail: reactive[bool]

    def __init__(
        self,
        file_paths: list[str],
        watcher: WatcherBase,
        can_tail: bool = True,
    ) -> None: ...
```

**Key bindings:**
| Key | Action |
|-----|--------|
| `Ctrl+T` | Toggle tail mode |
| `Ctrl+L` | Toggle line numbers |
| `Ctrl+F` or `/` | Show find dialog |
| `Ctrl+G` | Go to line number |

---

### `WatcherBase` — `src/toolong/watcher.py:39`

Abstract base class for file watchers.

```python
class WatcherBase(ABC):
    def add(
        self,
        log_file: LogFile,
        callback: Callable[[int, list[int]], None],
        error_callback: Callable[[Exception], None],
    ) -> None: ...

    def start(self) -> None: ...
    def close(self) -> None: ...

    @classmethod
    def scan_chunk(cls, chunk: bytes, position: int) -> list[int]: ...

    @abstractmethod
    def run(self) -> None: ...
```

**`get_watcher()` factory function:**
```python
def get_watcher() -> WatcherBase:
    """Return a Watcher appropriate for the OS."""
    # Darwin → SelectorWatcher
    # Other  → PollWatcher
```

The `callback` signature is `(new_size: int, new_line_breaks: list[int]) -> None`.

---

### `FindDialog(Widget)` — `src/toolong/find_dialog.py:25`

Docked search dialog widget.

```python
class FindDialog(Widget, can_focus_children=True):
    def __init__(self, suggester: Suggester) -> None: ...
    def focus_input(self) -> None: ...
    def get_value(self) -> str: ...

    class Update(Message):
        find: str
        regex: bool
        case_sensitive: bool

    class Dismiss(Message): pass
    class MovePointer(Message):
        direction: int  # +1 or -1
    class SelectLine(Message): pass
```

---

### `LinePanel(ScrollableContainer)` — `src/toolong/line_panel.py:57`

Detail panel for the currently selected line.

```python
class LinePanel(ScrollableContainer):
    async def update(
        self,
        line: str,
        text: Text,
        timestamp: datetime | None,
    ) -> None: ...
```

Renders `JSON.from_data()` for valid JSON lines; otherwise renders the syntax-highlighted `Text`. Handles escaped `\n` sequences in the line.

---

### `GotoScreen(ModalScreen)` — `src/toolong/goto_screen.py:15`

Modal dialog for jumping to a specific line number.

```python
class GotoScreen(ModalScreen):
    def __init__(self, log_lines: LogLines) -> None: ...
```

Displays a numeric input pre-filled with the current pointer/scroll position. Updates `log_lines.pointer_line` reactively as the user types.

---

## Internal Message Bus

All widget-to-widget communication is done via Textual messages (`src/toolong/messages.py`). These are not public API but are important for understanding event flow:

| Message | Direction | Purpose |
|---------|-----------|---------|
| `NewBreaks(log_file, breaks, scanned_size, tail)` | LogLines → LogLines | New line-break offsets discovered during scan or tail |
| `ScanProgress(message, complete, scan_start)` | LogLines → LogView | Scan progress percentage and message |
| `ScanComplete(size, scan_start)` | LogLines → LogView | Initial scan finished |
| `TailFile(tail=True)` | Various → LogView | Enable/disable tail mode |
| `PointerMoved(pointer_line)` | LogLines → LogView | Pointer line changed |
| `PendingLines(count)` | LogLines → LogView | New lines arrived while not tailing |
| `FileError(error)` | Watcher callback → LogLines | Error watching file |
| `DismissOverlay()` | LogLines → LogView | Request to close overlays/pointer |
| `Goto()` | MetaLabel → LogView | Trigger go-to line dialog |

---

## Configuration and Extension Points

### Adding a New Log Format

To add a custom log format, create a subclass of `LogFormat` or `RegexLogFormat` in `format_parser.py` and add an instance to the `FORMATS` list:

```python
class MyCustomFormat(RegexLogFormat):
    REGEX = re.compile(
        r'(?P<date>\d{4}-\d{2}-\d{2}) (?P<level>INFO|WARN|ERROR) (?P<message>.*)'
    )

FORMATS = [
    JSONLogFormat(),
    MyCustomFormat(),     # Add here
    CommonLogFormat(),
    CombinedLogFormat(),
]
```

### Adding Timestamp Formats

Add a `TimestampFormat` entry to `TIMESTAMP_FORMATS` in `timestamps.py`:

```python
TIMESTAMP_FORMATS = [
    ...
    TimestampFormat(
        r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}",
        parse_timestamp("%Y/%m/%d %H:%M:%S"),
    ),
]
```

### Adding Syntax Highlighting Patterns

Extend `LogHighlighter.highlights` in `highlighter.py` with additional regex patterns. Patterns use Rich's `repr.*` style namespace:

```python
class LogHighlighter(RegexHighlighter):
    highlights = [
        _combine_regex(
            r"(?P<ipv4>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
            r"(?P<my_custom>MY_PATTERN)",  # Add here
            ...
        ),
    ]
```

### CSS Customization

All Textual widgets define `DEFAULT_CSS` or `CSS` class attributes. These can be overridden by placing a CSS file in the app's CSS path. Key component classes:

- `LogLines` — `.loglines--filter-highlight`, `.loglines--pointer-highlight`, `.loglines--line-numbers`, `.loglines--line-numbers-active`
- `LogLines.-scanning` — tint applied during initial scan
- `LogLines.-tail` — active when tailing
- `LogView.show-panel` — shows the `LinePanel`
- `InfoOverlay` — the pending-lines notification
- `LogFooter .tail.on` — the TAIL indicator when active

### Key Bindings

Bindings are defined in `BINDINGS` class attributes on `LogLines`, `LogView`, `LogScreen`, `FindDialog`, `HelpScreen`, and `GotoScreen`. They follow Textual's binding priority system.

---

## Integration Patterns

### Embedding the UI in Another Application

```python
from toolong.ui import UI

app = UI(
    file_paths=["/var/log/nginx/access.log"],
    merge=False,
    save_merge=None,
)
app.run()
```

### Using LogFile for File Scanning

```python
from threading import Event
from toolong.log_file import LogFile

log = LogFile("/var/log/app.log")
exit_event = Event()
log.open(exit_event)

# Scan line breaks
for position, breaks in log.scan_line_breaks():
    print(f"Found {len(breaks)} line breaks near position {position}")

# Read a specific line
line = log.get_line(start=0, end=breaks[0])
print(line)

log.close()
```

### Using TimestampScanner Standalone

```python
from toolong.timestamps import TimestampScanner, parse

scanner = TimestampScanner()

# Scan individual lines
ts = scanner.scan("2024-01-29 13:48:00 INFO Server started")
print(ts)  # datetime(2024, 1, 29, 13, 48, 0)

# One-off parse
fmt, ts = parse("121.0.0.1 - - [29/Jan/2024:13:45:19 +0000] ...")
print(ts)
```

### Using FormatParser Standalone

```python
from toolong.format_parser import FormatParser

parser = FormatParser()

# Parse a log line
timestamp, line_str, rich_text = parser.parse(
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
)
print(timestamp)    # datetime object or None
print(line_str)     # original line string
print(rich_text)    # Rich Text with syntax highlighting applied
```
