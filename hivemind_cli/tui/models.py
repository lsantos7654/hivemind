"""Data models for the TUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    operation_status: OperationStatus | None = None  # Track if operation is in progress
    status_message: str | None = None  # Detailed progress message for display


@dataclass
class OperationProgress:
    """Tracks progress of an individual operation."""

    expert_name: str
    status: OperationStatus
    phase: str
    progress: int  # 0-100
    error_msg: str | None = None


@dataclass
class VersionInfo:
    """Information about a git version (tag or commit)."""

    commit: str
    type: str  # "tag" or "commit"
    name: str  # tag name or commit message
    date: str
    analyzed: bool
