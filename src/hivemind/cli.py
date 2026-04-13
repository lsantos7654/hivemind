"""Hivemind CLI - Manage expert agents for AI coding platforms."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from pathlib import Path
from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.traceback import install as install_traceback

from hivemind.analysis import expected_analysis_files
from hivemind.config import (
    AGENTS_DIR,
    COMMANDS_DIR,
    EXTERNAL_DOCS_DIR,
    HIVEMIND_ROOT,
    REPOS_DIR,
    TEAMS_DIR,
    count_versions,
    ensure_external_docs_link,
    ensure_repos_link,
    expert_names,
    get_active_provider,
    get_expert_dir,
    get_head_commit,
    is_private_expert,
    load_config,
    load_hivemind,
    load_private_repos,
    load_repos,
    load_teams,
    save_config,
)
from hivemind.deployment import (
    deploy_agent,
    deploy_expert,
    regenerate_hivemind_md,
    undeploy_agent,
    update_librarian,
)
from hivemind.experts import (
    delete_expert as core_delete_expert_fn,
)
from hivemind.experts import (
    disable_expert as core_disable_expert,
)
from hivemind.experts import (
    enable_expert as core_enable_expert,
)
from hivemind.experts import (
    switch_provider,
)
from hivemind.git import clone_repo
from hivemind.models import ProgressInfo, RepoEntry, UpdatePhase
from hivemind.redeploy import redeploy_all_agents
from hivemind.teams import (
    add_expert_to_team as core_add_expert_to_team,
)
from hivemind.teams import (
    add_experts_to_team as core_add_experts_to_team,
)
from hivemind.teams import (
    create_team as core_create_team,
)
from hivemind.teams import (
    delete_team as core_delete_team,
)
from hivemind.teams import (
    remove_expert_from_team as core_remove_expert_from_team,
)

THEME = Theme(
    {
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
        "heading": "bold",
        "commit": "cyan",
    },
)

app = typer.Typer(
    name="hivemind",
    help="Manage expert agents for AI coding platforms.",
    invoke_without_command=True,
)
console = Console(theme=THEME)
install_traceback(show_locals=True, console=console)

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class AnalysisProgress:
    """Rich Live display for analysis file progress checklist."""

    def __init__(self, target_console: Console, name: str, expected_files: list[str]) -> None:
        self._console = target_console
        self._name = name
        self._expected = expected_files
        self._found: set[str] = set()
        self._tick = 0
        self._running = False
        self._live = Live(self._render(), console=target_console, refresh_per_second=4)

    def _render(self) -> Group:
        spinner = _SPINNER_FRAMES[self._tick % len(_SPINNER_FRAMES)]
        lines: list[str] = []
        lines.append(f"  [heading]Analyzing {self._name}...[/heading]")
        hit_first_pending = False
        for f in self._expected:
            if f in self._found:
                lines.append(f"    [success]✓[/success] {f}")
            elif not hit_first_pending and self._running:
                hit_first_pending = True
                lines.append(f"    [info]{spinner}[/info] {f}")
            else:
                lines.append(f"    [dim]·[/dim] {f}")
        lines.append(
            f"    [dim]{len(self._found)}/{len(self._expected)} files generated[/dim]",
        )
        # Render markup strings through the console so custom theme is applied
        return Group(*(self._console.render_str(line) for line in lines))

    def start(self) -> None:
        """Start the live display."""
        self._running = True
        self._live.start()

    def update(self, files_found: list[str] | None) -> None:
        """Update progress with newly found files."""
        if files_found:
            self._found.update(files_found)
        self._tick += 1
        self._live.update(self._render())

    def finish(self) -> None:
        """Mark as complete and stop live display."""
        self._running = False
        self._live.update(self._render())
        self._live.stop()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Manage expert agents for AI coding platforms."""
    if ctx.invoked_subcommand is None:
        from hivemind.tui import HivemindApp

        app_instance = HivemindApp()
        app_instance.run()


# Paths imported from core module


def _complete_expert(incomplete: str) -> list[str]:
    """Shell completion for expert names."""
    return [n for n in expert_names() if n.startswith(incomplete)]


# --- Expert subcommands ---

expert_app = typer.Typer(
    name="expert",
    help="Manage experts.",
    no_args_is_help=True,
)
app.add_typer(expert_app, name="expert")


def _complete_provider(incomplete: str) -> list[str]:
    """Shell completion for provider names."""
    from hivemind.providers import PROVIDER_CLASSES

    return [n for n in PROVIDER_CLASSES if n.startswith(incomplete)]


def _setup_symlink(target: Path, link: Path, label: str) -> None:
    """Create or update a symlink, backing up existing directories."""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            console.print(f"  [success]✓[/success] {label} symlink already correct")
            return
        console.print(f"  [warning]![/warning] {label} symlink points to {link.readlink()}, updating...")
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        console.print(f"  [warning]![/warning] {label} is a real directory, backing up to {backup.name}/")
        link.rename(backup)
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    console.print(f"  [success]✓[/success] {label} → {target}")


