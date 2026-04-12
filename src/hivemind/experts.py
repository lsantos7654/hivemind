"""Expert lifecycle operations for hivemind."""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.analysis import (
    handle_async_cancellation,
    make_cancellation_checker,
    run_async_analysis,
)
from hivemind.config import (
    EXPERTS_DIR,
    GIT_CLONE_TIMEOUT,
    GIT_FETCH_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    PRIVATE_EXPERTS_DIR,
    REPOS_DIR,
    ensure_repos_link,
    get_active_provider,
    get_expert_dir,
    get_head_commit,
    get_repos_for_expert,
    invalidate_provider_cache,
    is_private_expert,
    load_config,
    load_private_repos,
    load_repos,
    load_teams,
    make_emit,
    save_config,
    save_private_repos,
    save_repos,
    save_teams,
)
from hivemind.deployment import (
    deploy_agent,
    deploy_expert,
    flush_librarian,
    mark_librarian_dirty,
    regenerate_hivemind_md,
    undeploy_agent,
    undeploy_expert,
)
from hivemind.git import (
    clone_repo,
    commit_analysis_results,
    resolve_latest_commit,
    revert_checkout,
    save_commit_to_repos,
    stage_for_analysis,
)
from hivemind.models import (
    AppConfig,
    CancellationToken,
    DisableResult,
    EnableResult,
    OperationResult,
    ProgressCallback,
    RepoEntry,
    SwitchProviderResult,
    UpdatePhase,
    UpdateResult,
)
from hivemind.templates import update_expert_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind.tui.models import VersionInfo

logger = logging.getLogger(__name__)

__all__ = [
    "add_expert",
    "commit_exists_in_repo",
    "delete_expert",
    "disable_expert",
    "enable_expert",
    "get_git_versions",
    "switch_provider",
    "switch_version_async",
    "update_expert",
]


