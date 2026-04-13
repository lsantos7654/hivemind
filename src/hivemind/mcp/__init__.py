"""Hivemind MCP server — structured tool interface for expert management.

Run via ``hivemind mcp`` (stdio transport) or ``python -m hivemind.mcp``.
"""

from hivemind.mcp.server import create_server

__all__ = ["create_server"]
