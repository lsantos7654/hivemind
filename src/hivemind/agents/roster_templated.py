"""``RosterTemplatedBody`` — body strategy for team lead agents.

A team lead agent is assembled at deploy time from per-file inputs under
``teams/<name>/``: ``description.md`` (the team's one-paragraph blurb) and
one ``expert-<expert>.md`` per roster member (the AI-generated section
body). Membership mutations (``add_expert_to_team`` /
``remove_expert_from_team``) write or delete those files; the Jinja
``team_lead.md.j2`` template renders them into the deployed
``agents/team-lead-<name>.md`` when ``Agent.deploy()`` runs.

Enable/disable behaves like any other agent: the deployed
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
from hivemind.constants import DESCRIPTION_FILENAME
from hivemind.git import clone_from_remote
from hivemind.hooks import afire_post_mutation, fire_post_mutation
from hivemind.models import (
    AddExpertsResult,
    ExpertError,
    OperationResult,
    RosterTemplatedParams,
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
    "refresh_team_lead_notes_header",
    "remove_expert_from_team",
    "update_team",
]

_SECTION_BATCH_SIZE = 15


# ---------------------------------------------------------------------------
# Body strategy
# ---------------------------------------------------------------------------


class RosterTemplatedBody:
    """Body strategy for team lead agents.

    Holds its catalog data as a typed :class:`RosterTemplatedParams`. Access
    params via ``self.params`` (e.g. ``self.params.experts``); mutations
    re-validate because the params model has ``validate_assignment=True``.
    """

    kind: str = "roster_templated"

    def __init__(self, name: str, params: RosterTemplatedParams) -> None:
        self.name = name
        self.params = params

    # --- catalog (de)serialisation -----------------------------------------

    @classmethod
    def from_catalog(cls, name: str, params: dict[str, Any]) -> RosterTemplatedBody:
        return cls(name=name, params=RosterTemplatedParams.model_validate(params))

    @classmethod
    def from_params(cls, name: str, params: RosterTemplatedParams) -> RosterTemplatedBody:
        return cls(name=name, params=params)

    def to_catalog(self) -> dict[str, Any]:
        return self.params.model_dump()

    # --- body protocol -----------------------------------------------------

    def description(self) -> str:
        """Read the team's one-paragraph description for frontmatter."""
        desc_md = TEAMS_DIR / self.name / DESCRIPTION_FILENAME
        if desc_md.exists():
            return desc_md.read_text(encoding="utf-8").strip()
        return self.params.description

    def render(self) -> str:
        """Render the deploy-time team-lead body from per-expert section files.

        Reads ``teams/<name>/description.md`` and one
        ``teams/<name>/expert-<expert>.md`` per current roster member, then
        passes them through the Jinja team-lead template. Roster mutations
        write to those files directly; template tweaks take effect on
        ``hivemind redeploy`` with no AI spend.
        """
        team_dir = TEAMS_DIR / self.name
        desc_md = team_dir / DESCRIPTION_FILENAME
        if not desc_md.exists():
            return ""
        description = desc_md.read_text(encoding="utf-8").strip()
        expert_sections: dict[str, str] = {}
        for expert_name in self.params.experts:
            section_path = team_dir / f"expert-{expert_name}.md"
            if section_path.exists():
                expert_sections[expert_name] = section_path.read_text(encoding="utf-8").strip()
        return team_lead_template(self.name, description, expert_sections)

    def librarian_entry(self) -> str:
        roster = ", ".join(self.params.experts)
        return (
            f"### team-lead-{self.name}\n"
            f"Team lead for {self.params.description}. Roster: {roster}.\n"
            f"Consult this team lead for routing and coordination within this domain."
        )

    def on_deploy(self) -> None:
        """Ensure every roster member has its repo cached locally."""
        from hivemind.agents import registry
        from hivemind.agents.base import run_coro_sync
        from hivemind.agents.git_analyzed import GitAnalyzedBody

        for expert_name in self.params.experts:
            member = registry.get(expert_name)
            if member is None or not isinstance(member.body, GitAnalyzedBody):
                continue
            try:
                run_coro_sync(
                    clone_from_remote(
                        expert_name,
                        member.body.params.remote,
                        commit=member.body.params.commit,
                        ref_name=member.body.params.ref_name,
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
    """Parse AI output into ``{name: section_body}`` with the heading stripped.

    The deploy-time Jinja template emits the ``## expert-<name>`` heading
    itself, so the dict values must be heading-free body text.
    """
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
        # Drop the marker line itself; keep the body underneath.
        body = output[start + len(marker) : next_start]
        sections[name] = body.strip()
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


def _write_description_file(team_name: str, description: str) -> None:
    team_dir = TEAMS_DIR / team_name
    team_dir.mkdir(parents=True, exist_ok=True)
    (team_dir / DESCRIPTION_FILENAME).write_text(description.strip() + "\n", encoding="utf-8")


def _write_expert_section_file(team_name: str, expert_name: str, body: str) -> None:
    team_dir = TEAMS_DIR / team_name
    team_dir.mkdir(parents=True, exist_ok=True)
    (team_dir / f"expert-{expert_name}.md").write_text(body.strip() + "\n", encoding="utf-8")


def _delete_expert_section_file(team_name: str, expert_name: str) -> None:
    section_path = TEAMS_DIR / team_name / f"expert-{expert_name}.md"
    if section_path.exists():
        section_path.unlink()


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

    _write_description_file(name, description)
    for expert_name in experts:
        _write_expert_section_file(name, expert_name, sections[expert_name])
        create_expert_notes_stub(name, expert_name)
    create_team_lead_notes_stub(name)

    body = RosterTemplatedBody(
        name=name,
        params=RosterTemplatedParams(description=description, experts=list(experts)),
    )
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

    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, RosterTemplatedBody):
        return OperationResult(success=False, error=f"Team '{name}' does not exist")

    body: RosterTemplatedBody = agent.body

    if description is not None:
        body.params.description = description

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

        new_body = RosterTemplatedBody(
            name=new_name,
            params=RosterTemplatedParams(
                description=body.params.description,
                experts=list(body.params.experts),
            ),
        )
        new_agent = Agent(name=new_name, body=new_body, enabled=False)
        registry.add(new_agent)
        if was_enabled:
            registry.set_enabled(new_name, True)

        if description is not None:
            _write_description_file(new_name, description)
    else:
        registry.save_body(agent)
        if description is not None:
            _write_description_file(name, description)

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
    existing = body.params.experts

    all_experts = set(get_all_expert_names()) | {a.name for a in registry.by_kind("git_analyzed")}

    added: list[str] = []
    skipped: list[str] = []
    failed: list[ExpertError] = []
    to_generate: list[str] = []

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

        _write_expert_section_file(team_name, expert_name, section)
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

    if expert_name in body.params.experts:
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

    _write_expert_section_file(team_name, expert_name, section)
    create_expert_notes_stub(team_name, expert_name)
    body.params.experts.append(expert_name)
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

    if expert_name not in body.params.experts:
        return OperationResult(success=False, error=f"Expert '{expert_name}' not on team")

    _delete_expert_section_file(team_name, expert_name)

    notes_dir = TEAMS_DIR / team_name / f"expert-{expert_name}"
    if notes_dir.exists():
        shutil.rmtree(notes_dir)

    body.params.experts.remove(expert_name)
    registry.save_body(agent)

    fire_post_mutation()
    return OperationResult(success=True)
