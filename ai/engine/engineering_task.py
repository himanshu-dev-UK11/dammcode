"""
EngineeringTask — Autonomous Engineering Task definition.

Extends the base Task/ExecutionTask concept to provide granular
details required for an autonomous engineering workflow. 
Each engineering task represents a specific sub-step in a larger plan.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ai.engine.task import TaskPriority, TaskStatus


class EngineeringTaskStatus(str, Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"
    CANCELLED  = "cancelled"
    RETRYING   = "retrying"


@dataclass
class EngineeringTask:
    """
    An autonomous engineering task representing a single step in a plan.

    Attributes:
        id:                 Unique identifier.
        title:              Short title of the task.
        description:        Detailed description of what needs to be done.
        priority:           Priority of this specific task.
        status:             Current execution status.
        dependencies:       List of task IDs this task depends on.
        affected_files:     List of files this task is expected to modify.
        estimated_duration: Estimated duration in seconds.
        actual_duration:    Actual duration in seconds.
        assigned_model:     The AI model assigned to execute this task.
        verification_state: Status of the verification (e.g. 'unverified', 'passed', 'failed').
        retry_count:        Number of times this task has been retried.
        logs:               List of specific engineering logs (reasoning summary, files changed, tool calls, etc).
    """

    id:                 str = field(default_factory=lambda: str(uuid.uuid4()))
    title:              str = ""
    description:        str = ""
    priority:           TaskPriority = TaskPriority.MEDIUM
    status:             EngineeringTaskStatus = EngineeringTaskStatus.PENDING
    dependencies:       List[str] = field(default_factory=list)
    affected_files:     List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None
    actual_duration:    Optional[int] = None
    assigned_model:     Optional[str] = None
    verification_state: str = "unverified"
    retry_count:        int = 0
    logs:               List[Dict[str, Any]] = field(default_factory=list)

    def add_log(self, reasoning: str = "", files_changed: List[str] = None, 
                tool_calls: List[str] = None, verification_result: str = "", 
                execution_time_ms: float = 0.0):
        """Append an engineering-specific log entry."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning_summary": reasoning,
            "files_changed": files_changed or [],
            "tool_calls": tool_calls or [],
            "verification_result": verification_result,
            "execution_time_ms": execution_time_ms
        })

