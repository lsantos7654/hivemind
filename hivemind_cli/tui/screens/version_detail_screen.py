"""Screen for viewing and switching expert versions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Static, Input, Button
from textual.binding import Binding
from textual.reactive import reactive

from hivemind_cli.tui.models import ExpertRow, VersionInfo, OperationStatus
from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import VimDataTable
from hivemind_cli.core import get_git_versions, commit_exists_in_repo, EXPERTS_DIR, PRIVATE_EXPERTS_DIR


class VersionDetailScreen(BaseScreen):
    """Screen for viewing and switching expert versions."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        Binding("q", "quit_or_back", "Back", show=True),
        Binding("enter", "switch_version", "Switch", show=True),
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

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                f"Expert: {self.expert.name}\n"
                f"Current HEAD: {self.expert.commit[:12] if self.expert.commit else 'none'}\n"
                f"Remote: {self.expert.remote}",
                id="expert-header",
            ),
            Horizontal(
                Static("Search: ", classes="search-label"),
                Input(placeholder="Filter by name or message", id="search-input"),
                classes="search-container",
            ),
            Static("Versions (analyzed first, then available):", classes="section-title"),
            VimDataTable(id="version-table", zebra_stripes=True),
            Container(
                Static("Commit hash:", classes="input-label"),
                Input(placeholder="Enter full commit hash (40 chars)", id="commit-input"),
                Button("Analyze", id="analyze-button", variant="primary"),
                id="commit-input-container",
                classes="hidden",
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load versions and populate table when mounted."""
        table = self.query_one("#version-table", VimDataTable)
        table.add_columns("Status", "Type", "Commit", "Date", "Name/Message")
        table.cursor_type = "row"

        self._load_versions()
        self._populate_table()

        table.focus()

    def _load_versions(self) -> None:
        """Load versions from git repo."""
        expert_dir = (
            PRIVATE_EXPERTS_DIR / self.expert.name if self.expert.is_private
            else EXPERTS_DIR / self.expert.name
        )
        self.versions = get_git_versions(self.expert.name, expert_dir)

    def _populate_table(self) -> None:
        """Populate the version table with loaded versions (filtered)."""
        table = self.query_one("#version-table", VimDataTable)
        table.clear()

        filtered_versions = self.versions
        if self.filter_query:
            query = self.filter_query.lower()
            filtered_versions = [
                v for v in self.versions
                if query in v.name.lower() or query in v.commit.lower()
            ]

        self._filtered_versions = filtered_versions

        if not filtered_versions:
            table.add_row("No versions found", "", "", "", "")
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

    def action_handle_escape(self) -> None:
        """Exit search input, clear search, or go back."""
        search_input = self.query_one("#search-input", Input)
        if search_input.has_focus:
            self.action_clear_search()
        elif self.filter_query:
            self.action_clear_search()
        else:
            self.app.pop_screen()

    def action_quit_or_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()

    def action_switch_version(self) -> None:
        """Switch to the selected version."""
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
        """Start async version switch operation."""
        from hivemind_cli.tui.operations import CancellationToken

        token = CancellationToken()
        self.register_worker(self.expert.name, token)
        self.run_worker(self._switch_version_wrapper(target_commit, token), exclusive=True)

    async def _switch_version_wrapper(self, target_commit: str, token):
        """Wrapper to call async switch function with cancellation support."""
        from hivemind_cli.tui.operations import switch_version_async_tui
        await switch_version_async_tui(self, self.expert.name, target_commit, token)

    def action_input_commit(self) -> None:
        """Toggle visibility of commit input field."""
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
        """Handle analyze button press."""
        if event.button.id == "analyze-button":
            self._handle_commit_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "commit-input":
            self._handle_commit_input()
        elif event.input.id == "search-input":
            self.query_one("#version-table", VimDataTable).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.filter_query = event.value

    def on_data_table_row_selected(self, event: VimDataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key pressed)."""
        if event.data_table.id == "version-table":
            self.action_switch_version()

    def _handle_commit_input(self) -> None:
        """Validate and process manual commit input."""
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
        """Refresh git data and reload versions."""
        table = self.query_one("#version-table", VimDataTable)
        current_cursor = table.cursor_row

        self._load_versions()
        self._populate_table()

        if current_cursor is not None and current_cursor < len(self._filtered_versions):
            table.move_cursor(row=current_cursor)

        self.notify("Versions refreshed", severity="information")

    def action_clear_search(self) -> None:
        """Clear search and return focus to table."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.filter_query = ""
        self.query_one("#version-table", VimDataTable).focus()

    def watch_filter_query(self, new_query: str) -> None:
        """React to filter query changes."""
        self._populate_table()

    def set_status_message(self, message: str) -> None:
        """Update status message (shown in header)."""
        header = self.query_one("#expert-header", Static)
        header.update(
            f"Expert: {self.expert.name}\n"
            f"Current HEAD: {self.expert.commit[:12] if self.expert.commit else 'none'}\n"
            f"Remote: {self.expert.remote}\n"
            f"[cyan]{message}[/cyan]"
        )
