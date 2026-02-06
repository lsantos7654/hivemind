"""Hivemind CLI - Manage Claude Code expert agents."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
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
CACHE_DIR = Path.home() / ".cache" / "hivemind"
REPOS_DIR = CACHE_DIR / "repos"
REPOS_LINK = HIVEMIND_ROOT / "repos"
REPOS_JSON = HIVEMIND_ROOT / "repos.json"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
AGENTS_DIR = HIVEMIND_ROOT / "agents"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
COMMANDS_DIR = HIVEMIND_ROOT / "commands"
CLAUDE_MD = HIVEMIND_ROOT / "CLAUDE.md"

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


def _complete_expert(incomplete: str) -> list[str]:
    """Shell completion for expert names."""
    return [n for n in _expert_names() if n.startswith(incomplete)]


def _get_head_commit(expert_dir: Path) -> str | None:
    """Read the HEAD symlink to get the current commit hash."""
    head = expert_dir / "HEAD"
    if not head.is_symlink():
        return None
    return os.readlink(head)


def _count_versions(expert_dir: Path) -> int:
    """Count commit directories (excludes HEAD symlink)."""
    if not expert_dir.exists():
        return 0
    return sum(
        1
        for d in expert_dir.iterdir()
        if d.is_dir() and not d.is_symlink() and d.name != "__pycache__"
    )


def _ensure_repos_link() -> None:
    """Ensure HIVEMIND_ROOT/repos symlink points to the cache repos dir."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    if REPOS_LINK.is_symlink():
        if REPOS_LINK.resolve() == REPOS_DIR.resolve():
            return
        REPOS_LINK.unlink()
    elif REPOS_LINK.is_dir():
        # Move existing real directory contents to cache
        for item in REPOS_LINK.iterdir():
            dest = REPOS_DIR / item.name
            if not dest.exists():
                item.rename(dest)
        REPOS_LINK.rmdir()
    elif REPOS_LINK.exists():
        REPOS_LINK.unlink()
    REPOS_LINK.symlink_to(REPOS_DIR)


def _link_agent(name: str) -> bool:
    """Create agents/expert-<name>.md → ../experts/<name>/HEAD/agent.md. Returns False if HEAD/agent.md doesn't exist."""
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    expert_dir = EXPERTS_DIR / name
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        head_link = expert_dir / "HEAD"
        if not head_link.exists():
            console.print(f"  [yellow]![/yellow] {name}: no HEAD, skipping agent link")
        else:
            console.print(f"  [yellow]![/yellow] {name}: no agent.md in HEAD, skipping agent link")
        return False

    agent_link = AGENTS_DIR / f"expert-{name}.md"
    link_target = Path("..") / "experts" / name / "HEAD" / "agent.md"

    if agent_link.is_symlink():
        if os.readlink(agent_link) == str(link_target):
            return True  # Already correct
        agent_link.unlink()
    elif agent_link.exists():
        agent_link.unlink()

    agent_link.symlink_to(link_target)
    console.print(f"  [green]✓[/green] {name}: agent symlink created")
    return True


def _unlink_agent(name: str) -> None:
    """Remove agents/expert-<name>.md if it exists."""
    agent_link = AGENTS_DIR / f"expert-{name}.md"
    if agent_link.is_symlink() or agent_link.exists():
        agent_link.unlink()
        console.print(f"  [green]✓[/green] {name}: agent symlink removed")


def _clone_repo(name: str, repos: dict) -> bool:
    """Clone a repo to cache repos dir if not already present. Returns True if cloned."""
    if name not in repos:
        console.print(f"  [yellow]![/yellow] {name}: not in repos.json, skipping clone")
        return False

    _ensure_repos_link()

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # Already cloned
    repo = repos[name]
    remote = repo["remote"]
    commit = repo.get("commit", "")
    ref_name = repo.get("ref_name", "")

    if commit:
        console.print(f"  Cloning {name} at {commit[:12]}...")
        subprocess.run(
            ["git", "clone", "--progress", remote, str(repo_dir)],
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "--quiet", commit],
            cwd=str(repo_dir),
            check=True,
        )
        console.print(f"  [green]✓[/green] {name}: cloned at commit {commit[:12]}")
    elif ref_name:
        console.print(f"  Cloning {name} at ref {ref_name}...")
        subprocess.run(
            [
                "git", "clone", "--progress", "--branch", ref_name,
                "--depth", "1", remote, str(repo_dir),
            ],
            check=True,
        )
        console.print(f"  [green]✓[/green] {name}: cloned at ref {ref_name}")
    else:
        console.print(f"  Cloning {name} (default branch)...")
        subprocess.run(
            ["git", "clone", "--progress", "--depth", "1", remote, str(repo_dir)],
            check=True,
        )
        console.print(f"  [green]✓[/green] {name}: cloned (default branch)")

    return True



