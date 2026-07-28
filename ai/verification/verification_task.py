"""
verification_task.py — Task dataclass for verification operations.

Represents a single verification run with all its components:
- Edit results to verify
- Verifier configurations
- Execution status and results
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional


class VerifierType(Enum):
    """Types of verifiers that can be run."""
    BUILD = "build"
    TEST = "test"
    FORMAT = "format"
    LINT = "lint"
    ANALYSIS = "analysis"


class VerifierStatus(Enum):
    """Status of a verifier execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class VerifierConfig:
    """
    Configuration for a single verifier.

    Attributes:
        type:         Verifier type (build, test, format, lint, analysis)
        enabled:      Whether this verifier is active
        command:      Command to execute (can be None if auto-detected)
        options:      Additional command-line options
        timeout:      Max execution time in seconds
        retry_count:  Number of retries on failure
    """
    type:         VerifierType
    enabled:      bool = True
    command:      Optional[str] = None
    options:      List[str] = field(default_factory=list)
    timeout:      int = 60
    retry_count:  int = 0


@dataclass
class VerifierResult:
    """
    Result of a single verifier execution.

    Attributes:
        verifier_type:   Type of verifier that ran
        command:         Command that was executed
        status:          Success/failure status
        stdout:          Standard output from execution
        stderr:          Standard error from execution
        exit_code:       Process exit code
        duration_ms:     Execution time in milliseconds
        diagnostics:     List of structured diagnostics (warnings/errors)
        files_changed:   Number of files modified by this verifier
    """
    verifier_type:   VerifierType
    command:         str
    status:          VerifierStatus
    stdout:          str
    stderr:          str
    exit_code:       int
    duration_ms:     float
    diagnostics:     List[Dict[str, Any]] = field(default_factory=list)
    files_changed:   int = 0


@dataclass
class VerificationTask:
    """
    A complete verification task.

    Attributes:
        task_id:         Unique identifier for this task
        edit_request_id: ID of the edit being verified
        user_prompt:     Original user request
        files_modified:  List of modified file paths
        timestamp:       When the task was created
        status:          Overall task status
        config:          Verifier configurations
        results:         Results from each verifier
        retry_count:     Number of retry attempts
        max_retries:     Maximum allowed retries
        error_count:     Total number of errors across all verifiers
        risk_level:      Estimated risk of the changes (low/medium/high)
    """
    task_id:          str
    edit_request_id:  str
    user_prompt:      str
    files_modified:   List[str]
    timestamp:        datetime
    status:           str  # pending, running, completed, failed
    config:           Dict[VerifierType, VerifierConfig]
    results:          Dict[VerifierType, VerifierResult] = field(default_factory=dict)
    retry_count:      int = 0
    max_retries:      int = 3
    error_count:      int = 0
    risk_level:       str = "low"

    @classmethod
    def create(
        cls,
        edit_request_id: str,
        user_prompt: str,
        files_modified: List[str],
        config: Optional[Dict[VerifierType, VerifierConfig]] = None,
        max_retries: int = 3,
    ) -> VerificationTask:
        """Create a new verification task."""
        return cls(
            task_id=f"ver_{uuid.uuid4().hex[:12]}",
            edit_request_id=edit_request_id,
            user_prompt=user_prompt,
            files_modified=files_modified,
            timestamp=datetime.now(),
            status="pending",
            config=config or {},
            results={},
            retry_count=0,
            max_retries=max_retries,
            error_count=0,
            risk_level="low",
        )

    def add_result(self, result: VerifierResult) -> None:
        """Add a verifier result to this task."""
        self.results[result.verifier_type] = result
        if result.status == VerifierStatus.FAILED:
            self.error_count += 1

    def is_complete(self) -> bool:
        """Check if all enabled verifiers have completed."""
        for vtype, result in self.results.items():
            if self.config.get(vtype, VerifierConfig(type=vtype)).enabled:
                if result.status not in (VerifierStatus.PASSED, VerifierStatus.FAILED):
                    return False
        return True

    def get_overall_status(self) -> str:
        """Determine overall verification status."""
        if not self.results:
            return "pending"

        all_passed = all(
            r.status == VerifierStatus.PASSED
            for r in self.results.values()
            if self.config.get(r.verifier_type, VerifierConfig(type=r.verifier_type)).enabled
        )
        return "success" if all_passed else "failed"

    def get_failed_verifiers(self) -> List[VerifierType]:
        """Return list of verifier types that failed."""
        return [
            vtype for vtype, result in self.results.items()
            if self.config.get(vtype, VerifierConfig(type=vtype)).enabled
            and result.status == VerifierStatus.FAILED
        ]

    def get_passed_verifiers(self) -> List[VerifierType]:
        """Return list of verifier types that passed."""
        return [
            vtype for vtype, result in self.results.items()
            if self.config.get(vtype, VerifierConfig(type=vtype)).enabled
            and result.status == VerifierStatus.PASSED
        ]

    def needs_retry(self) -> bool:
        """Check if this task should be retried."""
        return (
            self.retry_count < self.max_retries
            and self.get_overall_status() == "failed"
        )


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