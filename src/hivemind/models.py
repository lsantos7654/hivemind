"""Shared data models for hivemind — config schemas, operation results, and core types."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime  # noqa: TC003 — Pydantic needs datetime at runtime for field validation
from enum import StrEnum
from pathlib import Path  # noqa: TC003 — Pydantic needs Path at runtime for field validation
from typing import Self

from pydantic import BaseModel, ValidationInfo, model_validator

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
    """A repository registration in hivemind.json."""

    remote: str
    commit: str = ""
    ref_name: str = ""


class TeamData(BaseModel):
    """A team definition in config.json."""

    description: str
    experts: list[str] = []


class ServerConfig(BaseModel):
    """Provider backend server configuration in hivemind.json."""

    port: int = 4096
    hostname: str = "127.0.0.1"


class ServerState(BaseModel):
    """Runtime state of a running provider backend server.

    Persisted to ~/.cache/hivemind/server.json while the server is running.
    """

    pid: int
    port: int
    hostname: str
    provider: str
    started_at: datetime
    log_file: str


class ProviderSettings(BaseModel):
    """Provider-specific settings."""

    model: str = ""
    tools: list[str] | dict[str, bool] = []
    temperature: float | None = None


class ProviderConfig(BaseModel):
    """Provider configuration from hivemind.json.

    Fields default to empty strings because inactive providers in hivemind.json
    may have incomplete config.  Use ``context={'strict': True}`` when loading
    the *active* provider to enforce that required fields are set.
    """

    engine: str = ""
    home_dir: str = ""
    settings: ProviderSettings = ProviderSettings()
    server: ServerConfig = ServerConfig()
    permissions: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_when_active(self, info: ValidationInfo) -> Self:
        """Enforce completeness only when the provider is being activated."""
        if not (info.context and info.context.get("strict")):
            return self
        errors: list[str] = []
        if not self.engine:
            errors.append("engine must be set")
        if not self.home_dir:
            errors.append("home_dir must be set")
        if not self.settings.model:
            errors.append("settings.model must be set")
        if errors:
            msg = f"Incomplete provider config: {'; '.join(errors)}. Check hivemind.json."
            raise ValueError(msg)
        return self


class HivemindConfig(BaseModel):
    """Full hivemind.json schema."""

    providers: dict[str, ProviderConfig] = {}
    repos: dict[str, RepoEntry] = {}


class AppConfig(BaseModel):
    """Full config.json schema."""

    enabled: list[str] = []
    disabled: list[str] = []
    active_provider: str = ""
    teams: dict[str, TeamData] = {}
    private: list[str] = []


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


class SwitchProviderResult(OperationResult):
    old_provider: str = ""
    new_provider: str = ""
    already_active: bool = False


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


class RepoLookup(BaseModel):
    """Result of looking up repos for an expert."""

    repos: dict[str, RepoEntry]
    is_private: bool
