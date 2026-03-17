"""Hivemind CLI - Manage expert agents for AI coding platforms."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
import typing
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.traceback import install as install_traceback

from hivemind_cli.templates import (
    create_expert_prompt,
)
from hivemind_cli.core import (
    _load_json,
    _save_json,
    _load_config,
    _save_config,
    _load_hivemind,
    _save_hivemind,
    _load_repos,
    _save_repos,
    _load_private_repos,
    _save_private_repos,
    _load_teams,
    _load_projects,
    _is_private_expert,
    _get_expert_dir,
    _get_provider,
    _expert_names,
    _get_head_commit,
    _count_versions,
    _ensure_repos_link,
    _ensure_external_docs_link,
    _deploy_agent,
    _undeploy_agent,
    _deploy_expert,
    _undeploy_expert,
    _clone_repo,
    _analyze_repo,
    _update_librarian,
    _regenerate_hivemind_md,
    update_expert,
    enable_expert as core_enable_expert,
    disable_expert as core_disable_expert,
    delete_expert as core_delete_expert_fn,
    redeploy_all_agents,
    switch_provider,
    create_team as core_create_team,
    delete_team as core_delete_team,
    add_expert_to_team as core_add_expert_to_team,
    remove_expert_from_team as core_remove_expert_from_team,
    create_project as core_create_project,
    delete_project as core_delete_project,
    add_team_to_project as core_add_team_to_project,
    remove_team_from_project as core_remove_team_from_project,
    add_repo_to_project as core_add_repo_to_project,
    set_active_project as core_set_active_project,
    clear_active_project as core_clear_active_project,
    UpdatePhase,
    ProgressInfo,
    HIVEMIND_ROOT,
    CACHE_DIR,
    REPOS_DIR,
    REPOS_LINK,
    EXTERNAL_DOCS_DIR,
    EXTERNAL_DOCS_LINK,
    HIVEMIND_JSON,
    CONFIG_JSON,
    AGENTS_DIR,
    EXPERTS_DIR,
    PRIVATE_EXPERTS_DIR,
    COMMANDS_DIR,
    TEAMS_DIR,
    PROJECTS_DIR,
)

THEME = Theme(
    {
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
        "heading": "bold",
        "commit": "cyan",
    }
)

app = typer.Typer(
    name="hivemind",
    help="Manage expert agents for AI coding platforms.",
    invoke_without_command=True,
)
console = Console(theme=THEME)
install_traceback(show_locals=True, console=console)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Manage expert agents for AI coding platforms."""
    if ctx.invoked_subcommand is None:
        from hivemind_cli.tui import HivemindApp

        app_instance = HivemindApp()
        app_instance.run()

# Paths imported from core module


def _complete_expert(incomplete: str) -> list[str]:
    """Shell completion for expert names."""
    return [n for n in _expert_names() if n.startswith(incomplete)]


def _complete_provider(incomplete: str) -> list[str]:
    """Shell completion for provider names."""
    from hivemind_cli.providers import PROVIDER_CLASSES

    return [n for n in PROVIDER_CLASSES if n.startswith(incomplete)]


def _setup_symlink(target: Path, link: Path, label: str) -> None:
    """Create or update a symlink, backing up existing directories."""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            console.print(f"  [success]✓[/success] {label} symlink already correct")
            return
        console.print(
            f"  [warning]![/warning] {label} symlink points to {link.readlink()}, updating..."
        )
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        console.print(
            f"  [warning]![/warning] {label} is a real directory, backing up to {backup.name}/"
        )
        link.rename(backup)
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    console.print(f"  [success]✓[/success] {label} → {target}")


