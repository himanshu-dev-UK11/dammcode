"""
verification_engine.py — Main coordinator for verification operations.

Orchestrates the entire verification pipeline:
  1. Execute all configured verifiers
  2. Collect and aggregate results
  3. Determine success/failure
  4. Handle retries
  5. Generate verification reports
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.logger import setup_logger
from core.event_bus import EventBus

from ai.editing.change_request import ChangeRequest, ChangeStatus
from ai.editing.rollback_manager import RollbackManager
from ai.verification.verification_task import (
    VerificationTask, VerifierType, VerifierResult, VerifierStatus, VerifierConfig
)
from ai.verification.build_runner import BuildRunner
from ai.verification.test_runner import TestRunner
from ai.verification.formatter_runner import FormatterRunner
from ai.verification.linter_runner import LinterRunner
from ai.verification.error_classifier import ErrorClassifier
from ai.verification.retry_manager import RetryManager
from ai.verification.success_validator import SuccessValidator
from ai.verification.verification_report import VerificationReportGenerator

logger = setup_logger(__name__)


@dataclass
class VerificationResult:
    """
    Final result of the verification engine.

    Attributes:
        task_id:           ID of the verification task
        success:           True if all verifiers passed
        total_verifiers:   Number of verifiers executed
        passed_verifiers:  Number that passed
        failed_verifiers:  Number that failed
        total_errors:      Total error count
        total_warnings:    Total warning count
        execution_time_ms: Total execution time
        report:            Generated verification report
    """
    task_id:           str
    success:           bool
    total_verifiers:   int
    passed_verifiers:  int
    failed_verifiers:  int
    total_errors:      int
    total_warnings:    int
    execution_time_ms: float
    report:            str


class VerificationEngine:
    """
    Main coordinator for AI code verification.

    Manages a pool of verifiers that run in sequence or parallel
    depending on configuration.

    Usage:
        engine = VerificationEngine(event_bus, project_root)
        result = engine.verify(task)
    """

    def __init__(
        self,
        event_bus: EventBus,
        project_root: str,
        config: Optional[Dict[VerifierType, VerifierConfig]] = None,
    ) -> None:
        self.event_bus = event_bus
        self._root = Path(project_root)
        self._config = config or create_default_config()

        # Initialize runner instances
        self._build_runner = BuildRunner(project_root)
        self._test_runner = TestRunner(project_root)
        self._formatter_runner = FormatterRunner(project_root)
        self._linter_runner = LinterRunner(project_root)
        self._error_classifier = ErrorClassifier()
        self._retry_manager = RetryManager()
        self._success_validator = SuccessValidator()
        self._report_generator = VerificationReportGenerator()

        # State management
        self._lock = threading.Lock()
        self._current_task: Optional[VerificationTask] = None

        logger.info(
            f"VerificationEngine initialized (root='{self._root.name}', "
            f"config={len(self._config)} verifiers)"
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def verify(
        self,
        task: VerificationTask,
    ) -> VerificationResult:
        """
        Execute the verification pipeline for a task.

        Args:
            task: The VerificationTask to run.

        Returns:
            VerificationResult with overall success/failure.
        """
        with self._lock:
            self._current_task = task

        logger.info(
            f"VerificationEngine.verify(): task={task.task_id[:8]}, "
            f"files={len(task.files_modified)}, prompt='{task.user_prompt[:40]}...'"
        )
        self._publish("verification_started", {"task_id": task.task_id})

        start_time = time.perf_counter()

        try:
            # Execute each enabled verifier
            for vtype, verifer_config in self._config.items():
                if not verifer_config.enabled:
                    logger.debug(f"Verification: skipping {vtype.value} (disabled)")
                    continue

                result = self._run_verifier(task, vtype)
                task.add_result(result)

                # Publish progress
                self._publish("verification_progress", {
                    "task_id": task.task_id,
                    "verifier": vtype.value,
                    "status": result.status.value,
                    "duration_ms": result.duration_ms,
                })

                # Check if we should stop on critical failure
                if result.status == VerifierStatus.ERROR:
                    logger.warning(f"Verification: critical error in {vtype.value}")
                    break

            # Determine overall status
            task.status = task.get_overall_status()
            task.error_count = len(task.get_failed_verifiers())

            # Calculate execution time
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Generate report
            report = self._report_generator.generate(task, execution_time_ms)

            # Publish completion
            self._publish("verification_complete", {
                "task_id": task.task_id,
                "success": task.get_overall_status() == "success",
                "report": report,
            })

            return VerificationResult(
                task_id=task.task_id,
                success=task.get_overall_status() == "success",
                total_verifiers=len(task.results),
                passed_verifiers=len(task.get_passed_verifiers()),
                failed_verifiers=len(task.get_failed_verifiers()),
                total_errors=task.error_count,
                total_warnings=sum(
                    len(r.diagnostics) for r in task.results.values()
                    if r.status == VerifierStatus.FAILED
                ),
                execution_time_ms=execution_time_ms,
                report=report,
            )

        except Exception as exc:
            logger.error(f"VerificationEngine: unexpected error: {exc}")
            self._publish("verification_error", {
                "task_id": task.task_id,
                "error": str(exc),
            })
            raise

    def verify_edit(
        self,
        edit_request: ChangeRequest,
        files_modified: List[str],
    ) -> VerificationResult:
        """
        Convenience method: Create and run verification for an edit request.

        Args:
            edit_request: The ChangeRequest to verify.
            files_modified: List of files that were modified.

        Returns:
            VerificationResult with success/failure.
        """
        task = VerificationTask.create(
            edit_request_id=edit_request.request_id,
            user_prompt=edit_request.user_prompt,
            files_modified=files_modified,
            config=self._config,
            max_retries=self._retry_manager.max_retries,
        )
        return self.verify(task)

    def retry_failed(self, task: VerificationTask) -> Optional[VerificationTask]:
        """
        Create a retry task if verification failed and retries remain.

        Args:
            task: The failed VerificationTask.

        Returns:
            New VerificationTask for retry, or None if no retries remain.
        """
        if not task.needs_retry():
            return None

        task.retry_count += 1
        logger.info(
            f"VerificationEngine: retry #{task.retry_count}/{task.max_retries} "
            f"for task {task.task_id[:8]}"
        )

        # Create new task with same parameters
        new_task = VerificationTask.create(
            edit_request_id=task.edit_request_id,
            user_prompt=task.user_prompt,
            files_modified=task.files_modified,
            config=task.config,
            max_retries=task.max_retries,
        )
        new_task.retry_count = task.retry_count

        return new_task

    def get_status(self) -> Dict[str, Any]:
        """Return engine status for UI display."""
        return {
            "running": self._current_task is not None,
            "current_task": self._current_task.task_id if self._current_task else None,
            "config": {
                vtype.value: {
                    "enabled": config.enabled,
                    "timeout": config.timeout,
                    "retry_count": config.retry_count,
                }
                for vtype, config in self._config.items()
            },
        }

    # ── Verifier execution ──────────────────────────────────────────────────

    def _run_verifier(
        self,
        task: VerificationTask,
        vtype: VerifierType,
    ) -> VerifierResult:
        """Run a single verifier and return result."""
        command = self._config[vtype].command
        timeout = self._config[vtype].timeout
        options = self._config[vtype].options

        logger.info(f"VerificationEngine: running {vtype.value} verifier")

        try:
            if vtype == VerifierType.BUILD:
                return self._build_runner.run(task, timeout)
            elif vtype == VerifierType.TEST:
                return self._test_runner.run(task, timeout)
            elif vtype == VerifierType.FORMAT:
                return self._formatter_runner.run(task, timeout)
            elif vtype == VerifierType.LINT:
                return self._linter_runner.run(task, timeout)
            elif vtype == VerifierType.ANALYSIS:
                # Analysis not yet implemented
                return VerifierResult(
                    verifier_type=vtype,
                    command="analysis (not implemented)",
                    status=VerifierStatus.SKIPPED,
                    stdout="Analysis not yet implemented",
                    stderr="",
                    exit_code=0,
                    duration_ms=0.0,
                    diagnostics=[],
                    files_changed=0,
                )
            else:
                return VerifierResult(
                    verifier_type=vtype,
                    command="unknown",
                    status=VerifierStatus.ERROR,
                    stdout="",
                    stderr=f"Unknown verifier type: {vtype}",
                    exit_code=1,
                    duration_ms=0.0,
                    diagnostics=[],
                    files_changed=0,
                )

        except Exception as exc:
            logger.error(f"VerificationEngine: {vtype.value} error: {exc}")
            return VerifierResult(
                verifier_type=vtype,
                command=str(command or "unknown"),
                status=VerifierStatus.ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )

    # ── EventBus publishing ────────────────────────────────────────────────

    def _publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to the EventBus."""
        try:
            self.event_bus.publish(event_type, data)
        except Exception as exc:
            logger.debug(f"VerificationEngine: publish failed ({event_type}): {exc}")


def create_default_config() -> Dict[VerifierType, VerifierConfig]:
    """Create default verifier configurations."""
    return {
        VerifierType.FORMAT: VerifierConfig(
            type=VerifierType.FORMAT,
            enabled=True,
            timeout=30,
            retry_count=0,
        ),
        VerifierType.LINT: VerifierConfig(
            type=VerifierType.LINT,
            enabled=True,
            timeout=60,
            retry_count=0,
        ),
        VerifierType.BUILD: VerifierConfig(
            type=VerifierType.BUILD,
            enabled=True,
            timeout=120,
            retry_count=1,
        ),
        VerifierType.TEST: VerifierConfig(
            type=VerifierType.TEST,
            enabled=True,
            timeout=180,
            retry_count=0,
        ),
        VerifierType.ANALYSIS: VerifierConfig(
            type=VerifierType.ANALYSIS,
            enabled=False,
            timeout=60,
            retry_count=0,
        ),
    }