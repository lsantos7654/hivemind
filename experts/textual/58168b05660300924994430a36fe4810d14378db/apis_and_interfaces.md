# Textual APIs and Interfaces

## Public APIs and Entry Points

### Application Entry Point: App Class

The `App` class in `textual.app` is the primary entry point for all Textual applications:

```python
from textual.app import App, ComposeResult
from textual.widgets import Button, Header, Footer

class MyApp(App):
    """A simple Textual application."""

    # Inline CSS styling
    CSS = """
    Screen {
        align: center middle;
    }
    """

    # Keyboard bindings
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield Button("Click Me!", id="start")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        self.exit("Button clicked!")

    def action_toggle_dark(self) -> None:
        """Action to toggle dark mode."""
        self.dark = not self.dark

if __name__ == "__main__":
    app = MyApp()
    result = app.run()  # Blocking call that runs until exit
    print(f"App exited with: {result}")
```

**Key App Methods**:
- `run()`: Start the application (blocking)
- `run_async()`: Async version for integration with other async code
- `compose()`: Return widgets to display (ComposeResult)
- `on_mount()`: Called when app is ready
- `on_ready()`: Called after mount, styles applied
- `exit(return_value)`: Exit application with optional return value
- `push_screen(screen)`: Push new screen onto stack
- `pop_screen()`: Pop current screen
- `install_screen(screen, name)`: Register named screen
- `query(selector)`: Query widgets by CSS selector
- `set_interval(interval, callback)`: Schedule repeating callback
- `set_timer(delay, callback)`: Schedule one-time callback

**App Attributes**:
- `CSS`: Inline CSS stylesheet (class variable)
- `CSS_PATH`: Path to external .tcss file
- `BINDINGS`: List of keyboard bindings
- `dark`: Boolean, toggle dark/light mode
- `title`: Application title (shown in header)
- `sub_title`: Application subtitle

### Widget Base Class

All UI elements inherit from `Widget` in `textual.widget`:

```python
from textual.widget import Widget
from textual.app import ComposeResult
from textual.reactive import reactive

class Counter(Widget):
    """A simple counter widget."""

    # Reactive attributes auto-update UI
    count = reactive(0)

    def compose(self) -> ComposeResult:
        """Define child widgets."""
        yield Button(f"Count: {self.count}")

    def watch_count(self, old_value: int, new_value: int) -> None:
        """Called when count changes."""
        self.query_one(Button).label = f"Count: {new_value}"

    def on_button_pressed(self) -> None:
        """Increment counter on button press."""
        self.count += 1
```

**Core Widget Methods**:
- `compose()`: Return child widgets
- `render()`: Return Rich renderable for widget content
- `on_mount()`: Initialization after widget added to DOM
- `on_show()`: Called when widget becomes visible
- `on_hide()`: Called when widget hidden
- `remove()`: Remove widget from DOM
- `refresh()`: Request re-render
- `focus()`: Give keyboard focus to widget
- `scroll_visible()`: Scroll widget into view
- `mount(*widgets)`: Add child widgets dynamically
- `query(selector)`: Query descendant widgets
- `query_one(selector)`: Query single descendant

**Widget Properties**:
- `styles`: Access CSS styles programmatically
- `id`: Widget identifier (unique within screen)
- `classes`: CSS classes (set of strings)
- `disabled`: Boolean, disable widget interaction
- `display`: Boolean, show/hide widget
- `can_focus`: Boolean, whether widget accepts focus
- `has_focus`: Boolean, whether widget currently focused

### Screen Management

Screens represent distinct views in your application:

```python
from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult

class SettingsScreen(Screen):
    """Settings screen with custom styling."""

    CSS = """
    SettingsScreen {
        background: $surface;
    }
    """

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Settings go here")

# In your App:
class MyApp(App):
    def on_mount(self) -> None:
        self.install_screen(SettingsScreen(), "settings")

    def action_show_settings(self) -> None:
        self.push_screen("settings")
```

