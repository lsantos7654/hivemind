"""Agent deployment, librarian generation, and HIVEMIND.md for hivemind."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from hivemind.config import (
    AGENTS_DIR,
    EXPERTS_DIR,
    HIVEMIND_MD,
    HIVEMIND_ROOT,
    PRIVATE_EXPERTS_DIR,
    PROVIDERS_DIR,
    TEAMS_DIR,
    get_active_provider,
    get_expert_dir,
    load_teams,
)
from hivemind.providers import extract_description, strip_frontmatter

if TYPE_CHECKING:
    from collections.abc import Generator

    from hivemind.models import AppConfig

__all__ = [
    "_librarian_dirty",
    "deploy_agent",
    "deploy_expert",
    "deploy_team_lead",
    "flush_librarian",
    "librarian_batch",
    "mark_librarian_dirty",
    "regenerate_hivemind_md",
    "undeploy_agent",
    "undeploy_expert",
    "undeploy_team_lead",
    "update_librarian",
]


def deploy_agent(name: str) -> bool:
    """Generate and deploy agent file with provider-specific frontmatter.

    Reads the canonical body from experts/{name}/HEAD/agent.md, strips any
    existing frontmatter, extracts the description, and generates a new file
    with the active provider's frontmatter and path transformations.

    Returns False if HEAD/agent.md doesn't exist.
    """
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    expert_dir = get_expert_dir(name)
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        return False

    provider = get_active_provider()

    # Read canonical body and strip any frontmatter
    raw_content = head_agent.read_text(encoding="utf-8")
    body = strip_frontmatter(raw_content)
    body += provider.get_context_append("expert")
    description = extract_description(body)

    # Generate provider-specific content
    content = provider.format_agent_md(name, description, body)

    # Deploy to agents/ directory
    provider.deploy_agent(name, content, agents_dir=AGENTS_DIR)
    return True


def undeploy_agent(name: str) -> None:
    """Remove agents/expert-<name>.md if it exists."""
    provider = get_active_provider()
    provider.undeploy_agent(name, agents_dir=AGENTS_DIR)


def deploy_expert(name: str) -> bool:
    """Deploy expert directory to active provider's expert location.

    Returns True if deployed, False if expert doesn't exist.
    """
    source_dir = get_expert_dir(name)
    if not source_dir.exists():
        return False

    provider = get_active_provider()
    provider.deploy_expert(name, source_dir)
    return True


def undeploy_expert(name: str) -> None:
    """Remove expert from active provider's expert location."""
    provider = get_active_provider()
    provider.undeploy_expert(name)


_librarian_dirty = False


def mark_librarian_dirty() -> None:
    """Mark the librarian catalog as needing regeneration."""
    global _librarian_dirty
    _librarian_dirty = True


def flush_librarian(config: AppConfig) -> None:
    """Regenerate the librarian catalog if marked dirty."""
    global _librarian_dirty
    if _librarian_dirty:
        update_librarian(config=config)
        _librarian_dirty = False


@contextlib.contextmanager
def librarian_batch(config: AppConfig) -> Generator[None, None, None]:
    """Context manager that regenerates the librarian once at exit.

    Use instead of manual mark_librarian_dirty() + flush_librarian() pairs.
    """
    try:
        yield
    finally:
        update_librarian(config=config)


