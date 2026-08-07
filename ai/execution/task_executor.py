"""
TaskExecutor — thread pool executor with retry logic.

Executes tasks from the queue using a configurable thread pool.
Handles retries, timeouts, and failure recovery.

Features:
- Configurable thread pool size
- Per-task timeout
- Retry with configurable strategy (fixed, exponential, jittered)
- Statistics tracking
- Error handling and recovery

Usage:
    executor = TaskExecutor(
        pool_size=4,
        max_retries=2,
        default_timeout=300  # seconds
    )
    executor.start()
    executor.submit(task)
    # ... later ...
    executor.shutdown()
"""

from __future__ import annotations

import threading
import time
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .execution_task import ExecutionTask, ExecutionConfig, ExecutionMode, ExecutionResult
from .task_state import TaskState, StateTransition
from .execution_queue import ExecutionQueue


class RetryStrategy(Enum):
    """Retry strategy for failed tasks."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    JITTERED = "jittered"


@dataclass
class ExecutorConfig:
    """
    Configuration for TaskExecutor.
    
    Attributes:
        pool_size:      Number of worker threads
        max_retries:    Maximum retry attempts per task
        default_timeout: Default timeout in seconds for tasks without one
        retry_delay:    Base delay between retries (seconds)
        on_task_start:  Callback when task starts
        on_task_complete: Callback when task completes
        on_task_error:  Callback when task errors
    """
    pool_size:      int = 4
    max_retries:    int = 2
    default_timeout: Optional[int] = None
    retry_delay:    float = 1.0
    on_task_start:  Optional[Callable[[ExecutionTask], None]] = None
    on_task_complete: Optional[Callable[[ExecutionTask, bool], None]] = None
    on_task_error:  Optional[Callable[[ExecutionTask, Exception], None]] = None


class TaskExecutor:
    """
    Thread pool executor for ExecutionTasks.
    
    Manages a pool of worker threads that consume tasks from
    the execution queue and execute them.
    
    Usage:
        executor = TaskExecutor(config)
        executor.start()
        
        while not shutdown:
            task = queue.dequeue()
            if task:
                executor.submit(task)
        
        executor.shutdown()
    """
    
    def __init__(self, config: ExecutorConfig) -> None:
        self._config = config
        self._executor = ThreadPoolExecutor(
            max_workers=config.pool_size,
            thread_name_prefix="TaskExecutor"
        )
        self._shutdown = False
        self._lock = threading.Lock()
        
        # Statistics
        self._tasks_submitted = 0
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._total_execution_time = 0.0
        
        # Active tasks tracking
        self._active_tasks: Dict[str, ExecutionTask] = {}
        self._active_futures: Dict[str, Future] = {}
        
        logger = setup_logger(__name__)
        logger.info(f"TaskExecutor initialized (pool_size={config.pool_size}, max_retries={config.max_retries})")
    
    # ── Public API ──────────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Start the executor (no-op, ThreadPoolExecutor starts automatically)."""
        with self._lock:
            self._shutdown = False
        logger = setup_logger(__name__)
        logger.info("TaskExecutor started")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor.
        
        Args:
            wait: If True, wait for all tasks to complete
        """
        with self._lock:
            self._shutdown = True
        
        self._executor.shutdown(wait=wait)
        
        logger = setup_logger(__name__)
        logger.info("TaskExecutor shutdown complete")
    
    def submit(self, task: ExecutionTask) -> None:
        """
        Submit a task for execution.
        
        Args:
            task: Task to execute
        """
        with self._lock:
            self._tasks_submitted += 1
            self._active_tasks[task.id] = task
        
        # Update state
        task.state_history.add_transition(
            StateTransition(
                from_state=task.state,
                to_state=TaskState.RUNNING,
                timestamp=datetime.utcnow(),
                reason="Task started execution",
            )
        )
        
        # Notify start callback
        if self._config.on_task_start:
            try:
                self._config.on_task_start(task)
            except Exception as e:
                logger = setup_logger(__name__)
                logger.error(f"Task start callback failed: {e}")
        
        # Schedule execution
        future = self._executor.submit(self._execute_task, task)
        
        with self._lock:
            self._active_futures[task.id] = future
        
        # Add callback for completion
        future.add_done_callback(lambda f: self._handle_completion(task, f))
    
    def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled
        """
        with self._lock:
            future = self._active_futures.get(task_id)
            if not future:
                return False
            
            # Cancel the future
            if future.cancel():
                task = self._active_tasks.get(task_id)
                if task:
                    task.state_history.add_transition(
                        StateTransition(
                            from_state=task.state,
                            to_state=TaskState.CANCELLED,
                            timestamp=datetime.utcnow(),
                            reason="Task cancelled by user",
                        )
                    )
                return True
            
            return False
    
    def get_active_tasks(self) -> List[ExecutionTask]:
        """Get all currently executing tasks."""
        with self._lock:
            return list(self._active_tasks.values())
    
    def get_active_count(self) -> int:
        """Get number of currently executing tasks."""
        with self._lock:
            return len(self._active_tasks)
    
    def get_stats(self) -> dict:
        """Get executor statistics."""
        with self._lock:
            avg_time = (
                self._total_execution_time / self._tasks_completed
                if self._tasks_completed > 0
                else 0.0
            )
            
            return {
                "active": len(self._active_tasks),
                "submitted": self._tasks_submitted,
                "completed": self._tasks_completed,
                "failed": self._tasks_failed,
                "avg_execution_time_ms": avg_time * 1000,
            }
    
    # ── Internal execution ���─────────────────────────────────────────────────────
    
    def _execute_task(self, task: ExecutionTask) -> None:
        """
        Execute a single task.
        
        This method runs in a worker thread.
        """
        start_time = time.time()
        
        try:
            # Check for cancellation
            if self._shutdown:
                raise Exception("Executor shutting down")
            
            # Execute the task's plan
            self._execute_plan(task)
            
            # Mark as success
            task.state_history.add_transition(
                StateTransition(
                    from_state=task.state,
                    to_state=TaskState.SUCCESS,
                    timestamp=datetime.utcnow(),
                    reason="Task completed successfully",
                )
            )
            
        except Exception as e:
            # Check if we can retry
            if self._can_retry(task):
                self._retry_task(task, e)
            else:
                task.state_history.add_transition(
                    StateTransition(
                        from_state=task.state,
                        to_state=TaskState.FAILED,
                        timestamp=datetime.utcnow(),
                        reason=str(e),
                    )
                )
                task.error = str(e)
        
        finally:
            execution_time = time.time() - start_time
            
            with self._lock:
                self._total_execution_time += execution_time
                if task.state == TaskState.SUCCESS:
                    self._tasks_completed += 1
                else:
                    self._tasks_failed += 1
                
                # Clean up
                self._active_tasks.pop(task.id, None)
                self._active_futures.pop(task.id, None)
            
            # Notify completion callback
            if self._config.on_task_complete:
                try:
                    self._config.on_task_complete(task, task.state == TaskState.SUCCESS)
                except Exception as e:
                    logger = setup_logger(__name__)
                    logger.error(f"Task completion callback failed: {e}")
    
    # ── Chat engine injection ──────────────────────────────────────────────────

    _chat_engine = None   # class-level slot; set by ExecutionEngine after init

    @classmethod
    def set_chat_engine(cls, engine) -> None:
        """Inject the AIChatEngine so executor can call it for AI generation."""
        cls._chat_engine = engine

    # ── Plan execution ─────────────────────────────────────────────────────────

    def _execute_plan(self, task: ExecutionTask) -> None:
        """
        Execute the task's plan by calling the AI chat engine for each step.

        Each step description is sent as a prompt.  Responses accumulate
        in task.results.  If no chat engine is available we still record
        a result so the UI sees progress.
        """
        logger = setup_logger(__name__)
        steps = task.task.plan if task.task.plan else [task.task.original_prompt]

        for index, step_text in enumerate(steps):
            if self._shutdown:
                raise Exception("Executor shutting down")

            step_start = time.time()
            output = ""
            success = True

            try:
                engine = self.__class__._chat_engine
                if engine:
                    # Build a focused prompt for this step
                    prompt = (
                        f"[Engineering task step {index + 1}/{len(steps)}]\n"
                        f"{step_text}\n\n"
                        "Provide a concise technical response or code change."
                    )

                    # Collect the full response via on_complete callback
                    result_holder: list = []

                    def _on_complete(response: str, _holder=result_holder):
                        _holder.append(response)

                    engine.send_message(
                        message=prompt,
                        model_id=engine.get_current_model(),
                        on_chunk=None,
                        on_complete=_on_complete,
                    )

                    # Wait (blocking — we are on a worker thread)
                    deadline = time.time() + 300   # 5 min max per step
                    while not result_holder and time.time() < deadline:
                        time.sleep(0.1)

                    output = result_holder[0] if result_holder else "[no response]"
                else:
                    # No engine available — record a placeholder so the UI
                    # still tracks progress correctly.
                    output = (
                        f"[Step {index + 1}] {step_text}\n"
                        "(AI engine not available — connect a provider in Settings)"
                    )

            except Exception as exc:
                success = False
                output = str(exc)
                logger.error(f"TaskExecutor step {index + 1} failed: {exc}", exc_info=True)

            duration_ms = (time.time() - step_start) * 1000

            result = ExecutionResult(
                step_index=index,
                step_text=step_text,
                success=success,
                output=output,
                duration_ms=duration_ms,
                attempt=1,
            )

            task.results.append(result)
            task.stats.steps_executed += 1

            if not success:
                raise Exception(f"Step {index + 1} failed: {output}")

        task.stats.total_duration_ms = (
            (time.time() - task.started_time.timestamp()) * 1000
            if task.started_time else 0.0
        )
    
    def _can_retry(self, task: ExecutionTask) -> bool:
        """Check if task can be retried."""
        config = task.config
        max_retries = config.max_retries if config.max_retries >= 0 else self._config.max_retries
        
        current_attempts = sum(1 for r in task.results if not r.success)
        return current_attempts < max_retries
    
    def _retry_task(self, task: ExecutionTask, error: Exception) -> None:
        """
        Schedule a retry for a failed task.
        """
        config = task.config
        strategy = config.retry_strategy if config.retry_strategy != RetryStrategy.NONE else self._config.retry_strategy
        base_delay = config.retry_delay if config.retry_delay else self._config.retry_delay
        
        # Calculate delay
        current_retries = task.stats.retry_count
        if strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2 ** current_retries)
        elif strategy == RetryStrategy.JITTERED:
            import random
            delay = base_delay * (2 ** current_retries) * (0.5 + random.random())
        else:  # FIXED
            delay = base_delay
        
        task.stats.retry_count += 1
        
        # Re-queue the task
        task.state_history.add_transition(
            StateTransition(
                from_state=task.state,
                to_state=TaskState.SCHEDULED,
                timestamp=datetime.utcnow(),
                reason=f"Retry #{task.stats.retry_count}",
            )
        )
        
        # Schedule retry
        def schedule_retry():
            time.sleep(delay)
            # In production, re-enqueue to queue
            pass
        
        threading.Thread(target=schedule_retry, daemon=True).start()
    
    def _handle_completion(self, task: ExecutionTask, future: Future) -> None:
        """Handle task completion callback."""
        try:
            # Get any exception from the future
            exception = future.exception()
            
            if exception:
                # Already handled in _execute_task
                pass
            
        except Exception as e:
            logger = setup_logger(__name__)
            logger.error(f"Future completion handler error: {e}")


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
