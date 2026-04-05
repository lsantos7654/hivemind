"""Modal dialog for adding an expert by Git URL."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label

from hivemind_cli.tui.widgets.form_modal import FormModal

if TYPE_CHECKING:
    from textual.app import ComposeResult


class AddExpertModal(FormModal):
    """Form modal that accepts a Git URL and returns it on confirm."""

    AUTO_FOCUS = "#url-input"

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = "Add Expert"
            yield Label("Git URL:")
            yield Input(
                placeholder="https://github.com/org/repo",
                id="url-input",
            )
            yield Label("", id="error-label", classes="error-label")
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Add", id="confirm", variant="primary")

    def _submit(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        error_label = self.query_one("#error-label", Label)

        if not url:
            error_label.update("URL is required")
            error_label.styles.display = "block"
            return

        if not url.startswith("http"):
            error_label.update("URL must start with http:// or https://")
            error_label.styles.display = "block"
            return

        self.dismiss(url)
