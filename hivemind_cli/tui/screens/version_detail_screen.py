"""Screen for viewing and switching expert versions."""

from __future__ import annotations

import time
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Header, DataTable, Static, Input, Button
from textual.binding import Binding
from textual.reactive import reactive

from hivemind_cli.tui.models import ExpertRow, VersionInfo, OperationStatus
from hivemind_cli.core import get_git_versions, commit_exists_in_repo, EXPERTS_DIR, PRIVATE_EXPERTS_DIR


class VersionDetailScreen(Screen):
    """Screen for viewing and switching expert versions."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "back", "Back"),
        Binding("enter", "switch_version", "Switch"),
        Binding("i", "input_commit", "Input Commit"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "goto_top", "Top", show=False),
        Binding("G", "goto_bottom", "Bottom", show=False),
        Binding("slash", "focus_search", "Search"),
        Binding("ctrl+d", "page_down_half", "Half Page Down", show=False),
        Binding("ctrl+u", "page_up_half", "Half Page Up", show=False),
    ]

    def __init__(self, expert: ExpertRow, **kwargs):
        super().__init__(**kwargs)
        self.expert = expert
        self.versions: list[VersionInfo] = []
        self._filtered_versions: list[VersionInfo] = []  # Cached filtered list
        self._last_g_press = 0.0
        self._active_workers: dict[str, dict] = {}  # For cancellation
        self._input_visible = False

    # Reactive variable for search filtering
    filter_query: reactive[str] = reactive("", init=False)

    def compose(self) -> ComposeResult:
        """Compose the version detail screen."""
        yield Header(show_clock=True)
        yield Container(
            # Expert info panel
            Static(
                f"Expert: {self.expert.name}\n"
                f"Current HEAD: {self.expert.commit[:12] if self.expert.commit else 'none'}\n"
                f"Remote: {self.expert.remote}",
                id="expert-header",
            ),
            # Search bar (always visible like main screen)
            Horizontal(
                Static("Search: ", classes="search-label"),
                Input(placeholder="Filter by name or message", id="search-input"),
                classes="search-container",
            ),
            # Section title
            Static("Versions (analyzed first, then available):", classes="section-title"),
            # Version table
            DataTable(id="version-table", zebra_stripes=True),
            # Commit input container (hidden by default)
            Container(
                Static("Commit hash:", classes="input-label"),
                Input(placeholder="Enter full commit hash (40 chars)", id="commit-input"),
                Button("Analyze", id="analyze-button", variant="primary"),
                id="commit-input-container",
                classes="hidden",
            ),
            # Footer
            Static(
                "↑↓/jk: Navigate  Ctrl+d/u: Half Page  Enter: Switch  /: Search  i: Input  r: Refresh  Esc/q: Back",
                classes="footer keybindings",
            ),
            id="main-container",
        )

    def on_mount(self) -> None:
        """Load versions and populate table when mounted."""
        # Set up table columns
        table = self.query_one("#version-table", DataTable)
        table.add_columns("Status", "Type", "Commit", "Date", "Name/Message")
        table.cursor_type = "row"

        # Load and display versions
        self._load_versions()
        self._populate_table()

        # Focus the table
        table.focus()

    def _load_versions(self) -> None:
        """Load versions from git repo."""
        # Get the correct expert directory based on privacy status
        expert_dir = (
            PRIVATE_EXPERTS_DIR / self.expert.name if self.expert.is_private
            else EXPERTS_DIR / self.expert.name
        )
        self.versions = get_git_versions(self.expert.name, expert_dir)

    def _populate_table(self) -> None:
        """Populate the version table with loaded versions (filtered)."""
        table = self.query_one("#version-table", DataTable)
        table.clear()

        # Apply filter
        filtered_versions = self.versions
        if self.filter_query:
            query = self.filter_query.lower()
            filtered_versions = [
                v for v in self.versions
                if query in v.name.lower() or query in v.commit.lower()
            ]

        # Cache filtered versions for action_switch_version
        self._filtered_versions = filtered_versions

        if not filtered_versions:
            # Show empty message
            table.add_row("No versions found", "", "", "", "")
            return

        for version in filtered_versions:
            # Status indicator
            if version.is_active:
                status = "[green]● active[/green]"
            elif version.analyzed:
                status = "[cyan]✓ analyzed[/cyan]"
            else:
                status = "[dim]○ available[/dim]"

            # Type indicator
            type_str = "[bold]TAG[/bold]" if version.type == "tag" else "commit"

            # Truncate commit hash
            commit_short = version.commit[:12]

            # Add row
            table.add_row(
                status,
                type_str,
                commit_short,
                version.date,
                version.name,
            )

    def action_back(self) -> None:
        """Return to main screen, or exit search input if focused."""
        # Check if search input is focused
        search_input = self.query_one("#search-input", Input)
        if search_input.has_focus:
            # Exit search input and return focus to table
            self.action_clear_search()
        elif self.filter_query:
            # If there's a search query but input not focused, clear it
            self.action_clear_search()
        else:
            # Go back to main screen
            self.app.pop_screen()

    def action_switch_version(self) -> None:
        """Switch to the selected version."""
        table = self.query_one("#version-table", DataTable)

        # Get selected row index
        if table.cursor_row is None:
            return

        # Use filtered versions (which is what's displayed in the table)
        if not self._filtered_versions or table.cursor_row >= len(self._filtered_versions):
            return

        selected_version = self._filtered_versions[table.cursor_row]

        # Prevent switching if already active
        if selected_version.is_active:
            self.notify("This version is already active", severity="information")
            return

        # Start the version switch
        self._start_version_switch(selected_version.commit)

    def _start_version_switch(self, target_commit: str) -> None:
        """Start async version switch operation."""
        from hivemind_cli.tui.operations import CancellationToken

        # Create cancellation token
        token = CancellationToken()
        self.register_worker(self.expert.name, token)

        # Start async operation
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
            # Hide input
            container.add_class("hidden")
            self._input_visible = False
            self.query_one("#version-table", DataTable).focus()
        else:
            # Show input
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
            # Return focus to table without clearing search (like main screen)
            self.query_one("#version-table", DataTable).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.filter_query = event.value

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
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

        # Validate commit exists
        if not commit_exists_in_repo(self.expert.name, commit):
            self.notify(f"Commit {commit[:12]} not found in repository", severity="error")
            return

        # Hide input container
        container = self.query_one("#commit-input-container")
        container.add_class("hidden")
        self._input_visible = False

        # Clear input
        input_field.value = ""

        # Start switch
        self._start_version_switch(commit)

    def action_refresh(self) -> None:
        """Refresh git data and reload versions."""
        table = self.query_one("#version-table", DataTable)
        current_cursor = table.cursor_row

        # Reload versions
        self._load_versions()
        self._populate_table()

        # Restore cursor position if possible (use filtered versions count)
        if current_cursor is not None and current_cursor < len(self._filtered_versions):
            table.move_cursor(row=current_cursor)

        self.notify("Versions refreshed", severity="information")

    # Vim navigation
    def action_cursor_down(self) -> None:
        """Move cursor down (j)."""
        table = self.query_one("#version-table", DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up (k)."""
        table = self.query_one("#version-table", DataTable)
        table.action_cursor_up()

    def action_goto_top(self) -> None:
        """Go to top (gg)."""
        now = time.time()
        if now - self._last_g_press < 0.5:  # Double-g within 0.5s
            table = self.query_one("#version-table", DataTable)
            table.move_cursor(row=0)
            self._last_g_press = 0.0
        else:
            self._last_g_press = now

    def action_goto_bottom(self) -> None:
        """Go to bottom (G)."""
        table = self.query_one("#version-table", DataTable)
        if len(self._filtered_versions) > 0:
            table.move_cursor(row=len(self._filtered_versions) - 1)

    def action_focus_search(self) -> None:
        """Focus search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear search and return focus to table."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.filter_query = ""
        self.query_one("#version-table", DataTable).focus()

    def watch_filter_query(self, new_query: str) -> None:
        """React to filter query changes."""
        self._populate_table()

    def action_page_down_half(self) -> None:
        """Move cursor down by half a page (vim-style ctrl-d)."""
        table = self.query_one("#version-table", DataTable)

        if table.cursor_row is None:
            return

        # Calculate half page size (estimate 10 rows for half page)
        half_page = max(1, 10)

        new_row = min(table.cursor_row + half_page, table.row_count - 1)
        table.move_cursor(row=new_row)

    def action_page_up_half(self) -> None:
        """Move cursor up by half a page (vim-style ctrl-u)."""
        table = self.query_one("#version-table", DataTable)

        if table.cursor_row is None:
            return

        half_page = max(1, 10)
        new_row = max(0, table.cursor_row - half_page)
        table.move_cursor(row=new_row)

    # Worker management (for cancellation support)
    def register_worker(self, expert_name: str, token: "CancellationToken") -> None:
        """Register active worker for an expert."""
        from hivemind_cli.tui.operations import CancellationToken
        self._active_workers[expert_name] = {"token": token, "pid": None}

    def register_subprocess_pid(self, expert_name: str, pid: int) -> None:
        """Register subprocess PID for cancellation."""
        if expert_name in self._active_workers:
            self._active_workers[expert_name]["pid"] = pid

    def unregister_worker(self, expert_name: str) -> None:
        """Remove worker from registry."""
        self._active_workers.pop(expert_name, None)

    def set_status_message(self, message: str) -> None:
        """Update status message (shown in header)."""
        header = self.query_one("#expert-header", Static)
        header.update(
            f"Expert: {self.expert.name}\n"
            f"Current HEAD: {self.expert.commit[:12] if self.expert.commit else 'none'}\n"
            f"Remote: {self.expert.remote}\n"
            f"[cyan]{message}[/cyan]"
        )
