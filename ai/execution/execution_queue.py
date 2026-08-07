"""
ExecutionQueue — priority queue with persistence support.

Manages a priority queue of ExecutionTasks for the TaskScheduler.
Supports:
- Priority-based ordering
- Task groups for parallel execution
- Persistence to disk for application restarts
- Thread-safe operations

Tasks are ordered by:
1. Priority (higher = first)
2. Created time (earlier = first)
3. Task ID (alphabetically for stability)

This queue survives application restarts by serializing
its state to a JSON file in the config directory.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from uuid import uuid4

from .execution_task import ExecutionTask, ExecutionConfig
from .task_state import TaskState, StateTransition


class QueuePriority(int, Enum):
    """Priority levels for task queuing."""
    CRITICAL = 100
    URGENT   = 90
    HIGH     = 80
    MEDIUM   = 50
    LOW      = 20
    IDLE     = 10


class ExecutionQueue:
    """
    Thread-safe priority queue for ExecutionTasks.
    
    Features:
    - Priority-based ordering (higher priority = dequeued first)
    - Task groups for related tasks
    - Persistence to disk for restarts
    - Thread-safe operations via lock
    - Statistics tracking
    
    Usage:
        queue = ExecutionQueue(config_dir="/path/to/config")
        
        # Add task
        queue.enqueue(task)
        
        # Dequeue highest priority task
        task = queue.dequeue()
        
        # Save to disk
        queue.save()
        
        # Load from disk
        queue.load()
    """
    
    def __init__(
        self,
        config_dir: str,
        name: str = "default",
    ) -> None:
        self._config_dir = Path(config_dir)
        self._queue_file = self._config_dir / f"execution_queue_{name}.json"
        self._lock = threading.RLock()
        
        # Internal data structures
        self._tasks: Dict[str, ExecutionTask] = {}  # id → task
        self._priority_heap: List[tuple] = []       # (-priority, created_time, id)
        
        # Statistics
        self._total_enqueued = 0
        self._total_dequeued = 0
        self._total_requeued = 0
        
        logger = setup_logger(__name__)
        logger.info(f"ExecutionQueue initialized (file={self._queue_file.name})")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def enqueue(self, task: ExecutionTask) -> None:
        """
        Add a task to the queue.
        
        Args:
            task: Task to enqueue
        
        Raises:
            ValueError: If task is already terminal
        """
        if task.state_history.is_terminal:
            raise ValueError(f"Cannot enqueue terminal task: {task.id}")
        
        with self._lock:
            if task.id in self._tasks:
                # Already in queue, update and reheap
                self._tasks[task.id] = task
                self._rebuild_heap()
            else:
                self._tasks[task.id] = task
                self._push_to_heap(task)
                self._total_enqueued += 1
            
            # Update state
            task.state_history.add_transition(
                StateTransition(
                    from_state=task.state,
                    to_state=TaskState.SCHEDULED,
                    timestamp=datetime.utcnow(),
                    reason="Task enqueued",
                )
            )
        
        self._maybe_save()
    
    def dequeue(self) -> Optional[ExecutionTask]:
        """
        Remove and return the highest priority task.
        
        Returns:
            Highest priority task, or None if queue empty
        """
        with self._lock:
            if not self._priority_heap:
                return None
            
            _, _, task_id = self._priority_heap.pop(0)
            task = self._tasks.pop(task_id, None)
            
            if task:
                self._total_dequeued += 1
                task.state_history.add_transition(
                    StateTransition(
                        from_state=task.state,
                        to_state=TaskState.RUNNING,
                        timestamp=datetime.utcnow(),
                        reason="Task dequeued for execution",
                    )
                )
            
            return task
    
    def peek(self) -> Optional[ExecutionTask]:
        """Return highest priority task without removing it."""
        with self._lock:
            if not self._priority_heap:
                return None
            _, _, task_id = self._priority_heap[0]
            return self._tasks.get(task_id)
    
    def remove(self, task_id: str) -> bool:
        """
        Remove a specific task from the queue.
        
        Args:
            task_id: ID of task to remove
            
        Returns:
            True if task was removed, False if not found
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            del self._tasks[task_id]
            self._rebuild_heap()
            return True
    
    def contains(self, task_id: str) -> bool:
        """Check if a task is in the queue."""
        with self._lock:
            return task_id in self._tasks
    
    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        """Get a task by ID without removing it."""
        with self._lock:
            return self._tasks.get(task_id)
    
    def list_tasks(self) -> List[ExecutionTask]:
        """Return all tasks in priority order."""
        with self._lock:
            return [self._tasks[tid] for _, _, tid in sorted(self._priority_heap)]
    
    def count(self) -> int:
        """Return number of tasks in queue."""
        with self._lock:
            return len(self._tasks)
    
    def clear(self) -> None:
        """Remove all tasks from queue."""
        with self._lock:
            self._tasks.clear()
            self._priority_heap.clear()
    
    def get_by_group(self, group: str) -> List[ExecutionTask]:
        """Get all tasks in a group."""
        with self._lock:
            return [
                t for t in self._tasks.values()
                if t.config.group == group
            ]
    
    def get_pending_for_group(self, group: str) -> List[ExecutionTask]:
        """Get pending tasks in a group (waiting for dependencies)."""
        with self._lock:
            return [
                t for t in self._tasks.values()
                if t.config.group == group and t.state == TaskState.PENDING
            ]
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def save(self) -> None:
        """Save queue state to disk."""
        with self._lock:
            self._maybe_save()
    
    def load(self) -> int:
        """
        Load queue state from disk.
        
        Returns:
            Number of tasks loaded
        """
        if not self._queue_file.exists():
            return 0
        
        with self._lock:
            try:
                with open(self._queue_file, 'r') as f:
                    data = json.load(f)
                
                loaded = 0
                for task_data in data.get("tasks", []):
                    task = self._deserialize_task(task_data)
                    if task and not task.state_history.is_terminal:
                        self._tasks[task.id] = task
                        self._push_to_heap(task)
                        loaded += 1
                
                self._total_enqueued = data.get("total_enqueued", 0)
                self._total_dequeued = data.get("total_dequeued", 0)
                
                return loaded
                
            except Exception as e:
                logger = setup_logger(__name__)
                logger.error(f"Failed to load queue: {e}")
                return 0
    
    # ── Statistics ──────────────────────────────────────────────────────────────
    
    def stats(self) -> dict:
        """Return queue statistics."""
        with self._lock:
            return {
                "size": len(self._tasks),
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
                "total_requeued": self._total_requeued,
            }
    
    def stats_by_priority(self) -> Dict[str, int]:
        """Return task count grouped by priority."""
        with self._lock:
            counts: Dict[str, int] = {}
            for task in self._tasks.values():
                priority = task.config.priority or 50
                if priority >= 90:
                    key = "high"
                elif priority >= 50:
                    key = "medium"
                else:
                    key = "low"
                counts[key] = counts.get(key, 0) + 1
            return counts
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _push_to_heap(self, task: ExecutionTask) -> None:
        """Add task to priority heap."""
        priority = task.config.priority or 50
        created = task.created_time
        # Use negative priority for max-heap behavior (heapq is min-heap)
        entry = (-priority, created, task.id)
        self._priority_heap.append(entry)
        self._priority_heap.sort()  # Re-sort after insert
    
    def _rebuild_heap(self) -> None:
        """Rebuild heap from scratch."""
        self._priority_heap.clear()
        for task in self._tasks.values():
            self._push_to_heap(task)
    
    def _maybe_save(self) -> None:
        """Save to disk if not already saved recently."""
        # Don't save on every enqueue - only periodically
        # For simplicity, we save here. In production, use a timer.
        self._save()
    
    def _save(self) -> None:
        """Actually save to disk."""
        try:
            self._queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "saved_at": datetime.utcnow().isoformat(),
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
                "tasks": [
                    self._serialize_task(task)
                    for task in self._tasks.values()
                ],
            }
            
            with open(self._queue_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"Failed to save queue: {e}")
    
    def _serialize_task(self, task: ExecutionTask) -> dict:
        """Serialize task to dict."""
        return {
            "id": task.id,
            "prompt": task.task.original_prompt,
            "title": task.task.title,
            "status": task.status.value,
            "state": task.state.value,
            "created_time": task.created_time.isoformat(),
            "config": {
                "mode": task.config.mode.value,
                "max_retries": task.config.max_retries,
                "retry_strategy": task.config.retry_strategy.value,
                "timeout_secs": task.config.timeout_secs,
                "priority": task.config.priority,
                "group": task.config.group,
                "cancel_on_error": task.config.cancel_on_error,
                "depends_on": task.config.depends_on,
            },
        }
    
    def _deserialize_task(self, data: dict) -> Optional[ExecutionTask]:
        """Deserialize task from dict."""
        try:
            from ai.engine.task import Task as BaseTask, TaskStatus as BaseStatus
            
            base_task = BaseTask(
                original_prompt=data["prompt"],
                title=data.get("title", ""),
            )
            base_task.status = BaseStatus(data.get("status", "pending"))
            
            config_data = data.get("config", {})
            config = ExecutionConfig(
                mode=ExecutionMode(config_data.get("mode", "background")),
                max_retries=config_data.get("max_retries", 2),
                retry_strategy=RetryStrategy(config_data.get("retry_strategy", "exponential")),
                timeout_secs=config_data.get("timeout_secs"),
                priority=config_data.get("priority"),
                group=config_data.get("group"),
                cancel_on_error=config_data.get("cancel_on_error", True),
                depends_on=config_data.get("depends_on", []),
            )
            
            task = ExecutionTask(
                task=base_task,
                config=config,
            )
            
            # Restore timing
            task.created_time = datetime.fromisoformat(data["created_time"])
            
            # Restore state
            state = TaskState(data.get("state", "pending"))
            if not task.state_history.transitions:
                task.state_history.add_transition(
                    StateTransition(
                        from_state=None,
                        to_state=state,
                        timestamp=task.created_time,
                        reason="Task restored from queue",
                    )
                )
            else:
                task.state_history.transitions[-1].to_state = state
            
            return task
            
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"Failed to deserialize task: {e}")
            return None


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
