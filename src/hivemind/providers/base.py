"""Abstract provider base class for multi-platform AI coding agent support.

Each provider (Claude Code, OpenCode, etc.) defines how to:
- Format agent files (frontmatter + body)
- Build analysis engine commands
- Deploy agents, experts, commands, and rules to the provider's directory
- Initialize the provider's directory structure
"""

from __future__ import annotations

import json
import shlex
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from hivemind.constants import CACHE_DIR, CACHE_DIR_PLACEHOLDER, EXPERTS_DIR_PLACEHOLDER, TEAMS_DIR_PLACEHOLDER
from hivemind.models import InitResult, OperationResult, ProviderConfig, ProviderSettings

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
    """Abstract base for AI coding platform providers.

    Owns: shared deployment pipeline, path transforms, symlink management,
    engine validation, context injection.

    Declares abstract: all formatting methods and engine command builders.
    Each provider implements formatting with its own native types.
    """

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
    def model(self) -> str:
        """Configured model string. Raises if not set."""
        if not self._settings.model:
            msg = (
                f"No model configured for provider '{self.name}'. "
                f"Set 'settings.model' in hivemind.json under providers.{self.name}."
            )
            raise ValueError(msg)
        return self._settings.model

    def validate_engine(self) -> OperationResult:
        """Validate that the analysis engine binary and model are available.

        Subclasses should override to add model-level validation.

        Returns:
            OperationResult with success=False and descriptive error if validation fails.
        """
        if not self._engine:
            return OperationResult(
                success=False,
                error=f"No engine configured for provider '{self.name}'. "
                f"Set 'engine' in hivemind.json under providers.{self.name}.",
            )

        binary = shlex.split(self._engine)[0]
        if not shutil.which(binary):
            return OperationResult(
                success=False,
                error=f"Analysis engine '{binary}' not found on PATH. Install it first.",
            )

        if not self._settings.model:
            return OperationResult(
                success=False,
                error=f"No model configured for provider '{self.name}'. "
                f"Set 'settings.model' in hivemind.json under providers.{self.name}.",
            )

        return OperationResult(success=True)

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
            data = json.loads(context_path.read_text(encoding="utf-8"))
            append = data.get(agent_type, {}).get("append", "")
            if append:
                parts.append(append)

        # User overrides (not committed)
        overrides_path = self._providers_dir / self.name / "overrides.json"
        if overrides_path.exists():
            data = json.loads(overrides_path.read_text(encoding="utf-8"))
            append = data.get(agent_type, {}).get("append", "")
            if append:
                parts.append(append)

        return "".join(parts)

    # --- Agent formatting (all abstract -- each provider implements directly) ---

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

    @abstractmethod
    def format_lead_md(self, agent_name: str, description: str, body: str) -> str:
        """Format a lead agent file (team lead or project lead).

        Each provider implements this directly with its own native tool types
        and permission handling. No shared hook machinery.

        Args:
            agent_name: Full agent name (e.g. "team-lead-nix-infra")
            description: Agent description for frontmatter
            body: Platform-neutral markdown body (no frontmatter)

        Returns:
            Complete agent content with provider frontmatter + transformed body
        """

    @abstractmethod
    def format_librarian_md(self, body: str) -> str:
        """Format the librarian agent file.

        Each provider implements this directly with its own native tool types
        and formatting. The librarian description is imported from templates.py.

        Args:
            body: Librarian markdown body

        Returns:
            Complete librarian content with provider frontmatter + transformed body
        """

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

        # teams/ symlink directly under provider home
        if teams_dir:
            results.append(_setup_symlink(teams_dir, self._home_dir / "teams", "teams/"))

        # Provider-specific hook
        results.extend(self._post_init_dirs(permissions=permissions))

        return results

    def _post_init_dirs(self, *, permissions: dict[str, object] | None = None) -> list[InitResult]:
        """Provider-specific init steps. Override in subclasses."""
        return []


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
