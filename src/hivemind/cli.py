"""Hivemind CLI — manage agents for OpenCode.

All mutations go through :mod:`hivemind.lifecycle` and the per-body modules
under :mod:`hivemind.agents`. The CLI registers a single post-mutation
listener at module init that POSTs ``/global/dispose`` to the running
opencode server synchronously — the unified hook mechanism replaces the 12
scattered ``notify_opencode_reload()`` calls the pre-refactor CLI had.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC
from typing import Any
from urllib.parse import urlparse

import typer
from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.traceback import install as install_traceback

from hivemind import opencode
from hivemind.agents import registry
from hivemind.analysis import expected_analysis_files
from hivemind.config import (
    EXTERNAL_DOCS_DIR,
    count_versions,
    expert_names,
    get_expert_dir,
    get_head_commit,
)
from hivemind.hooks import register_post_mutation
from hivemind.models import ProgressInfo, UpdatePhase

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

app = typer.Typer(name="hivemind", help="Manage expert agents for OpenCode.", invoke_without_command=True)
console = Console(theme=THEME)
install_traceback(show_locals=True, console=console)


# ---------------------------------------------------------------------------
# Post-mutation listener (registered once at import; CLI is a short-lived
# process so this happens fresh every invocation)
# ---------------------------------------------------------------------------


def _cli_reload_listener() -> None:
    if opencode.notify_instance_reload():
        console.print("  [info]↻[/info] notified running opencode server to reload")


register_post_mutation(_cli_reload_listener)


# ---------------------------------------------------------------------------
# Progress rendering
# ---------------------------------------------------------------------------


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class AnalysisProgress:
    """Rich live display for analysis file progress."""

    def __init__(self, name: str, expected: list[str]) -> None:
        self._name = name
        self._expected = expected
        self._found: set[str] = set()
        self._tick = 0
        self._running = False
        self._live = Live(self._render(), console=console, refresh_per_second=4)

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
        lines.append(f"    [dim]{len(self._found)}/{len(self._expected)} files generated[/dim]")
        return Group(*(console.render_str(line) for line in lines))

    def start(self) -> None:
        self._running = True
        self._live.start()

    def update(self, files_found: list[str] | None) -> None:
        if files_found:
            self._found.update(files_found)
        self._tick += 1
        self._live.update(self._render())

    def finish(self) -> None:
        self._running = False
        self._live.update(self._render())
        self._live.stop()


def _render_progress(info: ProgressInfo, progress: AnalysisProgress | None = None) -> AnalysisProgress | None:
    """Default ``on_progress`` renderer used by CLI commands."""
    phase = info.phase
    if phase == UpdatePhase.ANALYZING:
        if progress is None:
            progress = AnalysisProgress(info.expert_name, expected_analysis_files(is_update=False))
            progress.start()
        progress.update(info.files_found)
        return progress

    if progress is not None:
        progress.finish()
        progress = None

    prefix_map = {
        UpdatePhase.CLONING: ("info", "⟲"),
        UpdatePhase.FETCHING: ("info", "↓"),
        UpdatePhase.CHECKING: ("info", "?"),
        UpdatePhase.STAGING: ("info", "…"),
        UpdatePhase.COMMITTING: ("success", "✓"),
        UpdatePhase.UPDATING_HEAD: ("success", "✓"),
        UpdatePhase.UPDATING_LIBRARIAN: ("success", "✓"),
    }
    style, glyph = prefix_map.get(phase, ("info", "·"))
    console.print(f"  [{style}]{glyph}[/{style}] {info.message}")
    return progress


# ---------------------------------------------------------------------------
# Root callback + passthrough
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Manage expert agents for OpenCode. When invoked without a subcommand, launches opencode."""
    if ctx.invoked_subcommand is None:
        _launch_opencode([])


def _launch_opencode(extra_args: list[str]) -> None:
    from hivemind.server import is_server_running, load_server_state

    if is_server_running():
        state = load_server_state()
        if state:
            url = f"http://{state.hostname}:{state.port}"
            cmd = opencode.attach_command(url, extra_args or None)
            os.execvp(cmd[0], cmd)

    cmd = opencode.launch_command(extra_args or None)
    os.execvp(cmd[0], cmd)


