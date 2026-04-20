"""``RosterTemplatedBody`` — body strategy for team lead agents.

A team lead agent is assembled from a ``lead.md`` template plus a roster of
member experts. Membership mutations (``add_expert_to_team`` /
``remove_expert_from_team``) AI-generate per-expert sections that are spliced
into ``lead.md``. Enable/disable behaves like any other agent: the deployed
``agents/team-lead-<name>.md`` is present when enabled and absent when not.

Roster mutations are refused while the team is disabled — you must enable
the team before modifying its roster.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import TYPE_CHECKING, Any

from hivemind import opencode
from hivemind.config import (
    TEAMS_DIR,
    get_expert_dir,
)
from hivemind.config import (
    expert_names as get_all_expert_names,
)
from hivemind.git import clone_from_remote
from hivemind.hooks import afire_post_mutation, fire_post_mutation
from hivemind.models import (
    AddExpertsResult,
    ExpertError,
    OperationResult,
)
from hivemind.templates import (
    expert_notes_template,
    expert_sections_prompt,
    team_lead_notes_template,
    team_lead_template,
)

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)


__all__ = [
    "RosterTemplatedBody",
    "add_expert_to_team",
    "add_experts_to_team",
    "create_expert_notes_stub",
    "create_team",
    "create_team_lead_notes_stub",
    "refresh_expert_notes_header",
    "refresh_team_lead_body",
    "refresh_team_lead_notes_header",
    "remove_expert_from_team",
    "remove_expert_section",
    "update_team",
]

_SECTION_BATCH_SIZE = 15


# ---------------------------------------------------------------------------
# Body strategy
# ---------------------------------------------------------------------------


class RosterTemplatedBody:
    """Body strategy for team lead agents."""

    kind: str = "roster_templated"

    def __init__(
        self,
        name: str,
        *,
        description: str,
        experts: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.experts: list[str] = list(experts) if experts else []

    # --- catalog (de)serialisation -----------------------------------------

    @classmethod
    def from_catalog(cls, name: str, params: dict[str, Any]) -> RosterTemplatedBody:
        raw_experts = params.get("experts") or []
        if not isinstance(raw_experts, list):
            raw_experts = []
        return cls(
            name=name,
            description=str(params.get("description", "")),
            experts=[str(e) for e in raw_experts],
        )

    def to_catalog(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "experts": list(self.experts),
        }

    # --- body protocol -----------------------------------------------------

    def render(self) -> str:
        """Return lead.md with the current roster spliced in."""
        lead_md = TEAMS_DIR / self.name / "lead.md"
        if not lead_md.exists():
            return ""
        body = opencode.strip_frontmatter(lead_md.read_text(encoding="utf-8"))
        roster_lines = "\n".join(f"- expert-{e}" for e in self.experts)
        roster_section = f"## Team Roster\n\n{roster_lines}"
        return body.replace("<!-- ROSTER -->", roster_section)

    def librarian_entry(self) -> str:
        roster = ", ".join(self.experts)
        return (
            f"### team-lead-{self.name}\n"
            f"Team lead for {self.description}. Roster: {roster}.\n"
            f"Consult this team lead for routing and coordination within this domain."
        )

    def on_deploy(self) -> None:
        """Ensure every roster member has its repo cached locally."""
        from hivemind.agents import registry
        from hivemind.agents.base import run_coro_sync
        from hivemind.agents.git_analyzed import GitAnalyzedBody

        for expert_name in self.experts:
            member = registry.get(expert_name)
            if member is None or not isinstance(member.body, GitAnalyzedBody):
                continue
            try:
                run_coro_sync(
                    clone_from_remote(
                        expert_name,
                        member.body.remote,
                        commit=member.body.commit,
                        ref_name=member.body.ref_name,
                        silent=True,
                    )
                )
            except Exception:
                log.exception("failed to clone member repo %s", expert_name)

    def on_undeploy(self) -> None:
        # The deployed agent file is removed by ``Agent.undeploy``; nothing
        # else to clean up here (team dir + notes + member repos preserved).
        pass

    def on_delete(self) -> None:
        team_dir = TEAMS_DIR / self.name
        if team_dir.exists():
            shutil.rmtree(team_dir)


# ---------------------------------------------------------------------------
# AI section generation (unchanged from legacy teams.py)
# ---------------------------------------------------------------------------


def _read_expert_summary(expert_name: str) -> str:
    expert_dir = get_expert_dir(expert_name)
    summary = expert_dir / "HEAD" / "summary.md"
    if summary.is_file():
        return summary.read_text(encoding="utf-8").strip()
    return ""


def _parse_expert_sections(output: str, expert_names: list[str]) -> dict[str, str]:
    sections: dict[str, str] = {}
    for name in expert_names:
        marker = f"## expert-{name}"
        if marker not in output:
            continue
        start = output.index(marker)
        next_start = len(output)
        for other_name in expert_names:
            if other_name == name:
                continue
            other_marker = f"## expert-{other_name}"
            pos = output.find(other_marker, start + len(marker))
            if pos != -1 and pos < next_start:
                next_start = pos
        sections[name] = output[start:next_start].strip()
    return sections


async def generate_expert_sections(expert_names: list[str], team_name: str) -> dict[str, str]:
    """AI-generate ``## expert-{name}`` sections in batched parallel calls."""
    expert_data: list[dict[str, str]] = []
    for name in expert_names:
        summary = _read_expert_summary(name)
        if not summary:
            continue
        expert_data.append({"name": name, "summary": summary})

    if not expert_data:
        return {}

    batches: list[list[dict[str, str]]] = [
        expert_data[i : i + _SECTION_BATCH_SIZE] for i in range(0, len(expert_data), _SECTION_BATCH_SIZE)
    ]

    async def _run_batch(batch: list[dict[str, str]]) -> dict[str, str]:
        prompt = expert_sections_prompt(batch, team_name)
        cmd = opencode.build_analysis_command()

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate(prompt.encode())

        if proc.returncode != 0:
            return {}

        output = stdout.decode().strip() if stdout else ""
        names = [e["name"] for e in batch]
        return _parse_expert_sections(output, names)

    batch_results = await asyncio.gather(*[_run_batch(batch) for batch in batches])
    merged: dict[str, str] = {}
    for result in batch_results:
        merged.update(result)
    return merged


