"""Claude Code platform provider."""

from __future__ import annotations

import json
import shlex
from typing import TYPE_CHECKING

from hivemind.models import InitResult
from hivemind.providers.base import Provider, yaml_escape_double_quoted
from hivemind.templates import LIBRARIAN_DESCRIPTION

if TYPE_CHECKING:
    from pathlib import Path


class ClaudeProvider(Provider):
    """Claude Code platform provider."""

    @property
    def name(self) -> str:
        return "claude"

    @property
    def rules_file_name(self) -> str:
        return "CLAUDE.md"

    # --- Formatting ---

    def _build_claude_frontmatter(
        self,
        *,
        agent_name: str,
        description: str,
        tools: list[str],
        body: str,
    ) -> str:
        """Build a complete Claude Code agent file with YAML frontmatter.

        Args:
            agent_name: Agent name for frontmatter (e.g. "expert-bazel", "team-lead-nix")
            description: Agent description
            tools: Tool names as list[str] (Claude's native format)
            body: Markdown body (will be path-transformed)
        """
        tools_str = ", ".join(tools)
        escaped = yaml_escape_double_quoted(description)
        frontmatter = (
            f'---\nname: {agent_name}\ndescription: "{escaped}"\ntools: {tools_str}\nmodel: {self.model}\n---\n\n'
        )
        return frontmatter + self._transform_body(body)

    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Format agent.md with Claude Code YAML frontmatter."""
        return self._build_claude_frontmatter(
            agent_name=f"expert-{name}",
            description=description,
            tools=list(self._settings.tools),
            body=body,
        )

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format a lead agent file with extra Edit tool."""
        tools = list(self._settings.tools)
        if "Edit" not in tools:
            tools.append("Edit")
        return self._build_claude_frontmatter(
            agent_name=agent_name,
            description=description,
            tools=tools,
            body=body,
        )

    def format_librarian_md(self, body: str) -> str:
        """Format librarian agent with read-only tools."""
        tools = [t for t in self._settings.tools if t in ("Read", "Grep", "Glob")]
        if not tools:
            tools = ["Read", "Grep", "Glob"]
        return self._build_claude_frontmatter(
            agent_name="librarian",
            description=LIBRARIAN_DESCRIPTION,
            tools=tools,
            body=body,
        )

    # --- Analysis engine ---

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
        write: bool = False,
    ) -> list[str]:
        """Build claude -p command for analysis."""
        cmd = shlex.split(self._engine)

        # Add tools — only include Write when the task needs file access
        analysis_tools = list(self._settings.tools)
        if write and "Write" not in analysis_tools:
            analysis_tools.append("Write")
        if not write:
            analysis_tools = [t for t in analysis_tools if t != "Write"]
        # Strip MCP tools for analysis (they're for runtime, not analysis)
        analysis_tools = [t for t in analysis_tools if not t.startswith("mcp__")]
        cmd.extend(["--allowedTools", ",".join(analysis_tools)])

        # Add model
        cmd.extend(["--model", self.model])

        # Add extra directories
        if extra_dirs:
            for d in extra_dirs:
                cmd.extend(["--add-dir", str(d)])

        return cmd

    def build_query_command(self) -> list[str]:
        """Build claude -p command for librarian queries."""
        cmd = shlex.split(self._engine)
        return [cmd[0], "-p", "--model", self.model]

    # --- Init ---

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Generate settings.json from permissions config."""
        results: list[InitResult] = []

        if permissions:
            settings_path = self._home_dir / "settings.json"
            # Remove old symlink if present
            if settings_path.is_symlink():
                settings_path.unlink()
            settings_data = {
                "permissions": permissions,
                "env": {
                    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
                },
            }
            settings_path.write_text(json.dumps(settings_data, indent=2) + "\n")
            results.append(InitResult(label="settings.json", status="generated from hivemind.json"))

        return results
