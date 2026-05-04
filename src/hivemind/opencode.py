"""OpenCode integration — formatting, deployment, engine, and server glue.

The previous ``Provider`` class has been collapsed into module-level
functions here. OpenCode is the only supported backend; there is no
abstraction for additional providers. The module caches the
``HivemindConfig`` loaded from ``hivemind.json`` on first access;
``invalidate_config_cache()`` resets it after config writes.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Literal, assert_never

import httpx

from hivemind.constants import (
    CACHE_DIR,
    CACHE_DIR_PLACEHOLDER,
    DEFAULT_TEMPERATURE,
    ENGINE_VALIDATION_TIMEOUT,
    EXPERTS_DIR_PLACEHOLDER,
    OPENCODE_CONFIG_DIR,
    TEAMS_DIR_PLACEHOLDER,
)
from hivemind.models import HivemindConfig, InitResult, OperationResult, ServerConfig
from hivemind.templates import LIBRARIAN_DESCRIPTION

log = logging.getLogger(__name__)

Kind = Literal["git_analyzed", "roster_templated", "user_supplied", "system_templated", "librarian"]

PROVIDER_NAME = "opencode"
RULES_FILE_NAME = "AGENTS.md"


# ---------------------------------------------------------------------------
# Config loading (replaces Provider.__init__)
# ---------------------------------------------------------------------------

_config_cache: HivemindConfig | None = None
_engine_validated: bool = False


def _cfg() -> HivemindConfig:
    """Return the cached ``HivemindConfig`` (loading it on first access)."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    from hivemind.config import load_hivemind

    cfg = load_hivemind()
    errors: list[str] = []
    if not cfg.home_dir:
        errors.append("home_dir must be set")
    if not cfg.model:
        errors.append("model must be set")
    if errors:
        msg = f"Incomplete config: {'; '.join(errors)}. Check hivemind.json."
        raise RuntimeError(msg)

    _config_cache = cfg
    return _config_cache


def _engine_path() -> str:
    """Resolve the bun-compiled hivemind-engine binary via Bazel runfiles.

    Resolution:
      1. ``$HIVEMIND_ENGINE`` — explicit override (tests, ad-hoc runs).
      2. ``$RUNFILES_DIR / ENGINE_RLOCATION`` — direct concatenation.
         ``ENGINE_RLOCATION`` is generated at build time from
         ``$(rlocationpath //:engine)`` via the ``_engine_rlocation``
         ``expand_template`` rule in ``src/hivemind/BUILD.bazel``, so
         it's already a canonical (post-repo-mapping) rlocation key.
         We bypass ``python.runfiles.Runfiles`` because that class uses
         ``__file__``-based walk-up to find the runfiles root, which
         lands inside the venv under ``py_venv_binary``.

    Works for both ``bazel run //:hivemind`` and direct launcher invocation
    (via ``~/.local/bin/hivemind``) — rules_py's launcher sets ``RUNFILES_DIR``
    regardless of how it's invoked.
    """
    if env := os.environ.get("HIVEMIND_ENGINE"):
        return env

    runfiles_dir = os.environ.get("RUNFILES_DIR")
    if not runfiles_dir:
        msg = "hivemind-engine not found: $RUNFILES_DIR unset (not running under Bazel)."
        raise RuntimeError(msg)

    from hivemind._engine_rlocation import ENGINE_RLOCATION  # type: ignore[import-untyped]

    path = Path(runfiles_dir) / ENGINE_RLOCATION
    if not path.exists():
        msg = f"hivemind-engine runfile missing at {path} (key={ENGINE_RLOCATION!r})."
        raise RuntimeError(msg)
    return str(path)


def invalidate_config_cache() -> None:
    """Clear the cached ``HivemindConfig`` — call after writes to hivemind.json."""
    global _config_cache, _engine_validated
    _config_cache = None
    _engine_validated = False


# ---------------------------------------------------------------------------
# Public path accessors
# ---------------------------------------------------------------------------


