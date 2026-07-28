"""
ExecutionMetrics — performance metrics tracking.

Tracks and aggregates execution metrics including:
- Average task execution time
- Average verification time
- Average context build time
- Average model execution time
- Average apply time
- Success rate
- Failure rate
- Retry rate

Metrics are used for:
- Performance monitoring
- Capacity planning
- Optimization opportunities
- SLA tracking

Usage:
    metrics = ExecutionMetrics()
    
    # Record task completion
    metrics.record_task_success(task)
    
    # Record task failure
    metrics.record_task_failure(task)
    
    # Get metrics
    stats = metrics.get_metrics()
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .execution_task import ExecutionTask
from .task_state import TaskState


@dataclass
class MetricSnapshot:
    """
    Snapshot of all metrics at a point in time.
    
    Attributes:
        timestamp:         When snapshot was taken
        tasks_executed:    Total tasks executed
        success_count:     Successful tasks
        failure_count:     Failed tasks
        cancel_count:      Cancelled tasks
        success_rate:      Success rate (0-100)
        failure_rate:      Failure rate (0-100)
        retry_count:       Total retries
        retry_rate:        Retry rate (0-100)
        avg_task_time_ms:  Average task execution time
        avg_verification_time_ms: Average verification time
        avg_context_time_ms: Average context build time
        avg_model_time_ms: Average model execution time
        avg_apply_time_ms: Average apply time
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tasks_executed: int = 0
    success_count: int = 0
    failure_count: int = 0
    cancel_count: int = 0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    retry_count: int = 0
    retry_rate: float = 0.0
    avg_task_time_ms: float = 0.0
    avg_verification_time_ms: float = 0.0
    avg_context_time_ms: float = 0.0
    avg_model_time_ms: float = 0.0
    avg_apply_time_ms: float = 0.0


