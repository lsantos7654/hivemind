"""Provider abstraction for multi-platform AI coding agent support.

Each provider (Claude Code, OpenCode, etc.) defines how to:
- Format agent files (frontmatter + body)
- Build analysis engine commands
- Deploy agents, experts, commands, and rules to the provider's directory
- Initialize the provider's directory structure
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
from abc import ABC, abstractmethod
from pathlib import Path


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
    h1_idx = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
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

    def __init__(self, config: dict):
        """Initialize provider from its config section.

        Args:
            config: Provider config dict with keys: enabled, engine, home_dir, settings
        """
        self._config = config
        self._home_dir = Path(os.path.expanduser(config.get("home_dir", "")))
        self._engine = config.get("engine", "")
        self._settings = config.get("settings", {})

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
    def settings(self) -> dict:
        """Provider-specific settings (model, tools, temperature, etc.)."""
        return self._settings

    @property
    def permissions(self) -> dict | None:
        """Provider permissions config (e.g. for settings.json generation)."""
        return self._config.get("permissions")

    @property
    def experts_base_path(self) -> str:
        """Base path for experts as it appears in agent bodies.

        Used for path replacement at deploy time.
        E.g. "~/.claude/experts" or "~/.config/opencode/experts"
        """
        home = self._config.get("home_dir", "")
        return f"{home}/experts"

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

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Wrap lead agent body with provider-specific frontmatter.

        Generic method for team leads and project leads. Uses the same
        formatting as format_agent_md but with a custom agent name
        (no 'expert-' prefix).

        Args:
            agent_name: Full agent name (e.g. "team-lead-nix-infra", "project-lead-foo")
            description: Agent description for frontmatter
            body: Platform-neutral markdown body (no frontmatter)

        Returns:
            Complete agent content with provider frontmatter + transformed body
        """
        # Default implementation delegates to _format_agent_md_internal
        # Subclasses can override if needed
        return self._format_agent_md_internal(agent_name, description, body)

    def _format_agent_md_internal(
        self, agent_name: str, description: str, body: str
    ) -> str:
        """Internal formatting — override in subclasses."""
        raise NotImplementedError

    @abstractmethod
    def format_librarian_md(self, body: str) -> str:
        """Wrap librarian body with provider-specific frontmatter.

        Args:
            body: Librarian markdown body (no frontmatter)

        Returns:
            Complete librarian.md content with provider frontmatter
        """

    # --- Analysis engine ---

    @abstractmethod
    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
    ) -> list[str]:
        """Build subprocess command for AI analysis.

        Args:
            extra_dirs: Additional directories to make available to the engine

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

    @abstractmethod
    def deploy_agent(self, name: str, content: str, *, agents_dir: Path) -> None:
        """Deploy a generated agent file.

        Args:
            name: Expert name
            content: Full agent.md content (with frontmatter)
            agents_dir: Hivemind's agents/ directory
        """

    @abstractmethod
    def undeploy_agent(self, name: str, *, agents_dir: Path) -> None:
        """Remove a deployed agent file.

        Args:
            name: Expert name
            agents_dir: Hivemind's agents/ directory
        """

    @abstractmethod
    def deploy_expert(self, name: str, source_dir: Path) -> None:
        """Deploy expert directory to provider's expert location.

        Args:
            name: Expert name
            source_dir: Path to expert directory in hivemind
        """

    @abstractmethod
    def undeploy_expert(self, name: str) -> None:
        """Remove expert from provider's expert location.

        Args:
            name: Expert name
        """

    def init_dirs(
        self,
        *,
        agents_dir: Path,
        commands_dir: Path,
        rules_source: Path,
        teams_dir: Path | None = None,
        projects_dir: Path | None = None,
        permissions: dict | None = None,
    ) -> list[tuple[str, str]]:
        """Initialize provider directory structure and deploy symlinks.

        Shared logic for all providers: agents/, commands/, rules file,
        experts/ directory, and hivemind/teams/ + hivemind/projects/ symlinks.
        Provider-specific steps go in _post_init_dirs().
        """
        results: list[tuple[str, str]] = []

        self._home_dir.mkdir(parents=True, exist_ok=True)

        # Core symlinks: agents/, commands/, rules file
        results.append(_setup_symlink(agents_dir, self._home_dir / "agents", "agents/"))
        results.append(
            _setup_symlink(commands_dir, self._home_dir / "commands", "commands/")
        )
        results.append(
            _setup_symlink(
                rules_source,
                self._home_dir / self.rules_file_name,
                self.rules_file_name,
            )
        )

        # experts/ directory (real dir, not symlink)
        experts_dir = self._home_dir / "experts"
        experts_dir.mkdir(parents=True, exist_ok=True)
        results.append(("experts/", "directory ready"))

        # teams/ and projects/ under hivemind/ subdirectory
        # (avoids conflicts with provider-owned directories)
        hivemind_subdir = self._home_dir / "hivemind"
        hivemind_subdir.mkdir(parents=True, exist_ok=True)

        if teams_dir:
            results.append(
                _setup_symlink(teams_dir, hivemind_subdir / "teams", "hivemind/teams/")
            )

        if projects_dir:
            results.append(
                _setup_symlink(
                    projects_dir, hivemind_subdir / "projects", "hivemind/projects/"
                )
            )

        # Provider-specific hook
        results.extend(self._post_init_dirs(permissions=permissions))

        return results

    def _post_init_dirs(
        self, *, permissions: dict | None = None
    ) -> list[tuple[str, str]]:
        """Provider-specific init steps. Override in subclasses."""
        return []

    def status_symlinks(
        self,
        *,
        agents_dir: Path,
        commands_dir: Path,
        rules_source: Path,
        teams_dir: Path | None = None,
        projects_dir: Path | None = None,
    ) -> list[tuple[str, Path, Path]]:
        """Return symlink checks for the status dashboard.

        Each tuple is (display_name, expected_target, link_path).
        Shared across all providers.
        """
        checks = [
            (f"{self._home_dir}/agents/", agents_dir, self._home_dir / "agents"),
            (
                f"{self._home_dir}/commands/",
                commands_dir,
                self._home_dir / "commands",
            ),
            (
                f"{self._home_dir}/{self.rules_file_name}",
                rules_source,
                self._home_dir / self.rules_file_name,
            ),
        ]
        hivemind_subdir = self._home_dir / "hivemind"
        if teams_dir:
            checks.append(
                (f"{hivemind_subdir}/teams/", teams_dir, hivemind_subdir / "teams")
            )
        if projects_dir:
            checks.append(
                (
                    f"{hivemind_subdir}/projects/",
                    projects_dir,
                    hivemind_subdir / "projects",
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

    @property
    def experts_base_path(self) -> str:
        return "~/.claude/experts"

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format lead agent with Edit tool added for self-management."""
        tools = list(self._settings.get("tools", []))
        if "Edit" not in tools:
            tools.append("Edit")
        model = self._settings.get("model", "sonnet")

        tools_str = ", ".join(tools)

        frontmatter = (
            f"---\n"
            f"name: {agent_name}\n"
            f"description: {description}\n"
            f"tools: {tools_str}\n"
            f"model: {model}\n"
            f"---\n\n"
        )

        transformed = replace_expert_paths(
            body,
            old_base="{EXPERTS_DIR}",
            new_base=self.experts_base_path,
        )

        return frontmatter + transformed

    def _format_agent_md_internal(
        self, agent_name: str, description: str, body: str
    ) -> str:
        """Internal Claude Code agent formatting with custom name."""
        tools = self._settings.get("tools", [])
        model = self._settings.get("model", "sonnet")

        tools_str = ", ".join(tools) if isinstance(tools, list) else str(tools)

        frontmatter = (
            f"---\n"
            f"name: {agent_name}\n"
            f"description: {description}\n"
            f"tools: {tools_str}\n"
            f"model: {model}\n"
            f"---\n\n"
        )

        transformed = replace_expert_paths(
            body,
            old_base="{EXPERTS_DIR}",
            new_base=self.experts_base_path,
        )

        return frontmatter + transformed

    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Format agent.md with Claude Code YAML frontmatter."""
        return self._format_agent_md_internal(f"expert-{name}", description, body)

    def format_librarian_md(self, body: str) -> str:
        """Format librarian.md with Claude Code YAML frontmatter."""
        tools = self._settings.get("tools", [])
        model = self._settings.get("model", "sonnet")

        # Librarian uses a subset of tools (no Write, no MCP)
        librarian_tools = [t for t in tools if t in ("Read", "Grep", "Glob")]
        if not librarian_tools:
            librarian_tools = ["Read", "Grep", "Glob"]
        tools_str = ", ".join(librarian_tools)

        frontmatter = (
            f"---\n"
            f"name: librarian\n"
            f'description: "Hivemind librarian -- knows every expert agent and their '
            f"capabilities. Ask the librarian to find the right expert for a question "
            f'before delegating to specialists."\n'
            f"tools: {tools_str}\n"
            f"model: {model}\n"
            f"---\n\n"
        )

        return frontmatter + body

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
    ) -> list[str]:
        """Build claude -p command for analysis."""
        # Parse engine string into base command
        cmd = shlex.split(self._engine)

        # Add tools (analysis needs Write too)
        analysis_tools = list(self._settings.get("tools", []))
        if "Write" not in analysis_tools:
            analysis_tools.append("Write")
        # Strip MCP tools for analysis (they're for runtime, not analysis)
        analysis_tools = [t for t in analysis_tools if not t.startswith("mcp__")]
        cmd.extend(["--allowedTools", ",".join(analysis_tools)])

        # Add model
        model = self._settings.get("model", "sonnet")
        cmd.extend(["--model", model])

        # Add extra directories
        if extra_dirs:
            for d in extra_dirs:
                cmd.extend(["--add-dir", str(d)])

        return cmd

    def build_query_command(self) -> list[str]:
        """Build claude -p command for librarian queries."""
        model = self._settings.get("model", "sonnet")
        return ["claude", "-p", "--model", model]

    def deploy_agent(self, name: str, content: str, *, agents_dir: Path) -> None:
        """Write agent file to agents/ directory."""
        agents_dir.mkdir(parents=True, exist_ok=True)
        agent_file = agents_dir / f"expert-{name}.md"
        # Remove old symlink if present (migrating from symlink to file)
        if agent_file.is_symlink():
            agent_file.unlink()
        agent_file.write_text(content)

    def undeploy_agent(self, name: str, *, agents_dir: Path) -> None:
        """Remove agent file from agents/ directory."""
        agent_file = agents_dir / f"expert-{name}.md"
        if agent_file.is_symlink() or agent_file.exists():
            agent_file.unlink()

    def deploy_expert(self, name: str, source_dir: Path) -> None:
        """Create symlink ~/.claude/experts/<name> -> source_dir."""
        provider_experts = self._home_dir / "experts"
        provider_experts.mkdir(parents=True, exist_ok=True)

        expert_link = provider_experts / name
        if expert_link.is_symlink():
            if expert_link.resolve() == source_dir.resolve():
                return  # Already correct
            expert_link.unlink()
        elif expert_link.exists():
            if expert_link.is_dir():
                shutil.rmtree(expert_link)
            else:
                expert_link.unlink()

        expert_link.symlink_to(source_dir)

    def undeploy_expert(self, name: str) -> None:
        """Remove ~/.claude/experts/<name> symlink."""
        expert_link = self._home_dir / "experts" / name
        if expert_link.is_symlink() or expert_link.exists():
            if expert_link.is_dir() and not expert_link.is_symlink():
                shutil.rmtree(expert_link)
            else:
                expert_link.unlink()

    def _post_init_dirs(
        self, *, permissions: dict | None = None
    ) -> list[tuple[str, str]]:
        """Generate settings.json from permissions config."""
        import json as _json

        results: list[tuple[str, str]] = []

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
            results.append(("settings.json", "generated from hivemind.json"))

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

    @property
    def experts_base_path(self) -> str:
        return "~/.config/opencode/experts"

    def _format_agent_md_internal(
        self, agent_name: str, description: str, body: str
    ) -> str:
        """Internal OpenCode agent formatting with custom name."""
        model = self._settings.get("model", "anthropic/claude-sonnet-4-20250514")
        temperature = self._settings.get("temperature", 0.1)
        tools = self._settings.get("tools", {})

        lines = [
            "---",
            f"description: {description}",
            "mode: subagent",
            f"model: {model}",
            f"temperature: {temperature}",
        ]

        if isinstance(tools, dict) and tools:
            lines.append("tools:")
            for tool_name, enabled in sorted(tools.items()):
                lines.append(f"  {tool_name}: {str(enabled).lower()}")

        # Generic permissions for hivemind paths
        lines.append("permission:")
        lines.append("  external_directory:")
        lines.append(f'    "~/.cache/hivemind/**": allow')
        lines.append(f'    "{self.experts_base_path}/**": allow')

        lines.append("---")
        lines.append("")
        lines.append("")

        frontmatter = "\n".join(lines)

        transformed = replace_expert_paths(
            body,
            old_base="{EXPERTS_DIR}",
            new_base=self.experts_base_path,
        )

        return frontmatter + transformed

    def format_agent_md(self, name: str, description: str, body: str) -> str:
        """Format agent.md with OpenCode YAML frontmatter."""
        return self._format_agent_md_internal(f"expert-{name}", description, body)

    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format lead agent with edit tool added for self-management."""
        model = self._settings.get("model", "anthropic/claude-sonnet-4-20250514")
        temperature = self._settings.get("temperature", 0.1)
        tools = dict(self._settings.get("tools", {}))
        if "edit" not in tools:
            tools["edit"] = True

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

        # Permissions for hivemind paths including teams/projects context
        home = self._config.get("home_dir", "~/.config/opencode")
        hivemind_subdir = f"{home}/hivemind"
        lines.append("permission:")
        lines.append("  external_directory:")
        lines.append(f'    "~/.cache/hivemind/**": allow')
        lines.append(f'    "{self.experts_base_path}/**": allow')
        lines.append(f'    "{hivemind_subdir}/teams/**": allow')
        lines.append(f'    "{hivemind_subdir}/projects/**": allow')

        lines.append("---")
        lines.append("")
        lines.append("")

        frontmatter = "\n".join(lines)

        transformed = replace_expert_paths(
            body,
            old_base="{EXPERTS_DIR}",
            new_base=self.experts_base_path,
        )

        return frontmatter + transformed

    def format_librarian_md(self, body: str) -> str:
        """Format librarian.md with OpenCode YAML frontmatter."""
        model = self._settings.get("model", "anthropic/claude-sonnet-4-20250514")
        temperature = self._settings.get("temperature", 0.1)

        lines = [
            "---",
            'description: "Hivemind librarian -- knows every expert agent and their '
            "capabilities. Ask the librarian to find the right expert for a question "
            'before delegating to specialists."',
            "mode: subagent",
            f"model: {model}",
            f"temperature: {temperature}",
            "tools:",
            "  read: true",
            "  grep: true",
            "  glob: true",
            "---",
            "",
            "",
        ]

        return "\n".join(lines) + body

    def build_analysis_command(
        self,
        *,
        extra_dirs: list[Path] | None = None,
    ) -> list[str]:
        """Build opencode run command for analysis."""
        cmd = shlex.split(self._engine)

        # Add model
        model = self._settings.get("model", "github-copilot/claude-sonnet-4")
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
        model = self._settings.get("model", "github-copilot/claude-sonnet-4")
        cmd.extend(["--model", model])
        return cmd

    def deploy_agent(self, name: str, content: str, *, agents_dir: Path) -> None:
        """Write agent file to agents/ directory.

        OpenCode reads from agents/ the same way, just uses regular files.
        """
        agents_dir.mkdir(parents=True, exist_ok=True)
        agent_file = agents_dir / f"expert-{name}.md"
        # Remove old symlink if present (migrating from symlink to file)
        if agent_file.is_symlink():
            agent_file.unlink()
        agent_file.write_text(content)

    def undeploy_agent(self, name: str, *, agents_dir: Path) -> None:
        """Remove agent file from agents/ directory."""
        agent_file = agents_dir / f"expert-{name}.md"
        if agent_file.is_symlink() or agent_file.exists():
            agent_file.unlink()

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

    def _post_init_dirs(
        self, *, permissions: dict | None = None
    ) -> list[tuple[str, str]]:
        """Generate/merge global permissions into opencode.json."""
        import json as _json

        results: list[tuple[str, str]] = []

        home = self._config.get("home_dir", "~/.config/opencode")
        experts_path = f"{home}/experts"
        hivemind_path = f"{home}/hivemind"

        hivemind_permissions = {
            "external_directory": {
                "~/.cache/hivemind/**": "allow",
                f"{experts_path}/**": "allow",
                f"{hivemind_path}/teams/**": "allow",
                f"{hivemind_path}/projects/**": "allow",
            },
            "read": {
                "~/.cache/hivemind/**": "allow",
                f"{experts_path}/**": "allow",
                f"{hivemind_path}/teams/**": "allow",
                f"{hivemind_path}/projects/**": "allow",
            },
            "grep": {
                "~/.cache/hivemind/**": "allow",
                f"{experts_path}/**": "allow",
            },
            "glob": {
                "~/.cache/hivemind/**": "allow",
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
            try:
                existing = _json.loads(config_path.read_text())
            except (ValueError, OSError):
                pass

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
        results.append(("opencode.json", "permissions merged for hivemind paths"))

        return results


# --- Provider Registry ---


PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "claude": ClaudeProvider,
    "opencode": OpenCodeProvider,
}


def get_provider(name: str, provider_config: dict) -> Provider:
    """Create a provider instance by name.

    Args:
        name: Provider name (e.g. "claude", "opencode")
        provider_config: Provider's config dict from config.json

    Returns:
        Provider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    cls = PROVIDER_CLASSES.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(PROVIDER_CLASSES)}"
        )
    return cls(provider_config)


# --- Internal Helpers ---


def _setup_symlink(target: Path, link: Path, label: str) -> tuple[str, str]:
    """Create or update a symlink, returning status for display.

    Args:
        target: What the symlink should point to
        link: Where to create the symlink
        label: Display label for status messages

    Returns:
        (label, status_message) tuple
    """
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            return (label, "already correct")
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        link.rename(backup)
        return (label, f"backed up existing dir to {backup.name}/, created symlink")
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    return (label, f"-> {target}")
