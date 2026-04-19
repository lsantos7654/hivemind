"""Jinja2 template loader for hivemind agent generation.

Templates live in the `templates/` directory inside the package.
Domain content constants (descriptions, prompts) also live here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, StrictUndefined

LIBRARIAN_DESCRIPTION: str = (
    "Hivemind librarian -- knows every expert agent and their "
    "capabilities. Ask the librarian to find the right expert for a question "
    "before delegating to specialists."
)

if TYPE_CHECKING:
    from pathlib import Path

_env = Environment(
    loader=PackageLoader("hivemind", "templates"),
    keep_trailing_newline=True,
    undefined=StrictUndefined,
)


def render(template_name: str, **kwargs: object) -> str:
    """Render a Jinja2 template by name."""
    return _env.get_template(template_name).render(**kwargs)


# --- HIVEMIND.md ---


def hivemind_md_base(teams_path: str) -> str:
    return render("hivemind.md.j2", teams_path=teams_path)


# --- Team Lead ---


def team_lead_template(
    team_name: str,
    description: str,
    expert_sections: str,
) -> str:
    return render(
        "team_lead.md.j2",
        team_name=team_name,
        description=description,
        expert_sections=expert_sections,
    )


# --- Expert Notes ---


def expert_notes_template(expert_name: str, team_name: str) -> str:
    return render(
        "expert_notes.md.j2",
        expert_name=expert_name,
        team_name=team_name,
    )


# --- Team Lead Notes ---


def team_lead_notes_template(team_name: str) -> str:
    return render(
        "team_lead_notes.md.j2",
        team_name=team_name,
    )


# --- Expert Agent ---


def agent_md_template(name: str, commit: str) -> str:
    return render("agent.md.j2", name=name, commit=commit)


# --- AI Prompts ---


def create_expert_prompt(
    name: str,
    commit: str,
    repo_dir: Path,
    commit_dir: Path,
) -> str:
    return render(
        "prompts/create_expert.md.j2",
        name=name,
        commit=commit,
        repo_dir=repo_dir,
        commit_dir=commit_dir,
        agent_template=agent_md_template(name, commit),
    )


def update_expert_prompt(
    name: str,
    commit: str,
    repo_dir: Path,
    commit_dir: Path,
) -> str:
    return render(
        "prompts/update_expert.md.j2",
        name=name,
        commit=commit,
        repo_dir=repo_dir,
        commit_dir=commit_dir,
    )


def regenerate_agent_prompt(
    name: str,
    commit: str,
    repo_dir: Path,
    commit_dir: Path,
) -> str:
    return render(
        "prompts/regenerate_agent.md.j2",
        name=name,
        commit=commit,
        repo_dir=repo_dir,
        commit_dir=commit_dir,
        agent_template=agent_md_template(name, commit),
    )


def expert_sections_prompt(
    experts: list[dict[str, str]],
    team_name: str,
) -> str:
    """Render a prompt for generating expert sections for a team lead.

    Each entry in experts should have 'name' and 'summary' keys.
    """
    return render(
        "prompts/expert_sections.md.j2",
        experts=experts,
        team_name=team_name,
    )
