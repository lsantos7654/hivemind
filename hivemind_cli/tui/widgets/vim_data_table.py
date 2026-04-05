"""DataTable with vim-style navigation."""

from __future__ import annotations

import time
from typing import ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import DataTable, SelectionList


class VimSelectionList(SelectionList):
    """SelectionList with vim-style navigation."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "goto_top", "Top", show=False),
        Binding("G", "goto_bottom", "Bottom", show=False),
        Binding("ctrl+d", "half_page_down", "Half Page Down", show=False),
        Binding("ctrl+u", "half_page_up", "Half Page Up", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_g_press: float = 0.0

    def action_goto_top(self) -> None:
        """Go to top on double-g (gg) within 0.5s."""
        now = time.monotonic()
        if now - self._last_g_press < 0.5:
            self.action_first()
            self._last_g_press = 0.0
        else:
            self._last_g_press = now

    def action_goto_bottom(self) -> None:
        """Go to last option (G)."""
        self.action_last()

    def action_half_page_down(self) -> None:
        """Move down half a visible page (ctrl-d)."""
        if self.option_count == 0 or self.highlighted is None:
            return
        half = max(1, self.scrollable_content_region.height // 2)
        self.highlighted = min(self.highlighted + half, self.option_count - 1)

    def action_half_page_up(self) -> None:
        """Move up half a visible page (ctrl-u)."""
        if self.option_count == 0 or self.highlighted is None:
            return
        half = max(1, self.scrollable_content_region.height // 2)
        self.highlighted = max(0, self.highlighted - half)


class VimDataTable(DataTable):
    """DataTable subclass with vim-style key bindings."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("j,ctrl+n", "cursor_down", "Down", show=False),
        Binding("k,ctrl+p", "cursor_up", "Up", show=False),
        Binding("g", "goto_top", "Top", show=False),
        Binding("G", "goto_bottom", "Bottom", show=False),
        Binding("ctrl+d", "half_page_down", "Half Page Down", show=False),
        Binding("ctrl+u", "half_page_up", "Half Page Up", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_g_press: float = 0.0

    def action_goto_top(self) -> None:
        """Go to top on double-g (gg) within 0.5s."""
        now = time.monotonic()
        if now - self._last_g_press < 0.5:
            self.move_cursor(row=0)
            self._last_g_press = 0.0
        else:
            self._last_g_press = now

    def action_goto_bottom(self) -> None:
        """Go to last row (G)."""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1)

    def action_half_page_down(self) -> None:
        """Move down half a visible page (ctrl-d)."""
        if self.row_count == 0:
            return
        half = max(1, self.size.height // 2)
        new_row = min(self.cursor_row + half, self.row_count - 1)
        self.move_cursor(row=new_row)

    def action_half_page_up(self) -> None:
        """Move up half a visible page (ctrl-u)."""
        if self.row_count == 0:
            return
        half = max(1, self.size.height // 2)
        new_row = max(0, self.cursor_row - half)
        self.move_cursor(row=new_row)
