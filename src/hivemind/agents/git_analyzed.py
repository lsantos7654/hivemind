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
    "find_staged_prep",
    "get_git_versions",
    "load_prep_result",
    "prep_create_expert",
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

        tmp_commit_dir = tmp_expert / commit
        tmp_commit_dir.mkdir(parents=True, exist_ok=True)

        prompt = create_expert_prompt(name, commit, tmp_repo, tmp_commit_dir)

        # Persist for cross-process finalize (CLI / subagent path).
        # The in-process composition path uses the returned object directly,
        # but a separate `hivemind expert finalize <name>` invocation needs
        # to reconstruct the prep state from disk.
        (tmpdir / _PREP_META_FILENAME).write_text(
            json.dumps(
                {
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


def find_staged_prep(name: str) -> Path | None:
    """Locate the staging dir for an in-flight prep of ``name``.

    Returns the staging root path or ``None`` if no staging dir matches.
    Raises ``ValueError`` if multiple stagings exist for the same name —
    the caller must clean up stale ones first.
    """
    if not STAGING_DIR.is_dir():
        return None
    candidates = sorted(p for p in STAGING_DIR.glob(f"{name}-*") if p.is_dir())
    if not candidates:
        return None
    if len(candidates) > 1:
        msg = f"Multiple staging dirs match '{name}-*': {[c.name for c in candidates]}. Remove stale ones and retry."
        raise ValueError(msg)
    return candidates[0]


def load_prep_result(staging_root: Path) -> PrepCreateResult:
    """Reconstruct a ``PrepCreateResult`` from a staging dir's prep.json."""
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


async def update_git_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
    *,
    skip_analysis: bool = False,
) -> UpdateResult:
    """Fetch, analyze, and rotate HEAD for a git-analyzed agent."""
    from hivemind.agents import registry

    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return UpdateResult(success=False, error=f"{name} is not a git-analyzed agent")

    body: GitAnalyzedBody = agent.body

    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)

    if not skip_analysis:
        validation = opencode.validate_engine()
        if not validation.success:
            return UpdateResult(success=False, error=validation.error)

    tmpdir: str | None = None
    old_commit: str | None = None
    repo_dir = REPOS_DIR / name

    try:
        check_cancel(UpdatePhase.CLONING)
        emit(UpdatePhase.CLONING, "Cloning repository...")
        if not await clone_from_remote(
            name,
            body.params.remote,
            commit=body.params.commit,
            ref_name=body.params.ref_name,
            silent=True,
        ):
            return UpdateResult(success=False, error="Failed to clone repository")

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
            return UpdateResult(success=False, error=f"Failed to fetch: {stderr.decode()}")

        check_cancel(UpdatePhase.CHECKING)
        emit(UpdatePhase.CHECKING, "Checking for updates...")
        new_commit = await resolve_latest_commit(repo_dir)
        if not new_commit:
            return UpdateResult(success=False, error="Could not resolve latest commit")

        expert_dir = get_expert_dir(name)
        old_commit = get_head_commit(expert_dir)

        if old_commit == new_commit:
            return UpdateResult(
                success=True,
                already_up_to_date=True,
                new_commit=new_commit,
                old_commit=old_commit,
            )

        check_cancel(UpdatePhase.STAGING)
        emit(
            UpdatePhase.STAGING,
            f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
            new_commit=new_commit,
            old_commit=old_commit,
        )
        staging = await stage_for_analysis(name, new_commit, expert_dir, old_commit, repo_dir)
        tmpdir, staged_path, tmp_commit_dir = staging.tmpdir, staging.staged_path, staging.commit_dir

        if not skip_analysis:
            check_cancel(UpdatePhase.ANALYZING)
            emit(
                UpdatePhase.ANALYZING,
                f"Analyzing {new_commit[:12]} (this may take 2-5 minutes)...",
                progress_percent=0,
                new_commit=new_commit,
                old_commit=old_commit,
            )

            prompt = update_expert_prompt(name, new_commit, repo_dir, tmp_commit_dir)
            analysis_result = await run_async_analysis(
                name,
                new_commit,
                prompt,
                staged_path,
                repo_dir,
                emit,
                old_commit=old_commit,
                cancellation_token=cancellation_token,
                on_subprocess_start=on_subprocess_start,
                commit_dir=tmp_commit_dir,
                is_update=True,
            )
            if not analysis_result.success:
                await revert_checkout(repo_dir, old_commit)
                return UpdateResult(
                    success=False,
                    error=analysis_result.error,
                    new_commit=new_commit,
                    old_commit=old_commit,
                )
        else:
            emit(
                UpdatePhase.ANALYZING,
                "Skipping analysis (reusing existing docs)...",
                new_commit=new_commit,
                old_commit=old_commit,
            )

        emit(UpdatePhase.COMMITTING, "Committing changes...")
        commit_analysis_results(tmp_commit_dir, expert_dir, new_commit)

        emit(UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink...")
        body.params.commit = new_commit
        registry.save_body(agent)

        await afire_post_mutation()
        return UpdateResult(success=True, new_commit=new_commit, old_commit=old_commit)

    except asyncio.CancelledError:
        return await handle_async_cancellation(None, None, None, repo_dir, old_commit, "Update cancelled by user")
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


async def switch_version(
    name: str,
    target_commit: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
) -> UpdateResult:
    """Switch a git-analyzed agent to a specific commit (analyzes if needed)."""
    from hivemind.agents import registry

    agent = registry.get(name)
    if agent is None or not isinstance(agent.body, GitAnalyzedBody):
        return UpdateResult(success=False, error=f"{name} is not a git-analyzed agent")

    body: GitAnalyzedBody = agent.body

    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)

    expert_dir = get_expert_dir(name)
    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return UpdateResult(success=False, error="Repository not cloned")

    validation = opencode.validate_engine()
    if not validation.success:
        return UpdateResult(success=False, error=validation.error)

    tmpdir: str | None = None
    old_commit: str | None = None

    try:
        # Resolve a tag/branch/short-SHA input to a full commit SHA. Skip the
        # fetch+rev-parse round-trip for full-or-short SHAs that are already
        # in the local repo — that's the common case from the TUI version
        # picker. Anything else (tag like "8.5.1", branch like "main",
        # foreign ref like "origin/feat/x") gets resolved.
        if not (_SHA_RE.match(target_commit) and await commit_exists_in_repo(name, target_commit)):
            resolved = await resolve_ref(repo_dir, target_commit)
            if resolved is None:
                return UpdateResult(
                    success=False,
                    error=f"Could not resolve ref '{target_commit}' in repo for agent '{name}'",
                )
            target_commit = resolved

        old_commit = get_head_commit(expert_dir)
        if old_commit == target_commit:
            return UpdateResult(
                success=True,
                already_up_to_date=True,
                old_commit=old_commit,
                new_commit=target_commit,
            )

        if not await commit_exists_in_repo(name, target_commit):
            return UpdateResult(
                success=False,
                error=f"Commit {target_commit[:12]} not found in repository",
            )

        target_dir = expert_dir / target_commit
        if (
            not target_dir.exists()
            or not (target_dir / DESCRIPTION_FILENAME).exists()
            or not (target_dir / EXPERTISE_FILENAME).exists()
        ):
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
                return UpdateResult(success=False, error=f"Failed to checkout commit: {stderr.decode()}")

            check_cancel(UpdatePhase.STAGING)
            emit(
                UpdatePhase.STAGING,
                f"Staging analysis for {target_commit[:12]}...",
                old_commit=old_commit,
                new_commit=target_commit,
            )

            tmpdir = str(create_staging_dir(name))
            staged_path = Path(tmpdir) / "expert"
            staged_path.mkdir()
            tmp_commit_dir = staged_path / target_commit
            tmp_commit_dir.mkdir()

            check_cancel(UpdatePhase.ANALYZING)
            emit(
                UpdatePhase.ANALYZING,
                f"Analyzing {target_commit[:12]} (this may take 2-5 minutes)...",
                progress_percent=0,
                old_commit=old_commit,
                new_commit=target_commit,
            )

            prompt = create_expert_prompt(name, target_commit, repo_dir, tmp_commit_dir)
            analysis_result = await run_async_analysis(
                name,
                target_commit,
                prompt,
                staged_path,
                repo_dir,
                emit,
                old_commit=old_commit,
                cancellation_token=cancellation_token,
                on_subprocess_start=on_subprocess_start,
                commit_dir=tmp_commit_dir,
                is_update=False,
            )
            if not analysis_result.success:
                await revert_checkout(repo_dir, old_commit)
                return UpdateResult(
                    success=False,
                    error=analysis_result.error,
                    old_commit=old_commit,
                    new_commit=target_commit,
                )

            emit(
                UpdatePhase.COMMITTING,
                "Committing changes...",
                old_commit=old_commit,
                new_commit=target_commit,
            )
            commit_analysis_results(tmp_commit_dir, expert_dir, target_commit)

        # Keep working tree in sync with HEAD
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
            return UpdateResult(
                success=False,
                error=f"Failed to checkout commit in repo: {stderr.decode()}",
            )

        emit(
            UpdatePhase.UPDATING_HEAD,
            "Updating HEAD symlink...",
            old_commit=old_commit,
            new_commit=target_commit,
        )
        head_link = expert_dir / "HEAD"
        if head_link.is_symlink():
            head_link.unlink()
        head_link.symlink_to(target_commit)

        body.params.commit = target_commit
        registry.save_body(agent)

        await afire_post_mutation()
        return UpdateResult(success=True, old_commit=old_commit, new_commit=target_commit)

    except asyncio.CancelledError:
        return await handle_async_cancellation(
            None, None, None, repo_dir, old_commit, "Version switch cancelled by user"
        )
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


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
