"""
Base Tool — v1.5

Abstract base class for all tools in the Universal Tool Calling Engine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from core.logger import setup_logger


class ToolPermission(Enum):
    """Permission levels for tools."""
    SAFE = "safe"           # No user confirmation required
    WARNING = "warning"     # User confirmation required
    DANGEROUS = "dangerous" # User confirmation required, logged


class ToolCategory(Enum):
    """Tool categories."""
    FILE = "file"
    PROJECT = "project"
    TERMINAL = "terminal"
    GIT = "git"
    GITHUB = "github"
    BROWSER = "browser"
    VERIFICATION = "verification"
    EDITOR = "editor"
    PLUGIN = "plugin"


@dataclass
class ToolResult:
    """Standardized result for tool execution."""
    success: bool
    tool_name: str
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "output": str(self.output) if self.output else None,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def success_result(cls, tool_name: str, output: Any = None, 
                       metadata: Optional[Dict] = None) -> "ToolResult":
        """Create a success result."""
        return cls(
            success=True,
            tool_name=tool_name,
            output=output,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(cls, tool_name: str, error: str,
                     metadata: Optional[Dict] = None) -> "ToolResult":
        """Create an error result."""
        return cls(
            success=False,
            tool_name=tool_name,
            error=error,
            metadata=metadata or {}
        )


@dataclass
class ToolContext:
    """Context passed to every tool."""
    project_root: Optional[str] = None
    workspace: Optional[str] = None
    open_files: List[str] = field(default_factory=list)
    selected_text: Optional[str] = None
    cursor_position: Optional[Dict[str, Any]] = None
    ai_task: Optional[str] = None
    current_model: Optional[str] = None
    project_intelligence: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_root": self.project_root,
            "workspace": self.workspace,
            "open_files": self.open_files,
            "selected_text": self.selected_text[:50] + "..." if self.selected_text and len(self.selected_text) > 50 else self.selected_text,
            "cursor_position": self.cursor_position,
            "ai_task": self.ai_task,
            "current_model": self.current_model,
            "project_intelligence": self.project_intelligence,
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Every tool must implement:
    - execute() — Main execution logic
    - cancel() — Cancel ongoing execution
    - validate() — Validate parameters before execution
    
    Tools receive ToolContext with project state for context-aware execution.
    """
    
    def __init__(self, name: str, description: str, category: ToolCategory,
                 permission_level: ToolPermission, supported_models: List[str]):
        self.name = name
        self.description = description
        self.category = category
        self.permission_level = permission_level
        self.supported_models = supported_models
        self.logger = setup_logger(f"tool.{name}")
        
        self._context: Optional[ToolContext] = None
        self._is_cancelled = False
        self._is_running = False
        self._last_result: Optional[ToolResult] = None
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        """Check if tool is currently executing."""
        return self._is_running
    
    @property
    def is_cancelled(self) -> bool:
        """Check if tool execution was cancelled."""
        return self._is_cancelled
    
    @property
    def requires_confirmation(self) -> bool:
        """Check if tool requires user confirmation."""
        return self.permission_level in (ToolPermission.WARNING, ToolPermission.DANGEROUS)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Execution
    # ─────────────────────────────────────────────────────────────────────────────

    def set_context(self, context: ToolContext) -> None:
        """Set the tool context."""
        self._context = context
    
    def get_context(self) -> Optional[ToolContext]:
        """Get the current tool context."""
        return self._context
    
    async def execute_async(self, **kwargs) -> ToolResult:
        """
        Execute the tool asynchronously.
        
        This method handles:
        - Setting running status
        - Calling execute()
        - Timing execution
        - Handling cancellation
        - Storing result
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success/failure and output
        """
        if self._is_cancelled:
            return ToolResult.error_result(
                self.name, 
                "Tool execution was cancelled"
            )
        
        self._is_running = True
        start_time = datetime.utcnow()
        
        try:
            # Validate parameters
            validation_result = self.validate(**kwargs)
            if not validation_result.success:
                return validation_result
            
            # Execute
            result = await self.execute(**kwargs)
            
            # Time it
            result.execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._last_result = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tool {self.name} execution error: {e}")
            result = ToolResult.error_result(
                self.name,
                str(e)
            )
            result.execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return result
            
        finally:
            self._is_running = False
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool synchronously.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success/failure and output
        """
        result = self._run_async(self.execute_async(**kwargs))
        return result
    
    @abstractmethod
    async def execute_async(self, **kwargs) -> ToolResult:
        """
        Async execution implementation.
        
        This is the main method that must be implemented by each tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success/failure and output
        """
        pass
    
    def cancel(self) -> bool:
        """
        Cancel ongoing execution.
        
        Returns:
            True if cancellation was successful
        """
        self._is_cancelled = True
        self._is_running = False
        self.logger.info(f"Tool {self.name} cancellation requested")
        return True
    
    def validate(self, **kwargs) -> ToolResult:
        """
        Validate tool parameters before execution.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            ToolResult with validation result
        """
        # Default implementation: always valid
        return ToolResult.success_result(self.name, metadata={"validated": True})
    
    def _run_async(self, coro) -> Any:
        """Run async coroutine in a thread-safe manner."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Utility methods
    # ─────────────────────────────────────────────────────────────────────────────

    def is_model_supported(self, model_id: str) -> bool:
        """Check if a model is supported by this tool."""
        return model_id in self.supported_models or "all" in self.supported_models
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "permission_level": self.permission_level.value,
            "supported_models": self.supported_models,
            "requires_confirmation": self.requires_confirmation,
            "is_running": self._is_running,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, category={self.category.value})"
