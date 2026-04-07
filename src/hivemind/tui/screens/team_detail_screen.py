"""Detail screen for viewing and managing a team's roster."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import Footer, Static

from hivemind.config import load_config
from hivemind.tui.models import OperationStatus
from hivemind.tui.screens.base_screen import BaseScreen
from hivemind.tui.widgets import SearchBar, VimDataTable
from hivemind.tui.widgets.search_mixin import SearchMixin

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from hivemind.models import TeamData


class TeamDetailScreen(SearchMixin, BaseScreen):
    """Screen showing a team's experts with add/remove actions."""

    BINDINGS: ClassVar[list[BindingType]] = [
        *BaseScreen.BINDINGS,
        *SearchMixin.SEARCH_BINDINGS,
        Binding("a", "add_expert", "Add Expert", show=True),
        Binding("e", "edit_team", "Edit", show=True),
        Binding("D", "remove_expert", "Remove", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
    ]

    def __init__(self, team_name: str, team_data: TeamData, **kwargs):
        super().__init__(**kwargs)
        self.team_name = team_name
        self.team_data = team_data
        self._pending_ops: dict[str, OperationStatus] = {}
        self._status_messages: dict[str, str] = {}
        self._init_search()

    def set_expert_operation_status(self, name: str, status: OperationStatus | None) -> None:
        """Set or clear the operation status for an expert row."""
        if status is None:
            self._pending_ops.pop(name, None)
        else:
            self._pending_ops[name] = status
        self._populate_table()
        self.query_one("#team-header", Static).update(self._format_header())

    def set_expert_status_message(self, name: str, message: str | None) -> None:
        """Set or clear the status message for an expert row."""
        if message is None:
            self._status_messages.pop(name, None)
        else:
            self._status_messages[name] = message
        self._populate_table()

    def _format_header(self) -> str:
        desc = self.team_data.description
        experts = self.team_data.experts
        count = len(experts)
        parts = [f"[bold]{self.team_name}[/bold]"]
        if desc:
            parts.append(desc)
        parts.append(f"{count} expert{'s' if count != 1 else ''}")
        return "  │  ".join(parts)

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), id="team-header")
        yield Static("", classes="filter-indicator")
        yield SearchBar()
        yield VimDataTable(id="team-roster-table", zebra_stripes=True)
        yield Footer()

    def _get_table(self) -> VimDataTable:
        return self.query_one("#team-roster-table", VimDataTable)

    def _get_total_count(self) -> int:
        return len(self.team_data.experts)

    def _on_all_clear(self) -> None:
        self.app.pop_screen()

    def on_mount(self) -> None:
        table = self._get_table()
        table.add_columns("Name", "Status")
        table.cursor_type = "row"
        self._populate_table()
        table.focus()

    def _populate_table(self) -> None:
        table = self._get_table()
        table.clear()
        self._visible_names = []

        config = load_config()
        enabled = set(config.enabled)

        # Experts already on the team
        for expert_name in sorted(self.team_data.experts):
            if self._filter_query and self._filter_query.lower() not in expert_name.lower():
                continue

            # Check if this expert has an active operation
            if expert_name in self._pending_ops:
                status = self._render_op_status(expert_name)
            else:
                status = "[green]enabled[/green]" if expert_name in enabled else "[dim]disabled[/dim]"

            table.add_row(expert_name, status)
            self._visible_names.append(expert_name)

        # Pending experts not yet in team_data (queued or currently being added)
        for expert_name in sorted(self._pending_ops):
            if expert_name in self.team_data.experts:
                continue  # already rendered above
            if self._filter_query and self._filter_query.lower() not in expert_name.lower():
                continue
            status = self._render_op_status(expert_name)
            table.add_row(expert_name, status)
            self._visible_names.append(expert_name)

        if not self._visible_names:
            if self._filter_query:
                table.add_row(f'[dim]No results for "{self._filter_query}"[/dim]', "")
            elif not self.team_data.experts:
                table.add_row("[dim]No experts[/dim]", "")

    def _render_op_status(self, expert_name: str) -> str:
        """Render the status column text for an expert with an active operation."""
        op = self._pending_ops.get(expert_name)
        msg = self._status_messages.get(expert_name)
        if op == OperationStatus.IN_PROGRESS:
            return f"[yellow]{msg or 'adding...'}[/yellow]"
        if op == OperationStatus.QUEUED:
            return "[dim]queued[/dim]"
        if op == OperationStatus.SUCCESS:
            return "[green]added[/green]"
        if op == OperationStatus.FAILED:
            return f"[red]{msg or 'failed'}[/red]"
        return "[dim]...[/dim]"

    def _reload(self) -> None:
        """Reload team data from config and refresh table."""
        teams = self.app.load_teams()
        if self.team_name in teams:
            self.team_data = teams[self.team_name]
        self._populate_table()
        self.query_one("#team-header", Static).update(self._format_header())

    def action_edit_team(self) -> None:
        from hivemind.teams import update_team
        from hivemind.tui.widgets.edit_team_modal import EditTeamModal

        current_desc = self.team_data.description

        def _handle_result(data: dict | None) -> None:
            if not data:
                return
            new_name = data["name"] if data["name"] != self.team_name else None
            new_desc = data["description"] if data["description"] != current_desc else None

            if new_name is None and new_desc is None:
                return

            from hivemind.config import load_config

            config = load_config()
            result = update_team(self.team_name, new_name=new_name, description=new_desc, config=config)
            if result.success:
                if new_name:
                    self.team_name = new_name
                self.notify(f"Updated team: {self.team_name}", severity="information")
                self._reload()
            else:
                self.notify(f"Failed: {result.error or 'Unknown'}", severity="error")

        self.app.push_screen(EditTeamModal(self.team_name, current_desc), _handle_result)

    def action_add_expert(self) -> None:
        from hivemind.tui.widgets.selection_modal import SelectionListModal

        all_experts = [e.name for e in self.app.experts]
        current = set(self.team_data.experts)
        available = [(n, n) for n in all_experts if n not in current]

        if not available:
            self.notify("No available experts to add", severity="warning")
            return

        def _handle_add(selected: list[str] | None) -> None:
            if not selected:
                return
            # Pre-populate all selected experts as queued so they appear in the table
            for name in selected:
                self._pending_ops[name] = OperationStatus.QUEUED
                self._status_messages[name] = "queued"
            self._populate_table()
            self.query_one("#team-header", Static).update(self._format_header())
            self.run_worker(self._add_experts_async(selected), exit_on_error=False)

        self.app.push_screen(SelectionListModal(available, title="Add Experts"), _handle_add)

    async def _add_experts_async(self, selected: list[str]) -> None:
        from hivemind.config import load_config
        from hivemind.teams import add_experts_to_team

        config = load_config()

        def on_progress(expert_name: str) -> None:
            """Called when an expert starts being AI-analyzed."""
            self.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
            self.set_expert_status_message(expert_name, "adding...")

        try:
            result = await add_experts_to_team(
                self.team_name,
                selected,
                on_progress=on_progress,
                config=config,
            )

            for name in result.added:
                self.notify(f"Added {name}", severity="information")
            for name in result.skipped:
                self.notify(f"{name}: already on team", severity="warning")
            for err in result.failed:
                self.notify(f"Failed {err.name}: {err.error}", severity="error")

            if not result.success:
                self.notify(f"Failed: {result.error or 'Unknown'}", severity="error")

        except Exception as e:
            self.notify(f"Error adding experts: {e}", severity="error")
        finally:
            self._pending_ops.clear()
            self._status_messages.clear()
            self._reload()

    def action_remove_expert(self) -> None:
        from hivemind.tui.widgets import ConfirmationModal

        expert_name = self.get_current_name()
        if not expert_name:
            return

        def _do_remove(confirmed: bool) -> None:
            if confirmed:
                from hivemind.config import load_config
                from hivemind.teams import remove_expert_from_team

                config = load_config()
                result = remove_expert_from_team(self.team_name, expert_name, config=config)
                if result.success:
                    self.notify(f"Removed {expert_name}", severity="information")
                    self._reload()
                else:
                    self.notify(f"Failed: {result.error or 'Unknown'}", severity="error")

        self.app.push_screen(
            ConfirmationModal(
                f"Remove '{expert_name}' from team '{self.team_name}'?",
                title="Remove Expert",
                confirm_label="Remove",
            ),
            _do_remove,
        )

    def action_quit_or_back(self) -> None:
        self.app.pop_screen()
