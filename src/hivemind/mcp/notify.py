"""Hot-reload notification helpers for the hivemind MCP server.

Sends ``ToolListChangedNotification`` to connected MCP clients after
mutations so the client UI refreshes its tool list.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.lowlevel.server import Server

log = logging.getLogger(__name__)


async def notify_tools_changed(server: Server[object]) -> None:
    """Send ``ToolListChangedNotification`` to the connected MCP client."""
    try:
        ctx = server.request_context
        await ctx.session.send_tool_list_changed()
        log.debug("Sent ToolListChangedNotification")
    except LookupError:
        log.debug("No active request context; cannot send ToolListChangedNotification")
