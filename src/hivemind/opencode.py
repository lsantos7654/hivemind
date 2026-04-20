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
import shlex
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
    OPENCODE_PLUGINS_DIR,
    TEAMS_DIR_PLACEHOLDER,
)
from hivemind.models import HivemindConfig, InitResult, OperationResult, ServerConfig
from hivemind.templates import LIBRARIAN_DESCRIPTION

log = logging.getLogger(__name__)

Kind = Literal["git_analyzed", "roster_templated", "librarian"]

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
    if not cfg.engine:
        errors.append("engine must be set")
    if not cfg.home_dir:
        errors.append("home_dir must be set")
    if not cfg.model:
        errors.append("model must be set")
    if errors:
        msg = f"Incomplete config: {'; '.join(errors)}. Check hivemind.json."
        raise RuntimeError(msg)

    _config_cache = cfg
    return _config_cache


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


def extract_description(body: str) -> str:
    """Extract description from agent.md body (first paragraph after h1 heading)."""
    lines = body.strip().splitlines()

    def _first_paragraph(start_idx: int) -> str:
        paragraph_lines: list[str] = []
        for line in lines[start_idx:]:
            stripped = line.strip()
            if not stripped and not paragraph_lines:
                continue
            if stripped.startswith("#") or (not stripped and paragraph_lines):
                break
            paragraph_lines.append(stripped)
        return " ".join(paragraph_lines)

    h1_idx = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if h1_idx is None:
        return ""

    result = _first_paragraph(h1_idx + 1)
    if result:
        return result

    for i, line in enumerate(lines):
        if line.strip().lower() == "## overview":
            result = _first_paragraph(i + 1)
            if result:
                return result

    return ""


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
            description=description,
            tools=dict(cfg.tools),
            body=body,
        )
    if kind == "roster_templated":
        tools = dict(cfg.tools)
        tools["edit"] = True
        return _build_frontmatter(
            description=description,
            tools=tools,
            extra_permissions=[f'"{teams_base_path()}/**": allow'],
            body=body,
        )
    if kind == "librarian":
        return _build_frontmatter(
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
    """Validate that the analysis engine binary and configured model are available.

    Result is cached per-process — the ``opencode models`` subprocess call is
    ~800 ms and the answer doesn't change without a config edit (which resets
    the cache via :func:`invalidate_config_cache`).
    """
    global _engine_validated
    if _engine_validated:
        return OperationResult(success=True)

    cfg = _cfg()
    if not cfg.engine:
        return OperationResult(
            success=False,
            error="No engine configured. Set 'engine' in hivemind.json.",
        )

    binary = shlex.split(cfg.engine)[0]
    if not shutil.which(binary):
        return OperationResult(
            success=False,
            error=f"Analysis engine '{binary}' not found on PATH. Install it first.",
        )

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
                "Run 'opencode providers' to configure it.\n"
                "Available models can be listed with 'opencode models'."
            ),
        )

    _engine_validated = True
    return OperationResult(success=True)


def build_analysis_command(
    *,
    extra_dirs: list[Path] | None = None,
    write: bool = False,
) -> list[str]:
    """Build an opencode subprocess command for AI analysis runs."""
    cfg = _cfg()
    cmd = shlex.split(cfg.engine)
    cmd.extend(["--model", cfg.model])

    if extra_dirs:
        import os

        resolved = [str(d.resolve()) for d in extra_dirs if d.exists()]
        if resolved:
            common = os.path.commonpath(resolved)
            cmd.extend(["--dir", common])

    return cmd


def build_query_command() -> list[str]:
    """Build an opencode subprocess command for librarian queries."""
    cfg = _cfg()
    cmd = shlex.split(cfg.engine)
    cmd.extend(["--model", cfg.model])
    return cmd


# ---------------------------------------------------------------------------
# Server lifecycle commands
# ---------------------------------------------------------------------------


def start_server_command(port: int, hostname: str) -> list[str]:
    binary = shlex.split(_cfg().engine)[0]
    return [binary, "serve", "--port", str(port), "--hostname", hostname]


def launch_command(extra_args: list[str] | None = None) -> list[str]:
    binary = shlex.split(_cfg().engine)[0]
    return [binary, *(extra_args or [])]


