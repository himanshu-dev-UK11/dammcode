"""
retry_manager.py — Retry logic for failed verifications.

Handles retry behavior:
  - Generate retry tasks with exponential backoff
  - Limit maximum retry attempts
  - Escalate when maximum attempts reached
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from core.logger import setup_logger

from ai.verification.verification_task import VerificationTask, VerifierType, VerifierStatus

logger = setup_logger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries:      int = 3
    base_delay_ms:    int = 1000    # 1 second
    backoff_multiplier: float = 2.0  # Exponential backoff
    max_delay_ms:     int = 30000   # 30 seconds
    retry_on:         List[VerifierStatus] = None

    def __post_init__(self):
        if self.retry_on is None:
            self.retry_on = [VerifierStatus.FAILED, VerifierStatus.ERROR, VerifierStatus.TIMEOUT]


class RetryManager:
    """
    Manages retry logic for verification tasks.

    Features:
      - Exponential backoff between retries
      - Configurable retry limits
      - Retry history tracking
      - Escalation on failure

    Usage:
        manager = RetryManager(max_retries=3)
        should_retry, delay = manager.should_retry(task)
    """

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        self._config = config or RetryConfig()
        self._lock = threading.Lock()
        self._retry_history: Dict[str, List[datetime]] = {}
        logger.debug(f"RetryManager initialized (max_retries={self._config.max_retries}).")

    # ── Public API ─────────────────────────────────────────────────────────

    def should_retry(self, task: VerificationTask) -> tuple[bool, float]:
        """
        Determine if a task should be retried.

        Args:
            task: The verification task to check.

        Returns:
            Tuple of (should_retry, delay_ms).
        """
        with self._lock:
            # Check retry count
            if task.retry_count >= self._config.max_retries:
                logger.info(
                    f"RetryManager: max retries reached for task {task.task_id[:8]}"
                )
                return False, 0.0

            # Check if any verifiers failed
            failed_verifiers = task.get_failed_verifiers()
            if not failed_verifiers:
                return False, 0.0

            # Check if failure type should be retried
            should = False
            for vtype in failed_verifiers:
                result = task.results.get(vtype)
                if result and result.status in self._config.retry_on:
                    should = True
                    break

            if not should:
                return False, 0.0

            # Calculate delay with exponential backoff
            delay_ms = self._calculate_delay(task.retry_count)

            logger.info(
                f"RetryManager: task {task.task_id[:8]} should retry "
                f"in {delay_ms:.0f}ms (attempt {task.retry_count + 1}/{self._config.max_retries})"
            )
            return True, delay_ms

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt.

        Args:
            attempt: The retry attempt number (0-indexed).

        Returns:
            Delay in milliseconds.
        """
        delay = self._config.base_delay_ms * (
            self._config.backoff_multiplier ** attempt
        )
        return min(delay, self._config.max_delay_ms)

    def record_retry(self, task_id: str) -> None:
        """Record a retry attempt for tracking."""
        with self._lock:
            if task_id not in self._retry_history:
                self._retry_history[task_id] = []
            self._retry_history[task_id].append(datetime.now())

    def get_retry_history(self, task_id: str) -> List[datetime]:
        """Get retry history for a task."""
        return self._retry_history.get(task_id, [])

    def reset_history(self, task_id: Optional[str] = None) -> None:
        """Reset retry history."""
        with self._lock:
            if task_id:
                self._retry_history.pop(task_id, None)
            else:
                self._retry_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Return retry manager statistics."""
        with self._lock:
            total_retries = sum(len(history) for history in self._retry_history.values())
            return {
                "max_retries": self._config.max_retries,
                "base_delay_ms": self._config.base_delay_ms,
                "backoff_multiplier": self._config.backoff_multiplier,
                "max_delay_ms": self._config.max_delay_ms,
                "retry_on": [s.value for s in self._config.retry_on],
                "total_retries": total_retries,
                "tracked_tasks": len(self._retry_history),
            }

    # ── Retry task generation ───────────────────────────────────────────────

    def create_retry_task(
        self,
        original: VerificationTask,
        new_task_id: Optional[str] = None,
    ) -> VerificationTask:
        """
        Create a new task for retry.

        Args:
            original:    The original verification task.
            new_task_id: Optional new task ID (auto-generated if not provided).

        Returns:
            New VerificationTask for retry.
        """
        retry_id = new_task_id or f"ver_{original.task_id[:8]}_retry{original.retry_count + 1}"

        # Create new task with same parameters
        new_task = VerificationTask.create(
            edit_request_id=original.edit_request_id,
            user_prompt=original.user_prompt,
            files_modified=original.files_modified,
            config=original.config,
            max_retries=self._config.max_retries,
        )
        new_task.task_id = retry_id
        new_task.retry_count = original.retry_count + 1

        logger.info(
            f"RetryManager: created retry task {retry_id[:8]} "
            f"for original {original.task_id[:8]}"
        )
        return new_task

    # ── Escalation handling ─────────────────────────────────────────────────

    def should_escalate(self, task: VerificationTask) -> bool:
        """
        Check if a failed task should be escalated (e.g., to human review).

        Args:
            task: The verification task to check.

        Returns:
            True if escalation is recommended.
        """
        # Escalate if max retries reached
        if task.retry_count >= self._config.max_retries:
            return True

        # Escalate if critical errors persist
        for result in task.results.values():
            if result.status == VerifierStatus.ERROR:
                return True

        return False

    def get_escalation_message(self, task: VerificationTask) -> str:
        """Generate escalation message for a task."""
        messages = []

        if task.retry_count >= self._config.max_retries:
            messages.append(f"Max retries ({task.retry_count}) reached")

        failed_verifiers = task.get_failed_verifiers()
        if failed_verifiers:
            messages.append(f"Failed verifiers: {', '.join(v.value for v in failed_verifiers)}")

        return "; ".join(messages) if messages else "Unknown failure"


# Convenience function

def should_retry_task(
    task: VerificationTask,
    max_retries: int = 3,
) -> tuple[bool, float]:
    """Convenience function to check if task should be retried."""
    manager = RetryManager(RetryConfig(max_retries=max_retries))
    return manager.should_retry(task)