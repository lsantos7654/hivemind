"""Reusable confirmation modal dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from hivemind_cli.tui.widgets.button_nav_mixin import ButtonNavigationMixin

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ConfirmationModal(ButtonNavigationMixin, ModalScreen[bool]):
    """Modal dialog for confirming destructive actions.

    CSS is in styles.tcss under ConfirmationModal.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("y", "confirm", description="Yes"),
        Binding("n", "dismiss_modal", description="No"),
        Binding("ctrl+s", "confirm", description="Confirm"),
        Binding("escape", "dismiss_modal", description="Cancel"),
        Binding("ctrl+o", "dismiss_modal", description="Back"),
        Binding("h", "prev_button"),
        Binding("l", "next_button"),
    ]

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_dismiss_modal(self) -> None:
        self.dismiss(False)
