"""Main Textual application for Hivemind TUI."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.css.query import NoMatches
from textual.widgets import ContentSwitcher, Footer, Static

from hivemind import opencode
from hivemind.agents import registry
from hivemind.config import (
    AGENTS_DIR,
    count_versions,
    get_expert_dir,
    get_head_commit,
)
from hivemind.hooks import register_post_mutation
from hivemind.tui.models import ExpertRow, ExpertStatus
from hivemind.tui.screens.experts_pane import ExpertsPane
from hivemind.tui.screens.teams_screen import TeamsPane
from hivemind.tui.widgets import SearchBar
from hivemind.tui.widgets.vim_data_table import VimDataTable

if TYPE_CHECKING:
    from hivemind.models import TeamData

TAB_ORDER = ["pane-experts", "pane-teams"]
TAB_NAMES = {"pane-experts": "Experts", "pane-teams": "Teams"}


class HivemindApp(App):
    """Hivemind TUI application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Hivemind Expert Manager"
    COMMANDS: ClassVar[set[type]] = set()
    COMMAND_PALETTE_BINDING = ""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("h", "previous_tab", "Prev Tab", show=False),
        Binding("l", "next_tab", "Next Tab", show=False),
        Binding("tab", "next_tab", "Next Tab", show=False, priority=True),
        Binding("shift+tab", "previous_tab", "Prev Tab", show=False, priority=True),
        Binding("1", "show_tab('pane-experts')", "Experts", show=False),
        Binding("2", "show_tab('pane-teams')", "Teams", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.experts: list[ExpertRow] = []
        self._teams_loaded = False

    def compose(self) -> ComposeResult:
        yield Static("", id="tab-indicator")
        with ContentSwitcher(initial="pane-experts", id="switcher"):
            yield ExpertsPane(self.experts, id="pane-experts")
            yield TeamsPane(id="pane-teams")
        yield Footer()

    def on_mount(self) -> None:
        self._register_post_mutation_listeners()
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

    def _register_post_mutation_listeners(self) -> None:
        """Register the TUI's post-mutation listeners: reload + pane refresh."""

        def reload_listener() -> None:
            opencode.notify_instance_reload()

        def refresh_listener() -> None:
            # Called synchronously from any thread; Textual refresh is safe to
            # call via call_from_thread if we're off-thread.
            try:
                self.call_from_thread(self.refresh_experts)
            except Exception:
                # If we're already on the app thread (rare), fall back.
                self.refresh_experts()

        register_post_mutation(reload_listener)
        register_post_mutation(refresh_listener)

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
            with contextlib.suppress(NoMatches):
                self.query_one(TeamsPane).load_teams()

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
        from hivemind.agents.git_analyzed import GitAnalyzedBody

        registry.load(refresh=True)
        git_experts = registry.by_kind("git_analyzed")

        self.experts = []
        for agent in git_experts:
            if not isinstance(agent.body, GitAnalyzedBody):
                continue

            status = ExpertStatus.ENABLED if agent.enabled else ExpertStatus.DISABLED

            expert_dir = get_expert_dir(agent.name)
            commit = get_head_commit(expert_dir)
            version_count = count_versions(expert_dir)
            has_agent = (AGENTS_DIR / f"expert-{agent.name}.md").is_file()

            self.experts.append(
                ExpertRow(
                    name=agent.name,
                    status=status,
                    commit=commit,
                    version_count=version_count,
                    has_agent=has_agent,
                    remote=agent.body.remote,
                    ref_name=agent.body.ref_name,
                    is_private=False,
                    operation_status=None,
                ),
            )

        self.experts.sort(key=lambda e: (0 if e.status == ExpertStatus.ENABLED else 1, e.name.lower()))

    def refresh_experts(self) -> None:
        self.load_experts()
        try:
            pane = self.query_one(ExpertsPane)
            pane.experts = self.experts
            table = pane.query_one("#expert-table")
            table.update_experts(self.experts)
        except (NoMatches, AttributeError):
            pass

    def load_teams(self) -> dict[str, TeamData]:
        """Return all teams as ``{name: TeamData}`` for display callers."""
        from hivemind.models import TeamData

        registry.load(refresh=True)
        teams = registry.by_kind("roster_templated")
        result: dict[str, TeamData] = {}
        for agent in teams:
            body_params = agent.body.to_catalog()
            result[agent.name] = TeamData(
                description=str(body_params.get("description", "")),
                experts=[str(e) for e in body_params.get("experts", [])],
            )
        return result