class ExecutionMetrics:
    """
    Performance metrics tracking for execution engine.
    
    Maintains running averages and counts for all execution metrics.
    
    Usage:
        metrics = ExecutionMetrics()
        
        # Record completions
        metrics.record_task_success(task)
        metrics.record_task_failure(task)
        
        # Get current metrics
        stats = metrics.get_metrics()
        
        # Get historical metrics
        history = metrics.get_history(limit=10)
    """
    
    def __init__(self) -> None:
        self._lock = threading.RLock()
        
        # Counters
        self._tasks_executed = 0
        self._success_count = 0
        self._failure_count = 0
        self._cancel_count = 0
        self._retry_count = 0
        
        # Timing storage (for running average)
        self._task_times: List[float] = []
        self._verification_times: List[float] = []
        self._context_times: List[float] = []
        self._model_times: List[float] = []
        self._apply_times: List[float] = []
        
        # Historical snapshots
        self._history: List[MetricSnapshot] = []
        self._max_history = 1000
        
        logger = setup_logger(__name__)
        logger.info("ExecutionMetrics initialized")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def record_task_success(self, task: ExecutionTask) -> None:
        """
        Record a successful task completion.
        
        Args:
            task: Completed task
        """
        with self._lock:
            self._tasks_executed += 1
            self._success_count += 1
            
            # Record task time
            if task.stats.total_duration_ms > 0:
                self._task_times.append(task.stats.total_duration_ms)
                # Keep only last 1000 for moving average
                if len(self._task_times) > 1000:
                    self._task_times = self._task_times[-1000:]
            
            # Record verification time if available
            if task.stats.verification_time_ms > 0:
                self._verification_times.append(task.stats.verification_time_ms)
                if len(self._verification_times) > 1000:
                    self._verification_times = self._verification_times[-1000:]
            
            # Record context time if available
            if task.stats.context_time_ms > 0:
                self._context_times.append(task.stats.context_time_ms)
                if len(self._context_times) > 1000:
                    self._context_times = self._context_times[-1000:]
            
            # Record retry count
            self._retry_count += task.stats.retry_count
            
            # Update history
            self._take_snapshot()
    
    def record_task_failure(self, task: ExecutionTask) -> None:
        """
        Record a failed task completion.
        
        Args:
            task: Failed task
        """
        with self._lock:
            self._tasks_executed += 1
            self._failure_count += 1
            
            # Record retry count
            self._retry_count += task.stats.retry_count
            
            # Update history
            self._take_snapshot()
    
    def record_task_cancelled(self, task: ExecutionTask) -> None:
        """
        Record a cancelled task.
        
        Args:
            task: Cancelled task
        """
        with self._lock:
            self._tasks_executed += 1
            self._cancel_count += 1
            
            # Update history
            self._take_snapshot()
    
    def record_verification_time(self, duration_ms: float) -> None:
        """
        Record a verification execution time.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self._verification_times.append(duration_ms)
            if len(self._verification_times) > 1000:
                self._verification_times = self._verification_times[-1000:]
    
    def record_context_build_time(self, duration_ms: float) -> None:
        """
        Record a context build time.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self._context_times.append(duration_ms)
            if len(self._context_times) > 1000:
                self._context_times = self._context_times[-1000:]
    
    def record_model_execution_time(self, duration_ms: float) -> None:
        """
        Record a model execution time.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self._model_times.append(duration_ms)
            if len(self._model_times) > 1000:
                self._model_times = self._model_times[-1000:]
    
    def record_apply_time(self, duration_ms: float) -> None:
        """
        Record a change apply time.
        
        Args:
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self._apply_times.append(duration_ms)
            if len(self._apply_times) > 1000:
                self._apply_times = self._apply_times[-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics as a dictionary.
        
        Returns:
            Metrics dictionary
        """
        with self._lock:
            total = self._tasks_executed or 1
            
            return {
                "tasks_executed": self._tasks_executed,
                "success_count": self._success_count,
                "failure_count": self._failure_count,
                "cancel_count": self._cancel_count,
                "success_rate": round((self._success_count / total) * 100, 2),
                "failure_rate": round((self._failure_count / total) * 100, 2),
                "retry_count": self._retry_count,
                "retry_rate": round((self._retry_count / self._tasks_executed) * 100, 2) if self._tasks_executed > 0 else 0.0,
                "avg_task_time_ms": self._avg(self._task_times),
                "avg_verification_time_ms": self._avg(self._verification_times),
                "avg_context_time_ms": self._avg(self._context_times),
                "avg_model_time_ms": self._avg(self._model_times),
                "avg_apply_time_ms": self._avg(self._apply_times),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    def get_history(self, limit: int = 10) -> List[MetricSnapshot]:
        """
        Get historical metrics snapshots.
        
        Args:
            limit: Maximum number of snapshots
            
        Returns:
            List of snapshots (newest first)
        """
        with self._lock:
            return list(reversed(self._history[-limit:]))
    
    def clear_history(self) -> None:
        """Clear historical snapshots."""
        with self._lock:
            self._history.clear()
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._tasks_executed = 0
            self._success_count = 0
            self._failure_count = 0
            self._cancel_count = 0
            self._retry_count = 0
            self._task_times.clear()
            self._verification_times.clear()
            self._context_times.clear()
            self._model_times.clear()
            self._apply_times.clear()
            self._history.clear()
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _avg(self, values: List[float]) -> float:
        """Calculate average of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _take_snapshot(self) -> None:
        """Take a metrics snapshot."""
        total = self._tasks_executed or 1
        
        snapshot = MetricSnapshot(
            tasks_executed=self._tasks_executed,
            success_count=self._success_count,
            failure_count=self._failure_count,
            cancel_count=self._cancel_count,
            success_rate=(self._success_count / total) * 100,
            failure_rate=(self._failure_count / total) * 100,
            retry_count=self._retry_count,
            retry_rate=(self._retry_count / self._tasks_executed) * 100 if self._tasks_executed > 0 else 0.0,
            avg_task_time_ms=self._avg(self._task_times),
            avg_verification_time_ms=self._avg(self._verification_times),
            avg_context_time_ms=self._avg(self._context_times),
            avg_model_time_ms=self._avg(self._model_times),
            avg_apply_time_ms=self._avg(self._apply_times),
        )
        
        self._history.append(snapshot)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]


def setup_logger(name: str):
    """Simple logger setup for this module."""
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
