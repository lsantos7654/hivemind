"""Modal for choosing update mode: full analysis or pull-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from hivemind.tui.widgets.button_nav_mixin import ButtonNavigationMixin

if TYPE_CHECKING:
    from textual.app import ComposeResult


class UpdateModeModal(ButtonNavigationMixin, ModalScreen[bool | None]):
    """Modal to choose between full update (with AI analysis) and pull-only.

    Dismisses with:
      False  -> skip_analysis=False (full update, default)
      True   -> skip_analysis=True  (pull only)
      None   -> cancelled
    """

    SCOPED_CSS = False
    CSS = """
    UpdateModeModal .modal-body {
        width: 56;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("u", "full_update", description="Full Update"),
        Binding("p", "pull_only", description="Pull Only"),
        Binding("escape", "dismiss_modal", description="Cancel"),
        Binding("ctrl+o", "dismiss_modal", description="Back"),
        Binding("h", "prev_button"),
        Binding("l", "next_button"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = "Update Mode"
            yield Label(
                "[b]u[/b] Update — fetch + AI analysis\n[b]p[/b] Pull Only — fetch, skip analysis",
                classes="modal-message",
            )
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel", variant="default")
                yield Button("Pull Only", id="pull-only", variant="default")
                yield Button("Update", id="update", variant="primary")

    def on_mount(self) -> None:
        # Focus the primary "Update" button by default
        self.query_one("#update", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "update":
            self.dismiss(False)
        elif event.button.id == "pull-only":
            self.dismiss(True)
        else:
            self.dismiss(None)

    def action_full_update(self) -> None:
        self.dismiss(False)

    def action_pull_only(self) -> None:
        self.dismiss(True)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)
