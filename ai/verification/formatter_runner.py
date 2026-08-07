"""
formatter_runner.py — Code formatter execution (plugin-agnostic).

Supports multiple formatters through a plugin architecture:
  - Black (Python)
  - isort (Python imports)
  - dart format (Dart)
  - prettier (JS/TS)
  - clang-format (C/C++/Java)
  - rustfmt (Rust)
"""

from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger

from ai.verification.verification_task import VerificationTask, VerifierResult, VerifierStatus, VerifierType

logger = setup_logger(__name__)


@dataclass
class FormatterConfig:
    """Configuration for a formatter."""
    name:        str
    command:     str
    extensions:  List[str]
    options:     List[str]


class FormatterRunner:
    """
    Runs code formatters on modified files.

    Features:
      - Plugin-agnostic design (configs are configurable)
      - Only formats modified files
      - Reports formatting changes
      - Non-blocking if formatter not available

    Usage:
        runner = FormatterRunner(project_root)
        result = runner.run(task, timeout=30)
    """

    def __init__(
        self,
        project_root: str,
        configs: Optional[List[FormatterConfig]] = None,
    ) -> None:
        self._root = Path(project_root)
        self._configs = configs or self._default_configs()
        self._available_formatters = self._find_available_formatters()
        logger.debug(f"FormatterRunner initialized ({len(self._available_formatters)} available).")

    # ── Public API ─────────────────────────────────────────────────────────

    def run(
        self,
        task: VerificationTask,
        timeout: int = 30,
    ) -> VerifierResult:
        """
        Run formatters on modified files.

        Args:
            task:    The verification task containing modified files.
            timeout: Max execution time per formatter in seconds.

        Returns:
            VerifierResult with formatting outcome.
        """
        if not task.files_modified:
            logger.info("FormatterRunner: no files to format")
            return self._skip_result("No files to format")

        # Find relevant formatters for the files
        relevant_formatters = self._find_relevant_formatters(task.files_modified)

        if not relevant_formatters:
            logger.info("FormatterRunner: no suitable formatter found")
            return self._skip_result("No suitable formatter found")

        start = datetime.now()
        files_formatted = 0
        stdout = ""
        stderr = ""

        for formatter in relevant_formatters:
            # Filter files matching this formatter's extensions
            matching_files = [
                f for f in task.files_modified
                if Path(f).suffix in formatter.extensions
            ]

            if not matching_files:
                continue

            # Run formatter on each file
            for file_path in matching_files:
                result = self._format_file(file_path, formatter, timeout)

                stdout += f"Formatted: {file_path}\n"
                stdout += result.stdout + "\n"
                stderr += result.stderr + "\n"

                if result.exit_code == 0:
                    files_formatted += 1

        elapsed = (datetime.now() - start).total_seconds() * 1000

        # If files were formatted, status is PASS; otherwise SKIP
        status = (
            VerifierStatus.PASSED
            if files_formatted > 0
            else VerifierStatus.SKIPPED
        )

        return VerifierResult(
            verifier_type=VerifierType.FORMAT,
            command=" | ".join(f.command for f in relevant_formatters),
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=0 if files_formatted > 0 else 1,
            duration_ms=round(elapsed, 1),
            diagnostics=[],
            files_changed=files_formatted,
        )

    # ── Helper methods ──────────────────────────────────────────────────────

    def _format_file(
        self,
        file_path: str,
        formatter: FormatterConfig,
        timeout: int,
    ) -> VerifierResult:
        """Format a single file."""
        command = [formatter.command] + formatter.options + [file_path]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=timeout,
            )
            return VerifierResult(
                verifier_type=VerifierType.FORMAT,
                command=" ".join(command),
                status=(
                    VerifierStatus.PASSED
                    if result.returncode == 0
                    else VerifierStatus.FAILED
                ),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )
        except subprocess.TimeoutExpired:
            return VerifierResult(
                verifier_type=VerifierType.FORMAT,
                command=" ".join(command),
                status=VerifierStatus.TIMEOUT,
                stdout="",
                stderr=f"Formatting timeout after {timeout}s",
                exit_code=124,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )
        except Exception as exc:
            return VerifierResult(
                verifier_type=VerifierType.FORMAT,
                command=" ".join(command),
                status=VerifierStatus.ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )

    def _skip_result(self, reason: str) -> VerifierResult:
        """Return a skip result with the given reason."""
        return VerifierResult(
            verifier_type=VerifierType.FORMAT,
            command="none",
            status=VerifierStatus.SKIPPED,
            stdout=reason,
            stderr="",
            exit_code=0,
            duration_ms=0.0,
            diagnostics=[],
            files_changed=0,
        )

    # ── Formatter detection ──────────────────────────────────────────────────

    def _default_configs(self) -> List[FormatterConfig]:
        """Return default formatter configurations."""
        return [
            FormatterConfig(
                name="Black",
                command="black",
                extensions=[".py"],
                options=["--quiet"],
            ),
            FormatterConfig(
                name="isort",
                command="isort",
                extensions=[".py"],
                options=["--profile", "black"],
            ),
            FormatterConfig(
                name="dart format",
                command="dart",
                extensions=[".dart"],
                options=["format"],
            ),
            FormatterConfig(
                name="prettier",
                command="prettier",
                extensions=[".js", ".ts", ".jsx", ".tsx", ".json", ".md"],
                options=["--write"],
            ),
            FormatterConfig(
                name="clang-format",
                command="clang-format",
                extensions=[".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".java"],
                options=["-i"],
            ),
            FormatterConfig(
                name="rustfmt",
                command="rustfmt",
                extensions=[".rs"],
                options=["--emit", "stdout"],
            ),
        ]

    def _find_available_formatters(self) -> List[FormatterConfig]:
        """Return list of formatters that are installed and available."""
        available = []
        for config in self._configs:
            if shutil.which(config.command):
                available.append(config)
        return available

    def _find_relevant_formatters(
        self,
        files: List[str],
    ) -> List[FormatterConfig]:
        """Return formatters relevant for the given files."""
        relevant = set()

        for file_path in files:
            ext = Path(file_path).suffix.lower()
            for formatter in self._available_formatters:
                if ext in formatter.extensions:
                    relevant.add(formatter)

        return list(relevant)

    def is_formatter_available(self, name: str) -> bool:
        """Check if a specific formatter is available."""
        return any(f.name == name for f in self._available_formatters)

    def get_available_formatters(self) -> List[FormatterConfig]:
        """Return list of available formatters."""
        return self._available_formatters