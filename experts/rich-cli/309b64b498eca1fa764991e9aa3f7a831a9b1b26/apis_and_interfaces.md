# Rich-CLI APIs and Interfaces

## Public APIs and Entry Points

Rich-CLI is primarily a command-line application, so its main public interface is the `rich` command. However, it also exposes Python APIs for programmatic use.

### Command-Line Interface

**Primary Entry Point**: The `rich` command

```bash
rich [OPTIONS] <PATH, TEXT, URL, or '-'>
```

**Help Display**:
```bash
rich --help
```

This displays a richly formatted help screen showing all available options.

### Python Entry Points

**Console Script**: Defined in `pyproject.toml`:
```toml
[project.scripts]
rich = "rich_cli.__main__:run"
```

**Python Function Call**:
```python
from rich_cli.__main__ import run

# Programmatic invocation
run()  # Processes sys.argv
```

**Direct Module Execution**:
```bash
python -m rich_cli <args>
```

## Key Classes, Functions, and Interfaces

### Core CLI Function

**`main()` - Primary Command Handler**

```python
@click.command(cls=RichCommand)
@click.argument("resource", metavar="<PATH or TEXT or '-'>", default="")
# ... 50+ option decorators ...
def main(
    resource: str,
    version: bool = False,
    _print: bool = False,
    syntax: bool = False,
    # ... many more parameters ...
):
    """Rich toolbox for console output."""
```

This function is the heart of the application, handling all CLI logic.

**Key Parameters**:
- `resource`: File path, URL, text, or '-' for stdin
- `version`: Print version and exit
- `_print`: Enable console markup printing
- `syntax`: Force syntax highlighting mode
- `json`: Force JSON rendering
- `markdown`/`rst`/`csv`/`ipynb`: Force specific format
- `theme`: Pygments theme name (default: "ansi_dark")
- `line_numbers`/`guides`: Syntax highlighting options
- `pager`: Launch interactive pager
- `export_html`/`export_svg`: Export to file

### Input Reading

**`read_resource(path: str, lexer: Optional[str]) -> Tuple[str, Optional[str]]`**

Unified function for reading content from multiple sources:

```python
# Read from file
text, lexer = read_resource("file.py", None)

# Read from URL
text, lexer = read_resource("https://example.com/file.py", None)

# Read from stdin
text, lexer = read_resource("-", None)
```

**Behavior**:
- File paths: Opens and reads file with UTF-8 encoding
- URLs (http/https): Fetches via requests library, detects MIME type
- Stdin ("-"): Reads from `sys.stdin`
- Auto-detects lexer from file extension or MIME type
- Returns tuple of (content, lexer_name)

**Error Handling**: Calls `on_error()` on failures

### Rendering Functions

**`render_csv()` - CSV Table Renderer**

```python
def render_csv(
    resource: str,
    head: Optional[int] = None,
    tail: Optional[int] = None,
    title: Optional[str] = None,
    caption: Optional[str] = None,
) -> RenderableType:
    """Render resource as CSV."""
```

**Features**:
- Auto-detects CSV dialect (delimiter, quoting)
- Detects if CSV has header row
- Right-aligns numeric columns
- Supports head/tail limiting
- Returns Rich Table renderable

**Usage**:
```python
table = render_csv("data.csv", head=10, title="Data Sample")
console.print(table)
```

**`render_ipynb()` - Jupyter Notebook Renderer**

```python
def render_ipynb(
    resource: str,
    theme: str,
    hyperlinks: bool,
    lexer: str,
    head: Optional[int],
    tail: Optional[int],
    line_numbers: bool,
    guides: bool,
    no_wrap: bool,
) -> RenderableType:
    """Render resource as Jupyter notebook."""
```

**Features**:
- Parses .ipynb JSON format
- Renders code cells with syntax highlighting
- Renders Markdown cells with full formatting
- Displays execution counts (In[n]/Out[n])
- Shows cell outputs including errors and results
- Returns Rich Group renderable

### Custom Renderables

**`ForceWidth` - Width Constraint Renderable**

```python
class ForceWidth:
    """Force a renderable to a given width."""

    def __init__(self, renderable: RenderableType, width: int = 80) -> None:
        self.renderable = renderable
        self.width = width

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        child_options = options.update_width(self.width)
        yield from console.render(self.renderable, child_options)
```