# Wrapper functions to add console output to core module functions
def _deploy_agent_cli(name: str) -> bool:
    """Wrapper for _deploy_agent that adds console output."""
    result = _deploy_agent(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: agent deployed")
    else:
        expert_dir = _get_expert_dir(name)
        head_link = expert_dir / "HEAD"
        if not head_link.exists():
            console.print(
                f"  [warning]![/warning] {name}: no HEAD, skipping agent deploy"
            )
        else:
            console.print(
                f"  [warning]![/warning] {name}: no agent.md in HEAD, skipping agent deploy"
            )
    return result


def _undeploy_agent_cli(name: str) -> None:
    """Wrapper for _undeploy_agent that adds console output."""
    _undeploy_agent(name)
    console.print(f"  [success]✓[/success] {name}: agent removed")


def _deploy_expert_cli(name: str) -> bool:
    """Wrapper for _deploy_expert that adds console output."""
    result = _deploy_expert(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: expert deployed")
    else:
        console.print(f"  [warning]![/warning] {name}: expert directory not found")
    return result


def _clone_repo_cli(name: str, repos: dict) -> bool:
    """Wrapper for _clone_repo that adds console output."""
    if name not in repos:
        console.print(
            f"  [warning]![/warning] {name}: not in hivemind.json repos, skipping clone"
        )
        return False

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # Already cloned

    repo = repos[name]
    commit = repo.get("commit", "")
    ref_name = repo.get("ref_name", "")

    if commit:
        console.print(f"  Cloning {name} at {commit[:12]}...")
    elif ref_name:
        console.print(f"  Cloning {name} at ref {ref_name}...")
    else:
        console.print(f"  Cloning {name} (default branch)...")

    result = _clone_repo(name, repos, silent=False)

    if result:
        if commit:
            console.print(
                f"  [success]✓[/success] {name}: cloned at commit {commit[:12]}"
            )
        elif ref_name:
            console.print(f"  [success]✓[/success] {name}: cloned at ref {ref_name}")
        else:
            console.print(f"  [success]✓[/success] {name}: cloned (default branch)")

    return result


def _update_librarian_cli() -> None:
    """Wrapper for _update_librarian that adds console output."""
    _update_librarian()
    console.print("  [success]✓[/success] Librarian updated")


# --- Commands ---


@app.command()
def init() -> None:
    """Set up provider directory symlinks and enable agents."""
    provider = _get_provider()
    console.print(
        f"[heading]Initializing hivemind (provider: {provider.name})...[/heading]\n"
    )

    # Use provider to initialize directory structure
    results = provider.init_dirs(
        agents_dir=AGENTS_DIR,
        commands_dir=COMMANDS_DIR,
        rules_source=HIVEMIND_ROOT / "HIVEMIND.md",
        teams_dir=TEAMS_DIR,
        projects_dir=PROJECTS_DIR,
        permissions=provider.permissions,
    )
    for label, status_msg in results:
        console.print(f"  [success]✓[/success] {label}: {status_msg}")

    _ensure_repos_link()
    console.print(f"  [success]✓[/success] repos/ → {REPOS_DIR}")
    _ensure_external_docs_link()
    console.print(f"  [success]✓[/success] external_docs/ → {EXTERNAL_DOCS_DIR}")

    config = _load_config()
    repos = _load_repos()

    console.print()
    for name in config["enabled"]:
        _clone_repo_cli(name, repos)
        _deploy_agent_cli(name)
        _deploy_expert_cli(name)

    _update_librarian_cli()

    # Mark provider as enabled in hivemind.json
    if not provider.enabled:
        hivemind = _load_hivemind()
        hivemind.setdefault("providers", {}).setdefault(provider.name, {})["enabled"] = (
            True
        )
        _save_hivemind(hivemind)

    # Remove stale agent files
    for f in AGENTS_DIR.glob("expert-*.md"):
        expert_name = f.name.removeprefix("expert-").removesuffix(".md")
        if expert_name not in config["enabled"]:
            f.unlink()
            console.print(f"  [error]✗[/error] Removed stale: {f.name}")

    # Clean up stale expert symlinks in provider dir
    provider_experts = provider.home_dir / "experts"
    if provider_experts.is_dir():
        for link in provider_experts.iterdir():
            expert_name = link.name
            if expert_name not in config["enabled"]:
                if link.is_symlink():
                    link.unlink()
                elif link.is_dir():
                    import shutil

                    shutil.rmtree(link)
                console.print(f"  [error]✗[/error] Removed stale expert: {expert_name}")

    console.print("\n[bold success]Hivemind initialized![/bold success]")


@app.command(name="list")
def list_experts() -> None:
    """Show all experts with their status."""
    config = _load_config()
    repos = _load_repos()
    private_repos = _load_private_repos()
    private_experts = set(config.get("private", []))
    experts = _expert_names()

    if not experts:
        console.print(
            "No experts found. Use [heading]hivemind add <url>[/heading] to add one."
        )
        return

    # Separate into public and private
    public_expert_names = [name for name in experts if name not in private_experts]
    private_expert_names = [name for name in experts if name in private_experts]

    def create_table_for_experts(expert_names: list[str], title: str) -> Table | None:
        """Create a table for a list of experts."""
        if not expert_names:
            return None

        table = Table(
            title=title, show_header=True, header_style="bold", box=box.ROUNDED
        )
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("HEAD")
        table.add_column("Versions")
        table.add_column("Remote")

        for name in expert_names:
            is_private = name in private_experts

            # Status
            if name in config["enabled"]:
                status = "[success]enabled[/success]"
            elif name in config["disabled"]:
                status = "[warning]disabled[/warning]"
            else:
                status = "[error]unlisted[/error]"

            # HEAD commit
            expert_dir = _get_expert_dir(name)
            head_commit = _get_head_commit(expert_dir)
            head_display = (
                f"[commit]{head_commit[:12]}[/commit]"
                if head_commit
                else "[dim]none[/dim]"
            )

            # Version count
            version_count = _count_versions(expert_dir)
            versions = str(version_count) if version_count > 0 else "[dim]0[/dim]"

            # Remote URL (check both repos)
            remote = ""
            repos_dict = private_repos if is_private else repos
            if name in repos_dict:
                url = repos_dict[name].get("remote", "")
                ref = repos_dict[name].get("ref_name", "")
                remote = url
                if ref:
                    remote += f" @ {ref}"

            table.add_row(name, status, head_display, versions, remote)

        return table

    # Display public experts table
    public_table = create_table_for_experts(public_expert_names, "Public Experts")
    if public_table:
        console.print(public_table)

    # Display private experts table
    private_table = create_table_for_experts(private_expert_names, "Private Experts")
    if private_table:
        if public_table:
            console.print()  # Add spacing between tables
        console.print(private_table)


@app.command()
def add(
    url: str = typer.Argument(help="Git remote URL"),
    ref: typing.Optional[str] = typer.Option(
        None, "--ref", help="Tag, branch, or commit"
    ),
    private: bool = typer.Option(
        False, "--private", help="Mark as private (won't be committed to git)"
    ),
) -> None:
    """Register a new repo expert, clone, analyze, and create agent."""
    # Derive name from URL
    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    console.print(f"[heading]Adding expert: {name}[/heading]")
    console.print(f"  URL: {url}")
    if private:
        console.print(
            f"  [warning]Mode: PRIVATE (will not be committed to git)[/warning]"
        )

    # Error out early if expert already exists (check both public and private)
    public_expert_dir = EXPERTS_DIR / name
    private_expert_dir = PRIVATE_EXPERTS_DIR / name
    if public_expert_dir.is_dir() or private_expert_dir.is_dir():
        console.print(
            f"[error]Error: expert '{name}' already exists. "
            f"Use [bold]hivemind update {name}[/bold] instead.[/error]"
        )
        raise typer.Exit(1)

    # Resolve commit from ref (if provided)
    commit = ""
    ref_name = ref or ""
    if ref:
        console.print(f"  Resolving ref '{ref}'...")
        try:
            result = subprocess.run(
                ["git", "ls-remote", url, ref],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.stdout.strip():
                commit = result.stdout.strip().split()[0]
            else:
                commit = ref
                ref_name = ref
        except (subprocess.TimeoutExpired, FileNotFoundError):
            commit = ref
        console.print(f"  Commit: {commit}")

    # All work happens in a temp directory — nothing visible until success
    tmpdir = tempfile.mkdtemp(prefix=f"hivemind-{name}-")
    tmp_repo = Path(tmpdir) / "repo"
    tmp_expert = Path(tmpdir) / "expert"
    tmp_expert.mkdir()

    try:
        # Clone repo into temp directory
        console.print(f"  Cloning {name}...")
        if commit and ref_name:
            subprocess.run(
                ["git", "clone", "--progress", url, str(tmp_repo)],
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "--quiet", commit],
                cwd=str(tmp_repo),
                check=True,
            )
        elif ref_name:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--progress",
                    "--branch",
                    ref_name,
                    url,
                    str(tmp_repo),
                ],
                check=True,
            )
        else:
            subprocess.run(
                ["git", "clone", "--progress", url, str(tmp_repo)],
                check=True,
            )
        console.print(f"  [success]✓[/success] Cloned to staging area")

        # Resolve commit hash from clone if not pinned
        if not commit:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(tmp_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            commit = result.stdout.strip()
            console.print(f"  [success]✓[/success] Resolved commit: {commit[:12]}")

        # Create versioned directory in temp expert dir
        tmp_commit_dir = tmp_expert / commit
        tmp_commit_dir.mkdir(parents=True, exist_ok=True)
        console.print(
            f"  [success]✓[/success] Created staging experts/{name}/{commit[:12]}/"
        )

        # Run AI analysis — writes into temp dirs
        with console.status(
            f"[heading]Running AI analysis of {name}...[/heading]", spinner="dots"
        ):
            success = _analyze_repo(name, commit, tmp_repo, tmp_expert)
        if not success:
            console.print(f"[error]Error: AI analysis failed for {name}[/error]")
            raise typer.Exit(1)
        console.print(f"  [success]✓[/success] AI analysis complete")

        # --- Success: move everything to final locations ---

        # Move repo to final location
        _ensure_repos_link()
        final_repo = REPOS_DIR / name
        if final_repo.exists():
            shutil.rmtree(final_repo)
        shutil.move(str(tmp_repo), str(final_repo))
        console.print(f"  [success]✓[/success] Repo installed to repos/{name}/")

        # Move expert dir to final location (public or private)
        if private:
            expert_dir = PRIVATE_EXPERTS_DIR / name
            PRIVATE_EXPERTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_expert), str(expert_dir))
            console.print(
                f"  [success]✓[/success] Expert installed to private-experts/{name}/"
            )
        else:
            expert_dir = EXPERTS_DIR / name
            EXPERTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_expert), str(expert_dir))
            console.print(f"  [success]✓[/success] Expert installed to experts/{name}/")

        # Create HEAD symlink
        head_link = expert_dir / "HEAD"
        head_link.symlink_to(commit)
        console.print(f"  [success]✓[/success] HEAD → {commit[:12]}")

        # Update repos.json or private-repos.json
        if private:
            repos = _load_private_repos()
            repos[name] = {"remote": url, "commit": commit, "ref_name": ref_name}
            _save_private_repos(repos)
            console.print("  [success]✓[/success] Added to hivemind.json (private)")
        else:
            repos = _load_repos()
            repos[name] = {"remote": url, "commit": commit, "ref_name": ref_name}
            _save_repos(repos)
            console.print("  [success]✓[/success] Added to hivemind.json")

        # Enable in config and mark as private if needed
        config = _load_config()
        if name not in config["enabled"]:
            config["enabled"].append(name)
        if name in config["disabled"]:
            config["disabled"].remove(name)
        if private:
            config.setdefault("private", [])
            if name not in config["private"]:
                config["private"].append(name)
        _save_config(config)
        console.print("  [success]✓[/success] Enabled in config.json")

        # Deploy agent and expert
        _deploy_agent_cli(name)
        _deploy_expert_cli(name)
        _update_librarian_cli()

        summary_lines = [
            f"[success]✓[/success] Expert [heading]{name}[/heading] is ready",
            f"[success]✓[/success] HEAD → [commit]{commit[:12]}[/commit]",
            f"[success]✓[/success] Agent: [heading]expert-{name}[/heading]",
        ]
        console.print()
        console.print(
            Panel(
                "\n".join(summary_lines),
                title="[bold success]Expert created successfully[/bold success]",
                border_style="green",
            )
        )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.command()