**Screen Features**:
- Modal screens: `app.push_screen(ModalScreen())`
- Screen callbacks: `app.push_screen(screen, callback=handle_result)`
- Screen results: Return values from screens
- Screen-specific bindings and styles

### Event System

Events flow through the widget hierarchy with bubbling:

```python
from textual import events, on
from textual.widget import Widget

class MyWidget(Widget):
    # Method naming convention: on_{event_name}
    def on_key(self, event: events.Key) -> None:
        """Handle any key press."""
        if event.key == "enter":
            self.post_message(self.Submitted())

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Handle mouse movement."""
        self.log(f"Mouse at {event.x}, {event.y}")

    def on_click(self, event: events.Click) -> None:
        """Handle mouse click."""
        event.stop()  # Stop event propagation

    # Using @on decorator for specific widgets
    @on(Button.Pressed, "#save")
    def save_button_pressed(self) -> None:
        """Only called for button with id='save'"""
        self.save_data()
```

**Common Events**:
- `Key`: Keyboard input
- `Mouse*`: MouseMove, MouseDown, MouseUp, Click
- `Focus`, `Blur`: Focus changes
- `Mount`, `Unmount`: Widget lifecycle
- `Resize`: Terminal/widget size change
- `Show`, `Hide`: Visibility changes

**Custom Messages**:
```python
from textual.message import Message

class MyWidget(Widget):
    class ItemSelected(Message):
        """Posted when item selected."""
        def __init__(self, item_id: str) -> None:
            self.item_id = item_id
            super().__init__()

    def select_item(self, item_id: str) -> None:
        self.post_message(self.ItemSelected(item_id))

# Handle in parent:
def on_my_widget_item_selected(self, event: MyWidget.ItemSelected) -> None:
    self.log(f"Selected: {event.item_id}")
```

## Key Classes, Functions, and Interfaces

### Reactive System

Reactive attributes enable declarative state management:

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class LoginForm(Widget):
    # Reactive with watchers
    username = reactive("", init=False)
    password = reactive("")

    # Simple reactive without watchers
    attempts = var(0)

    def watch_username(self, old: str, new: str) -> None:
        """Called when username changes."""
        self.validate_username(new)

    def watch_password(self, old: str, new: str) -> None:
        """Called when password changes."""
        if len(new) > 0:
            self.add_class("has-password")

    # Computed reactive properties
    @property
    def is_valid(self) -> bool:
        return len(self.username) > 0 and len(self.password) > 8
```

**Reactive Parameters**:
- `default`: Default value or callable
- `layout`: Trigger layout update on change
- `repaint`: Trigger repaint on change
- `init`: Run watcher on initialization
- `always_update`: Run watcher even if value unchanged

### CSS Styling

Apply styles programmatically or via CSS:

```python
# Programmatic styling
widget.styles.background = "red"
widget.styles.color = "white"
widget.styles.border = ("heavy", "blue")
widget.styles.width = "50%"
widget.styles.height = 10  # Lines

# CSS file (styles.tcss)
"""
MyWidget {
    background: $primary;
    color: $text;
    border: heavy $accent;
    padding: 1 2;
    width: 1fr;
}

MyWidget:hover {
    background: $primary-darken-1;
}

MyWidget.-active {
    border: heavy $success;
}
"""

# Load CSS
class MyApp(App):
    CSS_PATH = "styles.tcss"
```

**Common Style Properties**:
- Layout: `display`, `width`, `height`, `min-width`, `max-height`, `dock`
- Spacing: `padding`, `margin`, `offset`
- Colors: `background`, `color`, `border-color`
- Borders: `border`, `outline`
- Grid: `grid-size-columns`, `grid-size-rows`, `row-span`, `column-span`
- Alignment: `align`, `content-align`, `text-align`
- Scrollbar: `scrollbar-gutter`, `scrollbar-size`, `scrollbar-color`
- Visibility: `opacity`, `visibility`, `display`

### Query System

Query widgets using CSS-like selectors:

```python
from textual.css.query import NoMatches