**Usage**:
```python
# Force content to 80 columns
narrow_content = ForceWidth(renderable, width=80)
console.print(narrow_content)
```

**`PagerRenderable` - Pre-rendered Content Wrapper**

```python
class PagerRenderable:
    def __init__(
        self,
        lines: Iterable[List[Segment]],
        new_lines: bool = False,
        width: int = 80
    ) -> None:
        self.lines = list(lines)
        self.new_lines = new_lines
        self.width = width
```

Wraps pre-rendered segment lists for display in the pager.

### Custom Click Components

**`RichCommand` - Enhanced Help Formatter**

```python
class RichCommand(click.Command):
    """Override Clicks help with a Richer version."""

    def format_help(self, ctx, formatter):
        # Custom Rich-formatted help display
        console = Console(theme=Theme({
            "option": "bold cyan",
            "switch": "bold green",
        }))
        # ... renders table of options ...
```

Provides beautifully formatted help output using Rich tables and styling.

### Utility Functions

**`on_error()` - Error Handler**

```python
def on_error(
    message: str,
    error: Optional[Exception] = None,
    code: int = -1
) -> NoReturn:
    """Render an error message then exit the app."""
```

**Usage**:
```python
if not valid_input:
    on_error("Invalid input format")

try:
    data = process_file(path)
except Exception as e:
    on_error(f"Failed to process {path}", e)
```

**`blend_text()` - Gradient Text Generator**

```python
def blend_text(
    message: str,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int]
) -> Text:
    """Blend text from one color to another."""
```

Creates gradient effects for decorative text:

```python
from rich.color import Color

gradient = blend_text(
    "Hello World",
    Color.parse("#ff0000").triplet,
    Color.parse("#0000ff").triplet
)
console.print(gradient)
```

**`_line_range()` - Line Range Calculator**

```python
def _line_range(
    head: Optional[int],
    tail: Optional[int],
    num_lines: int
) -> Optional[Tuple[int, int]]:
    """Calculate line range for head/tail display."""
```

Helper for computing which lines to display when using `--head` or `--tail`.

## Usage Examples with Code Snippets

### Basic Syntax Highlighting

```bash
# Highlight Python file with line numbers and guides
rich mycode.py -n -g

# Use specific theme
rich mycode.py --theme monokai

# Set lexer explicitly
rich data.txt --lexer json
```

### Markdown Rendering

```bash
# Render markdown file (auto-detected from .md extension)
rich README.md

# Enable hyperlinks
rich README.md --hyperlinks

# Explicit markdown mode
rich document.txt --markdown
```

### JSON Pretty-Printing

```bash
# Format JSON file
rich data.json

# Pipe JSON to rich
curl https://api.example.com/data | rich - --json --force-terminal

# From string
echo '{"name":"John","age":30}' | rich - -J
```

### CSV Table Display

```bash
# Display CSV as table
rich data.csv

# Show only first 10 rows
rich data.csv --head 10

# Show last 5 rows
rich data.csv --tail 5

# With title and caption
rich sales.csv --title "Sales Data" --caption "2024 Q1"
```

### Console Markup Printing

```bash
# Print styled text
rich "Hello [bold red]World[/]!" --print

# Multiple styles
rich "Status: [bold green on white]SUCCESS[/]" -p

# With emoji codes
rich "Success :sparkle:" -p --emoji
```

### Layout and Styling

```bash
# Center aligned with padding
rich "Important Message" -p -c -d 2

# Add panel border
rich "Announcement" -p --panel heavy --title "Notice"

# Set width and justify
rich "Long text here..." -p -w 40 --text-full

# Apply background style
rich "Highlighted text" -p --style "on blue"
```

### Interactive Pager

```bash
# View file in pager
rich largefile.py --pager

# Pager with options
rich README.md -m --pager -w 100

# Navigation:
#   j/k: scroll line by line
#   ctrl+d/ctrl+u: half-page scroll
#   space: page down
#   q: quit
```

### Network Resources

```bash
# Fetch and display from URL
rich https://raw.githubusercontent.com/user/repo/main/README.md

# With markdown rendering
rich https://example.com/doc.md --markdown

# Force terminal output when piping
curl https://example.com/code.py | rich - --force-terminal
```

### Export to HTML/SVG

