"""Base pane widget with shared search, escape, and filter logic."""

from __future__ import annotations

from textual.widget import Widget

from hivemind_cli.tui.widgets.search_mixin import SearchMixin
from hivemind_cli.tui.widgets.vim_data_table import VimDataTable


class BasePane(SearchMixin, Widget, can_focus=False):
    """Base class for all tabbed panes with shared search/escape/filter behavior."""

    BINDINGS = [*SearchMixin.SEARCH_BINDINGS]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_search()

    def _get_table_id(self) -> str:
        """Return the CSS id of this pane's table. Override in subclass."""
        raise NotImplementedError

    def _get_table(self) -> VimDataTable:
        """Get this pane's data table."""
        return self.query_one(f"#{self._get_table_id()}", VimDataTable)
