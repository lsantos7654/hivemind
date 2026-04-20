"""Teams pane — team list content used inside the tabbed layout."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import DataTable, Static

from hivemind.tui.widgets import SearchBar, VimDataTable
from hivemind.tui.widgets.base_pane import BasePane

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from hivemind.models import TeamData


class TeamsPane(BasePane):
    """Team list pane for the tabbed layout."""

    BINDINGS: ClassVar[list[BindingType]] = [
        *BasePane.BINDINGS,
        Binding("n", "create_team", "New", show=True),
        Binding("D", "delete_team", "Delete", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._teams: dict[str, TeamData] = {}

    def _get_table_id(self) -> str:
        return "teams-table"

    def _get_total_count(self) -> int:
        return len(self._teams)

    def compose(self) -> ComposeResult:
        yield Static("", classes="filter-indicator")
        yield SearchBar()
        yield VimDataTable(id="teams-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self._get_table()
        table.add_columns("Name", "Experts", "Description")
        table.cursor_type = "row"
        table.focus()

    def load_teams(self) -> None:
        self._teams = self.app.load_teams()
        self._populate_table()
        self._update_filter_indicator()

    def _populate_table(self) -> None:
        table = self._get_table()
        table.clear()
        self._visible_names = []

        for name, data in sorted(self._teams.items()):
            if self._filter_query:
                query = self._filter_query.lower()
                if query not in name.lower() and query not in data.description.lower():
                    continue

            experts = data.experts
            expert_count = f"{len(experts)} expert{'s' if len(experts) != 1 else ''}"
            description = data.description or "[dim]none[/dim]"

            table.add_row(name, expert_count, description)
            self._visible_names.append(name)

        if not self._visible_names:
            if self._filter_query:
                table.add_row(f'[dim]No results for "{self._filter_query}"[/dim]', "", "")
            elif not self._teams:
                table.add_row("[dim]No teams[/dim]", "", "")

    def action_create_team(self) -> None:
        from hivemind.tui.widgets.create_team_modal import CreateTeamModal

        def _handle_result(data: dict | None) -> None:
            if data:
                self.run_worker(self._create_team_async(data), exit_on_error=False)

        self.app.push_screen(CreateTeamModal(), _handle_result)

    async def _create_team_async(self, data: dict) -> None:
        from hivemind.agents.roster_templated import create_team

        result = await create_team(data["name"], data["description"], data["experts"])
        if result.success:
            self.notify(f"Created team: {data['name']}", severity="information")
            self.load_teams()
        else:
            self.notify(f"Failed: {result.error or 'Unknown'}", severity="error")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_show_details()

    def action_show_details(self) -> None:
        name = self.get_current_name()
        if name and name in self._teams:
            from hivemind.tui.screens.team_detail_screen import TeamDetailScreen

            self.app.push_screen(TeamDetailScreen(name, self._teams[name]))

    def action_delete_team(self) -> None:
        from hivemind.tui.widgets import ConfirmationModal

        name = self.get_current_name()
        if not name:
            return

        def _do_delete(confirmed: bool) -> None:
            if confirmed:
                from hivemind.lifecycle import delete_agent

                result = delete_agent(name)
                if result.success:
                    self.notify(f"Deleted team: {name}", severity="information")
                    self.load_teams()
                else:
                    self.notify(f"Failed: {result.error or 'Unknown'}", severity="error")

        self.app.push_screen(
            ConfirmationModal(
                f"Delete team '{name}'?",
                title="Delete Team",
                confirm_label="Delete",
            ),
            _do_delete,
        )