# ---------------------------------------------------------------------------
# tui / mcp subcommands
# ---------------------------------------------------------------------------


@app.command()
def tui() -> None:
    """Open the hivemind TUI dashboard."""
    from hivemind.tui import HivemindApp

    HivemindApp().run()


@app.command()
def mcp() -> None:
    """Run the hivemind MCP server (stdio transport)."""
    from hivemind.mcp.__main__ import main as mcp_main

    mcp_main()


# ---------------------------------------------------------------------------
# server subcommand group
# ---------------------------------------------------------------------------


server_app = typer.Typer(name="server", help="Manage opencode backend server.", no_args_is_help=True)
app.add_typer(server_app, name="server")


@server_app.command("start")
def server_start(
    port: int | None = typer.Option(None, "--port", "-p"),
    hostname: str | None = typer.Option(None, "--hostname"),
) -> None:
    """Start the opencode backend server as a background process."""
    from hivemind.server import is_server_running, load_server_state, start_server

    if is_server_running():
        state = load_server_state()
        if state:
            console.print(
                f"[warning]Server already running on {state.hostname}:{state.port} (PID {state.pid})[/warning]"
            )
            raise typer.Exit(0)

    cfg = opencode.server_config()
    effective_port = port or cfg.port
    effective_hostname = hostname or cfg.hostname

    console.print(f"[heading]Starting opencode server on {effective_hostname}:{effective_port}...[/heading]")
    try:
        state = start_server(port=effective_port, hostname=effective_hostname)
    except RuntimeError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(1) from None

    console.print(f"[success]Server started on {state.hostname}:{state.port} (PID {state.pid})[/success]")


@server_app.command("stop")
def server_stop() -> None:
    from hivemind.server import stop_server

    if stop_server():
        console.print("[success]Server stopped.[/success]")
    else:
        console.print("[dim]No server running.[/dim]")


@server_app.command("status")
def server_status_cmd() -> None:
    from datetime import datetime

    from hivemind.server import is_server_running, load_server_state

    if not is_server_running():
        console.print("[dim]Server is not running.[/dim]")
        return
    state = load_server_state()
    if not state:
        console.print("[dim]Server is not running.[/dim]")
        return

    uptime = datetime.now(UTC) - state.started_at
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    lines = [
        "[heading]Server Status[/heading]",
        f"Provider: [success]{state.provider}[/success]",
        f"Address: {state.hostname}:{state.port}",
        f"PID: {state.pid}",
        f"Uptime: {h}h {m}m {s}s",
        f"Log: {state.log_file}",
    ]
    console.print(Panel("\n".join(lines), border_style="blue"))


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


@app.command()
def init() -> None:
    """Set up directory symlinks and deploy every enabled agent."""
    from hivemind.lifecycle import bootstrap_workspace

    console.print("[heading]Initializing hivemind...[/heading]\n")

    def on_event(label: str, status: str) -> None:
        style = "error" if status.startswith("failed") else "success"
        glyph = "✗" if style == "error" else "✓"
        console.print(f"  [{style}]{glyph}[/{style}] {label}: {status}")

    bootstrap_workspace(on_event=on_event)
    console.print("\n[bold success]Hivemind initialized![/bold success]")


# ---------------------------------------------------------------------------
# expert subcommand group
# ---------------------------------------------------------------------------


expert_app = typer.Typer(name="expert", help="Manage experts.", no_args_is_help=True)
app.add_typer(expert_app, name="expert")


def _complete_agent(incomplete: str) -> list[str]:
    try:
        return [n for n in registry.all_names() if n.startswith(incomplete)]
    except Exception:
        return []


