"""Search/filter/escape mixin for panes and screens."""

from __future__ import annotations

import time

from textual.binding import Binding
from textual.widgets import Static

from hivemind_cli.tui.widgets.search_bar import SearchBar
from hivemind_cli.tui.widgets.vim_data_table import VimDataTable


class SearchMixin:
    """Mixin providing search, filter, and progressive escape behavior.

    Concrete classes must:
    - Yield SearchBar() and Static("", classes="filter-indicator") in compose()
    - Implement _get_table() -> VimDataTable
    - Implement _populate_table()
    - Implement _get_total_count() -> int
    - Optionally override _on_all_clear()
    """

    SEARCH_BINDINGS = [
        Binding("slash", "focus_search", "Search", show=True),
        Binding("escape", "handle_escape", "Back/Clear", show=True),
        Binding("ctrl+c", "handle_escape", "Back/Clear", show=False),
    ]

    def _init_search(self) -> None:
        """Call from __init__ to initialize search state."""
        self._filter_query: str = ""
        self._visible_names: list[str] = []
        self._last_escape_press: float = 0.0

    def _get_table(self) -> VimDataTable:
        raise NotImplementedError

    def _populate_table(self) -> None:
        raise NotImplementedError

    def _get_total_count(self) -> int:
        return 0

    def _on_all_clear(self) -> None:
        """Double-press escape to exit. Override for extra clear steps."""
        now = time.monotonic()
        if now - self._last_escape_press < 0.5:
            self.app.exit()
        else:
            self._last_escape_press = now

    def get_current_name(self) -> str | None:
        """Get the name at the current cursor position."""
        table = self._get_table()
        if not table.row_count or not self._visible_names:
            return None
        row_idx = table.cursor_row
        if row_idx >= len(self._visible_names):
            return None
        return self._visible_names[row_idx]

    def _update_filter_indicator(self) -> None:
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

    def action_focus_search(self) -> None:
        self.query_one(SearchBar).show()

    def on_input_changed(self, event) -> None:
        if event.input.id == "search-input":
            self._filter_query = event.value
            self._populate_table()
            self._update_filter_indicator()

    def on_input_submitted(self, event) -> None:
        if event.input.id == "search-input":
            self.query_one(SearchBar).hide()
            self._get_table().focus()

    def action_handle_escape(self) -> None:
        search_bar = self.query_one(SearchBar)
        search_input = self.query_one("#search-input")
        table = self._get_table()

        if search_input.has_focus or search_bar.is_shown:
            search_bar.hide()
            table.focus()
            return

        if self._filter_query:
            search_bar.clear()
            self._filter_query = ""
            self._populate_table()
            self._update_filter_indicator()
            table.focus()
            return

        self._on_all_clear()
