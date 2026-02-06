#!/usr/bin/env python3
"""Regenerate agent.md files with updated template instructions.

This is a maintenance script that regenerates ONLY agent.md files while
preserving all knowledge documentation (summary.md, code_structure.md, etc.).

Usage:
    python scripts/regenerate_agents.py [expert_name]     # Single expert
    python scripts/regenerate_agents.py --all             # All experts
    python scripts/regenerate_agents.py                   # All enabled experts
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Import centralized templates
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hivemind_cli.templates import regenerate_agent_prompt

# Paths
HIVEMIND_ROOT = Path(__file__).resolve().parent.parent
REPOS_DIR = Path.home() / ".cache" / "hivemind" / "repos"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
REPOS_JSON = HIVEMIND_ROOT / "repos.json"

console = Console()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_config() -> dict:
    return load_json(CONFIG_JSON)


def load_repos() -> dict:
    return load_json(REPOS_JSON)


def get_head_commit(expert_dir: Path) -> str | None:
    """Read the HEAD symlink to get the current commit hash."""
    head = expert_dir / "HEAD"
    if not head.is_symlink():
        return None
    import os
    return os.readlink(head)


def regenerate_agent_md(name: str, commit: str, repo_dir: Path, expert_dir: Path, background: bool = False):
    """Regenerate ONLY agent.md for an expert using existing knowledge docs.

    Args:
        name: Expert name
        commit: Commit hash
        repo_dir: Path to cloned repo
        expert_dir: Path to expert directory
        background: If True, returns Popen object; otherwise waits for completion

    Returns:
        subprocess.Popen if background=True, bool indicating success otherwise
    """
    commit_dir = expert_dir / commit

    # Use centralized template from templates.py
    prompt = regenerate_agent_prompt(name, commit, repo_dir, commit_dir)

    cmd = [
        "claude", "-p",
        "--verbose",
        "--allowedTools", "Read,Grep,Glob,Bash,Write",
        "--model", "sonnet",
        "--add-dir", str(repo_dir),
        "--add-dir", str(expert_dir),
        "--dangerously-skip-permissions",
    ]

    if background:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
        return proc
    else:
        proc = subprocess.run(
            cmd,
            input=prompt.encode(),
            capture_output=True,
        )
        return proc.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Regenerate agent.md files for all commit versions")
    parser.add_argument("name", nargs="?", help="Expert name to regenerate (or omit for enabled)")
    parser.add_argument("--all", action="store_true", help="Regenerate all experts")
    args = parser.parse_args()

    config = load_config()
    repos = load_repos()

    # Determine which experts to regenerate
    if args.name:
        names = [args.name]
        if not (EXPERTS_DIR / args.name).is_dir():
            console.print(f"[red]Error: expert '{args.name}' not found in experts/[/red]")
            sys.exit(1)
    elif args.all:
        names = sorted(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())
    else:
        names = config.get("enabled", [])

    if not names:
        console.print("No experts to regenerate.")
        return

    console.print(f"[bold cyan]Finding all agent.md files to regenerate...[/bold cyan]\n")

    # Find ALL commit versions for each expert
    to_process: list[tuple[str, str, Path, Path]] = []  # (name, commit, repo_dir, expert_dir)

    for name in names:
        expert_dir = EXPERTS_DIR / name

        if name not in repos:
            console.print(f"  [yellow]![/yellow] {name}: not in repos.json, skipping")
            continue

        repo_dir = REPOS_DIR / name
        if not repo_dir.is_dir():
            console.print(f"  [yellow]![/yellow] {name}: repo not cloned, skipping")
            continue

        # Find all commit directories (exclude HEAD symlink)
        commit_dirs = [
            d for d in expert_dir.iterdir()
            if d.is_dir() and not d.is_symlink() and d.name != "__pycache__"
        ]

        if not commit_dirs:
            console.print(f"  [yellow]![/yellow] {name}: no commit directories found, skipping")
            continue

        # Add all commit versions to the processing queue
        for commit_dir in commit_dirs:
            commit = commit_dir.name
            required_docs = ["summary.md", "code_structure.md", "build_system.md", "apis_and_interfaces.md"]
            missing = [doc for doc in required_docs if not (commit_dir / doc).exists()]

            if missing:
                console.print(f"  [yellow]![/yellow] {name}/{commit[:12]}: missing docs, skipping")
                continue

            to_process.append((name, commit, repo_dir, expert_dir))

    if not to_process:
        console.print("\n[yellow]No agent.md files to regenerate.[/yellow]")
        return

    console.print(f"[bold cyan]Found {len(to_process)} agent.md file(s) to regenerate[/bold cyan]\n")
    console.print(f"[bold cyan]Running AI analysis in parallel...[/bold cyan]\n")

    # Run all regenerations in parallel
    processes: list[tuple[str, str, subprocess.Popen]] = []
    statuses: dict[str, str] = {}

    def make_progress_table() -> Table:
        t = Table(box=box.ROUNDED, title="Agent.md Regeneration")
        t.add_column("Expert/Version", style="bold")
        t.add_column("Status")
        for key in sorted(statuses.keys()):
            t.add_row(key, statuses[key])
        return t

    # Start all processes
    for name, commit, repo_dir, expert_dir in to_process:
        key = f"{name}/{commit[:12]}"
        proc = regenerate_agent_md(name, commit, repo_dir, expert_dir, background=True)
        processes.append((name, commit, proc))
        statuses[key] = "[cyan]analyzing...[/cyan]"

    # Wait for all to complete with live progress
    success_count = 0
    fail_count = 0

    with Live(make_progress_table(), console=console, refresh_per_second=2) as live:
        while any(proc.poll() is None for _, _, proc in processes):
            for name, commit, proc in processes:
                key = f"{name}/{commit[:12]}"
                if proc.poll() is not None and statuses[key] == "[cyan]analyzing...[/cyan]":
                    expert_dir = EXPERTS_DIR / name
                    agent_md = expert_dir / commit / "agent.md"

                    if proc.returncode == 0 and agent_md.exists():
                        statuses[key] = "[green]✓ done[/green]"
                        success_count += 1
                    else:
                        statuses[key] = "[red]✗ failed[/red]"
                        fail_count += 1

            live.update(make_progress_table())
            time.sleep(0.5)

        # Final update for any stragglers
        for name, commit, proc in processes:
            key = f"{name}/{commit[:12]}"
            if statuses[key] == "[cyan]analyzing...[/cyan]":
                expert_dir = EXPERTS_DIR / name
                agent_md = expert_dir / commit / "agent.md"

                if proc.returncode == 0 and agent_md.exists():
                    statuses[key] = "[green]✓ done[/green]"
                    success_count += 1
                else:
                    statuses[key] = "[red]✗ failed[/red]"
                    fail_count += 1

        live.update(make_progress_table())

    console.print(f"\n[bold green]Regeneration complete: {success_count} succeeded, {fail_count} failed.[/bold green]")


if __name__ == "__main__":
    main()