def _analyze_repo(
    name: str,
    commit: str,
    repo_dir: Path,
    expert_dir: Path,
    *,
    is_update: bool = False,
    background: bool = False,
) -> subprocess.Popen | bool:
    """Run AI analysis on a repo via `claude -p`.

    For create (is_update=False): generates 5 files (4 knowledge + agent.md).
    For update (is_update=True): regenerates 4 knowledge files, preserves agent.md.

    If background=True, returns the Popen object immediately.
    Otherwise, waits for completion and returns True on success.
    """
    commit_dir = expert_dir / commit

    if is_update:
        prompt = f"""\
You are analyzing the repository at {repo_dir} to refresh knowledge documentation for the "{name}" expert.

The commit is {commit}. Write updated documentation files into {commit_dir}/.

Regenerate these 4 files (overwrite completely):

1. **{commit_dir}/summary.md** (500-800 words)
   - Repository purpose and goals
   - Key features and capabilities
   - Primary use cases and target audience
   - High-level architecture overview
   - Related projects and dependencies

2. **{commit_dir}/code_structure.md** (1000-1500 words)
   - Complete annotated directory tree
   - Module and package organization
   - Main source directories and their purposes
   - Key files and their roles
   - Code organization patterns

3. **{commit_dir}/build_system.md** (800-1200 words)
   - Build system type and configuration files
   - External dependencies and management
   - Build targets and commands
   - How to build, test, and deploy

4. **{commit_dir}/apis_and_interfaces.md** (1000-1500 words)
   - Public APIs and entry points
   - Key classes, functions, and macros
   - Usage examples with code snippets
   - Integration patterns and workflows
   - Configuration options and extension points

**IMPORTANT:** Do NOT modify {commit_dir}/agent.md — it contains custom agent configuration that must be preserved.

Analyze the repository thoroughly using Read, Grep, and Glob tools before writing. Explore the directory structure, key source files, build files, and documentation. Write comprehensive, accurate documentation based on actual code inspection."""
    else:
        prompt = f"""\
You are performing a deep analysis of the repository at {repo_dir} to create expert knowledge documentation for the "{name}" expert.

The commit is {commit}. Write all files into {commit_dir}/.

Generate these 5 files:

1. **{commit_dir}/summary.md** (500-800 words)
   - Repository purpose and goals
   - Key features and capabilities
   - Primary use cases and target audience
   - High-level architecture overview
   - Related projects and dependencies

2. **{commit_dir}/code_structure.md** (1000-1500 words)
   - Complete annotated directory tree
   - Module and package organization
   - Main source directories and their purposes
   - Key files and their roles
   - Code organization patterns

3. **{commit_dir}/build_system.md** (800-1200 words)
   - Build system type and configuration files
   - External dependencies and management
   - Build targets and commands
   - How to build, test, and deploy

4. **{commit_dir}/apis_and_interfaces.md** (1000-1500 words)
   - Public APIs and entry points
   - Key classes, functions, and macros
   - Usage examples with code snippets
   - Integration patterns and workflows
   - Configuration options and extension points

5. **{commit_dir}/agent.md** — Expert subagent definition. Use this exact template, filling in the bracketed sections from your analysis:

```markdown
---
name: expert-{name}
description: Expert on {name} repository. Use proactively when questions involve [topics from analysis]. Automatically invoked for questions about [scenarios from analysis].
tools: Read, Grep, Glob, Bash, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
model: sonnet
---

# Expert: [Full Repository Name]

## Knowledge Base

- Summary: ~/.claude/experts/{name}/HEAD/summary.md
- Code Structure: ~/.claude/experts/{name}/HEAD/code_structure.md
- Build System: ~/.claude/experts/{name}/HEAD/build_system.md
- APIs: ~/.claude/experts/{name}/HEAD/apis_and_interfaces.md

## Source Access

Repository source at `~/.cache/hivemind/repos/{name}`.
If not present, run: `hivemind enable {name}`

## Instructions

1. Read relevant knowledge docs first
2. Search source at ~/.cache/hivemind/repos/{name} for details
3. Provide file paths and code references
4. Include working examples from actual repo patterns

## Expertise

[Generate detailed list of expertise areas from your analysis]

## Constraints

- Only answer questions related to this repository
- Defer to source code when knowledge docs are insufficient
- Note if information might be outdated relative to repo version
```

Replace the bracketed sections with specific content from your analysis. The description field in the YAML frontmatter should list concrete topics and scenarios.

Analyze the repository thoroughly using Read, Grep, and Glob tools before writing. Explore the directory structure, key source files, build files, and documentation. Write comprehensive, accurate documentation based on actual code inspection."""

    cmd = [
        "claude", "-p",
        "--verbose",
        "--allowedTools", "Read,Grep,Glob,Bash,Write",
        "--model", "sonnet",
        "--add-dir", str(repo_dir),
        "--add-dir", str(expert_dir),
        "--dangerously-skip-permissions",
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        # stdout/stderr inherit from parent → streams to terminal
    )

    if background:
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
        return proc

    proc.communicate(input=prompt.encode())
    return proc.returncode == 0