```bash
# Export to HTML
rich mycode.py -o output.html

# Export to SVG
rich data.json --export-svg output.svg

# With custom styling
rich README.md -m --panel rounded --title "Documentation" -o readme.html
```

## Integration Patterns and Workflows

### Shell Script Integration

**Pattern 1: Enhanced cat Replacement**

```bash
#!/bin/bash
# Use rich instead of cat for colorized output
rich "$1" -n  # Show file with line numbers
```

**Pattern 2: Log File Viewer**

```bash
#!/bin/bash
# View logs with syntax highlighting
tail -f app.log | rich - --lexer log --force-terminal
```

**Pattern 3: API Response Formatter**

```bash
#!/bin/bash
# Pretty-print API responses
curl -s https://api.github.com/users/$1 | rich - --json
```

### Python Integration

**Pattern 1: Programmatic Usage**

```python
import sys
from rich_cli.__main__ import read_resource, render_csv
from rich.console import Console

console = Console()

# Read and render CSV
table = render_csv("data.csv", head=5)
console.print(table)
```

**Pattern 2: Custom Wrapper**

```python
import subprocess

def rich_display(content, mode="auto"):
    """Display content using rich-cli."""
    cmd = ["rich", "-"]
    if mode == "json":
        cmd.append("--json")
    elif mode == "markdown":
        cmd.append("--markdown")

    subprocess.run(cmd, input=content, text=True)

# Usage
rich_display('{"status": "ok"}', mode="json")
```

### Build Tool Integration

**Pattern: Add to Makefile**

```makefile
.PHONY: show-readme
show-readme:
	rich README.md --markdown --pager

.PHONY: show-config
show-config:
	rich config.json --json

.PHONY: lint-output
lint-output:
	pylint mypackage | rich - --lexer text
```

## Configuration Options and Extension Points

### Environment Variables

**`RICH_THEME`**: Set default syntax theme

```bash
# Set globally
export RICH_THEME=dracula

# Use in command
rich mycode.py  # Uses dracula theme

# Override
RICH_THEME=monokai rich mycode.py
```

### Extending Markdown Rendering

The `markdown.py` module demonstrates the extension pattern:

```python
from rich.markdown import Markdown, TextElement

class CustomElement(TextElement):
    style_name = "markdown.custom"

    @classmethod
    def create(cls, markdown: Markdown, node: Any) -> "CustomElement":
        # Custom parsing logic
        return cls(node.content)

    def __rich_console__(self, console, options):
        # Custom rendering logic
        yield Text(str(self.text), style="custom")

# Register extension
Markdown.elements["custom_element"] = CustomElement
```

### Custom Renderable Pattern

Any Rich-compatible renderable can be integrated:

```python
from rich.console import Console, RenderableType

class MyCustomRenderable:
    def __rich_console__(self, console, options):
        yield Text("Custom content")

    def __rich_measure__(self, console, options):
        return Measurement(10, 50)

# Use with Rich-CLI's rendering pipeline
console = Console()
console.print(MyCustomRenderable())
```

### Pager Customization

The `PagerApp` can be subclassed for custom keybindings:

```python
from rich_cli.pager import PagerApp

class CustomPager(PagerApp):
    async def on_key(self, event):
        if event.key == "n":
            # Custom navigation
            self.body.scroll_down()
        else:
            await super().on_key(event)

# Use custom pager
CustomPager.run(title="Document", content=renderable)
```

### Windows Terminal Compatibility

The `win_vt.py` module provides a reusable context manager:

```python
from rich_cli.win_vt import enable_windows_virtual_terminal_processing

with enable_windows_virtual_terminal_processing():
    # ANSI codes work on Windows
    print("\033[31mRed text\033[0m")
```

This pattern can be adopted in other Python CLI tools needing Windows support.

### Format Auto-Detection

The CLI's auto-detection logic (lines 498-523 in `__main__.py`) can be adapted:

```python
import os.path

def detect_format(resource: str) -> str:
    """Detect format from file extension."""
    ext = os.path.splitext(resource)[-1].lower()

    format_map = {
        ".md": "markdown",
        ".json": "json",
        ".csv": "csv",
        ".tsv": "csv",
        ".rst": "rst",
        ".ipynb": "ipynb",
    }

    return format_map.get(ext, "syntax")
```

Rich-CLI provides a comprehensive, well-structured API for terminal output formatting, with clear extension points for customization and integration into various workflows.
