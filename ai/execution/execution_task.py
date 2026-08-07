"""
ExecutionTask — extended task dataclass with execution metadata.

Extends the base Task dataclass with execution-specific fields
needed by the Execution Engine. Maintains compatibility with
existing Task while adding monitoring and reporting features.

All execution tasks flow through the ExecutionEngine and
are tracked by the ExecutionMonitor.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ai.engine.task import Task, TaskStatus, TaskPriority, TaskComplexity
from .task_state import TaskState, TaskStateHistory, StateTransition
from .task_state import TaskState, TaskStateHistory


class ExecutionMode(str, Enum):
    """Execution mode for a task."""
    FOREGROUND   = "foreground"   # Blocks calling thread
    BACKGROUND   = "background"   # Runs in executor pool
    MONITOR_ONLY = "monitor_only" # Only monitor, no execution


class RetryStrategy(str, Enum):
    """Strategy for handling task retries."""
    FIXED      = "fixed"       # Fixed delay between retries
    EXPONENTIAL = "exponential" # Exponential backoff
    JITTERED   = "jittered"    # Exponential + random jitter
    NONE       = "none"        # No retries


@dataclass
class ExecutionConfig:
    """
    Execution configuration for a task.
    
    Attributes:
        mode:           Execution mode (foreground/background/monitor_only)
        max_retries:    Maximum retry attempts
        retry_strategy: Strategy for timing between retries
        timeout_secs:   Maximum execution time before timeout
        priority:       Execution priority (overrides Task.priority)
        depends_on:     IDs of tasks this depends on
        group:          Task group name for parallel execution
        cancel_on_error: Stop entire group on error
    """
    mode:           ExecutionMode  = ExecutionMode.BACKGROUND
    max_retries:    int            = 2
    retry_strategy: RetryStrategy  = RetryStrategy.EXPONENTIAL
    timeout_secs:   Optional[int]  = None
    priority:       Optional[int]  = None  # None = use Task.priority
    depends_on:     List[str]      = field(default_factory=list)
    group:          Optional[str]  = None
    cancel_on_error: bool          = True


@dataclass
class ExecutionResult:
    """
    Result of a single execution attempt.
    
    Attributes:
        step_index:    Index of step in plan
        step_text:     Original step description
        success:       True if step succeeded
        output:        Step output data
        error:         Error message if failed
        duration_ms:   Execution time
        attempt:       Attempt number (1 = first)
        model_used:    Model used for this step
        tools_used:    Tools called during step
        verification:  Verification result if applicable
    """
    step_index:   int
    step_text:    str
    success:      bool
    output:       Any = None
    error:        Optional[str] = None
    duration_ms:  float = 0.0
    attempt:      int = 1
    model_used:   Optional[str] = None
    tools_used:   List[str] = field(default_factory=list)
    verification: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionStats:
    """
    Execution statistics for a task.
    
    Attributes:
        total_duration_ms:   Full execution time
        model_time_ms:       Total time waiting for model responses
        context_time_ms:     Total time building context
        verification_time_ms: Total time for verification
        tool_time_ms:        Total time spent in tools
        retry_count:         Number of retries performed
        steps_executed:      Number of steps actually executed
        files_modified:      List of modified file paths
        files_created:       List of created file paths
        files_deleted:       List of deleted file paths
    """
    total_duration_ms:   float = 0.0
    model_time_ms:       float = 0.0
    context_time_ms:     float = 0.0
    verification_time_ms: float = 0.0
    tool_time_ms:        float = 0.0
    retry_count:         int = 0
    steps_executed:      int = 0
    files_modified:      List[str] = field(default_factory=list)
    files_created:       List[str] = field(default_factory=list)
    files_deleted:       List[str] = field(default_factory=list)


@dataclass
class ExecutionTask:
    """
    Extended task with execution engine metadata.
    
    Wraps a base Task and adds:
    - State machine tracking
    - Execution configuration
    - Execution history
    - Performance metrics
    - Audit trail
    
    This is the unit of work that flows through the
    ExecutionEngine, TaskScheduler, and TaskExecutor.
    
    Attributes:
        task:          Base Task object (for compatibility)
        state_history: State machine history
        config:        Execution configuration
        results:       Step-by-step execution results
        stats:         Aggregated statistics
        created_time:  When task was created
        scheduled_time: When task entered SCHEDULED state
        started_time:  When task entered RUNNING state
        completed_time: When task reached terminal state
        error:         Final error message (if failed)
        cancelled_by:  User who cancelled (if cancelled)
    """
    # ── Wrapped task (for compatibility) ─────────────────────────────────────
    task: Task
    
    # ── State machine ────────────────────────────────────────────────────────
    state_history: TaskStateHistory = field(default_factory=TaskStateHistory)
    
    # ── Configuration ────────────────────────────────────────────────────────
    config: ExecutionConfig = field(default_factory=ExecutionConfig)
    
    # ── Execution history ────────────────────────────────────────────────────
    results: List[ExecutionResult] = field(default_factory=list)
    
    # ── Statistics ───────────────────────────────────────────────────────────
    stats: ExecutionStats = field(default_factory=ExecutionStats)
    
    # ── Timing ───────────────────────────────────────────────────────────────
    created_time:    datetime = field(default_factory=datetime.utcnow)
    scheduled_time:  Optional[datetime] = None
    started_time:    Optional[datetime] = None
    completed_time:  Optional[datetime] = None
    
    # ── Terminal state info ──────────────────────────────────────────────────
    error:         Optional[str] = None
    cancelled_by:  Optional[str] = None
    
    @property
    def id(self) -> str:
        """Return task ID (from wrapped task)."""
        return self.task.id
    
    @property
    def state(self) -> TaskState:
        """Return current state (from state history)."""
        return self.state_history.current_state
    
    @property
    def is_terminal(self) -> bool:
        """Return True if task has reached a terminal state."""
        return self.state_history.is_terminal
    
    @property
    def success(self) -> bool:
        """Return True if task succeeded."""
        return self.state == TaskState.SUCCESS
    
    @property
    def status(self) -> TaskStatus:
        """Return TaskStatus enum for compatibility."""
        mapping = {
            TaskState.PENDING:    TaskStatus.PENDING,
            TaskState.SCHEDULED:  TaskStatus.PENDING,
            TaskState.RUNNING:    TaskStatus.EXECUTING,
            TaskState.PAUSED:     TaskStatus.PENDING,
            TaskState.SUCCESS:    TaskStatus.COMPLETED,
            TaskState.FAILED:     TaskStatus.FAILED,
            TaskState.CANCELLED:  TaskStatus.CANCELLED,
            TaskState.EXPIRED:    TaskStatus.FAILED,
        }
        return mapping.get(self.state, TaskStatus.PENDING)
    
    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        return {
            "id": self.id,
            "title": self.task.title,
            "status": self.status.value,
            "state": self.state.value,
            "created_time": self.created_time.isoformat(),
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "started_time": self.started_time.isoformat() if self.started_time else None,
            "completed_time": self.completed_time.isoformat() if self.completed_time else None,
            "config": {
                "mode": self.config.mode.value,
                "max_retries": self.config.max_retries,
                "retry_strategy": self.config.retry_strategy.value,
                "timeout_secs": self.config.timeout_secs,
                "priority": self.config.priority,
                "group": self.config.group,
                "cancel_on_error": self.config.cancel_on_error,
            },
            "stats": {
                "total_duration_ms": self.stats.total_duration_ms,
                "model_time_ms": self.stats.model_time_ms,
                "retry_count": self.stats.retry_count,
                "steps_executed": self.stats.steps_executed,
            },
            "results_count": len(self.results),
        }
    
    def __repr__(self) -> str:
        return (
            f"ExecutionTask(id={self.id[:8]}..., title={self.task.title!r}, "
            f"state={self.state.value}, status={self.status.value})"
        )


def create_execution_task(prompt: str, config: Optional[ExecutionConfig] = None) -> ExecutionTask:
    """
    Factory function to create a new ExecutionTask.
    
    Args:
        prompt: User prompt text
        config: Optional execution configuration
        
    Returns:
        New ExecutionTask with PENDING state
    """
    base_task = Task(original_prompt=prompt)
    task = ExecutionTask(task=base_task, config=config or ExecutionConfig())
    
    # Initial state transition
    task.state_history.add_transition(
        StateTransition(
            from_state=None,
            to_state=TaskState.PENDING,
            timestamp=datetime.utcnow(),
            reason="Task created",
        )
    )
    
    return task