def enable(
    name: str = typer.Argument(
        help="Expert name to enable", autocompletion=_complete_expert
    ),
) -> None:
    """Enable an expert (clones repo if needed, creates agent symlink)."""
    result = core_enable_expert(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    repos = _load_repos()
    _clone_repo_cli(name, repos)
    _deploy_agent_cli(name)

    if result["already_enabled"]:
        console.print(
            f"[success]✓[/success] {name}: already enabled, ensured repo and agent link"
        )
    else:
        console.print(f"[success]✓[/success] Enabled: {name}")


@app.command()
def disable(
    name: str = typer.Argument(
        help="Expert name to disable", autocompletion=_complete_expert
    ),
) -> None:
    """Disable an expert (removes agent symlink)."""
    result = core_disable_expert(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    _undeploy_agent_cli(name)

    if result["already_disabled"]:
        console.print(
            f"[warning]✓[/warning] {name}: already disabled, ensured agent link removed"
        )
    else:
        console.print(f"[warning]✓[/warning] Disabled: {name}")


@app.command()
def delete(
    name: str = typer.Argument(
        help="Expert name to delete", autocompletion=_complete_expert
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompt"
    ),
) -> None:
    """Delete an expert entirely (removes all local data and agent files)."""
    if not force:
        confirm = typer.confirm(
            f"Delete expert '{name}'? This removes all local data, agent files, and cached repos."
        )
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    result = core_delete_expert_fn(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    console.print(f"[error]✗[/error] Deleted: {name}")


@app.command()
def update(
    name: typing.Optional[str] = typer.Argument(
        None,
        help="Expert name (or omit for all enabled)",
        autocompletion=_complete_expert,
    ),
    skip_analysis: bool = typer.Option(
        False,
        "--skip-analysis",
        help="Pull latest repo changes without re-running AI analysis",
    ),
) -> None:
    """Fetch latest commits and re-analyze with AI."""
    config = _load_config()
    repos = _load_repos()

    if name:
        names = [name]
        if name not in repos:
            console.print(f"[error]Error: '{name}' not found in hivemind.json repos[/error]")
            raise typer.Exit(1)
    else:
        names = config["enabled"]

    if not names:
        console.print("No experts to update.")
        return

    # Track which experts need updating (not already up to date)
    experts_to_update: list[str] = []

    for expert_name in names:
        console.print(f"\n[heading]Updating {expert_name}...[/heading]")

        # Define progress callback for CLI
        def on_progress(info: ProgressInfo):
            if info.phase == UpdatePhase.ANALYZING:
                console.print(f"  [info]→[/info] {info.message}")
            elif info.phase not in [UpdatePhase.CLONING, UpdatePhase.FETCHING]:
                console.print(f"  [success]✓[/success] {info.message}")

        result = update_expert(
            expert_name, on_progress=on_progress, skip_analysis=skip_analysis
        )

        if not result["success"]:
            console.print(f"  [error]✗[/error] {result['error']}")
        elif result.get("already_up_to_date"):
            console.print(
                f"  [success]✓[/success] Already up to date ({result['new_commit'][:12]})"
            )
        else:
            old_display = result["old_commit"][:12] if result["old_commit"] else "none"
            console.print(
                f"  [success]✓[/success] Updated from {old_display} to {result['new_commit'][:12]}"
            )
            experts_to_update.append(expert_name)

    # Regenerate librarian if any experts were updated
    if experts_to_update:
        _update_librarian_cli()
        console.print(f"\n[bold success]Update complete.[/bold success]")
    else:
        console.print("\n[success]All experts are up to date.[/success]")


@app.command()
def query(
    question: str = typer.Argument(help="Question to ask the librarian"),
) -> None:
    """Ask the librarian which expert(s) can help with a question."""
    librarian = AGENTS_DIR / "librarian.md"
    if not librarian.exists():
        console.print(
            "[error]Error: librarian.md not found. Run [bold]hivemind init[/bold] first.[/error]"
        )
        raise typer.Exit(1)

    provider = _get_provider()
    system_prompt = librarian.read_text()
    cmd = provider.build_query_command()

    with console.status("Asking the librarian...", spinner="dots"):
        result = subprocess.run(
            cmd,
            input=f"{system_prompt}\n\n{question}",
            text=True,
            capture_output=True,
        )
    if result.stdout:
        console.print(result.stdout.rstrip())


# --- Provider subcommands ---

provider_app = typer.Typer(
    name="provider",
    help="Manage AI coding platform providers.",
    no_args_is_help=True,
)
app.add_typer(provider_app, name="provider")


@provider_app.command(name="list")
def provider_list() -> None:
    """List available providers and their status."""
    from hivemind_cli.providers import PROVIDER_CLASSES

    config = _load_config()
    hivemind = _load_hivemind()
    active = config.get("active_provider", "")
    providers = hivemind.get("providers", {})

    table = Table(
        title="Providers", show_header=True, header_style="bold", box=box.ROUNDED
    )
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Engine")
    table.add_column("Home Directory")
    table.add_column("Model")

    for name in sorted(PROVIDER_CLASSES):
        prov_config = providers.get(name, {})
        is_active = name == active
        enabled = prov_config.get("enabled", False)

        if is_active:
            status_str = "[success]active[/success]"
        elif enabled:
            status_str = "[info]enabled[/info]"
        else:
            status_str = "[dim]disabled[/dim]"

        engine = prov_config.get("engine", "[dim]not configured[/dim]")
        home_dir = prov_config.get("home_dir", "[dim]not configured[/dim]")
        model = prov_config.get("settings", {}).get("model", "[dim]default[/dim]")

        table.add_row(name, status_str, engine, home_dir, model)

    console.print(table)


@provider_app.command(name="switch")
def provider_switch(
    name: str = typer.Argument(
        help="Provider name to switch to", autocompletion=_complete_provider
    ),
) -> None:
    """Switch active provider (regenerates all agent files)."""
    result = switch_provider(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    console.print(f"[success]Switched to provider: [heading]{name}[/heading][/success]")
    console.print(
        "[info]Run [bold]hivemind redeploy[/bold] to regenerate agent files "
        "for the new provider.[/info]"
    )


@provider_app.command(name="show")
def provider_show(
    name: typing.Optional[str] = typer.Argument(
        None,
        help="Provider name (default: active provider)",
        autocompletion=_complete_provider,
    ),
) -> None:
    """Show detailed configuration for a provider."""
    config = _load_config()
    hivemind = _load_hivemind()
    active = config.get("active_provider", "")
    target = name or active
    providers = hivemind.get("providers", {})

    if target not in providers:
        console.print(f"[error]Error: provider '{target}' not found in config[/error]")
        raise typer.Exit(1)

    prov_config = providers[target]
    is_active = target == active

    lines: list[str] = []
    lines.append(f"[heading]Provider: {target}[/heading]")
    lines.append(
        f"Active: {'[success]yes[/success]' if is_active else '[dim]no[/dim]'}"
    )
    lines.append(
        f"Enabled: {'[success]yes[/success]' if prov_config.get('enabled') else '[dim]no[/dim]'}"
    )
    lines.append(f"Engine: {prov_config.get('engine', 'not set')}")
    lines.append(f"Home directory: {prov_config.get('home_dir', 'not set')}")

    settings = prov_config.get("settings", {})
    if settings:
        lines.append("")
        lines.append("[heading]Settings:[/heading]")
        for key, value in sorted(settings.items()):
            if isinstance(value, list):
                lines.append(f"  {key}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                lines.append(f"  {key}:")
                for k, v in sorted(value.items()):
                    lines.append(f"    {k}: {v}")
            else:
                lines.append(f"  {key}: {value}")

    console.print(Panel("\n".join(lines), border_style="blue"))


# --- Team subcommands ---

team_app = typer.Typer(
    name="team",
    help="Manage expert teams.",
    no_args_is_help=True,
)
app.add_typer(team_app, name="team")


def _complete_team(incomplete: str) -> list[str]:
    """Shell completion for team names."""
    return [n for n in _load_teams() if n.startswith(incomplete)]


@team_app.command(name="list")
def team_list() -> None:
    """List all teams with their roster info."""
    teams = _load_teams()

    if not teams:
        console.print(
            "No teams configured. Use [heading]hivemind team create <name>[/heading] to create one."
        )
        return

    table = Table(
        title="Teams", show_header=True, header_style="bold", box=box.ROUNDED
    )
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Roster")
    table.add_column("Size")

    for name, data in sorted(teams.items()):
        experts = data.get("experts", [])
        max_roster = data.get("max_roster", 8)
        roster_str = ", ".join(experts) if experts else "[dim]empty[/dim]"
        size_str = f"{len(experts)}/{max_roster}"
        table.add_row(name, data.get("description", ""), roster_str, size_str)

    console.print(table)


@team_app.command(name="create")
def team_create(
    name: str = typer.Argument(help="Team name"),
    description: str = typer.Option(..., "--description", "-d", help="Team description"),
    experts: str = typer.Option(
        ..., "--experts", "-e", help="Comma-separated expert names"
    ),
    max_roster: int | None = typer.Option(
        None, "--max-roster", help="Maximum roster size"
    ),
    skip_analysis: bool = typer.Option(
        False, "--skip-analysis", help="Use template instead of AI-generated lead"
    ),
) -> None:
    """Create a new team with AI-generated lead agent."""
    expert_list = [e.strip() for e in experts.split(",") if e.strip()]

    console.print(f"[heading]Creating team: {name}[/heading]")
    console.print(f"  Description: {description}")
    console.print(f"  Experts: {', '.join(expert_list)}")

    if not skip_analysis:
        with console.status(
            "[heading]Generating team lead agent...[/heading]", spinner="dots"
        ):
            result = core_create_team(
                name, description, expert_list, max_roster=max_roster
            )
    else:
        result = core_create_team(
            name,
            description,
            expert_list,
            max_roster=max_roster,
            skip_analysis=True,
        )

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    console.print(f"  [success]✓[/success] Team lead deployed: team-lead-{name}")
    console.print(f"  [success]✓[/success] Team experts deployed")
    console.print(f"  [success]✓[/success] Librarian updated")
    console.print(f"\n[bold success]Team '{name}' created![/bold success]")


@team_app.command(name="show")
def team_show(
    name: str = typer.Argument(
        help="Team name", autocompletion=_complete_team
    ),
) -> None:
    """Show team details and roster."""
    teams = _load_teams()
    if name not in teams:
        console.print(f"[error]Error: team '{name}' not found[/error]")
        raise typer.Exit(1)

    team = teams[name]
    lines: list[str] = []
    lines.append(f"[heading]Team: {name}[/heading]")
    lines.append(f"Description: {team.get('description', '')}")
    lines.append(f"Max roster: {team.get('max_roster', 8)}")

    experts = team.get("experts", [])
    lines.append(f"\n[heading]Roster ({len(experts)}):[/heading]")
    for expert in experts:
        lines.append(f"  - {expert}")

    # Show context files
    team_dir = TEAMS_DIR / name
    lines.append(f"\n[heading]Context files:[/heading]")
    for fname in ["lead.md", "general.md", "private.md"]:
        fpath = team_dir / fname
        status = "[success]exists[/success]" if fpath.exists() else "[dim]empty[/dim]"
        lines.append(f"  - {fname}: {status}")

    # Expert overrides
    experts_dir = team_dir / "experts"
    if experts_dir.exists():
        overrides = list(experts_dir.glob("*.md"))
        if overrides:
            lines.append(f"\n[heading]Expert overrides:[/heading]")
            for f in overrides:
                lines.append(f"  - {f.name}")

    # Projects using this team
    projects = _load_projects()
    team_projects = [
        p for p, d in projects.items() if name in d.get("teams", [])
    ]
    if team_projects:
        lines.append(f"\n[heading]Projects:[/heading]")
        for p in team_projects:
            lines.append(f"  - {p}")

    console.print(Panel("\n".join(lines), border_style="blue"))


@team_app.command(name="add-expert")
def team_add_expert(
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
    expert: str = typer.Argument(
        help="Expert name", autocompletion=_complete_expert
    ),
) -> None:
    """Add an expert to a team's roster."""
    result = core_add_expert_to_team(team, expert)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Added {expert} to team {team}"
    )


@team_app.command(name="remove-expert")
def team_remove_expert(
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
    expert: str = typer.Argument(
        help="Expert name", autocompletion=_complete_expert
    ),
) -> None:
    """Remove an expert from a team's roster."""
    result = core_remove_expert_from_team(team, expert)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Removed {expert} from team {team}"
    )


@team_app.command(name="delete")
def team_delete(
    name: str = typer.Argument(help="Team name", autocompletion=_complete_team),
) -> None:
    """Delete a team and its deployed agents."""
    if not typer.confirm(f"Delete team '{name}' and all its agents?"):
        console.print("[warning]Cancelled[/warning]")
        raise typer.Exit(0)

    result = core_delete_team(name)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Team '{name}' deleted")


# --- Project subcommands ---

project_app = typer.Typer(
    name="project",
    help="Manage projects.",
    no_args_is_help=True,
)
app.add_typer(project_app, name="project")


def _complete_project(incomplete: str) -> list[str]:
    """Shell completion for project names."""
    return [n for n in _load_projects() if n.startswith(incomplete)]


@project_app.command(name="list")
def project_list() -> None:
    """List all projects."""
    projects = _load_projects()
    config = _load_config()
    active = config.get("active_project")

    if not projects:
        console.print(
            "No projects configured. Use [heading]hivemind project create <name>[/heading] to create one."
        )
        return

    table = Table(
        title="Projects", show_header=True, header_style="bold", box=box.ROUNDED
    )
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Description")
    table.add_column("Teams")

    for name, data in sorted(projects.items()):
        status = "[success]active[/success]" if name == active else "[dim]inactive[/dim]"
        teams_str = ", ".join(data.get("teams", [])) or "[dim]none[/dim]"
        table.add_row(name, status, data.get("description", ""), teams_str)

    console.print(table)


@project_app.command(name="create")
def project_create(
    name: str = typer.Argument(help="Project name"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Project description"
    ),
    teams: str = typer.Option("", "--teams", "-t", help="Comma-separated team names"),
    repos: str = typer.Option("", "--repos", "-r", help="Comma-separated repo names"),
    objectives: str = typer.Option(
        "", "--objectives", "-o", help="Comma-separated objectives"
    ),
    skip_analysis: bool = typer.Option(
        False, "--skip-analysis", help="Use template instead of AI-generated lead"
    ),
) -> None:
    """Create a new project with AI-generated lead agent."""
    teams_list = [t.strip() for t in teams.split(",") if t.strip()]
    repos_list = [r.strip() for r in repos.split(",") if r.strip()]
    objectives_list = [o.strip() for o in objectives.split(",") if o.strip()]

    console.print(f"[heading]Creating project: {name}[/heading]")
    console.print(f"  Description: {description}")
    if teams_list:
        console.print(f"  Teams: {', '.join(teams_list)}")
    if repos_list:
        console.print(f"  Repos: {', '.join(repos_list)}")

    if not skip_analysis:
        with console.status(
            "[heading]Generating project lead agent...[/heading]", spinner="dots"
        ):
            result = core_create_project(
                name, description, teams_list, repos_list, objectives_list
            )
    else:
        result = core_create_project(
            name,
            description,
            teams_list,
            repos_list,
            objectives_list,
            skip_analysis=True,
        )

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    console.print(f"  [success]✓[/success] Project lead deployed: project-lead-{name}")
    console.print(f"  [success]✓[/success] Librarian updated")
    console.print(f"\n[bold success]Project '{name}' created![/bold success]")


@project_app.command(name="show")
def project_show(
    name: str = typer.Argument(
        help="Project name", autocompletion=_complete_project
    ),
) -> None:
    """Show project details."""
    projects = _load_projects()
    if name not in projects:
        console.print(f"[error]Error: project '{name}' not found[/error]")
        raise typer.Exit(1)

    project = projects[name]
    config = _load_config()
    is_active = config.get("active_project") == name

    lines: list[str] = []
    lines.append(f"[heading]Project: {name}[/heading]")
    lines.append(f"Description: {project.get('description', '')}")
    lines.append(
        f"Status: {'[success]active[/success]' if is_active else '[dim]inactive[/dim]'}"
    )

    teams_list = project.get("teams", [])
    lines.append(f"\n[heading]Teams ({len(teams_list)}):[/heading]")
    for team in teams_list:
        lines.append(f"  - {team}")

    repos_list = project.get("repos", [])
    if repos_list:
        lines.append(f"\n[heading]Repos:[/heading]")
        for repo in repos_list:
            lines.append(f"  - {repo}")

    objectives = project.get("objectives", [])
    if objectives:
        lines.append(f"\n[heading]Objectives:[/heading]")
        for obj in objectives:
            lines.append(f"  - {obj}")

    # Show context files
    project_dir = PROJECTS_DIR / name
    lines.append(f"\n[heading]Context files:[/heading]")
    for fname in ["lead.md", "overview.md", "context.md", "project.md"]:
        fpath = project_dir / fname
        status = "[success]exists[/success]" if fpath.exists() else "[dim]empty[/dim]"
        lines.append(f"  - {fname}: {status}")

    console.print(Panel("\n".join(lines), border_style="blue"))


@project_app.command(name="set")
def project_set(
    name: str = typer.Argument(
        help="Project name to activate", autocompletion=_complete_project
    ),
) -> None:
    """Set the active project (updates HIVEMIND.md for all sessions)."""
    result = core_set_active_project(name)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Active project set to [heading]{name}[/heading]"
    )
    console.print("[info]HIVEMIND.md updated — all new sessions will see this project.[/info]")


@project_app.command(name="clear")
def project_clear() -> None:
    """Clear the active project."""
    result = core_clear_active_project()
    console.print("[success]✓[/success] Active project cleared")
    console.print("[info]HIVEMIND.md updated — no active project.[/info]")


@project_app.command(name="add-team")
def project_add_team(
    project: str = typer.Argument(
        help="Project name", autocompletion=_complete_project
    ),
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
) -> None:
    """Assign a team to a project."""
    result = core_add_team_to_project(project, team)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Added team {team} to project {project}"
    )


@project_app.command(name="remove-team")
def project_remove_team(
    project: str = typer.Argument(
        help="Project name", autocompletion=_complete_project
    ),
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
) -> None:
    """Remove a team from a project."""
    result = core_remove_team_from_project(project, team)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Removed team {team} from project {project}"
    )


