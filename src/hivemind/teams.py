"""Team management operations for hivemind."""

from __future__ import annotations

import asyncio
import shutil
from typing import TYPE_CHECKING

from hivemind.config import (
    TEAMS_DIR,
    get_active_provider,
    get_expert_dir,
    load_teams,
    save_teams,
)
from hivemind.config import (
    expert_names as get_all_expert_names,
)
from hivemind.deployment import (
    deploy_team_lead,
    flush_librarian,
    mark_librarian_dirty,
    undeploy_team_lead,
)
from hivemind.models import AddExpertsResult, AppConfig, ExpertError, OperationResult, TeamData

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "add_expert_to_team",
    "add_experts_to_team",
    "create_expert_notes_stub",
    "create_team",
    "create_team_lead_notes_stub",
    "delete_team",
    "generate_expert_section",
    "refresh_expert_notes_header",
    "refresh_team_lead_body",
    "refresh_team_lead_notes_header",
    "remove_expert_from_team",
    "remove_expert_section",
    "update_team",
]


async def generate_expert_section(expert_name: str, team_name: str) -> str | None:
    """AI-generate a ## expert-{name} section for a team lead.

    Calls the provider's analysis engine with the expert's knowledge docs.
    Returns the generated markdown section, or None on failure.
    """
    from hivemind.templates import expert_section_prompt

    expert_dir = get_expert_dir(expert_name)
    head_dir = expert_dir / "HEAD"
    if not head_dir.exists():
        return None

    prompt = expert_section_prompt(expert_name, team_name, head_dir)

    provider = get_active_provider()
    cmd = provider.build_analysis_command(extra_dirs=[head_dir])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate(prompt.encode())

    if proc.returncode != 0:
        return None

    # The AI should write to stdout, not a file
    output = stdout.decode().strip() if stdout else ""
    if output and f"## expert-{expert_name}" in output:
        # Extract just the section (in case there's extra output)
        idx = output.index(f"## expert-{expert_name}")
        return output[idx:]
    return None


def remove_expert_section(team_name: str, expert_name: str) -> bool:
    """Remove ## expert-{name} section from lead.md.

    Deletes everything from the ## expert-{name} heading to the next ## heading
    or end of file. Returns True if section was found and removed.
    """
    lead_md = TEAMS_DIR / team_name / "lead.md"
    if not lead_md.exists():
        return False

    content = lead_md.read_text(encoding="utf-8")
    heading = f"## expert-{expert_name}"

    if heading not in content:
        return False

    lines = content.split("\n")
    result: list[str] = []
    skipping = False

    for line in lines:
        if line.strip() == heading:
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            result.append(line)

    # Clean up double blank lines
    cleaned = "\n".join(result)
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")

    lead_md.write_text(cleaned, encoding="utf-8")
    return True


def create_expert_notes_stub(team_name: str, expert_name: str) -> None:
    """Create teams/{team}/expert-{name}/notes.md from template."""
    from hivemind.templates import expert_notes_template

    notes_dir = TEAMS_DIR / team_name / f"expert-{expert_name}"
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(expert_notes_template(expert_name, team_name), encoding="utf-8")


def refresh_expert_notes_header(team_name: str, expert_name: str) -> None:
    """Regenerate the template header in notes.md, preserving entries below ---."""
    from hivemind.templates import expert_notes_template

    notes_file = TEAMS_DIR / team_name / f"expert-{expert_name}" / "notes.md"
    if not notes_file.exists():
        create_expert_notes_stub(team_name, expert_name)
        return

    content = notes_file.read_text(encoding="utf-8")
    template = expert_notes_template(expert_name, team_name)

    # Template ends with "---\n", entries live below that
    separator = "\n---\n"
    if separator in content:
        _, entries = content.split(separator, 1)
        # Template already ends with "---\n", append preserved entries
        notes_file.write_text(template + entries, encoding="utf-8")
    else:
        # No entries yet — rewrite from template
        notes_file.write_text(template, encoding="utf-8")


def create_team_lead_notes_stub(team_name: str) -> None:
    """Create teams/{team}/notes.md from template."""
    from hivemind.templates import team_lead_notes_template

    team_dir = TEAMS_DIR / team_name
    team_dir.mkdir(parents=True, exist_ok=True)
    notes_file = team_dir / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(team_lead_notes_template(team_name), encoding="utf-8")


def refresh_team_lead_notes_header(team_name: str) -> None:
    """Regenerate the template header in team notes.md, preserving entries below ---."""
    from hivemind.templates import team_lead_notes_template

    notes_file = TEAMS_DIR / team_name / "notes.md"
    if not notes_file.exists():
        create_team_lead_notes_stub(team_name)
        return

    content = notes_file.read_text(encoding="utf-8")
    template = team_lead_notes_template(team_name)

    # Template ends with "---\n", entries live below that
    separator = "\n---\n"
    if separator in content:
        _, entries = content.split(separator, 1)
        # Template already ends with "---\n", append preserved entries
        notes_file.write_text(template + entries, encoding="utf-8")
    else:
        # No entries yet — rewrite from template
        notes_file.write_text(template, encoding="utf-8")