async def update_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
    *,
    skip_analysis: bool = False,
) -> UpdateResult:
    """Update a single expert with progress reporting and cancellation support."""
    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)
    repo_lookup = get_repos_for_expert(name)
    repos, is_private = repo_lookup.repos, repo_lookup.is_private

    if name not in repos:
        return UpdateResult(success=False, error=f"{name} not in repos")

    # Validate analysis engine and model are available before doing any work
    if not skip_analysis:
        provider = get_active_provider()
        validation = provider.validate_engine()
        if not validation.success:
            return UpdateResult(success=False, error=validation.error)

    tmpdir = None
    old_commit = None
    repo_dir = REPOS_DIR / name

    try:
        # Clone/fetch
        check_cancel(UpdatePhase.CLONING)
        emit(UpdatePhase.CLONING, "Cloning repository...")
        if not await clone_repo(name, repos, silent=True):
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

        # Resolve latest commit
        check_cancel(UpdatePhase.CHECKING)
        emit(UpdatePhase.CHECKING, "Checking for updates...")
        new_commit = await resolve_latest_commit(repo_dir)
        if not new_commit:
            return UpdateResult(success=False, error="Could not resolve latest commit")

        expert_dir = get_expert_dir(name)
        old_commit = get_head_commit(expert_dir)

        if old_commit == new_commit:
            return UpdateResult(success=True, already_up_to_date=True, new_commit=new_commit, old_commit=old_commit)

        # Stage
        check_cancel(UpdatePhase.STAGING)
        emit(
            UpdatePhase.STAGING,
            f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
            new_commit=new_commit,
            old_commit=old_commit,
        )
        staging = await stage_for_analysis(name, new_commit, expert_dir, old_commit, repo_dir)
        tmpdir, staged_path, tmp_commit_dir = staging.tmpdir, staging.staged_path, staging.commit_dir

        # Async analysis
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
                    success=False, error=analysis_result.error, new_commit=new_commit, old_commit=old_commit
                )
        else:
            emit(
                UpdatePhase.ANALYZING,
                "Skipping analysis (reusing existing docs)...",
                new_commit=new_commit,
                old_commit=old_commit,
            )

        # Commit + HEAD
        emit(UpdatePhase.COMMITTING, "Committing changes...")
        commit_analysis_results(tmp_commit_dir, expert_dir, new_commit)
        emit(UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink...")
        save_commit_to_repos(name, new_commit, repos, is_private)

        return UpdateResult(success=True, new_commit=new_commit, old_commit=old_commit)

    except asyncio.CancelledError:
        return await handle_async_cancellation(None, None, None, repo_dir, old_commit, "Update cancelled by user")

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


async def get_git_versions(name: str, expert_dir: Path) -> list[VersionInfo]:
    """Retrieve all available versions from git repo (tags + recent commits).

    Args:
        name: Expert name
        expert_dir: Path to expert directory (~/.claude/experts/<name>)

    Returns:
        List of VersionInfo objects sorted by: active first -> tags -> commits (by date)
    """
    from hivemind.tui.models import VersionInfo

    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return []

    try:
        # Check if repo is shallow and unshallow it to get full history
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

        # Get current HEAD commit
        current_head = get_head_commit(expert_dir)

        # Get analyzed commits from expert_dir subdirectories
        analyzed_commits = set()
        if expert_dir.exists():
            for d in expert_dir.iterdir():
                if d.is_dir() and not d.is_symlink() and d.name != "__pycache__":
                    analyzed_commits.add(d.name)

        versions = []
        commit_to_info = {}  # Track commits to avoid duplicates

        # Query git tags
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

                    # Resolve tag to commit hash
                    resolve_proc = await asyncio.create_subprocess_exec(
                        "git",
                        "rev-parse",
                        tag_name,
                        cwd=str(repo_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    resolve_stdout, _ = await asyncio.wait_for(
                        resolve_proc.communicate(),
                        timeout=GIT_LOCAL_TIMEOUT,
                    )
                    if resolve_proc.returncode == 0:
                        commit = resolve_stdout.decode().strip()

                        version_info = VersionInfo(
                            commit=commit,
                            type="tag",
                            name=tag_name,
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(version_info)
                        commit_to_info[commit] = version_info

        # Query recent commits (exclude ones already added as tags)
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

                    # Skip if already added as a tag
                    if commit not in commit_to_info:
                        version_info = VersionInfo(
                            commit=commit,
                            type="commit",
                            name=message[:80],  # Truncate long messages
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(version_info)
                        commit_to_info[commit] = version_info

        # Sort: active first -> analyzed -> available (by date descending)
        def sort_key(v: VersionInfo) -> tuple[int, str]:
            if v.is_active:
                return (2, v.date)  # Highest priority with reverse=True
            if v.analyzed:
                return (1, v.date)
            return (0, v.date)  # Lowest priority with reverse=True

        versions.sort(key=sort_key, reverse=True)

    except Exception:
        logger.exception("Error getting git versions")
        return []
    else:
        return versions


async def commit_exists_in_repo(name: str, commit: str) -> bool:
    """Validate that a commit hash exists in the git repo.

    Args:
        name: Expert name
        commit: Commit hash to validate

    Returns:
        True if commit exists, False otherwise
    """
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
    except Exception:
        return False
    else:
        return proc.returncode == 0


async def switch_version_async(
    name: str,
    target_commit: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
) -> UpdateResult:
    """Switch expert to a different version (async with cancellation support)."""
    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)
    repo_lookup = get_repos_for_expert(name)
    repos, is_private = repo_lookup.repos, repo_lookup.is_private

    if name not in repos:
        return UpdateResult(success=False, error=f"{name} not in repos")

    expert_dir = get_expert_dir(name)
    repo_dir = REPOS_DIR / name

    if not repo_dir.exists():
        return UpdateResult(success=False, error="Repository not cloned")

    # Validate engine/model before doing any work
    provider = get_active_provider()
    validation = provider.validate_engine()
    if not validation.success:
        return UpdateResult(success=False, error=validation.error)

    tmpdir = None
    old_commit = None

    try:
        old_commit = get_head_commit(expert_dir)

        if old_commit == target_commit:
            return UpdateResult(success=True, already_up_to_date=True, old_commit=old_commit, new_commit=target_commit)

        if not await commit_exists_in_repo(name, target_commit):
            return UpdateResult(success=False, error=f"Commit {target_commit[:12]} not found in repository")

        target_dir = expert_dir / target_commit

        # Analyze if not already done
        if not target_dir.exists() or not (target_dir / "agent.md").exists():
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

            tmpdir = tempfile.mkdtemp(prefix=f"hivemind-version-{name}-")
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

            from hivemind.templates import create_expert_prompt

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
                    success=False, error=analysis_result.error, old_commit=old_commit, new_commit=target_commit
                )

            # Commit staged files
            emit(UpdatePhase.COMMITTING, "Committing changes...", old_commit=old_commit, new_commit=target_commit)
            commit_analysis_results(tmp_commit_dir, expert_dir, target_commit)

        # Checkout in repo to keep in sync
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
            return UpdateResult(success=False, error=f"Failed to checkout commit in repo: {stderr.decode()}")

        # Update HEAD (for already-analyzed versions, commit_analysis_results already did this for new ones)
        emit(UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink...", old_commit=old_commit, new_commit=target_commit)
        head_link = expert_dir / "HEAD"
        if head_link.is_symlink():
            head_link.unlink()
        head_link.symlink_to(target_commit)

        deploy_agent(name)
        save_commit_to_repos(name, target_commit, repos, is_private)

        return UpdateResult(success=True, old_commit=old_commit, new_commit=target_commit)

    except asyncio.CancelledError:
        return await handle_async_cancellation(
            None, None, None, repo_dir, old_commit, "Version switch cancelled by user"
        )

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


async def add_expert(
    name: str,
    url: str,
    *,
    ref_name: str = "",
    is_private: bool = False,
    on_progress: ProgressCallback | None = None,
) -> OperationResult:
    """Register a new expert: clone, analyze, and deploy.

    All work happens in temp directories — nothing visible until success.
    """
    from hivemind.analysis import run_async_analysis
    from hivemind.templates import create_expert_prompt

    emit = make_emit(name, on_progress)

    expert_dir = (PRIVATE_EXPERTS_DIR if is_private else EXPERTS_DIR) / name
    if expert_dir.is_dir():
        return OperationResult(success=False, error=f"Expert '{name}' already exists")

    # Validate analysis engine and model are available before doing any work
    provider = get_active_provider()
    validation = provider.validate_engine()
    if not validation.success:
        return OperationResult(success=False, error=validation.error)

    # Resolve commit from ref
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

    # Clone to temp directory
    tmpdir = tempfile.mkdtemp(prefix=f"hivemind-{name}-")
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
            await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
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
            await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
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
            await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
            if proc.returncode != 0:
                return OperationResult(success=False, error="Failed to clone repository")

        # Resolve commit hash if not pinned
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

        # Create versioned directory and run analysis
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

        # --- Success: move everything to final locations ---
        ensure_repos_link()
        final_repo = REPOS_DIR / name
        if final_repo.exists():
            shutil.rmtree(final_repo)
        shutil.move(str(tmp_repo), str(final_repo))

        target_dir = PRIVATE_EXPERTS_DIR if is_private else EXPERTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        final_expert = target_dir / name
        shutil.move(str(tmp_expert), str(final_expert))

        # Create HEAD symlink
        head_link = final_expert / "HEAD"
        head_link.symlink_to(commit)

        # Update repos config
        repo_entry = RepoEntry(remote=url, commit=commit, ref_name=ref_name)
        if is_private:
            repos = load_private_repos()
            repos[name] = repo_entry
            save_private_repos(repos)
        else:
            repos = load_repos()
            repos[name] = repo_entry
            save_repos(repos)

        # Enable in config
        config = load_config()
        if name not in config.enabled:
            config.enabled.append(name)
        if name in config.disabled:
            config.disabled.remove(name)
        if is_private and name not in config.private:
            config.private.append(name)
        save_config(config)

        # Deploy
        deploy_agent(name)
        deploy_expert(name)
        mark_librarian_dirty()
        flush_librarian(config=config)

        return OperationResult(success=True)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- Expert Lifecycle (future: use_cases/expert/) ---


async def enable_expert(name: str, config: AppConfig) -> EnableResult:
    """Enable an expert (clone repo + create agent symlink)."""
    expert_dir = get_expert_dir(name)
    if not expert_dir.is_dir():
        return EnableResult(success=False, error=f"Expert '{name}' not found")

    # Validate engine/model before deploying — a deployed agent with a broken
    # model will fail at runtime with ProviderModelNotFoundError.
    provider = get_active_provider()
    validation = provider.validate_engine()
    if not validation.success:
        return EnableResult(success=False, error=validation.error)

    already_enabled = name in config.enabled

    if not already_enabled:
        config.enabled.append(name)
        if name in config.disabled:
            config.disabled.remove(name)
        save_config(config)

    repo_lookup = get_repos_for_expert(name)
    if not await clone_repo(name, repo_lookup.repos, silent=True):
        return EnableResult(success=False, error="Failed to clone repository")

    deploy_agent(name)
    deploy_expert(name)

    mark_librarian_dirty()
    flush_librarian(config=config)

    return EnableResult(success=True, already_enabled=already_enabled)


def disable_expert(name: str, config: AppConfig) -> DisableResult:
    """Disable an expert (remove agent symlink)."""
    expert_dir = get_expert_dir(name)
    if not expert_dir.is_dir():
        return DisableResult(success=False, error=f"Expert '{name}' not found")

    already_disabled = name not in config.enabled and name in config.disabled

    if not already_disabled:
        if name in config.enabled:
            config.enabled.remove(name)
        if name not in config.disabled:
            config.disabled.append(name)
        save_config(config)

    undeploy_agent(name)
    undeploy_expert(name)

    mark_librarian_dirty()
    flush_librarian(config=config)

    return DisableResult(success=True, already_disabled=already_disabled)


def delete_expert(name: str, config: AppConfig) -> OperationResult:
    """Delete an expert entirely - removes config entries, agent files, expert dir, and repo entry."""
    import shutil

    expert_dir = get_expert_dir(name)
    if not expert_dir.is_dir():
        return OperationResult(success=False, error=f"Expert '{name}' not found")

    is_private = is_private_expert(name)

    # Undeploy agent and provider expert files
    undeploy_agent(name)
    undeploy_expert(name)

    # Remove from config.json (enabled/disabled lists)
    if name in config.enabled:
        config.enabled.remove(name)
    if name in config.disabled:
        config.disabled.remove(name)
    save_config(config)

    # Remove from repos (hivemind.json or private-repos.json)
    if is_private:
        repos = load_private_repos()
        if name in repos:
            del repos[name]
            save_private_repos(repos)
    else:
        repos = load_repos()
        if name in repos:
            del repos[name]
            save_repos(repos)

    # Remove from any team rosters
    teams = load_teams()
    for team_data in teams.values():
        if name in team_data.experts:
            team_data.experts.remove(name)
    save_teams(teams, config=config)

    # Delete expert directory
    if expert_dir.exists():
        shutil.rmtree(expert_dir)

    # Delete cached repo
    repo_cache = REPOS_DIR / name
    if repo_cache.exists():
        shutil.rmtree(repo_cache)

    mark_librarian_dirty()
    flush_librarian(config=config)
    return OperationResult(success=True)


def switch_provider(provider_name: str, config: AppConfig) -> SwitchProviderResult:
    """Switch active provider."""
    from hivemind.providers import PROVIDER_CLASSES

    if provider_name not in PROVIDER_CLASSES:
        available = ", ".join(PROVIDER_CLASSES)
        return SwitchProviderResult(
            success=False,
            error=f"Unknown provider '{provider_name}'. Available: {available}",
        )

    old_provider = config.active_provider

    if old_provider == provider_name:
        return SwitchProviderResult(
            success=True,
            old_provider=old_provider,
            new_provider=provider_name,
            already_active=True,
        )

    config.active_provider = provider_name
    save_config(config)
    invalidate_provider_cache()

    # Regenerate HIVEMIND.md with new provider's instructions
    regenerate_hivemind_md(config=config)

    return SwitchProviderResult(
        success=True,
        old_provider=old_provider,
        new_provider=provider_name,
    )
