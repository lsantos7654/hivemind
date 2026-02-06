"""Hivemind CLI - Manage Claude Code expert agents."""

from __future__ import annotations

import json
import os
import subprocess
import typing
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="hivemind",
    help="Manage Claude Code expert agents.",
    no_args_is_help=True,
)
console = Console()

# Paths
HIVEMIND_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = Path.home() / ".claude"
REPOS_DIR = CLAUDE_DIR / "repos"
REPOS_JSON = HIVEMIND_ROOT / "repos.json"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
AGENTS_DIR = HIVEMIND_ROOT / "agents"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
COMMANDS_DIR = HIVEMIND_ROOT / "commands"

# --- Helpers ---


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def _load_config() -> dict:
    default = {"enabled": [], "disabled": []}
    if not CONFIG_JSON.exists():
        return default
    data = _load_json(CONFIG_JSON)
    data.setdefault("enabled", [])
    data.setdefault("disabled", [])
    return data


def _save_config(config: dict) -> None:
    _save_json(CONFIG_JSON, config)


def _load_repos() -> dict:
    return _load_json(REPOS_JSON)


def _save_repos(repos: dict) -> None:
    _save_json(REPOS_JSON, repos)


def _expert_names() -> list[str]:
    """List all expert names from experts/ directory."""
    if not EXPERTS_DIR.exists():
        return []
    return sorted(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())


def _resolve_placeholder(text: str) -> str:
    """Replace {{HIVEMIND_ROOT}} with actual absolute path."""
    return text.replace("{{HIVEMIND_ROOT}}", str(HIVEMIND_ROOT))


def _run_sync() -> None:
    """Core sync logic, reused by multiple commands."""
    config = _load_config()
    enabled = config["enabled"]

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    generated: set[str] = set()

    for name in enabled:
        agent_src = EXPERTS_DIR / name / "agent.md"
        agent_dst = AGENTS_DIR / f"expert-{name}.md"

        if not agent_src.exists():
            console.print(f"  [yellow]![/yellow] {name}: no agent.md found, skipping")
            continue

        content = agent_src.read_text()
        resolved = _resolve_placeholder(content)
        agent_dst.write_text(resolved)

        console.print(f"  [green]\u2713[/green] {name} \u2192 agents/expert-{name}.md")
        generated.add(f"expert-{name}.md")

    # Remove stale agent files
    for f in AGENTS_DIR.glob("expert-*.md"):
        if f.name not in generated:
            f.unlink()
            console.print(f"  [red]\u2717[/red] Removed stale: {f.name}")

    console.print("[green]Sync complete.[/green]")


def _setup_symlink(target: Path, link: Path, label: str) -> None:
    """Create or update a symlink, backing up existing directories."""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            console.print(f"  [green]\u2713[/green] {label} symlink already correct")
            return
        console.print(
            f"  [yellow]![/yellow] {label} symlink points to {link.readlink()}, updating..."
        )
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        console.print(
            f"  [yellow]![/yellow] {label} is a real directory, backing up to {backup.name}/"
        )
        link.rename(backup)
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    console.print(f"  [green]\u2713[/green] {label} \u2192 {target}")


# --- Commands ---


@app.command()
def init() -> None:
    """Set up ~/.claude symlinks and sync agent files."""
    console.print("[bold]Initializing hivemind...[/bold]\n")

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    _setup_symlink(AGENTS_DIR, CLAUDE_DIR / "agents", "agents/")
    _setup_symlink(COMMANDS_DIR, CLAUDE_DIR / "commands", "commands/")

    console.print()
    _run_sync()
    console.print("\n[green bold]Hivemind initialized![/green bold]")


@app.command(name="list")
def list_experts() -> None:
    """Show all experts with their status."""
    config = _load_config()
    repos = _load_repos()
    experts = _expert_names()

    if not experts:
        console.print("No experts found. Use [bold]hivemind add <url>[/bold] to add one.")
        return

    table = Table(title="Experts", show_header=True, header_style="bold")
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Fetched")
    table.add_column("Agent")
    table.add_column("Remote")

    for name in experts:
        # Status
        if name in config["enabled"]:
            status = "[green]enabled[/green]"
        elif name in config["disabled"]:
            status = "[yellow]disabled[/yellow]"
        else:
            status = "[red]unlisted[/red]"

        # Fetched
        fetched = "[green]yes[/green]" if (REPOS_DIR / name).is_dir() else "[red]no[/red]"

        # Agent file generated
        agent = (
            "[green]yes[/green]"
            if (AGENTS_DIR / f"expert-{name}.md").is_file()
            else "[dim]no[/dim]"
        )

        # Remote URL (truncated)
        remote = ""
        if name in repos:
            url = repos[name].get("remote", "")
            ref = repos[name].get("ref_name", "")
            remote = url
            if ref:
                remote += f" @ {ref}"

        table.add_row(name, status, fetched, agent, remote)

    console.print(table)


