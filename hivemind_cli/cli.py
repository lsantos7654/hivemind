"""Hivemind CLI - Manage Claude Code expert agents."""

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
    _load_repos,
    _save_repos,
    _load_private_repos,
    _save_private_repos,
    _is_private_expert,
    _get_expert_dir,
    _expert_names,
    _get_head_commit,
    _count_versions,
    _ensure_repos_link,
    _ensure_external_docs_link,
    _link_agent,
    _unlink_agent,
    _link_expert,
    _unlink_expert,
    _clone_repo,
    _analyze_repo,
    _update_librarian,
    update_expert,
    enable_expert as core_enable_expert,
    disable_expert as core_disable_expert,
    UpdatePhase,
    ProgressInfo,
    HIVEMIND_ROOT,
    CLAUDE_DIR,
    CACHE_DIR,
    REPOS_DIR,
    REPOS_LINK,
    EXTERNAL_DOCS_DIR,
    EXTERNAL_DOCS_LINK,
    REPOS_JSON,
    CONFIG_JSON,
    AGENTS_DIR,
    EXPERTS_DIR,
    PRIVATE_EXPERTS_DIR,
    PRIVATE_REPOS_JSON,
    COMMANDS_DIR,
    CLAUDE_MD,
    SETTINGS_JSON,
)

THEME = Theme({
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
    "heading": "bold",
    "commit": "cyan",
})

app = typer.Typer(
    name="hivemind",
    help="Manage Claude Code expert agents.",
    no_args_is_help=True,
)
console = Console(theme=THEME)
install_traceback(show_locals=True, console=console)

# Paths imported from core module


