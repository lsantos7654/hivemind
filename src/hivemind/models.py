"""Shared data models for hivemind — config schemas, operation results, and core types."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime  # noqa: TC003 — Pydantic needs datetime at runtime for field validation
from enum import StrEnum
from pathlib import Path  # noqa: TC003 — Pydantic needs Path at runtime for field validation
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, model_validator

# --- Update Progress Types ---


class UpdatePhase(StrEnum):
    """Phases of the update process."""

    CLONING = "cloning"
    FETCHING = "fetching"
    CHECKING = "checking"
    STAGING = "staging"
    ANALYZING = "analyzing"
    COMMITTING = "committing"
    UPDATING_HEAD = "updating_head"
    UPDATING_LIBRARIAN = "updating_librarian"


class ProgressInfo(BaseModel):
    """Progress information for callbacks."""

    model_config = {"arbitrary_types_allowed": True}

    expert_name: str
    phase: UpdatePhase
    message: str
    progress_percent: int | None = None  # 0-100 for analysis phase
    new_commit: str | None = None
    old_commit: str | None = None
    error: str | None = None
    files_found: list[str] | None = None  # analysis files created so far


ProgressCallback = Callable[[ProgressInfo], None]


class CancellationToken:
    """Token to signal and check for cancellation."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Signal cancellation."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        return self._cancelled


# --- Config Models (matching JSON schemas) ---


class RepoEntry(BaseModel):
    """A git repository registration used by ``GitAnalyzedBody``."""

    remote: str
    commit: str = ""
    ref_name: str = ""


class TeamData(BaseModel):
    """A view of a ``RosterTemplatedBody`` agent for display callers.

    This is not the canonical storage format — the roster lives in
    ``config.json.teams`` (per-machine, gitignored). It exists for TUI
    screens that expect a typed object instead of a dict.
    """

    description: str = ""
    experts: list[str] = []


class ServerConfig(BaseModel):
    """OpenCode backend server configuration in hivemind.json."""

    port: int = 4096
    hostname: str = "127.0.0.1"


class ServerState(BaseModel):
    """Runtime state of a running OpenCode backend server.

    Persisted to ~/.cache/hivemind/server.json while the server is running.
    """

    pid: int
    port: int
    hostname: str
    provider: str
    started_at: datetime
    log_file: str


class GitAnalyzedParams(BaseModel):
    """Catalog params for the ``git_analyzed`` body kind."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    remote: str
    commit: str = ""
    ref_name: str = ""


class RosterTemplatedParams(BaseModel):
    """Catalog params for the ``roster_templated`` body kind."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    description: str = ""
    experts: list[str] = []


class UserSuppliedParams(BaseModel):
    """Catalog params for the ``user_supplied`` body kind.

    The agent body is a markdown file the user dropped into
    ``opencode/agents/``. Hivemind copies the file through verbatim on
    deploy — no AI analysis, no template merging. ``filename`` is the
    basename relative to ``opencode/agents/``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    filename: str


class SystemTemplatedParams(BaseModel):
    """Catalog params for the ``system_templated`` body kind.

    The agent body is rendered at deploy time from a Jinja template
    under ``src/hivemind/templates/``. Used for hivemind-managed worker
    agents (today: ``hivemind-expert-curator``) that are deployed
    alongside user-facing experts and teams but whose markdown is
    generated, not authored. ``template`` is the path passed to
    :func:`hivemind.templates.render` — typically ``"agents/<name>.md.j2"``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    template: str


BodyParams = GitAnalyzedParams | RosterTemplatedParams | UserSuppliedParams | SystemTemplatedParams