def _setup_symlink(target: Path, link: Path, label: str) -> None:
    """Create or update a symlink, backing up existing directories."""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            console.print(f"  [green]✓[/green] {label} symlink already correct")
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
    console.print(f"  [green]✓[/green] {label} → {target}")


def _update_librarian() -> None:
    """Regenerate agents/librarian.md from all experts with valid HEAD/agent.md."""
    entries: list[str] = []

    for expert_dir in sorted(EXPERTS_DIR.iterdir()):
        if not expert_dir.is_dir():
            continue
        name = expert_dir.name
        agent_md = expert_dir / "HEAD" / "agent.md"
        if not agent_md.exists():
            continue

        # Parse description from frontmatter
        description = ""
        try:
            text = agent_md.read_text()
            parts = text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].splitlines():
                    if line.startswith("description:"):
                        description = line[len("description:"):].strip()
                        break
        except OSError:
            pass

        # Read first ~5 lines of summary.md
        summary_lines = ""
        summary_md = expert_dir / "HEAD" / "summary.md"
        try:
            lines = summary_md.read_text().splitlines()
            summary_lines = "\n".join(lines[:5])
        except OSError:
            pass

        entry = f"### expert-{name}\n{description}\n\n{summary_lines}"
        entries.append(entry)

    if not entries:
        return

    catalog = "\n\n---\n\n".join(entries)

    content = f"""\
---
name: librarian
description: "Hivemind librarian — knows every expert agent and their capabilities. Ask the librarian to find the right expert for a question before delegating to specialists."
tools: Read, Grep, Glob
model: sonnet
---

# Hivemind Librarian

You are the hivemind librarian. You know every registered expert and what they specialize in. When asked a question, identify which expert(s) are best suited and recommend them by name.

## Expert Catalog

{catalog}

## Instructions

1. Identify the most relevant expert(s) from the catalog
2. Respond with expert name(s) and why they're the right fit
3. If multiple experts are relevant, rank by relevance
4. If no expert matches, say so clearly
"""

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    (AGENTS_DIR / "librarian.md").write_text(content)
    console.print("  [green]✓[/green] Librarian updated")


# --- Commands ---


