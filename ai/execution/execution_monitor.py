"""
ExecutionMonitor — real-time monitoring of execution metrics.

Monitors running tasks and collects metrics for:
- Current step
- Current tool
- Current model
- Execution time
- Progress
- Memory usage
- CPU usage
- Errors and warnings

Provides a unified view of execution state for the UI and
other monitoring systems.

Usage:
    monitor = ExecutionMonitor(engine)
    monitor.start()
    
    # Get current status
    status = monitor.get_status()
    
    # Subscribe to updates
    monitor.on_status_change(lambda status: print(status))
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .execution_task import ExecutionTask, ExecutionResult
from .task_state import TaskState
from core.logger import setup_logger


@dataclass
class MonitorStatus:
    """
    Current monitoring status.
    
    Attributes:
        timestamp:      When this status was captured
        active_task:    Currently executing task (if any)
        task_progress:  Progress percentage (0-100)
        current_step:   Current step index
        current_tool:   Currently executing tool (if any)
        current_model:  Currently selected model (if any)
        elapsed_time_ms: Total execution time so far
        estimated_total_ms: Estimated total time
        estimated_remaining_ms: Estimated remaining time
        memory_usage_mb: Current memory usage
        cpu_usage_percent: Current CPU usage
        errors:         Recent errors
        warnings:       Recent warnings
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    active_task: Optional[str] = None
    task_progress: float = 0.0
    current_step: int = 0
    current_tool: Optional[str] = None
    current_model: Optional[str] = None
    elapsed_time_ms: float = 0.0
    estimated_total_ms: float = 0.0
    estimated_remaining_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ExecutionMonitor:
    """
    Real-time execution monitor.
    
    Continuously monitors running tasks and provides
    up-to-date status information.
    
    Usage:
        monitor = ExecutionMonitor(engine)
        monitor.start()
        
        # Get current status
        while monitor.is_running():
            status = monitor.get_status()
            print(status)
            time.sleep(1.0)
        
        monitor.stop()
    """
    
    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self._lock = threading.RLock()
        self._shutdown = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Status storage
        self._status: MonitorStatus = MonitorStatus()
        self._status_listeners: List[Callable[[MonitorStatus], None]] = []
        
        # Recent history for trending
        self._history: List[MonitorStatus] = []
        self._max_history = 100
        
        logger = setup_logger(__name__)
        logger.info("ExecutionMonitor initialized")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Start monitoring."""
        if self._monitor_thread:
            return
        
        self._shutdown = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ExecutionMonitor",
        )
        self._monitor_thread.start()
        
        logger = setup_logger(__name__)
        logger.info("ExecutionMonitor started")
    
    def stop(self) -> None:
        """Stop monitoring."""
        self._shutdown = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
        
        logger = setup_logger(__name__)
        logger.info("ExecutionMonitor stopped")
    
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._monitor_thread is not None and not self._shutdown
    
    def get_status(self) -> MonitorStatus:
        """
        Get current monitoring status.
        
        Returns:
            Current MonitorStatus
        """
        with self._lock:
            return self._update_status()
    
    def get_status_for_task(self, task_id: str) -> Optional[MonitorStatus]:
        """Get status for a specific task."""
        with self._lock:
            task = self._engine.get_task(task_id)
            if not task:
                return None
            
            # Build status for this task
            status = MonitorStatus()
            
            if task.started_time:
                elapsed = (datetime.utcnow() - task.started_time).total_seconds() * 1000
                status.elapsed_time_ms = elapsed
            
            if task.completed_time:
                total = (task.completed_time - task.started_time).total_seconds() * 1000 if task.started_time else 0
                status.estimated_total_ms = total
                status.task_progress = 100.0
            elif task.started_time:
                # Estimate based on completed steps
                completed = sum(1 for r in task.results if r.success)
                total_steps = len(task.task.plan) or 1
                status.task_progress = (completed / total_steps) * 100
                
                # Estimate remaining
                if completed > 0:
                    avg_step_time = elapsed / completed
                    remaining = (total_steps - completed) * avg_step_time
                    status.estimated_remaining_ms = remaining
                    status.estimated_total_ms = elapsed + remaining
            
            status.active_task = task_id
            status.errors = [task.error] if task.error else []
            
            return status
    
    def on_status_change(self, callback: Callable[[MonitorStatus], None]) -> None:
        """
        Register a callback for status changes.
        
        Args:
            callback: Function that takes MonitorStatus
        """
        with self._lock:
            self._status_listeners.append(callback)
    
    def get_history(self, limit: int = 10) -> List[MonitorStatus]:
        """
        Get recent status history.
        
        Args:
            limit: Maximum number of history items
            
        Returns:
            List of recent MonitorStatus (newest first)
        """
        with self._lock:
            return list(reversed(self._history[-limit:]))
    
    def clear_history(self) -> None:
        """Clear status history."""
        with self._lock:
            self._history.clear()
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while not self._shutdown:
            try:
                status = self._update_status()
                
                with self._lock:
                    self._status = status
                    self._history.append(status)
                    
                    # Trim history
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
                    
                    # Notify listeners
                    for listener in self._status_listeners[:]:
                        try:
                            listener(status)
                        except Exception as e:
                            logger = setup_logger(__name__)
                            logger.error(f"Status listener error: {e}")
                
                # Small delay
                time.sleep(0.5)
                
            except Exception as e:
                logger = setup_logger(__name__)
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1.0)
    
    def _update_status(self) -> MonitorStatus:
        """Update and return current status."""
        now = datetime.utcnow()
        
        # Get active task
        active_tasks = self._engine.get_running_tasks()
        active_task = active_tasks[0] if active_tasks else None
        
        status = MonitorStatus(timestamp=now)
        
        if active_task:
            status.active_task = active_task.id
            
            # Calculate progress
            completed = sum(1 for r in active_task.results if r.success)
            total_steps = len(active_task.task.plan) or 1
            status.task_progress = (completed / total_steps) * 100
            status.current_step = completed
            
            # Get current step details
            if active_task.results:
                last_result = active_task.results[-1]
                status.current_tool = last_result.tools_used[0] if last_result.tools_used else None
                status.current_model = last_result.model_used
            
            # Calculate timing
            if active_task.started_time:
                elapsed = (now - active_task.started_time).total_seconds() * 1000
                status.elapsed_time_ms = elapsed
                
                # Estimate remaining
                if completed > 0:
                    avg_step_time = elapsed / completed
                    remaining = (total_steps - completed) * avg_step_time
                    status.estimated_remaining_ms = remaining
                    status.estimated_total_ms = elapsed + remaining
            
            # Error/warning collection
            if active_task.error:
                status.errors.append(active_task.error)
        
        # Collect status from all tasks
        all_tasks = self._engine.get_all_tasks()
        errors = []
        warnings = []
        
        for task in all_tasks:
            if task.error:
                errors.append(f"Task {task.id[:8]}: {task.error}")
            
            # Check for warnings in results
            for result in task.results:
                if not result.success:
                    warnings.append(f"Step {result.step_index}: {result.error}")
        
        status.errors = errors
        status.warnings = warnings
        
        # Mock resource usage (in production, gather from OS)
        status.memory_usage_mb = 100.0 + len(all_tasks) * 10
        status.cpu_usage_percent = min(50.0 + len(active_tasks) * 10, 100.0)
        
        return status


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