@project_app.command(name="add-repo")
def project_add_repo(
    project: str = typer.Argument(
        help="Project name", autocompletion=_complete_project
    ),
    repo: str = typer.Argument(
        help="Repo name", autocompletion=_complete_expert
    ),
) -> None:
    """Associate a repo with a project."""
    result = core_add_repo_to_project(project, repo)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(
        f"[success]✓[/success] Added repo {repo} to project {project}"
    )


@project_app.command(name="delete")
def project_delete(
    name: str = typer.Argument(
        help="Project name", autocompletion=_complete_project
    ),
) -> None:
    """Delete a project."""
    if not typer.confirm(f"Delete project '{name}' and its lead agent?"):
        console.print("[warning]Cancelled[/warning]")
        raise typer.Exit(0)

    result = core_delete_project(name)
    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Project '{name}' deleted")


# --- Redeploy command ---


@app.command()
def redeploy() -> None:
    """Regenerate all agent files for the active provider.

    Use after changing provider settings in hivemind.json
    (model, tools, temperature) or after switching providers.
    """
    provider = _get_provider()
    console.print(
        f"[heading]Redeploying all agents (provider: {provider.name})...[/heading]\n"
    )

    result = redeploy_all_agents()

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    deployed = result.get("deployed", [])
    failed = result.get("failed", [])
    teams_deployed = result.get("teams_deployed", [])
    projects_deployed = result.get("projects_deployed", [])

    for name in deployed:
        console.print(f"  [success]✓[/success] {name}: redeployed")
    for name in failed:
        console.print(f"  [warning]![/warning] {name}: failed to redeploy")
    for name in teams_deployed:
        console.print(f"  [success]✓[/success] {name}: redeployed")
    for name in projects_deployed:
        console.print(f"  [success]✓[/success] {name}: redeployed")

    if result.get("librarian_updated"):
        console.print(f"  [success]✓[/success] Librarian updated")

    total = len(deployed) + len(teams_deployed) + len(projects_deployed)
    console.print(f"\n[bold success]Redeployed {total} agent(s).[/bold success]")



