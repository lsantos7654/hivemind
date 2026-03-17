"""Projects pane — project list content used inside the tabbed layout."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from hivemind_cli.tui.widgets.base_pane import BasePane
from hivemind_cli.tui.widgets import VimDataTable, SearchBar


class ProjectsPane(BasePane):
    """Project list pane for the tabbed layout."""

    BINDINGS = [
        *BasePane.BINDINGS,
        Binding("enter", "show_details", "Details", show=True),
        Binding("s", "set_active", "Set Active", show=True),
        Binding("D", "delete_project", "Delete", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._projects: dict = {}
        self._active_project: str | None = None

    def _get_table_id(self) -> str:
        return "projects-table"

    def _get_total_count(self) -> int:
        return len(self._projects)

    def compose(self) -> ComposeResult:
        yield Static("", classes="filter-indicator")
        yield SearchBar()
        yield VimDataTable(id="projects-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self._get_table()
        table.add_columns("Name", "Active", "Teams", "Description")
        table.cursor_type = "row"
        table.focus()

    def load_projects(self) -> None:
        self._projects, self._active_project = self.app.load_projects()
        self._populate_table()
        self._update_filter_indicator()

    def _populate_table(self) -> None:
        table = self._get_table()
        table.clear()
        self._visible_names = []

        for name, data in sorted(self._projects.items()):
            if self._filter_query:
                query = self._filter_query.lower()
                if query not in name.lower() and query not in data.get("description", "").lower():
                    continue

            active = "[green]●[/green]" if name == self._active_project else "[dim]○[/dim]"
            teams = ", ".join(data.get("teams", [])) or "[dim]none[/dim]"
            description = data.get("description", "[dim]none[/dim]")

            table.add_row(name, active, teams, description)
            self._visible_names.append(name)

        if not self._visible_names:
            if self._filter_query:
                table.add_row(f"[dim]No results for \"{self._filter_query}\"[/dim]", "", "", "")
            elif not self._projects:
                table.add_row("[dim]No projects[/dim]", "", "", "")

    def action_show_details(self) -> None:
        name = self.get_current_name()
        if name:
            self.notify(f"Project: {name}", severity="information")

    def action_set_active(self) -> None:
        from hivemind_cli.core import set_active_project

        name = self.get_current_name()
        if not name:
            return

        if name == self._active_project:
            self.notify(f"'{name}' is already active", severity="information")
            return

        result = set_active_project(name)
        if result["success"]:
            self.notify(f"Active project: {name}", severity="information")
            self.load_projects()
        else:
            self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

    def action_delete_project(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal
        from hivemind_cli.core import delete_project

        name = self.get_current_name()
        if not name:
            return

        async def _do_delete(confirmed: bool) -> None:
            if confirmed:
                result = delete_project(name)
                if result["success"]:
                    self.notify(f"Deleted project: {name}", severity="information")
                    self.load_projects()
                else:
                    self.notify(f"Failed: {result.get('error', 'Unknown')}", severity="error")

        self.app.push_screen(
            ConfirmationModal(
                f"Delete project '{name}'?",
                title="Delete Project",
                confirm_label="Delete",
            ),
            _do_delete,
        )
