"""Main screen showing expert list and operations."""

from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Header, Static, DataTable
from textual.binding import Binding

from hivemind_cli.tui.models import ExpertRow, ExpertStatus, OperationStatus
from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import ExpertTable, SearchBar
from hivemind_cli.tui.operations import (
    update_expert_async,
    enable_expert_sync,
    disable_expert_sync,
)


class MainScreen(BaseScreen):
    """Main screen for expert management."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        Binding("enter", "show_details", "Details"),
        Binding("space", "toggle_select", "Select"),
        Binding("e", "enable", "Enable"),
        Binding("d", "disable", "Disable"),
        Binding("u", "update", "Update"),
        Binding("U", "update_all", "Update Enabled"),
        Binding("x", "cancel_update", "Cancel", show=False),
    ]

    def __init__(self, experts: list[ExpertRow], **kwargs):
        super().__init__(**kwargs)
        self.experts = experts
        self._last_escape_press: float = 0.0

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Header(show_clock=True)
        yield Container(
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

    def action_go_back(self) -> None:
        """On main screen, ctrl-o exits the app."""
        self.app.exit()

    def action_handle_escape(self) -> None:
        """Clear search, deselect all, and focus table. Double-press exits."""
        table = self.query_one("#expert-table", ExpertTable)
        search_input = self.query_one("#search-input")

        # If in search input, just exit back to table
        if search_input.has_focus:
            table.focus()
            self._last_escape_press = 0.0
            return

        # If in table with selections, clear selections first
        if table.get_selected_experts():
            table.clear_selection()
            self._last_escape_press = 0.0
            return

        # If there's a search filter, clear it
        search_bar = self.query_one(SearchBar)
        if search_bar.query:
            search_bar.clear()
            table.focus()
            self._last_escape_press = 0.0
            return

        # Nothing to clear — double-press exits
        now = time.monotonic()
        if now - self._last_escape_press < 0.5:
            self.app.exit()
        else:
            self._last_escape_press = now

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
        enabled = [e.name for e in self.experts if e.status == ExpertStatus.ENABLED]
        if enabled:
            self.notify(f"Updating {len(enabled)} enabled expert(s)...", severity="information")

            # Start background workers for each update
            for name in enabled:
                self.run_worker(self._update_expert_wrapper(name), exclusive=False)
        else:
            self.notify("No enabled experts to update", severity="warning")

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