class CatalogEntry(BaseModel):
    """A single agent catalog entry in ``hivemind.json``.

    JSON shape is ``{"kind": "<kind>", "body": {...kind-specific params...}}``.
    The ``_dispatch_body`` validator picks the concrete ``BodyParams`` subclass
    based on ``kind`` before Pydantic runs the union validation, so a
    malformed body surfaces as a clear ``ValidationError`` at load time.
    """

    kind: str
    body: BodyParams

    @model_validator(mode="before")
    @classmethod
    def _dispatch_body(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        kind = data.get("kind")
        body = data.get("body")
        if not isinstance(body, dict):
            return data
        if kind == "git_analyzed":
            data = dict(data)
            data["body"] = GitAnalyzedParams.model_validate(body)
        elif kind == "roster_templated":
            data = dict(data)
            data["body"] = RosterTemplatedParams.model_validate(body)
        elif kind == "user_supplied":
            data = dict(data)
            data["body"] = UserSuppliedParams.model_validate(body)
        elif kind == "system_templated":
            data = dict(data)
            data["body"] = SystemTemplatedParams.model_validate(body)
        return data


class MemoryConfig(BaseModel):
    """``memory:`` section of ``hivemind.json`` — daemon trigger config.

    The compaction daemon (``hivemind-memory-daemon``) is auto-spawned
    by the file-write hook when an agent's ``short_memory.md`` crosses
    ``compaction_threshold_bytes``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    compaction_threshold_bytes: int = 8192


class HivemindConfig(BaseModel):
    """Full hivemind.json schema (committed to git; shared across teammates).

    The ``engine`` field is intentionally absent: hivemind is Bazel-native
    and resolves the engine binary at runtime from ``$HIVEMIND_ENGINE`` or
    ``src/hivemind/_bundled/hivemind-engine`` (see ``opencode._engine_path``).
    Any legacy ``engine`` value in ``hivemind.json`` is ignored.
    """

    model_config = ConfigDict(extra="ignore")

    home_dir: str = ""
    model: str = ""
    small_model: str = ""
    tools: dict[str, bool] = {}
    temperature: float | None = None
    server: ServerConfig = ServerConfig()
    permissions: dict[str, object] | None = None
    memory: MemoryConfig = MemoryConfig()
    agents: dict[str, CatalogEntry] = {}


class AppConfig(BaseModel):
    """Full config.json schema (per-machine local overlay, not committed)."""

    enabled: list[str] = []
    disabled: list[str] = []
    teams: dict[str, RosterTemplatedParams] = {}


# --- Operation Result Models ---


class OperationResult(BaseModel):
    """Base result for all operations.

    Invariant: ``error`` must be set when ``success=False`` and must be
    ``None`` when ``success=True``.  All subclasses inherit this validator.
    """

    success: bool
    error: str | None = None

    @model_validator(mode="after")
    def check_error_consistency(self) -> Self:
        if not self.success and self.error is None:
            msg = "error must be set when success=False"
            raise ValueError(msg)
        if self.success and self.error is not None:
            msg = "error must not be set when success=True"
            raise ValueError(msg)
        return self


class UpdateResult(OperationResult):
    new_commit: str = ""
    old_commit: str | None = None
    already_up_to_date: bool = False
    cancelled: bool = False


class PrepCreateResult(OperationResult):
    """Result of stage 1 (prep) of the git_analyzed create pipeline.

    The create pipeline has three stages: prep (clone + staging), analyze
    (generate the 6 knowledge files), and finalize (move staging into the
    catalog). Stage 1 returns this object so any of three analyzers can
    perform stage 2: the in-process subprocess (`run_async_analysis`), an
    opencode subagent that does the work in-session, or a human writing
    the files by hand. Pass this object back to ``finalize_create_expert``
    to land the agent in the catalog as *unlisted*.
    """

    name: str = ""
    url: str = ""
    ref_name: str = ""
    commit: str = ""
    repo_dir: Path | None = None
    commit_dir: Path | None = None
    staging_root: Path | None = None
    analysis_prompt: str = ""


class PrepUpdateResult(OperationResult):
    """Result of stage 1 (prep) of the git_analyzed update pipeline.

    Mirrors :class:`PrepCreateResult` but for updating an existing expert
    to its latest upstream commit. Update preserves the agent's
    ``description.md`` and ``expertise.md`` (they're staged in
    ``commit_dir`` from the prior commit before analysis runs), so stage
    2 only writes the 4 knowledge docs (per
    :func:`hivemind.analysis.expected_analysis_files` with
    ``is_update=True``).

    On the no-op path (``already_up_to_date=True``) the staging fields
    are unset — the caller skips analysis and treats the operation as
    complete.
    """

    name: str = ""
    new_commit: str = ""
    old_commit: str | None = None
    already_up_to_date: bool = False
    repo_dir: Path | None = None
    commit_dir: Path | None = None
    staging_root: Path | None = None
    analysis_prompt: str = ""


class PrepSwitchResult(OperationResult):
    """Result of stage 1 (prep) of the git_analyzed switch_version pipeline.

    Returned by ``prep_switch_version(name, ref)`` after resolving the
    ref to a full commit SHA and checking whether the target commit's
    analysis docs are already on disk.

    Two finalize paths:

    - ``cached=True``: docs are present at ``experts/<name>/<commit>/``.
      The staging fields are unset; ``finalize_switch_version`` repoints
      HEAD, updates body params, checks out the working tree, and fires
      the post-mutation hook. Sub-second.
    - ``cached=False``: a fresh analysis is needed. The staging fields
      are populated and ``analysis_prompt`` is the rendered
      create-expert prompt. The caller (curator subagent or subprocess)
      writes the 6 expected files into ``commit_dir`` then calls
      ``finalize_switch_version``.

    On the no-op path (``already_up_to_date=True``) — when the resolved
    ref is the agent's current HEAD — staging fields are unset and the
    caller treats the operation as complete.
    """

    name: str = ""
    target_commit: str = ""
    old_commit: str | None = None
    cached: bool = False
    already_up_to_date: bool = False
    repo_dir: Path | None = None
    commit_dir: Path | None = None
    staging_root: Path | None = None
    analysis_prompt: str = ""


class PrepCreateTeamResult(OperationResult):
    """Result of stage 1 (prep) of the roster_templated team-creation pipeline.

    Returned by ``prep_create_team(name, description, experts)`` after
    validating inputs and setting up a staging directory under
    ``STAGING_DIR``. The caller (curator subagent or subprocess
    composition) generates one ``## expert-<name>`` section per expert
    and writes each into the corresponding entry of ``expert_paths``.
    Pass this result to ``finalize_create_team`` to validate the
    section files, move them into the team's permanent directory under
    ``TEAMS_DIR``, write the description and notes stubs, and register
    the catalog entry as *unlisted*.

    ``expert_paths`` is a list of ``{name, summary_path, section_path}``
    dicts. ``summary_path`` is the existing expert's ``summary.md``
    that the analyzer reads as input; ``section_path`` is where the
    analyzer must write the generated ``## expert-<name>`` section.
    """

    name: str = ""
    description: str = ""
    experts: list[str] = []
    expert_paths: list[dict[str, str]] = []
    staging_root: Path | None = None


class EnableResult(OperationResult):
    already_enabled: bool = False


class DisableResult(OperationResult):
    already_disabled: bool = False


class RedeployResult(OperationResult):
    success: bool = True  # overridden by validator
    failed: list[str] = []
    teams_failed: list[str] = []
    experts_deployed: list[str] = []
    teams_deployed: list[str] = []

    @model_validator(mode="after")
    def derive_success(self) -> Self:
        has_failures = bool(self.failed or self.teams_failed)
        if has_failures and self.error is None:
            parts: list[str] = []
            if self.failed:
                parts.append(f"experts: {', '.join(self.failed)}")
            if self.teams_failed:
                parts.append(f"teams: {', '.join(self.teams_failed)}")
            self.error = f"Deploy failures -- {'; '.join(parts)}"
        # Derive success from error state: if error is set, we failed
        self.success = self.error is None
        return self


class ExpertError(BaseModel):
    """A failed expert operation with name and error message."""

    name: str
    error: str


class AddExpertsResult(OperationResult):
    added: list[str] = []
    skipped: list[str] = []
    failed: list[ExpertError] = []


# --- Internal Operation Types ---


class InitResult(BaseModel):
    """Result of an init_dirs step (label + status message)."""

    label: str
    status: str


class StagingResult(BaseModel):
    """Result of staging files for analysis."""

    model_config = {"arbitrary_types_allowed": True}

    tmpdir: str
    staged_path: Path
    commit_dir: Path


class AnalysisResult(BaseModel):
    """Result of an async AI analysis run."""

    model_config = {"arbitrary_types_allowed": True}

    success: bool
    error: str | None = None
    stderr_path: Path | None = None
    stdout_path: Path | None = None
