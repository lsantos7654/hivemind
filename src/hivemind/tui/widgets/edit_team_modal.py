"""Modal for editing a team's name and description."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label

from hivemind.tui.widgets.form_modal import FormModal

if TYPE_CHECKING:
    from textual.app import ComposeResult


class EditTeamModal(FormModal):
    """Form modal for editing a team.

    Returns dict {"name": str, "description": str} or None.
    """

    AUTO_FOCUS = "#name-input"

    def __init__(self, name: str, description: str):
        super().__init__()
        self._name = name
        self._description = description

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = "Edit Team"
            yield Label("Name:")
            yield Input(value=self._name, id="name-input")
            yield Label("Description:")
            yield Input(value=self._description, id="desc-input")
            yield Label("", id="error-label", classes="error-label")
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="confirm", variant="primary")

    def _submit(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            self.query_one("#error-label", Label).update("[red]Name is required[/red]")
            self.query_one("#error-label", Label).styles.display = "block"
            return

        desc = self.query_one("#desc-input", Input).value.strip()
        self.dismiss({"name": name, "description": desc})
