"""Base pane widget with shared search, escape, and filter logic."""

from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Static

from hivemind_cli.tui.widgets.search_bar import SearchBar
from hivemind_cli.tui.widgets.vim_data_table import VimDataTable


class BasePane(Widget, can_focus=False):
    """Base class for all tabbed panes with shared search/escape/filter behavior."""

    BINDINGS = [
        Binding("slash", "focus_search", "Search", show=True),
        Binding("escape", "handle_escape", "Back/Clear", show=True),
        Binding("ctrl+c", "handle_escape", "Back/Clear", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._filter_query: str = ""
        self._visible_names: list[str] = []
        self._last_escape_press: float = 0.0

    def _get_table_id(self) -> str:
        """Return the CSS id of this pane's table. Override in subclass."""
        raise NotImplementedError

    def _get_table(self) -> VimDataTable:
        """Get this pane's data table."""
        return self.query_one(f"#{self._get_table_id()}", VimDataTable)

    def _populate_table(self) -> None:
        """Populate the table with data. Override in subclass."""
        raise NotImplementedError

    def _get_total_count(self) -> int:
        """Return total item count before filtering. Override in subclass."""
        return 0

    def _on_all_clear(self) -> None:
        """Double-press escape/ctrl+c to exit. Override for extra clear steps."""
        now = time.monotonic()
        if now - self._last_escape_press < 0.5:
            self.app.exit()
        else:
            self._last_escape_press = now

    def get_current_name(self) -> str | None:
        """Get the name of the item at the current cursor position."""
        table = self._get_table()
        if not table.row_count or not self._visible_names:
            return None
        row_idx = table.cursor_row
        if row_idx >= len(self._visible_names):
            return None
        return self._visible_names[row_idx]

    # --- Filter indicator ---

    def _update_filter_indicator(self) -> None:
        """Update the filter indicator label."""
        try:
            indicator = self.query_one(".filter-indicator", Static)
        except Exception:
            return

        if self._filter_query:
            total = self._get_total_count()
            visible = len(self._visible_names)
            indicator.update(
                f"[dim]/[/dim] {self._filter_query}  "
                f"[dim italic]({visible} of {total})[/dim italic]"
            )
            indicator.display = True
        else:
            indicator.display = False

    # --- Search / filter ---

    def action_focus_search(self) -> None:
        """Show and focus the search overlay."""
        self.query_one(SearchBar).show()

    def on_input_changed(self, event) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self._filter_query = event.value
            self._populate_table()
            self._update_filter_indicator()

    def on_input_submitted(self, event) -> None:
        """Handle Enter in search — hide overlay and focus table."""
        if event.input.id == "search-input":
            self.query_one(SearchBar).hide()
            self._get_table().focus()

    # --- Escape handling ---

    def action_handle_escape(self) -> None:
        """Progressive escape: hide search → clear filter → subclass hook."""
        search_bar = self.query_one(SearchBar)
        search_input = self.query_one("#search-input")
        table = self._get_table()

        # Stage 1: If search overlay is visible, hide it
        if search_input.has_focus or search_bar.is_visible:
            search_bar.hide()
            table.focus()
            return

        # Stage 2: If filter is active, clear it
        if self._filter_query:
            search_bar.clear()
            self._filter_query = ""
            self._populate_table()
            self._update_filter_indicator()
            table.focus()
            return

        # Stage 3: Subclass-specific behavior
        self._on_all_clear()
