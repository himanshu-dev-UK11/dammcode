"""
Tool Result — v1.5

Extended ToolResult with additional metadata for tool execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

from ai.tools.tool_base import ToolResult


logger = setup_logger(__name__)


@dataclass
class ExtendedToolResult:
    """
    Extended tool result with additional metadata.
    
    Adds:
    - Tool context
    - Execution metadata
    - Validation info
    - Related tools
    """
    
    # Base result
    base_result: ToolResult
    
    # Tool context
    tool_name: str
    action: str
    context: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    execution_id: Optional[str] = None
    user: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Validation
    validated: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Related tools
    depends_on: List[str] = field(default_factory=list)
    affects: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_result": self.base_result.to_dict(),
            "tool_name": self.tool_name,
            "action": self.action,
            "context": self.context,
            "execution_id": self.execution_id,
            "user": self.user,
            "timestamp": self.timestamp.isoformat(),
            "validated": self.validated,
            "validation_errors": self.validation_errors,
            "depends_on": self.depends_on,
            "affects": self.affects,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_tool_result(cls, result: ToolResult, 
                        tool_name: str, 
                        action: str,
                        context: Optional[Dict[str, Any]] = None) -> "ExtendedToolResult":
        """Create from ToolResult."""
        return cls(
            base_result=result,
            tool_name=tool_name,
            action=action,
            context=context,
        )


class ToolResultCollector:
    """
    Collects and analyzes tool results.
    
    Provides:
    - Result aggregation
    - Pattern detection
    - Failure analysis
    """
    
    def __init__(self):
        self._results: List[ExtendedToolResult] = []
        self._lock = None  # Would use threading.Lock in production
        self._logger = logger
    
    def add_result(self, result: ExtendedToolResult) -> None:
        """Add a tool result."""
        self._results.append(result)
        self._logger.debug(f"Collected result: {result.tool_name}.{result.action}")
    
    def get_results(self) -> List[ExtendedToolResult]:
        """Get all collected results."""
        return list(self._results)
    
    def get_successes(self) -> List[ExtendedToolResult]:
        """Get successful results."""
        return [r for r in self._results if r.base_result.success]
    
    def get_failures(self) -> List[ExtendedToolResult]:
        """Get failed results."""
        return [r for r in self._results if not r.base_result.success]
    
    def get_by_tool(self, tool_name: str) -> List[ExtendedToolResult]:
        """Get results for a specific tool."""
        return [r for r in self._results if r.tool_name == tool_name]
    
    def get_by_status(self, success: bool) -> List[ExtendedToolResult]:
        """Get results by success status."""
        return [r for r in self._results if r.base_result.success == success]
    
    def get_recent(self, minutes: int = 60) -> List[ExtendedToolResult]:
        """Get recent results."""
        cutoff = datetime.utcnow().timestamp() - (minutes * 60)
        return [
            r for r in self._results
            if r.timestamp.timestamp() >= cutoff
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get result statistics."""
        total = len(self._results)
        successes = len(self.get_successes())
        failures = len(self.get_failures())
        
        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / total if total > 0 else 0.0,
            "tools_used": len(set(r.tool_name for r in self._results)),
        }
    
    def clear(self) -> None:
        """Clear all results."""
        self._results.clear()
