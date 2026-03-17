"""Detail screen for viewing and managing a team's roster."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static

from hivemind_cli.tui.screens.base_screen import BaseScreen
from hivemind_cli.tui.widgets import VimDataTable


class TeamDetailScreen(BaseScreen):
    """Screen showing a team's experts with add/remove actions."""

    BINDINGS = [
        *BaseScreen.BINDINGS,
        Binding("a", "add_expert", "Add Expert", show=True),
        Binding("D", "remove_expert", "Remove", show=True),
        Binding("q", "quit_or_back", "Back", show=True),
    ]

    def __init__(self, team_name: str, team_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.team_name = team_name
        self.team_data = team_data

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
        yield VimDataTable(id="team-roster-table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#team-roster-table", VimDataTable)
        table.add_columns("Name", "Status")
        table.cursor_type = "row"
        self._populate_table()
        table.focus()

    def _populate_table(self) -> None:
        table = self.query_one("#team-roster-table", VimDataTable)
        table.clear()

        config = self.app._load_config()
        enabled = set(config.get("enabled", []))

        for expert_name in sorted(self.team_data.get("experts", [])):
            status = "[green]enabled[/green]" if expert_name in enabled else "[dim]disabled[/dim]"
            table.add_row(expert_name, status)

        if not self.team_data.get("experts"):
            table.add_row("[dim]No experts[/dim]", "")

    def _reload(self) -> None:
        """Reload team data from config and refresh table."""
        teams = self.app.load_teams()
        if self.team_name in teams:
            self.team_data = teams[self.team_name]
        self._populate_table()
        self.query_one("#team-header", Static).update(self._format_header())

    def action_add_expert(self) -> None:
        from hivemind_cli.tui.widgets.confirmation_modal import ConfirmationModal
        from hivemind_cli.core import add_expert_to_team

        # Get experts not already on the team
        all_experts = [e.name for e in self.app.experts]
        current = set(self.team_data.get("experts", []))
        available = [n for n in all_experts if n not in current]

        if not available:
            self.notify("No available experts to add", severity="warning")
            return

        # Use a simple SelectionList modal
        from textual.app import ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.screen import ModalScreen
        from textual.widgets import Button, Label
        from hivemind_cli.tui.widgets.vim_data_table import VimSelectionList

        class AddExpertToTeamModal(ModalScreen[list[str] | None]):
            def compose(self) -> ComposeResult:
                with Vertical(classes="modal-body") as v:
                    v.border_title = "Add Experts"
                    yield Label("Select experts to add:")
                    yield VimSelectionList(
                        *[(n, n) for n in available],
                        id="add-expert-list",
                    )
                    with Horizontal(classes="modal-buttons"):
                        yield Button("Cancel", id="cancel")
                        yield Button("Add", id="confirm", variant="primary")

            def on_mount(self) -> None:
                self._bindings.bind("escape", "dismiss_modal")
                self._bindings.bind("ctrl+o", "dismiss_modal")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "confirm":
                    selected = list(self.query_one("#add-expert-list", VimSelectionList).selected)
                    self.dismiss(selected if selected else None)
                else:
                    self.dismiss(None)

            def action_dismiss_modal(self) -> None:
                self.dismiss(None)

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

        self.app.push_screen(AddExpertToTeamModal(), _handle_add)

    def action_remove_expert(self) -> None:
        from hivemind_cli.tui.widgets import ConfirmationModal
        from hivemind_cli.core import remove_expert_from_team

        table = self.query_one("#team-roster-table", VimDataTable)
        experts = sorted(self.team_data.get("experts", []))
        if not experts or table.cursor_row >= len(experts):
            return

        expert_name = experts[table.cursor_row]

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

    def action_handle_escape(self) -> None:
        self.app.pop_screen()
