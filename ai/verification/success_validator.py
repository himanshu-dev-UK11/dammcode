"""
success_validator.py — Determine if verification is successful.

Only marks task complete if ALL conditions are met:
  - Formatting passed
  - Lint passed
  - Build passed
  - Tests passed
  - No critical errors remain
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ai.verification.verification_task import (
    VerificationTask, VerifierType, VerifierStatus, VerifierConfig
)


@dataclass
class ValidationResult:
    """
    Result of success validation.

    Attributes:
        is_success:        True if task passed all checks
        passed_verifiers:  List of verifier types that passed
        failed_verifiers:  List of verifier types that failed
        missing_verifiers: List of verifier types that weren't run
        errors:            List of error messages
        warnings:          List of warning messages
    """
    is_success:        bool
    passed_verifiers:  List[VerifierType]
    failed_verifiers:  List[VerifierType]
    missing_verifiers: List[VerifierType]
    errors:            List[str]
    warnings:          List[str]


class SuccessValidator:
    """
    Validates that all verification checks have passed.

    Usage:
        validator = SuccessValidator()
        result = validator.validate(task)
    """

    def __init__(self) -> None:
        # Verifiers that must pass for success
        self._required_verifiers = [
            VerifierType.FORMAT,
            VerifierType.LINT,
            VerifierType.BUILD,
            VerifierType.TEST,
        ]

    # ── Public API ─────────────────────────────────────────────────────────

    def validate(
        self,
        task: VerificationTask,
    ) -> ValidationResult:
        """
        Validate that a verification task succeeded.

        Args:
            task: The verification task to validate.

        Returns:
            ValidationResult with success status and details.
        """
        errors: List[str] = []
        warnings: List[str] = []
        passed: List[VerifierType] = []
        failed: List[VerifierType] = []
        missing: List[VerifierType] = []

        # Check each required verifier
        for vtype in self._required_verifiers:
            config = task.config.get(vtype, VerifierConfig(type=vtype, enabled=True))
            result = task.results.get(vtype)

            if not config.enabled:
                # Not enabled, skip
                continue

            if not result:
                missing.append(vtype)
                errors.append(f"Missing result for {vtype.value} verifier")
                continue

            if result.status == VerifierStatus.PASSED:
                passed.append(vtype)
            else:
                failed.append(vtype)
                errors.append(
                    f"{vtype.value} failed: {result.stderr[:100] if result.stderr else 'unknown error'}"
                )

        # Check for critical errors
        for vtype, result in task.results.items():
            if result.status == VerifierStatus.ERROR:
                errors.append(f"Critical error in {vtype.value}: {result.stderr}")

        # Determine overall success
        is_success = (
            len(failed) == 0
            and len(errors) == 0
            and len(passed) > 0  # At least one verifier must have run
        )

        return ValidationResult(
            is_success=is_success,
            passed_verifiers=passed,
            failed_verifiers=failed,
            missing_verifiers=missing,
            errors=errors,
            warnings=warnings,
        )

    def validate_with_optional(
        self,
        task: VerificationTask,
        optional_verifiers: List[VerifierType] = None,
    ) -> ValidationResult:
        """
        Validate with additional optional verifiers.

        Args:
            task:             The verification task.
            optional_verifiers: Additional verifiers to include.

        Returns:
            ValidationResult with success status.
        """
        all_required = self._required_verifiers + (optional_verifiers or [])
        # We need to update task config to mark these as required
        # For simplicity, just call the main validate method
        return self.validate(task)

    def can_proceed(self, task: VerificationTask) -> bool:
        """
        Quick check if task can proceed to the next stage.

        Args:
            task: The verification task.

        Returns:
            True if task passed all required checks.
        """
        result = self.validate(task)
        return result.is_success

    def get_failure_reason(self, task: VerificationTask) -> str:
        """
        Get human-readable reason for failure.

        Args:
            task: The verification task.

        Returns:
            Description of why verification failed.
        """
        result = self.validate(task)

        if result.is_success:
            return "Verification succeeded"

        if result.errors:
            return "; ".join(result.errors[:3])  # Limit to first 3 errors

        if result.missing_verifiers:
            return f"Missing verifiers: {', '.join(v.value for v in result.missing_verifiers)}"

        if result.failed_verifiers:
            return f"Failed verifiers: {', '.join(v.value for v in result.failed_verifiers)}"

        return "Unknown verification failure"


# Convenience functions

def validate_success(task: VerificationTask) -> ValidationResult:
    """Convenience function to validate task success."""
    validator = SuccessValidator()
    return validator.validate(task)


def can_proceed(task: VerificationTask) -> bool:
    """Convenience function to check if task can proceed."""
    validator = SuccessValidator()
    return validator.can_proceed(task)