"""Screen for viewing and switching expert versions."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Input, Static

from hivemind_cli.config import EXPERTS_DIR, PRIVATE_EXPERTS_DIR
from hivemind_cli.experts import commit_exists_in_repo, get_git_versions
from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import SearchBar, VimDataTable

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from hivemind_cli.tui.models import ExpertRow, VersionInfo


class VersionDetailScreen(BaseScreen):
    """Screen for viewing and switching expert versions."""

    BINDINGS: ClassVar[list[BindingType]] = [
        *BaseScreen.BINDINGS,
        Binding("slash", "focus_search", "Search", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
        Binding("i", "input_commit", "Input Commit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    filter_query: reactive[str] = reactive("", init=False)

    def __init__(self, expert: ExpertRow, **kwargs):
        super().__init__(**kwargs)
        self.expert = expert
        self.versions: list[VersionInfo] = []
        self._filtered_versions: list[VersionInfo] = []
        self._input_visible = False

    def _format_header(self) -> str:
        head = self.expert.commit[:12] if self.expert.commit else "none"
        remote = self.expert.remote
        if len(remote) > 50:
            remote = remote[:47] + "..."
        return f"[bold]{self.expert.name}[/bold]  HEAD: {head}  Remote: {remote}"

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), id="expert-header")
        yield SearchBar()
        yield VimDataTable(id="version-table", zebra_stripes=True)
        yield Container(
            Static("Commit hash:", classes="input-label"),
            Input(placeholder="Enter full commit hash (40 chars)", id="commit-input"),
            Button("Analyze", id="analyze-button", variant="primary"),
            id="commit-input-container",
            classes="hidden",
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#version-table", VimDataTable)
        table.add_columns("Status", "Type", "Commit", "Date", "Name/Message")
        table.cursor_type = "row"

        self._load_versions()
        self._populate_table()

        table.focus()

    def _load_versions(self) -> None:
        expert_dir = (
            PRIVATE_EXPERTS_DIR / self.expert.name if self.expert.is_private else EXPERTS_DIR / self.expert.name
        )
        self.versions = get_git_versions(self.expert.name, expert_dir)

    def _populate_table(self) -> None:
        table = self.query_one("#version-table", VimDataTable)
        table.clear()

        filtered_versions = self.versions
        if self.filter_query:
            query = self.filter_query.lower()
            filtered_versions = [v for v in self.versions if query in v.name.lower() or query in v.commit.lower()]

        self._filtered_versions = filtered_versions

        if not filtered_versions:
            if self.filter_query:
                table.add_row(f'[dim]No results for "{self.filter_query}"[/dim]', "", "", "", "")
            else:
                table.add_row("[dim]No versions found[/dim]", "", "", "", "")
            return

        for version in filtered_versions:
            if version.is_active:
                status = "[green]● active[/green]"
            elif version.analyzed:
                status = "[cyan]✓ analyzed[/cyan]"
            else:
                status = "[dim]○ available[/dim]"

            type_str = "[bold]TAG[/bold]" if version.type == "tag" else "commit"
            commit_short = version.commit[:12]

            table.add_row(status, type_str, commit_short, version.date, version.name)

    # --- Search ---

    def action_focus_search(self) -> None:
        with contextlib.suppress(NoMatches):
            self.query_one(SearchBar).show()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.filter_query = event.value

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "commit-input":
            self._handle_commit_input()
        elif event.input.id == "search-input":
            self.query_one(SearchBar).hide()
            self.query_one("#version-table", VimDataTable).focus()

    def watch_filter_query(self, new_query: str) -> None:
        self._populate_table()

    # --- Escape ---

    def action_handle_escape(self) -> None:
        search_bar = self.query_one(SearchBar)
        search_input = self.query_one("#search-input")

        # Hide search overlay
        if search_input.has_focus or search_bar.is_shown:
            search_bar.hide()
            self.query_one("#version-table", VimDataTable).focus()
            return

        # Clear active filter
        if self.filter_query:
            search_bar.clear()
            self.filter_query = ""
            self.query_one("#version-table", VimDataTable).focus()
            return

        # Go back
        self.app.pop_screen()

    def action_quit_or_back(self) -> None:
        self.app.pop_screen()

    # --- Version switching ---

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_switch_version()

    def action_switch_version(self) -> None:
        table = self.query_one("#version-table", VimDataTable)

        if table.cursor_row is None:
            return

        if not self._filtered_versions or table.cursor_row >= len(self._filtered_versions):
            return

        selected_version = self._filtered_versions[table.cursor_row]

        if selected_version.is_active:
            self.notify("This version is already active", severity="information")
            return

        self._start_version_switch(selected_version.commit)

    def _start_version_switch(self, target_commit: str) -> None:
        from hivemind_cli.tui.operations import CancellationToken

        token = CancellationToken()
        self.register_worker(self.expert.name, token)
        self.run_worker(self._switch_version_wrapper(target_commit, token), exclusive=True)

    async def _switch_version_wrapper(self, target_commit: str, token):
        from hivemind_cli.tui.operations import switch_version_async_tui

        await switch_version_async_tui(self, self.expert.name, target_commit, token)

    # --- Commit input ---

    def action_input_commit(self) -> None:
        container = self.query_one("#commit-input-container")
        input_field = self.query_one("#commit-input", Input)

        if self._input_visible:
            container.add_class("hidden")
            self._input_visible = False
            self.query_one("#version-table", VimDataTable).focus()
        else:
            container.remove_class("hidden")
            self._input_visible = True
            input_field.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "analyze-button":
            self._handle_commit_input()

    def _handle_commit_input(self) -> None:
        input_field = self.query_one("#commit-input", Input)
        commit = input_field.value.strip()

        if not commit:
            self.notify("Please enter a commit hash", severity="warning")
            return

        if not commit_exists_in_repo(self.expert.name, commit):
            self.notify(f"Commit {commit[:12]} not found in repository", severity="error")
            return

        container = self.query_one("#commit-input-container")
        container.add_class("hidden")
        self._input_visible = False
        input_field.value = ""

        self._start_version_switch(commit)

    def action_refresh(self) -> None:
        table = self.query_one("#version-table", VimDataTable)
        current_cursor = table.cursor_row

        self._load_versions()
        self._populate_table()

        if current_cursor is not None and current_cursor < len(self._filtered_versions):
            table.move_cursor(row=current_cursor)

        self.notify("Versions refreshed", severity="information")

    def set_status_message(self, message: str) -> None:
        header = self.query_one("#expert-header", Static)
        header.update(f"{self._format_header()}  [cyan]{message}[/cyan]")
