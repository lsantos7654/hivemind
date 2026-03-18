"""Detail screen for viewing and managing a project's teams."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import SearchBar, VimDataTable
from hivemind_cli.tui.widgets.search_mixin import SearchMixin


class ProjectDetailScreen(SearchMixin, BaseScreen):
    """Screen showing a project's teams with add/remove/set-active actions."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        *SearchMixin.SEARCH_BINDINGS,
        Binding("a", "add_team", "Add Team", show=True),
        Binding("e", "edit_project", "Edit", show=True),
        Binding("D", "remove_team", "Remove", show=True),
        Binding("s", "set_active", "Set Active", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
    ]

    def __init__(self, project_name: str, project_data: dict, is_active: bool, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.project_data = project_data
        self._is_active_project = is_active
        self._init_search()

    def _format_header(self) -> str:
        desc = self.project_data.get("description", "")
        active = " [green]● active[/green]" if self._is_active_project else ""
        teams = self.project_data.get("teams", [])
        count = len(teams)
        parts = [f"[bold]{self.project_name}[/bold]{active}"]
        if desc:
            parts.append(desc)
        parts.append(f"{count} team{'s' if count != 1 else ''}")
        return "  │  ".join(parts)

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), id="project-header")
        yield Static("", classes="filter-indicator")
        yield SearchBar()
        yield VimDataTable(id="project-teams-table", zebra_stripes=True)
        yield Footer()

    def _get_table(self) -> VimDataTable:
        return self.query_one("#project-teams-table", VimDataTable)

    def _get_total_count(self) -> int:
        return len(self.project_data.get("teams", []))

    def _on_all_clear(self) -> None:
        self.app.pop_screen()

    def on_mount(self) -> None:
        table = self._get_table()
        table.add_columns("Name", "Expert Count", "Description")
        table.cursor_type = "row"
        self._populate_table()
        table.focus()

    def _populate_table(self) -> None:
        table = self._get_table()
        table.clear()
        self._visible_names = []

        all_teams = self.app.load_teams()
        project_teams = self.project_data.get("teams", [])

        for team_name in sorted(project_teams):
            if self._filter_query:
                if self._filter_query.lower() not in team_name.lower():
                    continue
            team_data = all_teams.get(team_name, {})
            expert_count = len(team_data.get("experts", []))
            desc = team_data.get("description", "[dim]none[/dim]")
            table.add_row(team_name, str(expert_count), desc)
            self._visible_names.append(team_name)

        if not self._visible_names:
            if self._filter_query:
                table.add_row(f"[dim]No results for \"{self._filter_query}\"[/dim]", "", "")
            elif not project_teams:
                table.add_row("[dim]No teams[/dim]", "", "")

    def _reload(self) -> None:
        """Reload project data from config and refresh table."""
        projects, active = self.app.load_projects()
        if self.project_name in projects:
            self.project_data = projects[self.project_name]
        self._is_active_project = active == self.project_name
        self._populate_table()
        self.query_one("#project-header", Static).update(self._format_header())

    def action_edit_project(self) -> None:
        from hivemind_cli.tui.widgets.edit_project_modal import EditProjectModal
        from hivemind_cli.core import update_project

        current_desc = self.project_data.get("description", "")

        async def _handle_result(data: dict | None) -> None:
            if not data:
                return
            new_name = data["name"] if data["name"] != self.project_name else None
            new_desc = data["description"] if data["description"] != current_desc else None

            if new_name is None and new_desc is None:
                return

            result = update_project(self.project_name, new_name=new_name, description=new_desc)
            if result["success"]:
                if new_name:
                    self.project_name = new_name
                self.notify(f"Updated project: {self.project_name}", severity="information")
                self._reload()
            else:
                self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

        self.app.push_screen(EditProjectModal(self.project_name, current_desc), _handle_result)

    def action_add_team(self) -> None:
        from hivemind_cli.tui.widgets.selection_modal import SelectionListModal
        from hivemind_cli.core import add_team_to_project

        all_teams = self.app.load_teams()
        current = set(self.project_data.get("teams", []))
        available = [(n, n) for n in sorted(all_teams) if n not in current]

        if not available:
            self.notify("No available teams to add", severity="warning")
            return

        async def _handle_add(selected: list[str] | None) -> None:
            if not selected:
                return
            for team_name in selected:
                result = add_team_to_project(self.project_name, team_name)
                if result["success"]:
                    self.notify(f"Added {team_name}", severity="information")
                else:
                    self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")
            self._reload()

        self.app.push_screen(SelectionListModal(available, title="Add Teams"), _handle_add)

    def action_remove_team(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal
        from hivemind_cli.core import remove_team_from_project

        team_name = self.get_current_name()
        if not team_name:
            return

        async def _do_remove(confirmed: bool) -> None:
            if confirmed:
                result = remove_team_from_project(self.project_name, team_name)
                if result["success"]:
                    self.notify(f"Removed {team_name}", severity="information")
                    self._reload()
                else:
                    self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

        self.app.push_screen(
            ConfirmationModal(
                f"Remove '{team_name}' from project '{self.project_name}'?",
                title="Remove Team",
                confirm_label="Remove",
            ),
            _do_remove,
        )

    def action_set_active(self) -> None:
        from hivemind_cli.core import set_active_project

        if self._is_active_project:
            self.notify(f"'{self.project_name}' is already active", severity="information")
            return

        result = set_active_project(self.project_name)
        if result["success"]:
            self._is_active_project = True
            self.notify(f"Active project: {self.project_name}", severity="information")
            self.query_one("#project-header", Static).update(self._format_header())
        else:
            self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

    def action_quit_or_back(self) -> None:
        self.app.pop_screen()
