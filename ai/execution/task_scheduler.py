"""
TaskScheduler — task scheduling with dependencies and groups.

Manages task scheduling for the ExecutionEngine with support for:
- Sequential execution (default)
- Parallel execution (tasks in same group)
- Dependencies between tasks (depends_on field)
- Priority ordering
- Task groups for related tasks

The scheduler uses a two-phase approach:
1. Dependency resolution: Build DAG, detect cycles, topological sort
2. Schedule execution: Determine execution order based on priorities and dependencies
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .execution_task import ExecutionTask, ExecutionConfig, ExecutionMode
from .task_state import TaskState, TaskStateHistory, StateTransition
from .execution_queue import ExecutionQueue


class DependencyStatus(Enum):
    """Status of a task's dependencies."""
    WAITING    = "waiting"    # Some dependencies not completed
    BLOCKED    = "blocked"    # A dependency failed/cancelled
    READY      = "ready"      # All dependencies satisfied
    NO_DEPS    = "no_deps"    # No dependencies defined


@dataclass
class ScheduleResult:
    """
    Result of scheduling operation.
    
    Attributes:
        scheduled:   List of tasks scheduled for execution
        waiting:     List of tasks waiting for dependencies
        blocked:     List of tasks blocked by failed dependencies
        errors:      List of error messages
    """
    scheduled: List[str] = field(default_factory=list)
    waiting:   List[str] = field(default_factory=list)
    blocked:   List[str] = field(default_factory=list)
    errors:    List[str] = field(default_factory=list)


