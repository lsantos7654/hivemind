"""Experts pane — the expert list content used inside the tabbed layout."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.binding import Binding

from hivemind_cli.tui.models import ExpertRow, ExpertStatus, OperationStatus
from hivemind_cli.tui.widgets.base_pane import BasePane
from hivemind_cli.tui.widgets import ExpertTable, SearchBar
from hivemind_cli.tui.operations import (
    update_expert_async,
    enable_expert_async_op,
    disable_expert_async_op,
)


class ExpertsPane(BasePane):
    """Expert list pane for the tabbed layout."""

    BINDINGS = [
        *BasePane.BINDINGS,
        Binding("enter", "show_details", "Details", show=True),
        Binding("space", "toggle_select", "Select", show=True),
        Binding("e", "enable", "Enable", show=True),
        Binding("d", "disable", "Disable", show=True),
        Binding("D", "delete", "Delete", show=True),
        Binding("a", "add_expert", "Add", show=True),
        Binding("u", "update", "Update", show=True),
        Binding("U", "update_all", "Update All", show=False),
        Binding("x", "cancel_update", "Cancel", show=False),
    ]

    def __init__(self, experts: list[ExpertRow], **kwargs):
        super().__init__(**kwargs)
        self.experts = experts
        self._active_workers: dict[str, dict] = {}

    def _get_table_id(self) -> str:
        return "expert-table"

    def _get_total_count(self) -> int:
        return len(self.experts)

    def compose(self) -> ComposeResult:
        yield Static("", classes="filter-indicator")
        yield SearchBar()
        yield ExpertTable(self.experts, id="expert-table")

    def on_mount(self) -> None:
        self.query_one("#expert-table", ExpertTable).focus()

    def _populate_table(self) -> None:
        """ExpertTable handles its own filtering via reactive filter_query."""
        table = self.query_one("#expert-table", ExpertTable)
        table.filter_query = self._filter_query
        # Build visible names from the filtered experts
        self._visible_names = [e.name for e in table.experts]

    def _on_all_clear(self) -> None:
        """Clear selections, then double-press to exit."""
        table = self.query_one("#expert-table", ExpertTable)

        if table.get_selected_experts():
            table.clear_selection()
            self._last_escape_press = 0.0
            return

        super()._on_all_clear()

    # --- Worker management ---

    def register_worker(self, expert_name: str, token) -> None:
        self._active_workers[expert_name] = {"token": token, "pid": None}

    def register_subprocess_pid(self, expert_name: str, pid: int) -> None:
        if expert_name in self._active_workers:
            self._active_workers[expert_name]["pid"] = pid

    def unregister_worker(self, expert_name: str) -> None:
        self._active_workers.pop(expert_name, None)

    def get_worker_info(self, expert_name: str) -> dict | None:
        return self._active_workers.get(expert_name)

    def set_expert_operation_status(self, expert_name: str, status: OperationStatus | None) -> None:
        for expert in self.experts:
            if expert.name == expert_name:
                expert.operation_status = status
                break
        self.query_one("#expert-table", ExpertTable).update_experts(self.experts)

    def set_expert_status_message(self, expert_name: str, message: str | None) -> None:
        for expert in self.experts:
            if expert.name == expert_name:
                expert.status_message = message
                break
        self.query_one("#expert-table", ExpertTable).update_experts(self.experts)

    # --- Actions ---

    def action_toggle_select(self) -> None:
        self.query_one("#expert-table", ExpertTable).toggle_selection()

    def action_show_details(self) -> None:
        from hivemind_cli.tui.screens.version_detail_screen import VersionDetailScreen

        table = self.query_one("#expert-table", ExpertTable)
        current = table.get_current_expert()

        if not current:
            return

        if current.operation_status == OperationStatus.IN_PROGRESS:
            self.notify("Cannot view details during active operation", severity="warning")
            return

        self.app.push_screen(VersionDetailScreen(current))

    def action_enable(self) -> None:
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            for name in selected:
                self.notify(f"Enabling {name}...", severity="information")
                self.run_worker(enable_expert_async_op(self, name), exit_on_error=False)
            table.clear_selection()

    def action_disable(self) -> None:
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            for name in selected:
                self.notify(f"Disabling {name}...", severity="information")
                self.run_worker(disable_expert_async_op(self, name), exit_on_error=False)
            table.clear_selection()

    def action_delete(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal

        table = self.query_one("#expert-table", ExpertTable)
        current = table.get_current_expert()

        if not current:
            return

        if current.operation_status == OperationStatus.IN_PROGRESS:
            self.notify("Cannot delete during active operation", severity="warning")
            return

        name = current.name

        async def _do_delete(confirmed: bool) -> None:
            if confirmed:
                from hivemind_cli.tui.operations import delete_expert_async_op
                self.notify(f"Deleting {name}...", severity="warning")
                self.run_worker(delete_expert_async_op(self, name), exit_on_error=False)

        self.app.push_screen(
            ConfirmationModal(
                f"Delete expert '{name}'? This removes all local data and agent files.",
                title="Delete Expert",
                confirm_label="Delete",
            ),
            _do_delete,
        )

    def action_add_expert(self) -> None:
        from hivemind_cli.tui.widgets.add_expert_modal import AddExpertModal

        async def _handle_result(url: str | None) -> None:
            if url:
                self.notify(f"Adding expert from {url}...", severity="information")
                self.run_worker(self._add_expert_wrapper(url), exclusive=False)

        self.app.push_screen(AddExpertModal(), _handle_result)

    async def _add_expert_wrapper(self, url: str):
        from hivemind_cli.tui.operations import add_expert_async
        await add_expert_async(self, url)

    def action_update(self) -> None:
        table = self.query_one("#expert-table", ExpertTable)
        selected = table.get_selected_experts()

        if not selected:
            current = table.get_current_expert()
            if current:
                selected = [current.name]

        if selected:
            table.clear_selection()
            for name in selected:
                self.run_worker(self._update_expert_wrapper(name), exclusive=False)

    async def _update_expert_wrapper(self, expert_name: str):
        from hivemind_cli.tui.operations import CancellationToken
        token = CancellationToken()
        self.register_worker(expert_name, token)
        await update_expert_async(self, expert_name, token)

    def action_update_all(self) -> None:
        enabled = [e.name for e in self.experts if e.status == ExpertStatus.ENABLED]
        if enabled:
            self.notify(f"Updating {len(enabled)} enabled expert(s)...", severity="information")
            for name in enabled:
                self.run_worker(self._update_expert_wrapper(name), exclusive=False)
        else:
            self.notify("No enabled experts to update", severity="warning")

    def action_cancel_update(self) -> None:
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

        if current.operation_status == OperationStatus.CANCELLING:
            return

        self.set_expert_operation_status(current.name, OperationStatus.CANCELLING)
        self.set_expert_status_message(current.name, "Cancelling...")
        worker_info["token"].cancel()

        if worker_info["pid"]:
            try:
                os.kill(worker_info["pid"], signal.SIGTERM)
                self.set_timer(5.0, lambda: self._force_kill_if_alive(worker_info["pid"]))
            except ProcessLookupError:
                pass

        self.notify(f"Cancelling {current.name}...", severity="warning")

    def _force_kill_if_alive(self, pid: int):
        import os
        import signal
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "expert-table":
            self.action_show_details()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "cancel_update":
            table = self.query_one("#expert-table", ExpertTable)
            current = table.get_current_expert()
            if current and current.operation_status == OperationStatus.IN_PROGRESS:
                return True
            return False
        return True