# Query all buttons
buttons = self.query(Button)
for button in buttons:
    button.disabled = True

# Query by ID
submit_button = self.query_one("#submit", Button)

# Query by class
for item in self.query(".list-item"):
    item.remove_class("selected")

# Query one with error handling
try:
    header = self.query_one(Header)
except NoMatches:
    self.log("No header found")

# Query with filters
visible_buttons = self.query(Button).filter(lambda w: w.display)

# Remove all matching
self.query(".temporary").remove()

# Set attributes on all matches
self.query(Input).set(disabled=True)
```

**Query Methods**:
- `query(selector)`: Query descendants
- `query_one(selector)`: Query single descendant (raises if multiple)
- `filter(predicate)`: Filter query results
- `exclude(selector)`: Exclude matching widgets
- `first()`, `last()`: Get first/last result
- `results()`: Get results as tuple
- `remove()`: Remove all matching widgets
- `set(**kwargs)`: Set attributes on all matches

### Built-in Widgets

Textual provides 40+ production-ready widgets:

```python
from textual.widgets import (
    Button,           # Clickable button
    Input,            # Single-line text input
    TextArea,         # Multi-line text editor with syntax highlighting
    DataTable,        # Tabular data with sorting
    Tree,             # Hierarchical tree view
    DirectoryTree,    # File system browser
    ListView,         # Scrollable list
    OptionList,       # Selectable options
    SelectionList,    # Multi-select list
    Select,           # Dropdown selection
    Label,            # Static text
    Static,           # Static content (any renderable)
    Markdown,         # Markdown rendering
    ProgressBar,      # Progress indicator
    Sparkline,        # Inline charts
    Checkbox,         # Boolean checkbox
    RadioButton,      # Exclusive selection
    RadioSet,         # Radio button group
    Switch,           # Toggle switch
    Tabs,             # Tab navigation
    TabbedContent,    # Tabbed container
    Collapsible,      # Expandable container
    Header,           # App header with title
    Footer,           # App footer with key bindings
)

# Example usage
from textual.widgets import Input, Button, DataTable

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter name...")
        yield Button("Submit", id="submit")
        yield DataTable()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_widget = self.query_one(Input)
        name = input_widget.value
        self.query_one(DataTable).add_row(name)
```

### Worker System

Run background tasks without blocking the UI:

```python
from textual import work
from textual.worker import Worker, WorkerState

class MyApp(App):
    @work(exclusive=True, thread=True)
    async def fetch_data(self) -> dict:
        """Fetch data in background."""
        # Long-running operation
        data = await expensive_operation()
        return data

    def on_mount(self) -> None:
        # Start worker
        worker = self.fetch_data()

    @work
    async def on_button_pressed(self) -> None:
        """Work decorator on event handler."""
        result = await self.fetch_data()
        self.update_ui(result)
```

**Worker Features**:
- `@work(thread=True)`: Run in thread pool (for blocking I/O)
- `@work(exclusive=True)`: Cancel previous worker
- `@work(group="name")`: Group related workers
- Worker state: `WorkerState.PENDING`, `RUNNING`, `SUCCESS`, `ERROR`, `CANCELLED`

### Animation System

Animate widget attributes smoothly:

```python
from textual.widget import Widget

class MyWidget(Widget):
    offset_x = reactive(0.0)

    def move_right(self) -> None:
        # Animate offset_x from current value to 10
        self.animate("offset_x", 10.0, duration=1.0, easing="out_cubic")

    def fade_out(self) -> None:
        # Animate multiple properties
        self.animate("opacity", 0.0, duration=0.5)
        self.set_timer(0.5, self.remove)
```

**Animation Methods**:
- `animate(attribute, value, duration, easing)`: Animate single attribute
- `styles.animate()`: Animate style properties
- Easing functions: `linear`, `in_out_cubic`, `out_elastic`, etc.

## Usage Examples

### Complete Clock Application

```python
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Digits

