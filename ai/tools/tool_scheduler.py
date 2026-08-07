"""
Tool Scheduler — v1.5

Manages tool execution scheduling with support for:
- Sequential and parallel execution
- Priority-based ordering
- Cancellation
- Retries
- Timeouts
"""

import asyncio
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from core.logger import setup_logger

from ai.tools.tool_base import BaseTool, ToolResult


logger = setup_logger(__name__)


class TaskStatus(Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ScheduledTask:
    """A scheduled tool execution task."""
    task_id: str
    tool_name: str
    action: str
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ToolResult] = None
    error: Optional[str] = None
    on_complete: Optional[Callable[[ToolResult], None]] = None
    on_error: Optional[Callable[[str], None]] = None


class ToolScheduler:
    """
    Manages tool execution scheduling and coordination.
    
    Features:
    - Priority-based scheduling
    - Sequential and parallel execution
    - Cancellation support
    - Retry logic with exponential backoff
    - Timeout enforcement
    """
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._queue: List[ScheduledTask] = []
        self._running: Dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._logger = logger
        self._shutdown = False
        self._worker_thread: Optional[threading.Thread] = None
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Scheduling
    # ─────────────────────────────────────────────────────────────────────────────

    def schedule(self, tool_name: str, action: str, **kwargs) -> str:
        """
        Schedule a tool for execution.
        
        Args:
            tool_name: Name of the tool
            action: Method to call
            **kwargs: Tool arguments
            
        Returns:
            Task ID for the scheduled task
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            task_id=task_id,
            tool_name=tool_name,
            action=action,
            params=kwargs,
            priority=kwargs.get("priority", 0),
            timeout_seconds=kwargs.get("timeout_seconds"),
            max_retries=kwargs.get("max_retries", 0),
        )
        
        with self._lock:
            self._tasks[task_id] = task
            self._queue.append(task)
            self._queue.sort(key=lambda t: (-t.priority, t.created_at))
        
        self._logger.info(f"Scheduled task {task_id} for {tool_name}.{action}")
        return task_id
    
    def execute_now(self, tool_name: str, action: str, **kwargs) -> str:
        """
        Execute a tool immediately (bypassing queue).
        
        Args:
            tool_name: Name of the tool
            action: Method to call
            **kwargs: Tool arguments
            
        Returns:
            Task ID for the task
        """
        # Execute in background thread
        task_id = self.schedule(tool_name, action, **kwargs)
        
        def execute_task():
            task = self._tasks.get(task_id)
            if task:
                self._execute_task(task)
        
        threading.Thread(target=execute_task, daemon=True).start()
        return task_id
    
    def schedule_batch(self, tasks: List[Dict[str, Any]], 
                       mode: str = "sequential") -> List[str]:
        """
        Schedule multiple tasks.
        
        Args:
            tasks: List of task specifications
            mode: "sequential" or "parallel"
            
        Returns:
            List of task IDs
        """
        task_ids = []
        for task_spec in tasks:
            task_id = self.schedule(
                task_spec["tool_name"],
                task_spec["action"],
                **task_spec.get("params", {})
            )
            task_ids.append(task_id)
        
        self._logger.info(f"Scheduled {len(task_ids)} tasks in {mode} mode")
        return task_ids
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Cancellation
    # ─────────────────────────────────────────────────────────────────────────────

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a scheduled or running task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.COMPLETED:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            if task_id in self._running:
                del self._running[task_id]
            
            # Remove from queue
            self._queue = [t for t in self._queue if t.task_id != task_id]
        
        self._logger.info(f"Cancelled task {task_id}")
        return True
    
    def cancel_all(self) -> int:
        """
        Cancel all scheduled and running tasks.
        
        Returns:
            Number of tasks cancelled
        """
        cancelled = 0
        with self._lock:
            # Cancel running tasks
            for task_id in list(self._running.keys()):
                if self.cancel(task_id):
                    cancelled += 1
            
            # Cancel pending tasks
            for task in list(self._queue):
                if self.cancel(task.task_id):
                    cancelled += 1
        
        self._logger.info(f"Cancelled {cancelled} tasks")
        return cancelled
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Status
    # ───────────────────────────────────────────────��─────────────────────────────

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_pending(self) -> List[ScheduledTask]:
        """Get all pending scheduled tasks."""
        with self._lock:
            return [t for t in self._queue if t.status == TaskStatus.PENDING]
    
    def get_running(self) -> List[ScheduledTask]:
        """Get all currently running tasks."""
        with self._lock:
            return list(self._running.values())
    
    def get_completed(self) -> List[ScheduledTask]:
        """Get all completed tasks."""
        with self._lock:
            return [t for t in self._tasks.values() 
                   if t.status == TaskStatus.COMPLETED]
    
    def get_failed(self) -> List[ScheduledTask]:
        """Get all failed tasks."""
        with self._lock:
            return [t for t in self._tasks.values() 
                   if t.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        with self._lock:
            return {
                "total_tasks": len(self._tasks),
                "pending": len(self._queue),
                "running": len(self._running),
                "completed": sum(1 for t in self._tasks.values() 
                               if t.status == TaskStatus.COMPLETED),
                "failed": sum(1 for t in self._tasks.values() 
                            if t.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)),
                "cancelled": sum(1 for t in self._tasks.values() 
                               if t.status == TaskStatus.CANCELLED),
            }
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Execution
    # ─────────────────────────────────────────────────────────────────────────────

    def start_worker(self) -> None:
        """Start the worker thread for processing the queue."""
        if self._worker_thread:
            return
        
        self._shutdown = False
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="ToolScheduler"
        )
        self._worker_thread.start()
        self._logger.info("Tool scheduler worker started")
    
    def stop_worker(self) -> None:
        """Stop the worker thread."""
        self._shutdown = True
        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)
            self._worker_thread = None
        self._logger.info("Tool scheduler worker stopped")
    
    def _worker_loop(self) -> None:
        """Background worker loop for processing the queue."""
        while not self._shutdown:
            try:
                task = self._get_next_task()
                
                if task:
                    self._execute_task(task)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                self._logger.error(f"Worker loop error: {e}")
                time.sleep(1.0)
    
    def _get_next_task(self) -> Optional[ScheduledTask]:
        """Get the next task from the queue."""
        with self._lock:
            if not self._queue:
                return None
            
            # Get highest priority task
            task = self._queue.pop(0)
            
            # Check if still pending
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.SCHEDULED
                return task
            
            # Task was cancelled or completed
            return self._get_next_task()
    
    async def _execute_task_async(self, task: ScheduledTask) -> ToolResult:
        """Execute a task asynchronously."""
        # Try to get the tool
        try:
            from ai.tools.tool_manager import get_tool_manager
            manager = get_tool_manager()
            
            if not manager or not manager.registry:
                return ToolResult.error_result(
                    task.tool_name,
                    "Tool manager not available"
                )
            
            tool = manager.registry.get_tool(task.tool_name)
            
            if not tool:
                return ToolResult.error_result(
                    task.tool_name,
                    f"Tool '{task.tool_name}' not found"
                )
            
            # Execute the action
            method = getattr(tool, task.action, None)
            if not method:
                return ToolResult.error_result(
                    task.tool_name,
                    f"Action '{task.action}' not found on tool"
                )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                method(**task.params),
                timeout=task.timeout_seconds
            )
            
            return result
            
        except asyncio.TimeoutError:
            return ToolResult.error_result(
                task.tool_name,
                f"Task timed out after {task.timeout_seconds}s"
            )
        except Exception as e:
            return ToolResult.error_result(task.tool_name, str(e))
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        with self._lock:
            self._running[task.task_id] = task
        
        self._logger.info(f"Executing task {task.task_id}: {task.tool_name}.{task.action}")
        
        try:
            # Execute the task
            result = asyncio.run(self._execute_task_async(task))
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            
            self._logger.info(f"Task {task.task_id} completed")
            
            # Call completion callback
            if task.on_complete and result:
                try:
                    task.on_complete(result)
                except Exception as e:
                    self._logger.error(f"Completion callback error: {e}")
            
            # Remove from running
            with self._lock:
                if task.task_id in self._running:
                    del self._running[task.task_id]
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            self._logger.error(f"Task {task.task_id} failed: {e}")
            
            # Retry if configured
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                
                # Add back to queue with delay
                def retry():
                    time.sleep(2 ** task.retry_count)
                    with self._lock:
                        self._queue.append(task)
                        self._queue.sort(key=lambda t: (-t.priority, t.created_at))
                
                threading.Thread(target=retry, daemon=True).start()
                self._logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
            else:
                # Call error callback
                if task.on_error:
                    try:
                        task.on_error(task.error)
                    except Exception as e:
                        self._logger.error(f"Error callback error: {e}")
                
                # Remove from running
                with self._lock:
                    if task.task_id in self._running:
                        del self._running[task.task_id]
