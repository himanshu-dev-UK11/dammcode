"""
verification_report.py — Generate verification reports.

Generates comprehensive reports including:
  - Build status
  - Test results
  - Warnings
  - Errors
  - Execution time
  - Retries
  - Files changed
  - Risk level
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ai.verification.verification_task import VerificationTask, VerifierType, VerifierStatus


@dataclass
class ReportSection:
    """A section of the verification report."""
    title:    str
    content:  List[str]
    status:   str  # success, warning, error, info


class VerificationReportGenerator:
    """
    Generates human-readable verification reports.

    Usage:
        generator = VerificationReportGenerator()
        report = generator.generate(task, execution_time_ms)
    """

    def __init__(self) -> None:
        self._max_lines = 100  # Limit output lines

    # ── Public API ─────────────────────────────────────────────────────────

    def generate(
        self,
        task: VerificationTask,
        execution_time_ms: float,
    ) -> str:
        """
        Generate a verification report.

        Args:
            task:             The verification task.
            execution_time_ms: Total execution time in milliseconds.

        Returns:
            Human-readable report string.
        """
        sections = []

        # Header
        sections.append(self._generate_header(task, execution_time_ms))

        # Per-verifier results
        sections.append(self._generate_verifier_summary(task))

        # Verifier details
        for vtype, result in task.results.items():
            sections.append(self._generate_verifier_detail(vtype, result))

        # Summary
        sections.append(self._generate_summary(task, execution_time_ms))

        return "\n\n".join(sections)

    # ── Report sections ─────────────────────────────────────────────────────

    def _generate_header(
        self,
        task: VerificationTask,
        execution_time_ms: float,
    ) -> str:
        """Generate report header."""
        status_emoji = "✅" if task.get_overall_status() == "success" else "❌"
        status_text = "VERIFIED" if task.get_overall_status() == "success" else "FAILED"

        lines = [
            f"{status_emoji} {status_text} Verification Report",
            f"Task ID: {task.task_id}",
            f"Edit Request: {task.edit_request_id}",
            f"Prompt: {task.user_prompt[:80]}{'...' if len(task.user_prompt) > 80 else ''}",
            f"Files Modified: {len(task.files_modified)}",
            f"Executed In: {execution_time_ms:.0f}ms",
            f"Retry Count: {task.retry_count}/{task.max_retries}",
        ]

        return "\n".join(lines)

    def _generate_verifier_summary(self, task: VerificationTask) -> str:
        """Generate summary of all verifiers."""
        lines = [
            "## Verifier Summary",
            "",
        ]

        passed = []
        failed = []
        skipped = []
        errored = []

        for vtype in [VerifierType.FORMAT, VerifierType.LINT, VerifierType.BUILD, VerifierType.TEST]:
            result = task.results.get(vtype)
            if not result:
                skipped.append(vtype)
                continue

            if result.status == VerifierStatus.PASSED:
                passed.append(vtype)
            elif result.status == VerifierStatus.FAILED:
                failed.append(vtype)
            elif result.status == VerifierStatus.ERROR:
                errored.append(vtype)
            else:
                skipped.append(vtype)

        # Passed
        if passed:
            lines.append(f"✅ **Passed** ({len(passed)}): {', '.join(v.value for v in passed)}")
        else:
            lines.append("✅ **Passed**: None")

        # Failed
        if failed:
            lines.append(f"❌ **Failed** ({len(failed)}): {', '.join(v.value for v in failed)}")
        else:
            lines.append("❌ **Failed**: None")

        # Skipped
        if skipped:
            lines.append(f"⏭️ **Skipped** ({len(skipped)}): {', '.join(v.value for v in skipped)}")
        else:
            lines.append("⏭️ **Skipped**: None")

        # Errored
        if errored:
            lines.append(f"🔥 **Errored** ({len(errored)}): {', '.join(v.value for v in errored)}")
        else:
            lines.append("🔥 **Errored**: None")

        return "\n".join(lines)

    def _generate_verifier_detail(
        self,
        vtype: VerifierType,
        result,
    ) -> str:
        """Generate detailed output for a verifier."""
        if not result:
            return f"## {vtype.value.upper()}\nNot executed"

        status_emoji = {
            VerifierStatus.PASSED: "✅",
            VerifierStatus.FAILED: "❌",
            VerifierStatus.ERROR: "🔥",
            VerifierStatus.SKIPPED: "⏭️",
            VerifierStatus.TIMEOUT: "⏱️",
        }.get(result.status, "❓")

        lines = [
            f"## {status_emoji} {vtype.value.upper()}",
            "",
            f"Command: `{result.command}`",
            f"Duration: {result.duration_ms:.0f}ms",
            f"Exit Code: {result.exit_code}",
        ]

        # Output (truncated)
        if result.stdout:
            stdout_lines = result.stdout.splitlines()[:self._max_lines]
            lines.append("")
            lines.append("### Output:")
            lines.append("```")
            lines.extend(stdout_lines[:20])  # Limit stdout lines
            if len(stdout_lines) > 20:
                lines.append(f"... ({len(stdout_lines) - 20} more lines) ...")
            lines.append("```")

        if result.stderr:
            stderr_lines = result.stderr.splitlines()[:self._max_lines]
            lines.append("")
            lines.append("### Errors/Warnings:")
            lines.append("```")
            lines.extend(stderr_lines[:20])
            if len(stderr_lines) > 20:
                lines.append(f"... ({len(stderr_lines) - 20} more lines) ...")
            lines.append("```")

        return "\n".join(lines)

    def _generate_summary(
        self,
        task: VerificationTask,
        execution_time_ms: float,
    ) -> str:
        """Generate final summary."""
        status = task.get_overall_status()
        risk = self._determine_risk(task)

        lines = [
            "",
            "## Summary",
            "",
            f"Status: **{status.upper()}**",
            f"Risk Level: **{risk.upper()}**",
            f"Execution Time: {execution_time_ms:.0f}ms",
            f"Total Errors: {task.error_count}",
            f"Files Changed: {len(task.files_modified)}",
        ]

        if task.get_failed_verifiers():
            lines.append("")
            lines.append("⚠️  **Failed verifiers:**")
            for vtype in task.get_failed_verifiers():
                lines.append(f"   - {vtype.value}")

        if task.get_passed_verifiers():
            lines.append("")
            lines.append("✅ **Passed verifiers:**")
            for vtype in task.get_passed_verifiers():
                lines.append(f"   - {vtype.value}")

        return "\n".join(lines)

    def _determine_risk(self, task: VerificationTask) -> str:
        """Determine risk level based on verification results."""
        # Check for critical errors
        for result in task.results.values():
            if result.status == VerifierStatus.ERROR:
                return "high"

        failed_count = len(task.get_failed_verifiers())

        if failed_count == 0:
            return "low"
        elif failed_count == 1:
            return "medium"
        else:
            return "high"


# Convenience function

def generate_report(
    task: VerificationTask,
    execution_time_ms: float,
) -> str:
    """Convenience function to generate report."""
    generator = VerificationReportGenerator()
    return generator.generate(task, execution_time_ms)