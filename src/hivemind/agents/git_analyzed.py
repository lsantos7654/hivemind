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
import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hivemind import opencode
from hivemind.analysis import (
    handle_async_cancellation,
    make_cancellation_checker,
    run_async_analysis,
)
from hivemind.config import (
    EXPERTS_DIR,
    GIT_FETCH_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    REPOS_DIR,
    ensure_repos_link,
    get_expert_dir,
    get_head_commit,
    make_emit,
)
from hivemind.constants import AGENT_FILENAME
from hivemind.git import (
    clone_from_remote,
    commit_analysis_results,
    create_staging_dir,
    resolve_latest_commit,
    revert_checkout,
    stage_for_analysis,
)
from hivemind.hooks import afire_post_mutation
from hivemind.models import (
    CancellationToken,
    GitAnalyzedParams,
    OperationResult,
    ProgressCallback,
    UpdatePhase,
    UpdateResult,
)
from hivemind.templates import create_expert_prompt, update_expert_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind.tui.models import VersionInfo

log = logging.getLogger(__name__)


__all__ = [
    "GitAnalyzedBody",
    "commit_exists_in_repo",
    "create_git_expert",
    "get_git_versions",
    "switch_version",
    "update_git_expert",
]


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

    def render(self) -> str:
        """Return the canonical body read from ``experts/<name>/HEAD/agent.md``."""
        head_agent = get_expert_dir(self.name) / "HEAD" / AGENT_FILENAME
        if not head_agent.exists():
            return ""
        raw = head_agent.read_text(encoding="utf-8")
        return opencode.strip_frontmatter(raw)

    def librarian_entry(self) -> str:
        expert_dir = get_expert_dir(self.name)
        description = opencode.extract_description(self.render())

        summary_lines = ""
        summary_md = expert_dir / "HEAD" / "summary.md"
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


async def create_git_expert(
    name: str,
    url: str,
    *,
    ref_name: str = "",
    on_progress: ProgressCallback | None = None,
) -> OperationResult:
    """Clone, analyze, and register a new git-analyzed expert (unlisted).

    All work happens in temp directories; nothing visible until success.
    Adds the agent to the catalog in the *unlisted* state — the caller
    is expected to call ``lifecycle.enable_agent(name)`` afterwards to
    deploy it.
    """
    from hivemind.agents import registry
    from hivemind.agents.base import Agent

    registry.load(refresh=True)
    if registry.get(name) is not None:
        return OperationResult(success=False, error=f"Agent '{name}' already exists")

    emit = make_emit(name, on_progress)

    expert_dir = EXPERTS_DIR / name
    if expert_dir.is_dir():
        return OperationResult(success=False, error=f"experts/{name}/ already exists on disk")

    validation = opencode.validate_engine()
    if not validation.success:
        return OperationResult(success=False, error=validation.error)

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

    tmpdir = str(create_staging_dir(name))
    tmp_repo = Path(tmpdir) / "repo"
    tmp_expert = Path(tmpdir) / "expert"
    tmp_expert.mkdir()

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
                return OperationResult(success=False, error="Failed to clone repository")
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
                return OperationResult(success=False, error="Failed to clone repository")
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
                return OperationResult(success=False, error="Failed to clone repository")

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

        emit(UpdatePhase.ANALYZING, f"Analyzing {name} (this may take 2-5 minutes)...")
        prompt = create_expert_prompt(name, commit, tmp_repo, tmp_commit_dir)

        analysis_result = await run_async_analysis(
            name,
            commit,
            prompt,
            tmp_expert,
            tmp_repo,
            emit,
            commit_dir=tmp_commit_dir,
            is_update=False,
        )
        if not analysis_result.success:
            return OperationResult(success=False, error=analysis_result.error or "AI analysis failed")

        # Success — move to final locations
        ensure_repos_link()
        final_repo = REPOS_DIR / name
        if final_repo.exists():
            shutil.rmtree(final_repo)
        shutil.move(str(tmp_repo), str(final_repo))

        EXPERTS_DIR.mkdir(parents=True, exist_ok=True)
        final_expert = EXPERTS_DIR / name
        shutil.move(str(tmp_expert), str(final_expert))

        head_link = final_expert / "HEAD"
        head_link.symlink_to(commit)

        body = GitAnalyzedBody(
            name=name,
            params=GitAnalyzedParams(remote=url, commit=commit, ref_name=ref_name),
        )
        agent = Agent(name=name, body=body, enabled=False)
        registry.add(agent)

        await afire_post_mutation()
        return OperationResult(success=True)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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

    registry.load(refresh=True)
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

    registry.load(refresh=True)
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
        if not target_dir.exists() or not (target_dir / AGENT_FILENAME).exists():
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
