"""L2 helpers invoked after L1 domain mutations.

Any caller (CLI, TUI, MCP) that mutates expert/team state should call
``notify_opencode_reload()`` after the mutation succeeds so the opencode
server invalidates its in-process caches and all attached TUI clients pick
up the change.

Kept as a thin, explicit helper rather than a decorator on L1 functions so
``experts.py`` / ``teams.py`` stay opencode-agnostic (pure L1 domain).
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def notify_opencode_reload() -> None:
    """Best-effort: POST /global/dispose to the running opencode server.

    Fire-and-forget. Swallows connection errors — if opencode isn't running
    there is nothing to notify. Safe to call on every mutation path.
    """
    try:
        from hivemind.config import get_active_provider

        provider = get_active_provider()
        provider.notify_instance_reload()
    except Exception:
        log.exception("opencode reload notification failed")
