"""Base screen with worker management for push-screen views (e.g. VersionDetailScreen)."""

from __future__ import annotations

from textual.binding import Binding
from textual.screen import Screen


class BaseScreen(Screen):
    """Base screen providing worker management for async operations."""

    BINDINGS = [
        Binding("escape", "handle_escape", "Back/Clear", show=True),
        Binding("ctrl+c", "handle_escape", "Back/Clear", show=False),
        Binding("ctrl+o", "go_back", "Back", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_workers: dict[str, dict] = {}

    def register_worker(self, expert_name: str, token) -> None:
        """Register active worker for an expert."""
        self._active_workers[expert_name] = {"token": token, "pid": None}

    def register_subprocess_pid(self, expert_name: str, pid: int) -> None:
        """Register subprocess PID for cancellation."""
        if expert_name in self._active_workers:
            self._active_workers[expert_name]["pid"] = pid

    def unregister_worker(self, expert_name: str) -> None:
        """Remove worker from registry."""
        self._active_workers.pop(expert_name, None)

    def get_worker_info(self, expert_name: str) -> dict | None:
        """Get worker info for an expert."""
        return self._active_workers.get(expert_name)

    def action_handle_escape(self) -> None:
        """Override in subclass for screen-specific escape behavior."""

    def action_go_back(self) -> None:
        """Go back one screen."""
        self.app.pop_screen()