@app.command()
def init() -> None:
    """Set up ~/.claude symlinks and enable agents."""
    console.print("[bold]Initializing hivemind...[/bold]\n")

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    _setup_symlink(AGENTS_DIR, CLAUDE_DIR / "agents", "agents/")
    _setup_symlink(COMMANDS_DIR, CLAUDE_DIR / "commands", "commands/")
    _setup_symlink(EXPERTS_DIR, CLAUDE_DIR / "experts", "experts/")
    _setup_symlink(CLAUDE_MD, CLAUDE_DIR / "CLAUDE.md", "CLAUDE.md")
    _ensure_repos_link()
    console.print(f"  [green]✓[/green] repos/ → {REPOS_DIR}")

    config = _load_config()
    repos = _load_repos()

    console.print()
    for name in config["enabled"]:
        _clone_repo(name, repos)
        _link_agent(name)

    _update_librarian()

    # Remove stale agent symlinks
    for f in AGENTS_DIR.glob("expert-*.md"):
        expert_name = f.name.removeprefix("expert-").removesuffix(".md")
        if expert_name not in config["enabled"]:
            f.unlink()
            console.print(f"  [red]✗[/red] Removed stale: {f.name}")

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
    table.add_column("HEAD")
    table.add_column("Versions")
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

        # HEAD commit
        expert_dir = EXPERTS_DIR / name
        head_commit = _get_head_commit(expert_dir)
        head_display = f"[cyan]{head_commit[:12]}[/cyan]" if head_commit else "[dim]none[/dim]"

        # Version count
        version_count = _count_versions(expert_dir)
        versions = str(version_count) if version_count > 0 else "[dim]0[/dim]"

        # Agent file generated
        agent = (
            "[green]yes[/green]"
            if (AGENTS_DIR / f"expert-{name}.md").is_file()
            else "[dim]no[/dim]"
        )

        # Remote URL
        remote = ""
        if name in repos:
            url = repos[name].get("remote", "")
            ref = repos[name].get("ref_name", "")
            remote = url
            if ref:
                remote += f" @ {ref}"

        table.add_row(name, status, head_display, versions, agent, remote)

    console.print(table)


@app.command()
def add(
    url: str = typer.Argument(help="Git remote URL"),
    ref: typing.Optional[str] = typer.Option(None, "--ref", help="Tag, branch, or commit"),
) -> None:
    """Register a new repo expert, clone, analyze, and create agent."""
    # Derive name from URL
    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    console.print(f"[bold]Adding expert: {name}[/bold]")
    console.print(f"  URL: {url}")

    # Error out early if expert already exists
    expert_dir = EXPERTS_DIR / name
    if expert_dir.is_dir():
        console.print(
            f"[red]Error: expert '{name}' already exists. "
            f"Use [bold]hivemind update {name}[/bold] instead.[/red]"
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
                    "--depth", "1", url, str(tmp_repo),
                ],
                check=True,
            )
        else:
            subprocess.run(
                ["git", "clone", "--progress", "--depth", "1", url, str(tmp_repo)],
                check=True,
            )
        console.print(f"  [green]✓[/green] Cloned to staging area")

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
            console.print(f"  [green]✓[/green] Resolved commit: {commit[:12]}")

        # Create versioned directory in temp expert dir
        tmp_commit_dir = tmp_expert / commit
        tmp_commit_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]✓[/green] Created staging experts/{name}/{commit[:12]}/")

        # Run AI analysis — writes into temp dirs
        console.print(f"\n[bold]Running AI analysis of {name}...[/bold]")
        success = _analyze_repo(name, commit, tmp_repo, tmp_expert)
        if not success:
            console.print(f"[red]Error: AI analysis failed for {name}[/red]")
            raise typer.Exit(1)
        console.print(f"  [green]✓[/green] AI analysis complete")

        # --- Success: move everything to final locations ---

        # Move repo to final location
        _ensure_repos_link()
        final_repo = REPOS_DIR / name
        if final_repo.exists():
            shutil.rmtree(final_repo)
        shutil.move(str(tmp_repo), str(final_repo))
        console.print(f"  [green]✓[/green] Repo installed to repos/{name}/")

        # Move expert dir to final location
        EXPERTS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_expert), str(expert_dir))
        console.print(f"  [green]✓[/green] Expert installed to experts/{name}/")

        # Create HEAD symlink
        head_link = expert_dir / "HEAD"
        head_link.symlink_to(commit)
        console.print(f"  [green]✓[/green] HEAD → {commit[:12]}")

        # Update repos.json
        repos = _load_repos()
        repos[name] = {"remote": url, "commit": commit, "ref_name": ref_name}
        _save_repos(repos)
        console.print("  [green]✓[/green] Added to repos.json")

        # Enable in config
        config = _load_config()
        if name not in config["enabled"]:
            config["enabled"].append(name)
        if name in config["disabled"]:
            config["disabled"].remove(name)
        _save_config(config)
        console.print("  [green]✓[/green] Enabled in config.json")

        # Create agent symlink
        _link_agent(name)
        _update_librarian()

        console.print(f"\n[green bold]Expert '{name}' created successfully![/green bold]")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.command()
