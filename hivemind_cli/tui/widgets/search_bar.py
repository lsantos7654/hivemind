"""Search bar widget with debouncing."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Static
from textual.reactive import reactive


class SearchBar(Horizontal):
    """Search input with label."""

    query: reactive[str] = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Compose the search bar."""
        yield Static("Search: ", classes="search-label")
        yield Input(placeholder="Type to filter experts...", id="search-input")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "search-input":
            self.query = event.value
            # Update parent's table directly
            try:
                table = self.screen.query_one("#expert-table")
                table.filter_query = self.query
            except Exception:
                pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - return focus to table without clearing search."""
        if event.input.id == "search-input":
            try:
                table = self.screen.query_one("#expert-table")
                table.focus()
            except Exception:
                pass

    def clear(self) -> None:
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.query = ""