def refresh_team_lead_body(team_name: str) -> None:
    """Regenerate lead.md wrapper from template, preserving ## expert-{name} sections."""
    from hivemind.templates import team_lead_template

    lead_md = TEAMS_DIR / team_name / "lead.md"
    if not lead_md.exists():
        return

    teams = load_teams()
    if team_name not in teams:
        return

    team_data = teams[team_name]
    description = team_data.description

    # Extract existing ## expert-{name} sections from current lead.md
    content = lead_md.read_text(encoding="utf-8")
    lines = content.split("\n")
    expert_sections: list[str] = []
    current_section: list[str] = []
    in_expert_section = False

    for line in lines:
        if line.startswith("## expert-"):
            if current_section:
                expert_sections.append("\n".join(current_section))
            current_section = [line]
            in_expert_section = True
        elif line.startswith("## ") and in_expert_section:
            if current_section:
                expert_sections.append("\n".join(current_section))
                current_section = []
            in_expert_section = False
        elif in_expert_section:
            current_section.append(line)

    if current_section:
        expert_sections.append("\n".join(current_section))

    # Regenerate wrapper with preserved expert sections
    expert_content = "\n\n".join(s.rstrip() for s in expert_sections) if expert_sections else ""
    lead_body = team_lead_template(team_name, description, expert_content)
    lead_md.write_text(lead_body, encoding="utf-8")


async def create_team(
    name: str,
    description: str,
    experts: list[str],
    config: AppConfig,
) -> OperationResult:
    """Create a new team."""
    teams = config.teams
    if name in teams:
        return OperationResult(success=False, error=f"Team '{name}' already exists")

    # Validate experts exist
    all_experts = set(get_all_expert_names())
    for expert in experts:
        if expert not in all_experts:
            return OperationResult(success=False, error=f"Expert '{expert}' does not exist")

    # Create team directory
    team_dir = TEAMS_DIR / name
    team_dir.mkdir(parents=True, exist_ok=True)

    # Generate expert sections
    expert_sections: list[str] = []
    for expert_name in experts:
        section = await generate_expert_section(expert_name, name)
        if not section:
            shutil.rmtree(team_dir)
            return OperationResult(
                success=False,
                error=f"AI generation failed for expert section: {expert_name}",
            )
        expert_sections.append(section)

    # Create notes stubs (only after all sections generated successfully)
    for expert_name in experts:
        create_expert_notes_stub(name, expert_name)
    create_team_lead_notes_stub(name)

    # Assemble lead.md
    from hivemind.templates import team_lead_template

    lead_body = team_lead_template(name, description, "\n\n".join(expert_sections))
    (team_dir / "lead.md").write_text(lead_body, encoding="utf-8")

    # Save to config
    teams[name] = TeamData(description=description, experts=experts)
    save_teams(teams, config=config)

    # Deploy
    deploy_team_lead(name)
    mark_librarian_dirty()
    flush_librarian(config=config)

    return OperationResult(success=True)


def delete_team(name: str, config: AppConfig) -> OperationResult:
    """Delete a team and all its deployed agents."""
    teams = config.teams
    if name not in teams:
        return OperationResult(success=False, error=f"Team '{name}' does not exist")

    # Undeploy
    undeploy_team_lead(name)

    # Remove team directory
    team_dir = TEAMS_DIR / name
    if team_dir.exists():
        shutil.rmtree(team_dir)

    # Remove from config
    del teams[name]
    save_teams(teams, config=config)

    mark_librarian_dirty()
    flush_librarian(config=config)
    return OperationResult(success=True)


def update_team(
    name: str,
    *,
    new_name: str | None = None,
    description: str | None = None,
    config: AppConfig,
) -> OperationResult:
    """Update a team's name and/or description."""
    teams = config.teams
    if name not in teams:
        return OperationResult(success=False, error=f"Team '{name}' does not exist")

    team = teams[name]

    if description is not None:
        team.description = description

    if new_name and new_name != name:
        if new_name in teams:
            return OperationResult(success=False, error=f"Team '{new_name}' already exists")

        # Rename key in teams dict
        teams[new_name] = teams.pop(name)

        # Rename team directory
        old_dir = TEAMS_DIR / name
        new_dir = TEAMS_DIR / new_name
        if old_dir.exists():
            old_dir.rename(new_dir)

        # Redeploy team agents under new name
        undeploy_team_lead(name)
        save_teams(teams, config=config)
        deploy_team_lead(new_name)
        mark_librarian_dirty()
        flush_librarian(config=config)
    else:
        save_teams(teams, config=config)
        deploy_team_lead(name)
        mark_librarian_dirty()
        flush_librarian(config=config)

    return OperationResult(success=True)


