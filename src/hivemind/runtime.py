"""Process-wide runtime context.

Resolved once at ingress startup so downstream code reads a stable value
instead of scattering ``is_server_running()`` calls. Three modes:

- ``attached``: an opencode server is running; reload listeners post HTTP.
- ``detached``: no server running; reload listeners no-op. Mutations still
  write files, which opencode will pick up on next launch.
- ``test``: pytest-controlled; listeners no-op, filesystem confined to tmpdir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["attached", "detached", "test"]


@dataclass(frozen=True)
class RuntimeContext:
    mode: Mode
    server_url: str | None = None


_ctx: RuntimeContext | None = None


__all__ = [
    "RuntimeContext",
    "clear_context",
    "current_context",
    "detect_context",
    "set_context",
]


def set_context(ctx: RuntimeContext) -> None:
    """Explicitly set the process context (tests / ingress startup)."""
    global _ctx
    _ctx = ctx


def clear_context() -> None:
    """Forget the cached context (tests only)."""
    global _ctx
    _ctx = None


def current_context() -> RuntimeContext:
    """Return the current context, detecting it on first call if unset."""
    global _ctx
    if _ctx is None:
        _ctx = detect_context()
    return _ctx


def detect_context() -> RuntimeContext:
    """Detect whether an opencode server is running and build the context.

    Import kept lazy to avoid pulling server/httpx at module import time.
    """
    from hivemind.server import get_server_url

    url = get_server_url()
    if url is None:
        return RuntimeContext(mode="detached", server_url=None)
    return RuntimeContext(mode="attached", server_url=url)
