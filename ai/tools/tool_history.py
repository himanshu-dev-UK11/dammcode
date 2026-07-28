"""
Tool History — v1.5

Records and analyzes tool execution history.
"""

import json
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

from ai.tools.tool_base import ToolResult


logger = setup_logger(__name__)


@dataclass
class ExecutionRecord:
    """Record of a tool execution."""
    timestamp: datetime
    tool_name: str
    action: str
    success: bool
    execution_time_ms: float
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user: Optional[str] = None
    rollback_id: Optional[str] = None


class ToolHistory:
    """
    Stores and analyzes tool execution history.
    
    Provides:
    - Execution history storage
    - Statistics and metrics
    - Rollback capability
    """
    
    def __init__(self, history_dir: str = "config/tool_history"):
        self.history_dir = Path(history_dir)
        self._records: List[ExecutionRecord] = []
        self._lock = threading.Lock()
        self._tool_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "success": 0,
            "failure": 0,
            "total_time_ms": 0.0,
            "avg_time_ms": 0.0,
            "min_time_ms": float("inf"),
            "max_time_ms": 0.0,
        })
        self._logger = logger
        self._rollback_index: Dict[str, List[str]] = defaultdict(list)
        
        # Ensure directory exists
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._logger.warning(f"Could not create history directory: {e}")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Recording
    # ─────────────────────────────────────────────────────────────────────────────

    def record_result(self, result: ToolResult, 
                      context: Optional[Dict[str, Any]] = None,
                      user: Optional[str] = None,
                      rollback_id: Optional[str] = None) -> None:
        """
        Record a tool execution result.
        
        Args:
            result: ToolResult from execution
            context: Execution context (optional)
            user: User who executed (optional)
            rollback_id: Rollback identifier (optional)
        """
        record = ExecutionRecord(
            timestamp=datetime.utcnow(),
            tool_name=result.tool_name,
            action="",  # Action not stored in ToolResult
            success=result.success,
            execution_time_ms=result.execution_time_ms,
            error=result.error,
            context=context,
            user=user,
            rollback_id=rollback_id,
        )
        
        with self._lock:
            self._records.append(record)
            self._update_stats(result)
            
            if rollback_id:
                self._rollback_index[rollback_id].append(
                    f"{result.tool_name}.{record.timestamp.isoformat()}"
                )
        
        self._logger.debug(f"Recorded execution: {result.tool_name} - {'success' if result.success else 'failed'}")
    
    def record_execution(self, tool_name: str, action: str, success: bool,
                        execution_time_ms: float, error: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None,
                        user: Optional[str] = None,
                        rollback_id: Optional[str] = None) -> None:
        """Record a tool execution directly."""
        result = ToolResult(
            success=success,
            tool_name=tool_name,
            error=error,
            metadata={"execution_time_ms": execution_time_ms}
        )
        result.execution_time_ms = execution_time_ms
        self.record_result(result, context, user, rollback_id)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────────────────────────────────────

    def get_history(self, limit: int = 100, 
                    tool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            limit: Maximum number of records
            tool_name: Filter by tool name (optional)
            
        Returns:
            List of execution records
        """
        with self._lock:
            if tool_name:
                records = [r for r in self._records if r.tool_name == tool_name]
            else:
                records = list(self._records)
            
            # Sort by timestamp (newest first)
            records.sort(key=lambda r: r.timestamp, reverse=True)
            
            # Return limited
            return [self._record_to_dict(r) for r in records[:limit]]
    
    def get_recent(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get executions from the last N minutes."""
        cutoff = datetime.utcnow().timestamp() - (minutes * 60)
        
        with self._lock:
            recent = [
                r for r in self._records
                if r.timestamp.timestamp() >= cutoff
            ]
        
        recent.sort(key=lambda r: r.timestamp, reverse=True)
        return [self._record_to_dict(r) for r in recent]
    
    def get_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed executions."""
        with self._lock:
            errors = [r for r in self._records if not r.success]
        
        errors.sort(key=lambda r: r.timestamp, reverse=True)
        return [self._record_to_dict(r) for r in errors[:limit]]
    
    def get_by_rollback_id(self, rollback_id: str) -> List[Dict[str, Any]]:
        """Get executions by rollback ID."""
        with self._lock:
            record_ids = self._rollback_index.get(rollback_id, [])
            return [self._record_to_dict(r) for r in self._records 
                   if f"{r.tool_name}.{r.timestamp.isoformat()}" in record_ids]
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────────────

    def get_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a tool or all tools.
        
        Args:
            tool_name: Tool name or None for all
            
        Returns:
            Statistics dictionary
        """
        with self._lock:
            if tool_name:
                return self._tool_stats.get(tool_name, {}).copy()
            
            # Aggregate all stats
            stats = {}
            for name, data in self._tool_stats.items():
                stats[name] = {
                    "total": data["total"],
                    "success": data["success"],
                    "failure": data["failure"],
                    "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0.0,
                    "avg_time_ms": data["avg_time_ms"],
                    "min_time_ms": data["min_time_ms"] if data["min_time_ms"] != float("inf") else 0,
                    "max_time_ms": data["max_time_ms"],
                }
            return stats
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        with self._lock:
            total = len(self._records)
            success = sum(1 for r in self._records if r.success)
            failure = total - success
            
            total_time = sum(r.execution_time_ms for r in self._records)
            avg_time = total_time / total if total > 0 else 0.0
            
            return {
                "total_executions": total,
                "successful": success,
                "failed": failure,
                "success_rate": success / total if total > 0 else 0.0,
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "tools_count": len(self._tool_stats),
            }
    
    def get_top_tools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently used tools."""
        with self._lock:
            tools = []
            for name, data in self._tool_stats.items():
                tools.append({
                    "tool_name": name,
                    "total": data["total"],
                    "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0.0,
                    "avg_time_ms": data["avg_time_ms"],
                })
        
        tools.sort(key=lambda t: t["total"], reverse=True)
        return tools[:limit]
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────────────

    def get_history_size(self) -> int:
        """Get number of records in history."""
        with self._lock:
            return len(self._records)
    
    def clear_history(self, before: Optional[datetime] = None) -> int:
        """
        Clear old history records.
        
        Args:
            before: Clear records before this timestamp
            
        Returns:
            Number of records cleared
        """
        with self._lock:
            if before:
                original_count = len(self._records)
                self._records = [
                    r for r in self._records 
                    if r.timestamp >= before
                ]
                cleared = original_count - len(self._records)
            else:
                cleared = len(self._records)
                self._records.clear()
            
            return cleared
    
    def save_to_file(self, filepath: Optional[str] = None) -> str:
        """Save history to file."""
        filepath = filepath or str(self.history_dir / "history.json")
        
        with self._lock:
            data = {
                "records": [
                    self._record_to_dict(r) for r in self._records
                ],
                "saved_at": datetime.utcnow().isoformat(),
            }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return filepath
        except Exception as e:
            self._logger.error(f"Failed to save history: {e}")
            return ""
    
    def load_from_file(self, filepath: str) -> int:
        """Load history from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = data.get("records", [])
            for r_data in records:
                record = ExecutionRecord(
                    timestamp=datetime.fromisoformat(r_data["timestamp"]),
                    tool_name=r_data["tool_name"],
                    action=r_data.get("action", ""),
                    success=r_data["success"],
                    execution_time_ms=r_data.get("execution_time_ms", 0),
                    error=r_data.get("error"),
                    context=r_data.get("context"),
                    user=r_data.get("user"),
                    rollback_id=r_data.get("rollback_id"),
                )
                self._records.append(record)
                self._update_stats_from_record(record)
            
            return len(records)
        except Exception as e:
            self._logger.error(f"Failed to load history: {e}")
            return 0
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────────────

    def _record_to_dict(self, record: ExecutionRecord) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "timestamp": record.timestamp.isoformat(),
            "tool_name": record.tool_name,
            "action": record.action,
            "success": record.success,
            "execution_time_ms": record.execution_time_ms,
            "error": record.error,
            "context": record.context,
            "user": record.user,
            "rollback_id": record.rollback_id,
        }
    
    def _update_stats(self, result: ToolResult) -> None:
        """Update statistics for a tool."""
        stats = self._tool_stats[result.tool_name]
        
        stats["total"] += 1
        if result.success:
            stats["success"] += 1
        else:
            stats["failure"] += 1
        
        stats["total_time_ms"] += result.execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["total"]
        stats["min_time_ms"] = min(stats["min_time_ms"], result.execution_time_ms)
        stats["max_time_ms"] = max(stats["max_time_ms"], result.execution_time_ms)
    
    def _update_stats_from_record(self, record: ExecutionRecord) -> None:
        """Update stats from a loaded record."""
        stats = self._tool_stats[record.tool_name]
        
        stats["total"] += 1
        if record.success:
            stats["success"] += 1
        else:
            stats["failure"] += 1
        
        stats["total_time_ms"] += record.execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["total"]
        stats["min_time_ms"] = min(stats["min_time_ms"], record.execution_time_ms)
        stats["max_time_ms"] = max(stats["max_time_ms"], record.execution_time_ms)


# Global instance
_tool_history = None


def get_tool_history() -> ToolHistory:
    """Get the global tool history."""
    global _tool_history
    if _tool_history is None:
        _tool_history = ToolHistory()
    return _tool_history


def reset_tool_history():
    """Reset the global tool history."""
    global _tool_history
    _tool_history = None
