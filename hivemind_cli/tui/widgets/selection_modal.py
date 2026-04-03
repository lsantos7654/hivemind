"""Searchable selection list modal for picking from a list of options."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label

from hivemind_cli.tui.widgets.form_modal import FormModal
from hivemind_cli.tui.widgets.search_bar import SearchBar
from hivemind_cli.tui.widgets.vim_data_table import VimSelectionList


class SelectionListModal(FormModal):
    """Modal with a searchable, filterable VimSelectionList.

    Returns list of selected values on confirm, None on cancel.
    """

    AUTO_FOCUS = "#selection-list"

    DEFAULT_CSS = """
    SelectionListModal .modal-body {
        max-height: 80%;
    }

    SelectionListModal #selection-list {
        max-height: 20;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("slash", "focus_search", "Search", show=False),
    ]

    def __init__(self, options: list[tuple[str, str]], title: str = "Select"):
        super().__init__()
        self._title = title
        self._all_options = options

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-body") as v:
            v.border_title = self._title
            yield SearchBar()
            yield VimSelectionList(
                *self._all_options,
                id="selection-list",
            )
            yield Label("", id="error-label", classes="error-label")
            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Confirm", id="confirm", variant="primary")

    def action_focus_search(self) -> None:
        self.query_one(SearchBar).show()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return
        query = event.value.lower()
        sel_list = self.query_one("#selection-list", VimSelectionList)

        # Snapshot current selections before clearing
        saved = set(sel_list.selected)

        sel_list.clear_options()
        for label, value in self._all_options:
            if not query or query in label.lower():
                sel_list.add_option((label, value))

        # Restore selections that still exist in filtered list
        for value in saved:
            sel_list.select(value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            event.stop()
            self.query_one(SearchBar).hide()
            self.query_one("#selection-list", VimSelectionList).focus()

    def _submit(self) -> None:
        sel_list = self.query_one("#selection-list", VimSelectionList)
        selected = list(sel_list.selected)
        self.dismiss(selected or None)
