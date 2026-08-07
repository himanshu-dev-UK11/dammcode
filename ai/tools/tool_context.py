"""
Tool Context — v1.5

Context passed to every tool for context-aware execution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ToolContext:
    """
    Context passed to every tool for context-aware execution.
    
    Provides tools with project state information so they can
    make informed decisions and provide better results.
    """
    
    # Project information
    project_root: Optional[str] = None
    workspace: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    detected_language: Optional[str] = None
    detected_framework: Optional[str] = None
    
    # File information
    open_files: List[str] = field(default_factory=list)
    selected_text: Optional[str] = None
    current_file: Optional[str] = None
    cursor_position: Optional[Dict[str, Any]] = None  # {line, column}
    
    # Task information
    ai_task: Optional[str] = None
    task_id: Optional[str] = None
    task_type: Optional[str] = None  # coding, debugging, testing, etc.
    
    # Model information
    current_model: Optional[str] = None
    model_provider: Optional[str] = None
    
    # Intelligence
    project_intelligence: Optional[Dict[str, Any]] = None
    
    # Context metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "project_root": self.project_root,
            "workspace": self.workspace,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "open_files": self.open_files[:5] if len(self.open_files) > 5 else self.open_files,
            "selected_text_length": len(self.selected_text) if self.selected_text else 0,
            "current_file": self.current_file,
            "cursor_position": self.cursor_position,
            "ai_task": self.ai_task,
            "current_model": self.current_model,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolContext":
        """Create context from dictionary."""
        context = cls()
        
        context.project_root = data.get("project_root")
        context.workspace = data.get("workspace")
        context.project_name = data.get("project_name")
        context.project_type = data.get("project_type")
        context.detected_language = data.get("detected_language")
        context.detected_framework = data.get("detected_framework")
        context.open_files = data.get("open_files", [])
        context.selected_text = data.get("selected_text")
        context.current_file = data.get("current_file")
        context.cursor_position = data.get("cursor_position")
        context.ai_task = data.get("ai_task")
        context.task_id = data.get("task_id")
        context.task_type = data.get("task_type")
        context.current_model = data.get("current_model")
        context.model_provider = data.get("model_provider")
        context.project_intelligence = data.get("project_intelligence")
        
        if data.get("timestamp"):
            from datetime import datetime
            context.timestamp = datetime.fromisoformat(data["timestamp"])
        
        context.session_id = data.get("session_id")
        
        return context
    
    def merge(self, other: "ToolContext") -> None:
        """Merge another context into this one."""
        if other.project_root:
            self.project_root = other.project_root
        if other.workspace:
            self.workspace = other.workspace
        if other.project_name:
            self.project_name = other.project_name
        if other.project_type:
            self.project_type = other.project_type
        if other.detected_language:
            self.detected_language = other.detected_language
        if other.detected_framework:
            self.detected_framework = other.detected_framework
        if other.open_files:
            self.open_files = list(set(self.open_files + other.open_files))
        if other.selected_text:
            self.selected_text = other.selected_text
        if other.current_file:
            self.current_file = other.current_file
        if other.cursor_position:
            self.cursor_position = other.cursor_position
        if other.ai_task:
            self.ai_task = other.ai_task
        if other.task_id:
            self.task_id = other.task_id
        if other.task_type:
            self.task_type = other.task_type
        if other.current_model:
            self.current_model = other.current_model
        if other.model_provider:
            self.model_provider = other.model_provider
        if other.project_intelligence:
            self.project_intelligence = other.project_intelligence
        if other.timestamp:
            self.timestamp = other.timestamp
        if other.session_id:
            self.session_id = other.session_id
