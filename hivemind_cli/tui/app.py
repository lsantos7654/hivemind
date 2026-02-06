"""Main Textual application for Hivemind TUI."""

from __future__ import annotations

import json
import os
from pathlib import Path

from textual.app import App
from textual.css.query import NoMatches

from hivemind_cli.tui.models import ExpertRow, ExpertStatus
from hivemind_cli.tui.screens import MainScreen


class HivemindApp(App):
    """Hivemind TUI application."""

    CSS_PATH = "styles.tcss"
    TITLE = "Hivemind Expert Manager"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.experts: list[ExpertRow] = []

        # Paths (same as CLI)
        self.hivemind_root = Path(__file__).resolve().parent.parent.parent
        self.experts_dir = self.hivemind_root / "experts"
        self.agents_dir = self.hivemind_root / "agents"
        self.config_json = self.hivemind_root / "config.json"
        self.repos_json = self.hivemind_root / "repos.json"

    def on_mount(self) -> None:
        """Load data and show main screen when app mounts."""
        self.load_experts()
        self.push_screen(MainScreen(self.experts))

    def load_experts(self) -> None:
        """Load expert data from config and repos.json."""
        config = self._load_config()
        repos = self._load_repos()
        expert_names = self._expert_names()

        self.experts = []

        for name in expert_names:
            # Determine status
            if name in config["enabled"]:
                status = ExpertStatus.ENABLED
            elif name in config["disabled"]:
                status = ExpertStatus.DISABLED
            else:
                status = ExpertStatus.UNLISTED

            # Get HEAD commit
            expert_dir = self.experts_dir / name
            commit = self._get_head_commit(expert_dir)

            # Count versions
            version_count = self._count_versions(expert_dir)

            # Check if agent exists
            has_agent = (self.agents_dir / f"expert-{name}.md").is_file()

            # Get remote info
            remote = ""
            ref_name = ""
            if name in repos:
                remote = repos[name].get("remote", "")
                ref_name = repos[name].get("ref_name", "")

            self.experts.append(
                ExpertRow(
                    name=name,
                    status=status,
                    commit=commit,
                    version_count=version_count,
                    has_agent=has_agent,
                    remote=remote,
                    ref_name=ref_name,
                    operation_status=None,
                )
            )

        # Sort: enabled first, then alphabetically by name
        self.experts.sort(key=lambda e: (
            0 if e.status == ExpertStatus.ENABLED else 1,  # Enabled first
            e.name.lower()  # Then alphabetically
        ))

    def refresh_experts(self) -> None:
        """Reload expert data and update the screen."""
        self.load_experts()
        try:
            main_screen = self.screen
            if isinstance(main_screen, MainScreen):
                # Update the main screen's expert list
                main_screen.experts = self.experts
                # Update the table
                table = main_screen.query_one("#expert-table")
                table.update_experts(self.experts)
        except (NoMatches, AttributeError):
            pass

    def _load_config(self) -> dict:
        """Load config.json."""
        default = {"enabled": [], "disabled": []}
        if not self.config_json.exists():
            return default
        data = json.loads(self.config_json.read_text())
        data.setdefault("enabled", [])
        data.setdefault("disabled", [])
        return data

    def _load_repos(self) -> dict:
        """Load repos.json."""
        if not self.repos_json.exists():
            return {}
        return json.loads(self.repos_json.read_text())

    def _expert_names(self) -> list[str]:
        """List all expert names from experts/ directory."""
        if not self.experts_dir.exists():
            return []
        return sorted(d.name for d in self.experts_dir.iterdir() if d.is_dir())

    def _get_head_commit(self, expert_dir: Path) -> str | None:
        """Read the HEAD symlink to get the current commit hash."""
        head = expert_dir / "HEAD"
        if not head.is_symlink():
            return None
        return os.readlink(head)

    def _count_versions(self, expert_dir: Path) -> int:
        """Count commit directories (excludes HEAD symlink)."""
        if not expert_dir.exists():
            return 0
        return sum(
            1
            for d in expert_dir.iterdir()
            if d.is_dir() and not d.is_symlink() and d.name != "__pycache__"
        )