@app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    agent: str = typer.Argument(
        ..., help="Agent name for output directory", autocompletion=_complete_expert
    ),
    max_pages: int | None = typer.Option(
        None, "--max-pages", "-n", help="Maximum pages to crawl (default: no limit)"
    ),
    raw_markdown: bool = typer.Option(
        False,
        "--raw-markdown",
        help="Force raw markdown fetching (.md endpoints only, no browser fallback)",
    ),
) -> None:
    """Crawl a website and save documentation for an expert agent.

    Crawls the specified URL and saves markdown files to
    ~/.cache/hivemind/external_docs/<agent>/ for use by expert agents.

    Always runs in preview mode - you'll see all discovered URLs
    before the crawl begins.
    """
    # Validate that the agent exists
    expert_dir = _get_expert_dir(agent)
    if not expert_dir.is_dir():
        console.print(f"[error]Error: Expert '{agent}' not found.[/error]")
        console.print("\n[info]Available experts:[/info]")
        experts = sorted(_expert_names())
        if experts:
            for expert in experts:
                console.print(f"  - {expert}")
        else:
            console.print(
                "  [dim]No experts configured. Use [bold]hivemind add <url>[/bold] to add one.[/dim]"
            )
        raise typer.Exit(1)

    from hivemind_cli.crawler import (
        crawl_from_sitemap,
        crawl_urls_raw_markdown,
        crawl_website,
        is_sitemap_url,
        preview_crawl,
        preview_sitemap,
    )

    output_dir = EXTERNAL_DOCS_DIR / agent

    console.print(f"[heading]Crawling Documentation for {agent}[/heading]\n")
    console.print(f"[info]URL:[/info] {url}")
    console.print(f"[info]Output:[/info] {output_dir}")
    console.print()

    # Phase 1: Preview (discover URLs)
    # Detect and route based on URL type
    if is_sitemap_url(url):
        console.print("[info]🗺️  Detected sitemap URL, discovering pages...[/info]")
        try:
            discovered_urls = asyncio.run(
                preview_sitemap(sitemap_url=url, max_pages=max_pages)
            )
        except Exception as e:
            console.print(f"[error]✗ Failed to fetch sitemap: {e}[/error]")
            raise typer.Exit(1)
        is_sitemap = True
    else:
        console.print("[info]Discovering URLs...[/info]")
        try:
            discovered_urls = asyncio.run(preview_crawl(url=url, max_pages=max_pages))
        except Exception as e:
            console.print(f"[error]✗ Failed to discover URLs: {e}[/error]")
            raise typer.Exit(1)
        is_sitemap = False

    if not discovered_urls:
        console.print("[error]✗ No URLs discovered[/error]")
        raise typer.Exit(1)

    console.print(f"\n[success]Found {len(discovered_urls)} pages:[/success]\n")

    # Show ALL discovered URLs
    for i, discovered_url in enumerate(discovered_urls, 1):
        console.print(f"  {i}. {discovered_url}")

    console.print()

    # Ask for confirmation
    if not typer.confirm(f"Crawl all {len(discovered_urls)} pages?", default=True):
        console.print("[warning]Crawl cancelled[/warning]")
        raise typer.Exit(0)

    console.print()

    # Phase 2: Full crawl with progress
    # Determine strategy based on explicit flags
    if raw_markdown:
        # User explicitly requested raw markdown only
        console.print("[info]Raw markdown mode enabled (no browser fallback)[/info]\n")
        strategy_name = "raw_markdown"
    elif is_sitemap:
        # Sitemap-based crawl
        console.print("[heading]Crawling pages...[/heading]\n")
        strategy_name = "sitemap"
    else:
        # Default: browser-based scraping
        console.print("[heading]Crawling pages...[/heading]\n")
        strategy_name = "browser"

    from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

    progress = Progress(
        TextColumn("[bold blue]{task.fields[current_url]}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.completed}/{task.total} pages"),
        TimeRemainingColumn(),
        console=console,
    )

    def on_page(page_url: str, success: bool) -> None:
        progress.update(task_id, advance=1, current_url=page_url)
        if success:
            progress.console.log(f"[success]✓[/success] {page_url}")

    with progress:
        task_id = progress.add_task(
            "crawling",
            total=len(discovered_urls),
            current_url=url,
        )

        try:
            if strategy_name == "raw_markdown":
                # Pure raw markdown (no fallback)
                result = asyncio.run(
                    crawl_urls_raw_markdown(
                        urls=discovered_urls,
                        output_dir=str(output_dir),
                        on_page_callback=on_page,
                    )
                )
            elif strategy_name == "sitemap":
                # Sitemap-based browser crawl
                result = asyncio.run(
                    crawl_from_sitemap(
                        sitemap_url=url,
                        max_pages=len(discovered_urls),
                        output_dir=str(output_dir),
                        on_page_callback=on_page,
                    )
                )
            else:  # browser
                # Browser crawl with BFS
                result = asyncio.run(
                    crawl_website(
                        url=url,
                        max_pages=len(discovered_urls),
                        output_dir=str(output_dir),
                        on_page_callback=on_page,
                    )
                )
        except Exception as e:
            console.print(f"\n[error]✗ Crawl failed: {e}[/error]")
            raise typer.Exit(1)

    # Display summary
    console.print()

    table = Table(title="Crawl Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")

    table.add_row("Total Pages", str(result.total_pages))
    table.add_row("Successful", str(result.successful_pages))
    table.add_row("Failed", str(result.failed_pages))
    table.add_row("Output Directory", str(output_dir))

    console.print(table)
    console.print()

    if result.successful_pages > 0:
        console.print(
            f"[success]✓ Successfully crawled {result.successful_pages} pages[/success]"
        )
        console.print(f"\n[info]Documentation saved to:[/info] {output_dir}")
        console.print(f"[info]Expert agents can now access these docs[/info]")
    else:
        console.print("[error]✗ No pages were successfully crawled[/error]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show a dashboard of hivemind status."""
    provider = _get_provider()
    config = _load_config()

    # --- Overview panel ---
    overview_lines: list[str] = []
    overview_lines.append(f"Provider: [heading]{provider.name}[/heading]")

    active_project = config.get("active_project")
    if active_project:
        overview_lines.append(
            f"Active project: [success]{active_project}[/success] "
            f"(lead: project-lead-{active_project})"
        )
    else:
        overview_lines.append("Active project: [dim]none[/dim]")

    enabled = config.get("enabled", [])
    disabled = config.get("disabled", [])
    teams = _load_teams()
    projects = _load_projects()
    overview_lines.append(
        f"Experts: [success]{len(enabled)} enabled[/success]"
        + (f", [warning]{len(disabled)} disabled[/warning]" if disabled else "")
    )
    overview_lines.append(f"Teams: {len(teams)}")
    overview_lines.append(f"Projects: {len(projects)}")

    console.print(Panel("\n".join(overview_lines), title="Hivemind", border_style="blue"))

    # --- Experts table (enabled + disabled only, skip unlisted) ---
    repos = _load_repos()
    private_repos = _load_private_repos()
    private_expert_set = set(config.get("private", []))

    listed_experts = [
        name for name in _expert_names()
        if name in enabled or name in disabled
    ]

    if listed_experts:
        table = Table(
            title="Experts", show_header=True, header_style="bold", box=box.ROUNDED
        )
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("HEAD")
        table.add_column("Teams")

        for name in listed_experts:
            # Status
            if name in enabled:
                status_str = "[success]enabled[/success]"
            else:
                status_str = "[warning]disabled[/warning]"

            # HEAD
            expert_dir = _get_expert_dir(name)
            head_commit = _get_head_commit(expert_dir)
            head_display = (
                f"[commit]{head_commit[:12]}[/commit]"
                if head_commit
                else "[dim]none[/dim]"
            )

            # Teams this expert belongs to
            expert_teams = [
                t for t, td in teams.items() if name in td.get("experts", [])
            ]
            teams_display = ", ".join(expert_teams) if expert_teams else "[dim]-[/dim]"

            table.add_row(name, status_str, head_display, teams_display)

        console.print(table)

    # --- Teams table ---
    if teams:
        table = Table(
            title="Teams", show_header=True, header_style="bold", box=box.ROUNDED
        )
        table.add_column("Name", style="bold")
        table.add_column("Roster")
        table.add_column("Projects")

        for name, data in sorted(teams.items()):
            experts_list = data.get("experts", [])
            max_roster = data.get("max_roster", 8)
            roster_str = f"{', '.join(experts_list)} ({len(experts_list)}/{max_roster})"

            team_projects = [
                p for p, pd in projects.items() if name in pd.get("teams", [])
            ]
            projects_str = ", ".join(team_projects) if team_projects else "[dim]-[/dim]"

            table.add_row(name, roster_str, projects_str)

        console.print(table)

    # --- Projects table ---
    if projects:
        table = Table(
            title="Projects", show_header=True, header_style="bold", box=box.ROUNDED
        )
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("Teams")
        table.add_column("Objectives")

        for name, data in sorted(projects.items()):
            is_active = name == active_project
            status_str = (
                "[success]active[/success]" if is_active else "[dim]inactive[/dim]"
            )
            teams_str = ", ".join(data.get("teams", [])) or "[dim]-[/dim]"
            objectives = data.get("objectives", [])
            obj_str = "; ".join(objectives[:2]) if objectives else "[dim]-[/dim]"
            if len(objectives) > 2:
                obj_str += f" (+{len(objectives) - 2})"

            table.add_row(name, status_str, teams_str, obj_str)

        console.print(table)
