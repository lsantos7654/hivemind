"""Shared data models for hivemind — config schemas, operation results, and core types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import IO, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

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


@dataclass
class ProgressInfo:
    """Progress information for callbacks."""

    expert_name: str
    phase: UpdatePhase
    message: str
    progress_percent: int | None = None  # 0-100 for analysis phase
    new_commit: str | None = None
    old_commit: str | None = None
    error: str | None = None


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


@dataclass
class AnalysisHandle:
    """Handle for a running analysis subprocess, allowing progress monitoring."""

    proc: subprocess.Popen[bytes]
    commit_dir: Path
    expected_files: list[str]
    stderr_path: Path
    stdout_path: Path
    _stderr_file: IO[str] | None = None  # kept open until finish
    _stdout_file: IO[str] | None = None


# --- Config Models (matching JSON schemas) ---


@dataclass
class RepoEntry:
    """A repository registration in hivemind.json."""

    remote: str
    commit: str = ""
    ref_name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoEntry:
        return cls(
            remote=data.get("remote", ""),
            commit=data.get("commit", ""),
            ref_name=data.get("ref_name", ""),
        )


@dataclass
class TeamData:
    """A team definition in config.json."""

    description: str
    experts: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeamData:
        return cls(
            description=data.get("description", ""),
            experts=list(data.get("experts", [])),
        )


@dataclass
class ProviderSettings:
    """Provider-specific settings."""

    model: str = ""
    tools: list[str] | dict[str, bool] = field(default_factory=list)
    temperature: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderSettings:
        raw_tools = data.get("tools", [])
        # tools can be list[str] (claude) or dict[str, bool] (opencode)
        if isinstance(raw_tools, dict):
            tools: list[str] | dict[str, bool] = dict(raw_tools)
        else:
            tools = list(raw_tools)
        return cls(
            model=data.get("model", ""),
            tools=tools,
            temperature=data.get("temperature"),
        )


@dataclass
class ProviderConfig:
    """Provider configuration from hivemind.json."""

    engine: str = ""
    home_dir: str = ""
    settings: ProviderSettings = field(default_factory=ProviderSettings)
    permissions: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderConfig:
        return cls(
            engine=data.get("engine", ""),
            home_dir=data.get("home_dir", ""),
            settings=ProviderSettings.from_dict(data.get("settings", {})),
            permissions=data.get("permissions"),
        )


@dataclass
class HivemindConfig:
    """Full hivemind.json schema."""

    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    repos: dict[str, RepoEntry] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HivemindConfig:
        return cls(
            providers={k: ProviderConfig.from_dict(v) for k, v in data.get("providers", {}).items()},
            repos={k: RepoEntry.from_dict(v) for k, v in data.get("repos", {}).items()},
        )


@dataclass
class AppConfig:
    """Full config.json schema."""

    enabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    active_provider: str = ""
    teams: dict[str, TeamData] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        return cls(
            enabled=list(data.get("enabled", [])),
            disabled=list(data.get("disabled", [])),
            active_provider=data.get("active_provider", ""),
            teams={k: TeamData.from_dict(v) for k, v in data.get("teams", {}).items()},
        )


# --- Operation Result Models ---


@dataclass
class OperationResult:
    """Base result for all operations."""

    success: bool
    error: str | None = None


@dataclass
class UpdateResult(OperationResult):
    new_commit: str = ""
    old_commit: str | None = None
    already_up_to_date: bool = False
    cancelled: bool = False


@dataclass
class EnableResult(OperationResult):
    already_enabled: bool = False


@dataclass
class DisableResult(OperationResult):
    already_disabled: bool = False


@dataclass
class RedeployResult(OperationResult):
    failed: list[str] = field(default_factory=list)
    experts_deployed: list[str] = field(default_factory=list)
    teams_deployed: list[str] = field(default_factory=list)


@dataclass
class SwitchProviderResult(OperationResult):
    old_provider: str = ""
    new_provider: str = ""
    already_active: bool = False
