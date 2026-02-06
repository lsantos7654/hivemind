"""Expert table widget with multi-select capability."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.reactive import reactive

from hivemind_cli.tui.models import ExpertRow, ExpertStatus, OperationStatus


class ExpertTable(DataTable):
    """DataTable for displaying experts with multi-select support."""

    selected_rows: reactive[set[str]] = reactive(set(), init=False)
    filter_query: reactive[str] = reactive("", init=False)
    filter_status: reactive[str | None] = reactive(None, init=False)

    def __init__(self, experts: list[ExpertRow], **kwargs):
        self._is_mounted = False  # Set BEFORE super().__init__()
        super().__init__(**kwargs)
        self.experts = experts
        self._all_experts = experts.copy()
        self.cursor_type = "row"
        self.zebra_stripes = True

    def on_mount(self) -> None:
        """Set up the table when mounted."""
        self.add_columns("☐", "Name", "Status", "Version", "Versions", "Remote")
        self._is_mounted = True
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh table data based on current filters."""
        # Don't refresh before mount completes
        if not self._is_mounted:
            return

        self.clear()

        # Apply filters
        filtered = self._all_experts

        if self.filter_query:
            query = self.filter_query.lower()
            filtered = [
                e for e in filtered
                if query in e.name.lower() or query in e.remote.lower()
            ]

        if self.filter_status:
            filtered = [
                e for e in filtered
                if e.status.value == self.filter_status
            ]

        # Update experts list
        self.experts = filtered

        # Add rows
        for expert in self.experts:
            checkbox = "☑" if expert.name in self.selected_rows else "☐"

            # Format status with color - show operation status if present
            if expert.operation_status == OperationStatus.CANCELLING:
                status = "[yellow]cancelling...[/yellow]"
            elif expert.operation_status == OperationStatus.IN_PROGRESS:
                if expert.status_message:
                    status = f"[cyan]{expert.status_message}[/cyan]"
                else:
                    status = "[cyan]updating...[/cyan]"
            elif expert.operation_status == OperationStatus.QUEUED:
                status = "[yellow]queued[/yellow]"
            elif expert.status == ExpertStatus.ENABLED:
                status = "[green]enabled[/green]"
            elif expert.status == ExpertStatus.DISABLED:
                status = "[yellow]disabled[/yellow]"
            else:
                status = "[red]unlisted[/red]"

            # Format version
            version = expert.commit[:12] if expert.commit else "[dim]none[/dim]"

            # Format version count
            versions = str(expert.version_count) if expert.version_count > 0 else "[dim]0[/dim]"

            # Format remote (truncate if too long)
            remote = expert.remote
            if len(remote) > 50:
                remote = remote[:47] + "..."

            self.add_row(checkbox, expert.name, status, version, versions, remote)

    def toggle_selection(self) -> None:
        """Toggle selection of the current row."""
        if not self.experts:
            return

        cursor_row = self.cursor_row
        if cursor_row >= len(self.experts):
            return

        expert = self.experts[cursor_row]

        if expert.name in self.selected_rows:
            self.selected_rows.remove(expert.name)
        else:
            self.selected_rows.add(expert.name)

        # Save cursor position before refresh
        saved_cursor = cursor_row
        self.refresh_data()

        # Restore cursor position if still valid
        if saved_cursor < self.row_count:
            self.move_cursor(row=saved_cursor)

    def get_current_expert(self) -> ExpertRow | None:
        """Get the expert at the current cursor position."""
        if not self.experts:
            return None

        cursor_row = self.cursor_row
        if cursor_row >= len(self.experts):
            return None

        return self.experts[cursor_row]

    def get_selected_experts(self) -> list[str]:
        """Get list of selected expert names."""
        return list(self.selected_rows)

    def clear_selection(self) -> None:
        """Clear all selections."""
        self.selected_rows.clear()

        # Save cursor position before refresh
        saved_cursor = self.cursor_row
        self.refresh_data()

        # Restore cursor position if still valid
        if saved_cursor < self.row_count:
            self.move_cursor(row=saved_cursor)

    def update_experts(self, experts: list[ExpertRow]) -> None:
        """Update the expert list."""
        self._all_experts = experts.copy()

        # Save cursor position before refresh
        saved_cursor = self.cursor_row
        self.refresh_data()

        # Restore cursor position if still valid
        if saved_cursor < self.row_count:
            self.move_cursor(row=saved_cursor)

    def watch_filter_query(self, new_query: str) -> None:
        """React to filter query changes."""
        if self._is_mounted:
            # Save cursor position before refresh
            saved_cursor = self.cursor_row
            self.refresh_data()

            # Restore cursor position if still valid
            if saved_cursor < self.row_count:
                self.move_cursor(row=saved_cursor)

    def watch_filter_status(self, new_status: str | None) -> None:
        """React to filter status changes."""
        if self._is_mounted:
            # Save cursor position before refresh
            saved_cursor = self.cursor_row
            self.refresh_data()

            # Restore cursor position if still valid
            if saved_cursor < self.row_count:
                self.move_cursor(row=saved_cursor)