class TaskScheduler:
    """
    Task scheduler with dependency and group support.
    
    The scheduler maintains a dependency graph and uses it to
    determine which tasks are ready to execute.
    
    Key behaviors:
    - Tasks with no dependencies are scheduled first
    - Tasks in the same group can run in parallel
    - Tasks with unsatisfied dependencies wait
    - Tasks with failed dependencies are blocked
    
    Usage:
        scheduler = TaskScheduler(queue, config_dir)
        scheduler.add_task(task)
        ready, waiting = scheduler.get_ready_tasks()
        scheduler.mark_completed(task_id)
    """
    
    def __init__(
        self,
        queue: ExecutionQueue,
        config_dir: str,
    ) -> None:
        self._queue = queue
        self._config_dir = Path(config_dir)
        self._dependency_graph: Dict[str, Set[str]] = {}  # task_id → dependencies
        self._dependents: Dict[str, Set[str]] = {}        # task_id → dependents
        self._lock = threading.RLock()
        self._grouped_tasks: Dict[str, List[str]] = defaultdict(list)  # group → task_ids
        
        logger = setup_logger(__name__)
        logger.info("TaskScheduler initialized")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def add_task(self, task: ExecutionTask) -> bool:
        """
        Add a task to the scheduler.
        
        Args:
            task: Task to add
            
        Returns:
            True if added successfully
        """
        with self._lock:
            task_id = task.id
            
            # Register dependencies
            deps = set(task.config.depends_on)
            self._dependency_graph[task_id] = deps
            self._dependents[task_id] = set()
            
            # Update reverse dependency mapping
            for dep_id in deps:
                if dep_id in self._dependents:
                    self._dependents[dep_id].add(task_id)
            
            # Register group
            if task.config.group:
                self._grouped_tasks[task.config.group].append(task_id)
            
            # Update task state
            task.state_history.add_transition(
                StateTransition(
                    from_state=task.state,
                    to_state=TaskState.SCHEDULED,
                    timestamp=datetime.utcnow(),
                    reason="Task scheduled",
                )
            )
            
            return True
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the scheduler.
        
        Args:
            task_id: ID of task to remove
            
        Returns:
            True if removed
        """
        with self._lock:
            if task_id not in self._dependency_graph:
                return False
            
            # Remove from dependency graph
            deps = self._dependency_graph.pop(task_id)
            for dep_id in deps:
                if dep_id in self._dependents:
                    self._dependents[dep_id].discard(task_id)
            
            # Remove dependents
            self._dependents.pop(task_id, None)
            
            # Remove from groups
            for group, task_ids in self._grouped_tasks.items():
                if task_id in task_ids:
                    task_ids.remove(task_id)
            
            return True
    
    def get_ready_tasks(self) -> List[ExecutionTask]:
        """
        Get all tasks that are ready to execute.
        
        A task is ready if:
        - All its dependencies are completed successfully
        - No dependency failed/cancelled
        - Task itself is in PENDING or SCHEDULED state
        
        Returns:
            List of ready tasks, ordered by priority
        """
        with self._lock:
            ready = []
            
            for task_id, deps in self._dependency_graph.items():
                task = self._queue.get_task(task_id)
                if not task:
                    continue
                
                # Skip if not in pending/scheduled state
                if task.state not in (TaskState.PENDING, TaskState.SCHEDULED):
                    continue
                
                # Check dependencies
                status = self._check_dependencies(deps)
                
                if status == DependencyStatus.READY or status == DependencyStatus.NO_DEPS:
                    ready.append(task)
            
            # Sort by priority (higher first)
            ready.sort(key=lambda t: t.config.priority or 50, reverse=True)
            
            return ready
    
    def get_group_ready_tasks(self, group: str) -> List[ExecutionTask]:
        """
        Get all ready tasks in a group.
        
        Args:
            group: Group name
            
        Returns:
            List of ready tasks in group
        """
        with self._lock:
            group_tasks = self._grouped_tasks.get(group, [])
            ready = []
            
            for task_id in group_tasks:
                task = self._queue.get_task(task_id)
                if not task:
                    continue
                
                if task.state not in (TaskState.PENDING, TaskState.SCHEDULED):
                    continue
                
                deps = self._dependency_graph.get(task_id, set())
                status = self._check_dependencies(deps)
                
                if status == DependencyStatus.READY or status == DependencyStatus.NO_DEPS:
                    ready.append(task)
            
            ready.sort(key=lambda t: t.config.priority or 50, reverse=True)
            return ready
    
    def get_dependents(self, task_id: str) -> List[ExecutionTask]:
        """
        Get all tasks that depend on this task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of dependent tasks
        """
        with self._lock:
            dependent_ids = self._dependents.get(task_id, set())
            return [
                self._queue.get_task(tid)
                for tid in dependent_ids
                if self._queue.get_task(tid)
            ]
    
    def mark_completed(self, task_id: str, success: bool = True) -> List[str]:
        """
        Mark a task as completed and update dependents.
        
        Args:
            task_id: Completed task ID
            success: True if task succeeded
            
        Returns:
            List of task IDs that are now ready due to this completion
        """
        with self._lock:
            now_ready = []
            
            # Update dependents
            for dep_id in self._dependents.get(task_id, set()):
                task = self._queue.get_task(dep_id)
                if not task:
                    continue
                
                if task.state in (TaskState.PENDING, TaskState.SCHEDULED):
                    status = self._check_dependencies(self._dependency_graph.get(dep_id, set()))
                    
                    if status == DependencyStatus.READY:
                        now_ready.append(dep_id)
                    elif status == DependencyStatus.BLOCKED and success:
                        # Task was waiting but now unblocked
                        now_ready.append(dep_id)
            
            return now_ready
    
    def mark_failed(self, task_id: str) -> List[str]:
        """
        Mark a task as failed and block dependents.
        
        Args:
            task_id: Failed task ID
            
        Returns:
            List of blocked task IDs
        """
        with self._lock:
            blocked = []
            
            for dep_id in self._dependents.get(task_id, set()):
                task = self._queue.get_task(dep_id)
                if task and task.state == TaskState.PENDING:
                    task.state_history.add_transition(
                        StateTransition(
                            from_state=task.state,
                            to_state=TaskState.PENDING,
                            timestamp=datetime.utcnow(),
                            reason=f"Dependent task {task_id[:8]} failed",
                        )
                    )
                    blocked.append(dep_id)
            
            return blocked
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the dependency graph.
        
        Returns:
            List of cycles (each cycle is a list of task IDs)
        """
        with self._lock:
            cycles = []
            visited = set()
            rec_stack = set()
            path = []
            
            def dfs(node: str) -> None:
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for dep in self._dependency_graph.get(node, set()):
                    if dep not in visited:
                        dfs(dep)
                    elif dep in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep)
                        cycle = path[cycle_start:] + [dep]
                        cycles.append(cycle)
                
                path.pop()
                rec_stack.remove(node)
            
            for node in self._dependency_graph:
                if node not in visited:
                    dfs(node)
            
            return cycles
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _check_dependencies(self, deps: Set[str]) -> DependencyStatus:
        """Check dependency status for a task."""
        if not deps:
            return DependencyStatus.NO_DEPS
        
        all_completed = True
        any_failed = False
        
        for dep_id in deps:
            task = self._queue.get_task(dep_id)
            if not task:
                all_completed = False
                continue
            
            if task.state_history.is_terminal:
                if not task.success:
                    any_failed = True
            else:
                all_completed = False
        
        if any_failed:
            return DependencyStatus.BLOCKED
        if all_completed:
            return DependencyStatus.READY
        return DependencyStatus.WAITING


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
