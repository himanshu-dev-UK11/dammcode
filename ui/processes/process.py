"""
Process Manager — Process Model

Represents a running process in the terminal.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ProcessStatus(Enum):
    """Process execution status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    KILLED = "killed"
    PAUSED = "paused"


class ProcessType(Enum):
    """Process type classification."""
    FOREGROUND = "foreground"
    BACKGROUND = "background"
    LONG_RUNNING = "long_running"
    DEBUGGER = "debugger"
    SYSTEM = "system"


@dataclass
class Process:
    """Represents a running process."""
    
    process_id: str
    name: str
    command: str
    working_directory: str
    shell: str = "cmd"
    
    # Process info
    pid: Optional[int] = None
    status: ProcessStatus = ProcessStatus.RUNNING
    exit_code: Optional[int] = None
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Resource usage
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Metadata
    process_type: ProcessType = ProcessType.FOREGROUND
    is_background: bool = False
    long_running: bool = False
    tags: list = field(default_factory=list)
    
    # Terminal association
    terminal_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "process_id": self.process_id,
            "name": self.name,
            "command": self.command,
            "working_directory": self.working_directory,
            "shell": self.shell,
            "pid": self.pid,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "cpu_usage": self.cpu_usage,
            "memory_usage_mb": self.memory_usage_mb,
            "process_type": self.process_type.value,
            "is_background": self.is_background,
            "long_running": self.long_running,
            "tags": self.tags,
            "terminal_id": self.terminal_id,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Process":
        """Create process from dictionary."""
        return cls(
            process_id=data["process_id"],
            name=data["name"],
            command=data["command"],
            working_directory=data["working_directory"],
            shell=data.get("shell", "cmd"),
            pid=data.get("pid"),
            status=ProcessStatus(data.get("status", "running")),
            exit_code=data.get("exit_code"),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_ms=data.get("duration_ms"),
            cpu_usage=data.get("cpu_usage", 0.0),
            memory_usage_mb=data.get("memory_usage_mb", 0.0),
            process_type=ProcessType(data.get("process_type", "foreground")),
            is_background=data.get("is_background", False),
            long_running=data.get("long_running", False),
            tags=data.get("tags", []),
            terminal_id=data.get("terminal_id"),
            session_id=data.get("session_id")
        )
    
    @property
    def duration_str(self) -> str:
        """Get human-readable duration."""
        if self.duration_ms is None:
            return "N/A"
        
        seconds = self.duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @property
    def start_time_str(self) -> str:
        """Get human-readable start time."""
        if self.start_time:
            return self.start_time.strftime("%H:%M:%S")
        return "N/A"


@dataclass
class DebugMessage:
    """A debug message from the debug console."""
    
    message_id: str
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source: str  # runtime, exception, warning, debugger, app, system
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "stack_trace": self.stack_trace
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebugMessage":
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=data["level"],
            source=data["source"],
            message=data["message"],
            file=data.get("file"),
            line=data.get("line"),
            stack_trace=data.get("stack_trace")
        )
    
    @property
    def level_color(self) -> str:
        """Get color for log level."""
        colors = {
            "DEBUG": "#71717A",
            "INFO": "#3B82F6",
            "WARNING": "#F59E0B",
            "ERROR": "#EF4444",
            "CRITICAL": "#7F1D1D"
        }
        return colors.get(self.level, "#71717A")
    
    @property
    def level_icon(self) -> str:
        """Get icon for log level."""
        icons = {
            "DEBUG": "🐛",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥"
        }
        return icons.get(self.level, "📄")


@dataclass
class ResourceUsage:
    """Current system resource usage."""
    
    timestamp: datetime
    cpu_usage: float  # Percentage
    memory_usage_mb: float
    memory_usage_percent: float
    process_count: int
    running_tasks: int
    terminal_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage_mb": self.memory_usage_mb,
            "memory_usage_percent": self.memory_usage_percent,
            "process_count": self.process_count,
            "running_tasks": self.running_tasks,
            "terminal_count": self.terminal_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceUsage":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            cpu_usage=data["cpu_usage"],
            memory_usage_mb=data["memory_usage_mb"],
            memory_usage_percent=data["memory_usage_percent"],
            process_count=data["process_count"],
            running_tasks=data["running_tasks"],
            terminal_count=data["terminal_count"]
        )
