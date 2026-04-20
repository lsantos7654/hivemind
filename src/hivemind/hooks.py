"""Post-mutation hook registry.

Every domain mutation (enable_agent, disable_agent, create_git_expert, …)
calls ``fire_post_mutation()`` / ``await afire_post_mutation()`` at its
success tail. Each ingress (CLI, TUI, MCP) registers its own listener
once at startup — CLI posts reload synchronously; TUI posts reload + pane
refresh; MCP schedules a 500 ms-deferred reload so the in-flight tool
result isn't cancelled.

Per-listener exceptions are caught and logged — one bad subscriber cannot
break a mutation.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import TypeAlias

log = logging.getLogger(__name__)

Listener: TypeAlias = Callable[[], None] | Callable[[], Awaitable[None]]

_listeners: list[Listener] = []


__all__ = [
    "afire_post_mutation",
    "clear_post_mutation",
    "fire_post_mutation",
    "register_post_mutation",
]


def register_post_mutation(listener: Listener) -> None:
    """Register a listener to run after every successful domain mutation."""
    _listeners.append(listener)


def clear_post_mutation() -> None:
    """Remove all registered listeners (tests only)."""
    _listeners.clear()


def fire_post_mutation() -> None:
    """Synchronously fire the post-mutation event.

    Called from sync mutation functions. Async listeners are scheduled via
    ``asyncio.create_task`` if a running loop is present; otherwise executed
    inline via ``asyncio.run``. Sync listeners run inline.
    """
    for listener in _listeners:
        try:
            result = listener()
            if inspect.isawaitable(result):
                _drive_awaitable(result)
        except Exception:
            log.exception("post-mutation listener failed: %r", listener)


async def afire_post_mutation() -> None:
    """Async fire — awaits async listeners inline, calls sync listeners directly."""
    for listener in _listeners:
        try:
            result = listener()
            if inspect.isawaitable(result):
                await result
        except Exception:
            log.exception("post-mutation listener failed: %r", listener)


def _drive_awaitable(awaitable: Awaitable[None]) -> None:
    """Run an awaitable from sync code.

    If a loop is already running in this thread, schedule it as a detached
    task so the sync caller returns immediately. Otherwise spin up a
    short-lived loop to drain it.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_wrap(awaitable))
        return

    task = loop.create_task(_wrap(awaitable))
    # Keep a reference so the task isn't GC'd mid-flight.
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _wrap(awaitable: Awaitable[None]) -> None:
    try:
        await awaitable
    except Exception:
        log.exception("post-mutation async listener failed")


_background_tasks: set[asyncio.Task[None]] = set()
