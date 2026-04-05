"""Data models for the TUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hivemind_cli.models import CancellationToken


class WorkerInfo:
    """Tracks an active worker's cancellation token and subprocess PID."""

    def __init__(self, token: CancellationToken, pid: int | None = None) -> None:
        self.token = token
        self.pid = pid


class ExpertStatus(str, Enum):
    """Expert status enumeration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLISTED = "unlisted"


class OperationStatus(str, Enum):
    """Operation status enumeration."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


@dataclass
class ExpertRow:
    """Represents a single expert in the table."""

    name: str
    status: ExpertStatus
    commit: str | None
    version_count: int
    has_agent: bool
    remote: str
    ref_name: str
    is_private: bool = False
    operation_status: OperationStatus | None = None  # Track if operation is in progress
    status_message: str | None = None  # Detailed progress message for display


@dataclass
class VersionInfo:
    """Information about a git version (tag or commit)."""

    commit: str
    type: str  # "tag" or "commit"
    name: str  # tag name or commit message
    date: str
    analyzed: bool
    is_active: bool = False  # True if this is current HEAD
