"""Detail screen for viewing and managing a team's roster."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import SearchBar, VimDataTable
from hivemind_cli.tui.widgets.search_mixin import SearchMixin


class TeamDetailScreen(SearchMixin, BaseScreen):
    """Screen showing a team's experts with add/remove actions."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        *SearchMixin.SEARCH_BINDINGS,
        Binding("a", "add_expert", "Add Expert", show=True),
        Binding("e", "edit_team", "Edit", show=True),
        Binding("D", "remove_expert", "Remove", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
    ]

    def __init__(self, team_name: str, team_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.team_name = team_name
        self.team_data = team_data
        self._init_search()

    def _format_header(self) -> str:
        desc = self.team_data.get("description", "")
        experts = self.team_data.get("experts", [])
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
        return len(self.team_data.get("experts", []))

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

        config = self.app._load_config()
        enabled = set(config.get("enabled", []))

        for expert_name in sorted(self.team_data.get("experts", [])):
            if self._filter_query:
                if self._filter_query.lower() not in expert_name.lower():
                    continue
            status = "[green]enabled[/green]" if expert_name in enabled else "[dim]disabled[/dim]"
            table.add_row(expert_name, status)
            self._visible_names.append(expert_name)

        if not self._visible_names:
            if self._filter_query:
                table.add_row(f"[dim]No results for \"{self._filter_query}\"[/dim]", "")
            elif not self.team_data.get("experts"):
                table.add_row("[dim]No experts[/dim]", "")

    def _reload(self) -> None:
        """Reload team data from config and refresh table."""
        teams = self.app.load_teams()
        if self.team_name in teams:
            self.team_data = teams[self.team_name]
        self._populate_table()
        self.query_one("#team-header", Static).update(self._format_header())

    def action_edit_team(self) -> None:
        from hivemind_cli.tui.widgets.edit_team_modal import EditTeamModal
        from hivemind_cli.core import update_team

        current_desc = self.team_data.get("description", "")

        async def _handle_result(data: dict | None) -> None:
            if not data:
                return
            new_name = data["name"] if data["name"] != self.team_name else None
            new_desc = data["description"] if data["description"] != current_desc else None

            if new_name is None and new_desc is None:
                return

            result = update_team(self.team_name, new_name=new_name, description=new_desc)
            if result["success"]:
                if new_name:
                    self.team_name = new_name
                self.notify(f"Updated team: {self.team_name}", severity="information")
                self._reload()
            else:
                self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

        self.app.push_screen(EditTeamModal(self.team_name, current_desc), _handle_result)

    def action_add_expert(self) -> None:
        from hivemind_cli.tui.widgets.selection_modal import SelectionListModal
        from hivemind_cli.core import add_expert_to_team

        all_experts = [e.name for e in self.app.experts]
        current = set(self.team_data.get("experts", []))
        available = [(n, n) for n in all_experts if n not in current]

        if not available:
            self.notify("No available experts to add", severity="warning")
            return

        async def _handle_add(selected: list[str] | None) -> None:
            if not selected:
                return
            for expert_name in selected:
                result = add_expert_to_team(self.team_name, expert_name)
                if result["success"]:
                    self.notify(f"Added {expert_name}", severity="information")
                else:
                    self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")
            self._reload()

        self.app.push_screen(SelectionListModal(available, title="Add Experts"), _handle_add)

    def action_remove_expert(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal
        from hivemind_cli.core import remove_expert_from_team

        expert_name = self.get_current_name()
        if not expert_name:
            return

        async def _do_remove(confirmed: bool) -> None:
            if confirmed:
                result = remove_expert_from_team(self.team_name, expert_name)
                if result["success"]:
                    self.notify(f"Removed {expert_name}", severity="information")
                    self._reload()
                else:
                    self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

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
