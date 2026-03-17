"""Main Textual application for Hivemind TUI."""

from __future__ import annotations

import json
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.widgets import ContentSwitcher, Footer, Static

from hivemind_cli.tui.models import ExpertRow, ExpertStatus
from hivemind_cli.tui.screens.experts_pane import ExpertsPane
from hivemind_cli.tui.screens.teams_screen import TeamsPane
from hivemind_cli.tui.screens.projects_screen import ProjectsPane
from hivemind_cli.tui.widgets import SearchBar
from hivemind_cli.tui.widgets.vim_data_table import VimDataTable


TAB_ORDER = ["pane-experts", "pane-teams", "pane-projects"]
TAB_NAMES = {"pane-experts": "Experts", "pane-teams": "Teams", "pane-projects": "Projects"}


class HivemindApp(App):
    """Hivemind TUI application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Hivemind Expert Manager"
    COMMANDS = set()
    COMMAND_PALETTE_BINDING = ""

    BINDINGS = [
        Binding("h", "previous_tab", "Prev Tab", show=False),
        Binding("l", "next_tab", "Next Tab", show=False),
        Binding("tab", "next_tab", "Next Tab", show=False, priority=True),
        Binding("shift+tab", "previous_tab", "Prev Tab", show=False, priority=True),
        Binding("1", "show_tab('pane-experts')", "Experts", show=False),
        Binding("2", "show_tab('pane-teams')", "Teams", show=False),
        Binding("3", "show_tab('pane-projects')", "Projects", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.experts: list[ExpertRow] = []

        # Paths (same as CLI)
        self.hivemind_root = Path(__file__).resolve().parent.parent.parent
        self.experts_dir = self.hivemind_root / "experts"
        self.private_experts_dir = self.hivemind_root / "private-experts"
        self.agents_dir = self.hivemind_root / "agents"
        self.config_json = self.hivemind_root / "config.json"
        self.hivemind_json = self.hivemind_root / "hivemind.json"

        self._teams_loaded = False
        self._projects_loaded = False

    def compose(self) -> ComposeResult:
        yield Static("", id="tab-indicator")
        with ContentSwitcher(initial="pane-experts", id="switcher"):
            yield ExpertsPane(self.experts, id="pane-experts")
            yield TeamsPane(id="pane-teams")
            yield ProjectsPane(id="pane-projects")
        yield Footer()

    def on_mount(self) -> None:
        self.load_experts()
        try:
            pane = self.query_one(ExpertsPane)
            pane.experts = self.experts
            table = pane.query_one("#expert-table")
            table.update_experts(self.experts)
        except NoMatches:
            pass
        self._update_tab_indicator()
        self._focus_active_table()

    # --- Tab navigation ---

    def action_next_tab(self) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        idx = TAB_ORDER.index(switcher.current)
        switcher.current = TAB_ORDER[(idx + 1) % len(TAB_ORDER)]
        self._on_tab_switched()

    def action_previous_tab(self) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        idx = TAB_ORDER.index(switcher.current)
        switcher.current = TAB_ORDER[(idx - 1) % len(TAB_ORDER)]
        self._on_tab_switched()

    def action_show_tab(self, tab_id: str) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        if tab_id in TAB_ORDER:
            switcher.current = tab_id
            self._on_tab_switched()

    def _on_tab_switched(self) -> None:
        self._lazy_load_active_tab()
        self._update_tab_indicator()
        self._focus_active_table()

    def _lazy_load_active_tab(self) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        active = switcher.current

        if active == "pane-teams" and not self._teams_loaded:
            self._teams_loaded = True
            try:
                self.query_one(TeamsPane).load_teams()
            except NoMatches:
                pass

        elif active == "pane-projects" and not self._projects_loaded:
            self._projects_loaded = True
            try:
                self.query_one(ProjectsPane).load_projects()
            except NoMatches:
                pass

    def _focus_active_table(self) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        try:
            pane = self.query_one(f"#{switcher.current}")
            table = pane.query_one(VimDataTable)
            table.focus()
        except NoMatches:
            pass

    def _update_tab_indicator(self) -> None:
        switcher = self.query_one("#switcher", ContentSwitcher)
        active = switcher.current
        parts = []
        for tab_id in TAB_ORDER:
            name = TAB_NAMES[tab_id]
            if tab_id == active:
                parts.append(f"[bold]{name}[/bold]")
            else:
                parts.append(f"[dim]{name}[/dim]")
        self.query_one("#tab-indicator", Static).update("  │  ".join(parts))

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Block tab switching when a screen is pushed or search input has focus."""
        if action in ("next_tab", "previous_tab", "show_tab"):
            if len(self.screen_stack) > 1:
                return False
            try:
                for sb in self.query(SearchBar):
                    if sb.query_one("#search-input").has_focus:
                        return False
            except Exception:
                pass
        return True

    # --- Data loading ---

    def load_experts(self) -> None:
        config = self._load_config()
        repos = self._load_repos()
        private_repos = self._load_private_repos()
        private_experts = set(config.get("private", []))
        expert_names = self._expert_names()

        self.experts = []

        for name in expert_names:
            is_private = name in private_experts
            if name in config["enabled"]:
                status = ExpertStatus.ENABLED
            elif name in config["disabled"]:
                status = ExpertStatus.DISABLED
            else:
                status = ExpertStatus.UNLISTED

            expert_dir = (
                self.private_experts_dir / name if is_private
                else self.experts_dir / name
            )
            commit = self._get_head_commit(expert_dir)
            version_count = self._count_versions(expert_dir)
            has_agent = (self.agents_dir / f"expert-{name}.md").is_file()

            remote = ""
            ref_name = ""
            repos_dict = private_repos if is_private else repos
            if name in repos_dict:
                remote = repos_dict[name].get("remote", "")
                ref_name = repos_dict[name].get("ref_name", "")

            self.experts.append(
                ExpertRow(
                    name=name,
                    status=status,
                    commit=commit,
                    version_count=version_count,
                    has_agent=has_agent,
                    remote=remote,
                    ref_name=ref_name,
                    is_private=is_private,
                    operation_status=None,
                )
            )

        self.experts.sort(key=lambda e: (
            0 if e.status == ExpertStatus.ENABLED else 1,
            e.name.lower()
        ))

    def refresh_experts(self) -> None:
        self.load_experts()
        try:
            pane = self.query_one(ExpertsPane)
            pane.experts = self.experts
            table = pane.query_one("#expert-table")
            table.update_experts(self.experts)
        except (NoMatches, AttributeError):
            pass

    def load_teams(self) -> dict:
        config = self._load_config()
        return config.get("teams", {})

    def load_projects(self) -> tuple[dict, str | None]:
        config = self._load_config()
        projects = config.get("projects", {})
        active = config.get("active_project")
        return projects, active

    def _load_config(self) -> dict:
        default = {"enabled": [], "disabled": []}
        if not self.config_json.exists():
            return default
        data = json.loads(self.config_json.read_text())
        data.setdefault("enabled", [])
        data.setdefault("disabled", [])
        return data

    def _load_hivemind(self) -> dict:
        if not self.hivemind_json.exists():
            return {}
        return json.loads(self.hivemind_json.read_text())

    def _load_repos(self) -> dict:
        return self._load_hivemind().get("repos", {})

    def _load_private_repos(self) -> dict:
        private_repos_json = self.hivemind_root / "private-repos.json"
        if not private_repos_json.exists():
            return {}
        return json.loads(private_repos_json.read_text())

    def _expert_names(self) -> list[str]:
        experts = []
        if self.experts_dir.exists():
            experts.extend(d.name for d in self.experts_dir.iterdir() if d.is_dir())
        if self.private_experts_dir.exists():
            experts.extend(d.name for d in self.private_experts_dir.iterdir() if d.is_dir())
        return sorted(experts)

    def _get_head_commit(self, expert_dir: Path) -> str | None:
        head = expert_dir / "HEAD"
        if not head.is_symlink():
            return None
        return os.readlink(head)

    def _count_versions(self, expert_dir: Path) -> int:
        if not expert_dir.exists():
            return 0
        return sum(
            1
            for d in expert_dir.iterdir()
            if d.is_dir() and not d.is_symlink() and d.name != "__pycache__"
        )
