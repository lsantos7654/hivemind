"""Base form modal for CRUD operations."""

from __future__ import annotations

from textual.screen import ModalScreen
from textual.widgets import Button, Input


class FormModal(ModalScreen):
    """Base modal for form-based CRUD operations.

    Subclasses should override compose() to add form fields inside a
    Vertical(classes="modal-body") container, and override _submit()
    to validate and dismiss with data.
    """

    def on_mount(self) -> None:
        self._bindings.bind("escape", "dismiss_modal")
        self._bindings.bind("ctrl+o", "dismiss_modal")
        self._bindings.bind("ctrl+s", "submit_form", description="Confirm")
        self._bindings.bind("h", "prev_button")
        self._bindings.bind("l", "next_button")

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