async def generate_expert_section(expert_name: str, team_name: str) -> str | None:
    results = await generate_expert_sections([expert_name], team_name)
    return results.get(expert_name)


# ---------------------------------------------------------------------------
# Section / notes helpers (mostly unchanged from teams.py)
# ---------------------------------------------------------------------------


def remove_expert_section(team_name: str, expert_name: str) -> bool:
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

    cleaned = "\n".join(result)
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    lead_md.write_text(cleaned, encoding="utf-8")
    return True


def create_expert_notes_stub(team_name: str, expert_name: str) -> None:
    notes_dir = TEAMS_DIR / team_name / f"expert-{expert_name}"
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(expert_notes_template(expert_name, team_name), encoding="utf-8")


def refresh_expert_notes_header(team_name: str, expert_name: str) -> None:
    notes_file = TEAMS_DIR / team_name / f"expert-{expert_name}" / "notes.md"
    if not notes_file.exists():
        create_expert_notes_stub(team_name, expert_name)
        return

    content = notes_file.read_text(encoding="utf-8")
    template = expert_notes_template(expert_name, team_name)
    separator = "\n---\n"
    if separator in content:
        _, entries = content.split(separator, 1)
        notes_file.write_text(template + entries, encoding="utf-8")
    else:
        notes_file.write_text(template, encoding="utf-8")


def create_team_lead_notes_stub(team_name: str) -> None:
    team_dir = TEAMS_DIR / team_name
    team_dir.mkdir(parents=True, exist_ok=True)
    notes_file = team_dir / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(team_lead_notes_template(team_name), encoding="utf-8")