class ClockApp(App):
    """Display current time."""

    CSS = """
    Screen {
        align: center middle;
    }
    Digits {
        width: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Digits("")

    def on_ready(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%T}")

if __name__ == "__main__":
    ClockApp().run()
```

### DataTable with Sorting

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header

class TableApp(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "Age", "City")
        table.add_row("Alice", 30, "NYC")
        table.add_row("Bob", 25, "LA")
        table.add_row("Charlie", 35, "Chicago")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key
        row_data = self.query_one(DataTable).get_row(row_key)
        self.title = f"Selected: {row_data[0]}"
```

### Form with Validation

```python
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Input, Button, Static
from textual.validation import Length, Function

class FormApp(App):
    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Username:")
            yield Input(
                placeholder="Enter username",
                validators=[Length(minimum=3)],
                id="username"
            )
            yield Static("Email:")
            yield Input(
                placeholder="Enter email",
                validators=[Function(self.is_valid_email)],
                id="email"
            )
            yield Button("Submit", id="submit")

    @staticmethod
    def is_valid_email(value: str) -> bool:
        return "@" in value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        username = self.query_one("#username", Input)
        email = self.query_one("#email", Input)

        if username.is_valid and email.is_valid:
            self.exit({"username": username.value, "email": email.value})
```

## Integration Patterns and Workflows

### Testing Workflow

```python
import pytest
from textual.widgets import Button

@pytest.mark.asyncio
async def test_button_click():
    from my_app import MyApp

    app = MyApp()
    async with app.run_test() as pilot:
        # Wait for app to be ready
        await pilot.pause()

        # Simulate button click
        await pilot.click("#submit")

        # Assert UI state
        assert app.query_one(Static).renderable == "Clicked!"

        # Simulate keyboard input
        await pilot.press("q")  # Quit
```

### Modal Dialog Pattern

```python
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Container

class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog for confirmation."""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    Container {
        background: $surface;
        border: heavy $primary;
        width: 40;
        height: 9;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Are you sure?")
            yield Button("Yes", variant="success", id="yes")
            yield Button("No", variant="error", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

# Use in app:
async def action_delete(self) -> None:
    result = await self.push_screen_wait(ConfirmDialog())
    if result:
        self.delete_item()
```

## Configuration Options and Extension Points

### Custom Widget Development

```python
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text

class CustomGauge(Widget):
    """Custom gauge widget."""

    DEFAULT_CSS = """
    CustomGauge {
        height: 3;
        border: solid $primary;
    }
    """

    value = reactive(0.0)
    maximum = reactive(100.0)

    def render(self) -> Text:
        """Render the gauge."""
        bar_width = int(self.size.width * (self.value / self.maximum))
        bar = "█" * bar_width
        return Text(f"{bar} {self.value:.1f}%")

    def watch_value(self, old: float, new: float) -> None:
        """Refresh when value changes."""
        self.refresh()
```

### Custom CSS Properties

```python
# Define custom CSS property
from textual.css.types import CSSLocation

class MyWidget(Widget):
    class MyProperty(CSSLocation):
        """Custom CSS property."""
        pass
```

### Command Palette Extension

```python
from textual.command import Provider, Hit

class MyCommands(Provider):
    """Custom command provider."""

    async def search(self, query: str) -> Hits:
        """Search for commands matching query."""
        if "save" in query.lower():
            yield Hit(
                score=query.score("save"),
                command="save_file",
                text="Save File",
                help="Save the current file"
            )
```

### Custom Drivers

For specialized environments, implement custom drivers:

```python
from textual.drivers.driver import Driver

class CustomDriver(Driver):
    """Custom driver for special terminal."""
    # Implement required methods
```

Textual's comprehensive API enables building sophisticated terminal applications with minimal code while maintaining flexibility for advanced use cases.