# Wrapper functions to add console output to core module functions
def _deploy_agent_cli(name: str) -> bool:
    """Wrapper for _deploy_agent that adds console output."""
    result = deploy_agent(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: agent deployed")
    else:
        expert_dir = get_expert_dir(name)
        head_link = expert_dir / "HEAD"
        if not head_link.exists():
            console.print(f"  [warning]![/warning] {name}: no HEAD, skipping agent deploy")
        else:
            console.print(f"  [warning]![/warning] {name}: no agent.md in HEAD, skipping agent deploy")
    return result


def _undeploy_agent_cli(name: str) -> None:
    """Wrapper for _undeploy_agent that adds console output."""
    undeploy_agent(name)
    console.print(f"  [success]✓[/success] {name}: agent removed")


def _deploy_expert_cli(name: str) -> bool:
    """Wrapper for _deploy_expert that adds console output."""
    result = deploy_expert(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: expert deployed")
    else:
        console.print(f"  [warning]![/warning] {name}: expert directory not found")
    return result


def _clone_repo_cli(name: str, repos: dict[str, RepoEntry]) -> bool:
    """Wrapper for _clone_repo that adds console output."""
    if name not in repos:
        console.print(f"  [warning]![/warning] {name}: not in hivemind.json repos, skipping clone")
        return False

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # Already cloned

    repo = repos[name]
    commit = repo.commit
    ref_name = repo.ref_name

    if commit:
        console.print(f"  Cloning {name} at {commit[:12]}...")
    elif ref_name:
        console.print(f"  Cloning {name} at ref {ref_name}...")
    else:
        console.print(f"  Cloning {name} (default branch)...")

    result = asyncio.run(clone_repo(name, repos, silent=False))

    if result:
        if commit:
            console.print(f"  [success]✓[/success] {name}: cloned at commit {commit[:12]}")
        elif ref_name:
            console.print(f"  [success]✓[/success] {name}: cloned at ref {ref_name}")
        else:
            console.print(f"  [success]✓[/success] {name}: cloned (default branch)")

    return result


def _update_librarian_cli() -> None:
    """Wrapper for _update_librarian that adds console output."""
    update_librarian(config=load_config())
    console.print("  [success]✓[/success] Librarian updated")


# --- Commands ---


@app.command()
def init() -> None:
    """Set up provider directory symlinks and enable agents."""
    from hivemind.providers import PROVIDER_CLASSES

    config = load_config()
    if not config.active_provider:
        # Bootstrap: no provider set yet
        hivemind = load_hivemind()
        available = [name for name in hivemind.providers if name in PROVIDER_CLASSES]
        if not available:
            console.print("[error]No providers configured in hivemind.json[/error]")
            raise typer.Exit(1)
        if len(available) == 1:
            chosen = available[0]
            console.print(f"[info]Auto-selecting provider: {chosen}[/info]")
        else:
            console.print("[heading]Select a provider:[/heading]")
            for i, name in enumerate(available, 1):
                console.print(f"  {i}. {name}")
            choice = typer.prompt("Provider number", type=int)
            if choice < 1 or choice > len(available):
                console.print("[error]Invalid selection[/error]")
                raise typer.Exit(1)
            chosen = available[choice - 1]
        config.active_provider = chosen
        save_config(config)

    provider = get_active_provider()
    console.print(f"[heading]Initializing hivemind (provider: {provider.name})...[/heading]\n")

    # Generate HIVEMIND.md before symlink setup (it's the symlink target)
    regenerate_hivemind_md(config=config)
    console.print("  [success]✓[/success] HIVEMIND.md generated")

    # Use provider to initialize directory structure
    results = provider.init_dirs(
        agents_dir=AGENTS_DIR,
        commands_dir=COMMANDS_DIR,
        rules_source=HIVEMIND_ROOT / "HIVEMIND.md",
        teams_dir=TEAMS_DIR,
        permissions=provider.permissions,
    )
    for result in results:
        console.print(f"  [success]✓[/success] {result.label}: {result.status}")

    ensure_repos_link()
    console.print(f"  [success]✓[/success] repos/ → {REPOS_DIR}")
    ensure_external_docs_link()
    console.print(f"  [success]✓[/success] external_docs/ → {EXTERNAL_DOCS_DIR}")

    config = load_config()
    repos = load_repos()

    console.print()
    for name in config.enabled:
        _clone_repo_cli(name, repos)
        _deploy_agent_cli(name)
        _deploy_expert_cli(name)

    _update_librarian_cli()

    # Remove stale agent files
    for f in AGENTS_DIR.glob("expert-*.md"):
        expert_name = f.name.removeprefix("expert-").removesuffix(".md")
        if expert_name not in config.enabled:
            f.unlink()
            console.print(f"  [error]✗[/error] Removed stale: {f.name}")

    # Clean up stale expert symlinks in provider dir
    provider_experts = provider.home_dir / "experts"
    if provider_experts.is_dir():
        for link in provider_experts.iterdir():
            expert_name = link.name
            if expert_name not in config.enabled:
                if link.is_symlink():
                    link.unlink()
                elif link.is_dir():
                    import shutil

                    shutil.rmtree(link)
                console.print(f"  [error]✗[/error] Removed stale expert: {expert_name}")

    console.print("\n[bold success]Hivemind initialized![/bold success]")


@expert_app.command(name="list")
def list_experts() -> None:
    """Show all experts with their status."""
    config = load_config()
    repos = load_repos()
    private_repos = load_private_repos()
    experts = expert_names()

    if not experts:
        console.print("No experts found. Use [heading]hivemind add <url>[/heading] to add one.")
        return

    # Separate into public and private
    public_expert_names = [name for name in experts if not is_private_expert(name)]
    private_expert_names = [name for name in experts if is_private_expert(name)]

    def create_table_for_experts(expert_names: list[str], title: str) -> Table | None:
        """Create a table for a list of experts."""
        if not expert_names:
            return None

        table = Table(title=title, show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("HEAD")
        table.add_column("Versions")
        table.add_column("Remote")

        for name in expert_names:
            is_private = is_private_expert(name)

            # Status
            if name in config.enabled:
                status = "[success]enabled[/success]"
            elif name in config.disabled:
                status = "[warning]disabled[/warning]"
            else:
                status = "[error]unlisted[/error]"

            # HEAD commit
            expert_dir = get_expert_dir(name)
            head_commit = get_head_commit(expert_dir)
            head_display = f"[commit]{head_commit[:12]}[/commit]" if head_commit else "[dim]none[/dim]"

            # Version count
            version_count = count_versions(expert_dir)
            versions = str(version_count) if version_count > 0 else "[dim]0[/dim]"

            # Remote URL (check both repos)
            remote = ""
            repos_dict = private_repos if is_private else repos
            if name in repos_dict:
                url = repos_dict[name].remote
                ref = repos_dict[name].ref_name
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


@expert_app.command("show")
def show_expert(
    name: str = typer.Argument(..., help="Expert name", autocompletion=_complete_expert),
) -> None:
    """Show detailed information about an expert."""
    experts = expert_names()
    if name not in experts:
        console.print(f"[error]Error: expert '{name}' not found[/error]")
        raise typer.Exit(1)

    config = load_config()
    repos = load_repos()
    private_repos = load_private_repos()
    teams = load_teams()

    is_private = is_private_expert(name)

    # Status
    if name in config.enabled:
        status_str = "[success]enabled[/success]"
    elif name in config.disabled:
        status_str = "[warning]disabled[/warning]"
    else:
        status_str = "[error]unlisted[/error]"

    # Visibility
    visibility = "[warning]private[/warning]" if is_private else "[info]public[/info]"

    # HEAD commit and version count
    expert_dir = get_expert_dir(name)
    head_commit = get_head_commit(expert_dir)
    head_display = f"[commit]{head_commit}[/commit]" if head_commit else "[dim]none[/dim]"
    version_count = count_versions(expert_dir)

    # Remote URL
    repos_dict = private_repos if is_private else repos
    remote = ""
    ref_name = ""
    if name in repos_dict:
        remote = repos_dict[name].remote
        ref_name = repos_dict[name].ref_name

    # Teams containing this expert
    expert_teams = [t for t, td in teams.items() if name in td.experts]

    # Agent file status
    agent_file = AGENTS_DIR / f"expert-{name}.md"
    agent_status = "[success]deployed[/success]" if agent_file.exists() else "[dim]not deployed[/dim]"

    lines: list[str] = []
    lines.append(f"[heading]Expert: {name}[/heading]")
    lines.append(f"Status: {status_str}")
    lines.append(f"Visibility: {visibility}")
    lines.append(f"HEAD: {head_display}")
    lines.append(f"Versions: {version_count}")
    if remote:
        remote_display = escape(remote)
        if ref_name:
            remote_display += f" @ {escape(ref_name)}"
        lines.append(f"Remote: {remote_display}")
    lines.append(f"Agent: {agent_status}")

    if expert_teams:
        lines.append("\n[heading]Teams:[/heading]")
        lines.extend(f"  - {t}" for t in expert_teams)

    console.print(Panel("\n".join(lines), border_style="blue"))


@expert_app.command()
def add(
    url: str = typer.Argument(help="Git remote URL"),
    ref: str | None = typer.Option(None, "--ref", help="Tag, branch, or commit"),
    private: bool = typer.Option(False, "--private", help="Mark as private (won't be committed to git)"),
) -> None:
    """Register a new repo expert, clone, analyze, and create agent."""
    from hivemind.experts import add_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    console.print(f"[heading]Adding expert: {name}[/heading]")
    console.print(f"  URL: {escape(url)}")
    if private:
        console.print("  [warning]Mode: PRIVATE (will not be committed to git)[/warning]")

    expected = expected_analysis_files(is_update=False)
    progress: AnalysisProgress | None = None

    def on_progress(info: ProgressInfo) -> None:
        nonlocal progress
        if info.phase == UpdatePhase.ANALYZING:
            if progress is None:
                progress = AnalysisProgress(console, name, expected)
                progress.start()
            progress.update(info.files_found)
        else:
            if progress is not None:
                progress.finish()
                progress = None
            console.print(f"  [info]→[/info] {info.message}")

    result = asyncio.run(
        add_expert(
            name,
            url,
            ref_name=ref or "",
            is_private=private,
            on_progress=on_progress,
        )
    )

    if progress is not None:
        progress.finish()
        progress = None

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel(
            f"[success]✓[/success] Expert [heading]{name}[/heading] is ready\n"
            f"[success]✓[/success] Agent: [heading]expert-{name}[/heading]",
            title="[bold success]Expert created successfully[/bold success]",
            border_style="green",
        ),
    )


@expert_app.command()
def enable(
    name: str = typer.Argument(help="Expert name to enable", autocompletion=_complete_expert),
) -> None:
    """Enable an expert (clones repo if needed, creates agent symlink)."""
    config = load_config()
    result = asyncio.run(core_enable_expert(name, config=config))

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    if result.already_enabled:
        console.print(f"[success]✓[/success] {name}: already enabled, ensured repo and agent link")
    else:
        console.print(f"[success]✓[/success] Enabled: {name}")


@expert_app.command()
def disable(
    name: str = typer.Argument(help="Expert name to disable", autocompletion=_complete_expert),
) -> None:
    """Disable an expert (removes agent symlink)."""
    config = load_config()
    result = core_disable_expert(name, config=config)

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    _undeploy_agent_cli(name)

    if result.already_disabled:
        console.print(f"[warning]✓[/warning] {name}: already disabled, ensured agent link removed")
    else:
        console.print(f"[warning]✓[/warning] Disabled: {name}")


@expert_app.command()
def delete(
    name: str = typer.Argument(help="Expert name to delete", autocompletion=_complete_expert),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """Delete an expert entirely (removes all local data and agent files)."""
    if not force:
        confirm = typer.confirm(f"Delete expert '{name}'? This removes all local data, agent files, and cached repos.")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    config = load_config()
    result = core_delete_expert_fn(name, config=config)

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    console.print(f"[error]✗[/error] Deleted: {name}")


@expert_app.command()
def update(
    name: str = typer.Argument(
        ...,
        help="Expert name to update",
        autocompletion=_complete_expert,
    ),
    skip_analysis: bool = typer.Option(
        False,
        "--skip-analysis",
        help="Pull latest repo changes without re-running AI analysis",
    ),
) -> None:
    """Fetch latest commits and re-analyze with AI."""
    repos = load_repos()

    if name not in repos:
        console.print(f"[error]Error: '{name}' not found in hivemind.json repos[/error]")
        raise typer.Exit(1)

    console.print(f"\n[heading]Updating {name}...[/heading]")

    # Define progress callback for CLI with Rich Live file checklist
    expected = expected_analysis_files(is_update=True)
    progress: AnalysisProgress | None = None

    def on_progress(
        info: ProgressInfo,
        _expert_name: str = name,
        _expected: list[str] = expected,
    ) -> None:
        nonlocal progress
        if info.phase == UpdatePhase.ANALYZING:
            if progress is None:
                progress = AnalysisProgress(console, _expert_name, _expected)
                progress.start()
            progress.update(info.files_found)
        else:
            if progress is not None:
                progress.finish()
                progress = None
            if info.phase not in [UpdatePhase.CLONING, UpdatePhase.FETCHING]:
                console.print(f"  [success]✓[/success] {info.message}")

    from hivemind.experts import update_expert

    result = asyncio.run(update_expert(name, on_progress=on_progress, skip_analysis=skip_analysis))

    if progress is not None:
        progress.finish()
        progress = None

    if not result.success:
        console.print(f"  [error]✗[/error] {escape(str(result.error))}")
        raise typer.Exit(1)
    if result.already_up_to_date:
        console.print(f"  [success]✓[/success] Already up to date ({result.new_commit[:12]})")
    else:
        old_display = result.old_commit[:12] if result.old_commit else "none"
        console.print(f"  [success]✓[/success] Updated from {old_display} to {result.new_commit[:12]}")
        _update_librarian_cli()
        console.print("\n[bold success]Update complete.[/bold success]")


@expert_app.command()
def query(
    question: str = typer.Argument(help="Question to ask the librarian"),
) -> None:
    """Ask the librarian which expert(s) can help with a question."""
    librarian = AGENTS_DIR / "librarian.md"
    if not librarian.exists():
        console.print("[error]Error: librarian.md not found. Run [bold]hivemind init[/bold] first.[/error]")
        raise typer.Exit(1)

    provider = get_active_provider()
    system_prompt = librarian.read_text()
    cmd = provider.build_query_command()

    async def _run_query() -> str:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate(f"{system_prompt}\n\n{question}".encode())
        return stdout.decode() if stdout else ""

    with console.status("Asking the librarian...", spinner="dots"):
        output = asyncio.run(_run_query())
    if output:
        console.print(output.rstrip())


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
    from hivemind.providers import PROVIDER_CLASSES

    config = load_config()
    hivemind = load_hivemind()
    active = config.active_provider
    providers = hivemind.providers

    table = Table(title="Providers", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Engine")
    table.add_column("Home Directory")
    table.add_column("Model")

    for name in sorted(PROVIDER_CLASSES):
        from hivemind.models import ProviderConfig

        prov_config = providers.get(name, ProviderConfig())
        is_active = name == active

        if is_active:
            status_str = "[success]active[/success]"
        elif prov_config.engine:
            status_str = "[info]configured[/info]"
        else:
            status_str = "[dim]not configured[/dim]"

        engine = prov_config.engine or "[dim]not configured[/dim]"
        home_dir = prov_config.home_dir or "[dim]not configured[/dim]"
        model = prov_config.settings.model or "[dim]default[/dim]"

        table.add_row(name, status_str, engine, home_dir, model)

    console.print(table)


@provider_app.command(name="switch")
def provider_switch(
    name: str = typer.Argument(help="Provider name to switch to", autocompletion=_complete_provider),
) -> None:
    """Switch active provider (regenerates all agent files)."""
    config = load_config()
    result = switch_provider(name, config=config)

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    console.print(f"[success]Switched to provider: [heading]{name}[/heading][/success]")
    console.print("[info]Run [bold]hivemind redeploy[/bold] to regenerate agent files for the new provider.[/info]")


@provider_app.command(name="show")
def provider_show(
    name: str | None = typer.Argument(
        None,
        help="Provider name (default: active provider)",
        autocompletion=_complete_provider,
    ),
) -> None:
    """Show detailed configuration for a provider."""
    config = load_config()
    hivemind = load_hivemind()
    active = config.active_provider
    target = name or active
    providers = hivemind.providers

    if target not in providers:
        console.print(f"[error]Error: provider '{target}' not found in config[/error]")
        raise typer.Exit(1)

    prov_config = providers[target]
    is_active = target == active

    lines: list[str] = []
    lines.append(f"[heading]Provider: {target}[/heading]")
    lines.append(f"Active: {'[success]yes[/success]' if is_active else '[dim]no[/dim]'}")
    lines.append(f"Engine: {escape(prov_config.engine or 'not set')}")
    lines.append(f"Home directory: {escape(prov_config.home_dir or 'not set')}")

    settings_dict = prov_config.settings.model_dump(exclude_defaults=True)
    if settings_dict:
        lines.append("")
        lines.append("[heading]Settings:[/heading]")
        for key, value in sorted(settings_dict.items()):
            if isinstance(value, list):
                lines.append(f"  {escape(str(key))}: {', '.join(escape(str(v)) for v in value)}")
            elif isinstance(value, dict):
                lines.append(f"  {escape(str(key))}:")
                for k, v in sorted(value.items()):
                    lines.append(f"    {escape(str(k))}: {escape(str(v))}")
            else:
                lines.append(f"  {escape(str(key))}: {escape(str(value))}")

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
    return [n for n in load_teams() if n.startswith(incomplete)]


@team_app.command(name="list")
def team_list() -> None:
    """List all teams with their roster info."""
    teams = load_teams()

    if not teams:
        console.print("No teams configured. Use [heading]hivemind team create <name>[/heading] to create one.")
        return

    table = Table(title="Teams", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Roster")
    table.add_column("Size")

    for name, data in sorted(teams.items()):
        experts = data.experts
        roster_str = ", ".join(experts) if experts else "[dim]empty[/dim]"
        table.add_row(name, data.description, roster_str, str(len(experts)))

    console.print(table)


@team_app.command(name="create")
def team_create(
    name: str = typer.Argument(help="Team name"),
    description: str = typer.Option(..., "--description", "-d", help="Team description"),
    experts: str = typer.Option(..., "--experts", "-e", help="Comma-separated expert names"),
) -> None:
    """Create a new team with AI-generated lead agent."""
    expert_list = [e.strip() for e in experts.split(",") if e.strip()]

    console.print(f"[heading]Creating team: {name}[/heading]")
    console.print(f"  Description: {description}")
    console.print(f"  Experts: {', '.join(expert_list)}")

    config = load_config()
    with console.status("[heading]Generating team lead agent...[/heading]", spinner="dots"):
        result = asyncio.run(core_create_team(name, description, expert_list, config=config))

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    console.print(f"  [success]✓[/success] Team lead deployed: team-lead-{name}")
    console.print("  [success]✓[/success] Librarian updated")
    console.print(f"\n[bold success]Team '{name}' created![/bold success]")


@team_app.command(name="show")
def team_show(
    name: str = typer.Argument(help="Team name", autocompletion=_complete_team),
) -> None:
    """Show team details and roster."""
    teams = load_teams()
    if name not in teams:
        console.print(f"[error]Error: team '{name}' not found[/error]")
        raise typer.Exit(1)

    team = teams[name]
    lines: list[str] = []
    lines.append(f"[heading]Team: {escape(name)}[/heading]")
    lines.append(f"Description: {escape(team.description)}")
    experts = team.experts
    lines.append(f"\n[heading]Roster ({len(experts)}):[/heading]")
    lines.extend(f"  - {expert}" for expert in experts)

    # Show files
    team_dir = TEAMS_DIR / name
    lead_status = "[success]exists[/success]" if (team_dir / "lead.md").exists() else "[dim]missing[/dim]"
    lines.append("\n[heading]Files:[/heading]")
    lines.append(f"  - lead.md: {lead_status}")
    for expert in experts:
        notes_path = team_dir / f"expert-{expert}" / "notes.md"
        notes_status = "[success]exists[/success]" if notes_path.exists() else "[dim]missing[/dim]"
        lines.append(f"  - expert-{expert}/notes.md: {notes_status}")

    console.print(Panel("\n".join(lines), border_style="blue"))


@team_app.command(name="add-expert")
def team_add_expert(
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
    experts: list[str] = typer.Argument(help="Expert name(s)", autocompletion=_complete_expert),  # noqa: B008
) -> None:
    """Add one or more experts to a team's roster."""
    config = load_config()
    if len(experts) == 1:
        with console.status(
            f"[heading]Generating expert section for {experts[0]}...[/heading]",
            spinner="dots",
        ):
            result = asyncio.run(core_add_expert_to_team(team, experts[0], config=config))
        if not result.success:
            console.print(f"[error]Error: {escape(str(result.error))}[/error]")
            raise typer.Exit(1)
        console.print(f"[success]✓[/success] Added {experts[0]} to team {team}")
        return

    status = console.status("", spinner="dots")
    with status:

        def _on_progress(name: str) -> None:
            status.update(f"[heading]Generating expert section for {name}...[/heading]")

        result = asyncio.run(core_add_experts_to_team(team, experts, on_progress=_on_progress, config=config))

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    for name in result.added:
        console.print(f"[success]✓[/success] Added {name} to team {team}")
    for name in result.skipped:
        console.print(f"[dim]⊘ Skipped {name} (already on team)[/dim]")
    for entry in result.failed:
        console.print(f"[error]✗ Failed {entry.name}: {escape(entry.error)}[/error]")


@team_app.command(name="remove-expert")
def team_remove_expert(
    team: str = typer.Argument(help="Team name", autocompletion=_complete_team),
    expert: str = typer.Argument(help="Expert name", autocompletion=_complete_expert),
) -> None:
    """Remove an expert from a team's roster."""
    config = load_config()
    result = core_remove_expert_from_team(team, expert, config=config)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Removed {expert} from team {team}")


@team_app.command(name="delete")
def team_delete(
    name: str = typer.Argument(help="Team name", autocompletion=_complete_team),
) -> None:
    """Delete a team and its deployed agents."""
    if not typer.confirm(f"Delete team '{name}' and all its agents?"):
        console.print("[warning]Cancelled[/warning]")
        raise typer.Exit(0)

    config = load_config()
    result = core_delete_team(name, config=config)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Team '{name}' deleted")


# --- Redeploy command ---


@app.command()
def redeploy() -> None:
    """Regenerate all agent files for the active provider.

    Use after changing provider settings in hivemind.json
    (model, tools, temperature) or after switching providers.
    """
    provider = get_active_provider()
    console.print(f"[heading]Redeploying all agents (provider: {provider.name})...[/heading]\n")

    config = load_config()
    result = redeploy_all_agents(config=config)

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    deployed = [n for n in config.enabled if n not in result.failed]
    failed = result.failed
    experts_deployed = result.experts_deployed
    teams_deployed = result.teams_deployed

    for name in deployed:
        console.print(f"  [success]✓[/success] {name}: redeployed")
    for name in failed:
        console.print(f"  [warning]![/warning] {name}: failed to redeploy")
    for name in experts_deployed:
        console.print(f"  [success]✓[/success] {name}: expert dir deployed")
    for name in teams_deployed:
        console.print(f"  [success]✓[/success] {name}: redeployed")

    total = len(deployed) + len(teams_deployed)
    console.print(f"\n[bold success]Redeployed {total} agent(s), {len(experts_deployed)} expert dir(s).[/bold success]")


# --- Crawl service subcommands ---

crawl_app = typer.Typer(
    name="crawl",
    help="Manage the Firecrawl crawling service.",
    no_args_is_help=True,
)
app.add_typer(crawl_app, name="crawl")


@crawl_app.command(name="start")
def crawl_start() -> None:
    """Start the Firecrawl Docker service.

    Clones the Firecrawl repo if needed and runs docker compose up.
    Requires Docker to be installed and running.
    """
    from hivemind.crawler import is_firecrawl_running, start_firecrawl

    if is_firecrawl_running():
        console.print("[success]Firecrawl is already running.[/success]")
        return

    console.print("[info]Starting Firecrawl service...[/info]")
    try:
        start_firecrawl()
    except Exception as e:
        console.print(f"[error]Failed to start Firecrawl: {escape(str(e))}[/error]")
        raise typer.Exit(1) from None

    console.print("[success]Firecrawl service started at http://localhost:3002[/success]")


@crawl_app.command(name="stop")
def crawl_stop() -> None:
    """Stop the Firecrawl Docker service."""
    from hivemind.crawler import stop_firecrawl

    console.print("[info]Stopping Firecrawl service...[/info]")
    try:
        stop_firecrawl()
    except Exception as e:
        console.print(f"[error]Failed to stop Firecrawl: {escape(str(e))}[/error]")
        raise typer.Exit(1) from None

    console.print("[success]Firecrawl service stopped.[/success]")


@crawl_app.command(name="status")
def crawl_status_cmd() -> None:
    """Check if the Firecrawl service is running."""
    from hivemind.crawler import FIRECRAWL_URL, is_firecrawl_running

    if is_firecrawl_running():
        console.print(f"[success]Firecrawl is running at {FIRECRAWL_URL}[/success]")
    else:
        console.print(f"[warning]Firecrawl is not running at {FIRECRAWL_URL}[/warning]")
        console.print("[info]Start it with: hivemind crawl start[/info]")


# --- Expert crawl command ---


@expert_app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    agent: str = typer.Argument(..., help="Agent name for output directory", autocompletion=_complete_expert),
    max_pages: int | None = typer.Option(None, "--max-pages", "-n", help="Maximum pages to crawl (default: no limit)"),
    raw_markdown: bool = typer.Option(
        False,
        "--raw-markdown",
        help="Force raw markdown fetching (.md endpoints only, no Firecrawl)",
    ),
) -> None:
    """Crawl a website and save documentation for an expert agent.

    Crawls the specified URL and saves markdown files to
    ~/.cache/hivemind/external_docs/<agent>/ for use by expert agents.

    Uses Firecrawl (self-hosted) by default. Pass --raw-markdown for sites
    that serve source markdown at .md endpoints (e.g. rspress-based docs).

    The Firecrawl service must be running first: hivemind crawl start
    """
    # Validate that the agent exists
    expert_dir = get_expert_dir(agent)
    if not expert_dir.is_dir():
        console.print(f"[error]Error: Expert '{agent}' not found.[/error]")
        console.print("\n[info]Available experts:[/info]")
        experts = sorted(expert_names())
        if experts:
            for expert in experts:
                console.print(f"  - {expert}")
        else:
            console.print("  [dim]No experts configured. Use [bold]hivemind add <url>[/bold] to add one.[/dim]")
        raise typer.Exit(1)

    from hivemind.crawler import (
        FirecrawlNotRunningError,
        crawl_urls_raw_markdown,
        crawl_website,
        discover_urls,
    )

    output_dir = EXTERNAL_DOCS_DIR / agent

    console.print(f"[heading]Crawling Documentation for {agent}[/heading]\n")
    console.print(f"[info]URL:[/info] {escape(url)}")
    console.print(f"[info]Output:[/info] {escape(str(output_dir))}")
    console.print()

    if raw_markdown:
        # Raw markdown mode: discover URLs via Firecrawl /map, then fetch .md directly
        console.print("[info]Raw markdown mode — discovering URLs via Firecrawl...[/info]")
        try:
            discovered_urls = discover_urls(url=url, max_pages=max_pages)
        except FirecrawlNotRunningError as e:
            console.print(f"[error]{escape(str(e))}[/error]")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"[error]Failed to discover URLs: {escape(str(e))}[/error]")
            raise typer.Exit(1) from None

        if not discovered_urls:
            console.print("[error]No URLs discovered[/error]")
            raise typer.Exit(1)

        console.print(f"\n[success]Found {len(discovered_urls)} pages:[/success]\n")
        for i, discovered_url in enumerate(discovered_urls, 1):
            console.print(f"  {i}. {discovered_url}")
        console.print()

        if not typer.confirm(f"Fetch raw markdown for all {len(discovered_urls)} pages?", default=True):
            console.print("[warning]Crawl cancelled[/warning]")
            raise typer.Exit(0)

        console.print("\n[info]Fetching raw markdown...[/info]\n")

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
                "fetching",
                total=len(discovered_urls),
                current_url=url,
            )

            try:
                result = asyncio.run(
                    crawl_urls_raw_markdown(
                        urls=discovered_urls,
                        output_dir=str(output_dir),
                        on_page_callback=on_page,
                    ),
                )
            except Exception as e:
                console.print(f"\n[error]Crawl failed: {escape(str(e))}[/error]")
                raise typer.Exit(1) from None

    else:
        # Firecrawl mode: crawl the entire site
        console.print("[info]Crawling via Firecrawl...[/info]\n")

        try:
            result = crawl_website(
                url=url,
                max_pages=max_pages,
                output_dir=str(output_dir),
            )
        except FirecrawlNotRunningError as e:
            console.print(f"[error]{escape(str(e))}[/error]")
            raise typer.Exit(1) from None
        except Exception as e:
            console.print(f"\n[error]Crawl failed: {escape(str(e))}[/error]")
            raise typer.Exit(1) from None

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
        console.print(f"[success]Successfully crawled {result.successful_pages} pages[/success]")
        console.print(f"\n[info]Documentation saved to:[/info] {output_dir}")
        console.print("[info]Expert agents can now access these docs[/info]")
    else:
        console.print("[error]No pages were successfully crawled[/error]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show a dashboard of hivemind status."""
    provider = get_active_provider()
    config = load_config()

    # --- Overview panel ---
    overview_lines: list[str] = []
    overview_lines.append(f"Provider: [heading]{provider.name}[/heading]")

    enabled = config.enabled
    disabled = config.disabled
    teams = load_teams()
    overview_lines.append(
        f"Experts: [success]{len(enabled)} enabled[/success]"
        + (f", [warning]{len(disabled)} disabled[/warning]" if disabled else ""),
    )
    overview_lines.append(f"Teams: {len(teams)}")

    console.print(Panel("\n".join(overview_lines), title="Hivemind", border_style="blue"))

    # --- Experts table (enabled + disabled only, skip unlisted) ---
    listed_experts = [name for name in expert_names() if name in enabled or name in disabled]

    if listed_experts:
        table = Table(title="Experts", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("HEAD")
        table.add_column("Teams")

        for name in listed_experts:
            status_str = "[success]enabled[/success]" if name in enabled else "[warning]disabled[/warning]"

            # HEAD
            expert_dir = get_expert_dir(name)
            head_commit = get_head_commit(expert_dir)
            head_display = f"[commit]{head_commit[:12]}[/commit]" if head_commit else "[dim]none[/dim]"

            # Teams this expert belongs to
            expert_teams = [t for t, td in teams.items() if name in td.experts]
            teams_display = ", ".join(expert_teams) if expert_teams else "[dim]-[/dim]"

            table.add_row(name, status_str, head_display, teams_display)

        console.print(table)

    # --- Teams table ---
    if teams:
        table = Table(title="Teams", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="bold")
        table.add_column("Roster")

        for name, data in sorted(teams.items()):
            experts_list = data.experts
            roster_str = ", ".join(experts_list) if experts_list else "[dim]empty[/dim]"

            table.add_row(name, roster_str)

        console.print(table)


# --- Backward-compatible aliases for moved expert commands ---

_DEPRECATION = "[yellow]Note: 'hivemind {cmd}' is now 'hivemind expert {cmd}'[/yellow]"


@app.command("list", hidden=True)
def list_compat() -> None:
    """Deprecated: use 'hivemind expert list'."""
    console.print(_DEPRECATION.format(cmd="list"))
    list_experts()


@app.command("add", hidden=True)
def add_compat(
    url: str = typer.Argument(help="Git remote URL"),
    ref: str | None = typer.Option(None, "--ref", help="Tag, branch, or commit"),
    private: bool = typer.Option(False, "--private", help="Mark as private (won't be committed to git)"),
) -> None:
    """Deprecated: use 'hivemind expert add'."""
    console.print(_DEPRECATION.format(cmd="add"))
    add(url=url, ref=ref, private=private)


@app.command("enable", hidden=True)
def enable_compat(
    name: str = typer.Argument(help="Expert name to enable", autocompletion=_complete_expert),
) -> None:
    """Deprecated: use 'hivemind expert enable'."""
    console.print(_DEPRECATION.format(cmd="enable"))
    enable(name=name)


@app.command("disable", hidden=True)
def disable_compat(
    name: str = typer.Argument(help="Expert name to disable", autocompletion=_complete_expert),
) -> None:
    """Deprecated: use 'hivemind expert disable'."""
    console.print(_DEPRECATION.format(cmd="disable"))
    disable(name=name)


@app.command("delete", hidden=True)
def delete_compat(
    name: str = typer.Argument(help="Expert name to delete", autocompletion=_complete_expert),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """Deprecated: use 'hivemind expert delete'."""
    console.print(_DEPRECATION.format(cmd="delete"))
    delete(name=name, force=force)


@app.command("query", hidden=True)
def query_compat(
    question: str = typer.Argument(help="Question to ask the librarian"),
) -> None:
    """Deprecated: use 'hivemind expert query'."""
    console.print(_DEPRECATION.format(cmd="query"))
    query(question=question)


@app.command("crawl", hidden=True)
def crawl_compat(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    agent: str = typer.Argument(..., help="Agent name for output directory", autocompletion=_complete_expert),
    max_pages: int | None = typer.Option(None, "--max-pages", "-n", help="Maximum pages to crawl (default: no limit)"),
    raw_markdown: bool = typer.Option(
        False,
        "--raw-markdown",
        help="Force raw markdown fetching (.md endpoints only, no browser fallback)",
    ),
) -> None:
    """Deprecated: use 'hivemind expert crawl'."""
    console.print(_DEPRECATION.format(cmd="crawl"))
    crawl(url=url, agent=agent, max_pages=max_pages, raw_markdown=raw_markdown)
