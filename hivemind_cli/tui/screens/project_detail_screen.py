"""Detail screen for viewing and managing a project's teams."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import VimDataTable


class ProjectDetailScreen(BaseScreen):
    """Screen showing a project's teams with add/remove/set-active actions."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        Binding("a", "add_team", "Add Team", show=True),
        Binding("D", "remove_team", "Remove", show=True),
        Binding("s", "set_active", "Set Active", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
    ]

    def __init__(self, project_name: str, project_data: dict, is_active: bool, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.project_data = project_data
        self.is_active = is_active

    def _format_header(self) -> str:
        desc = self.project_data.get("description", "")
        active = " [green]● active[/green]" if self.is_active else ""
        teams = self.project_data.get("teams", [])
        count = len(teams)
        parts = [f"[bold]{self.project_name}[/bold]{active}"]
        if desc:
            parts.append(desc)
        parts.append(f"{count} team{'s' if count != 1 else ''}")
        return "  │  ".join(parts)

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), id="project-header")
        yield VimDataTable(id="project-teams-table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#project-teams-table", VimDataTable)
        table.add_columns("Name", "Expert Count", "Description")
        table.cursor_type = "row"
        self._populate_table()
        table.focus()

    def _populate_table(self) -> None:
        table = self.query_one("#project-teams-table", VimDataTable)
        table.clear()

        all_teams = self.app.load_teams()
        project_teams = self.project_data.get("teams", [])

        for team_name in sorted(project_teams):
            team_data = all_teams.get(team_name, {})
            expert_count = len(team_data.get("experts", []))
            desc = team_data.get("description", "[dim]none[/dim]")
            table.add_row(team_name, str(expert_count), desc)

        if not project_teams:
            table.add_row("[dim]No teams[/dim]", "", "")

    def _reload(self) -> None:
        """Reload project data from config and refresh table."""
        projects, active = self.app.load_projects()
        if self.project_name in projects:
            self.project_data = projects[self.project_name]
        self.is_active = active == self.project_name
        self._populate_table()
        self.query_one("#project-header", Static).update(self._format_header())

    def action_add_team(self) -> None:
        from hivemind_cli.core import add_team_to_project

        all_teams = self.app.load_teams()
        current = set(self.project_data.get("teams", []))
        available = [n for n in sorted(all_teams) if n not in current]

        if not available:
            self.notify("No available teams to add", severity="warning")
            return

        from textual.app import ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.screen import ModalScreen
        from textual.widgets import Button, Label
        from hivemind_cli.tui.widgets.vim_data_table import VimSelectionList

        class AddTeamToProjectModal(ModalScreen[list[str] | None]):
            def compose(self) -> ComposeResult:
                with Vertical(classes="modal-body") as v:
                    v.border_title = "Add Teams"
                    yield Label("Select teams to add:")
                    yield VimSelectionList(
                        *[(n, n) for n in available],
                        id="add-team-list",
                    )
                    with Horizontal(classes="modal-buttons"):
                        yield Button("Cancel", id="cancel")
                        yield Button("Add", id="confirm", variant="primary")

            def on_mount(self) -> None:
                self._bindings.bind("escape", "dismiss_modal")
                self._bindings.bind("ctrl+o", "dismiss_modal")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "confirm":
                    selected = list(self.query_one("#add-team-list", VimSelectionList).selected)
                    self.dismiss(selected if selected else None)
                else:
                    self.dismiss(None)

            def action_dismiss_modal(self) -> None:
                self.dismiss(None)

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

        self.app.push_screen(AddTeamToProjectModal(), _handle_add)

    def action_remove_team(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal
        from hivemind_cli.core import remove_team_from_project

        project_teams = sorted(self.project_data.get("teams", []))
        table = self.query_one("#project-teams-table", VimDataTable)
        if not project_teams or table.cursor_row >= len(project_teams):
            return

        team_name = project_teams[table.cursor_row]

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

        if self.is_active:
            self.notify(f"'{self.project_name}' is already active", severity="information")
            return

        result = set_active_project(self.project_name)
        if result["success"]:
            self.is_active = True
            self.notify(f"Active project: {self.project_name}", severity="information")
            self.query_one("#project-header", Static).update(self._format_header())
        else:
            self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

    def action_quit_or_back(self) -> None:
        self.app.pop_screen()

    def action_handle_escape(self) -> None:
        self.app.pop_screen()
