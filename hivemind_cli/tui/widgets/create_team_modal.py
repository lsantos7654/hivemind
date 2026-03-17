"""Modal for creating a new team."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label

from hivemind_cli.tui.widgets.form_modal import FormModal
from hivemind_cli.tui.widgets.vim_data_table import VimSelectionList


class CreateTeamModal(FormModal):
    """Form modal for creating a new team.

    Returns dict {"name": str, "description": str, "experts": list[str]} or None.
    """

    AUTO_FOCUS = "#name-input"

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = "Create Team"
            yield Label("Name:")
            yield Input(placeholder="team-name", id="name-input")
            yield Label("Description:")
            yield Input(placeholder="Team description", id="desc-input")
            yield Label("Experts:")
            yield VimSelectionList(
                *[
                    (expert.name, expert.name)
                    for expert in self.app.experts
                ],
                id="expert-list",
            )
            yield Label("", id="error-label", classes="error-label")
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="confirm", variant="primary")

    def _submit(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            self.query_one("#error-label", Label).update("[red]Name is required[/red]")
            return

        desc = self.query_one("#desc-input", Input).value.strip()
        selection_list = self.query_one("#expert-list", VimSelectionList)
        experts = list(selection_list.selected)

        self.dismiss({"name": name, "description": desc, "experts": experts})
