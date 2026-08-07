"""
test_runner.py — Automated test framework detection and execution.

Detects testing frameworks and runs tests:
  - Python: pytest, unittest
  - Node.js: jest, mocha
  - Flutter: flutter test
  - Rust: cargo test
  - Java: mvn test, gradle test
"""

from __future__ import annotations

import subprocess
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.logger import setup_logger

from ai.verification.verification_task import VerificationTask, VerifierResult, VerifierStatus, VerifierType

logger = setup_logger(__name__)


@dataclass
class TestFramework:
    """Detected test framework information."""
    name:         str
    command:      str
    args:         List[str]
    config_file:  str


class TestRunner:
    """
    Runs automated tests for different frameworks.

    Features:
      - Automatic test framework detection
      - Test summary parsing (passed/failed/skipped)
      - Timeout handling
      - Test result reporting

    Usage:
        runner = TestRunner(project_root)
        result = runner.run(task, timeout=180)
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root)
        self._detected: Optional[TestFramework] = None
        logger.debug(f"TestRunner initialized (root='{self._root.name}').")

    # ── Public API ─────────────────────────────────────────────────────────

    def run(
        self,
        task: VerificationTask,
        timeout: int = 180,
    ) -> VerifierResult:
        """
        Run tests for the project.

        Args:
            task:    The verification task containing project info.
            timeout: Max execution time in seconds.

        Returns:
            VerifierResult with test outcome.
        """
        framework = self._detect_test_framework()
        if not framework:
            logger.info("TestRunner: no test framework detected, skipping tests")
            return VerifierResult(
                verifier_type=VerifierType.TEST,
                command="none",
                status=VerifierStatus.SKIPPED,
                stdout="No test framework detected",
                stderr="",
                exit_code=0,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )

        self._detected = framework
        logger.info(f"TestRunner: detected {framework.name} testing framework")

        start = datetime.now()
        command = [framework.command] + framework.args

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=timeout,
            )
            elapsed = (datetime.now() - start).total_seconds() * 1000

            # Parse test results
            test_stats = self._parse_test_output(result.stdout)

            # Classify result
            diagnostics = self._classify_diagnostics(
                result.stdout + result.stderr,
                test_stats
            )

            status = (
                VerifierStatus.PASSED
                if result.returncode == 0 and test_stats.get("failed", 0) == 0
                else VerifierStatus.FAILED
            )

            return VerifierResult(
                verifier_type=VerifierType.TEST,
                command=" ".join(command),
                status=status,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=round(elapsed, 1),
                diagnostics=diagnostics,
                files_changed=test_stats.get("test_count", 0),
            )

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            return VerifierResult(
                verifier_type=VerifierType.TEST,
                command=" ".join(command),
                status=VerifierStatus.TIMEOUT,
                stdout="",
                stderr=f"Tests timeout after {timeout}s",
                exit_code=124,
                duration_ms=round(elapsed, 1),
                diagnostics=[],
                files_changed=0,
            )
        except Exception as exc:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            return VerifierResult(
                verifier_type=VerifierType.TEST,
                command=" ".join(command),
                status=VerifierStatus.ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                duration_ms=round(elapsed, 1),
                diagnostics=[],
                files_changed=0,
            )

    # ── Test framework detection ────────────────────────────────────────────

    def _detect_test_framework(self) -> Optional[TestFramework]:
        """Detect the project's testing framework."""
        # Check each framework in priority order
        checks = [
            ("pytest", self._check_pytest),
            ("unittest", self._check_unittest),
            ("Jest", self._check_jest),
            ("Mocha", self._check_mocha),
            ("Flutter", self._check_flutter),
            ("Rust", self._check_rust),
            ("Maven", self._check_maven),
            ("Gradle", self._check_gradle),
        ]

        for name, check_func in checks:
            result = check_func()
            if result:
                logger.debug(f"TestRunner: detected {name}")
                return result

        return None

    def _check_pytest(self) -> Optional[TestFramework]:
        """Check for pytest framework."""
        # Check for pytest config or test files
        pytest_configs = ["pytest.ini", "pyproject.toml", "setup.cfg"]
        if any((self._root / cfg).exists() for cfg in pytest_configs):
            return TestFramework(
                name="pytest",
                command="pytest",
                args=["-v"],
                config_file="pytest.ini",
            )

        # Check for test directory
        test_dirs = ["tests", "test", "tests/unit", "tests/integration"]
        if any((self._root / d).is_dir() for d in test_dirs):
            return TestFramework(
                name="pytest",
                command="pytest",
                args=["-v"],
                config_file="tests/",
            )

        return None

    def _check_unittest(self) -> Optional[TestFramework]:
        """Check for Python unittest framework."""
        if any((self._root / f).exists() for f in ["test_*.py", "*_test.py"]):
            return TestFramework(
                name="unittest",
                command="python",
                args=["-m", "unittest", "discover"],
                config_file="test_*.py",
            )
        return None

    def _check_jest(self) -> Optional[TestFramework]:
        """Check for Jest framework."""
        package_json = self._root / "package.json"
        if package_json.exists():
            import json
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "jest" in deps:
                    return TestFramework(
                        name="Jest",
                        command="npx",
                        args=["jest"],
                        config_file="jest.config.js",
                    )
            except json.JSONDecodeError:
                pass
        return None

    def _check_mocha(self) -> Optional[TestFramework]:
        """Check for Mocha framework."""
        package_json = self._root / "package.json"
        if package_json.exists():
            import json
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "mocha" in deps:
                    return TestFramework(
                        name="Mocha",
                        command="npx",
                        args=["mocha"],
                        config_file="test/",
                    )
            except json.JSONDecodeError:
                pass
        return None

    def _check_flutter(self) -> Optional[TestFramework]:
        """Check for Flutter testing."""
        if (self._root / "pubspec.yaml").exists():
            return TestFramework(
                name="Flutter",
                command="flutter",
                args=["test"],
                config_file="pubspec.yaml",
            )
        return None

    def _check_rust(self) -> Optional[TestFramework]:
        """Check for Rust testing."""
        if (self._root / "Cargo.toml").exists():
            return TestFramework(
                name="Rust",
                command="cargo",
                args=["test"],
                config_file="Cargo.toml",
            )
        return None

    def _check_maven(self) -> Optional[TestFramework]:
        """Check for Maven testing."""
        if (self._root / "pom.xml").exists():
            return TestFramework(
                name="Maven",
                command="mvn",
                args=["test"],
                config_file="pom.xml",
            )
        return None

    def _check_gradle(self) -> Optional[TestFramework]:
        """Check for Gradle testing."""
        if (self._root / "build.gradle").exists() or (self._root / "build.gradle.kts").exists():
            return TestFramework(
                name="Gradle",
                command="gradle",
                args=["test"],
                config_file="build.gradle",
            )
        return None

    # ── Test output parsing ──────────────────────────────────────────────────

    def _parse_test_output(self, output: str) -> Dict[str, int]:
        """Parse test output for statistics."""
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "test_count": 0,
        }

        # Pytest pattern
        pytest_match = re.search(r"(\d+) passed(?:,)?\s*(\d+) failed(?:,)?\s*(\d+) skipped", output)
        if pytest_match:
            stats["passed"] = int(pytest_match.group(1))
            stats["failed"] = int(pytest_match.group(2))
            stats["skipped"] = int(pytest_match.group(3))
            stats["total"] = stats["passed"] + stats["failed"] + stats["skipped"]
            return stats

        # Jest pattern
        jest_match = re.search(r"Tests:\s+(\d+) passed", output)
        if jest_match:
            stats["passed"] = int(jest_match.group(1))
            stats["total"] = stats["passed"]
            return stats

        # Generic pattern for test count
        test_count = len(re.findall(r"(?i)(test\s+(?:\w+.*?pass|✓|✓))", output))
        stats["test_count"] = test_count
        stats["total"] = test_count

        return stats

    def _classify_diagnostics(self, output: str, stats: Dict[str, int]) -> List[Dict]:
        """Parse test output for diagnostics."""
        diagnostics = []

        # Look for failure messages
        failure_patterns = [
            (r"FAILED\s+(\S+)", "error"),
            (r"(?i)(test\s+failed)", "error"),
            (r"(?i)(AssertionError)", "error"),
            (r"(?i)(Error:)", "error"),
            (r"(?i)(Warning:)", "warning"),
        ]

        lines = output.splitlines()
        for i, line in enumerate(lines):
            for pattern, severity in failure_patterns:
                if re.search(pattern, line):
                    diagnostics.append({
                        "severity": severity,
                        "message": line.strip(),
                        "line": i + 1,
                        "source": "test",
                    })
                    break

        # Add summary diagnostics
        if stats["failed"] > 0:
            diagnostics.append({
                "severity": "error",
                "message": f"{stats['failed']} test(s) failed",
                "line": 0,
                "source": "test_summary",
            })

        if stats["skipped"] > 0:
            diagnostics.append({
                "severity": "warning",
                "message": f"{stats['skipped']} test(s) skipped",
                "line": 0,
                "source": "test_summary",
            })

        return diagnostics