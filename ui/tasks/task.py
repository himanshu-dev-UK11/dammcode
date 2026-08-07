"""
Task System — Task Model

Represents a task that can be executed in the terminal.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Task type classification."""
    DEFAULT = "default"      # Auto-detected default task
    CUSTOM = "custom"        # User-defined custom task
    BUILD = "build"          # Build task
    TEST = "test"            # Test task
    LINT = "lint"            # Lint task
    FORMAT = "format"        # Format task
    RUN = "run"              # Run task
    DEBUG = "debug"          # Debug task (placeholder)
    CLEAN = "clean"          # Clean task
    INSTALL = "install"      # Install dependencies
    UPDATE = "update"        # Update dependencies
    PACKAGE = "package"      # Package/deploy task


@dataclass
class Task:
    """Represents a task that can be executed in the terminal."""
    
    # Basic identification
    id: str
    name: str
    command: str
    task_type: TaskType
    
    # Execution context
    working_directory: str
    shell: str = "cmd"
    
    # Execution state
    status: TaskStatus = TaskStatus.QUEUED
    exit_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Configuration
    environment: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    # UI preferences
    is_pinned: bool = False
    is_favorite: bool = False
    order: int = 0
    
    # History
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "task_type": self.task_type.value,
            "working_directory": self.working_directory,
            "shell": self.shell,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "environment": self.environment,
            "description": self.description,
            "is_pinned": self.is_pinned,
            "is_favorite": self.is_favorite,
            "order": self.order,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            command=data["command"],
            task_type=TaskType(data.get("task_type", "default")),
            working_directory=data["working_directory"],
            shell=data.get("shell", "cmd"),
            status=TaskStatus(data.get("status", "queued")),
            exit_code=data.get("exit_code"),
            execution_time_ms=data.get("execution_time_ms"),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            environment=data.get("environment", {}),
            description=data.get("description", ""),
            is_pinned=data.get("is_pinned", False),
            is_favorite=data.get("is_favorite", False),
            order=data.get("order", 0),
            last_execution=datetime.fromisoformat(data["last_execution"]) if data.get("last_execution") else None,
            execution_count=data.get("execution_count", 0)
        )


@dataclass
class TaskExecutionRecord:
    """Record of a task execution for history."""
    
    task_id: str
    task_name: str
    command: str
    working_directory: str
    status: str
    exit_code: Optional[int]
    execution_time_ms: Optional[int]
    execution_time: datetime
    result: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "command": self.command,
            "working_directory": self.working_directory,
            "status": self.status,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "execution_time": self.execution_time.isoformat(),
            "result": self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecutionRecord":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            task_name=data["task_name"],
            command=data["command"],
            working_directory=data["working_directory"],
            status=data["status"],
            exit_code=data.get("exit_code"),
            execution_time_ms=data.get("execution_time_ms"),
            execution_time=datetime.fromisoformat(data["execution_time"]),
            result=data.get("result", "")
        )