async def add_experts_to_team(
    team_name: str,
    expert_names: list[str],
    *,
    on_progress: Callable[[str], None] | None = None,
    config: AppConfig,
) -> AddExpertsResult:
    """Add multiple experts to a team's roster in one operation.

    AI-generates expert sections, creates notes stubs, and redeploys
    the team lead + librarian only once at the end.
    """
    teams = config.teams
    if team_name not in teams:
        return AddExpertsResult(
            success=False,
            error=f"Team '{team_name}' does not exist",
        )

    team = teams[team_name]
    existing = team.experts
    all_experts = set(get_all_expert_names())

    added: list[str] = []
    skipped: list[str] = []
    failed: list[ExpertError] = []

    lead_md = TEAMS_DIR / team_name / "lead.md"

    for expert_name in expert_names:
        if expert_name in existing:
            skipped.append(expert_name)
            continue
        if expert_name not in all_experts:
            failed.append(ExpertError(name=expert_name, error="does not exist"))
            continue

        if on_progress:
            on_progress(expert_name)

        section = await generate_expert_section(expert_name, team_name)
        if not section:
            failed.append(ExpertError(name=expert_name, error="AI generation failed"))
            continue

        # Append section to lead.md
        if lead_md.exists():
            content = lead_md.read_text(encoding="utf-8")
            for marker in ["## Expert Notes", "## Instructions"]:
                if marker in content:
                    idx = content.index(marker)
                    content = content[:idx] + section + "\n\n" + content[idx:]
                    break
            else:
                content += "\n\n" + section + "\n"
            lead_md.write_text(content, encoding="utf-8")

        create_expert_notes_stub(team_name, expert_name)
        existing.append(expert_name)
        added.append(expert_name)

    # Save config and redeploy once
    if added:
        team.experts = existing
        save_teams(teams, config=config)
        deploy_team_lead(team_name)
        mark_librarian_dirty()
        flush_librarian(config=config)

    return AddExpertsResult(success=True, added=added, skipped=skipped, failed=failed)


async def add_expert_to_team(team_name: str, expert_name: str, config: AppConfig) -> OperationResult:
    """Add an expert to a team's roster.

    AI-generates a new ## expert-{name} section in lead.md,
    creates a notes.md stub, and redeploys the team lead.
    """
    teams = config.teams
    if team_name not in teams:
        return OperationResult(success=False, error=f"Team '{team_name}' does not exist")

    team = teams[team_name]
    experts = team.experts

    if expert_name in experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' already on team")

    # Validate expert exists
    all_experts = set(get_all_expert_names())
    if expert_name not in all_experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' does not exist")

    # Generate expert section for lead.md
    section = await generate_expert_section(expert_name, team_name)
    if not section:
        return OperationResult(
            success=False,
            error=f"AI generation failed for expert section: {expert_name}",
        )

    # Append section to lead.md
    lead_md = TEAMS_DIR / team_name / "lead.md"
    if lead_md.exists():
        content = lead_md.read_text(encoding="utf-8")
        # Insert before ## Instructions or ## Expert Notes (whichever comes first)
        for marker in ["## Expert Notes", "## Instructions"]:
            if marker in content:
                idx = content.index(marker)
                content = content[:idx] + section + "\n\n" + content[idx:]
                break
        else:
            content += "\n\n" + section + "\n"
        lead_md.write_text(content, encoding="utf-8")

    # Create notes stub
    create_expert_notes_stub(team_name, expert_name)

    # Update config
    experts.append(expert_name)
    team.experts = experts
    save_teams(teams, config=config)

    # Redeploy team lead (roster list updates automatically)
    deploy_team_lead(team_name)
    mark_librarian_dirty()
    flush_librarian(config=config)

    return OperationResult(success=True)


def remove_expert_from_team(team_name: str, expert_name: str, config: AppConfig) -> OperationResult:
    """Remove an expert from a team's roster.

    Removes the ## expert-{name} section from lead.md,
    deletes the expert's notes directory, and redeploys the team lead.
    """
    teams = config.teams
    if team_name not in teams:
        return OperationResult(success=False, error=f"Team '{team_name}' does not exist")

    team = teams[team_name]
    experts = team.experts

    if expert_name not in experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' not on team")

    # Remove expert section from lead.md
    remove_expert_section(team_name, expert_name)

    # Remove expert notes directory
    notes_dir = TEAMS_DIR / team_name / f"expert-{expert_name}"
    if notes_dir.exists():
        shutil.rmtree(notes_dir)

    # Update config
    experts.remove(expert_name)
    team.experts = experts
    save_teams(teams, config=config)

    # Redeploy team lead (roster list updates automatically)
    deploy_team_lead(team_name)
    mark_librarian_dirty()
    flush_librarian(config=config)
    return OperationResult(success=True)
