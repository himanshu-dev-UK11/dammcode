"""
change_request.py — Dataclass representing an AI code modification request.

This is the input contract that flows from Model Manager into the
editing pipeline. It captures what the AI wants to do, why, and
which files are affected.

All fields are immutable to ensure request integrity throughout
the pipeline. Once created, a ChangeRequest cannot be changed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class ChangePriority(Enum):
    """Priority levels for code change requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeStatus(Enum):
    """Status of a change request in the pipeline."""
    PENDING = "pending"
    VALIDATING = "validating"
    PREVIEW_READY = "preview_ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class ChangeRequest:
    """
    Represents a request from an AI model to modify files.

    Attributes:
        request_id:    Unique identifier for this request.
        user_prompt:   The original user request that triggered this change.
        files:         List of absolute file paths to be modified.
        changes:       Detailed change descriptions (diff hunks).
        reason:        Human-readable explanation of what is being changed.
        priority:      Importance level for scheduling.
        timestamp:     When this request was created.
        status:        Current state in the editing pipeline.
        metadata:      Arbitrary extra data (e.g., model name, confidence).
        rollback_id:   ID of the rollback point created before this change.
    """

    request_id:     str
    user_prompt:    str
    files:          List[str]
    changes:        List[Dict[str, Any]]
    reason:         str
    priority:       ChangePriority
    timestamp:      datetime
    status:         ChangeStatus
    metadata:       Dict[str, Any] = field(default_factory=dict)
    rollback_id:    Optional[str] = None

    # Class-level counter for sequential request IDs
    _counter: int = 0

    @classmethod
    def create(
        cls,
        user_prompt:  str,
        files:        List[str],
        changes:      List[Dict[str, Any]],
        reason:       str,
        priority:     ChangePriority = ChangePriority.NORMAL,
        metadata:     Optional[Dict[str, Any]] = None,
    ) -> ChangeRequest:
        """
        Create a new ChangeRequest with automatic ID generation.

        Args:
            user_prompt: The original user request.
            files:       List of affected file paths.
            changes:     List of change hunks (dicts with 'type', 'old', 'new').
            reason:      Explanation of the changes.
            priority:    Request priority (default: NORMAL).
            metadata:    Extra data for tracking (default: empty dict).
        """
        cls._counter += 1

        return cls(
            request_id=f"req_{cls._counter:06d}_{uuid.uuid4().hex[:8]}",
            user_prompt=user_prompt,
            files=files,
            changes=changes,
            reason=reason,
            priority=priority,
            timestamp=datetime.now(),
            status=ChangeStatus.PENDING,
            metadata=metadata or {},
            rollback_id=None,
        )

    def with_status(self, status: ChangeStatus) -> ChangeRequest:
        """Return a copy of this request with updated status."""
        return dataclasses_replace(
            self,
            status=status,
        )

    def with_metadata(self, key: str, value: Any) -> ChangeRequest:
        """Return a copy with an updated metadata entry."""
        new_metadata = dict(self.metadata)
        new_metadata[key] = value
        return dataclasses_replace(
            self,
            metadata=new_metadata,
        )

    def with_rollback_id(self, rollback_id: str) -> ChangeRequest:
        """Return a copy with the rollback ID set."""
        return dataclasses_replace(
            self,
            status=ChangeStatus.PREVIEW_READY,
            rollback_id=rollback_id,
        )


# Helper to replace dataclass fields immutably
def dataclasses_replace(instance, **changes):
    """Replacement for dataclasses.replace that works across Python versions."""
    import dataclasses
    return dataclasses.replace(instance, **changes)


def make_request_id() -> str:
    """Generate a unique request ID with timestamp."""
    import time
    ts = int(time.time() * 1000)
    return f"req_{ts:013d}_{uuid.uuid4().hex[:8]}"