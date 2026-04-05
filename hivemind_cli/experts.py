"""Expert lifecycle operations for hivemind."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind_cli.analysis import (
    analyze_repo,
    handle_async_cancellation,
    make_cancellation_checker,
    run_async_analysis,
)
from hivemind_cli.config import (
    GIT_FETCH_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    REPOS_DIR,
    get_expert_dir,
    get_head_commit,
    get_repos_for_expert,
    invalidate_provider_cache,
    is_private_expert,
    load_private_repos,
    load_repos,
    load_teams,
    make_emit,
    save_config,
    save_private_repos,
    save_repos,
    save_teams,
)
from hivemind_cli.deployment import (
    deploy_agent,
    deploy_expert,
    flush_librarian,
    mark_librarian_dirty,
    regenerate_hivemind_md,
    undeploy_agent,
    undeploy_expert,
)
from hivemind_cli.git import (
    cleanup_log_files,
    clone_repo,
    commit_analysis_results,
    read_analysis_error,
    resolve_latest_commit,
    revert_checkout,
    save_commit_to_repos,
    stage_for_analysis,
)
from hivemind_cli.models import (
    AppConfig,
    CancellationToken,
    DisableResult,
    EnableResult,
    OperationResult,
    ProgressCallback,
    SwitchProviderResult,
    UpdatePhase,
    UpdateResult,
)
from hivemind_cli.templates import update_expert_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind_cli.tui.models import VersionInfo

logger = logging.getLogger(__name__)

__all__ = [
    "commit_exists_in_repo",
    "delete_expert",
    "disable_expert",
    "enable_expert",
    "get_git_versions",
    "switch_provider",
    "switch_version_async",
    "update_expert",
    "update_expert_async_internal",
]


def update_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
    *,
    skip_analysis: bool = False,
) -> UpdateResult:
    """Update a single expert with progress reporting."""
    emit = make_emit(name, on_progress)
    repo_lookup = get_repos_for_expert(name)
    repos, is_private = repo_lookup.repos, repo_lookup.is_private

    if name not in repos:
        return UpdateResult(success=False, error=f"{name} not in repos")

    # Clone/fetch
    emit(UpdatePhase.CLONING, "Cloning repository...")
    if not clone_repo(name, repos, silent=True):
        return UpdateResult(success=False, error="Failed to clone repository")

    repo_dir = REPOS_DIR / name
    emit(UpdatePhase.FETCHING, "Fetching latest commits...")
    try:
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=str(repo_dir),
            capture_output=True,
            check=True,
            timeout=GIT_FETCH_TIMEOUT,
        )
    except subprocess.CalledProcessError as e:
        return UpdateResult(success=False, error=f"Failed to fetch: {e.stderr.decode()}")

    # Resolve latest commit
    emit(UpdatePhase.CHECKING, "Checking for updates...")
    new_commit = resolve_latest_commit(repo_dir)
    if not new_commit:
        return UpdateResult(success=False, error="Could not resolve latest commit")

    expert_dir = get_expert_dir(name)
    old_commit = get_head_commit(expert_dir)

    if old_commit == new_commit:
        return UpdateResult(success=True, already_up_to_date=True, new_commit=new_commit, old_commit=old_commit)

    # Stage
    emit(
        UpdatePhase.STAGING,
        f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
        new_commit=new_commit,
        old_commit=old_commit,
    )
    staging = stage_for_analysis(name, new_commit, expert_dir, old_commit, repo_dir)
    tmpdir, staged_path, tmp_commit_dir = staging.tmpdir, staging.staged_path, staging.commit_dir

    try:
        # Analyze
        if not skip_analysis:
            emit(
                UpdatePhase.ANALYZING,
                f"Analyzing {new_commit[:12]} (this may take 2-5 minutes)...",
                progress_percent=0,
                new_commit=new_commit,
                old_commit=old_commit,
            )

            handle = analyze_repo(name, new_commit, repo_dir, staged_path, is_update=True)

            while handle.proc.poll() is None:
                time.sleep(1)
                emit(
                    UpdatePhase.ANALYZING,
                    f"Analyzing {new_commit[:12]}...",
                    new_commit=new_commit,
                    old_commit=old_commit,
                )

            if handle._stderr_file is not None:
                handle._stderr_file.close()
            if handle._stdout_file is not None:
                handle._stdout_file.close()

            if handle.proc.returncode != 0:
                error_msg = read_analysis_error(handle.proc.returncode, handle.stderr_path, handle.stdout_path)
                cleanup_log_files(handle.stderr_path, handle.stdout_path)
                revert_checkout(repo_dir, old_commit)
                return UpdateResult(success=False, error=error_msg, new_commit=new_commit, old_commit=old_commit)

            cleanup_log_files(handle.stderr_path, handle.stdout_path)
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

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


async def update_expert_async_internal(
    name: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: CancellationToken | None = None,
) -> UpdateResult:
    """Async version of update_expert with cancellation support."""
    emit = make_emit(name, on_progress)
    check_cancel = make_cancellation_checker(cancellation_token)
    repo_lookup = get_repos_for_expert(name)
    repos, is_private = repo_lookup.repos, repo_lookup.is_private

    if name not in repos:
        return UpdateResult(success=False, error=f"{name} not in repos")

    tmpdir = None
    old_commit = None
    repo_dir = REPOS_DIR / name

    try:
        # Clone/fetch
        check_cancel(UpdatePhase.CLONING)
        emit(UpdatePhase.CLONING, "Cloning repository...")
        if not clone_repo(name, repos, silent=True):
            return UpdateResult(success=False, error="Failed to clone repository")

        check_cancel(UpdatePhase.FETCHING)
        emit(UpdatePhase.FETCHING, "Fetching latest commits...")
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=str(repo_dir),
                capture_output=True,
                check=True,
                timeout=GIT_FETCH_TIMEOUT,
            )
        except subprocess.CalledProcessError as e:
            return UpdateResult(success=False, error=f"Failed to fetch: {e.stderr.decode()}")

        # Resolve latest commit
        check_cancel(UpdatePhase.CHECKING)
        emit(UpdatePhase.CHECKING, "Checking for updates...")
        new_commit = resolve_latest_commit(repo_dir)
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
        staging = stage_for_analysis(name, new_commit, expert_dir, old_commit, repo_dir)
        tmpdir, staged_path, tmp_commit_dir = staging.tmpdir, staging.staged_path, staging.commit_dir

        # Async analysis
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
        )

        if not analysis_result.success:
            revert_checkout(repo_dir, old_commit)
            return UpdateResult(
                success=False, error=analysis_result.error, new_commit=new_commit, old_commit=old_commit
            )

        # Commit + HEAD
        emit(UpdatePhase.COMMITTING, "Committing changes...")
        commit_analysis_results(tmp_commit_dir, expert_dir, new_commit)
        emit(UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink...")
        save_commit_to_repos(name, new_commit, repos, is_private)

        return UpdateResult(success=True, new_commit=new_commit, old_commit=old_commit)

    except asyncio.CancelledError:
        return handle_async_cancellation(None, None, None, repo_dir, old_commit, "Update cancelled by user")

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def get_git_versions(name: str, expert_dir: Path) -> list[VersionInfo]:
    """Retrieve all available versions from git repo (tags + recent commits).

    Args:
        name: Expert name
        expert_dir: Path to expert directory (~/.claude/experts/<name>)

    Returns:
        List of VersionInfo objects sorted by: active first -> tags -> commits (by date)
    """
    from hivemind_cli.tui.models import VersionInfo

    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return []

    try:
        # Check if repo is shallow and unshallow it to get full history
        shallow_file = repo_dir / ".git" / "shallow"
        if shallow_file.exists():
            # Repo is shallow - fetch full history
            subprocess.run(
                ["git", "fetch", "--unshallow"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=GIT_FETCH_TIMEOUT,
            )

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
        result = subprocess.run(
            [
                "git",
                "tag",
                "-l",
                "--format=%(refname:short)|%(creatordate:short)|%(objectname)",
            ],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=GIT_LOCAL_TIMEOUT,
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 3:
                    tag_name, date, _ = parts[0], parts[1], parts[2]

                    # Resolve tag to commit hash
                    resolve_result = subprocess.run(
                        ["git", "rev-parse", tag_name],
                        cwd=str(repo_dir),
                        capture_output=True,
                        text=True,
                        timeout=GIT_LOCAL_TIMEOUT,
                    )
                    if resolve_result.returncode == 0:
                        commit = resolve_result.stdout.strip()

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
        result = subprocess.run(
            ["git", "log", "--all", "--format=%H|%cs|%s", "-n", "50"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=GIT_LOCAL_TIMEOUT,
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
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


def commit_exists_in_repo(name: str, commit: str) -> bool:
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
        result = subprocess.run(
            ["git", "rev-parse", "--verify", commit],
            cwd=str(repo_dir),
            capture_output=True,
            timeout=GIT_LOCAL_TIMEOUT,
        )
    except Exception:
        return False
    else:
        return result.returncode == 0


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

    tmpdir = None
    old_commit = None

    try:
        old_commit = get_head_commit(expert_dir)

        if old_commit == target_commit:
            return UpdateResult(success=True, already_up_to_date=True, old_commit=old_commit, new_commit=target_commit)

        if not commit_exists_in_repo(name, target_commit):
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

            try:
                subprocess.run(
                    ["git", "checkout", "--quiet", target_commit],
                    cwd=str(repo_dir),
                    check=True,
                    timeout=GIT_LOCAL_TIMEOUT,
                )
            except subprocess.CalledProcessError as e:
                return UpdateResult(success=False, error=f"Failed to checkout commit: {e}")

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

            from hivemind_cli.templates import create_expert_prompt

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
            )

            if not analysis_result.success:
                revert_checkout(repo_dir, old_commit)
                return UpdateResult(
                    success=False, error=analysis_result.error, old_commit=old_commit, new_commit=target_commit
                )

            # Commit staged files
            emit(UpdatePhase.COMMITTING, "Committing changes...", old_commit=old_commit, new_commit=target_commit)
            commit_analysis_results(tmp_commit_dir, expert_dir, target_commit)

        # Checkout in repo to keep in sync
        try:
            subprocess.run(
                ["git", "checkout", "--quiet", target_commit], cwd=str(repo_dir), check=True, timeout=GIT_LOCAL_TIMEOUT
            )
        except subprocess.CalledProcessError as e:
            return UpdateResult(success=False, error=f"Failed to checkout commit in repo: {e}")

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
        return handle_async_cancellation(None, None, None, repo_dir, old_commit, "Version switch cancelled by user")

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


# --- Expert Lifecycle (future: use_cases/expert/) ---


def enable_expert(name: str, config: AppConfig) -> EnableResult:
    """Enable an expert (clone repo + create agent symlink)."""
    expert_dir = get_expert_dir(name)
    if not expert_dir.is_dir():
        return EnableResult(success=False, error=f"Expert '{name}' not found")

    already_enabled = name in config.enabled

    if not already_enabled:
        config.enabled.append(name)
        if name in config.disabled:
            config.disabled.remove(name)
        save_config(config)

    repo_lookup = get_repos_for_expert(name)
    if not clone_repo(name, repo_lookup.repos, silent=True):
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
    save_teams(teams)

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
    from hivemind_cli.providers import PROVIDER_CLASSES

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
