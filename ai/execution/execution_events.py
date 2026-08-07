"""
ExecutionEvents — event definitions for UI integration.

Defines all events published by the ExecutionEngine for UI
integration. UI components subscribe to these events to
update in real-time without polling.

Event Categories:
- Task lifecycle: creation, scheduling, execution, completion
- Progress updates: step progress, model selection, tool execution
- Errors and warnings: failures, cancellations, timeouts
- Status updates: overall engine status

Usage:
    # In UI code
    event_bus.subscribe(ExecutionEvents.TASK_CREATED, on_task_created)
    event_bus.subscribe(ExecutionEvents.TASK_COMPLETED, on_task_completed)
    event_bus.subscribe(ExecutionEvents.STATUS_UPDATE, on_status_update)
"""

from __future__ import annotations

from typing import Dict, Any


class ExecutionEvents:
    """
    Event names for ExecutionEngine events.
    
    All events follow the pattern: execution_<category>_<action>
    """
    
    # ── Task lifecycle events ──────────────────────────────────────────────────
    
    TASK_CREATED = "execution_task_created"
    """
    Fired when a new task is created.
    
    Payload:
        task_id:    Task ID
        prompt:     User prompt
        priority:   Task priority
    """
    
    TASK_PLAN_SET = "execution_task_plan_set"
    """
    Fired when a task's plan is set.
    
    Payload:
        task_id: Task ID
        steps:   Number of steps in plan
    """
    
    TASK_STARTED = "execution_task_started"
    """
    Fired when a task starts execution.
    
    Payload:
        task_id:   Task ID
        started_at: Timestamp (ISO format)
    """
    
    TASK_COMPLETED = "execution_task_completed"
    """
    Fired when a task completes successfully.
    
    Payload:
        task_id:      Task ID
        completed_at: Timestamp (ISO format)
        results_count: Number of step results
    """
    
    TASK_FAILED = "execution_task_failed"
    """
    Fired when a task fails.
    
    Payload:
        task_id: Task ID
        error:   Error message
    """
    
    TASK_CANCELLED = "execution_task_cancelled"
    """
    Fired when a task is cancelled.
    
    Payload:
        task_id:      Task ID
        cancelled_by: User who cancelled
    """
    
    TASK_PAUSED = "execution_task_paused"
    """
    Fired when a task is paused.
    
    Payload:
        task_id: Task ID
    """
    
    TASK_RESUMED = "execution_task_resumed"
    """
    Fired when a task is resumed.
    
    Payload:
        task_id: Task ID
    """
    
    TASK_STATE_CHANGED = "execution_task_state_changed"
    """
    Fired when a task's state changes.
    
    Payload:
        task_id:   Task ID
        old_state: Previous state
        new_state: New state
    """
    
    # ── Step execution events ──────────────────────────────────────────────────
    
    STEP_STARTED = "execution_step_started"
    """
    Fired when a step starts.
    
    Payload:
        task_id:   Task ID
        step_index: Step index
        step_text:  Step description
    """
    
    STEP_COMPLETED = "execution_step_completed"
    """
    Fired when a step completes.
    
    Payload:
        task_id:  Task ID
        step_index: Step index
        output:   Step output
        duration_ms: Duration in milliseconds
    """
    
    STEP_FAILED = "execution_step_failed"
    """
    Fired when a step fails.
    
    Payload:
        task_id:   Task ID
        step_index: Step index
        error:     Error message
        attempts:   Number of attempts
    """
    
    # ── Model and tool events ──────────────────────────────────────────────────
    
    MODEL_SELECTED = "execution_model_selected"
    """
    Fired when a model is selected for execution.
    
    Payload:
        task_id:  Task ID
        model:    Model name
        reason:   Reason for selection
    """
    
    MODEL_EXECUTING = "execution_model_executing"
    """
    Fired when a model is executing.
    
    Payload:
        task_id:  Task ID
        model:    Model name
        context_size: Token count
    """
    
    MODEL_RESPONSE_RECEIVED = "execution_model_response_received"
    """
    Fired when a model response is received.
    
    Payload:
        task_id:  Task ID
        model:    Model name
        response_length: Response length
        latency_ms:    Latency in milliseconds
    """
    
    TOOL_EXECUTING = "execution_tool_executing"
    """
    Fired when a tool starts executing.
    
    Payload:
        task_id: Task ID
        tool:    Tool name
        action:  Action being performed
    """
    
    TOOL_COMPLETED = "execution_tool_completed"
    """
    Fired when a tool completes.
    
    Payload:
        task_id:  Task ID
        tool:     Tool name
        output:   Tool output
        duration_ms: Duration in milliseconds
    """
    
    # ── Verification events ────────────────────────────────────────────────────
    
    VERIFICATION_STARTED = "execution_verification_started"
    """
    Fired when verification starts.
    
    Payload:
        task_id: Task ID
        verifiers: List of verifiers to run
    """
    
    VERIFICATION_COMPLETE = "execution_verification_complete"
    """
    Fired when verification completes.
    
    Payload:
        task_id:   Task ID
        success:   True if all verifiers passed
        report:    Verification report
    """
    
    # ── Progress and metrics events ────────────────────────────────────────────
    
    PROGRESS_UPDATE = "execution_progress_update"
    """
    Fired periodically with progress updates.
    
    Payload:
        task_id:      Task ID
        progress:     Progress percentage (0-100)
        current_step: Current step index
        total_steps:  Total steps
    """
    
    STATUS_UPDATE = "execution_status_update"
    """
    Fired with engine-wide status updates.
    
    Payload:
        active_tasks:   Number of active tasks
        pending_tasks:  Number of pending tasks
        running_tasks:  Number of running tasks
        completed_tasks: Number of completed tasks
        failed_tasks:   Number of failed tasks
        executor_stats: Executor statistics
        queue_stats:    Queue statistics
    """
    
    METRICS_UPDATE = "execution_metrics_update"
    """
    Fired with metrics updates.
    
    Payload:
        tasks_executed:    Total tasks executed
        success_rate:      Success rate (0-100)
        avg_execution_time: Average execution time in ms
        retry_rate:        Retry rate (0-100)
    """
    
    # ── Error and warning events ───────────────────────────────────────────────
    
    ERROR_OCCURRED = "execution_error_occurred"
    """
    Fired when an error occurs.
    
    Payload:
        task_id: Task ID
        error:   Error message
        level:   Error level (warning/error/critical)
    """
    
    WARNING_OCCURRED = "execution_warning_occurred"
    """
    Fired when a warning occurs.
    
    Payload:
        task_id: Task ID
        warning: Warning message
    """
    
    # ── Utility methods ────────────────────────────────────────────────────────
    
    @classmethod
    def get_all_events(cls) -> list[str]:
        """Return all event names."""
        return [
            attr for attr in dir(cls)
            if attr.isupper()
            and not attr.startswith("_")
            and isinstance(getattr(cls, attr), str)
        ]
    
    @classmethod
    def get_event_description(cls, event_name: str) -> str:
        """
        Get description for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Event description, or "Unknown event" if not found
        """
        attr = getattr(cls, event_name, None)
        if attr is None:
            return "Unknown event"
        
        doc = getattr(cls, event_name).__doc__
        return doc or "No description available"


# Event payload type hints
EventPayload = Dict[str, Any]

# Type alias for event handlers (Python 3.9+ compatible)
try:
    from typing import Callable
    EventCallback = Callable[[EventPayload], None]
except ImportError:
    EventCallback = callable


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
