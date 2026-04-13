"""OpenCode platform provider."""

from __future__ import annotations

import contextlib
import json
import logging
import shlex
import subprocess
from typing import TYPE_CHECKING, Any

import httpx

from hivemind.constants import DEFAULT_TEMPERATURE, ENGINE_VALIDATION_TIMEOUT
from hivemind.models import InitResult, OperationResult
from hivemind.providers.base import Provider, yaml_escape_double_quoted
from hivemind.templates import LIBRARIAN_DESCRIPTION, opencode_branding_plugin

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)


class OpenCodeProvider(Provider):
    """OpenCode platform provider."""

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def rules_file_name(self) -> str:
        return "AGENTS.md"

    def validate_engine(self) -> OperationResult:
        """Validate engine binary and model availability for OpenCode."""
        base = super().validate_engine()
        if not base.success:
            return base

        # Check the configured model is actually accessible
        binary = shlex.split(self._engine)[0]
        try:
            result = subprocess.run(
                [binary, "models"],
                capture_output=True,
                text=True,
                timeout=ENGINE_VALIDATION_TIMEOUT,
                check=False,
            )
        except FileNotFoundError:
            return OperationResult(
                success=False,
                error=f"Engine binary '{binary}' not found.",
            )
        except subprocess.TimeoutExpired:
            return OperationResult(
                success=False,
                error=f"Model validation timed out ({binary} models). Check that opencode is responsive.",
            )

        if result.returncode != 0:
            return OperationResult(
                success=False,
                error=f"Failed to query available models: {result.stderr.strip()[:200]}",
            )

        # Check if the configured model appears in the output (exact match per line)
        available = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        model = self._settings.model
        if model and model not in available:
            return OperationResult(
                success=False,
                error=f"Model '{model}' not available. "
                f"Run 'opencode providers' to configure it.\n"
                f"Available models can be listed with 'opencode models'.",
            )

        return OperationResult(success=True)

    # --- Formatting ---

    def _build_opencode_frontmatter(
        self,
        *,
        description: str,
        tools: dict[str, bool],
        extra_permissions: list[str] | None = None,
        body: str,
    ) -> str:
        """Build a complete OpenCode agent file with YAML frontmatter.

        Args:
            description: Agent description
            tools: Tool permissions as dict[str, bool] (OpenCode's native format)
            extra_permissions: Additional permission path patterns
            body: Markdown body (will be path-transformed)
        """
        temperature = self._settings.temperature if self._settings.temperature is not None else DEFAULT_TEMPERATURE

        lines = [
            "---",
            f'description: "{yaml_escape_double_quoted(description)}"',
            "mode: subagent",
            f"model: {self.model}",
            f"temperature: {temperature}",
        ]

        if tools:
            lines.append("tools:")
            for tool_name, enabled in sorted(tools.items()):
                lines.append(f"  {tool_name}: {str(enabled).lower()}")

        # Permissions for hivemind paths
        lines.append("permission:")
        lines.append("  external_directory:")
        lines.append(f'    "{self.cache_base_path}/**": allow')
        lines.append(f'    "{self.experts_base_path}/**": allow')
        if extra_permissions:
            lines.extend(f"    {perm}" for perm in extra_permissions)

        lines.append("---")
        lines.append("")
        lines.append("")

        frontmatter = "\n".join(lines)
        return frontmatter + self._transform_body(body)

    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Format agent.md with OpenCode YAML frontmatter."""
        tools = dict(self._settings.tools) if isinstance(self._settings.tools, dict) else {}
        return self._build_opencode_frontmatter(
            description=description,
            tools=tools,
            body=body,
        )

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format a lead agent file with extra edit tool and team permissions."""
        tools = dict(self._settings.tools) if isinstance(self._settings.tools, dict) else {}
        tools["edit"] = True
        return self._build_opencode_frontmatter(
            description=description,
            tools=tools,
            extra_permissions=[f'"{self.teams_base_path}/**": allow'],
            body=body,
        )

    def format_librarian_md(self, body: str) -> str:
        """Format librarian agent with read-only tools."""
        return self._build_opencode_frontmatter(
            description=LIBRARIAN_DESCRIPTION,
            tools={"read": True, "grep": True, "glob": True},
            body=body,
        )

    # --- Analysis engine ---

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
        write: bool = False,
    ) -> list[str]:
        """Build opencode run command for analysis."""
        cmd = shlex.split(self._engine)

        # Add model
        cmd.extend(["--model", self.model])

        # Set working directory to common parent of extra dirs so opencode
        # can access both the cloned repo and expert staging directory
        if extra_dirs:
            import os

            resolved = [str(d.resolve()) for d in extra_dirs if d.exists()]
            if resolved:
                common = os.path.commonpath(resolved)
                cmd.extend(["--dir", common])

        return cmd

    def build_query_command(self) -> list[str]:
        """Build opencode run command for librarian queries."""
        cmd = shlex.split(self._engine)
        cmd.extend(["--model", self.model])
        return cmd

    # --- Server support ---

    @property
    def supports_server(self) -> bool:
        return True

    def start_server_command(self, port: int, hostname: str) -> list[str]:
        binary = shlex.split(self._engine)[0]
        return [binary, "serve", "--port", str(port), "--hostname", hostname]

    def connect_args(self, port: int, hostname: str) -> list[str]:
        return ["--port", str(port), "--hostname", hostname]

    def launch_command(self, extra_args: list[str] | None = None) -> list[str]:
        binary = shlex.split(self._engine)[0]
        return [binary, *(extra_args or [])]

    def health_check_url(self, port: int, hostname: str) -> str:
        return f"http://{hostname}:{port}/global/health"

    # --- MCP config deployment ---

    def deploy_mcp_config(self, project_dir: Path) -> None:
        """Merge hivemind MCP server entry into opencode.json."""
        config_path = self._home_dir / "opencode.json"
        existing: dict[str, Any] = {}
        if config_path.exists() and not config_path.is_symlink():
            with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
                existing = json.loads(config_path.read_text(encoding="utf-8"))

        mcp_section = existing.get("mcp", {})
        if not isinstance(mcp_section, dict):
            mcp_section = {}

        mcp_section["hivemind"] = {
            "type": "local",
            "command": ["hivemind", "mcp"],
            "environment": {
                "PYTHONUNBUFFERED": "1",
            },
        }

        existing["mcp"] = mcp_section
        config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")

    def notify_instance_reload(self) -> bool:
        """POST /instance/dispose on the running OpenCode server."""
        from hivemind.server import get_server_url

        url = get_server_url()
        if url is None:
            return False

        try:
            resp = httpx.post(f"{url}/instance/dispose", timeout=5.0)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            log.debug("Failed to notify OpenCode server at %s", url)
            return False

    # --- Init ---

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Generate/merge global permissions into opencode.json."""
        results: list[InitResult] = []

        cache_path = self.cache_base_path
        experts_path = self.experts_base_path
        teams_path = self.teams_base_path

        hivemind_permissions = {
            "bash": {
                "sudo *": "deny",
            },
            "external_directory": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
                f"{teams_path}/**": "allow",
            },
            "read": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
                f"{teams_path}/**": "allow",
            },
            "grep": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
            },
            "glob": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
            },
            "write": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
                f"{teams_path}/**": "allow",
            },
            "edit": {
                f"{teams_path}/**": "allow",
            },
        }

        config_path = self._home_dir / "opencode.json"
        existing: dict[str, Any] = {}
        if config_path.exists() and not config_path.is_symlink():
            with contextlib.suppress(FileNotFoundError):
                existing = json.loads(config_path.read_text(encoding="utf-8"))

        # Top-level security hardening (force-set; hivemind is authoritative)
        existing["share"] = "disabled"
        existing["autoshare"] = False
        existing["autoupdate"] = False
        raw_server = existing.get("server")
        server: dict[str, object] = raw_server if isinstance(raw_server, dict) else {}
        server["hostname"] = "127.0.0.1"
        existing["server"] = server

        # Deep-merge hivemind permissions into existing permission key
        existing_perms = existing.get("permission", {})
        for tool_key, patterns in hivemind_permissions.items():
            if tool_key not in existing_perms:
                existing_perms[tool_key] = {}
            if isinstance(existing_perms[tool_key], dict):
                existing_perms[tool_key].update(patterns)
            else:
                # Was a flat string like "allow" -- convert to pattern dict
                existing_perms[tool_key] = {"*": existing_perms[tool_key]}
                existing_perms[tool_key].update(patterns)

        existing["permission"] = existing_perms
        config_path.write_text(json.dumps(existing, indent=2) + "\n")
        results.append(InitResult(label="opencode.json", status="hardening + permissions merged"))

        # Branding plugin: replace OpenCode's home screen logo with Hivemind
        plugins_dir = self._home_dir / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        plugin_path = plugins_dir / "hivemind-branding.js"
        plugin_path.write_text(opencode_branding_plugin(), encoding="utf-8")
        # Remove stale .tsx version from previous installs
        stale_tsx = plugins_dir / "hivemind-branding.tsx"
        if stale_tsx.exists():
            stale_tsx.unlink()
        results.append(InitResult(label="hivemind-branding.js", status="branding plugin deployed"))

        # Register branding plugin in tui.json (TUI plugins are NOT loaded from
        # opencode.json — they require a separate tui.json config file)
        tui_config_path = self._home_dir / "tui.json"
        tui_existing: dict[str, Any] = {}
        if tui_config_path.exists() and not tui_config_path.is_symlink():
            with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
                tui_existing = json.loads(tui_config_path.read_text(encoding="utf-8"))

        plugin_url = f"file://{plugin_path}"
        raw_plugins = tui_existing.get("plugin", [])
        tui_plugins: list[object] = raw_plugins if isinstance(raw_plugins, list) else []
        # Ensure our plugin is registered (replace any stale entry)
        tui_plugins = [p for p in tui_plugins if not (isinstance(p, str) and "hivemind-branding" in p)]
        tui_plugins.append(plugin_url)
        tui_existing["plugin"] = tui_plugins
        tui_config_path.write_text(json.dumps(tui_existing, indent=2) + "\n", encoding="utf-8")
        results.append(InitResult(label="tui.json", status="branding plugin registered"))

        return results
