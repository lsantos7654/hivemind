"""Reusable confirmation modal dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmationModal(ModalScreen[bool]):
    """Modal dialog for confirming destructive actions.

    CSS is in styles.tcss under ConfirmationModal.
    """

    def __init__(
        self,
        message: str,
        title: str = "Confirm",
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ):
        super().__init__()
        self._message = message
        self._title = title
        self._confirm_label = confirm_label
        self._cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = self._title
            yield Label(self._message, classes="modal-message")
            with Horizontal(classes="modal-buttons"):
                yield Button(self._cancel_label, id="cancel", variant="default")
                yield Button(self._confirm_label, id="confirm", variant="error")

    def on_mount(self) -> None:
        """Bind y/n/escape for keyboard confirmation."""
        self._bindings.bind("y", "confirm", description="Yes")
        self._bindings.bind("n", "dismiss_modal", description="No")
        self._bindings.bind("ctrl+s", "confirm", description="Confirm")
        self._bindings.bind("escape", "dismiss_modal", description="Cancel")
        self._bindings.bind("ctrl+o", "dismiss_modal", description="Back")
        self._bindings.bind("h", "prev_button")
        self._bindings.bind("l", "next_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_dismiss_modal(self) -> None:
        self.dismiss(False)

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
