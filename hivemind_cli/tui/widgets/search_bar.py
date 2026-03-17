"""Search bar widget — floating overlay toggled by / key."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Static
from textual.reactive import reactive


class SearchBar(Horizontal):
    """Search input with label, displayed as a floating overlay."""

    query: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static("Search: ", classes="search-label")
        yield Input(placeholder="Type to filter...", id="search-input")

    def show(self) -> None:
        """Show the search overlay and focus input."""
        self.add_class("visible")
        self.query_one("#search-input", Input).focus()

    def hide(self) -> None:
        """Hide the search overlay."""
        self.remove_class("visible")

    @property
    def is_visible(self) -> bool:
        """Check if the overlay is currently shown."""
        return self.has_class("visible")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes — update reactive query."""
        if event.input.id == "search-input":
            self.query = event.value

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key — hide overlay, keep filter active."""
        if event.input.id == "search-input":
            self.hide()

    def clear(self) -> None:
        """Clear the search input and query."""
        self.query_one("#search-input", Input).value = ""
        self.query = ""