def home_dir() -> Path:
    """OpenCode home directory (typically ``~/.config/opencode``)."""
    return Path(_cfg().home_dir).expanduser()


def experts_base_path() -> str:
    """Absolute base path for experts as it appears in agent bodies."""
    return str(home_dir() / "experts")


def teams_base_path() -> str:
    """Absolute base path for teams dir as it appears in agent bodies."""
    return str(home_dir() / "teams")


def cache_base_path() -> str:
    """Absolute base path for hivemind cache directory."""
    return str(CACHE_DIR)


def permissions() -> dict[str, object] | None:
    """Provider permissions config (opaque dict, passed to deployed config)."""
    return _cfg().permissions


def supports_server() -> bool:
    """Whether this provider has a backend server mode (always True for opencode)."""
    return True


def server_config() -> ServerConfig:
    """Return the opencode backend server configuration."""
    return _cfg().server


def memory_dir() -> Path:
    """Root of the per-agent hivemind memory tree."""
    return home_dir() / "hivemind" / "memory"


def orchestrator_memory_dir() -> Path:
    """Memory directory for the opencode orchestrator (non-agent user session)."""
    return memory_dir() / "_orchestrator"


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return content


def yaml_escape_double_quoted(s: str) -> str:
    """Escape a string for use inside a YAML double-quoted scalar."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def replace_expert_paths(body: str, *, old_base: str, new_base: str) -> str:
    """Replace expert base directory paths in agent body."""
    return body.replace(old_base, new_base)


def _transform_body(body: str) -> str:
    """Apply standard path placeholder substitution in agent bodies."""
    body = replace_expert_paths(body, old_base=EXPERTS_DIR_PLACEHOLDER, new_base=experts_base_path())
    body = body.replace(TEAMS_DIR_PLACEHOLDER, teams_base_path())
    return body.replace(CACHE_DIR_PLACEHOLDER, cache_base_path())


# ---------------------------------------------------------------------------
# Agent file formatting
# ---------------------------------------------------------------------------


def _build_frontmatter(
    *,
    name: str,
    description: str,
    tools: dict[str, bool],
    extra_permissions: list[str] | None = None,
    body: str,
) -> str:
    """Build a complete OpenCode agent file with YAML frontmatter."""
    cfg = _cfg()
    temperature = cfg.temperature if cfg.temperature is not None else DEFAULT_TEMPERATURE

    lines = [
        "---",
        f'description: "{yaml_escape_double_quoted(description)}"',
        "mode: subagent",
        f"model: {cfg.model}",
        f"temperature: {temperature}",
    ]

    if tools:
        lines.append("tools:")
        for tool_name, enabled in sorted(tools.items()):
            lines.append(f"  {tool_name}: {str(enabled).lower()}")

    lines.append("permission:")
    lines.append("  external_directory:")
    lines.append(f'    "{cache_base_path()}/**": allow')
    lines.append(f'    "{experts_base_path()}/**": allow')
    lines.append(f'    "{memory_dir()}/{name}/**": allow')
    if extra_permissions:
        lines.extend(f"    {perm}" for perm in extra_permissions)

    lines.append("---")
    lines.append("")
    lines.append("")

    return "\n".join(lines) + _transform_body(body)


def format_agent(kind: Kind, name: str, description: str, body: str) -> str:
    """Format a deployed agent file for a given agent kind.

    Dispatches on ``kind`` to choose tools and extra permissions:

    - ``git_analyzed``: standard expert tools, no extra permissions.
    - ``roster_templated``: standard tools + ``edit`` + write access to teams/.
    - ``librarian``: read-only (read/grep/glob) tools only.
    """
    cfg = _cfg()
    if kind == "git_analyzed":
        return _build_frontmatter(
            name=name,
            description=description,
            tools=dict(cfg.tools),
            body=body,
        )
    if kind == "roster_templated":
        tools = dict(cfg.tools)
        tools["edit"] = True
        return _build_frontmatter(
            name=name,
            description=description,
            tools=tools,
            extra_permissions=[f'"{teams_base_path()}/**": allow'],
            body=body,
        )
    if kind == "user_supplied":
        # The user owns the entire markdown including frontmatter.
        # Pass it through untouched — `_build_frontmatter` would clobber
        # whatever they wrote.
        return body
    if kind == "system_templated":
        # The Jinja template owns the entire markdown including
        # frontmatter (description, mode, model, tools, permissions).
        # Same pass-through treatment as user_supplied.
        return body
    if kind == "librarian":
        return _build_frontmatter(
            name=name,
            description=LIBRARIAN_DESCRIPTION,
            tools={"read": True, "grep": True, "glob": True},
            body=body,
        )
    assert_never(kind)


def agent_filename(kind: Kind, name: str) -> str:
    """The on-disk filename within ``agents/`` for a deployed agent of ``kind``."""
    if kind == "git_analyzed":
        return f"expert-{name}.md"
    if kind == "roster_templated":
        return f"team-lead-{name}.md"
    if kind == "user_supplied":
        return f"{name}.md"
    if kind == "system_templated":
        return f"{name}.md"
    if kind == "librarian":
        return "librarian.md"
    assert_never(kind)


def write_agent_file(kind: Kind, name: str, content: str, *, agents_dir: Path) -> None:
    """Write the formatted agent file into ``agents_dir``."""
    agents_dir.mkdir(parents=True, exist_ok=True)
    path = agents_dir / agent_filename(kind, name)
    if path.is_symlink():
        path.unlink()
    path.write_text(content, encoding="utf-8")


def remove_agent_file(kind: Kind, name: str, *, agents_dir: Path) -> None:
    """Remove the deployed agent file if present."""
    path = agents_dir / agent_filename(kind, name)
    if path.is_symlink() or path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Backing-dir deployment (git_analyzed experts need a symlink into experts/)
# ---------------------------------------------------------------------------


def deploy_backing_dir(name: str, source_dir: Path) -> None:
    """Symlink ``source_dir`` into the opencode experts directory under ``name``."""
    provider_experts = home_dir() / "experts"
    provider_experts.mkdir(parents=True, exist_ok=True)

    link = provider_experts / name
    if link.is_symlink():
        if link.resolve() == source_dir.resolve():
            return
        link.unlink()
    elif link.exists():
        if link.is_dir():
            shutil.rmtree(link)
        else:
            link.unlink()
    link.symlink_to(source_dir)


def undeploy_backing_dir(name: str) -> None:
    """Remove the opencode experts symlink for ``name`` if present."""
    link = home_dir() / "experts" / name
    if not link.is_symlink() and not link.exists():
        return
    if link.is_dir() and not link.is_symlink():
        shutil.rmtree(link)
    else:
        link.unlink()


# ---------------------------------------------------------------------------
# Engine validation & analysis command construction
# ---------------------------------------------------------------------------


def validate_engine() -> OperationResult:
    """Validate that the bundled engine binary and configured model are available.

    Result is cached per-process — the ``hivemind-engine models`` subprocess
    call is ~800 ms and the answer doesn't change without a config edit
    (which resets the cache via :func:`invalidate_config_cache`).
    """
    global _engine_validated
    if _engine_validated:
        return OperationResult(success=True)

    cfg = _cfg()

    try:
        binary = _engine_path()
    except RuntimeError as e:
        return OperationResult(success=False, error=str(e))

    if not cfg.model:
        return OperationResult(
            success=False,
            error="No model configured. Set 'model' in hivemind.json.",
        )

    try:
        result = subprocess.run(
            [binary, "models"],
            capture_output=True,
            text=True,
            timeout=ENGINE_VALIDATION_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        return OperationResult(success=False, error=f"Engine binary '{binary}' not found.")
    except subprocess.TimeoutExpired:
        return OperationResult(
            success=False,
            error=f"Model validation timed out ({binary} models).",
        )

    if result.returncode != 0:
        return OperationResult(
            success=False,
            error=f"Failed to query available models: {result.stderr.strip()[:200]}",
        )

    available = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if cfg.model not in available:
        return OperationResult(
            success=False,
            error=(
                f"Model '{cfg.model}' not available. "
                "Run 'hivemind-engine providers' to configure it.\n"
                "Available models can be listed with 'hivemind-engine models'."
            ),
        )

    _engine_validated = True
    return OperationResult(success=True)


def build_analysis_command(
    *,
    extra_dirs: list[Path] | None = None,
    write: bool = False,
) -> list[str]:
    """Build a hivemind-engine subprocess command for AI analysis runs."""
    cfg = _cfg()
    # `run` is opencode's non-interactive prompt subcommand; analysis runs
    # always feed a single prompt and exit, so this is the right driver.
    cmd = [_engine_path(), "run", "--model", cfg.model]

    if extra_dirs:
        resolved = [str(d.resolve()) for d in extra_dirs if d.exists()]
        if resolved:
            common = os.path.commonpath(resolved)
            cmd.extend(["--dir", common])

    return cmd


def build_query_command() -> list[str]:
    """Build a hivemind-engine subprocess command for librarian queries."""
    cfg = _cfg()
    return [_engine_path(), "run", "--model", cfg.model]


# ---------------------------------------------------------------------------
# Server lifecycle commands
# ---------------------------------------------------------------------------


def start_server_command(port: int, hostname: str) -> list[str]:
    return [_engine_path(), "serve", "--port", str(port), "--hostname", hostname]


def launch_command(extra_args: list[str] | None = None) -> list[str]:
    return [_engine_path(), *(extra_args or [])]


def attach_command(server_url: str, extra_args: list[str] | None = None) -> list[str]:
    """Build the engine command to attach to a running hivemind server.

    Routing:
      - No extra args → ``engine attach <url>`` (plain TUI attach).
      - First extra arg is ``run`` → ``engine run --attach <url> <rest>``
        (one-shot prompt against the attached server).
      - Otherwise (TUI flags like ``-s``, ``-c``, ``--fork``) →
        ``engine attach <url> <args>`` so the flags reach the TUI.

    Previously the no-empty-args branch always routed through
    ``run --attach``, which silently used non-interactive mode for
    e.g. ``hivemind -- -s ses_xxx`` resume requests.
    """
    binary = _engine_path()
    args = extra_args or []
    if args and args[0] == "run":
        return [binary, "run", "--attach", server_url, *args[1:]]
    return [binary, "attach", server_url, *args]


def health_check_url(port: int, hostname: str) -> str:
    return f"http://{hostname}:{port}/global/health"


def notify_instance_reload() -> bool:
    """POST /global/reload-agents on the running opencode server.

    Re-reads agents/*.md for every active instance WITHOUT disposing
    the InstanceState. Unlike the old `/global/dispose` path, this does
    not SIGTERM MCP subprocesses, so an in-flight tool call (the
    hivemind MCP server itself, when called via MCP transport) survives
    the reload and the user does not have to type `continue` after
    every catalog mutation.

    Provided by the //third_party/patches/0004-add-reload-agents-endpoint.patch
    patch in our opencode fork; not available against upstream opencode.

    Fire-and-forget — returns False when no server is reachable
    (``detached`` or ``test`` modes).
    """
    from hivemind.runtime import current_context

    ctx = current_context()
    if ctx.mode == "attached":
        assert ctx.server_url is not None  # implied by mode; documents the invariant
        try:
            resp = httpx.post(f"{ctx.server_url}/global/reload-agents", timeout=5.0)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            log.debug("Failed to notify OpenCode server at %s", ctx.server_url)
            return False
    if ctx.mode == "detached":
        # Mutation already persisted to disk; opencode picks it up on next launch.
        return False
    if ctx.mode == "test":
        # Tests don't run a real server; mock at the httpx layer if needed.
        return False
    assert_never(ctx.mode)


# ---------------------------------------------------------------------------
# Session HTTP API
#
# Thin wrappers around the running engine's REST endpoints, used by the
# cross-session MCP tools (list_sessions, send_message). All require a
# running engine; raise RuntimeError when detached so callers can surface
# a clear error to the model instead of silently returning empty.
# ---------------------------------------------------------------------------

SESSION_HTTP_TIMEOUT = 10.0


def _server_url() -> str:
    from hivemind.runtime import current_context

    ctx = current_context()
    if ctx.mode == "attached":
        assert ctx.server_url is not None  # implied by mode; documents the invariant
        return ctx.server_url
    if ctx.mode == "detached":
        raise RuntimeError("no opencode server is running — start one with `hivemind` first")
    if ctx.mode == "test":
        raise RuntimeError("_server_url called in test mode — mock the HTTP layer instead of hitting it")
    assert_never(ctx.mode)


def session_list(roots: bool | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    """GET /session — list sessions, optionally filtered to root sessions."""
    params: dict[str, str] = {}
    if roots is not None:
        params["roots"] = "true" if roots else "false"
    if limit is not None:
        params["limit"] = str(limit)
    resp = httpx.get(
        f"{_server_url()}/session",
        params=params,
        timeout=SESSION_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data: list[dict[str, Any]] = resp.json()
    return data


def session_delete(session_id: str) -> None:
    """DELETE /session/:sessionID — hard-remove a session and its descendants.

    Best-effort aborts the session first (so an in-flight prompt stops
    streaming into a row that's about to vanish), then DELETEs. The
    engine recurses into child sessions, fires ``session.deleted`` on
    the bus (the TUI subagents pill subscribes to this), and removes
    the SQLite row. Not recoverable. Idempotent — calling on an
    already-deleted ID returns success silently because upstream's
    ``Session.remove`` swallows not-found at session.ts:471-473.
    """
    with contextlib.suppress(httpx.HTTPError):
        httpx.post(
            f"{_server_url()}/session/{session_id}/abort",
            timeout=SESSION_HTTP_TIMEOUT,
        )

    resp = httpx.delete(
        f"{_server_url()}/session/{session_id}",
        timeout=SESSION_HTTP_TIMEOUT,
    )
    resp.raise_for_status()


def session_inbox(session_id: str, text: str) -> dict[str, Any]:
    """POST /session/:id/inbox — queue-on-busy message delivery.

    Provided by ``//third_party/patches/0007-...inbox...patch``. Returns
    ``{sessionID, queued, depth}`` once the engine has decided whether
    to deliver immediately or queue for the next idle. The prompt's
    full turn runs asynchronously regardless.
    """
    body = {"parts": [{"type": "text", "text": text}]}
    resp = httpx.post(
        f"{_server_url()}/session/{session_id}/inbox",
        json=body,
        timeout=SESSION_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return data


def live_session_ids() -> set[str]:
    """GET /global/live-sessions — sessions a TUI is currently attached to.

    Provided by ``//third_party/patches/0009-SSE-liveness-counter.patch``.
    A session shows up here while at least one TUI process holds an open
    SSE subscription (``GET /event?sessionID=<id>``); the count
    increments on stream open and decrements when the abort handler
    fires. Closing the TUI drops the entry.
    """
    resp = httpx.get(
        f"{_server_url()}/global/live-sessions",
        timeout=SESSION_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    sessions: list[str] = data.get("sessions", [])
    return set(sessions)


def background_tasks_active() -> list[dict[str, Any]]:
    """GET /global/background-tasks — background-mode Task children.

    Provided by
    ``//third_party/patches/0017-Background-Task-mode-cascade-cancellation.patch``.
    Each entry has ``parentID``, ``taskID``, and ``status``
    (``"running"`` | ``"complete"``). Running entries are subagents
    spawned via ``Task(background=true)`` whose prompts have not yet
    finished; complete entries are buffered results awaiting
    consumption by the parent via the ``read_task_result`` tool.
    """
    resp = httpx.get(
        f"{_server_url()}/global/background-tasks",
        timeout=SESSION_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    tasks: list[dict[str, Any]] = data.get("tasks", [])
    return tasks


# ---------------------------------------------------------------------------
# Directory initialisation
# ---------------------------------------------------------------------------


def init_dirs(
    *,
    agents_dir: Path,
    commands_dir: Path,
    skills_dir: Path,
    rules_source: Path,
    teams_dir: Path | None = None,
) -> list[InitResult]:
    """Initialize the opencode directory structure.

    Sets up symlinks for agents/, commands/, skills/, rules, experts/ (real
    dir), and teams/, then injects per-user runtime config (path-token
    permissions + MCP server registration) into opencode.json and purges
    stale TUI plugins from earlier hivemind installs.
    """
    results: list[InitResult] = []

    home = home_dir()
    home.mkdir(parents=True, exist_ok=True)

    results.append(_setup_symlink(agents_dir, home / "agents", "agents/"))
    results.append(_setup_symlink(commands_dir, home / "commands", "commands/"))
    results.append(_setup_symlink(skills_dir, home / "skills", "skills/"))
    results.append(_setup_symlink(rules_source, home / RULES_FILE_NAME, RULES_FILE_NAME))

    experts = home / "experts"
    experts.mkdir(parents=True, exist_ok=True)
    results.append(InitResult(label="experts/", status="directory ready"))

    if teams_dir:
        results.append(_setup_symlink(teams_dir, home / "teams", "teams/"))

    # Ensure memory tree exists (per-agent dirs are populated later by lifecycle)
    mem = memory_dir()
    mem.mkdir(parents=True, exist_ok=True)
    results.append(InitResult(label="hivemind/memory/", status="memory root ready"))

    results.extend(_post_init_dirs())

    return results


def _post_init_dirs() -> list[InitResult]:
    """Apply bundled opencode defaults: path-token permissions + MCP registration.

    Hardening keys (share, autoshare, autoupdate, server.hostname) and the
    `bash.sudo *: deny` permission used to be merged here too, but they're now
    baked into the bun-compiled engine via patches in `//third_party/patches/`
    so this function only handles user-specific runtime injection:
      - path-token permission rules (need {CACHE_PATH}/{EXPERTS_PATH}/{TEAMS_PATH}
        substitution against per-user paths)
      - the hivemind MCP server registration (command path varies per install)
    """
    results: list[InitResult] = []
    home = home_dir()

    defaults = _load_opencode_defaults()
    permissions_section = _substitute_path_tokens(defaults.get("permissions", {}))

    config_path = home / "opencode.json"
    existing: dict[str, Any] = {}
    if config_path.exists() and not config_path.is_symlink():
        with contextlib.suppress(FileNotFoundError):
            existing = json.loads(config_path.read_text(encoding="utf-8"))

    existing_perms = existing.get("permission", {})
    for tool_key, patterns in permissions_section.items():
        if tool_key not in existing_perms:
            existing_perms[tool_key] = {}
        if isinstance(existing_perms[tool_key], dict):
            existing_perms[tool_key].update(patterns)
        else:
            existing_perms[tool_key] = {"*": existing_perms[tool_key]}
            existing_perms[tool_key].update(patterns)
    existing["permission"] = existing_perms

    mcp_section = existing.get("mcp")
    if not isinstance(mcp_section, dict):
        mcp_section = {}
    # Use the absolute launcher path (~/.local/bin/hivemind, written by `make
    # install`). opencode spawns this as a subprocess and may not have
    # ~/.local/bin on its PATH (it inherits the parent process's PATH, which
    # depends on how the user launched opencode). Resolving the path here
    # eliminates that dependency entirely.
    launcher = str(Path.home() / ".local" / "bin" / "hivemind")
    mcp_section["hivemind"] = {
        "type": "local",
        "command": [launcher, "mcp"],
        "environment": {"PYTHONUNBUFFERED": "1"},
    }
    existing["mcp"] = mcp_section

    config_path.write_text(json.dumps(existing, indent=2) + "\n")
    results.append(InitResult(label="opencode.json", status="path-token permissions merged"))
    results.append(InitResult(label="opencode.json", status="mcp server registered"))

    # TUI plugins are no longer installed: their functionality (HIVEMIND
    # branding + connection indicator) is now baked into the bundled engine
    # via patches under //third_party/patches/. We still clean up any stale
    # plugin files from previous hivemind installs so leftover `file://`
    # entries in tui.json don't fail to load.
    _purge_legacy_tui_plugins(home, results)

    return results


def _purge_legacy_tui_plugins(home: Path, results: list[InitResult]) -> None:
    """Remove any tui-plugins/ entries hivemind shipped before the bun-vendor era."""
    legacy_stems = ("branding", "connection-indicator", "hivemind")
    plugins_dir = home / "tui-plugins"
    if plugins_dir.exists():
        removed: list[str] = []
        for child in plugins_dir.iterdir():
            if any(stem in child.name for stem in legacy_stems):
                child.unlink(missing_ok=True)
                removed.append(child.name)
        if removed:
            results.append(InitResult(label="tui-plugins/", status=f"removed legacy: {', '.join(removed)}"))

    tui_config_path = home / "tui.json"
    if tui_config_path.exists() and not tui_config_path.is_symlink():
        with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
            tui_existing: dict[str, Any] = json.loads(tui_config_path.read_text(encoding="utf-8"))
            raw_plugins = tui_existing.get("plugin", [])
            if isinstance(raw_plugins, list):
                filtered = [
                    p for p in raw_plugins if not (isinstance(p, str) and any(stem in p for stem in legacy_stems))
                ]
                if filtered != raw_plugins:
                    tui_existing["plugin"] = filtered
                    tui_config_path.write_text(json.dumps(tui_existing, indent=2) + "\n", encoding="utf-8")
                    results.append(InitResult(label="tui.json", status="legacy plugin entries purged"))


def _load_opencode_defaults() -> dict[str, Any]:
    """Load opencode/config/defaults.json bundled with this repo."""
    defaults_path = OPENCODE_CONFIG_DIR / "defaults.json"
    raw = json.loads(defaults_path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _substitute_path_tokens(permission_patterns: dict[str, Any]) -> dict[str, Any]:
    """Replace path tokens in permission patterns."""
    tokens = {
        "{CACHE_PATH}": cache_base_path(),
        "{EXPERTS_PATH}": experts_base_path(),
        "{TEAMS_PATH}": teams_base_path(),
    }

    def render(pattern: str) -> str:
        for token, value in tokens.items():
            pattern = pattern.replace(token, value)
        return pattern

    resolved: dict[str, Any] = {}
    for tool_key, patterns in permission_patterns.items():
        if isinstance(patterns, dict):
            resolved[tool_key] = {render(pat): verdict for pat, verdict in patterns.items()}
        else:
            resolved[tool_key] = patterns
    return resolved


# ---------------------------------------------------------------------------
# Symlink helper
# ---------------------------------------------------------------------------


def _setup_symlink(target: Path, link: Path, label: str) -> InitResult:
    """Create or refresh a symlink."""
    status = ""
    if link.is_symlink():
        current = link.resolve()
        if current == target.resolve():
            return InitResult(label=label, status="already correct")
        link.unlink()
    elif link.is_dir():
        backup = link.with_name(link.name + ".bak")
        link.rename(backup)
        status = f"backed up existing dir to {backup.name}/, "
    elif link.exists():
        link.unlink()

    link.symlink_to(target)
    return InitResult(label=label, status=f"{status}-> {target}")
