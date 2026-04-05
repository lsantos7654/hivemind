"""Base form modal for CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.screen import ModalScreen

from hivemind.tui.widgets.button_nav_mixin import ButtonNavigationMixin

if TYPE_CHECKING:
    from textual.widgets import Button, Input


class FormModal(ButtonNavigationMixin, ModalScreen):
    """Base modal for form-based CRUD operations.

    Subclasses should override compose() to add form fields inside a
    Vertical(classes="modal-body") container, and override _submit()
    to validate and dismiss with data.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss_modal"),
        Binding("ctrl+o", "dismiss_modal"),
        Binding("ctrl+s", "submit_form", description="Confirm"),
        Binding("h", "prev_button"),
        Binding("l", "next_button"),
    ]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allow Enter to submit from any Input except search."""
        if event.input.id == "search-input":
            return
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self._submit()
        elif event.button.id == "cancel":
            self.dismiss(None)

    def _submit(self) -> None:
        """Validate and dismiss with data. Override in subclass."""
        raise NotImplementedError

    def action_submit_form(self) -> None:
        """Submit the form (ctrl+s)."""
        self._submit()

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)
