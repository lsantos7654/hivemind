"""OpenCode platform provider — formatting, deployment, and engine management.

Provides the ``Provider`` class that handles:
- Formatting agent files with OpenCode YAML frontmatter
- Building analysis/query engine subprocess commands
- Deploying/undeploying agent files and expert symlinks
- Initialising the OpenCode directory structure
- Server lifecycle commands and MCP config deployment

Also exports helper functions used across the codebase:
``extract_description``, ``strip_frontmatter``, ``yaml_escape_double_quoted``,
``replace_expert_paths``.
"""

from __future__ import annotations

import contextlib
import json
import logging
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx

from hivemind.constants import (
    CACHE_DIR,
    CACHE_DIR_PLACEHOLDER,
    DEFAULT_TEMPERATURE,
    ENGINE_VALIDATION_TIMEOUT,
    EXPERTS_DIR_PLACEHOLDER,
    OPENCODE_CONFIG_DIR,
    OPENCODE_PLUGINS_DIR,
    TEAMS_DIR_PLACEHOLDER,
)
from hivemind.models import HivemindConfig, InitResult, OperationResult, ServerConfig
from hivemind.templates import LIBRARIAN_DESCRIPTION

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_description(body: str) -> str:
    """Extract description from agent.md body (first paragraph after heading).

    Expects format:
        # Expert: Name
        <blank line>
        Description paragraph...
        <blank line>
        ## Next Section

    Falls back to the first paragraph under an '## Overview' section if no
    paragraph is found directly under the h1 heading.

    Returns:
        Description string, or empty string if not found.
    """
    lines = body.strip().splitlines()

    def _first_paragraph(start_idx: int) -> str:
        """Return the first non-empty paragraph starting from start_idx."""
        paragraph_lines: list[str] = []
        for line in lines[start_idx:]:
            stripped = line.strip()
            if not stripped and not paragraph_lines:
                continue
            if stripped.startswith("#") or (not stripped and paragraph_lines):
                break
            paragraph_lines.append(stripped)
        return " ".join(paragraph_lines)

    # Find h1 heading index
    h1_idx = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if h1_idx is None:
        return ""

    # Try direct paragraph under h1
    result = _first_paragraph(h1_idx + 1)
    if result:
        return result

    # Fallback: first paragraph under ## Overview
    for i, line in enumerate(lines):
        if line.strip().lower() == "## overview":
            result = _first_paragraph(i + 1)
            if result:
                return result

    return ""


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content.

    Handles content with or without frontmatter.
    """
    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return content


def yaml_escape_double_quoted(s: str) -> str:
    """Escape a string for use inside a YAML double-quoted scalar.

    Per the YAML spec, inside double-quoted scalars backslash is the
    escape character, so both ``\\`` and ``"`` must be escaped.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"')