def refresh_team_lead_notes_header(team_name: str) -> None:
    notes_file = TEAMS_DIR / team_name / "notes.md"
    if not notes_file.exists():
        create_team_lead_notes_stub(team_name)
        return

    content = notes_file.read_text(encoding="utf-8")
    template = team_lead_notes_template(team_name)
    separator = "\n---\n"
    if separator in content:
        _, entries = content.split(separator, 1)
        notes_file.write_text(template + entries, encoding="utf-8")
    else:
        notes_file.write_text(template, encoding="utf-8")


def refresh_team_lead_body(team_name: str) -> None:
    """Regenerate lead.md wrapper from template, preserving ``## expert-*`` sections."""
    from hivemind.agents import registry

    lead_md = TEAMS_DIR / team_name / "lead.md"
    if not lead_md.exists():
        return

    agent = registry.get(team_name)
    if agent is None or not isinstance(agent.body, RosterTemplatedBody):
        return

    description = agent.body.description
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

    expert_content = "\n\n".join(s.rstrip() for s in expert_sections) if expert_sections else ""
    lead_body = team_lead_template(team_name, description, expert_content)
    lead_md.write_text(lead_body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Module-level creators / mutators
# ---------------------------------------------------------------------------


def _require_enabled(team_name: str) -> OperationResult | None:
    """Return an error result if the team is not enabled. ``None`` = ok."""
    from hivemind.agents import registry

    agent = registry.get(team_name)
    if agent is None or not isinstance(agent.body, RosterTemplatedBody):
        return OperationResult(success=False, error=f"Team '{team_name}' does not exist")
    if not agent.enabled:
        return OperationResult(
            success=False,
            error=f"Team '{team_name}' is disabled; enable it before modifying.",
        )
    return None


async def create_team(
    name: str,
    description: str,
    experts: list[str],
) -> OperationResult:
    """Create a new team in the catalog (unlisted by default)."""
    from hivemind.agents import registry
    from hivemind.agents.base import Agent

    registry.load(refresh=True)
    if registry.get(name) is not None:
        return OperationResult(success=False, error=f"Team '{name}' already exists")

    all_experts = set(get_all_expert_names()) | {a.name for a in registry.by_kind("git_analyzed")}
    for expert in experts:
        if expert not in all_experts:
            return OperationResult(success=False, error=f"Expert '{expert}' does not exist")

    team_dir = TEAMS_DIR / name
    team_dir.mkdir(parents=True, exist_ok=True)

    sections = await generate_expert_sections(experts, name)
    failed = [e for e in experts if e not in sections]
    if failed:
        shutil.rmtree(team_dir)
        return OperationResult(
            success=False,
            error=f"AI generation failed for expert section(s): {', '.join(failed)}",
        )

    expert_sections = [sections[e] for e in experts]
    for expert_name in experts:
        create_expert_notes_stub(name, expert_name)
    create_team_lead_notes_stub(name)

    lead_body = team_lead_template(name, description, "\n\n".join(expert_sections))
    (team_dir / "lead.md").write_text(lead_body, encoding="utf-8")

    body = RosterTemplatedBody(name=name, description=description, experts=list(experts))
    agent = Agent(name=name, body=body, enabled=False)
    registry.add(agent)

    await afire_post_mutation()
    return OperationResult(success=True)


def update_team(
    name: str,
    *,
    new_name: str | None = None,
    description: str | None = None,
) -> OperationResult:
    """Update a team's description and/or name.

    Renaming requires the team to exist; enable state transfers with the rename.
    """
    from hivemind.agents import registry

    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, RosterTemplatedBody):
        return OperationResult(success=False, error=f"Team '{name}' does not exist")

    body: RosterTemplatedBody = agent.body

    if description is not None:
        body.description = description

    if new_name and new_name != name:
        if registry.get(new_name) is not None:
            return OperationResult(success=False, error=f"Agent '{new_name}' already exists")

        old_dir = TEAMS_DIR / name
        new_dir = TEAMS_DIR / new_name
        if old_dir.exists():
            old_dir.rename(new_dir)

        was_enabled = agent.enabled
        # Rebuild the agent under the new name in the catalog
        registry.remove(name)
        from hivemind.agents.base import Agent

        new_body = RosterTemplatedBody(name=new_name, description=body.description, experts=list(body.experts))
        new_agent = Agent(name=new_name, body=new_body, enabled=False)
        registry.add(new_agent)
        if was_enabled:
            registry.set_enabled(new_name, True)

        refresh_team_lead_body(new_name)
    else:
        registry.save_body(agent)
        refresh_team_lead_body(name)

    fire_post_mutation()
    return OperationResult(success=True)


