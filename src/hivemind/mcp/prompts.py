"""MCP prompt definitions for hivemind.

Prompts become slash commands on both OpenCode and Claude Code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.types import GetPromptResult, Prompt, PromptMessage, TextContent

if TYPE_CHECKING:
    from mcp.server import Server


def register_prompts(server: Server) -> None:
    """Register hivemind MCP prompts on the server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="hivemind-status",
                description="Show the hivemind dashboard with provider, experts, teams, and server status.",
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
        if name == "hivemind-status":
            return GetPromptResult(
                description="Hivemind status dashboard",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text="Show the current hivemind status using the status tool.",
                        ),
                    ),
                ],
            )

        msg = f"Unknown prompt: {name}"
        raise ValueError(msg)