def replace_expert_paths(body: str, *, old_base: str, new_base: str) -> str:
    """Replace expert base directory paths in agent body.

    Args:
        body: Agent markdown body
        old_base: Path prefix to replace (e.g. "{EXPERTS_DIR}")
        new_base: Replacement path prefix (e.g. "~/.config/opencode/experts")
    """
    return body.replace(old_base, new_base)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class Provider:
    """OpenCode platform provider.

    Handles agent formatting, deployment, engine validation, and directory
    initialisation for the OpenCode platform.
    """

    name: str = "opencode"
    rules_file_name: str = "AGENTS.md"

    def __init__(self, config: HivemindConfig) -> None:
        self._config = config
        self._home_dir = Path(config.home_dir).expanduser() if config.home_dir else Path()
        self._engine: str = config.engine
        self._model: str = config.model
        self._tools: dict[str, bool] = dict(config.tools)
        self._temperature: float | None = config.temperature

    # --- Properties ---

    @property
    def home_dir(self) -> Path:
        """Provider's home directory (e.g. ~/.config/opencode)."""
        return self._home_dir

    @property
    def engine(self) -> str:
        """Analysis engine command string."""
        return self._engine

    @property
    def model(self) -> str:
        """Configured model string. Raises if not set."""
        if not self._model:
            msg = "No model configured. Set 'model' in hivemind.json."
            raise ValueError(msg)
        return self._model

    @property
    def permissions(self) -> dict[str, object] | None:
        """Provider permissions config."""
        return self._config.permissions

    @property
    def experts_base_path(self) -> str:
        """Absolute base path for experts as it appears in agent bodies."""
        return str(self._home_dir / "experts")

    @property
    def teams_base_path(self) -> str:
        """Absolute base path for teams dir as it appears in agent bodies."""
        return str(self._home_dir / "teams")

    @property
    def cache_base_path(self) -> str:
        """Absolute base path for hivemind cache directory."""
        return str(CACHE_DIR)

    @property
    def supports_server(self) -> bool:
        """Whether this provider has a backend server mode."""
        return True

    @property
    def server_config(self) -> ServerConfig:
        """Server configuration from hivemind.json."""
        return self._config.server

    # --- Engine validation ---

    def validate_engine(self) -> OperationResult:
        """Validate that the analysis engine binary and model are available."""
        if not self._engine:
            return OperationResult(
                success=False,
                error="No engine configured. Set 'engine' in hivemind.json.",
            )

        binary = shlex.split(self._engine)[0]
        if not shutil.which(binary):
            return OperationResult(
                success=False,
                error=f"Analysis engine '{binary}' not found on PATH. Install it first.",
            )

        if not self._model:
            return OperationResult(
                success=False,
                error="No model configured. Set 'model' in hivemind.json.",
            )

        # Check the configured model is actually accessible
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
        if self._model not in available:
            return OperationResult(
                success=False,
                error=f"Model '{self._model}' not available. "
                f"Run 'opencode providers' to configure it.\n"
                f"Available models can be listed with 'opencode models'.",
            )

        return OperationResult(success=True)

    # --- Formatting ---

    def _build_frontmatter(
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
            tools: Tool permissions as dict[str, bool]
            extra_permissions: Additional permission path patterns
            body: Markdown body (will be path-transformed)
        """
        temperature = self._temperature if self._temperature is not None else DEFAULT_TEMPERATURE

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
        return self._build_frontmatter(
            description=description,
            tools=dict(self._tools),
            body=body,
        )

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format a lead agent file with extra edit tool and team permissions."""
        tools = dict(self._tools)
        tools["edit"] = True
        return self._build_frontmatter(
            description=description,
            tools=tools,
            extra_permissions=[f'"{self.teams_base_path}/**": allow'],
            body=body,
        )

    def format_librarian_md(self, body: str) -> str:
        """Format librarian agent with read-only tools."""
        return self._build_frontmatter(
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

    def start_server_command(self, port: int, hostname: str) -> list[str]:
        binary = shlex.split(self._engine)[0]
        return [binary, "serve", "--port", str(port), "--hostname", hostname]

    def launch_command(self, extra_args: list[str] | None = None) -> list[str]:
        binary = shlex.split(self._engine)[0]
        return [binary, *(extra_args or [])]

    def attach_command(self, server_url: str, extra_args: list[str] | None = None) -> list[str]:
        binary = shlex.split(self._engine)[0]
        if extra_args:
            # Headless mode: opencode run --attach <url> <extra_args>
            return [binary, "run", "--attach", server_url, *extra_args]
        # TUI mode: opencode attach <url>
        return [binary, "attach", server_url]

    def health_check_url(self, port: int, hostname: str) -> str:
        return f"http://{hostname}:{port}/global/health"

    def notify_instance_reload(self) -> bool:
        """POST /global/dispose on the running OpenCode server.

        Uses the global endpoint rather than /instance/dispose so that every
        cached InstanceState (agent registry, plugins, skills, ...) for every
        directory the server has seen gets invalidated. /instance/dispose only
        clears the caller's directory context, which leaves stale agent lists
        in any directory the TUI is attached from.
        """
        from hivemind.server import get_server_url

        url = get_server_url()
        if url is None:
            return False

        try:
            resp = httpx.post(f"{url}/global/dispose", timeout=5.0)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            log.debug("Failed to notify OpenCode server at %s", url)
            return False

    # --- Deployment ---

    def deploy_agent(self, name: str, content: str, *, agents_dir: Path) -> None:
        """Deploy a generated agent file."""
        agents_dir.mkdir(parents=True, exist_ok=True)
        agent_file = agents_dir / f"expert-{name}.md"
        if agent_file.is_symlink():
            agent_file.unlink()
        agent_file.write_text(content, encoding="utf-8")

    def undeploy_agent(self, name: str, *, agents_dir: Path) -> None:
        """Remove a deployed agent file."""
        agent_file = agents_dir / f"expert-{name}.md"
        if agent_file.is_symlink() or agent_file.exists():
            agent_file.unlink()

    def _transform_body(self, body: str) -> str:
        """Apply standard path replacements to agent body."""
        body = replace_expert_paths(body, old_base=EXPERTS_DIR_PLACEHOLDER, new_base=self.experts_base_path)
        body = body.replace(TEAMS_DIR_PLACEHOLDER, self.teams_base_path)
        return body.replace(CACHE_DIR_PLACEHOLDER, self.cache_base_path)

    def deploy_expert(self, name: str, source_dir: Path) -> None:
        """Create symlink in provider's experts directory."""
        provider_experts = self._home_dir / "experts"
        provider_experts.mkdir(parents=True, exist_ok=True)

        expert_link = provider_experts / name
        if expert_link.is_symlink():
            if expert_link.resolve() == source_dir.resolve():
                return
            expert_link.unlink()
        elif expert_link.exists():
            if expert_link.is_dir():
                shutil.rmtree(expert_link)
            else:
                expert_link.unlink()

        expert_link.symlink_to(source_dir)

    def undeploy_expert(self, name: str) -> None:
        """Remove expert from provider's experts directory."""
        expert_link = self._home_dir / "experts" / name
        if expert_link.is_symlink() or expert_link.exists():
            if expert_link.is_dir() and not expert_link.is_symlink():
                shutil.rmtree(expert_link)
            else:
                expert_link.unlink()

    # --- Init ---

    def init_dirs(
        self,
        *,
        agents_dir: Path,
        commands_dir: Path,
        rules_source: Path,
        teams_dir: Path | None = None,
        permissions: dict[str, object] | None = None,
    ) -> list[InitResult]:
        """Initialize provider directory structure and deploy symlinks.

        Sets up agents/, commands/, rules file, experts/ directory, and teams/
        symlinks, then applies OpenCode-specific security hardening and
        branding plugin deployment.
        """
        results: list[InitResult] = []

        self._home_dir.mkdir(parents=True, exist_ok=True)

        # Core symlinks: agents/, commands/, rules file
        results.append(_setup_symlink(agents_dir, self._home_dir / "agents", "agents/"))
        results.append(_setup_symlink(commands_dir, self._home_dir / "commands", "commands/"))
        results.append(
            _setup_symlink(
                rules_source,
                self._home_dir / self.rules_file_name,
                self.rules_file_name,
            ),
        )

        # experts/ directory (real dir, not symlink)
        experts_dir = self._home_dir / "experts"
        experts_dir.mkdir(parents=True, exist_ok=True)
        results.append(InitResult(label="experts/", status="directory ready"))

        # teams/ symlink directly under provider home
        if teams_dir:
            results.append(_setup_symlink(teams_dir, self._home_dir / "teams", "teams/"))

        # OpenCode-specific: security hardening + permissions + branding
        results.extend(self._post_init_dirs())

        return results

    def _post_init_dirs(self) -> list[InitResult]:
        """Apply bundled OpenCode defaults (opencode.json config + branding plugin).

        Reads opencode/config/defaults.json and opencode/plugins/ from the repo
        and installs them into ~/.config/opencode. The JSON is split into
        ``hardening`` (force-set top-level keys) and ``permissions``
        (deep-merged). Path tokens ``{CACHE_PATH}`` / ``{EXPERTS_PATH}`` /
        ``{TEAMS_PATH}`` in permission patterns are substituted here.
        """
        results: list[InitResult] = []

        defaults = self._load_opencode_defaults()
        hardening = defaults.get("hardening", {})
        permissions = self._substitute_path_tokens(defaults.get("permissions", {}))

        config_path = self._home_dir / "opencode.json"
        existing: dict[str, Any] = {}
        if config_path.exists() and not config_path.is_symlink():
            with contextlib.suppress(FileNotFoundError):
                existing = json.loads(config_path.read_text(encoding="utf-8"))

        # Hardening: force-set (hivemind is authoritative). Nested dicts are
        # merged so we don't clobber sibling keys under e.g. `server`.
        for key, value in hardening.items():
            if isinstance(value, dict):
                raw = existing.get(key)
                merged: dict[str, object] = raw if isinstance(raw, dict) else {}
                merged.update(value)
                existing[key] = merged
            else:
                existing[key] = value

        # Deep-merge permissions into existing permission key
        existing_perms = existing.get("permission", {})
        for tool_key, patterns in permissions.items():
            if tool_key not in existing_perms:
                existing_perms[tool_key] = {}
            if isinstance(existing_perms[tool_key], dict):
                existing_perms[tool_key].update(patterns)
            else:
                # Was a flat string like "allow" -- convert to pattern dict
                existing_perms[tool_key] = {"*": existing_perms[tool_key]}
                existing_perms[tool_key].update(patterns)

        existing["permission"] = existing_perms

        mcp_section = existing.get("mcp")
        if not isinstance(mcp_section, dict):
            mcp_section = {}
        mcp_section["hivemind"] = {
            "type": "local",
            "command": ["hivemind", "mcp"],
            "environment": {"PYTHONUNBUFFERED": "1"},
        }
        existing["mcp"] = mcp_section

        config_path.write_text(json.dumps(existing, indent=2) + "\n")
        results.append(InitResult(label="opencode.json", status="hardening + permissions merged"))
        results.append(InitResult(label="opencode.json", status="mcp server registered"))

        # Deploy every bundled plugin as a real JS file.
        # Install to `tui-plugins/` rather than `plugins/`: opencode's server-side
        # plugin auto-discovery globs `{plugin,plugins}/*.{ts,js}` under the config
        # dir (see opencode config/plugin.ts) and treats anything it finds as a
        # server plugin, which fails the validator for our TUI-only plugins.
        plugins_dir = self._home_dir / "tui-plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        installed_plugin_paths: list[Path] = []
        for source in sorted(OPENCODE_PLUGINS_DIR.glob("*.js")):
            dest = plugins_dir / source.name
            shutil.copyfile(source, dest)
            installed_plugin_paths.append(dest)
            results.append(InitResult(label=source.name, status="plugin deployed"))

        # Register plugins in tui.json (TUI plugins require tui.json, not opencode.json)
        if installed_plugin_paths:
            tui_config_path = self._home_dir / "tui.json"
            tui_existing: dict[str, Any] = {}
            if tui_config_path.exists() and not tui_config_path.is_symlink():
                with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
                    tui_existing = json.loads(tui_config_path.read_text(encoding="utf-8"))

            raw_plugins = tui_existing.get("plugin", [])
            tui_plugins: list[object] = raw_plugins if isinstance(raw_plugins, list) else []
            # Drop any existing entries pointing at our bundled plugins; re-add fresh
            bundled_stems = {p.stem for p in installed_plugin_paths}
            tui_plugins = [
                p for p in tui_plugins if not (isinstance(p, str) and any(stem in p for stem in bundled_stems))
            ]
            for plugin_path in installed_plugin_paths:
                tui_plugins.append(f"file://{plugin_path}")
            tui_existing["plugin"] = tui_plugins
            tui_config_path.write_text(json.dumps(tui_existing, indent=2) + "\n", encoding="utf-8")
            results.append(InitResult(label="tui.json", status="plugins registered"))

        return results

    def _load_opencode_defaults(self) -> dict[str, Any]:
        """Load opencode/config/defaults.json bundled with this repo."""
        defaults_path = OPENCODE_CONFIG_DIR / "defaults.json"
        raw = json.loads(defaults_path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}

    def _substitute_path_tokens(self, permissions: dict[str, Any]) -> dict[str, Any]:
        """Replace {CACHE_PATH}/{EXPERTS_PATH}/{TEAMS_PATH} tokens in permission patterns."""
        tokens = {
            "{CACHE_PATH}": str(self.cache_base_path),
            "{EXPERTS_PATH}": str(self.experts_base_path),
            "{TEAMS_PATH}": str(self.teams_base_path),
        }

        def render(pattern: str) -> str:
            for token, value in tokens.items():
                pattern = pattern.replace(token, value)
            return pattern

        resolved: dict[str, Any] = {}
        for tool_key, patterns in permissions.items():
            if isinstance(patterns, dict):
                resolved[tool_key] = {render(pat): verdict for pat, verdict in patterns.items()}
            else:
                resolved[tool_key] = patterns
        return resolved


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _setup_symlink(target: Path, link: Path, label: str) -> InitResult:
    """Create or update a symlink, returning status for display.

    Args:
        target: What the symlink should point to
        link: Where to create the symlink
        label: Display label for status messages

    Returns:
        InitResult with label and status message
    """
    status = ""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            return InitResult(label=label, status="already correct")
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        link.rename(backup)
        status = f"backed up existing dir to {backup.name}/, "
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    return InitResult(label=label, status=f"{status}-> {target}")