def attach_command(server_url: str, extra_args: list[str] | None = None) -> list[str]:
    binary = shlex.split(_cfg().engine)[0]
    if extra_args:
        return [binary, "run", "--attach", server_url, *extra_args]
    return [binary, "attach", server_url]


def health_check_url(port: int, hostname: str) -> str:
    return f"http://{hostname}:{port}/global/health"


def notify_instance_reload() -> bool:
    """POST /global/dispose on the running opencode server.

    Uses the global endpoint rather than /instance/dispose so that every
    cached InstanceState (agent registry, plugins, skills, ...) for every
    directory the server has seen gets invalidated. Fire-and-forget —
    returns False if no server is running.
    """
    from hivemind.runtime import current_context

    ctx = current_context()
    if ctx.server_url is None:
        return False

    try:
        resp = httpx.post(f"{ctx.server_url}/global/dispose", timeout=5.0)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        log.debug("Failed to notify OpenCode server at %s", ctx.server_url)
        return False


# ---------------------------------------------------------------------------
# Directory initialisation
# ---------------------------------------------------------------------------


def init_dirs(
    *,
    agents_dir: Path,
    commands_dir: Path,
    rules_source: Path,
    teams_dir: Path | None = None,
) -> list[InitResult]:
    """Initialize the opencode directory structure.

    Sets up symlinks for agents/, commands/, rules, experts/ (real dir), and
    teams/, then merges opencode-specific defaults (hardening + permissions +
    MCP registration) and deploys bundled TUI plugins.
    """
    results: list[InitResult] = []

    home = home_dir()
    home.mkdir(parents=True, exist_ok=True)

    results.append(_setup_symlink(agents_dir, home / "agents", "agents/"))
    results.append(_setup_symlink(commands_dir, home / "commands", "commands/"))
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
    """Apply bundled opencode defaults + install TUI plugins."""
    results: list[InitResult] = []
    home = home_dir()

    defaults = _load_opencode_defaults()
    hardening = defaults.get("hardening", {})
    permissions_section = _substitute_path_tokens(defaults.get("permissions", {}))

    config_path = home / "opencode.json"
    existing: dict[str, Any] = {}
    if config_path.exists() and not config_path.is_symlink():
        with contextlib.suppress(FileNotFoundError):
            existing = json.loads(config_path.read_text(encoding="utf-8"))

    for key, value in hardening.items():
        if isinstance(value, dict):
            raw = existing.get(key)
            merged: dict[str, object] = raw if isinstance(raw, dict) else {}
            merged.update(value)
            existing[key] = merged
        else:
            existing[key] = value

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
    mcp_section["hivemind"] = {
        "type": "local",
        "command": ["hivemind", "mcp"],
        "environment": {"PYTHONUNBUFFERED": "1"},
    }
    existing["mcp"] = mcp_section

    config_path.write_text(json.dumps(existing, indent=2) + "\n")
    results.append(InitResult(label="opencode.json", status="hardening + permissions merged"))
    results.append(InitResult(label="opencode.json", status="mcp server registered"))

    plugins_dir = home / "tui-plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    installed_plugin_paths: list[Path] = []
    for source in sorted(OPENCODE_PLUGINS_DIR.glob("*.js")):
        dest = plugins_dir / source.name
        shutil.copyfile(source, dest)
        installed_plugin_paths.append(dest)
        results.append(InitResult(label=source.name, status="plugin deployed"))

    if installed_plugin_paths:
        tui_config_path = home / "tui.json"
        tui_existing: dict[str, Any] = {}
        if tui_config_path.exists() and not tui_config_path.is_symlink():
            with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
                tui_existing = json.loads(tui_config_path.read_text(encoding="utf-8"))

        raw_plugins = tui_existing.get("plugin", [])
        tui_plugins: list[object] = raw_plugins if isinstance(raw_plugins, list) else []
        bundled_stems = {p.stem for p in installed_plugin_paths}
        tui_plugins = [p for p in tui_plugins if not (isinstance(p, str) and any(stem in p for stem in bundled_stems))]
        for plugin_path in installed_plugin_paths:
            tui_plugins.append(f"file://{plugin_path}")
        tui_existing["plugin"] = tui_plugins
        tui_config_path.write_text(json.dumps(tui_existing, indent=2) + "\n", encoding="utf-8")
        results.append(InitResult(label="tui.json", status="plugins registered"))

    return results


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