@app.command()
def add(
    url: str = typer.Argument(help="Git remote URL"),
    ref: typing.Optional[str] = typer.Option(None, "--ref", help="Tag, branch, or commit"),
    name: typing.Optional[str] = typer.Option(None, "--name", help="Custom expert name"),
) -> None:
    """Add a repo to repos.json and create an expert skeleton."""
    # Derive name from URL
    if not name:
        name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    console.print(f"[bold]Adding expert: {name}[/bold]")
    console.print(f"  URL: {url}")

    # Resolve commit
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

    # Update repos.json
    repos = _load_repos()
    repos[name] = {"remote": url, "commit": commit, "ref_name": ref_name}
    _save_repos(repos)
    console.print("  [green]\u2713[/green] Added to repos.json")

    # Create expert skeleton
    expert_dir = EXPERTS_DIR / name
    expert_dir.mkdir(parents=True, exist_ok=True)

    agent_file = expert_dir / "agent.md"
    if not agent_file.exists():
        agent_file.write_text(
            f"""---
name: expert-{name}
description: Expert on {name} repository. Use proactively when questions involve {name}. Automatically invoked for questions about {name}.
tools: Read, Grep, Glob, Bash, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
model: sonnet
---

# Expert: {name}

## Knowledge Base

- Summary: {{{{HIVEMIND_ROOT}}}}/experts/{name}/summary.md
- Code Structure: {{{{HIVEMIND_ROOT}}}}/experts/{name}/code_structure.md
- Build System: {{{{HIVEMIND_ROOT}}}}/experts/{name}/build_system.md
- APIs: {{{{HIVEMIND_ROOT}}}}/experts/{name}/apis_and_interfaces.md

## Source Access

Repository source at `~/.claude/repos/{name}`.
If not present, run: `hivemind fetch {name}`

## Instructions

1. Read relevant knowledge docs first
2. Search source at ~/.claude/repos/{name} for details
3. Provide file paths and code references
4. Include working examples from actual repo patterns

## Expertise

[Generated from analysis - run /create-repo-expert to populate]

## Constraints

- Only answer questions related to this repository
- Defer to source code when knowledge docs are insufficient
- Note if information might be outdated relative to repo version
"""
        )
        console.print(f"  [green]\u2713[/green] Created {expert_dir}/agent.md (skeleton)")
    else:
        console.print("  [yellow]![/yellow] agent.md already exists, skipping")

    # Enable the expert
    config = _load_config()
    if name not in config["enabled"]:
        config["enabled"].append(name)
    if name in config["disabled"]:
        config["disabled"].remove(name)
    _save_config(config)
    console.print("  [green]\u2713[/green] Enabled in config.json")

    console.print()
    panel = Panel(
        f"[bold]hivemind fetch {name}[/bold]        Clone the repo\n"
        f"[bold]/create-repo-expert {url}[/bold]    Generate knowledge docs\n"
        f"[bold]hivemind sync[/bold]               Regenerate agent files",
        title="Next steps",
        border_style="blue",
    )
    console.print(panel)


@app.command()
def fetch(
    name: typing.Optional[str] = typer.Argument(None, help="Expert name to fetch"),
    all_repos: bool = typer.Option(False, "--all", help="Fetch all repos"),
    force: bool = typer.Option(False, "--force", help="Re-clone even if already fetched"),
) -> None:
    """Clone a repo to ~/.claude/repos/<name>."""
    if all_repos:
        console.print("[bold]Fetching all repos...[/bold]")
        repos = _load_repos()
        for repo_name in sorted(repos):
            _fetch_one(repo_name, force)
        return

    if not name:
        console.print("[red]Error: name is required (or use --all)[/red]")
        raise typer.Exit(1)

    _fetch_one(name, force)


