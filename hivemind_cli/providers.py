"""Provider abstraction for multi-platform AI coding agent support.

Each provider (Claude Code, OpenCode, etc.) defines how to:
- Format agent files (frontmatter + body)
- Build analysis engine commands
- Deploy agents, experts, commands, and rules to the provider's directory
- Initialize the provider's directory structure
"""

from __future__ import annotations

import contextlib
import json
import shlex
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from hivemind_cli.models import InitResult, ProviderConfig, ProviderSettings, SymlinkCheck

ToolsConfig = list[str] | dict[str, bool]

# --- Helpers ---


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


def replace_expert_paths(body: str, *, old_base: str, new_base: str) -> str:
    """Replace expert base directory paths in agent body.

    Args:
        body: Agent markdown body
        old_base: Path prefix to replace (e.g. "{EXPERTS_DIR}")
        new_base: Replacement path prefix (e.g. "~/.claude/experts")
    """
    return body.replace(old_base, new_base)


# --- Provider Base Class ---


class Provider(ABC):
    """Abstract base for AI coding platform providers."""

    def __init__(self, config: ProviderConfig, *, providers_dir: Path | None = None):
        """Initialize provider from its config section.

        Args:
            config: Provider configuration model
            providers_dir: Path to the providers directory (for context append lookups)
        """
        self._config: ProviderConfig = config
        self._home_dir = Path(config.home_dir).expanduser() if config.home_dir else Path()
        self._engine: str = config.engine
        self._settings: ProviderSettings = config.settings
        self._providers_dir: Path | None = providers_dir

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'claude', 'opencode')."""

    @property
    @abstractmethod
    def rules_file_name(self) -> str:
        """Filename for the rules file in the provider's home directory.

        E.g. "CLAUDE.md" for Claude Code, "AGENTS.md" for OpenCode.
        """

    @property
    def home_dir(self) -> Path:
        """Provider's home directory (e.g. ~/.claude, ~/.config/opencode)."""
        return self._home_dir

    @property
    def engine(self) -> str:
        """Analysis engine command string."""
        return self._engine

    @property
    def settings(self) -> ProviderSettings:
        """Provider-specific settings (model, tools, temperature, etc.)."""
        return self._settings

    @property
    def permissions(self) -> dict[str, object] | None:
        """Provider permissions config (e.g. for settings.json generation)."""
        return self._config.permissions

    @property
    def experts_base_path(self) -> str:
        """Absolute base path for experts as it appears in agent bodies.

        Used for path replacement at deploy time.
        Uses expanded absolute path so AI tools don't need to resolve ~.
        """
        return str(self._home_dir / "experts")

    @property
    def hivemind_base_path(self) -> str:
        """Absolute base path for hivemind dir as it appears in agent bodies.

        Used for path replacement at deploy time.
        Uses expanded absolute path so AI tools don't need to resolve ~.
        """
        return str(self._home_dir / "hivemind")

    @property
    def cache_base_path(self) -> str:
        """Absolute base path for hivemind cache directory.

        Used for path replacement at deploy time.
        E.g. "/home/user/.cache/hivemind"
        """
        return str(Path.home() / ".cache" / "hivemind")

    # --- Context injection ---

    def get_context_append(self, agent_type: str) -> str:
        """Get provider-specific context to append to an agent body.

        Loads from providers/{name}/context.json and providers/{name}/overrides.json.
        The overrides file is for user customizations (not committed to git).

        Args:
            agent_type: One of "expert", "team_lead", "project_lead"

        Returns:
            Markdown text to append, or empty string
        """
        if self._providers_dir is None:
            return ""

        parts: list[str] = []

        # Provider defaults
        context_path = self._providers_dir / self.name / "context.json"
        if context_path.exists():
            try:
                data = json.loads(context_path.read_text(encoding="utf-8"))
                append = data.get(agent_type, {}).get("append", "")
                if append:
                    parts.append(append)
            except (json.JSONDecodeError, AttributeError):
                pass

        # User overrides (not committed)
        overrides_path = self._providers_dir / self.name / "overrides.json"
        if overrides_path.exists():
            try:
                data = json.loads(overrides_path.read_text(encoding="utf-8"))
                append = data.get(agent_type, {}).get("append", "")
                if append:
                    parts.append(append)
            except (json.JSONDecodeError, AttributeError):
                pass

        return "".join(parts)

    # --- Agent formatting ---

    @abstractmethod
    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Wrap platform-neutral body with provider-specific frontmatter.

        Args:
            name: Expert name (e.g. "bazel")
            description: Expert description for frontmatter
            body: Platform-neutral markdown body (no frontmatter)

        Returns:
            Complete agent.md content with provider frontmatter + transformed body
        """

    def _lead_extra_tools(self) -> ToolsConfig:
        """Extra tools to add for lead agents. Override in subclasses."""
        return []

    def _lead_extra_permissions(self) -> list[str]:
        """Extra permission path patterns for lead agents. Override in subclasses."""
        return []

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Wrap lead agent body with provider-specific frontmatter.

        Generic method for team leads and project leads. Delegates to
        _format_agent_md_internal with lead-specific extra tools and permissions.

        Args:
            agent_name: Full agent name (e.g. "team-lead-nix-infra", "project-lead-foo")
            description: Agent description for frontmatter
            body: Platform-neutral markdown body (no frontmatter)

        Returns:
            Complete agent content with provider frontmatter + transformed body
        """
        return self._format_agent_md_internal(
            agent_name,
            description,
            body,
            extra_tools=self._lead_extra_tools(),
            extra_permissions=self._lead_extra_permissions(),
        )

    @abstractmethod
    def _format_agent_md_internal(
        self,
        agent_name: str,
        description: str,
        body: str,
        *,
        extra_tools: ToolsConfig | None = None,
        extra_permissions: list[str] | None = None,
    ) -> str:
        """Internal formatting — override in subclasses."""

    LIBRARIAN_DESCRIPTION: str = (
        "Hivemind librarian -- knows every expert agent and their "
        "capabilities. Ask the librarian to find the right expert for a question "
        "before delegating to specialists."
    )

    def _get_librarian_tools(self) -> ToolsConfig:
        """Return the tool set for the librarian agent. Override in subclasses."""
        return []

    @abstractmethod
    def _format_librarian_md_internal(self, tools: ToolsConfig, description: str, body: str) -> str:
        """Format librarian frontmatter — provider-specific. Override in subclasses."""

    def format_librarian_md(self, body: str) -> str:
        """Wrap librarian body with provider-specific frontmatter."""
        return self._format_librarian_md_internal(
            self._get_librarian_tools(),
            self.LIBRARIAN_DESCRIPTION,
            body,
        )

    # --- Analysis engine ---

    @abstractmethod
    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
        write: bool = False,
    ) -> list[str]:
        """Build subprocess command for AI analysis.

        Args:
            extra_dirs: Additional directories to make available to the engine
            write: Whether the task needs file write access

        Returns:
            Command list suitable for subprocess.Popen
        """

    @abstractmethod
    def build_query_command(self) -> list[str]:
        """Build subprocess command for librarian queries.

        Returns:
            Command list suitable for subprocess.run (prompt via stdin)
        """

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
        body = replace_expert_paths(body, old_base="{EXPERTS_DIR}", new_base=self.experts_base_path)
        body = body.replace("{HIVEMIND_DIR}", self.hivemind_base_path)
        return body.replace("{CACHE_DIR}", self.cache_base_path)

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

        Shared logic for all providers: agents/, commands/, rules file,
        experts/ directory, and hivemind/teams/ symlinks.
        Provider-specific steps go in _post_init_dirs().
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

        # teams/ under hivemind/ subdirectory
        # (avoids conflicts with provider-owned directories)
        hivemind_subdir = self._home_dir / "hivemind"
        hivemind_subdir.mkdir(parents=True, exist_ok=True)

        if teams_dir:
            results.append(_setup_symlink(teams_dir, hivemind_subdir / "teams", "hivemind/teams/"))

        # Provider-specific hook
        results.extend(self._post_init_dirs(permissions=permissions))

        return results

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Provider-specific init steps. Override in subclasses."""
        return []

    def status_symlinks(
        self,
        *,
        agents_dir: Path,
        commands_dir: Path,
        rules_source: Path,
        teams_dir: Path | None = None,
    ) -> list[SymlinkCheck]:
        """Return symlink checks for the status dashboard.

        Each entry contains display_name, expected_target, and link_path.
        Shared across all providers.
        """
        checks = [
            SymlinkCheck(
                display_name=f"{self._home_dir}/agents/",
                expected_target=agents_dir,
                link_path=self._home_dir / "agents",
            ),
            SymlinkCheck(
                display_name=f"{self._home_dir}/commands/",
                expected_target=commands_dir,
                link_path=self._home_dir / "commands",
            ),
            SymlinkCheck(
                display_name=f"{self._home_dir}/{self.rules_file_name}",
                expected_target=rules_source,
                link_path=self._home_dir / self.rules_file_name,
            ),
        ]
        hivemind_subdir = self._home_dir / "hivemind"
        if teams_dir:
            checks.append(
                SymlinkCheck(
                    display_name=f"{hivemind_subdir}/teams/",
                    expected_target=teams_dir,
                    link_path=hivemind_subdir / "teams",
                )
            )
        return checks


# --- Claude Code Provider ---


class ClaudeProvider(Provider):
    """Claude Code platform provider."""

    @property
    def name(self) -> str:
        return "claude"

    @property
    def rules_file_name(self) -> str:
        return "CLAUDE.md"

    def _lead_extra_tools(self) -> ToolsConfig:
        return ["Edit"]

    def _format_agent_md_internal(
        self,
        agent_name: str,
        description: str,
        body: str,
        *,
        extra_tools: ToolsConfig | None = None,
        extra_permissions: list[str] | None = None,
    ) -> str:
        """Internal Claude Code agent formatting with custom name."""
        tools = list(self._settings.tools)
        if isinstance(extra_tools, list):
            for t in extra_tools:
                if t not in tools:
                    tools.append(t)
        model = self._settings.model or "sonnet"

        tools_str = ", ".join(tools)

        frontmatter = (
            f"---\nname: {agent_name}\ndescription: {description}\ntools: {tools_str}\nmodel: {model}\n---\n\n"
        )

        return frontmatter + self._transform_body(body)

    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Format agent.md with Claude Code YAML frontmatter."""
        return self._format_agent_md_internal(f"expert-{name}", description, body)

    def _get_librarian_tools(self) -> ToolsConfig:
        tools = self._settings.tools
        librarian_tools = [t for t in tools if t in ("Read", "Grep", "Glob")]
        return librarian_tools or ["Read", "Grep", "Glob"]

    def _format_librarian_md_internal(self, tools: ToolsConfig, description: str, body: str) -> str:
        model = self._settings.model or "sonnet"
        tools_str = ", ".join(tools) if isinstance(tools, list) else str(tools)

        frontmatter = f'---\nname: librarian\ndescription: "{description}"\ntools: {tools_str}\nmodel: {model}\n---\n\n'

        return frontmatter + body

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
        write: bool = False,
    ) -> list[str]:
        """Build claude -p command for analysis."""
        # Parse engine string into base command
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
        model = self._settings.model or "sonnet"
        cmd.extend(["--model", model])

        # Add extra directories
        if extra_dirs:
            for d in extra_dirs:
                cmd.extend(["--add-dir", str(d)])

        return cmd

    def build_query_command(self) -> list[str]:
        """Build claude -p command for librarian queries."""
        model = self._settings.model or "sonnet"
        return ["claude", "-p", "--model", model]

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Generate settings.json from permissions config."""
        import json as _json

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
            settings_path.write_text(_json.dumps(settings_data, indent=2) + "\n")
            results.append(InitResult(label="settings.json", status="generated from hivemind.json"))

        return results


# --- OpenCode Provider ---


class OpenCodeProvider(Provider):
    """OpenCode platform provider."""

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def rules_file_name(self) -> str:
        return "AGENTS.md"

    def _lead_extra_tools(self) -> ToolsConfig:
        return {"edit": True}

    def _lead_extra_permissions(self) -> list[str]:
        return [
            f'"{self.hivemind_base_path}/teams/**": allow',
            f'"{self.hivemind_base_path}/projects/**": allow',
        ]

    def _format_agent_md_internal(
        self,
        agent_name: str,
        description: str,
        body: str,
        *,
        extra_tools: ToolsConfig | None = None,
        extra_permissions: list[str] | None = None,
    ) -> str:
        """Internal OpenCode agent formatting with custom name."""
        model = self._settings.model or "anthropic/claude-sonnet-4-20250514"
        temperature = self._settings.temperature if self._settings.temperature is not None else 0.1
        tools = dict(self._settings.tools) if isinstance(self._settings.tools, dict) else {}
        if isinstance(extra_tools, dict):
            tools.update(extra_tools)

        lines = [
            "---",
            f"description: {description}",
            "mode: subagent",
            f"model: {model}",
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
        return self._format_agent_md_internal(f"expert-{name}", description, body)

    def _get_librarian_tools(self) -> ToolsConfig:
        return {"read": True, "grep": True, "glob": True}

    def _format_librarian_md_internal(self, tools: ToolsConfig, description: str, body: str) -> str:
        model = self._settings.model or "anthropic/claude-sonnet-4-20250514"
        temperature = self._settings.temperature if self._settings.temperature is not None else 0.1

        lines = [
            "---",
            f'description: "{description}"',
            "mode: subagent",
            f"model: {model}",
            f"temperature: {temperature}",
        ]

        if isinstance(tools, dict):
            lines.append("tools:")
            for tool_name, enabled in sorted(tools.items()):
                lines.append(f"  {tool_name}: {str(enabled).lower()}")

        lines.extend(["---", "", ""])

        return "\n".join(lines) + body

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
        write: bool = False,
    ) -> list[str]:
        """Build opencode run command for analysis."""
        cmd = shlex.split(self._engine)

        # Add model
        model = self._settings.model or "github-copilot/claude-sonnet-4"
        cmd.extend(["--model", model])

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
        model = self._settings.model or "github-copilot/claude-sonnet-4"
        cmd.extend(["--model", model])
        return cmd

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Generate/merge global permissions into opencode.json."""
        import json as _json

        results: list[InitResult] = []

        cache_path = self.cache_base_path
        experts_path = self.experts_base_path
        hivemind_path = self.hivemind_base_path

        hivemind_permissions = {
            "bash": {
                "sudo *": "deny",
            },
            "external_directory": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
                f"{hivemind_path}/teams/**": "allow",
                f"{hivemind_path}/projects/**": "allow",
            },
            "read": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
                f"{hivemind_path}/teams/**": "allow",
                f"{hivemind_path}/projects/**": "allow",
            },
            "grep": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
            },
            "glob": {
                f"{cache_path}/**": "allow",
                f"{experts_path}/**": "allow",
            },
            "edit": {
                f"{hivemind_path}/teams/**": "allow",
                f"{hivemind_path}/projects/**": "allow",
            },
        }

        config_path = self._home_dir / "opencode.json"
        existing: dict = {}
        if config_path.exists() and not config_path.is_symlink():
            with contextlib.suppress(ValueError, OSError):
                existing = _json.loads(config_path.read_text(encoding="utf-8"))

        # Deep-merge hivemind permissions into existing permission key
        existing_perms = existing.get("permission", {})
        for tool_key, patterns in hivemind_permissions.items():
            if tool_key not in existing_perms:
                existing_perms[tool_key] = {}
            if isinstance(existing_perms[tool_key], dict):
                existing_perms[tool_key].update(patterns)
            else:
                # Was a flat string like "allow" — convert to pattern dict
                existing_perms[tool_key] = {"*": existing_perms[tool_key]}
                existing_perms[tool_key].update(patterns)

        existing["permission"] = existing_perms
        config_path.write_text(_json.dumps(existing, indent=2) + "\n")
        results.append(InitResult(label="opencode.json", status="permissions merged for hivemind paths"))

        return results


# --- Provider Registry ---


PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "claude": ClaudeProvider,
    "opencode": OpenCodeProvider,
}


def get_provider(name: str, provider_config: ProviderConfig, *, providers_dir: Path | None = None) -> Provider:
    """Create a provider instance by name.

    Args:
        name: Provider name (e.g. "claude", "opencode")
        provider_config: Provider configuration model
        providers_dir: Path to the providers directory (for context append lookups)

    Returns:
        Provider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    cls = PROVIDER_CLASSES.get(name)
    if cls is None:
        msg = f"Unknown provider '{name}'. Available: {', '.join(PROVIDER_CLASSES)}"
        raise ValueError(msg)
    return cls(provider_config, providers_dir=providers_dir)


# --- Internal Helpers ---


def _setup_symlink(target: Path, link: Path, label: str) -> InitResult:
    """Create or update a symlink, returning status for display.

    Args:
        target: What the symlink should point to
        link: Where to create the symlink
        label: Display label for status messages

    Returns:
        InitResult with label and status message
    """
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            return InitResult(label=label, status="already correct")
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        link.rename(backup)
        return InitResult(label=label, status=f"backed up existing dir to {backup.name}/, created symlink")
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    return InitResult(label=label, status=f"-> {target}")