@expert_app.command("list")
def expert_list() -> None:
    """Show every expert with its status."""
    experts = sorted(registry.by_kind("git_analyzed"), key=lambda a: a.name)
    if not experts:
        console.print("No experts found. Use [heading]hivemind expert add <url>[/heading] to add one.")
        return

    table = Table(title="Experts", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("HEAD")
    table.add_column("Versions")
    table.add_column("Remote")

    for agent in experts:
        status = "[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"
        expert_dir = get_expert_dir(agent.name)
        head_commit = get_head_commit(expert_dir)
        head_display = f"[commit]{head_commit[:12]}[/commit]" if head_commit else "[dim]none[/dim]"
        versions = str(count_versions(expert_dir)) if expert_dir.exists() else "[dim]0[/dim]"

        body_params = agent.body.to_catalog()
        remote = str(body_params.get("remote", ""))
        ref = str(body_params.get("ref_name", ""))
        remote_display = f"{remote} @ {ref}" if ref else remote

        table.add_row(agent.name, status, head_display, versions, remote_display)
    console.print(table)


@expert_app.command("show")
def expert_show(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Show detailed information about an expert."""
    agent = registry.get(name)
    if agent is None or agent.kind != "git_analyzed":
        console.print(f"[error]Error: expert '{name}' not found[/error]")
        raise typer.Exit(1)

    expert_dir = get_expert_dir(name)
    head_commit = get_head_commit(expert_dir)
    body_params = agent.body.to_catalog()

    lines = [
        f"[heading]{name}[/heading]",
        "Status: " + ("[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"),
        f"HEAD: {head_commit or '[dim]none[/dim]'}",
        f"Versions: {count_versions(expert_dir)}",
        f"Remote: {body_params.get('remote', '')}",
        f"Ref: {body_params.get('ref_name') or '[dim]default[/dim]'}",
    ]
    console.print(Panel("\n".join(lines), border_style="blue"))


@expert_app.command("add")
def expert_add(
    url: str = typer.Argument(..., help="Git remote URL"),
    ref: str | None = typer.Option(None, "--ref", help="Tag, branch, or commit (optional)"),
) -> None:
    """Register a new git-analyzed expert (clones + analyzes; agent stays unlisted)."""
    from hivemind.agents.git_analyzed import create_git_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    progress: AnalysisProgress | None = None

    def on_progress(info: ProgressInfo) -> None:
        nonlocal progress
        progress = _render_progress(info, progress)

    console.print(f"[heading]Adding expert '{name}'...[/heading]\n")
    result = asyncio.run(create_git_expert(name, url, ref_name=ref or "", on_progress=on_progress))
    if progress is not None:
        progress.finish()

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[success]Expert '{name}' added to catalog.[/success]\n"
            "Run [heading]hivemind expert enable " + name + "[/heading] to deploy it.",
            border_style="green",
        )
    )


@expert_app.command("enable")
def expert_enable(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Enable an expert (deploys agent files, ensures repo cloned)."""
    from hivemind.lifecycle import enable_agent

    result = enable_agent(name)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] {name}: enabled")


@expert_app.command("disable")
def expert_disable(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Disable an expert (removes agent file; preserves backing data)."""
    from hivemind.lifecycle import disable_agent

    result = disable_agent(name)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] {name}: disabled")


@expert_app.command("delete")
def expert_delete(
    name: str = typer.Argument(..., autocompletion=_complete_agent),
    force: bool = typer.Option(False, "--force", "-f"),
    purge_memory: bool = typer.Option(False, "--purge-memory"),
) -> None:
    """Delete an expert entirely (removes backing files + catalog entry)."""
    from hivemind.lifecycle import delete_agent

    if not force:
        typer.confirm(
            f"Delete expert '{name}' and all its data{' (including memory)' if purge_memory else ''}?",
            abort=True,
        )

    result = delete_agent(name, purge_memory=purge_memory)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[error]✗[/error] Deleted: {name}")


@expert_app.command("update")
def expert_update(
    name: str = typer.Argument(..., autocompletion=_complete_agent),
    skip_analysis: bool = typer.Option(False, "--skip-analysis"),
) -> None:
    """Fetch + re-analyze an expert from its remote."""
    from hivemind.agents.git_analyzed import update_git_expert

    progress: AnalysisProgress | None = None

    def on_progress(info: ProgressInfo) -> None:
        nonlocal progress
        progress = _render_progress(info, progress)

    console.print(f"[heading]Updating {name}...[/heading]\n")
    result = asyncio.run(update_git_expert(name, on_progress=on_progress, skip_analysis=skip_analysis))
    if progress is not None:
        progress.finish()

    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    if result.already_up_to_date:
        console.print(f"  [success]✓[/success] {name}: already up to date at {result.new_commit[:12]}")
    else:
        old = result.old_commit[:12] if result.old_commit else "none"
        console.print(f"  [success]✓[/success] {name}: updated {old} → {result.new_commit[:12]}")


@expert_app.command("switch-version")
def expert_switch_version(
    name: str = typer.Argument(..., autocompletion=_complete_agent),
    commit: str = typer.Argument(..., help="Target commit hash"),
) -> None:
    """Switch an expert to a specific commit."""
    from hivemind.agents.git_analyzed import switch_version

    progress: AnalysisProgress | None = None

    def on_progress(info: ProgressInfo) -> None:
        nonlocal progress
        progress = _render_progress(info, progress)

    result = asyncio.run(switch_version(name, commit, on_progress=on_progress))
    if progress is not None:
        progress.finish()
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)

    if result.already_up_to_date:
        console.print(f"  [success]✓[/success] {name}: already at {result.new_commit[:12]}")
    else:
        old = result.old_commit[:12] if result.old_commit else "none"
        console.print(f"  [success]✓[/success] {name}: switched {old} → {result.new_commit[:12]}")


# ---------------------------------------------------------------------------
# expert crawl command
# ---------------------------------------------------------------------------


def _crawl_render(state: dict[str, Any]) -> Group:
    """Render the live crawl trace from a mutable state dict.

    Sections rendered (in order, only when populated):
      Probe        — capability summary + chosen strategies
      Discover     — sitemap leaf table (status, MB, in-scope hits)
                     or single-line summary for spider/browser
      Extract      — progress bar + last 5 completed URLs
    """
    spinner = _SPINNER_FRAMES[state["tick"] % len(_SPINNER_FRAMES)]
    lines: list[str] = []

    profile = state.get("profile")
    if profile is not None:
        yn = lambda v, y="works", n="no": f"[success]{y}[/success]" if v else f"[warning]{n}[/warning]"  # noqa: E731
        lines.append("[bold]Probe[/bold]")
        lines.append(
            f"  static extraction: {yn(profile.static_extraction_works)}"
            f"   static discovery: {yn(profile.static_discovery_works)}"
        )
        lines.append(
            f"  sitemap: [info]{profile.sitemap_status}[/info]   .md source: {yn(profile.has_md_source, 'yes', 'no')}"
        )
        lines.append(
            f"  → discovery=[bold]{profile.discovery_strategy}[/bold]"
            f", extraction=[bold]{profile.extraction_strategy}[/bold]"
        )
        lines.append("")

    leaves = state.get("leaves") or {}
    if leaves:
        lines.append(f"[bold]Discover[/bold] (sitemap, {len(leaves)} leaves)")
        for idx in sorted(leaves):
            leaf = leaves[idx]
            mb = leaf.bytes_read / (1024 * 1024)
            short = leaf.url.split("/")[-1] or leaf.url
            if leaf.status == "queued":
                marker = "[dim]·[/dim]"
                tail = "[dim](queued)[/dim]"
            elif leaf.status == "streaming":
                marker = f"[info]{spinner}[/info]"
                tail = f"[dim]{mb:6.1f} MB streamed[/dim]   [success]{leaf.in_scope_hits}[/success] in-scope"
            elif leaf.status == "done":
                marker = "[success]✓[/success]"
                tail = f"[dim]{mb:6.1f} MB[/dim]   [success]{leaf.in_scope_hits}[/success] in-scope"
            else:  # failed
                marker = "[error]✗[/error]"
                tail = f"[error]failed[/error] {leaf.error or ''}"
            lines.append(f"  {marker} leaf {idx + 1}/{leaf.total}  [dim]{short}[/dim]   {tail}")
        total_hits = sum(leaf.in_scope_hits for leaf in leaves.values())
        lines.append(f"  [bold]Total in-scope so far:[/bold] {total_hits}")
        lines.append("")

    discover_summary = state.get("discover_summary")
    if discover_summary and not leaves:
        lines.append(discover_summary)
        lines.append("")

    extract_total = state.get("extract_total")
    if extract_total is not None:
        ok = state["extract_ok"]
        fail = state["extract_fail"]
        done = ok + fail
        bar_width = 30
        filled = int(bar_width * done / extract_total) if extract_total else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        lines.append(f"[bold]Extract[/bold] ({state['extract_strategy']})  [{bar}] {done}/{extract_total}")
        lines.extend(f"  [success]✓[/success] [dim]{u}[/dim]" for u in list(state.get("recent", []))[-5:])

    return Group(*(console.render_str(line) for line in lines))


@expert_app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    agent: str = typer.Argument(..., help="Agent name for output directory", autocompletion=_complete_agent),
    max_pages: int | None = typer.Option(None, "--max-pages", "-n", help="Maximum pages to crawl (default: no limit)"),
) -> None:
    """Crawl a website and save documentation for an expert agent.

    Probes the site, picks the appropriate discovery + extraction
    strategy (sitemap / spider / browser), and saves clean markdown
    to ~/.cache/hivemind/external_docs/<agent>/.

    JS-rendered docs sites are detected automatically and rendered
    via Chromium. Run `uv run playwright install chromium` once if
    the browser binary isn't installed.
    """
    expert_dir = get_expert_dir(agent)
    if not expert_dir.is_dir():
        console.print(f"[error]Error: Expert '{agent}' not found.[/error]")
        console.print("\n[info]Available experts:[/info]")
        experts = sorted(expert_names())
        if experts:
            for expert in experts:
                console.print(f"  - {expert}")
        else:
            console.print("  [dim]No experts configured. Use [bold]hivemind expert add <url>[/bold] to add one.[/dim]")
        raise typer.Exit(1)

    from collections import deque

    from hivemind.crawl import BrowserUnavailableError, LeafProgress, crawl_website

    output_dir = EXTERNAL_DOCS_DIR / agent

    console.print(f"[heading]Crawling Documentation for {agent}[/heading]\n")
    console.print(f"[info]URL:[/info] {escape(url)}")
    console.print(f"[info]Output:[/info] {escape(str(output_dir))}")
    console.print()

    state: dict[str, Any] = {
        "tick": 0,
        "profile": None,
        "leaves": {},
        "discover_summary": None,
        "extract_strategy": None,
        "extract_total": None,
        "extract_ok": 0,
        "extract_fail": 0,
        "recent": deque(maxlen=5),
    }

    live = Live(_crawl_render(state), console=console, refresh_per_second=4, transient=False)

    def tick() -> None:
        state["tick"] += 1
        live.update(_crawl_render(state))

    def on_phase(phase: str, info: dict[str, object]) -> None:
        if phase == "probe":
            state["profile"] = info["profile"]
        elif phase == "discover":
            if not state["leaves"]:
                state["discover_summary"] = (
                    f"[bold]Discover[/bold] ({info['strategy']})  [success]{info['count']}[/success] URLs in scope"
                )
        elif phase == "extract_start":
            state["extract_strategy"] = info["strategy"]
            state["extract_total"] = info["count"]
        tick()

    def on_leaf(leaf: LeafProgress) -> None:
        state["leaves"][leaf.index] = leaf
        tick()

    def on_page(page_url: str, success: bool) -> None:
        if success:
            state["extract_ok"] += 1
            short = urlparse(page_url).path or page_url
            state["recent"].append(short)
        else:
            state["extract_fail"] += 1
        tick()

    live.start()
    try:
        result = asyncio.run(
            crawl_website(
                url=url,
                max_pages=max_pages,
                output_dir=str(output_dir),
                on_page_callback=on_page,
                on_phase_callback=on_phase,
                on_leaf_progress=on_leaf,
            ),
        )
    except BrowserUnavailableError as e:
        live.stop()
        console.print("\n[error]This site requires browser rendering, but Chromium isn't installed.[/error]")
        console.print("[info]Run:[/info]  [bold]uv run playwright install chromium[/bold]\n")
        console.print(f"[dim]Underlying error: {escape(str(e))}[/dim]")
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        live.stop()
        console.print(f"\n[warning]Interrupted.[/warning] {state['extract_ok']} pages saved to {output_dir}\n")
        raise typer.Exit(130) from None
    except Exception as e:
        live.stop()
        console.print(f"\n[error]Crawl failed: {escape(str(e))}[/error]")
        raise typer.Exit(1) from None
    finally:
        live.stop()

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


# ---------------------------------------------------------------------------
# team subcommand group
# ---------------------------------------------------------------------------


team_app = typer.Typer(name="team", help="Manage teams.", no_args_is_help=True)
app.add_typer(team_app, name="team")


@team_app.command("list")
def team_list() -> None:
    """Show every team with its roster and enabled state."""
    teams = sorted(registry.by_kind("roster_templated"), key=lambda a: a.name)
    if not teams:
        console.print("No teams configured.")
        return

    table = Table(title="Teams", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Description")
    table.add_column("Roster")

    for agent in teams:
        status = "[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"
        body = agent.body.to_catalog()
        description = str(body.get("description", ""))
        roster = ", ".join(str(e) for e in body.get("experts", [])) or "[dim]empty[/dim]"
        table.add_row(agent.name, status, description, roster)
    console.print(table)


@team_app.command("show")
def team_show(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Show detailed information about a team."""
    agent = registry.get(name)
    if agent is None or agent.kind != "roster_templated":
        console.print(f"[error]Error: team '{name}' not found[/error]")
        raise typer.Exit(1)

    body = agent.body.to_catalog()
    lines = [
        f"[heading]{name}[/heading]",
        "Status: " + ("[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"),
        f"Description: {body.get('description', '')}",
        f"Roster: {', '.join(str(e) for e in body.get('experts', [])) or '(empty)'}",
    ]
    console.print(Panel("\n".join(lines), border_style="blue"))


@team_app.command("create")
def team_create(
    name: str = typer.Argument(..., help="Team name"),
    description: str = typer.Option(..., "--description", "-d", help="Team description"),
    experts: str = typer.Option(..., "--experts", "-e", help="Comma-separated expert names"),
) -> None:
    """Create a new team (unlisted)."""
    from hivemind.agents.roster_templated import create_team

    expert_list = [e.strip() for e in experts.split(",") if e.strip()]
    if not expert_list:
        console.print("[error]Error: at least one expert required[/error]")
        raise typer.Exit(1)

    console.print(f"[heading]Creating team '{name}' with {len(expert_list)} experts...[/heading]")
    result = asyncio.run(create_team(name, description, expert_list))
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Team '{name}' created (unlisted).")
    console.print(f"Run [heading]hivemind team enable {name}[/heading] to deploy it.")


@team_app.command("enable")
def team_enable(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Enable a team (deploys team lead, clones member repos)."""
    from hivemind.lifecycle import enable_agent

    result = enable_agent(name)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] {name}: team enabled")


@team_app.command("disable")
def team_disable(name: str = typer.Argument(..., autocompletion=_complete_agent)) -> None:
    """Disable a team (removes team lead agent; preserves team data)."""
    from hivemind.lifecycle import disable_agent

    result = disable_agent(name)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] {name}: team disabled")


@team_app.command("delete")
def team_delete(
    name: str = typer.Argument(..., autocompletion=_complete_agent),
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    """Delete a team (removes team dir + catalog entry)."""
    from hivemind.lifecycle import delete_agent

    if not force:
        typer.confirm(f"Delete team '{name}' and all its data?", abort=True)

    result = delete_agent(name)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[error]✗[/error] Team deleted: {name}")


@team_app.command("add-expert")
def team_add_expert(
    team: str = typer.Argument(...),
    experts: str = typer.Argument(..., help="Comma-separated expert names"),
) -> None:
    """Add one or more experts to a team's roster."""
    from hivemind.agents.roster_templated import add_expert_to_team, add_experts_to_team

    expert_list = [e.strip() for e in experts.split(",") if e.strip()]
    if not expert_list:
        console.print("[error]Error: at least one expert required[/error]")
        raise typer.Exit(1)

    if len(expert_list) == 1:
        result = asyncio.run(add_expert_to_team(team, expert_list[0]))
        if not result.success:
            console.print(f"[error]Error: {escape(str(result.error))}[/error]")
            raise typer.Exit(1)
        console.print(f"[success]✓[/success] Added {expert_list[0]} to {team}")
        return

    result = asyncio.run(add_experts_to_team(team, expert_list))
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    for n in result.added:
        console.print(f"[success]✓[/success] Added {n} to {team}")
    for n in result.skipped:
        console.print(f"[warning]·[/warning] Skipped (already on team): {n}")
    for err in result.failed:
        console.print(f"[error]✗[/error] Failed {err.name}: {err.error}")


@team_app.command("remove-expert")
def team_remove_expert(
    team: str = typer.Argument(...),
    expert: str = typer.Argument(...),
) -> None:
    """Remove an expert from a team's roster."""
    from hivemind.agents.roster_templated import remove_expert_from_team

    result = remove_expert_from_team(team, expert)
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Removed {expert} from {team}")


# ---------------------------------------------------------------------------
# redeploy + status
# ---------------------------------------------------------------------------


@app.command()
def redeploy() -> None:
    """Regenerate every enabled agent file from the current catalog."""
    from hivemind.lifecycle import redeploy_all_agents

    console.print("[heading]Redeploying all agents...[/heading]")
    result = redeploy_all_agents()
    if not result.success:
        console.print(f"[error]Error: {escape(str(result.error))}[/error]")
        raise typer.Exit(1)
    for n in result.experts_deployed:
        console.print(f"[success]✓[/success] expert {n}")
    for n in result.teams_deployed:
        console.print(f"[success]✓[/success] team-lead {n}")
    for n in result.failed:
        console.print(f"[error]✗[/error] expert {n}")
    for n in result.teams_failed:
        console.print(f"[error]✗[/error] team-lead {n}")


@app.command()
def status() -> None:
    """Show a dashboard of hivemind status."""
    from hivemind.server import is_server_running, load_server_state

    cfg = opencode._cfg()

    try:
        engine_path = opencode._engine_path()
    except RuntimeError as e:
        engine_path = f"<unavailable: {e}>"

    overview_lines: list[str] = []
    overview_lines.append(f"Engine: [heading]{escape(engine_path)}[/heading]")
    overview_lines.append(f"Model: [heading]{escape(cfg.model)}[/heading]")

    if is_server_running():
        state = load_server_state()
        if state:
            overview_lines.append(
                f"Server: [success]running[/success] on {state.hostname}:{state.port} (PID {state.pid})"
            )
    else:
        overview_lines.append("Server: [dim]not running[/dim]")

    experts = registry.by_kind("git_analyzed")
    teams = registry.by_kind("roster_templated")
    overview_lines.append(
        f"Experts: [success]{sum(1 for a in experts if a.enabled)} enabled[/success]"
        + (
            f", [warning]{sum(1 for a in experts if not a.enabled)} disabled[/warning]"
            if any(not a.enabled for a in experts)
            else ""
        )
    )
    overview_lines.append(
        f"Teams: [success]{sum(1 for a in teams if a.enabled)} enabled[/success]"
        + (
            f", [warning]{sum(1 for a in teams if not a.enabled)} disabled[/warning]"
            if any(not a.enabled for a in teams)
            else ""
        )
    )

    console.print(Panel("\n".join(overview_lines), title="Hivemind", border_style="blue"))

    if experts:
        table = Table(title="Experts", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("HEAD")
        for agent in sorted(experts, key=lambda a: a.name):
            status_cell = "[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"
            head_commit = get_head_commit(get_expert_dir(agent.name))
            head_display = f"[commit]{head_commit[:12]}[/commit]" if head_commit else "[dim]none[/dim]"
            table.add_row(agent.name, status_cell, head_display)
        console.print(table)

    if teams:
        table = Table(title="Teams", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="bold")
        table.add_column("Status")
        table.add_column("Roster")
        for agent in sorted(teams, key=lambda a: a.name):
            status_cell = "[success]enabled[/success]" if agent.enabled else "[warning]disabled[/warning]"
            body = agent.body.to_catalog()
            roster = ", ".join(str(e) for e in body.get("experts", [])) or "[dim]empty[/dim]"
            table.add_row(agent.name, status_cell, roster)
        console.print(table)


# ---------------------------------------------------------------------------
# Passthrough entry point
# ---------------------------------------------------------------------------


def main_entry() -> None:
    """Entry point. With ``--``, forwards trailing args to opencode; otherwise dispatches via typer."""
    import sys

    args = sys.argv[1:]
    if "--" in args:
        idx = args.index("--")
        if idx != 0:
            console.print(
                "[error]hivemind: '--' must be the first argument; "
                "use 'hivemind -- <opencode args>' to forward to opencode[/error]"
            )
            sys.exit(2)
        # Direct passthrough to the engine binary — no attach logic.
        cmd = opencode.launch_command(args[idx + 1 :] or None)
        os.execvp(cmd[0], cmd)

    app(prog_name="hivemind")