def _fetch_one(name: str, force: bool) -> None:
    repos = _load_repos()
    if name not in repos:
        console.print(f"  [red]\u2717[/red] {name}: not found in repos.json")
        return

    repo = repos[name]
    remote = repo["remote"]
    commit = repo.get("commit", "")
    ref_name = repo.get("ref_name", "")

    repo_dir = REPOS_DIR / name
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    if repo_dir.is_dir() and not force:
        console.print(
            f"  [yellow]![/yellow] {name}: already fetched at {repo_dir} "
            "(use --force to re-clone)"
        )
        return

    if repo_dir.is_dir() and force:
        console.print(f"  [yellow]![/yellow] {name}: removing existing clone...")
        subprocess.run(["rm", "-rf", str(repo_dir)], check=True)

    with console.status(f"Cloning {name}...", spinner="dots"):
        if commit:
            subprocess.run(
                ["git", "clone", "--quiet", remote, str(repo_dir)],
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "--quiet", commit],
                cwd=str(repo_dir),
                check=True,
            )
            console.print(f"  [green]\u2713[/green] {name}: cloned at commit {commit[:12]}")
        elif ref_name:
            subprocess.run(
                [
                    "git", "clone", "--quiet", "--branch", ref_name,
                    "--depth", "1", remote, str(repo_dir),
                ],
                check=True,
            )
            console.print(f"  [green]\u2713[/green] {name}: cloned at ref {ref_name}")
        else:
            subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", remote, str(repo_dir)],
                check=True,
            )
            console.print(f"  [green]\u2713[/green] {name}: cloned (latest)")


@app.command()
def enable(name: str = typer.Argument(help="Expert name to enable")) -> None:
    """Enable an expert and regenerate agent files."""
    if not (EXPERTS_DIR / name).is_dir():
        console.print(f"[red]Error: expert '{name}' not found in experts/[/red]")
        raise typer.Exit(1)

    config = _load_config()
    if name not in config["enabled"]:
        config["enabled"].append(name)
    if name in config["disabled"]:
        config["disabled"].remove(name)
    _save_config(config)

    console.print(f"[green]\u2713[/green] Enabled: {name}")
    _run_sync()


@app.command()
def disable(name: str = typer.Argument(help="Expert name to disable")) -> None:
    """Disable an expert and regenerate agent files."""
    config = _load_config()
    if name in config["enabled"]:
        config["enabled"].remove(name)
    if name not in config["disabled"]:
        config["disabled"].append(name)
    _save_config(config)

    console.print(f"[yellow]\u2713[/yellow] Disabled: {name}")
    _run_sync()


@app.command()
def sync() -> None:
    """Regenerate agents/ from enabled experts."""
    console.print("[bold]Syncing agents...[/bold]")
    _run_sync()


@app.command()
def status() -> None:
    """Show a dashboard of hivemind status."""
    # Symlinks section
    symlink_lines: list[str] = []
    for label, target, link in [
        ("agents/", AGENTS_DIR, CLAUDE_DIR / "agents"),
        ("commands/", COMMANDS_DIR, CLAUDE_DIR / "commands"),
    ]:
        if link.is_symlink():
            actual = link.resolve()
            if actual == target.resolve():
                symlink_lines.append(f"[green]\u2713[/green] ~/.claude/{label} \u2192 {target}")
            else:
                symlink_lines.append(
                    f"[yellow]![/yellow] ~/.claude/{label} \u2192 {link.readlink()} "
                    f"(expected {target})"
                )
        else:
            symlink_lines.append(
                f"[red]\u2717[/red] ~/.claude/{label} is not a symlink "
                "(run: [bold]hivemind init[/bold])"
            )

    console.print(
        Panel("\n".join(symlink_lines), title="Symlinks", border_style="blue")
    )

    # Repos section
    repos = _load_repos()
    if repos:
        repo_lines: list[str] = []
        for name in sorted(repos):
            remote = repos[name].get("remote", "")
            commit = repos[name].get("commit", "")
            ref_name = repos[name].get("ref_name", "")
            fetched = (
                "[green]fetched[/green]"
                if (REPOS_DIR / name).is_dir()
                else "[red]not fetched[/red]"
            )
            ref_display = ""
            if ref_name:
                ref_display = f" @ {ref_name}"
            elif commit:
                ref_display = f" @ {commit[:12]}"
            repo_lines.append(f"[bold]{name}[/bold]: {remote}{ref_display} [{fetched}]")

        console.print(Panel("\n".join(repo_lines), title="Repos", border_style="blue"))
    else:
        console.print(Panel("No repos configured.", title="Repos", border_style="dim"))

    # Experts section
    console.print()
    list_experts()
