"""
linter_runner.py — Linter execution (plugin-agnostic).

Supports multiple linters through a plugin architecture:
  - Ruff (Python)
  - flake8 (Python)
  - pylint (Python)
  - ESLint (JS/TS)
  - Dart analyze (Dart)
  - Clang-tidy (C/C++)
"""

from __future__ import annotations

import subprocess
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger

from ai.verification.verification_task import VerificationTask, VerifierResult, VerifierStatus, VerifierType

logger = setup_logger(__name__)


@dataclass
class LinterConfig:
    """Configuration for a linter."""
    name:        str
    command:     str
    extensions:  List[str]
    options:     List[str]
    output_format: str  # "line", "json", "auto"


class LinterRunner:
    """
    Runs linters on modified files.

    Features:
      - Plugin-agnostic design (configs are configurable)
      - Only lints modified files
      - Parses structured diagnostics
      - Non-blocking if linter not available

    Usage:
        runner = LinterRunner(project_root)
        result = runner.run(task, timeout=60)
    """

    def __init__(
        self,
        project_root: str,
        configs: Optional[List[LinterConfig]] = None,
    ) -> None:
        self._root = Path(project_root)
        self._configs = configs or self._default_configs()
        self._available_linters = self._find_available_linters()
        logger.debug(f"LinterRunner initialized ({len(self._available_linters)} available).")

    # ── Public API ─────────────────────────────────────────────────────────

    def run(
        self,
        task: VerificationTask,
        timeout: int = 60,
    ) -> VerifierResult:
        """
        Run linters on modified files.

        Args:
            task:    The verification task containing modified files.
            timeout: Max execution time per linter in seconds.

        Returns:
            VerifierResult with linting outcome.
        """
        if not task.files_modified:
            logger.info("LinterRunner: no files to lint")
            return self._skip_result("No files to lint")

        # Find relevant linters for the files
        relevant_linters = self._find_relevant_linters(task.files_modified)

        if not relevant_linters:
            logger.info("LinterRunner: no suitable linter found")
            return self._skip_result("No suitable linter found")

        start = datetime.now()
        diagnostics: List[Dict] = []
        stdout = ""
        stderr = ""

        for linter in relevant_linters:
            # Filter files matching this linter's extensions
            matching_files = [
                f for f in task.files_modified
                if Path(f).suffix in linter.extensions
            ]

            if not matching_files:
                continue

            result = self._lint_files(matching_files, linter, timeout)
            stdout += f"{linter.name} output:\n{result.stdout}\n"
            stderr += result.stderr + "\n"

            # Parse diagnostics based on output format
            if linter.output_format == "json":
                parsed = self._parse_json_diagnostics(result.stdout)
            else:
                parsed = self._parse_line_diagnostics(result.stdout, linter.name)

            diagnostics.extend(parsed)

        elapsed = (datetime.now() - start).total_seconds() * 1000

        # Classify result based on diagnostics
        error_count = sum(1 for d in diagnostics if d.get("severity") == "error")
        status = (
            VerifierStatus.PASSED
            if error_count == 0
            else VerifierStatus.FAILED
        )

        return VerifierResult(
            verifier_type=VerifierType.LINT,
            command=" | ".join(l.command for l in relevant_linters),
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=error_count,
            duration_ms=round(elapsed, 1),
            diagnostics=diagnostics,
            files_changed=0,
        )

    # ── Helper methods ──────────────────────────────────────────────────────

    def _lint_files(
        self,
        files: List[str],
        linter: LinterConfig,
        timeout: int,
    ) -> VerifierResult:
        """Lint a list of files."""
        command = [linter.command] + linter.options + files

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=timeout,
            )
            return VerifierResult(
                verifier_type=VerifierType.LINT,
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
                verifier_type=VerifierType.LINT,
                command=" ".join(command),
                status=VerifierStatus.TIMEOUT,
                stdout="",
                stderr=f"Linting timeout after {timeout}s",
                exit_code=124,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )
        except Exception as exc:
            return VerifierResult(
                verifier_type=VerifierType.LINT,
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
            verifier_type=VerifierType.LINT,
            command="none",
            status=VerifierStatus.SKIPPED,
            stdout=reason,
            stderr="",
            exit_code=0,
            duration_ms=0.0,
            diagnostics=[],
            files_changed=0,
        )

    # ── Linter detection ────────────────────────────────────────────────────

    def _default_configs(self) -> List[LinterConfig]:
        """Return default linter configurations."""
        return [
            LinterConfig(
                name="Ruff",
                command="ruff",
                extensions=[".py"],
                options=["check"],
                output_format="auto",
            ),
            LinterConfig(
                name="flake8",
                command="flake8",
                extensions=[".py"],
                options=["."],
                output_format="line",
            ),
            LinterConfig(
                name="pylint",
                command="pylint",
                extensions=[".py"],
                options=["--output-format=text"],
                output_format="line",
            ),
            LinterConfig(
                name="ESLint",
                command="eslint",
                extensions=[".js", ".ts", ".jsx", ".tsx"],
                options=["--format", "unix"],
                output_format="line",
            ),
            LinterConfig(
                name="Dart analyze",
                command="dart",
                extensions=[".dart"],
                options=["analyze"],
                output_format="auto",
            ),
            LinterConfig(
                name="Clang-tidy",
                command="clang-tidy",
                extensions=[".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".java"],
                options=["-p", "."],
                output_format="auto",
            ),
        ]

    def _find_available_linters(self) -> List[LinterConfig]:
        """Return list of linters that are installed and available."""
        import shutil
        available = []
        for config in self._configs:
            if shutil.which(config.command):
                available.append(config)
        return available

    def _find_relevant_linters(
        self,
        files: List[str],
    ) -> List[LinterConfig]:
        """Return linters relevant for the given files."""
        relevant = set()

        for file_path in files:
            ext = Path(file_path).suffix.lower()
            for linter in self._available_linters:
                if ext in linter.extensions:
                    relevant.add(linter)

        return list(relevant)

    # ── Diagnostic parsing ──────────────────────────────────────────────────

    def _parse_json_diagnostics(self, output: str) -> List[Dict]:
        """Parse JSON-format lint output."""
        diagnostics = []
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for item in data:
                    diagnostics.append({
                        "severity": item.get("severity", "warning"),
                        "message": item.get("message", ""),
                        "line": item.get("line", 0),
                        "column": item.get("column", 0),
                        "source": item.get("source", "lint"),
                    })
        except json.JSONDecodeError:
            pass
        return diagnostics

    def _parse_line_diagnostics(self, output: str, linter_name: str) -> List[Dict]:
        """Parse line-format lint output."""
        diagnostics = []
        lines = output.splitlines()

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Common patterns for lint diagnostics
            patterns = [
                # file:line:column: severity: message
                (r"([^:]+):(\d+):(\d+):(\w+):\s*(.+)", True),
                # file.py:line: message
                (r"([^:]+):(\d+):\s*(.+)", False),
                # ERROR: message (at file:line)
                (r"(ERROR|WARNING|FATAL):\s*(.+)", False),
            ]

            for pattern, has_column in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()

                    if has_column:
                        file_path, line_num, col, severity, message = groups
                    else:
                        file_path = ""
                        line_num = groups[1] if len(groups) > 1 else "0"
                        message = groups[-1]

                    diagnostics.append({
                        "severity": severity.lower() if severity.lower() in ("error", "warning") else "warning",
                        "message": message.strip(),
                        "line": int(line_num) if line_num.isdigit() else 0,
                        "column": int(groups[2]) if has_column and groups[2].isdigit() else 0,
                        "source": linter_name,
                    })
                    break

        return diagnostics

    def is_linter_available(self, name: str) -> bool:
        """Check if a specific linter is available."""
        return any(l.name == name for l in self._available_linters)

    def get_available_linters(self) -> List[LinterConfig]:
        """Return list of available linters."""
        return self._available_linters