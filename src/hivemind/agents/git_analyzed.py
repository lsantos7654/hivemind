"""``GitAnalyzedBody`` — body strategy for git-backed, AI-analyzed agents.

Concrete body implementation for the classic "hivemind expert" kind: a git
repository is cloned, an AI pass generates the agent.md + knowledge docs,
and subsequent ``update`` / ``switch_version`` mutations refresh or switch
the HEAD symlink. The deployable agent body is the file at
``experts/<name>/HEAD/agent.md``; the body's ``on_deploy`` hooks ensure the
backing repo is cloned and the expert dir is symlinked into opencode's
``experts/`` directory.

Module-level creators / mutators:

- :func:`create_git_expert` — async; registers in catalog as *unlisted*
- :func:`update_git_expert` — async; fetch + analyze + rotate HEAD
- :func:`switch_version` — async; switch to a specific commit
- :func:`get_git_versions` — read-only; tags + recent commits
- :func:`commit_exists_in_repo` — read-only
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hivemind import opencode
from hivemind.analysis import (
    expected_analysis_files,
    handle_async_cancellation,
    make_cancellation_checker,
    run_async_analysis,
)
from hivemind.config import (
    EXPERTS_DIR,
    GIT_FETCH_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    REPOS_DIR,
    STAGING_DIR,
    ensure_repos_link,
    get_expert_dir,
    get_head_commit,
    make_emit,
)
from hivemind.constants import DESCRIPTION_FILENAME, EXPERTISE_FILENAME
from hivemind.git import (
    clone_from_remote,
    commit_analysis_results,
    create_staging_dir,
    resolve_commit_provenance,
    resolve_latest_commit,
    resolve_ref,
    revert_checkout,
    stage_for_analysis,
)
from hivemind.hooks import afire_post_mutation
from hivemind.models import (
    CancellationToken,
    GitAnalyzedParams,
    OperationResult,
    PrepCreateResult,
    PrepSwitchResult,
    PrepUpdateResult,
    ProgressCallback,
    UpdatePhase,
    UpdateResult,
)
from hivemind.templates import create_expert_prompt, render_agent, update_expert_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind.tui.models import VersionInfo

log = logging.getLogger(__name__)


__all__ = [
    "GitAnalyzedBody",
    "commit_exists_in_repo",
    "create_git_expert",
    "finalize_create_expert",
    "finalize_switch_version",
    "finalize_update_agent",
    "find_staged_prep",
    "find_staged_switch_prep",
    "find_staged_update_prep",
    "get_git_versions",
    "load_prep_result",
    "load_switch_prep_result",
    "load_update_prep_result",
    "prep_create_expert",
    "prep_switch_version",
    "prep_update_agent",
    "switch_version",
    "update_git_expert",
]


_PREP_META_FILENAME = "prep.json"


_SHA_RE = re.compile(r"^[0-9a-f]{4,40}$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Body strategy
# ---------------------------------------------------------------------------


class GitAnalyzedBody:
    """Body strategy for git-cloned, AI-analyzed agents.

    Holds its catalog data as a typed :class:`GitAnalyzedParams`. Access
    params via ``self.params`` (e.g. ``self.params.commit``); mutations
    re-validate because the params model has ``validate_assignment=True``.
    """

    kind: str = "git_analyzed"

    def __init__(self, name: str, params: GitAnalyzedParams) -> None:
        self.name = name
        self.params = params

    # --- catalog (de)serialisation -----------------------------------------

    @classmethod
    def from_catalog(cls, name: str, params: dict[str, Any]) -> GitAnalyzedBody:
        return cls(name=name, params=GitAnalyzedParams.model_validate(params))

    @classmethod
    def from_params(cls, name: str, params: GitAnalyzedParams) -> GitAnalyzedBody:
        return cls(name=name, params=params)

    def to_catalog(self) -> dict[str, Any]:
        return self.params.model_dump()

    # --- body protocol -----------------------------------------------------

    def description(self) -> str:
        """Read the AI-generated one-paragraph description for frontmatter."""
        desc_md = get_expert_dir(self.name) / "HEAD" / DESCRIPTION_FILENAME
        if not desc_md.exists():
            return ""
        return desc_md.read_text(encoding="utf-8").strip()

    def render(self) -> str:
        """Render the deploy-time agent body from description.md + expertise.md.

        These two files are AI-generated; the rest of the agent body
        (workflow scaffolding, anti-hallucination rules, constraints) is
        provided by the Jinja template at deploy time, so prompt-engineering
        improvements take effect via ``hivemind redeploy`` — no AI spend.
        """
        head = get_expert_dir(self.name) / "HEAD"
        desc_path = head / DESCRIPTION_FILENAME
        expertise_path = head / EXPERTISE_FILENAME
        if not desc_path.exists() or not expertise_path.exists():
            return ""
        description = desc_path.read_text(encoding="utf-8").strip()
        expertise = expertise_path.read_text(encoding="utf-8").strip()
        commit = head.resolve().name
        return render_agent(
            name=self.name,
            commit=commit,
            description=description,
            expertise=expertise,
        )

    def librarian_entry(self) -> str:
        description = self.description()

        summary_lines = ""
        summary_md = get_expert_dir(self.name) / "HEAD" / "summary.md"
        try:
            lines = summary_md.read_text(encoding="utf-8").splitlines()
            summary_lines = "\n".join(lines[:5])
        except OSError:
            pass

        return f"### expert-{self.name}\n{description}\n\n{summary_lines}"

    def on_deploy(self) -> None:
        """Ensure the repo is cloned + symlink expert dir into opencode experts/."""
        from hivemind.agents.base import run_coro_sync

        expert_dir = get_expert_dir(self.name)
        if not expert_dir.exists():
            return

        # Clone repo if not cached. Works whether enable_agent was called
        # from the CLI (no running loop) or from an MCP handler (loop running)
        # — ``run_coro_sync`` handles both cases.
        run_coro_sync(self._ensure_repo_cloned())

        opencode.deploy_backing_dir(self.name, expert_dir)

    def on_undeploy(self) -> None:
        opencode.undeploy_backing_dir(self.name)

    def on_delete(self) -> None:
        """Remove the expert dir and the cached repo clone."""
        expert_dir = get_expert_dir(self.name)
        if expert_dir.exists():
            shutil.rmtree(expert_dir)
        repo_cache = REPOS_DIR / self.name
        if repo_cache.exists():
            shutil.rmtree(repo_cache)

    # --- internal helpers --------------------------------------------------

    async def _ensure_repo_cloned(self) -> bool:
        repo_dir = REPOS_DIR / self.name
        if repo_dir.is_dir():
            return True
        return await clone_from_remote(
            self.name,
            self.params.remote,
            commit=self.params.commit,
            ref_name=self.params.ref_name,
            silent=True,
        )


# ---------------------------------------------------------------------------
# Module-level creators / mutators
# ---------------------------------------------------------------------------


async def prep_create_expert(
    name: str,
    url: str,
    *,
    ref_name: str = "",
    on_progress: ProgressCallback | None = None,
) -> PrepCreateResult:
    """Stage 1 of the git_analyzed create pipeline: clone + staging.

    The create pipeline is intentionally split into three stages so the
    AI-analysis step (stage 2) is pluggable. Stage 1 (here) does the
    deterministic plumbing: validate the name is free, resolve a ref to
    a commit, clone the repo into a staging tree, and render the analysis
    prompt. Stage 2 — performed by ``run_async_analysis`` (subprocess),
    by an opencode subagent in-session, or by a human writing files
    directly — populates the 6 expected files in
    ``commit_dir``. Stage 3 (:func:`finalize_create_expert`) moves
    everything into the catalog.

    The staging dir persists across the call so the analyzer can write to
    it. ``finalize_create_expert`` removes it on success;
    ``git._cleanup_stale_staging`` reaps abandoned ones after 6h.
    """
    from hivemind.agents import registry

    if registry.get(name) is not None:
        return PrepCreateResult(success=False, error=f"Agent '{name}' already exists")

    expert_dir = EXPERTS_DIR / name
    if expert_dir.is_dir():
        return PrepCreateResult(success=False, error=f"experts/{name}/ already exists on disk")

    validation = opencode.validate_engine()
    if not validation.success:
        return PrepCreateResult(success=False, error=validation.error)

    emit = make_emit(name, on_progress)

    # Resolve commit from ref if provided
    commit = ""
    if ref_name:
        emit(UpdatePhase.CHECKING, f"Resolving ref '{ref_name}'...")
        proc = await asyncio.create_subprocess_exec(
            "git",
            "ls-remote",
            url,
            ref_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode().strip()
        commit = output.split()[0] if output else ref_name

    tmpdir = create_staging_dir(name)
    tmp_repo = tmpdir / "repo"
    tmp_expert = tmpdir / "expert"
    tmp_expert.mkdir()
    succeeded = False

    try:
        emit(UpdatePhase.CLONING, f"Cloning {name}...")
        if commit and ref_name:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--progress",
                url,
                str(tmp_repo),
            )
            await asyncio.wait_for(proc.wait(), timeout=300)
            if proc.returncode != 0:
                return PrepCreateResult(success=False, error="Failed to clone repository")
            proc = await asyncio.create_subprocess_exec(
                "git",
                "checkout",
                "--quiet",
                commit,
                cwd=str(tmp_repo),
            )
            await asyncio.wait_for(proc.wait(), timeout=GIT_LOCAL_TIMEOUT)
        elif ref_name:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--progress",
                "--branch",
                ref_name,
                url,
                str(tmp_repo),
            )
            await asyncio.wait_for(proc.wait(), timeout=300)
            if proc.returncode != 0:
                return PrepCreateResult(success=False, error="Failed to clone repository")
        else:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--progress",
                url,
                str(tmp_repo),
            )
            await asyncio.wait_for(proc.wait(), timeout=300)
            if proc.returncode != 0:
                return PrepCreateResult(success=False, error="Failed to clone repository")

        if not commit:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "HEAD",
                cwd=str(tmp_repo),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            commit = stdout.decode().strip()

        # Populate ref_name when the caller didn't pass --ref. Prefer a
        # tag-exact-match over the default branch — many adds happen
        # against a tagged release, and the tag name is what
        # ``/hivemind_sync`` compares against project version pins.
        # Falls back to the upstream default branch when the commit
        # isn't at a tag (the common case for "add at HEAD" without
        # any ref). Without this, the catalog stores ``ref_name=""``
        # and downstream consumers can't compare cleanly.
        if not ref_name:
            resolved_ref = await resolve_commit_provenance(tmp_repo, commit)
            if resolved_ref:
                ref_name = resolved_ref

        tmp_commit_dir = tmp_expert / commit
        tmp_commit_dir.mkdir(parents=True, exist_ok=True)

        prompt = create_expert_prompt(name, commit, tmp_repo, tmp_commit_dir)

        # Persist for cross-process finalize (curator subagent path).
        # The in-process composition path uses the returned object directly,
        # but a separate ``finalize_create_expert`` invocation from the
        # curator's MCP tool call needs to reconstruct the prep state.
        # The ``intent`` field disambiguates from update / switch_version
        # stagings that may also exist for the same agent name.
        (tmpdir / _PREP_META_FILENAME).write_text(
            json.dumps(
                {
                    "intent": "create",
                    "name": name,
                    "url": url,
                    "ref_name": ref_name,
                    "commit": commit,
                    "repo_dir": str(tmp_repo),
                    "commit_dir": str(tmp_commit_dir),
                    "analysis_prompt": prompt,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        succeeded = True
        return PrepCreateResult(
            success=True,
            name=name,
            url=url,
            ref_name=ref_name,
            commit=commit,
            repo_dir=tmp_repo,
            commit_dir=tmp_commit_dir,
            staging_root=tmpdir,
            analysis_prompt=prompt,
        )
    finally:
        if not succeeded:
            shutil.rmtree(str(tmpdir), ignore_errors=True)


def _find_staged_prep_for_intent(name: str, intent: str) -> Path | None:
    """Locate the staging dir for ``name`` with the given prep ``intent``.

    Filters glob hits by the ``intent`` field in each candidate's
    ``prep.json``. Missing ``intent`` is treated as ``"create"`` for
    back-compat with the pre-multi-intent prep.json layout.

    Returns the matching staging root, ``None`` if no match, or raises
    ``ValueError`` if multiple match (caller must remove stale ones).
    """
    if not STAGING_DIR.is_dir():
        return None
    candidates: list[Path] = []
    for p in sorted(STAGING_DIR.glob(f"{name}-*")):
        if not p.is_dir():
            continue
        meta_path = p / _PREP_META_FILENAME
        if not meta_path.is_file():
            continue
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("intent", "create") == intent:
            candidates.append(p)
    if not candidates:
        return None
    if len(candidates) > 1:
        msg = (
            f"Multiple staging dirs match '{name}' with intent '{intent}': "
            f"{[c.name for c in candidates]}. Remove stale ones and retry."
        )
        raise ValueError(msg)
    return candidates[0]


def find_staged_prep(name: str) -> Path | None:
    """Locate the create-intent staging dir for ``name``."""
    return _find_staged_prep_for_intent(name, "create")


def find_staged_update_prep(name: str) -> Path | None:
    """Locate the update-intent staging dir for ``name``."""
    return _find_staged_prep_for_intent(name, "update")


def find_staged_switch_prep(name: str) -> Path | None:
    """Locate the switch-intent staging dir for ``name``."""
    return _find_staged_prep_for_intent(name, "switch")


def load_prep_result(staging_root: Path) -> PrepCreateResult:
    """Reconstruct a ``PrepCreateResult`` from a create-intent staging dir."""
    meta_path = staging_root / _PREP_META_FILENAME
    if not meta_path.is_file():
        return PrepCreateResult(
            success=False,
            error=f"No prep metadata at {meta_path}",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return PrepCreateResult(
        success=True,
        name=meta["name"],
        url=meta["url"],
        ref_name=meta.get("ref_name", ""),
        commit=meta["commit"],
        repo_dir=Path(meta["repo_dir"]),
        commit_dir=Path(meta["commit_dir"]),
        staging_root=staging_root,
        analysis_prompt=meta.get("analysis_prompt", ""),
    )


def load_update_prep_result(staging_root: Path) -> PrepUpdateResult:
    """Reconstruct a ``PrepUpdateResult`` from an update-intent staging dir."""
    meta_path = staging_root / _PREP_META_FILENAME
    if not meta_path.is_file():
        return PrepUpdateResult(
            success=False,
            error=f"No prep metadata at {meta_path}",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return PrepUpdateResult(
        success=True,
        name=meta["name"],
        new_commit=meta["new_commit"],
        old_commit=meta.get("old_commit"),
        already_up_to_date=False,
        repo_dir=Path(meta["repo_dir"]),
        commit_dir=Path(meta["commit_dir"]),
        staging_root=staging_root,
        analysis_prompt=meta.get("analysis_prompt", ""),
    )


def load_switch_prep_result(staging_root: Path) -> PrepSwitchResult:
    """Reconstruct a ``PrepSwitchResult`` from a switch-intent staging dir.

    Both cached and fresh switches persist a ``prep.json``; the
    ``cached`` field decides which staging fields are populated. This
    lets ``finalize_switch_version`` use a uniform reconstruction path
    regardless of which finalize tail it'll run.
    """
    meta_path = staging_root / _PREP_META_FILENAME
    if not meta_path.is_file():
        return PrepSwitchResult(
            success=False,
            error=f"No prep metadata at {meta_path}",
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    cached = bool(meta.get("cached", False))
    if cached:
        return PrepSwitchResult(
            success=True,
            name=meta["name"],
            target_commit=meta["target_commit"],
            old_commit=meta.get("old_commit"),
            cached=True,
            already_up_to_date=False,
            staging_root=staging_root,
        )
    return PrepSwitchResult(
        success=True,
        name=meta["name"],
        target_commit=meta["target_commit"],
        old_commit=meta.get("old_commit"),
        cached=False,
        already_up_to_date=False,
        repo_dir=Path(meta["repo_dir"]),
        commit_dir=Path(meta["commit_dir"]),
        staging_root=staging_root,
        analysis_prompt=meta.get("analysis_prompt", ""),
    )


async def finalize_create_expert(prep: PrepCreateResult) -> OperationResult:
    """Stage 3 of the git_analyzed create pipeline: validate + register.

    Validates that the analyzer wrote all expected files into
    ``prep.commit_dir``, moves the staged repo and expert dir to their
    final cache locations, creates the HEAD symlink, registers the
    catalog entry as *unlisted*, fires the post-mutation hook, and
    cleans up the staging dir. Leaves staging in place if validation
    fails so the caller can inspect / retry.
    """
    from hivemind.agents import registry
    from hivemind.agents.base import Agent

    if not prep.success:
        return OperationResult(success=False, error=prep.error or "prep failed")
    if (
        prep.repo_dir is None
        or prep.commit_dir is None
        or prep.staging_root is None
        or not prep.name
        or not prep.commit
        or not prep.url
    ):
        return OperationResult(success=False, error="prep result is missing required fields")

    expected = expected_analysis_files(is_update=False)
    missing = [f for f in expected if not (prep.commit_dir / f).is_file()]
    if missing:
        return OperationResult(
            success=False,
            error=(
                f"Analysis incomplete — missing {missing} in {prep.commit_dir}. "
                "Re-run the analyzer or write the missing files by hand, then retry."
            ),
        )

    # Re-check the catalog — another process might have added the same name
    # between prep and finalize.
    if registry.get(prep.name) is not None:
        return OperationResult(success=False, error=f"Agent '{prep.name}' already exists")

    ensure_repos_link()
    final_repo = REPOS_DIR / prep.name
    if final_repo.exists():
        shutil.rmtree(final_repo)
    shutil.move(str(prep.repo_dir), str(final_repo))

    EXPERTS_DIR.mkdir(parents=True, exist_ok=True)
    final_expert = EXPERTS_DIR / prep.name
    if final_expert.exists():
        shutil.rmtree(final_expert)
    shutil.move(str(prep.commit_dir.parent), str(final_expert))

    head_link = final_expert / "HEAD"
    head_link.symlink_to(prep.commit)

    body = GitAnalyzedBody(
        name=prep.name,
        params=GitAnalyzedParams(
            remote=prep.url,
            commit=prep.commit,
            ref_name=prep.ref_name,
        ),
    )
    agent = Agent(name=prep.name, body=body, enabled=False)
    registry.add(agent)

    await afire_post_mutation()

    # repo and expert dirs are gone; only prep.json remains
    shutil.rmtree(str(prep.staging_root), ignore_errors=True)

    return OperationResult(success=True)


async def create_git_expert(
    name: str,
    url: str,
    *,
    ref_name: str = "",
    on_progress: ProgressCallback | None = None,
) -> OperationResult:
    """Clone, analyze (subprocess), and register a new git-analyzed expert.

    Composition of :func:`prep_create_expert` (stage 1),
    :func:`run_async_analysis` (stage 2 — subprocess), and
    :func:`finalize_create_expert` (stage 3). Identical externally-
    observable behavior to before the prep / finalize seam was
    introduced. Suitable for the CLI and the Textual TUI. From a
    chat-TUI orchestrator session, prefer spawning the
    ``hivemind-expert-curator`` subagent — it performs stage 2 in-session
    via Read/Grep/Glob/Write, avoiding the nested-subprocess overhead and
    the MCP request timeout.
    """
    prep = await prep_create_expert(name, url, ref_name=ref_name, on_progress=on_progress)
    if not prep.success:
        return OperationResult(success=False, error=prep.error)
    # Narrowing for mypy: prep.success=True implies the path fields are populated.
    assert prep.commit_dir is not None
    assert prep.repo_dir is not None

    try:
        emit = make_emit(name, on_progress)
        emit(UpdatePhase.ANALYZING, f"Analyzing {name} (this may take 2-5 minutes)...")
        analysis_result = await run_async_analysis(
            name,
            prep.commit,
            prep.analysis_prompt,
            prep.commit_dir.parent,
            prep.repo_dir,
            emit,
            commit_dir=prep.commit_dir,
            is_update=False,
        )
        if not analysis_result.success:
            return OperationResult(success=False, error=analysis_result.error or "AI analysis failed")
        return await finalize_create_expert(prep)
    finally:
        # Match pre-refactor behavior: convenience wrapper always GCs the
        # staging dir, regardless of outcome. finalize may have already
        # removed it; ignore_errors=True absorbs the missing-dir case.
        if prep.staging_root:
            shutil.rmtree(str(prep.staging_root), ignore_errors=True)


async def prep_update_agent(
    name: str,
    *,
    on_progress: ProgressCallback | None = None,
    cancellation_token: CancellationToken | None = None,
) -> PrepUpdateResult:
    """Stage 1 of the git_analyzed update pipeline.

    Validates the agent, fetches origin, resolves the latest commit, and
    stages the analysis input. ``stage_for_analysis`` (in :mod:`hivemind.git`)
    preserves ``description.md`` and ``expertise.md`` from the prior commit
    by copying them into ``commit_dir`` before returning — so stage 2
    (the analyzer) only writes the 4 fresh knowledge docs (per
    ``expected_analysis_files(is_update=True)``).

    On the no-op path, returns ``success=True`` with
    ``already_up_to_date=True`` and the staging fields unset — caller
    skips analysis and treats the operation as complete.
    """
    from hivemind.agents import registry

    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return PrepUpdateResult(success=False, error=f"{name} is not a git-analyzed agent")

    body: GitAnalyzedBody = agent.body
    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)

    validation = opencode.validate_engine()
    if not validation.success:
        return PrepUpdateResult(success=False, error=validation.error)

    repo_dir = REPOS_DIR / name

    check_cancel(UpdatePhase.CLONING)
    emit(UpdatePhase.CLONING, "Cloning repository...")
    if not await clone_from_remote(
        name,
        body.params.remote,
        commit=body.params.commit,
        ref_name=body.params.ref_name,
        silent=True,
    ):
        return PrepUpdateResult(success=False, error="Failed to clone repository")

    check_cancel(UpdatePhase.FETCHING)
    emit(UpdatePhase.FETCHING, "Fetching latest commits...")
    proc = await asyncio.create_subprocess_exec(
        "git",
        "fetch",
        "origin",
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=GIT_FETCH_TIMEOUT)
    if proc.returncode != 0:
        return PrepUpdateResult(success=False, error=f"Failed to fetch: {stderr.decode()}")

    check_cancel(UpdatePhase.CHECKING)
    emit(UpdatePhase.CHECKING, "Checking for updates...")
    new_commit = await resolve_latest_commit(repo_dir)
    if not new_commit:
        return PrepUpdateResult(success=False, error="Could not resolve latest commit")

    expert_dir = get_expert_dir(name)
    old_commit = get_head_commit(expert_dir)

    if old_commit == new_commit:
        return PrepUpdateResult(
            success=True,
            name=name,
            new_commit=new_commit,
            old_commit=old_commit,
            already_up_to_date=True,
        )

    check_cancel(UpdatePhase.STAGING)
    emit(
        UpdatePhase.STAGING,
        f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
        new_commit=new_commit,
        old_commit=old_commit,
    )

    succeeded = False
    staging_root: Path | None = None
    try:
        staging = await stage_for_analysis(name, new_commit, expert_dir, old_commit, repo_dir)
        staging_root = Path(staging.tmpdir)
        tmp_commit_dir = staging.commit_dir

        prompt = update_expert_prompt(name, new_commit, repo_dir, tmp_commit_dir)

        # Persist for cross-process finalize (curator subagent path).
        # ``intent: "update"`` disambiguates from concurrent create / switch
        # stagings on the same agent name.
        (staging_root / _PREP_META_FILENAME).write_text(
            json.dumps(
                {
                    "intent": "update",
                    "name": name,
                    "new_commit": new_commit,
                    "old_commit": old_commit,
                    "repo_dir": str(repo_dir),
                    "commit_dir": str(tmp_commit_dir),
                    "analysis_prompt": prompt,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        succeeded = True
        return PrepUpdateResult(
            success=True,
            name=name,
            new_commit=new_commit,
            old_commit=old_commit,
            already_up_to_date=False,
            repo_dir=repo_dir,
            commit_dir=tmp_commit_dir,
            staging_root=staging_root,
            analysis_prompt=prompt,
        )
    finally:
        if not succeeded:
            # Stage_for_analysis checks out the new commit in repo_dir;
            # revert that on failure so the cached repo is consistent.
            await revert_checkout(repo_dir, old_commit)
            if staging_root is not None:
                shutil.rmtree(str(staging_root), ignore_errors=True)


async def finalize_update_agent(prep: PrepUpdateResult) -> UpdateResult:
    """Stage 3 of the git_analyzed update pipeline.

    Validates the 4 expected fresh analysis docs (``description.md`` and
    ``expertise.md`` were preserved by prep, so they're guaranteed
    present), moves the staged commit dir into the agent's expert dir,
    rotates the HEAD symlink, updates the catalog body's commit, fires
    the post-mutation hook, and cleans up staging.

    On the no-op path (``prep.already_up_to_date=True``), returns
    success without touching any state — there's nothing to finalize.
    """
    from hivemind.agents import registry

    if not prep.success:
        return UpdateResult(success=False, error=prep.error or "prep failed")
    if prep.already_up_to_date:
        return UpdateResult(
            success=True,
            already_up_to_date=True,
            new_commit=prep.new_commit,
            old_commit=prep.old_commit,
        )
    if (
        prep.repo_dir is None
        or prep.commit_dir is None
        or prep.staging_root is None
        or not prep.name
        or not prep.new_commit
    ):
        return UpdateResult(success=False, error="prep result is missing required fields")

    expected = expected_analysis_files(is_update=True)
    missing = [f for f in expected if not (prep.commit_dir / f).is_file()]
    if missing:
        return UpdateResult(
            success=False,
            error=(
                f"Update analysis incomplete — missing {missing} in {prep.commit_dir}. "
                "Re-run the analyzer or write the missing files by hand, then retry."
            ),
            new_commit=prep.new_commit,
            old_commit=prep.old_commit,
        )

    agent = registry.get(prep.name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return UpdateResult(
            success=False,
            error=f"{prep.name} is no longer a git-analyzed agent",
            new_commit=prep.new_commit,
            old_commit=prep.old_commit,
        )

    expert_dir = get_expert_dir(prep.name)
    commit_analysis_results(prep.commit_dir, expert_dir, prep.new_commit)

    body: GitAnalyzedBody = agent.body
    body.params.commit = prep.new_commit
    registry.save_body(agent)

    await afire_post_mutation()

    shutil.rmtree(str(prep.staging_root), ignore_errors=True)

    return UpdateResult(
        success=True,
        new_commit=prep.new_commit,
        old_commit=prep.old_commit,
    )


async def update_git_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
    *,
    skip_analysis: bool = False,
) -> UpdateResult:
    """Fetch, analyze (subprocess), and rotate HEAD for a git-analyzed agent.

    Composition of :func:`prep_update_agent` (stage 1),
    :func:`run_async_analysis` (stage 2 — subprocess), and
    :func:`finalize_update_agent` (stage 3). Identical
    externally-observable behavior to before the prep / finalize seam
    was introduced. Suitable for the CLI and the Textual TUI. From a
    chat-TUI orchestrator session, prefer spawning the
    ``hivemind-expert-curator`` subagent — it performs stage 2
    in-session, avoiding the nested-subprocess overhead and the MCP
    request timeout.

    ``skip_analysis=True`` skips stage 2 entirely (description.md +
    expertise.md preserved from prior commit, no fresh knowledge docs).
    """
    prep = await prep_update_agent(
        name,
        on_progress=on_progress,
        cancellation_token=cancellation_token,
    )
    if not prep.success:
        return UpdateResult(success=False, error=prep.error)
    if prep.already_up_to_date:
        return UpdateResult(
            success=True,
            already_up_to_date=True,
            new_commit=prep.new_commit,
            old_commit=prep.old_commit,
        )
    # Narrowing for mypy: success + not already_up_to_date implies these are populated.
    assert prep.repo_dir is not None
    assert prep.commit_dir is not None

    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)

    try:
        if not skip_analysis:
            check_cancel(UpdatePhase.ANALYZING)
            emit(
                UpdatePhase.ANALYZING,
                f"Analyzing {prep.new_commit[:12]} (this may take 2-5 minutes)...",
                progress_percent=0,
                new_commit=prep.new_commit,
                old_commit=prep.old_commit,
            )

            analysis_result = await run_async_analysis(
                name,
                prep.new_commit,
                prep.analysis_prompt,
                prep.commit_dir.parent,
                prep.repo_dir,
                emit,
                old_commit=prep.old_commit,
                cancellation_token=cancellation_token,
                on_subprocess_start=on_subprocess_start,
                commit_dir=prep.commit_dir,
                is_update=True,
            )
            if not analysis_result.success:
                await revert_checkout(prep.repo_dir, prep.old_commit)
                return UpdateResult(
                    success=False,
                    error=analysis_result.error,
                    new_commit=prep.new_commit,
                    old_commit=prep.old_commit,
                )
        else:
            emit(
                UpdatePhase.ANALYZING,
                "Skipping analysis (reusing existing docs)...",
                new_commit=prep.new_commit,
                old_commit=prep.old_commit,
            )

        emit(UpdatePhase.COMMITTING, "Committing changes...")
        return await finalize_update_agent(prep)

    except asyncio.CancelledError:
        return await handle_async_cancellation(
            None, None, None, prep.repo_dir, prep.old_commit, "Update cancelled by user"
        )
    finally:
        # finalize already cleans up on success; this catches failure paths.
        if prep.staging_root is not None:
            shutil.rmtree(str(prep.staging_root), ignore_errors=True)


async def prep_switch_version(
    name: str,
    ref: str,
    *,
    on_progress: ProgressCallback | None = None,
    cancellation_token: CancellationToken | None = None,
) -> PrepSwitchResult:
    """Stage 1 of the git_analyzed switch_version pipeline.

    Resolves ``ref`` (tag / branch / short-or-full SHA) to a full commit
    SHA, then determines the finalize path:

    - **already_up_to_date**: HEAD is already at the resolved commit.
      No work needed.
    - **cached**: ``experts/<name>/<target_commit>/`` already has
      ``description.md`` + ``expertise.md`` from a prior analysis.
      Finalize will just repoint HEAD + checkout — sub-second.
    - **fresh**: target commit has no local analysis. Stages the
      analysis input (no file preservation — different commit, full
      re-analysis), checks out the working tree to the target commit
      (so the analyzer can scan it), and renders the create-expert
      prompt for stage 2.
    """
    from hivemind.agents import registry

    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return PrepSwitchResult(success=False, error=f"{name} is not a git-analyzed agent")

    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)

    expert_dir = get_expert_dir(name)
    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return PrepSwitchResult(success=False, error="Repository not cloned")

    validation = opencode.validate_engine()
    if not validation.success:
        return PrepSwitchResult(success=False, error=validation.error)

    # Resolve ref → full SHA. Same logic as the previous monolithic
    # switch_version: skip fetch+rev-parse for full/short SHAs already
    # in the local repo (the common case from the TUI version picker).
    if not (_SHA_RE.match(ref) and await commit_exists_in_repo(name, ref)):
        resolved = await resolve_ref(repo_dir, ref)
        if resolved is None:
            return PrepSwitchResult(
                success=False,
                error=f"Could not resolve ref '{ref}' in repo for agent '{name}'",
            )
        target_commit = resolved
    else:
        target_commit = ref

    old_commit = get_head_commit(expert_dir)
    if old_commit == target_commit:
        return PrepSwitchResult(
            success=True,
            name=name,
            target_commit=target_commit,
            old_commit=old_commit,
            cached=True,
            already_up_to_date=True,
        )

    if not await commit_exists_in_repo(name, target_commit):
        return PrepSwitchResult(
            success=False,
            error=f"Commit {target_commit[:12]} not found in repository",
        )

    # Cached path — analysis docs already on disk for the target commit.
    # We still create a staging dir and persist prep.json so finalize has
    # a uniform reconstruction path. The cached staging dir is just a
    # one-file marker (no expert/ subdir, no analysis files).
    target_dir = expert_dir / target_commit
    if (
        target_dir.exists()
        and (target_dir / DESCRIPTION_FILENAME).exists()
        and (target_dir / EXPERTISE_FILENAME).exists()
    ):
        cached_staging_root = create_staging_dir(name)
        (cached_staging_root / _PREP_META_FILENAME).write_text(
            json.dumps(
                {
                    "intent": "switch",
                    "name": name,
                    "target_commit": target_commit,
                    "old_commit": old_commit,
                    "cached": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return PrepSwitchResult(
            success=True,
            name=name,
            target_commit=target_commit,
            old_commit=old_commit,
            cached=True,
            already_up_to_date=False,
            staging_root=cached_staging_root,
        )

    # Fresh path — checkout target commit so the analyzer can scan it,
    # then stage analysis input.
    check_cancel(UpdatePhase.CHECKING)
    emit(
        UpdatePhase.CHECKING,
        f"Checking out {target_commit[:12]}...",
        old_commit=old_commit,
        new_commit=target_commit,
    )
    proc = await asyncio.create_subprocess_exec(
        "git",
        "checkout",
        "--quiet",
        target_commit,
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
    if proc.returncode != 0:
        return PrepSwitchResult(success=False, error=f"Failed to checkout commit: {stderr.decode()}")

    check_cancel(UpdatePhase.STAGING)
    emit(
        UpdatePhase.STAGING,
        f"Staging analysis for {target_commit[:12]}...",
        old_commit=old_commit,
        new_commit=target_commit,
    )

    succeeded = False
    staging_root: Path | None = None
    try:
        staging_root = create_staging_dir(name)
        staged_path = staging_root / "expert"
        staged_path.mkdir()
        tmp_commit_dir = staged_path / target_commit
        tmp_commit_dir.mkdir()

        prompt = create_expert_prompt(name, target_commit, repo_dir, tmp_commit_dir)

        # Persist for cross-process finalize (curator subagent path).
        # ``intent: "switch"`` disambiguates from concurrent create / update
        # stagings on the same agent name. ``cached: false`` distinguishes
        # the fresh path from the cached marker prep.json above.
        (staging_root / _PREP_META_FILENAME).write_text(
            json.dumps(
                {
                    "intent": "switch",
                    "name": name,
                    "target_commit": target_commit,
                    "old_commit": old_commit,
                    "cached": False,
                    "repo_dir": str(repo_dir),
                    "commit_dir": str(tmp_commit_dir),
                    "analysis_prompt": prompt,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        succeeded = True
        return PrepSwitchResult(
            success=True,
            name=name,
            target_commit=target_commit,
            old_commit=old_commit,
            cached=False,
            already_up_to_date=False,
            repo_dir=repo_dir,
            commit_dir=tmp_commit_dir,
            staging_root=staging_root,
            analysis_prompt=prompt,
        )
    finally:
        if not succeeded:
            await revert_checkout(repo_dir, old_commit)
            if staging_root is not None:
                shutil.rmtree(str(staging_root), ignore_errors=True)


async def finalize_switch_version(prep: PrepSwitchResult) -> UpdateResult:
    """Stage 3 of the git_analyzed switch_version pipeline.

    Two paths:

    - **cached** (no analysis was needed): repoint HEAD symlink, update
      catalog body's commit, checkout the working tree to the target
      commit, fire post-mutation hook. Sub-second.
    - **fresh**: validate the 6 expected analysis files in
      ``prep.commit_dir``, move the staged commit dir into
      ``experts/<name>/<target_commit>/``, then run the cached-path
      tail (HEAD + body params + checkout + hook), then clean up
      staging.

    On the no-op path (``prep.already_up_to_date=True``), returns
    success without touching state.
    """
    from hivemind.agents import registry

    if not prep.success:
        return UpdateResult(success=False, error=prep.error or "prep failed")
    if prep.already_up_to_date:
        return UpdateResult(
            success=True,
            already_up_to_date=True,
            old_commit=prep.old_commit,
            new_commit=prep.target_commit,
        )

    agent = registry.get(prep.name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return UpdateResult(
            success=False,
            error=f"{prep.name} is no longer a git-analyzed agent",
            old_commit=prep.old_commit,
            new_commit=prep.target_commit,
        )

    expert_dir = get_expert_dir(prep.name)
    repo_dir = REPOS_DIR / prep.name

    # Fresh path: validate + move staging into the agent's expert dir.
    if not prep.cached:
        if prep.commit_dir is None or prep.staging_root is None or not prep.target_commit:
            return UpdateResult(
                success=False,
                error="prep result is missing required fields for fresh switch",
                old_commit=prep.old_commit,
                new_commit=prep.target_commit,
            )

        expected = expected_analysis_files(is_update=False)
        missing = [f for f in expected if not (prep.commit_dir / f).is_file()]
        if missing:
            return UpdateResult(
                success=False,
                error=(
                    f"Switch analysis incomplete — missing {missing} in {prep.commit_dir}. "
                    "Re-run the analyzer or write the missing files by hand, then retry."
                ),
                old_commit=prep.old_commit,
                new_commit=prep.target_commit,
            )

        commit_analysis_results(prep.commit_dir, expert_dir, prep.target_commit)

    # Both paths: ensure working tree is at target commit.
    proc = await asyncio.create_subprocess_exec(
        "git",
        "checkout",
        "--quiet",
        prep.target_commit,
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
    if proc.returncode != 0:
        return UpdateResult(
            success=False,
            error=f"Failed to checkout commit in repo: {stderr.decode()}",
            old_commit=prep.old_commit,
            new_commit=prep.target_commit,
        )

    head_link = expert_dir / "HEAD"
    if head_link.is_symlink():
        head_link.unlink()
    head_link.symlink_to(prep.target_commit)

    body: GitAnalyzedBody = agent.body
    body.params.commit = prep.target_commit
    registry.save_body(agent)

    await afire_post_mutation()

    # Both paths created a staging dir (cached holds just prep.json,
    # fresh holds the moved-out commit dir + prep.json). Clean up either.
    if prep.staging_root is not None:
        shutil.rmtree(str(prep.staging_root), ignore_errors=True)

    return UpdateResult(
        success=True,
        old_commit=prep.old_commit,
        new_commit=prep.target_commit,
    )


async def switch_version(
    name: str,
    target_commit: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
) -> UpdateResult:
    """Switch a git-analyzed agent to a specific commit / tag / branch.

    Composition of :func:`prep_switch_version` (stage 1),
    :func:`run_async_analysis` (stage 2 — only when the target commit
    isn't already analyzed locally), and :func:`finalize_switch_version`
    (stage 3). Identical externally-observable behavior to before the
    prep / finalize seam was introduced. Suitable for the CLI and the
    Textual TUI. From a chat-TUI orchestrator session, prefer spawning
    the ``hivemind-expert-curator`` subagent — it routes to the cached
    fast path automatically when the target commit is already known.
    """
    prep = await prep_switch_version(
        name,
        target_commit,
        on_progress=on_progress,
        cancellation_token=cancellation_token,
    )
    if not prep.success:
        return UpdateResult(success=False, error=prep.error)
    if prep.already_up_to_date:
        return UpdateResult(
            success=True,
            already_up_to_date=True,
            old_commit=prep.old_commit,
            new_commit=prep.target_commit,
        )

    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)
    repo_dir = REPOS_DIR / name

    try:
        if not prep.cached:
            assert prep.repo_dir is not None
            assert prep.commit_dir is not None

            check_cancel(UpdatePhase.ANALYZING)
            emit(
                UpdatePhase.ANALYZING,
                f"Analyzing {prep.target_commit[:12]} (this may take 2-5 minutes)...",
                progress_percent=0,
                old_commit=prep.old_commit,
                new_commit=prep.target_commit,
            )

            analysis_result = await run_async_analysis(
                name,
                prep.target_commit,
                prep.analysis_prompt,
                prep.commit_dir.parent,
                prep.repo_dir,
                emit,
                old_commit=prep.old_commit,
                cancellation_token=cancellation_token,
                on_subprocess_start=on_subprocess_start,
                commit_dir=prep.commit_dir,
                is_update=False,
            )
            if not analysis_result.success:
                await revert_checkout(prep.repo_dir, prep.old_commit)
                return UpdateResult(
                    success=False,
                    error=analysis_result.error,
                    old_commit=prep.old_commit,
                    new_commit=prep.target_commit,
                )

            emit(
                UpdatePhase.COMMITTING,
                "Committing changes...",
                old_commit=prep.old_commit,
                new_commit=prep.target_commit,
            )

        emit(
            UpdatePhase.UPDATING_HEAD,
            "Updating HEAD symlink...",
            old_commit=prep.old_commit,
            new_commit=prep.target_commit,
        )
        return await finalize_switch_version(prep)

    except asyncio.CancelledError:
        return await handle_async_cancellation(
            None, None, None, repo_dir, prep.old_commit, "Version switch cancelled by user"
        )
    finally:
        # finalize cleans up on success; this catches failure paths.
        # Both cached and fresh paths persist a staging dir (cached just
        # holds the marker prep.json), so clean either.
        if prep.staging_root is not None:
            shutil.rmtree(str(prep.staging_root), ignore_errors=True)


# ---------------------------------------------------------------------------
# Read-only helpers
# ---------------------------------------------------------------------------


async def get_git_versions(name: str, expert_dir: Path) -> list[VersionInfo]:  # noqa: C901 — git tag/commit enumeration with fallbacks
    """Retrieve all available versions from git repo (tags + recent commits)."""
    from hivemind.tui.models import VersionInfo

    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return []

    try:
        shallow_file = repo_dir / ".git" / "shallow"
        if shallow_file.exists():
            proc = await asyncio.create_subprocess_exec(
                "git",
                "fetch",
                "--unshallow",
                cwd=str(repo_dir),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=GIT_FETCH_TIMEOUT)

        current_head = get_head_commit(expert_dir)

        analyzed_commits: set[str] = set()
        if expert_dir.exists():
            for d in expert_dir.iterdir():
                if d.is_dir() and not d.is_symlink() and d.name != "__pycache__":
                    analyzed_commits.add(d.name)

        versions: list[VersionInfo] = []
        commit_to_info: dict[str, VersionInfo] = {}

        proc = await asyncio.create_subprocess_exec(
            "git",
            "tag",
            "-l",
            "--format=%(refname:short)|%(creatordate:short)|%(objectname)",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
        tag_output = stdout.decode().strip()

        if proc.returncode == 0 and tag_output:
            for line in tag_output.split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 3:
                    tag_name, date, _ = parts[0], parts[1], parts[2]
                    resolve_proc = await asyncio.create_subprocess_exec(
                        "git",
                        "rev-parse",
                        tag_name,
                        cwd=str(repo_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    resolve_stdout, _ = await asyncio.wait_for(resolve_proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
                    if resolve_proc.returncode == 0:
                        commit = resolve_stdout.decode().strip()
                        vi = VersionInfo(
                            commit=commit,
                            type="tag",
                            name=tag_name,
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(vi)
                        commit_to_info[commit] = vi

        proc = await asyncio.create_subprocess_exec(
            "git",
            "log",
            "--all",
            "--format=%H|%cs|%s",
            "-n",
            "50",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
        log_output = stdout.decode().strip()

        if proc.returncode == 0 and log_output:
            for line in log_output.split("\n"):
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) >= 3:
                    commit, date, message = parts[0], parts[1], parts[2]
                    if commit not in commit_to_info:
                        vi = VersionInfo(
                            commit=commit,
                            type="commit",
                            name=message[:80],
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(vi)
                        commit_to_info[commit] = vi

        def sort_key(v: VersionInfo) -> tuple[int, str]:
            if v.is_active:
                return (2, v.date)
            if v.analyzed:
                return (1, v.date)
            return (0, v.date)

        versions.sort(key=sort_key, reverse=True)

    except (subprocess.SubprocessError, OSError):
        log.exception("Error getting git versions")
        return []
    else:
        return versions


async def commit_exists_in_repo(name: str, commit: str) -> bool:
    """Validate that a commit hash exists in the git repo."""
    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return False

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            "--verify",
            commit,
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=GIT_LOCAL_TIMEOUT)
    except (TimeoutError, OSError):
        return False
    else:
        return proc.returncode == 0
