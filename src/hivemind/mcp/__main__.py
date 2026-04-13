"""Entry point for ``python -m hivemind.mcp`` and ``hivemind mcp``."""

from __future__ import annotations

import asyncio
import logging
import sys


def main() -> None:
    """Run the hivemind MCP server on stdio."""
    # Configure logging to stderr (stdout is reserved for MCP JSON-RPC)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    from mcp.server.stdio import stdio_server

    from hivemind.mcp.server import create_server

    server = create_server()

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_run())


if __name__ == "__main__":
    main()
