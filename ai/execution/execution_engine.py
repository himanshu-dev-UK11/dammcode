"""
ExecutionEngine — main orchestrator for AI execution.

Coordinates all AI actions in MyCodingMaster. Does NOT contain
any LLM-specific code. It only manages execution:

- Creating tasks from user prompts
- Scheduling tasks (priority, dependencies, groups)
- Tracking task state and lifecycle
- Pausing, stopping, cancelling tasks
- Monitoring execution
- Generating reports and metrics

The engine is the central hub that ties together:
- Task creation (from Planner, user prompts)
- Task scheduling (TaskScheduler)
- Task execution (TaskExecutor)
- Task monitoring (ExecutionMonitor)
- Task storage (ExecutionQueue)

Usage:
    engine = ExecutionEngine(event_bus, config_dir, project_root)
    
    # Submit a task
    task = engine.submit_task("Add logging to every agent")
    
    # Monitor progress
    engine.start_monitoring()
    
    # Cancel a task
    engine.cancel_task(task.id)
    
    # Generate report
    report = engine.get_execution_report(task.id)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.event_bus import EventBus
from core.logger import setup_logger

from ai.engine.task import Task as BaseTask, TaskStatus
from ai.context.context_engine import ContextEngine, ContextPackage
from ai.models.model_manager import ModelManager
from ai.editing.change_applier import ChangeApplier
from ai.verification.verification_engine import VerificationEngine

from .execution_task import ExecutionTask, ExecutionConfig, ExecutionMode, RetryStrategy
from .execution_queue import ExecutionQueue
from .task_scheduler import TaskScheduler
from .task_executor import TaskExecutor, ExecutorConfig
from .execution_monitor import ExecutionMonitor
from .execution_report import ExecutionReportGenerator
from .execution_metrics import ExecutionMetrics
from .task_state import TaskState
from ai.engine.engineering_task import EngineeringTask


@dataclass
class ExecutionEngineConfig:
    """
    Configuration for ExecutionEngine.
    
    Attributes:
        max_concurrent:  Maximum concurrent tasks
        max_retries:     Default retry attempts
        default_timeout: Default task timeout in seconds
        config_dir:      Directory for queue persistence
        project_root:    Project root directory
    """
    max_concurrent: int = 4
    max_retries: int = 2
    default_timeout: Optional[int] = 300
    config_dir: str = "config"
    project_root: Optional[str] = None


class ExecutionEngine:
    """
    Central orchestrator for AI execution in MyCodingMaster.
    
    This is the main entry point for all AI execution. It:
    - Accepts user prompts and creates ExecutionTasks
    - Schedules tasks using priority, dependencies, and groups
    - Executes tasks using a thread pool
    - Monitors execution and reports status
    - Integrates with all other engine components
    
    Key principles:
    - NO LLM code here - pure orchestration
    - All UI updates via EventBus
    - Non-blocking execution
    - Full cancellation support
    
    Usage:
        engine = ExecutionEngine(event_bus, config)
        
        # Submit tasks
        task1 = engine.submit_task("Add logging")
        task2 = engine.submit_task("Refactor database", priority=100)
        
        # Monitor
        engine.start_monitoring()
        
        # Cancel if needed
        engine.cancel_task(task1.id)
        
        # Get report
        report = engine.get_execution_report(task2.id)
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        config: ExecutionEngineConfig,
    ) -> None:
        self._event_bus = event_bus
        self._config = config
        self._config_dir = Path(config.config_dir)
        
        # Initialize components
        self._queue = ExecutionQueue(
            config_dir=str(self._config_dir),
            name="main",
        )
        
        self._scheduler = TaskScheduler(self._queue, str(self._config_dir))
        
        self._executor_config = ExecutorConfig(
            pool_size=config.max_concurrent,
            max_retries=config.max_retries,
            default_timeout=config.default_timeout,
        )
        self._executor = TaskExecutor(self._executor_config)
        
        self._monitor = ExecutionMonitor(self)
        self._reporter = ExecutionReportGenerator()
        self._metrics = ExecutionMetrics()
        
        # Integration components
        self._context_engine: Optional[ContextEngine] = None
        self._model_manager: Optional[ModelManager] = None
        self._change_applier: Optional[ChangeApplier] = None
        self._verification_engine: Optional[VerificationEngine] = None
        
        # Task tracking
        self._tasks: Dict[str, ExecutionTask] = {}
        self._shutdown = False
        
        # Setup callbacks
        self._executor_config.on_task_start = self._on_task_start
        self._executor_config.on_task_complete = self._on_task_complete
        self._executor_config.on_task_error = self._on_task_error
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        
        logger = setup_logger(__name__)
        logger.info("ExecutionEngine initialized")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def submit_task(
        self,
        prompt: str,
        config: Optional[ExecutionConfig] = None,
    ) -> ExecutionTask:
        """
        Submit a new task for execution.
        
        Args:
            prompt: User prompt text
            config: Optional execution configuration
            
        Returns:
            New ExecutionTask
        """
        task = ExecutionTask(
            task=BaseTask(original_prompt=prompt),
            config=config or ExecutionConfig(),
        )
        
        # Add to queue
        self._queue.enqueue(task)
        
        # Add to scheduler
        self._scheduler.add_task(task)
        
        # Track task
        self._tasks[task.id] = task
        
        # Publish event
        self._publish("execution_task_created", {
            "task_id": task.id,
            "prompt": prompt,
            "priority": task.config.priority,
        })
        
        logger = setup_logger(__name__)
        logger.info(f"Task submitted: {task.id[:8]} - {prompt[:40]}...")
        
        return task
    
    def submit_with_plan(
        self,
        prompt: str,
        plan: List[str],
        config: Optional[ExecutionConfig] = None,
    ) -> ExecutionTask:
        """
        Submit a task with a pre-defined plan.
        
        Args:
            prompt: User prompt text
            plan: Ordered list of step descriptions
            config: Optional execution configuration
            
        Returns:
            New ExecutionTask
        """
        task = self.submit_task(prompt, config)
        task.task.plan = plan
        
        # Update event
        self._publish("execution_task_plan_set", {
            "task_id": task.id,
            "steps": len(plan),
        })
        
        return task
        
    def submit_engineering_tasks(self, tasks: List[EngineeringTask]) -> None:
        """Submit multiple pre-decomposed EngineeringTasks."""
        # Group independent tasks for parallel execution
        groups = {}
        for t in tasks:
            if not t.dependencies:
                # No dependencies - can run immediately
                if "parallel_batch" not in groups:
                    groups["parallel_batch"] = []
                groups["parallel_batch"].append(t)
            else:
                # Has dependencies - sequential
                groups[f"seq_{t.id[:8]}"] = [t]
        
        # Submit tasks with proper execution config
        for group_name, group_tasks in groups.items():
            for t in group_tasks:
                # Convert EngineeringTask to ExecutionTask
                exec_task = ExecutionTask(
                    task=BaseTask(
                        original_prompt=t.description,
                        title=t.title,
                        id=t.id
                    ),
                    config=ExecutionConfig(
                        mode=ExecutionMode.BACKGROUND,
                        max_retries=2,
                        retry_strategy=RetryStrategy.EXPONENTIAL,
                        depends_on=t.dependencies,
                        group=group_name if len(group_tasks) > 1 else None,
                        cancel_on_error=True
                    )
                )
                
                # Copy engineering-specific attributes
                exec_task.engineering_metadata = {
                    "estimated_duration": t.estimated_duration,
                    "actual_duration": t.actual_duration,
                    "assigned_model": t.assigned_model,
                    "verification_state": t.verification_state,
                    "affected_files": t.affected_files,
                    "retry_count": t.retry_count,
                    "logs": t.logs
                }
                
                # Add to queue
                self._queue.enqueue(exec_task)
                # Add to scheduler
                self._scheduler.add_task(exec_task)
                # Track task
                self._tasks[exec_task.id] = exec_task
                
                self._publish("execution_task_created", {
                    "task_id": exec_task.id,
                    "title": t.title,
                    "priority": t.priority.value if hasattr(t.priority, 'value') else str(t.priority),
                    "group": group_name,
                    "dependencies": t.dependencies,
                    "estimated_duration": t.estimated_duration
                })
            
        logger = setup_logger(__name__)
        logger.info(f"Submitted {len(tasks)} engineering tasks in {len(groups)} execution groups.")
        self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """Start background monitoring."""
        if self._monitor_thread:
            return
        
        self._shutdown = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ExecutionMonitor"
        )
        self._monitor_thread.start()
        
        logger = setup_logger(__name__)
        logger.info("Execution monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._shutdown = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
        
        logger = setup_logger(__name__)
        logger.info("Execution monitoring stopped")
    
    def cancel_task(self, task_id: str, by_user: str = "user") -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID to cancel
            by_user: User who cancelled (for audit)
            
        Returns:
            True if cancelled
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        # Stop executor if running
        self._executor.cancel(task_id)
        
        # Update state
        task.state_history.add_transition(
            StateTransition(
                from_state=task.state,
                to_state=TaskState.CANCELLED,
                timestamp=datetime.utcnow(),
                reason=f"Cancelled by {by_user}",
            )
        )
        
        # Update task
        task.cancelled_by = by_user
        
        # Publish event
        self._publish("execution_task_cancelled", {
            "task_id": task_id,
            "cancelled_by": by_user,
        })
        
        logger = setup_logger(__name__)
        logger.info(f"Task cancelled: {task_id[:8]}")
        
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a running task."""
        # In production, this would pause the executor
        # For now, we just mark it as paused
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        task.state_history.add_transition(
            StateTransition(
                from_state=task.state,
                to_state=TaskState.PAUSED,
                timestamp=datetime.utcnow(),
                reason="Task paused",
            )
        )
        
        self._publish("execution_task_paused", {"task_id": task_id})
        
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        task.state_history.add_transition(
            StateTransition(
                from_state=task.state,
                to_state=TaskState.RUNNING,
                timestamp=datetime.utcnow(),
                reason="Task resumed",
            )
        )
        
        # Re-submit to executor
        self._executor.submit(task)
        
        self._publish("execution_task_resumed", {"task_id": task_id})
        
        return True
    
    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ExecutionTask]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def get_pending_tasks(self) -> List[ExecutionTask]:
        """Get all pending tasks."""
        return [t for t in self._tasks.values() if t.state == TaskState.PENDING]
    
    def get_running_tasks(self) -> List[ExecutionTask]:
        """Get all running tasks."""
        return [t for t in self._tasks.values() if t.state == TaskState.RUNNING]
    
    def get_completed_tasks(self) -> List[ExecutionTask]:
        """Get all completed tasks."""
        return [t for t in self._tasks.values() if t.state == TaskState.SUCCESS]
    
    def get_failed_tasks(self) -> List[ExecutionTask]:
        """Get all failed tasks."""
        return [t for t in self._tasks.values() if t.state == TaskState.FAILED]
    
    def get_execution_report(self, task_id: str) -> Optional[dict]:
        """Get a detailed execution report for a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        return self._reporter.generate(task)
    
    def get_metrics(self) -> dict:
        """Get execution metrics."""
        return self._metrics.get_metrics()
    
    def get_status(self) -> dict:
        """Get engine status."""
        return {
            "active_tasks": self._executor.get_active_count(),
            "pending_tasks": len(self.get_pending_tasks()),
            "running_tasks": len(self.get_running_tasks()),
            "completed_tasks": len(self.get_completed_tasks()),
            "failed_tasks": len(self.get_failed_tasks()),
            "executor_stats": self._executor.get_stats(),
            "queue_stats": self._queue.stats(),
        }
    
    # ── Integration points ──────────────────────────────────────────────────────
    
    def attach_context_engine(self, engine: ContextEngine) -> None:
        """Attach ContextEngine for context building."""
        self._context_engine = engine
    
    def attach_model_manager(self, manager: ModelManager) -> None:
        """Attach ModelManager for model execution."""
        self._model_manager = manager
    
    def attach_change_applier(self, applier: ChangeApplier) -> None:
        """Attach ChangeApplier for code changes."""
        self._change_applier = applier
    
    def attach_verification_engine(self, engine: VerificationEngine) -> None:
        """Attach VerificationEngine for quality checks."""
        self._verification_engine = engine
    
    # ── Private helpers ─────────────────────────────────────────────────────────
    
    def _on_task_start(self, task: ExecutionTask) -> None:
        """Handle task start event."""
        task.started_time = datetime.utcnow()
        
        self._publish("execution_task_started", {
            "task_id": task.id,
            "started_at": task.started_time.isoformat(),
        })
    
    def _on_task_complete(self, task: ExecutionTask, success: bool) -> None:
        """Handle task completion event."""
        task.completed_time = datetime.utcnow()
        
        if success:
            task.state_history.add_transition(
                StateTransition(
                    from_state=task.state,
                    to_state=TaskState.SUCCESS,
                    timestamp=datetime.utcnow(),
                    reason="Task completed successfully",
                )
            )
            
            self._metrics.record_task_success(task)
            
            self._publish("execution_task_completed", {
                "task_id": task.id,
                "completed_at": task.completed_time.isoformat(),
                "results_count": len(task.results),
            })
            
            # Run verification if attached
            if self._verification_engine:
                self._run_verification(task)
            
            # Apply changes if attached
            if self._change_applier:
                self._apply_changes(task)
            
        else:
            task.state_history.add_transition(
                StateTransition(
                    from_state=task.state,
                    to_state=TaskState.FAILED,
                    timestamp=datetime.utcnow(),
                    reason="Task failed",
                )
            )
            
            self._metrics.record_task_failure(task)
    
    def _on_task_error(self, task: ExecutionTask, error: Exception) -> None:
        """Handle task error event."""
        self._publish("execution_task_error", {
            "task_id": task.id,
            "error": str(error),
        })
    
    def _run_verification(self, task: ExecutionTask) -> None:
        """Run verification on completed task via VerificationEngine."""
        if not self._verification_engine:
            return
        try:
            from ai.verification.verification_task import VerificationTask
            from ai.editing.change_request import ChangeRequest, ChangeStatus

            # Collect modified files from task results
            files: list = []
            for r in task.results:
                # Results may embed file paths in output as "FILE: <path>"
                for line in (r.output or "").splitlines():
                    if line.startswith("FILE:"):
                        files.append(line[5:].strip())

            if not files:
                return   # nothing to verify

            cr = ChangeRequest(
                request_id=task.id,
                user_prompt=task.task.original_prompt,
                status=ChangeStatus.PENDING,
            )
            vtask = VerificationTask.create(
                edit_request_id=cr.request_id,
                user_prompt=cr.user_prompt,
                files_modified=files,
                config=self._verification_engine._config,
                max_retries=1,
            )
            result = self._verification_engine.verify(vtask)
            logger = setup_logger(__name__)
            logger.info(
                f"Verification for task {task.id[:8]}: "
                f"success={result.success}, "
                f"errors={result.total_errors}"
            )
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"Verification failed for task {task.id[:8]}: {e}")

    def _apply_changes(self, task: ExecutionTask) -> None:
        """Apply code changes produced by the task via ChangeApplier."""
        if not self._change_applier:
            return
        try:
            from ai.editing.change_set import ChangeSet, ChangeOperation, OperationType
            from ai.editing.change_request import ChangeRequest, ChangeStatus

            # Only apply if any result carries explicit "CREATE:" / "MODIFY:" markers
            operations = []
            for r in task.results:
                for line in (r.output or "").splitlines():
                    if line.startswith("CREATE:"):
                        path = line[7:].strip()
                        operations.append(ChangeOperation(
                            op_type=OperationType.CREATE,
                            source_path=path,
                            content="",
                        ))
                    elif line.startswith("MODIFY:"):
                        path = line[7:].strip()
                        operations.append(ChangeOperation(
                            op_type=OperationType.MODIFY,
                            source_path=path,
                            hunks=[],
                        ))

            if not operations:
                return

            cs = ChangeSet(operations=operations)
            cr = ChangeRequest(
                request_id=task.id,
                user_prompt=task.task.original_prompt,
                status=ChangeStatus.PENDING,
            )
            result = self._change_applier.apply(cs, cr)
            logger = setup_logger(__name__)
            logger.info(
                f"ChangeApplier for task {task.id[:8]}: "
                f"applied={result.applied_count}, failed={result.failed_count}"
            )
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"ChangeApplier failed for task {task.id[:8]}: {e}")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while not self._shutdown:
            try:
                # Get ready tasks from scheduler
                ready_tasks = self._scheduler.get_ready_tasks()
                
                for task in ready_tasks:
                    if task.state == TaskState.SCHEDULED:
                        # Dequeue and execute
                        self._queue.dequeue()
                        self._executor.submit(task)
                        
                        # Publish detailed event
                        self._publish("execution_task_dispatched", {
                            "task_id": task.id,
                            "title": getattr(task, 'title', task.task.title if hasattr(task, 'task') else 'Unknown'),
                            "state": task.state.value
                        })
                
                # Update monitor
                status = self.get_status()
                self._publish("execution_status_update", status)
                
                # Publish individual task updates for UI
                for task_id, task in self._tasks.items():
                    if not task.is_terminal:
                        self._publish("execution_task_update", {
                            "task_id": task_id,
                            "title": getattr(task, 'title', task.task.title if hasattr(task, 'task') else 'Unknown'),
                            "state": task.state.value,
                            "status": task.status.value if hasattr(task, 'status') else task.state.value,
                            "progress": len(task.results) if hasattr(task, 'results') else 0
                        })
                
                # Small delay to avoid tight loop
                time.sleep(0.1)
                
            except Exception as e:
                logger = setup_logger(__name__)
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1.0)
    
    def _publish(self, event_type: str, data: dict) -> None:
        """Publish event to EventBus."""
        try:
            self._event_bus.publish(event_type, data)
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"Failed to publish event: {e}")


# Convenience factory function
def create_execution_engine(
    event_bus: EventBus,
    config_dir: str = "config",
    project_root: Optional[str] = None,
    max_concurrent: int = 4,
    max_retries: int = 2,
) -> ExecutionEngine:
    """
    Factory function to create and configure an ExecutionEngine.
    
    Args:
        event_bus: EventBus instance
        config_dir: Directory for queue persistence
        project_root: Project root directory
        max_concurrent: Maximum concurrent tasks
        max_retries: Default retry attempts
        
    Returns:
        Configured ExecutionEngine
    """
    config = ExecutionEngineConfig(
        config_dir=config_dir,
        project_root=project_root,
        max_concurrent=max_concurrent,
        max_retries=max_retries,
    )
    
    return ExecutionEngine(event_bus, config)
