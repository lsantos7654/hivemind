"""Main screen showing expert list and operations."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Static, DataTable
from textual.binding import Binding

from hivemind_cli.tui.models import ExpertRow, OperationStatus
from hivemind_cli.tui.widgets import ExpertTable, SearchBar
from hivemind_cli.tui.operations import (
    update_expert_async,
    enable_expert_sync,
    disable_expert_sync,
)


class MainScreen(Screen):
    """Main screen for expert management."""

    _last_g_press: float = 0.0

    BINDINGS = [
        Binding("slash", "focus_search", "Search"),
        Binding("enter", "show_details", "Details"),
        Binding("space", "toggle_select", "Select"),
        Binding("e", "enable", "Enable"),
        Binding("d", "disable", "Disable"),
        Binding("u", "update", "Update"),
        Binding("U", "update_all", "Update Enabled"),
        Binding("x", "cancel_update", "Cancel", show=False),
        Binding("escape", "clear_search", "Clear"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "goto_top", "Top", show=False),
        Binding("G", "goto_bottom", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
    ]

    def __init__(self, experts: list[ExpertRow], **kwargs):
        super().__init__(**kwargs)
        self.experts = experts
        self._active_workers: dict[str, dict] = {}
        # Maps expert_name -> {"token": CancellationToken, "pid": int | None}

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Header(show_clock=True)
        yield Container(
            Static("Hivemind Expert Manager", classes="header"),
            SearchBar(classes="search-container"),
            ExpertTable(self.experts, id="expert-table"),
            Static(
                "↑↓/jk: Navigate  Enter: Details  Space: Select  e: Enable  d: Disable  u: Update  U: Update Enabled  x: Cancel  /: Search  Esc: Clear",
                classes="footer keybindings",
            ),
            id="main-container",
        )

    def on_mount(self) -> None:
        """Focus the table when mounted."""
        self.query_one("#expert-table", ExpertTable).focus()

    def set_expert_operation_status(self, expert_name: str, status: OperationStatus | None) -> None:
        """Update the operation status of an expert and refresh the table."""
        for expert in self.experts:
            if expert.name == expert_name:
                expert.operation_status = status
                break
        table = self.query_one("#expert-table", ExpertTable)
        table.update_experts(self.experts)

    def set_expert_status_message(self, expert_name: str, message: str | None) -> None:
        """Update the status message for an expert (shown in Status column)."""
        for expert in self.experts:
            if expert.name == expert_name:
                expert.status_message = message
                break
        table = self.query_one("#expert-table", ExpertTable)
        table.update_experts(self.experts)

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

    def get_worker_info(self, expert_name: str) -> dict | None:
        """Get worker info for an expert."""
        return self._active_workers.get(expert_name)

    def action_toggle_select(self) -> None:
        """Toggle selection of current row."""
        table = self.query_one("#expert-table", ExpertTable)
        table.toggle_selection()

    def action_show_details(self) -> None:
        """Show version detail screen for current expert."""
        from hivemind_cli.tui.screens.version_detail_screen import VersionDetailScreen

        table = self.query_one("#expert-table", ExpertTable)
        current = table.get_current_expert()

        if not current:
            return

        # Prevent viewing during active operations
        if current.operation_status == OperationStatus.IN_PROGRESS:
            self.notify("Cannot view details during active operation", severity="warning")
            return

        # Push version detail screen
        self.app.push_screen(VersionDetailScreen(current))

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input")
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear search, deselect all, and focus table."""
        table = self.query_one("#expert-table", ExpertTable)
        search_input = self.query_one("#search-input")

        # If in search input, just exit back to table
        if search_input.has_focus:
            table.focus()
            return

        # If in table with selections, clear selections first
        if table.get_selected_experts():
            table.clear_selection()
            return

        # Otherwise clear the search filter
        search_bar = self.query_one(SearchBar)
        search_bar.clear()
        table.focus()

    def action_enable(self) -> None:
        """Enable selected or current expert."""
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            for name in selected:
                enable_expert_sync(self, name)

            # Clear selections
            table.clear_selection()

    def action_disable(self) -> None:
        """Disable selected or current expert."""
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            for name in selected:
                disable_expert_sync(self, name)

            # Clear selections
            table.clear_selection()

    def action_update(self) -> None:
        """Update selected or current expert."""
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            # Clear selections immediately
            table.clear_selection()

            # Start background workers for each update
            for name in selected:
                self.run_worker(self._update_expert_wrapper(name), exclusive=False)

    async def _update_expert_wrapper(self, expert_name: str):
        """Wrapper to call async update function with cancellation support."""
        from hivemind_cli.tui.operations import CancellationToken
        token = CancellationToken()
        self.register_worker(expert_name, token)
        await update_expert_async(self, expert_name, token)

    def action_update_all(self) -> None:
        """Update all enabled experts."""
        # Get all enabled experts
        from hivemind_cli.tui.models import ExpertStatus
        enabled = [e.name for e in self.experts if e.status == ExpertStatus.ENABLED]
        if enabled:
            self.notify(f"Updating {len(enabled)} enabled expert(s)...", severity="information")

            # Start background workers for each update
            for name in enabled:
                self.run_worker(self._update_expert_wrapper(name), exclusive=False)
        else:
            self.notify("No enabled experts to update", severity="warning")

    def action_cursor_down(self) -> None:
        """Move cursor down in the table."""
        table = self.query_one("#expert-table", ExpertTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table."""
        table = self.query_one("#expert-table", ExpertTable)
        table.action_cursor_up()

    def action_goto_top(self) -> None:
        """Handle 'g' key press - go to top if pressed twice (gg)."""
        import time
        current_time = time.time()

        # Check if 'g' was pressed within the last 0.5 seconds
        if current_time - self._last_g_press < 0.5:
            # Double 'g' pressed - go to top
            table = self.query_one("#expert-table", ExpertTable)
            table.move_cursor(row=0)
            self._last_g_press = 0.0
        else:
            # First 'g' press - record the time
            self._last_g_press = current_time

    def action_goto_bottom(self) -> None:
        """Go to bottom of table (G/Shift+g)."""
        table = self.query_one("#expert-table", ExpertTable)
        if table.row_count > 0:
            table.move_cursor(row=table.row_count - 1)

    def action_page_down(self) -> None:
        """Move down half a page (Ctrl+d)."""
        table = self.query_one("#expert-table", ExpertTable)
        # Calculate half page based on visible height
        half_page = max(1, table.size.height // 2)
        new_row = min(table.cursor_row + half_page, table.row_count - 1)
        table.move_cursor(row=new_row)

    def action_page_up(self) -> None:
        """Move up half a page (Ctrl+u)."""
        table = self.query_one("#expert-table", ExpertTable)
        # Calculate half page based on visible height
        half_page = max(1, table.size.height // 2)
        new_row = max(0, table.cursor_row - half_page)
        table.move_cursor(row=new_row)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_cancel_update(self) -> None:
        """Cancel currently running update for selected expert."""
        import os
        import signal

        table = self.query_one("#expert-table", ExpertTable)
        current = table.get_current_expert()

        if not current:
            return

        worker_info = self.get_worker_info(current.name)
        if not worker_info:
            self.notify("No active update to cancel", severity="warning")
            return

        # Don't allow cancelling if already cancelling
        if current.operation_status == OperationStatus.CANCELLING:
            return

        # Set status to cancelling
        self.set_expert_operation_status(current.name, OperationStatus.CANCELLING)
        self.set_expert_status_message(current.name, "Cancelling...")

        # Signal cancellation token (worker will detect in next poll)
        worker_info["token"].cancel()

        # Kill subprocess if it exists
        if worker_info["pid"]:
            try:
                os.kill(worker_info["pid"], signal.SIGTERM)
                # Schedule force kill after 5 seconds
                self.set_timer(5.0, lambda: self._force_kill_if_alive(worker_info["pid"]))
            except ProcessLookupError:
                pass  # Already terminated

        self.notify(f"Cancelling {current.name}...", severity="warning")

    def _force_kill_if_alive(self, pid: int):
        """Force kill subprocess if still running."""
        import os
        import signal
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Already dead

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key pressed)."""
        # Only handle events from the expert table
        if event.data_table.id == "expert-table":
            self.action_show_details()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Check if action should be available."""
        if action == "cancel_update":
            # Only show if current row has active update
            table = self.query_one("#expert-table", ExpertTable)
            current = table.get_current_expert()
            if current and current.operation_status == OperationStatus.IN_PROGRESS:
                return True
            return False
        return True