async def add_experts_to_team(
    team_name: str,
    expert_names: list[str],
    *,
    on_progress: Callable[[str], None] | None = None,
) -> AddExpertsResult:
    """Add multiple experts to a team's roster in one operation."""
    from hivemind.agents import registry

    guard = _require_enabled(team_name)
    if guard is not None:
        return AddExpertsResult(success=False, error=guard.error)

    agent = registry.get_or_raise(team_name)
    assert isinstance(agent.body, RosterTemplatedBody)
    body = agent.body
    existing = body.experts

    all_experts = set(get_all_expert_names()) | {a.name for a in registry.by_kind("git_analyzed")}

    added: list[str] = []
    skipped: list[str] = []
    failed: list[ExpertError] = []
    to_generate: list[str] = []

    lead_md = TEAMS_DIR / team_name / "lead.md"

    for expert_name in expert_names:
        if expert_name in existing:
            skipped.append(expert_name)
        elif expert_name not in all_experts:
            failed.append(ExpertError(name=expert_name, error="does not exist"))
        else:
            to_generate.append(expert_name)

    if on_progress:
        for n in to_generate:
            on_progress(n)

    sections = await generate_expert_sections(to_generate, team_name) if to_generate else {}

    for expert_name in to_generate:
        section = sections.get(expert_name)
        if not section:
            failed.append(ExpertError(name=expert_name, error="AI generation failed"))
            continue

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

    if added:
        registry.save_body(agent)

    await afire_post_mutation()
    return AddExpertsResult(success=True, added=added, skipped=skipped, failed=failed)


async def add_expert_to_team(team_name: str, expert_name: str) -> OperationResult:
    """Add a single expert to a team's roster."""
    from hivemind.agents import registry

    guard = _require_enabled(team_name)
    if guard is not None:
        return guard

    agent = registry.get_or_raise(team_name)
    assert isinstance(agent.body, RosterTemplatedBody)
    body = agent.body

    if expert_name in body.experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' already on team")

    all_experts = set(get_all_expert_names()) | {a.name for a in registry.by_kind("git_analyzed")}
    if expert_name not in all_experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' does not exist")

    section = await generate_expert_section(expert_name, team_name)
    if not section:
        return OperationResult(
            success=False,
            error=f"AI generation failed for expert section: {expert_name}",
        )

    lead_md = TEAMS_DIR / team_name / "lead.md"
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
    body.experts.append(expert_name)
    registry.save_body(agent)

    await afire_post_mutation()
    return OperationResult(success=True)


def remove_expert_from_team(team_name: str, expert_name: str) -> OperationResult:
    """Remove an expert from a team's roster."""
    from hivemind.agents import registry

    guard = _require_enabled(team_name)
    if guard is not None:
        return guard

    agent = registry.get_or_raise(team_name)
    assert isinstance(agent.body, RosterTemplatedBody)
    body = agent.body

    if expert_name not in body.experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' not on team")

    remove_expert_section(team_name, expert_name)

    notes_dir = TEAMS_DIR / team_name / f"expert-{expert_name}"
    if notes_dir.exists():
        shutil.rmtree(notes_dir)

    body.experts.remove(expert_name)
    registry.save_body(agent)

    fire_post_mutation()
    return OperationResult(success=True)