def enable(name: str = typer.Argument(help="Expert name to enable", autocompletion=_complete_expert)) -> None:
    """Enable an expert (clones repo if needed, creates agent symlink)."""
    if not (EXPERTS_DIR / name).is_dir():
        console.print(f"[red]Error: expert '{name}' not found in experts/[/red]")
        raise typer.Exit(1)

    config = _load_config()
    already_enabled = name in config["enabled"]

    if not already_enabled:
        config["enabled"].append(name)
        if name in config["disabled"]:
            config["disabled"].remove(name)
        _save_config(config)

    repos = _load_repos()
    _clone_repo(name, repos)
    _link_agent(name)

    if already_enabled:
        console.print(f"[green]✓[/green] {name}: already enabled, ensured repo and agent link")
    else:
        console.print(f"[green]✓[/green] Enabled: {name}")


@app.command()
def disable(name: str = typer.Argument(help="Expert name to disable", autocompletion=_complete_expert)) -> None:
    """Disable an expert (removes agent symlink)."""
    if not (EXPERTS_DIR / name).is_dir():
        console.print(f"[red]Error: expert '{name}' not found in experts/[/red]")
        raise typer.Exit(1)

    config = _load_config()
    already_disabled = name not in config["enabled"] and name in config["disabled"]

    if not already_disabled:
        if name in config["enabled"]:
            config["enabled"].remove(name)
        if name not in config["disabled"]:
            config["disabled"].append(name)
        _save_config(config)

    _unlink_agent(name)

    if already_disabled:
        console.print(f"[yellow]✓[/yellow] {name}: already disabled, ensured agent link removed")
    else:
        console.print(f"[yellow]✓[/yellow] Disabled: {name}")



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
            console.print(f"[red]Error: '{name}' not found in repos.json[/red]")
            raise typer.Exit(1)
    else:
        names = config["enabled"]

    if not names:
        console.print("No experts to update.")
        return

    # Phase 1: Fetch and stage into temp dirs — no visible state changes
    # Each entry: (expert_name, new_commit, old_commit, tmpdir)
    staged: list[tuple[str, str, str | None, str]] = []

    for expert_name in names:
        console.print(f"\n[bold]Updating {expert_name}...[/bold]")

        if expert_name not in repos:
            console.print(f"  [yellow]![/yellow] {expert_name}: not in repos.json, skipping")
            continue

        repo_dir = REPOS_DIR / expert_name

        # Ensure repo is cloned
        if not _clone_repo(expert_name, repos):
            continue

        # Fetch latest from remote
        with console.status(f"Fetching {expert_name}...", spinner="dots"):
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=str(repo_dir),
                capture_output=True,
                check=True,
            )

        # Get latest commit hash
        # Try origin/HEAD first, fall back to origin/main, then origin/master
        new_commit = None
        for ref in ["origin/HEAD", "origin/main", "origin/master"]:
            result = subprocess.run(
                ["git", "rev-parse", ref],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                new_commit = result.stdout.strip()
                break

        if not new_commit:
            console.print(f"  [red]✗[/red] {expert_name}: could not resolve latest commit")
            continue

        # Check if already up to date
        expert_dir = EXPERTS_DIR / expert_name
        current_head = _get_head_commit(expert_dir)
        if current_head == new_commit:
            console.print(f"  [green]✓[/green] {expert_name}: already up to date ({new_commit[:12]})")
            continue

        # Stage work in temp dir
        tmpdir = tempfile.mkdtemp(prefix=f"hivemind-update-{expert_name}-")
        tmp_expert = Path(tmpdir) / "expert"
        tmp_expert.mkdir()
        tmp_commit_dir = tmp_expert / new_commit
        tmp_commit_dir.mkdir()

        # Copy files from previous HEAD version as baseline
        if current_head:
            old_dir = expert_dir / current_head
            if old_dir.is_dir():
                for f in old_dir.iterdir():
                    if f.is_file():
                        shutil.copy2(f, tmp_commit_dir / f.name)
                console.print(f"  [green]✓[/green] Copied files from {current_head[:12]} as baseline")

        # Checkout new commit in repo (needed for analysis)
        subprocess.run(
            ["git", "checkout", "--quiet", new_commit],
            cwd=str(repo_dir),
            check=True,
        )
        console.print(f"  [green]✓[/green] Staged for analysis: {new_commit[:12]}")

        staged.append((expert_name, new_commit, current_head, tmpdir))

    if not staged:
        console.print("\n[green]All experts are up to date.[/green]")
        return

    # Phase 2: Parallel AI analysis — all writes go to temp dirs
    console.print(f"\n[bold]Running AI analysis for {len(staged)} updated expert(s)...[/bold]")

    try:
        processes: list[tuple[str, subprocess.Popen]] = []
        for expert_name, new_commit, _old_commit, tmpdir in staged:
            tmp_expert = Path(tmpdir) / "expert"
            repo_dir = REPOS_DIR / expert_name
            proc = _analyze_repo(
                expert_name, new_commit, repo_dir, tmp_expert,
                is_update=True, background=True,
            )
            processes.append((expert_name, proc))
            console.print(f"  [cyan]▶[/cyan] Started analysis: {expert_name}")

        # Wait for all to complete
        for (expert_name, proc), (_, new_commit, old_commit, tmpdir) in zip(processes, staged):
            proc.wait()

            if proc.returncode == 0:
                # Phase 3: Commit — move staged work to final locations
                tmp_commit_dir = Path(tmpdir) / "expert" / new_commit
                expert_dir = EXPERTS_DIR / expert_name

                shutil.move(str(tmp_commit_dir), str(expert_dir / new_commit))

                head_link = expert_dir / "HEAD"
                if head_link.is_symlink():
                    head_link.unlink()
                head_link.symlink_to(new_commit)

                repos[expert_name]["commit"] = new_commit

                console.print(f"  [green]✓[/green] {expert_name}: analysis complete, HEAD → {new_commit[:12]}")
            else:
                # Revert repo checkout to old commit
                if old_commit:
                    subprocess.run(
                        ["git", "checkout", "--quiet", old_commit],
                        cwd=str(REPOS_DIR / expert_name),
                        capture_output=True,
                    )
                console.print(f"  [red]✗[/red] {expert_name}: analysis failed (exit {proc.returncode}), reverted")

        # Batch-save repos.json once after all updates
        _save_repos(repos)
        _update_librarian()

        console.print(f"\n[green bold]Update complete.[/green bold]")

    finally:
        for _, _, _, tmpdir in staged:
            shutil.rmtree(tmpdir, ignore_errors=True)


@app.command()
def query(
    question: str = typer.Argument(help="Question to ask the librarian"),
) -> None:
    """Ask the librarian which expert(s) can help with a question."""
    librarian = AGENTS_DIR / "librarian.md"
    if not librarian.exists():
        console.print("[red]Error: librarian.md not found. Run [bold]hivemind init[/bold] first.[/red]")
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
def status() -> None:
    """Show a dashboard of hivemind status."""
    # Symlinks section
    symlink_lines: list[str] = []
    for display_name, target, link in [
        ("~/.claude/agents/", AGENTS_DIR, CLAUDE_DIR / "agents"),
        ("~/.claude/commands/", COMMANDS_DIR, CLAUDE_DIR / "commands"),
        ("~/.claude/experts/", EXPERTS_DIR, CLAUDE_DIR / "experts"),
        ("~/.claude/CLAUDE.md", CLAUDE_MD, CLAUDE_DIR / "CLAUDE.md"),
        ("repos/", REPOS_DIR, REPOS_LINK),
    ]:
        if link.is_symlink():
            actual = link.resolve()
            if actual == target.resolve():
                symlink_lines.append(f"[green]✓[/green] {display_name} → {target}")
            else:
                symlink_lines.append(
                    f"[yellow]![/yellow] {display_name} → {link.readlink()} "
                    f"(expected {target})"
                )
        else:
            symlink_lines.append(
                f"[red]✗[/red] {display_name} is not a symlink "
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
            # Show HEAD commit from expert dir
            expert_dir = EXPERTS_DIR / name
            head_commit = _get_head_commit(expert_dir)
            head_display = f"HEAD: {head_commit[:12]}" if head_commit else "HEAD: none"
            versions = _count_versions(expert_dir)

            ref_display = ""
            if ref_name:
                ref_display = f" @ {ref_name}"
            elif commit:
                ref_display = f" @ {commit[:12]}"
            repo_lines.append(
                f"[bold]{name}[/bold]: {remote}{ref_display} [{fetched}] "
                f"({head_display}, {versions} version{'s' if versions != 1 else ''})"
            )

        console.print(Panel("\n".join(repo_lines), title="Repos", border_style="blue"))
    else:
        console.print(Panel("No repos configured.", title="Repos", border_style="dim"))

    # Experts section
    console.print()
    list_experts()
