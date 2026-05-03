"""Unified ``Agent`` abstraction with a pluggable body strategy.

All hivemind agents — experts, team leads, and future kinds — share this
shape. An ``Agent`` carries identity (name + enabled flag) and deploy
mechanics; an ``AgentBody`` strategy handles how the markdown body is
produced and how kind-specific side effects (cloning repos, managing
team dirs, …) play out at deploy / undeploy / delete time.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from hivemind import opencode

if TYPE_CHECKING:
    from collections.abc import Coroutine

_T = TypeVar("_T")


def run_coro_sync(coro: Coroutine[Any, Any, _T]) -> _T:
    """Run an async coroutine from a synchronous caller, even if that caller
    is itself nested inside a running event loop.

    ``enable_agent`` and related lifecycle verbs are sync — they're called
    from CLI top-level (no loop) and from MCP tool handlers (loop running).
    A bare ``asyncio.run`` works for the first case but raises
    ``RuntimeError: asyncio.run() cannot be called from a running event
    loop`` for the second. This helper detects the situation and offloads
    to a short-lived worker thread when needed.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(asyncio.run, coro).result()


@runtime_checkable
class AgentBody(Protocol):
    """Strategy for producing and maintaining an agent's deployable body."""

    kind: str

    def render(self) -> str:
        """Produce the canonical markdown body for this agent."""
        ...

    def description(self) -> str:
        """Return the one-paragraph description used for agent frontmatter."""
        ...

    def librarian_entry(self) -> str:
        """One agent's entry for the librarian catalog."""
        ...

    def on_deploy(self) -> None:
        """Body-specific deploy side effects (clone, symlink, …)."""
        ...

    def on_undeploy(self) -> None:
        """Inverse of ``on_deploy``; preserves persistent backing state."""
        ...

    def on_delete(self) -> None:
        """Delete backing files for this body (called only on full delete)."""
        ...

    def to_catalog(self) -> dict[str, Any]:
        """Serialize body params for ``hivemind.json`` catalog entries."""
        ...


@dataclass
class Agent:
    """A deployable hivemind agent."""

    name: str
    body: AgentBody
    enabled: bool = False

    @property
    def kind(self) -> str:
        return self.body.kind

    @property
    def description(self) -> str:
        return self.body.description()

    def render_for_deploy(self) -> str:
        """Body + appended memory-instructions section.

        ``user_supplied`` agents skip the memory append because the
        user owns the entire markdown — injecting hivemind's memory
        rules into a hand-authored agent file would clobber the
        author's intent. They can opt in by writing the rules into
        their file directly.
        """
        from hivemind.agents.memory import render_memory_section

        body = self.body.render()
        if self.kind == "user_supplied":
            return body
        memory_section = render_memory_section(self.name, self.kind)
        return body.rstrip() + "\n\n" + memory_section

    def deploy(self, *, agents_dir: object) -> None:
        """Write the formatted agent file + run body-specific deploy."""
        from pathlib import Path

        from hivemind.agents.memory import ensure_agent_memory

        # Memory tree is hivemind-managed; ``user_supplied`` agents are
        # external to hivemind's expert/team mental model, so we don't
        # scaffold one for them. They can manage their own state under
        # whatever path they prefer.
        if self.kind != "user_supplied":
            ensure_agent_memory(self.name)

        content = opencode.format_agent(
            self.kind,  # type: ignore[arg-type]
            self.name,
            self.description,
            self.render_for_deploy(),
        )
        opencode.write_agent_file(
            self.kind,  # type: ignore[arg-type]
            self.name,
            content,
            agents_dir=agents_dir if isinstance(agents_dir, Path) else Path(str(agents_dir)),
        )
        self.body.on_deploy()

    def undeploy(self, *, agents_dir: object) -> None:
        """Remove the deployed agent file + run body-specific undeploy."""
        from pathlib import Path

        opencode.remove_agent_file(
            self.kind,  # type: ignore[arg-type]
            self.name,
            agents_dir=agents_dir if isinstance(agents_dir, Path) else Path(str(agents_dir)),
        )
        self.body.on_undeploy()
