# Rich APIs and Interfaces

## Public API Overview

Rich provides multiple API layers from simple convenience functions to sophisticated low-level rendering control. The library is designed with progressive disclosure—simple tasks are simple, complex tasks are possible.

## Entry Points and Import Patterns

### High-Level Convenience Functions

Import from the top-level `rich` package:

```python
from rich import print, print_json, inspect
from rich.console import Console
```

**`rich.print(*objects, sep=" ", end="\n", file=None, flush=False)`**

Drop-in replacement for built-in `print()` with Rich formatting:

```python
from rich import print

# Markup syntax
print("Hello [bold magenta]World[/bold magenta]!")

# Emoji support
print(":vampire: :thumbs_up: :pile_of_poo:")

# Pretty-print data structures
data = {"name": "Alice", "scores": [95, 87, 92]}
print(data)  # Automatically formatted
```

**`rich.inspect(obj, *, console=None, title=None, help=False, methods=False, ...)`**

Inspect any Python object:

```python
from rich import inspect

my_list = ["foo", "bar"]
inspect(my_list, methods=True)  # Show all methods
inspect(my_list, private=True)  # Include private attributes
inspect(my_list, all=True)      # Show everything
```

**`rich.print_json(json=None, *, data=None, indent=2, highlight=True, ...)`**

Pretty-print JSON:

```python
from rich import print_json

print_json('[{"name": "Alice", "age": 30}]')
# Or from data
print_json(data={"name": "Bob", "active": True})
```

**`rich.get_console() -> Console`**

Get the global Console instance:

```python
from rich import get_console

console = get_console()
console.print("Using global console")
```

## Console Class - Primary API

The `Console` class is the central interface for all Rich functionality.

### Creating a Console

```python
from rich.console import Console

# Basic console
console = Console()

# Customized console
console = Console(
    width=120,           # Override terminal width
    height=40,           # Override terminal height
    color_system="auto", # "auto", "standard", "256", "truecolor", "windows", None
    force_terminal=True, # Force terminal mode even if stdout is redirected
    force_jupyter=False, # Force Jupyter mode
    theme=my_theme,      # Custom theme
    file=sys.stderr,     # Output to stderr instead of stdout
    record=True,         # Record output for export
    markup=True,         # Enable markup parsing
    emoji=True,          # Enable emoji support
    highlight=True,      # Enable automatic highlighting
    log_path=False,      # Disable log path in log() calls
    log_time=True,       # Show time in log() calls
)
```

### Console Output Methods

**`console.print(*objects, sep=" ", end="\n", style=None, justify=None, ...)`**

Enhanced printing:

```python
# Basic output
console.print("Hello, World!")

# With style
console.print("Error!", style="bold red")
console.print("Success", style="green on black")

# With markup
console.print("[bold cyan]Styled[/bold cyan] text")

# Justify
console.print("Centered", justify="center")
console.print("Right aligned", justify="right")

# Multiple objects
console.print("Name:", name, "Age:", age)
```

**`console.log(*objects, _stack_offset=1, log_locals=False, ...)`**

Logging with automatic context:

```python
# Simple logging
console.log("Processing file...")

# With local variables
def process():
    filename = "data.csv"
    count = 100
    console.log("Processing", log_locals=True)  # Shows locals

# Custom formatting
console.log("Status", highlight=False)
```

**`console.rule(title="", characters="─", style="rule.line", align="center")`**

Horizontal rules:

```python
console.rule()                           # Plain rule
console.rule("Section 1")                # With title
console.rule("[bold red]Warning")        # Styled title
console.rule("Left", align="left")       # Left-aligned
```

### Status and Progress

**`console.status(status, spinner="dots", ...)`**

Context manager for spinner status:

```python
with console.status("[bold green]Working...") as status:
    # Long-running operation
    process_data()
    status.update("[bold blue]Almost done...")
    finalize()
```

**Progress tracking** via `rich.progress`:

```python
from rich.progress import Progress, track

# Simple progress
for item in track(sequence, description="Processing..."):
    process(item)

# Advanced progress
with Progress() as progress:
    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=500)

    while not progress.finished:
        progress.update(task1, advance=10)
        progress.update(task2, advance=5)
```

### Input Methods

**`console.input(prompt="", markup=True, password=False, stream=None)`**

Styled input prompts:

```python
name = console.input("Enter your [bold cyan]name[/]: ")
password = console.input("Password: ", password=True)
```

### Export and Recording

**`console.export_html(path=None, theme=None, clear=True, code_format=None)`**

Export console output as HTML:

```python
console = Console(record=True)
console.print("[bold]Hello[/bold] World")
html = console.export_html()
# Or save to file
console.save_html("output.html")
```

**`console.export_svg(path=None, theme=None, clear=True, code_format=None)`**

Export as SVG:

```python
console.save_svg("output.svg", title="Terminal Output")
```

**`console.export_text(clear=True, styles=False)`**

Export as plain text:

```python
text = console.export_text()
console.save_text("output.txt")
```

## Tables

The `Table` class creates formatted tables:

```python
from rich.table import Table
from rich.console import Console

console = Console()

# Create table
table = Table(title="Users", show_header=True, header_style="bold magenta")

# Add columns
table.add_column("ID", style="dim", width=6)
table.add_column("Name", min_width=20)
table.add_column("Status", justify="right")

# Add rows
table.add_row("1", "Alice", "[green]Active")
table.add_row("2", "Bob", "[red]Inactive")

# Display
console.print(table)
```

**Advanced table features**:

```python
# Grid layout (no borders)
table = Table(show_header=False, show_edge=False, pad_edge=False)

# Custom box style
from rich import box
table = Table(box=box.ROUNDED)
table = Table(box=box.DOUBLE)
table = Table(box=box.MINIMAL)

# Row styles (alternating)
table = Table(row_styles=["none", "dim"])

# Nested renderables
table.add_row("Name", Panel("Nested content"))

# Footer
table.add_column("Total", footer="Sum")
table.show_footer = True
```

## Syntax Highlighting

The `Syntax` class provides code highlighting:

```python
from rich.syntax import Syntax
from rich.console import Console

console = Console()

code = '''
def hello(name):
    print(f"Hello, {name}!")
'''

syntax = Syntax(
    code,
    "python",                    # Lexer name
    theme="monokai",            # Pygments theme
    line_numbers=True,          # Show line numbers
    start_line=1,               # Starting line number
    highlight_lines={2, 3},     # Highlight specific lines
    word_wrap=False,            # Enable word wrapping
    code_width=88,              # Max code width
)

console.print(syntax)

# From file
syntax = Syntax.from_path("script.py", line_numbers=True)
```

**Available themes**: Any Pygments theme (monokai, vim, vs, solarized-dark, etc.)

**Available lexers**: Any Pygments lexer (python, javascript, rust, go, etc.)

## Markdown Rendering

The `Markdown` class renders markdown:

```python
from rich.markdown import Markdown
from rich.console import Console

console = Console()

markdown_text = """
# Heading 1

## Heading 2

Regular text with **bold**, *italic*, and `code`.

- List item 1
- List item 2
  - Nested item

```python
def hello():
    print("Code block")
```

[Link text](https://example.com)
"""

md = Markdown(markdown_text)
console.print(md)

# From file
with open("README.md") as f:
    md = Markdown(f.read())
    console.print(md)
```

**Supported markdown features**:
- Headers (H1-H6)
- Bold, italic, inline code
- Code blocks with syntax highlighting
- Lists (ordered, unordered, nested)
- Links
- Block quotes
- Horizontal rules

## Tree Structures

The `Tree` class creates hierarchical displays:

```python
from rich.tree import Tree
from rich.console import Console

console = Console()

# Create tree
tree = Tree("📁 Project", guide_style="bold bright_blue")

# Add branches
python = tree.add("📁 python")
python.add("🐍 main.py")
python.add("🐍 utils.py")

docs = tree.add("📁 docs")
docs.add("📄 README.md")

tree.add("📄 LICENSE")

console.print(tree)
```

**Tree customization**:

```python
tree = Tree(
    label="Root",
    style="bold magenta",       # Tree style
    guide_style="blue",         # Guide line style
    expanded=True,              # Show children
    highlight=True,             # Highlight text
    hide_root=False,            # Hide root node
)
```

## Panels and Layout

**Panels** add borders around content:

```python
from rich.panel import Panel

panel = Panel(
    "Content here",
    title="Title",
    subtitle="Subtitle",
    border_style="blue",
    box=box.ROUNDED,
    padding=(1, 2),             # (top/bottom, left/right)
    expand=False,               # Expand to full width
)

console.print(panel)
```

**Layout** creates complex terminal UIs:

```python
from rich.layout import Layout
from rich.panel import Panel

layout = Layout()

# Split layout
layout.split_column(
    Layout(name="header", size=3),
    Layout(name="body"),
    Layout(name="footer", size=3),
)

# Split body into columns
layout["body"].split_row(
    Layout(name="left"),
    Layout(name="right"),
)

# Populate
layout["header"].update(Panel("Header"))
layout["left"].update(Panel("Left sidebar"))
layout["right"].update(Panel("Main content"))
layout["footer"].update(Panel("Footer"))

console.print(layout)
```

## Progress Bars

Detailed progress tracking:

```python
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TransferSpeedColumn,
)

# Custom progress layout
progress = Progress(
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeRemainingColumn(),
)

with progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        # Do work
        progress.update(task, advance=1)
```

**Track file operations**:

```python
from rich.progress import track

# Simple wrapper
for item in track(items, description="Processing"):
    process(item)
```

## Live Display

The `Live` context manager enables live-updating content:

```python
from rich.live import Live
from rich.table import Table
import time

table = Table()
table.add_column("Name")
table.add_column("Status")

with Live(table, refresh_per_second=4):
    for i in range(10):
        table.add_row(f"Task {i}", "[green]Complete")
        time.sleep(0.5)
```

## Traceback Rendering

Enhanced exception display:

```python
from rich.traceback import install

# Install as default handler
install(show_locals=True)

# Or use explicitly
from rich.console import Console
console = Console()

try:
    risky_operation()
except Exception:
    console.print_exception(show_locals=True)
```

## Theming and Styles

**Custom themes**:

```python
from rich.theme import Theme
from rich.console import Console

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)
console.print("This is info", style="info")
console.print("This is an error", style="error")
```

**Style composition**:

```python
from rich.style import Style

style = Style(
    color="bright_white",
    bgcolor="blue",
    bold=True,
    italic=False,
    underline=True,
    strike=False,
    blink=False,
)

# Combine styles
style = Style(color="red") + Style(bold=True)
```

## Renderable Protocol

Create custom renderables:

```python
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style

class CustomRenderable:
    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions
    ) -> RenderResult:
        # Yield segments
        yield Segment("Custom ", Style(color="red"))
        yield Segment("output", Style(color="blue", bold=True))
        yield Segment.line()

console = Console()
console.print(CustomRenderable())
```

This comprehensive API enables everything from simple colored output to sophisticated terminal applications with live updates, complex layouts, and rich formatting.
