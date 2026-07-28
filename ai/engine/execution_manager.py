"""
ExecutionManager — step-by-step plan coordinator.

Responsible for taking a completed plan (a list of ordered steps)
and executing each step through the ToolManager, while:
  - Monitoring for failures.
  - Retrying failed steps (up to a configurable limit).
  - Stopping safely when a step cannot be recovered.
  - Publishing granular progress events to the EventBus so the
    UI stays informed without polling.

This manager contains ZERO AI reasoning. It is a pure
coordinator — it reads the plan it is given and carries it out.
All intelligence lives in the agents that produce the plan.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from core.event_bus import EventBus
from ai.engine.task import Task, TaskStatus
from ai.engine.tool_manager import ToolManager

logger = setup_logger(__name__)


class StepResult:
    """
    Result of executing one step in a plan.

    Attributes:
        step_index:  Zero-based position in the plan list.
        step_text:   The original step description string.
        success:     True if the step completed without error.
        output:      Any output produced by the step.
        error:       Error message if the step failed.
        attempts:    How many times the step was attempted.
    """

    def __init__(
        self,
        step_index: int,
        step_text: str,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        attempts: int = 1,
    ) -> None:
        self.step_index = step_index
        self.step_text  = step_text
        self.success    = success
        self.output     = output
        self.error      = error
        self.attempts   = attempts

    def __repr__(self) -> str:
        return (
            f"StepResult(step={self.step_index}, success={self.success}, "
            f"attempts={self.attempts})"
        )


class ExecutionManager:
    """
    Coordinates the execution of a plan against a Task.

    Receives a Task (for context and status tracking) and its
    associated plan (list of steps), then runs each step through
    the ToolManager. All progress is broadcast via EventBus so
    the UI and memory systems can react in real time.

    Args:
        event_bus:    The application-wide EventBus instance.
        tool_manager: The shared ToolManager for all tool calls.
        max_retries:  How many times to retry a failing step before aborting.

    Events published:
        "execution_started"      — payload: {task_id, total_steps}
        "step_started"           — payload: {task_id, step_index, step_text}
        "step_completed"         — payload: {task_id, step_index, output}
        "step_failed"            — payload: {task_id, step_index, error, attempts}
        "execution_completed"    — payload: {task_id, results}
        "execution_failed"       — payload: {task_id, failed_step_index, error}
    """

    def __init__(
        self,
        event_bus: EventBus,
        tool_manager: ToolManager,
        max_retries: int = 2,
    ) -> None:
        self.event_bus    = event_bus
        self.tool_manager = tool_manager
        self.max_retries  = max_retries
        self._stop_requested = False
        logger.info(f"ExecutionManager initialized (max_retries={max_retries}).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_plan(self, task: Task, plan: List[str]) -> List[StepResult]:
        """
        Execute each step in the plan sequentially.

        Args:
            task: The Task being worked on. Its status will be mutated.
            plan: Ordered list of step description strings (from PlannerAgent).

        Returns:
            List of StepResult objects, one per plan step.

        Behaviour:
            - Each step is attempted up to (1 + max_retries) times.
            - If a step fails all attempts, execution halts and the task
              is marked as FAILED.
            - Calling `request_stop()` will abort gracefully after the
              current step completes.

        TODO:
            - Parse step text to derive the correct tool and action.
            - Implement actual tool dispatch per step type.
        """
        self._stop_requested = False
        task.status = TaskStatus.EXECUTING
        total_steps = len(plan)

        logger.info(f"Beginning execution of task {task.id[:8]} with {total_steps} steps.")
        self._publish("execution_started", {"task_id": task.id, "total_steps": total_steps})

        results: List[StepResult] = []

        for index, step_text in enumerate(plan):
            if self._stop_requested:
                logger.warning(f"Stop requested — halting execution at step {index}.")
                task.status = TaskStatus.CANCELLED
                break

            step_result = self._execute_step(task, index, step_text)
            results.append(step_result)

            if not step_result.success:
                task.mark_failed()
                self._publish(
                    "execution_failed",
                    {
                        "task_id":           task.id,
                        "failed_step_index": index,
                        "error":             step_result.error,
                    },
                )
                logger.error(
                    f"Task {task.id[:8]} failed at step {index}: {step_result.error}"
                )
                return results

        if not task.is_terminal():
            task.mark_completed()
            self._publish("execution_completed", {"task_id": task.id, "results": len(results)})
            logger.info(f"Task {task.id[:8]} completed successfully in {len(results)} steps.")

        return results

    def request_stop(self) -> None:
        """
        Signal the manager to stop execution after the current step.

        Thread-safe flag set. The running `execute_plan` loop checks
        this before starting each new step.
        """
        logger.warning("Stop requested — execution will halt after the current step.")
        self._stop_requested = True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _execute_step(
        self,
        task: Task,
        index: int,
        step_text: str,
    ) -> StepResult:
        """
        Attempt to execute a single plan step, with retry logic.

        Args:
            task:      The parent Task (used for context logging).
            index:     Zero-based step index in the plan.
            step_text: The step description string.

        Returns:
            StepResult indicating success or failure and the attempt count.

        TODO:
            - Parse `step_text` to extract tool name, action, and parameters.
            - Dispatch to self.tool_manager.execute_tool(name, action, **params).
        """
        logger.info(f"[Step {index + 1}] Starting: {step_text!r}")
        self._publish("step_started", {"task_id": task.id, "step_index": index, "step_text": step_text})

        last_error: Optional[str] = None

        for attempt in range(1, self.max_retries + 2):  # +2 = 1 initial + max_retries
            try:
                # TODO: Replace stub with real tool dispatch.
                # Example future implementation:
                #   tool_name, action, params = self._parse_step(step_text)
                #   result = self.tool_manager.execute_tool(tool_name, action, **params)
                #   if not result.success:
                #       raise RuntimeError(result.error)
                #   output = result.output

                output = f"[STUB] Step '{step_text}' simulated successfully."
                logger.info(f"[Step {index + 1}] Attempt {attempt} succeeded.")
                self._publish(
                    "step_completed",
                    {"task_id": task.id, "step_index": index, "output": output},
                )
                return StepResult(
                    step_index=index,
                    step_text=step_text,
                    success=True,
                    output=output,
                    attempts=attempt,
                )

            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"[Step {index + 1}] Attempt {attempt} failed: {last_error}"
                )
                self._publish(
                    "step_failed",
                    {
                        "task_id":    task.id,
                        "step_index": index,
                        "error":      last_error,
                        "attempts":   attempt,
                    },
                )
                if attempt <= self.max_retries:
                    wait = attempt * 1.5  # Exponential-ish back-off
                    logger.info(f"[Step {index + 1}] Retrying in {wait}s...")
                    time.sleep(wait)

        return StepResult(
            step_index=index,
            step_text=step_text,
            success=False,
            error=last_error,
            attempts=self.max_retries + 1,
        )

    def _publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Safely publish an event to the EventBus, logging any publish errors."""
        try:
            self.event_bus.publish(event_type, data)
        except Exception as exc:
            logger.error(f"Failed to publish event '{event_type}': {exc}")
