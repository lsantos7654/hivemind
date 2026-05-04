"""``UserSuppliedBody`` — body strategy for user-authored agent files.

A user drops a markdown file at ``opencode/agents/<name>.md``, and on
``hivemind redeploy`` the file is auto-registered in the catalog as a
``user_supplied`` agent. The deployed body is the file content
verbatim — no AI analysis, no Jinja templating, no memory section
appended. The user owns both the body and the YAML frontmatter.

Auto-sync is one-directional: dropping a file in adds the entry,
removing the file removes the entry on the next redeploy. Enable /
disable still flows through ``config.json`` like every other agent.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from hivemind.config import OPENCODE_DIR
from hivemind.models import UserSuppliedParams

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)


__all__ = [
    "USER_AGENTS_DIR",
    "UserSuppliedBody",
    "sync_user_supplied_agents",
]


# Where users drop ``<name>.md`` files. Symlinked into
# ``~/.config/opencode/agents/`` indirectly via the catalog deploy
# (each enabled file produces an ``agents/<name>.md`` under
# ``HIVEMIND_ROOT/agents/`` that the existing init_dirs symlink
# exposes to opencode).
USER_AGENTS_DIR = OPENCODE_DIR / "agents"


# ---------------------------------------------------------------------------
# Body strategy
# ---------------------------------------------------------------------------


class UserSuppliedBody:
    """Body strategy for user-authored markdown agents.

    The user controls the entire markdown file (frontmatter + body).
    Hivemind copies it through verbatim on deploy.
    """

    kind: str = "user_supplied"

    def __init__(self, name: str, params: UserSuppliedParams) -> None:
        self.name = name
        self.params = params

    # --- catalog (de)serialisation -----------------------------------------

    @classmethod
    def from_catalog(cls, name: str, params: dict[str, Any]) -> UserSuppliedBody:
        return cls(name=name, params=UserSuppliedParams.model_validate(params))

    def to_catalog(self) -> dict[str, Any]:
        return self.params.model_dump()

    # --- body protocol -----------------------------------------------------

    def _source_path(self) -> Path:
        return USER_AGENTS_DIR / self.params.filename

    def description(self) -> str:
        """Pull ``description`` out of the file's YAML frontmatter.

        Returns an empty string if the file has no frontmatter or no
        description field. ``format_agent`` for ``user_supplied`` does
        not consume this — the user's frontmatter already carries it —
        but ``Agent.description`` is also used by ``librarian_entry``
        callers, so we surface it here.
        """
        text = self._read()
        return _frontmatter_field(text, "description") or ""

    def render(self) -> str:
        """Return the file content verbatim."""
        return self._read()

    def memory_enabled(self) -> bool:
        """Whether hivemind should scaffold + reference a memory tree for this agent.

        Reads ``memory:`` from the file's YAML frontmatter. Defaults to
        ``False`` — user_supplied agents are external to hivemind's
        expert/team mental model (see ``Agent.deploy`` docstring), so the
        memory tree is opt-in rather than opt-out for this kind. Set
        ``memory: true`` in the frontmatter to opt in (which also causes
        ``Agent.render_for_deploy`` to append the memory section to the
        agent's prompt).
        """
        flag = _frontmatter_field(self._read(), "memory")
        if flag is None:
            return False
        return flag.strip().lower() in ("true", "yes", "on", "1")

    def librarian_entry(self) -> str:
        desc = self.description() or "(no description)"
        return (
            f"### {self.name}\n"
            f"User-supplied agent. {desc}\n"
            f"Source: ``opencode/agents/{self.params.filename}`` (edit and "
            f"``hivemind redeploy`` to update)."
        )

    def on_deploy(self) -> None:
        # No backing-dir setup. The agents/<name>.md file written by
        # Agent.deploy() is the entire deployment.
        pass

    def on_undeploy(self) -> None:
        pass

    def on_delete(self) -> None:
        # The source file under opencode/agents/ is owned by the user.
        # Don't touch it on `delete_agent` — they may want to re-add later.
        pass

    # --- helpers -----------------------------------------------------------

    def _read(self) -> str:
        path = self._source_path()
        if not path.exists():
            log.warning("user-supplied agent source missing: %s", path)
            return ""
        return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Auto-sync (called from lifecycle.bootstrap_workspace + redeploy_all_agents)
# ---------------------------------------------------------------------------


def sync_user_supplied_agents() -> None:
    """Reconcile the catalog with files under ``opencode/agents/``.

    - File present, not in catalog → add as ``user_supplied`` (unlisted).
    - File present, in catalog as ``user_supplied`` → no-op.
    - Catalog entry is ``user_supplied`` + file gone → remove from catalog.
    - Name collision with another kind → skip with a warning (existing
      catalog entry wins; the user's file is ignored until they rename or
      remove the conflicting entry).

    Idempotent. Safe to call on every redeploy.
    """
    from hivemind.agents import registry
    from hivemind.agents.base import Agent

    if not USER_AGENTS_DIR.exists():
        return

    on_disk: dict[str, str] = {}
    for path in USER_AGENTS_DIR.glob("*.md"):
        if path.name.lower() == "readme.md":
            continue
        on_disk[path.stem] = path.name

    for stem, filename in on_disk.items():
        existing = registry.get(stem)
        if existing is None:
            body = UserSuppliedBody(name=stem, params=UserSuppliedParams(filename=filename))
            registry.add(Agent(name=stem, body=body, enabled=False))
            continue
        if not isinstance(existing.body, UserSuppliedBody):
            log.warning(
                "user-supplied agent %r collides with existing %s entry; skipping",
                stem,
                existing.body.kind,
            )

    for agent in registry.by_kind("user_supplied"):
        if agent.name not in on_disk:
            registry.remove(agent.name)


# ---------------------------------------------------------------------------
# Frontmatter helper
# ---------------------------------------------------------------------------


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)


def _frontmatter_field(text: str, field: str) -> str | None:
    """Extract a single top-level YAML field from the frontmatter.

    Tolerates simple ``key: value`` entries (no nested structures).
    Multi-line scalar values are not supported — keep the description
    on one line. Returns ``None`` if no frontmatter or no matching
    field is found.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    for line in m.group("body").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key.strip() == field:
            return value.strip().strip("'\"")
    return None
