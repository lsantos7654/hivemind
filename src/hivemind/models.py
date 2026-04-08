"""Shared data models for hivemind — config schemas, operation results, and core types."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from pathlib import Path  # noqa: TC003 — Pydantic needs Path at runtime for field validation

from pydantic import BaseModel

# --- Update Progress Types ---


class UpdatePhase(str, Enum):
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


class ProviderSettings(BaseModel):
    """Provider-specific settings."""

    model: str = ""
    tools: list[str] | dict[str, bool] = []
    temperature: float | None = None


class ProviderConfig(BaseModel):
    """Provider configuration from hivemind.json."""

    engine: str = ""
    home_dir: str = ""
    settings: ProviderSettings = ProviderSettings()
    permissions: dict[str, object] | None = None


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
    """Base result for all operations."""

    success: bool
    error: str | None = None


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
    failed: list[str] = []
    experts_deployed: list[str] = []
    teams_deployed: list[str] = []


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


class SymlinkCheck(BaseModel):
    """Symlink verification entry for status dashboard."""

    model_config = {"arbitrary_types_allowed": True}

    display_name: str
    expected_target: Path
    link_path: Path


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
