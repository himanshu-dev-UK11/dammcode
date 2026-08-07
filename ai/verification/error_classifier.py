"""
error_classifier.py — Categorize and classify verification errors.

Categorizes errors into types:
  - Syntax Error
  - Import Error
  - Build Failure
  - Test Failure
  - Dependency Failure
  - Formatting Error
  - Runtime Error
  - Unknown

Assigns severity levels:
  - critical: blocks progress
  - high: must fix before merge
  - medium: should fix soon
  - low: nice to fix
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ErrorType(Enum):
    """Types of verification errors."""
    SYNTAX = "syntax"
    IMPORT = "import"
    BUILD = "build"
    TEST = "test"
    DEPENDENCY = "dependency"
    FORMATTING = "formatting"
    LINT = "lint"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ErrorClassification:
    """
    Classification of a single error.

    Attributes:
        error_type:  Categorized error type
        severity:    Impact level
        message:     Original error message
        file:        File path where error occurred (if applicable)
        line:        Line number where error occurred (if applicable)
        suggestion:  Suggested fix (if known)
    """
    error_type:  ErrorType
    severity:    Severity
    message:     str
    file:        Optional[str] = None
    line:        Optional[int] = None
    suggestion:  Optional[str] = None


class ErrorClassifier:
    """
    Classifies errors from verification runs.

    Usage:
        classifier = ErrorClassifier()
        classification = classifier.classify(error_message, file_path)
    """

    def __init__(self) -> None:
        self._patterns = self._build_patterns()
        self._suggestions = self._build_suggestions()

    # ── Public API ─────────────────────────────────────────────────────────

    def classify(
        self,
        error_message: str,
        file_path: Optional[str] = None,
    ) -> ErrorClassification:
        """
        Classify an error message.

        Args:
            error_message: The error message to classify.
            file_path:     Optional file path where error occurred.

        Returns:
            ErrorClassification with type, severity, and suggestion.
        """
        error_lower = error_message.lower()

        # Check each pattern
        for error_type, (pattern, severity, suggestion_key) in self._patterns.items():
            if re.search(pattern, error_lower):
                return ErrorClassification(
                    error_type=error_type,
                    severity=severity,
                    message=error_message,
                    file=file_path,
                    line=self._extract_line_number(error_message),
                    suggestion=self._suggestions.get(suggestion_key, None),
                )

        # Default to unknown
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            severity=Severity.MEDIUM,
            message=error_message,
            file=file_path,
            line=self._extract_line_number(error_message),
            suggestion="Review the error message and check documentation.",
        )

    def classify_batch(
        self,
        output: str,
        file_path: Optional[str] = None,
    ) -> List[ErrorClassification]:
        """
        Classify all errors in a multi-line output.

        Args:
            output:      Multi-line output containing errors.
            file_path:   Optional file path where errors occurred.

        Returns:
            List of classifications for each error found.
        """
        classifications = []
        lines = output.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            classification = self.classify(line, file_path)
            classifications.append(classification)

        return classifications

    # ── Pattern building ────────────────────────────────────────────────────

    def _build_patterns(self) -> Dict[ErrorType, tuple]:
        """Build regex patterns for error classification."""
        return {
            ErrorType.SYNTAX: (
                r"(\bsyntax\s+error|unexpected\s+\w+|invalid\s+syntax)",
                Severity.HIGH,
                "syntax_error",
            ),
            ErrorType.IMPORT: (
                r"(\bimport\s+error|module\s+not\s+found|cannot\s+import)",
                Severity.HIGH,
                "import_error",
            ),
            ErrorType.BUILD: (
                r"(\bbuild\s+failed|compile\s+error|link\s+error)",
                Severity.CRITICAL,
                "build_error",
            ),
            ErrorType.TEST: (
                r"(\btest\s+failed|assertion\s+error|test\s+error)",
                Severity.MEDIUM,
                "test_error",
            ),
            ErrorType.DEPENDENCY: (
                r"(\bdependency\s+error|package\s+not\s+found|pip\s+install)",
                Severity.HIGH,
                "dependency_error",
            ),
            ErrorType.FORMATTING: (
                r"(\bformat\s+error|black|prettier|clang-format)",
                Severity.LOW,
                "format_error",
            ),
            ErrorType.LINT: (
                r"(\blint\s+error|flake8|ruff|pylint|eslint)",
                Severity.MEDIUM,
                "lint_error",
            ),
            ErrorType.RUNTIME: (
                r"(\bruntime\s+error|exception|traceback|crash)",
                Severity.CRITICAL,
                "runtime_error",
            ),
        }

    def _build_suggestions(self) -> Dict[str, Optional[str]]:
        """Build error-specific suggestions."""
        return {
            "syntax_error": "Check for missing colons, parentheses, or quotes.",
            "import_error": "Ensure the module is installed and in the Python path.",
            "build_error": "Check build configuration files and dependencies.",
            "test_error": "Review test expectations and implementation.",
            "dependency_error": "Update requirements.txt or package.json.",
            "format_error": "Run the formatter (black, prettier, etc.).",
            "lint_error": "Fix linting issues or update lint config.",
            "runtime_error": "Check input data and exception handling.",
        }

    def _extract_line_number(self, message: str) -> Optional[int]:
        """Extract line number from error message if present."""
        patterns = [
            r":(\d+):",        # :123: format
            r"line\s+(\d+)",   # line 123 format
            r"at\s+(\d+)",     # at 123 format
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def get_severity_color(self, severity: Severity) -> str:
        """Get color code for severity level."""
        return {
            Severity.CRITICAL: "#EF4444",  # Red
            Severity.HIGH: "#F97316",      # Orange
            Severity.MEDIUM: "#F59E0B",    # Amber
            Severity.LOW: "#10B981",       # Green
        }.get(severity, "#52525C")


# Convenience functions

def classify_error(
    error_message: str,
    file_path: Optional[str] = None,
) -> ErrorClassification:
    """Convenience function to classify an error."""
    classifier = ErrorClassifier()
    return classifier.classify(error_message, file_path)


def classify_batch(output: str, file_path: Optional[str] = None) -> List[ErrorClassification]:
    """Convenience function to classify multiple errors."""
    classifier = ErrorClassifier()
    return classifier.classify_batch(output, file_path)