"""Hivemind MCP server — structured tool interface for expert and team management.

This module creates an MCP ``Server`` instance with tools that wrap the existing
hivemind core modules (experts.py, teams.py, deployment.py, config.py).
"""

from __future__ import annotations

import logging

from mcp.server import Server

from hivemind.mcp.prompts import register_prompts
from hivemind.mcp.tools import register_tools

log = logging.getLogger(__name__)


def create_server() -> Server:
    """Create and configure the hivemind MCP server.

    Returns a Server instance ready to be run with ``stdio_server()``.
    """
    server: Server = Server("hivemind")

    # Register all tool and prompt handlers
    register_tools(server)
    register_prompts(server)

    log.debug("Hivemind MCP server created with tools and prompts registered")
    return server


__all__ = ["create_server"]