def _complete_expert(incomplete: str) -> list[str]:
    """Shell completion for expert names."""
    return [n for n in _expert_names() if n.startswith(incomplete)]


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
def _link_agent_cli(name: str) -> bool:
    """Wrapper for _link_agent that adds console output."""
    result = _link_agent(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: agent symlink created")
    else:
        expert_dir = EXPERTS_DIR / name
        head_link = expert_dir / "HEAD"
        if not head_link.exists():
            console.print(f"  [warning]![/warning] {name}: no HEAD, skipping agent link")
        else:
            console.print(f"  [warning]![/warning] {name}: no agent.md in HEAD, skipping agent link")
    return result


def _unlink_agent_cli(name: str) -> None:
    """Wrapper for _unlink_agent that adds console output."""
    _unlink_agent(name)
    console.print(f"  [success]✓[/success] {name}: agent symlink removed")


def _link_expert_cli(name: str) -> bool:
    """Wrapper for _link_expert that adds console output."""
    result = _link_expert(name)
    if result:
        console.print(f"  [success]✓[/success] {name}: expert symlink created")
    else:
        console.print(f"  [warning]![/warning] {name}: expert directory not found")
    return result


def _clone_repo_cli(name: str, repos: dict) -> bool:
    """Wrapper for _clone_repo that adds console output."""
    if name not in repos:
        console.print(f"  [warning]![/warning] {name}: not in repos.json, skipping clone")
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
            console.print(f"  [success]✓[/success] {name}: cloned at commit {commit[:12]}")
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
    """Set up ~/.claude symlinks and enable agents."""
    console.print("[heading]Initializing hivemind...[/heading]\n")

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    _setup_symlink(AGENTS_DIR, CLAUDE_DIR / "agents", "agents/")
    _setup_symlink(COMMANDS_DIR, CLAUDE_DIR / "commands", "commands/")
    _setup_symlink(CLAUDE_MD, CLAUDE_DIR / "CLAUDE.md", "CLAUDE.md")
    _setup_symlink(SETTINGS_JSON, CLAUDE_DIR / "settings.json", "settings.json")
    _ensure_repos_link()
    console.print(f"  [success]✓[/success] repos/ → {REPOS_DIR}")
    _ensure_external_docs_link()
    console.print(f"  [success]✓[/success] external_docs/ → {EXTERNAL_DOCS_DIR}")

    # Create experts directory (no migration logic - use scripts/migrate_experts_symlinks.py)
    experts_dir = CLAUDE_DIR / "experts"
    experts_dir.mkdir(parents=True, exist_ok=True)

    config = _load_config()
    repos = _load_repos()

    console.print()
    for name in config["enabled"]:
        _clone_repo_cli(name, repos)
        _link_agent_cli(name)
        _link_expert_cli(name)

    _update_librarian_cli()

    # Remove stale agent symlinks
    for f in AGENTS_DIR.glob("expert-*.md"):
        expert_name = f.name.removeprefix("expert-").removesuffix(".md")
        if expert_name not in config["enabled"]:
            f.unlink()
            console.print(f"  [error]✗[/error] Removed stale: {f.name}")

    # Clean up stale expert symlinks
    if experts_dir.is_dir():
        for link in experts_dir.iterdir():
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
        console.print("No experts found. Use [heading]hivemind add <url>[/heading] to add one.")
        return

    # Separate into public and private
    public_expert_names = [name for name in experts if name not in private_experts]
    private_expert_names = [name for name in experts if name in private_experts]

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
            head_display = f"[commit]{head_commit[:12]}[/commit]" if head_commit else "[dim]none[/dim]"

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
    ref: typing.Optional[str] = typer.Option(None, "--ref", help="Tag, branch, or commit"),
    private: bool = typer.Option(False, "--private", help="Mark as private (won't be committed to git)"),
) -> None:
    """Register a new repo expert, clone, analyze, and create agent."""
    # Derive name from URL
    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    console.print(f"[heading]Adding expert: {name}[/heading]")
    console.print(f"  URL: {url}")
    if private:
        console.print(f"  [warning]Mode: PRIVATE (will not be committed to git)[/warning]")

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
                    "git", "clone", "--progress", "--branch", ref_name,
                    url, str(tmp_repo),
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
        console.print(f"  [success]✓[/success] Created staging experts/{name}/{commit[:12]}/")

        # Run AI analysis — writes into temp dirs
        with console.status(f"[heading]Running AI analysis of {name}...[/heading]", spinner="dots"):
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
            console.print(f"  [success]✓[/success] Expert installed to private-experts/{name}/")
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
            console.print("  [success]✓[/success] Added to private-repos.json")
        else:
            repos = _load_repos()
            repos[name] = {"remote": url, "commit": commit, "ref_name": ref_name}
            _save_repos(repos)
            console.print("  [success]✓[/success] Added to repos.json")

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

        # Create agent symlink
        _link_agent_cli(name)
        _link_expert(name)
        _update_librarian_cli()

        summary_lines = [
            f"[success]✓[/success] Expert [heading]{name}[/heading] is ready",
            f"[success]✓[/success] HEAD → [commit]{commit[:12]}[/commit]",
            f"[success]✓[/success] Agent: [heading]expert-{name}[/heading]",
        ]
        console.print()
        console.print(Panel(
            "\n".join(summary_lines),
            title="[bold success]Expert created successfully[/bold success]",
            border_style="green",
        ))

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.command()
def enable(name: str = typer.Argument(help="Expert name to enable", autocompletion=_complete_expert)) -> None:
    """Enable an expert (clones repo if needed, creates agent symlink)."""
    result = core_enable_expert(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    repos = _load_repos()
    _clone_repo_cli(name, repos)
    _link_agent_cli(name)

    if result["already_enabled"]:
        console.print(f"[success]✓[/success] {name}: already enabled, ensured repo and agent link")
    else:
        console.print(f"[success]✓[/success] Enabled: {name}")


@app.command()
def disable(name: str = typer.Argument(help="Expert name to disable", autocompletion=_complete_expert)) -> None:
    """Disable an expert (removes agent symlink)."""
    result = core_disable_expert(name)

    if not result["success"]:
        console.print(f"[error]Error: {result['error']}[/error]")
        raise typer.Exit(1)

    _unlink_agent_cli(name)

    if result["already_disabled"]:
        console.print(f"[warning]✓[/warning] {name}: already disabled, ensured agent link removed")
    else:
        console.print(f"[warning]✓[/warning] Disabled: {name}")



@app.command()
def update(
    name: typing.Optional[str] = typer.Argument(None, help="Expert name (or omit for all enabled)", autocompletion=_complete_expert),
) -> None:
    """Fetch latest commits and re-analyze with AI."""
    config = _load_config()
    repos = _load_repos()

    if name:
        names = [name]
        if name not in repos:
            console.print(f"[error]Error: '{name}' not found in repos.json[/error]")
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

        result = update_expert(expert_name, on_progress=on_progress)

        if not result["success"]:
            console.print(f"  [error]✗[/error] {result['error']}")
        elif result.get("already_up_to_date"):
            console.print(f"  [success]✓[/success] Already up to date ({result['new_commit'][:12]})")
        else:
            old_display = result["old_commit"][:12] if result["old_commit"] else "none"
            console.print(f"  [success]✓[/success] Updated from {old_display} to {result['new_commit'][:12]}")
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
        console.print("[error]Error: librarian.md not found. Run [bold]hivemind init[/bold] first.[/error]")
        raise typer.Exit(1)

    system_prompt = librarian.read_text()
    with console.status("Asking the librarian...", spinner="dots"):
        result = subprocess.run(
            ["claude", "-p", "--model", "sonnet"],
            input=f"{system_prompt}\n\n{question}",
            text=True,
            capture_output=True,
        )
    if result.stdout:
        console.print(result.stdout.rstrip())


@app.command()
def tui() -> None:
    """Launch interactive TUI for managing experts."""
    from hivemind_cli.tui import HivemindApp

    app_instance = HivemindApp()
    app_instance.run()


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    agent: str = typer.Argument(..., help="Agent name for output directory", autocompletion=_complete_expert),
    max_pages: int | None = typer.Option(None, "--max-pages", "-n", help="Maximum pages to crawl (default: no limit)"),
    raw_markdown: bool = typer.Option(False, "--raw-markdown", help="Force raw markdown fetching (.md endpoints only, no browser fallback)"),
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
            console.print("  [dim]No experts configured. Use [bold]hivemind add <url>[/bold] to add one.[/dim]")
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
            discovered_urls = asyncio.run(preview_sitemap(sitemap_url=url, max_pages=max_pages))
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
        console.print(f"[success]✓ Successfully crawled {result.successful_pages} pages[/success]")
        console.print(f"\n[info]Documentation saved to:[/info] {output_dir}")
        console.print(f"[info]Expert agents can now access these docs[/info]")
    else:
        console.print("[error]✗ No pages were successfully crawled[/error]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show a dashboard of hivemind status."""
    # Symlinks section
    symlink_lines: list[str] = []
    for display_name, target, link in [
        ("~/.claude/agents/", AGENTS_DIR, CLAUDE_DIR / "agents"),
        ("~/.claude/commands/", COMMANDS_DIR, CLAUDE_DIR / "commands"),
        ("~/.claude/CLAUDE.md", CLAUDE_MD, CLAUDE_DIR / "CLAUDE.md"),
        ("~/.claude/settings.json", SETTINGS_JSON, CLAUDE_DIR / "settings.json"),
        ("repos/", REPOS_DIR, REPOS_LINK),
        ("external_docs/", EXTERNAL_DOCS_DIR, EXTERNAL_DOCS_LINK),
    ]:
        if link.is_symlink():
            actual = link.resolve()
            if actual == target.resolve():
                symlink_lines.append(f"[success]✓[/success] {display_name} → {target}")
            else:
                symlink_lines.append(
                    f"[warning]![/warning] {display_name} → {link.readlink()} "
                    f"(expected {target})"
                )
        else:
            symlink_lines.append(
                f"[error]✗[/error] {display_name} is not a symlink "
                "(run: [heading]hivemind init[/heading])"
            )

    # Check experts directory (now a real directory with per-expert symlinks)
    claude_experts = CLAUDE_DIR / "experts"
    if claude_experts.is_dir() and not claude_experts.is_symlink():
        expert_count = sum(1 for _ in claude_experts.iterdir())
        symlink_lines.append(
            f"[success]✓[/success] ~/.claude/experts/ (directory with {expert_count} expert symlinks)"
        )
    elif claude_experts.is_symlink():
        symlink_lines.append(
            f"[warning]![/warning] ~/.claude/experts/ is a symlink (expected directory, run: hivemind init)"
        )
    else:
        symlink_lines.append(
            f"[error]✗[/error] ~/.claude/experts/ does not exist (run: hivemind init)"
        )

    console.print(
        Panel("\n".join(symlink_lines), title="Symlinks", border_style="blue")
    )

    # Repos section (combine public and private)
    repos = _load_repos()
    private_repos = _load_private_repos()
    config = _load_config()
    private_experts = set(config.get("private", []))

    all_repos = {**repos, **private_repos}
    if all_repos:
        repo_lines: list[str] = []
        for name in sorted(all_repos):
            is_private = name in private_experts
            repos_dict = private_repos if is_private else repos

            remote = repos_dict[name].get("remote", "")
            commit = repos_dict[name].get("commit", "")
            ref_name = repos_dict[name].get("ref_name", "")
            fetched = (
                "[success]fetched[/success]"
                if (REPOS_DIR / name).is_dir()
                else "[error]not fetched[/error]"
            )
            # Show HEAD commit from expert dir
            expert_dir = _get_expert_dir(name)
            head_commit = _get_head_commit(expert_dir)
            head_display = f"HEAD: {head_commit[:12]}" if head_commit else "HEAD: none"
            versions = _count_versions(expert_dir)

            ref_display = ""
            if ref_name:
                ref_display = f" @ {ref_name}"
            elif commit:
                ref_display = f" @ {commit[:12]}"

            name_display = f"{name} [private]" if is_private else name
            repo_lines.append(
                f"[heading]{name_display}[/heading]: {remote}{ref_display} [{fetched}] "
                f"({head_display}, {versions} version{'s' if versions != 1 else ''})"
            )

        console.print(Panel("\n".join(repo_lines), title="Repos", border_style="blue"))
    else:
        console.print(Panel("No repos configured.", title="Repos", border_style="dim"))

    # Experts section
    console.print()
    list_experts()