def update_librarian(config: AppConfig) -> None:
    """Regenerate agents/librarian.md from enabled experts with valid HEAD/agent.md."""
    enabled_experts = set(config.enabled)

    entries: list[str] = []

    # Scan both public and private experts
    for expert_base_dir in [EXPERTS_DIR, PRIVATE_EXPERTS_DIR]:
        if not expert_base_dir.exists():
            continue
        for expert_dir in sorted(expert_base_dir.iterdir()):
            if not expert_dir.is_dir():
                continue
            name = expert_dir.name

            # Skip if not enabled
            if name not in enabled_experts:
                continue

            agent_md = expert_dir / "HEAD" / "agent.md"
            if not agent_md.exists():
                continue

            # Extract description from body (not frontmatter)
            description = ""
            try:
                text = agent_md.read_text(encoding="utf-8")
                body = strip_frontmatter(text)
                description = extract_description(body)
            except OSError:
                pass

            # Read first ~5 lines of summary.md
            summary_lines = ""
            summary_md = expert_dir / "HEAD" / "summary.md"
            try:
                lines = summary_md.read_text(encoding="utf-8").splitlines()
                summary_lines = "\n".join(lines[:5])
            except OSError:
                pass

            entry = f"### expert-{name}\n{description}\n\n{summary_lines}"
            entries.append(entry)

    # Generate catalog even if empty, so librarian reflects current state
    catalog = "\n\n---\n\n".join(entries) if entries else "No experts are currently enabled."

    # Build team catalog
    teams = load_teams()
    team_entries: list[str] = []
    for team_name, team_data in sorted(teams.items()):
        desc = team_data.description
        experts = team_data.experts
        roster = ", ".join(experts)
        entry = (
            f"### team-lead-{team_name}\n"
            f"Team lead for {desc}. Roster: {roster}.\n"
            f"Consult this team lead for routing and coordination within this domain."
        )
        team_entries.append(entry)
    team_catalog = "\n\n---\n\n".join(team_entries) if team_entries else "No teams configured."

    # Build librarian body
    librarian_body = (
        "# Hivemind Librarian\n\n"
        "You are the hivemind librarian. You know every registered expert and team "
        "and what they specialize in. When asked a question, identify which "
        "expert(s) or team lead(s) are best suited and recommend them by name.\n\n"
        "## Expert Catalog\n\n"
        f"{catalog}\n\n"
        "## Team Catalog\n\n"
        f"{team_catalog}\n\n"
        "## Instructions\n\n"
        "1. For cross-expert coordination within a team's domain, recommend the team lead\n"
        "2. For domain-specific questions, recommend the expert\n"
        "3. Respond with agent name(s) and why they're the right fit\n"
        "4. If multiple agents are relevant, rank by relevance\n"
        "5. If no match, say so clearly\n"
    )

    # Format with provider-specific frontmatter
    provider = get_active_provider()
    content = provider.format_librarian_md(librarian_body)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    (AGENTS_DIR / "librarian.md").write_text(content, encoding="utf-8")


def regenerate_hivemind_md(config: AppConfig) -> None:
    """Regenerate HIVEMIND.md from base template + provider instructions."""
    from hivemind.templates import hivemind_md_base

    content = hivemind_md_base(str(HIVEMIND_ROOT))

    # Append provider-specific orchestration instructions
    active_provider = config.active_provider
    if active_provider:
        provider_instructions = PROVIDERS_DIR / active_provider / "instructions.md"
        if provider_instructions.exists():
            instructions_content = provider_instructions.read_text(encoding="utf-8").strip()
            if instructions_content:
                content += "\n" + instructions_content + "\n"

    HIVEMIND_MD.write_text(content, encoding="utf-8")


def deploy_team_lead(team_name: str) -> bool:
    """Deploy team lead agent file with provider-specific frontmatter.

    Reads teams/{team_name}/lead.md, injects current roster from config,
    appends provider context, applies frontmatter, writes to
    agents/team-lead-{team_name}.md.

    Returns False if lead.md does not exist.
    """
    lead_md = TEAMS_DIR / team_name / "lead.md"
    if not lead_md.exists():
        return False

    provider = get_active_provider()
    body = strip_frontmatter(lead_md.read_text(encoding="utf-8"))

    # Inject current roster from config via sentinel replacement
    teams = load_teams()
    if team_name in teams:
        experts = teams[team_name].experts
        roster_lines = "\n".join(f"- expert-{e}" for e in experts)
        roster_section = f"## Team Roster\n\n{roster_lines}"
        body = body.replace("<!-- ROSTER -->", roster_section)

    body += provider.get_context_append("team_lead")
    description = extract_description(body)

    content = provider.format_lead_md(f"team-lead-{team_name}", description, body)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    agent_file = AGENTS_DIR / f"team-lead-{team_name}.md"
    if agent_file.is_symlink():
        agent_file.unlink()
    agent_file.write_text(content, encoding="utf-8")
    return True


def undeploy_team_lead(team_name: str) -> None:
    """Remove agents/team-lead-{team_name}.md if it exists."""
    agent_file = AGENTS_DIR / f"team-lead-{team_name}.md"
    if agent_file.is_symlink() or agent_file.exists():
        agent_file.unlink()
