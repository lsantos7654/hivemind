"""Jinja2 template loader for hivemind agent generation.

Templates live in the `templates/` directory at the repository root.
This module provides convenience functions that match the old API so
call sites in core.py don't need to change.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    keep_trailing_newline=True,
    undefined=__import__("jinja2").StrictUndefined,
)


def render(template_name: str, **kwargs: object) -> str:
    """Render a Jinja2 template by name."""
    return _env.get_template(template_name).render(**kwargs)


# --- HIVEMIND.md ---


def hivemind_md_base(root_path: str) -> str:
    return render("hivemind.md.j2", root_path=root_path)


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


def expert_section_prompt(
    expert_name: str,
    team_name: str,
    expert_dir: Path,
) -> str:
    return render(
        "prompts/expert_section.md.j2",
        expert_name=expert_name,
        team_name=team_name,
        expert_dir=expert_dir,
    )
