"""Hot-reload notification helpers for the hivemind MCP server.

Sends ToolListChangedNotification to connected MCP clients and optionally
triggers POST /instance/dispose on the OpenCode server to invalidate the
subagent .md file cache.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.lowlevel.server import Server

    from hivemind.providers.base import Provider

log = logging.getLogger(__name__)


async def notify_tools_changed(server: Server[object]) -> None:
    """Send ToolListChangedNotification to the connected MCP client.

    Call this after any operation that changes the tool list (adding/removing
    experts, creating/deleting teams, redeploy, etc.).
    """
    try:
        ctx = server.request_context
        await ctx.session.send_tool_list_changed()
        log.debug("Sent ToolListChangedNotification")
    except LookupError:
        log.debug("No active request context; cannot send ToolListChangedNotification")


def notify_instance_reload(provider: Provider) -> bool:
    """Trigger agent cache reload on the running provider server.

    This handles the subagent .md file hot-reload — the provider-specific
    mechanism (e.g. POST /instance/dispose for OpenCode) that forces the
    platform to re-scan agent files from disk.

    Returns True if notification was sent successfully.
    """
    result = provider.notify_instance_reload()
    if result:
        log.debug("Instance reload notification sent to %s", provider.name)
    return result
