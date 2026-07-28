"""
Task dataclass — the universal unit of work.

Every user request is converted into a Task object.
This object is the standard format passed between all engine
components: TaskAnalyzer → Planner → ExecutionManager → Memory.

By centralizing the task definition here, every component works
on the same well-typed, serializable structure rather than raw
dictionaries or loose strings.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TaskStatus(str, Enum):
    """Lifecycle states a Task can occupy."""
    PENDING    = "pending"     # Just created, not yet analyzed
    ANALYZING  = "analyzing"   # TaskAnalyzer is working
    PLANNING   = "planning"    # PlannerAgent is working
    EXECUTING  = "executing"   # ExecutionManager is running steps
    COMPLETED  = "completed"   # Finished successfully
    FAILED     = "failed"      # Stopped due to an unrecoverable error
    CANCELLED  = "cancelled"   # Stopped by the user


class TaskPriority(str, Enum):
    """Execution priority levels."""
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"


class TaskComplexity(str, Enum):
    """Estimated complexity levels assigned by TaskAnalyzer."""
    SIMPLE   = "simple"    # Single-file edits, trivial commands
    MODERATE = "moderate"  # Multi-file changes, single-agent tasks
    COMPLEX  = "complex"   # Multi-agent, multi-step workflows
    EXPERT   = "expert"    # Requires planning, internet, and iteration


@dataclass
class Task:
    """
    The universal unit of work in MyCodingMaster.

    A Task is created from a raw user prompt by the TaskAnalyzer
    and is enriched as it passes through the pipeline. All engine
    components communicate by reading and writing to this object.

    Attributes:
        id:                   Unique identifier (UUID4 string).
        title:                Short human-readable label for the task.
        original_prompt:      The exact text the user typed.
        objective:            Cleaned, clarified goal extracted from the prompt.
        status:               Current lifecycle state of the task.
        priority:             Execution priority assigned during analysis.
        estimated_complexity: Complexity level assigned during analysis.
        required_tools:       Names of tools the task will need (e.g. "file", "terminal").
        required_models:      Model identifiers needed (e.g. "gemini", "qwen").
        created_time:         UTC timestamp when the Task was instantiated.
        completed_time:       UTC timestamp when the Task reached a terminal state.
        plan:                 Ordered list of step strings set by PlannerAgent.
        metadata:             Arbitrary key-value pairs for future extensibility.
    """

    # --- Core Identity ---
    original_prompt: str
    title: str = ""
    objective: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # --- State ---
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_complexity: TaskComplexity = TaskComplexity.SIMPLE

    # --- Requirements (populated by TaskAnalyzer) ---
    required_tools: List[str]  = field(default_factory=list)
    required_models: List[str] = field(default_factory=list)

    # --- Detected Context (populated by TaskAnalyzer) ---
    detected_language:  Optional[str] = None
    detected_framework: Optional[str] = None
    detected_project_type: Optional[str] = None
    needs_planning:    bool = False
    needs_internet:    bool = False
    needs_terminal:    bool = False
    needs_file_write:  bool = False

    @property
    def requires_code_changes(self) -> bool:
        """True when the task implies writing or modifying source files."""
        return self.needs_file_write or self.estimated_complexity in (
            TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.EXPERT
        )

    # --- Timing ---
    created_time: datetime   = field(default_factory=datetime.utcnow)
    completed_time: Optional[datetime] = None

    # --- Execution Artefacts ---
    plan: List[str]            = field(default_factory=list)
    metadata: dict             = field(default_factory=dict)

    def mark_completed(self) -> None:
        """Mark the task as successfully completed and record the timestamp."""
        self.status = TaskStatus.COMPLETED
        self.completed_time = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark the task as failed and record the timestamp."""
        self.status = TaskStatus.FAILED
        self.completed_time = datetime.utcnow()

    def is_terminal(self) -> bool:
        """Return True if the Task has reached a final, non-resumable state."""
        return self.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id[:8]}..., title={self.title!r}, "
            f"status={self.status.value}, priority={self.priority.value})"
        )
