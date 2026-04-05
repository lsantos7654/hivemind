"""Button navigation mixin for modal dialogs."""

from __future__ import annotations


class ButtonNavigationMixin:
    """Mixin providing h/l button navigation in modals."""

    def action_prev_button(self) -> None:
        """Move focus to previous button (h)."""
        from textual.widgets import Button

        if isinstance(self.focused, Button):
            self.focus_previous("Button")

    def action_next_button(self) -> None:
        """Move focus to next button (l)."""
        from textual.widgets import Button

        if isinstance(self.focused, Button):
            self.focus_next("Button")
