"""Deployment glue: librarian catalog + HIVEMIND.md regeneration.

Per-agent deploy / undeploy lives on ``Agent.deploy`` / ``Agent.undeploy``
(which consult the opencode module and the body strategy). This file keeps
the librarian-catalog and HIVEMIND.md helpers that don't fit on any single
agent.
"""

from __future__ import annotations

from hivemind import opencode
from hivemind.config import AGENTS_DIR, HIVEMIND_MD

__all__ = [
    "regenerate_hivemind_md",
    "regenerate_librarian",
]


def regenerate_librarian() -> None:
    """Rebuild ``agents/librarian.md`` from every currently-enabled agent."""
    from hivemind.agents import registry

    enabled = registry.enabled()

    expert_entries: list[str] = []
    team_entries: list[str] = []
    for agent in enabled:
        entry = agent.body.librarian_entry()
        if agent.kind == "roster_templated":
            team_entries.append(entry)
        else:
            expert_entries.append(entry)

    catalog = "\n\n---\n\n".join(expert_entries) if expert_entries else "No experts are currently enabled."
    team_catalog = "\n\n---\n\n".join(team_entries) if team_entries else "No teams configured."

    librarian_body = (
        "# Hivemind Librarian\n\n"
        "You are the hivemind librarian. You know every registered expert "
        "and team and what they specialize in. When asked a question, "
        "identify which expert(s) or team lead(s) are best suited and "
        "recommend them by name.\n\n"
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

    content = opencode.format_agent("librarian", "librarian", "", librarian_body)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    (AGENTS_DIR / "librarian.md").write_text(content, encoding="utf-8")


def regenerate_hivemind_md() -> None:
    """Rebuild HIVEMIND.md from the template."""
    from hivemind.templates import hivemind_md_base

    content = hivemind_md_base(opencode.teams_base_path())
    HIVEMIND_MD.write_text(content, encoding="utf-8")
