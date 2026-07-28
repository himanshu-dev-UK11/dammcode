"""
build_runner.py — Automated build system detection and execution.

Detects the project's build system and executes it safely:
  - Python: pip install -e ., python setup.py build
  - Node.js: npm install, npm run build
  - Flutter: flutter pub get, flutter build
  - Rust: cargo build
  - Go: go build ./...
  - Java/CMake: cmake, make
"""

from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.logger import setup_logger

from ai.verification.verification_task import VerificationTask, VerifierResult, VerifierStatus, VerifierType

logger = setup_logger(__name__)


@dataclass
class BuildSystem:
    """Detected build system information."""
    name:       str
    command:    str
    args:       List[str]
    lock_file:  str
    output_dir: str


class BuildRunner:
    """
    Runs automated builds for different project types.

    Features:
      - Automatic build system detection
      - Safe subprocess execution with timeout
      - stdout/stderr capture
      - Build status reporting

    Usage:
        runner = BuildRunner(project_root)
        result = runner.run(task, timeout=120)
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root)
        self._detected: Optional[BuildSystem] = None
        logger.debug(f"BuildRunner initialized (root='{self._root.name}').")

    # ── Public API ─────────────────────────────────────────────────────────

    def run(
        self,
        task: VerificationTask,
        timeout: int = 120,
    ) -> VerifierResult:
        """
        Run the build for the project.

        Args:
            task:    The verification task containing project info.
            timeout: Max execution time in seconds.

        Returns:
            VerifierResult with build outcome.
        """
        build_system = self._detect_build_system()
        if not build_system:
            logger.info("BuildRunner: no build system detected, skipping build")
            return VerifierResult(
                verifier_type=VerifierType.BUILD,
                command="none",
                status=VerifierStatus.SKIPPED,
                stdout="No build system detected",
                stderr="",
                exit_code=0,
                duration_ms=0.0,
                diagnostics=[],
                files_changed=0,
            )

        self._detected = build_system
        logger.info(f"BuildRunner: detected {build_system.name} build system")

        start = datetime.now()
        command = [build_system.command] + build_system.args

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=timeout,
            )
            elapsed = (datetime.now() - start).total_seconds() * 1000

            # Classify result
            diagnostics = self._classify_diagnostics(result.stdout + result.stderr)

            status = (
                VerifierStatus.PASSED
                if result.returncode == 0
                else VerifierStatus.FAILED
            )

            return VerifierResult(
                verifier_type=VerifierType.BUILD,
                command=" ".join(command),
                status=status,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=round(elapsed, 1),
                diagnostics=diagnostics,
                files_changed=self._count_build_artifacts(build_system.output_dir),
            )

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            return VerifierResult(
                verifier_type=VerifierType.BUILD,
                command=" ".join(command),
                status=VerifierStatus.TIMEOUT,
                stdout="",
                stderr=f"Build timeout after {timeout}s",
                exit_code=124,
                duration_ms=round(elapsed, 1),
                diagnostics=[],
                files_changed=0,
            )
        except Exception as exc:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            return VerifierResult(
                verifier_type=VerifierType.BUILD,
                command=" ".join(command),
                status=VerifierStatus.ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                duration_ms=round(elapsed, 1),
                diagnostics=[],
                files_changed=0,
            )

    # ── Build system detection ──────────────────────────────────────────────

    def _detect_build_system(self) -> Optional[BuildSystem]:
        """Detect the project's build system by scanning for configuration files."""
        # Check each build system in priority order
        checks = [
            ("CMake", self._check_cmake),
            ("Rust", self._check_rust),
            ("Go", self._check_go),
            ("Python", self._check_python),
            ("Node.js", self._check_node),
            ("Flutter", self._check_flutter),
            ("Java/CMake", self._check_java_cmake),
            ("Java/Maven", self._check_java_maven),
            ("Java/Gradle", self._check_java_gradle),
        ]

        for name, check_func in checks:
            result = check_func()
            if result:
                logger.debug(f"BuildRunner: detected {name}")
                return result

        return None

    def _check_cmake(self) -> Optional[BuildSystem]:
        """Check for CMake build system."""
        if (self._root / "CMakeLists.txt").exists():
            return BuildSystem(
                name="CMake",
                command="cmake",
                args=["-B", "build", "-S", "."],
                lock_file="CMakeLists.txt",
                output_dir="build",
            )
        return None

    def _check_rust(self) -> Optional[BuildSystem]:
        """Check for Rust/Cargo build system."""
        if (self._root / "Cargo.toml").exists():
            return BuildSystem(
                name="Rust",
                command="cargo",
                args=["build"],
                lock_file="Cargo.toml",
                output_dir="target",
            )
        return None

    def _check_go(self) -> Optional[BuildSystem]:
        """Check for Go build system."""
        if (self._root / "go.mod").exists():
            return BuildSystem(
                name="Go",
                command="go",
                args=["build", "./..."],
                lock_file="go.mod",
                output_dir="",
            )
        return None

    def _check_python(self) -> Optional[BuildSystem]:
        """Check for Python build system."""
        if (self._root / "setup.py").exists() or (self._root / "pyproject.toml").exists():
            return BuildSystem(
                name="Python",
                command="python",
                args=["setup.py", "build"],
                lock_file="setup.py",
                output_dir="build",
            )
        return None

    def _check_node(self) -> Optional[BuildSystem]:
        """Check for Node.js build system."""
        if (self._root / "package.json").exists():
            # Check for build script
            package_json = self._root / "package.json"
            if package_json.exists():
                import json
                try:
                    data = json.loads(package_json.read_text())
                    if "scripts" in data and "build" in data["scripts"]:
                        return BuildSystem(
                            name="Node.js",
                            command="npm",
                            args=["run", "build"],
                            lock_file="package.json",
                            output_dir="dist",
                        )
                except json.JSONDecodeError:
                    pass
        return None

    def _check_flutter(self) -> Optional[BuildSystem]:
        """Check for Flutter build system."""
        if (self._root / "pubspec.yaml").exists():
            return BuildSystem(
                name="Flutter",
                command="flutter",
                args=["build"],
                lock_file="pubspec.yaml",
                output_dir="build",
            )
        return None

    def _check_java_cmake(self) -> Optional[BuildSystem]:
        """Check for Java/CMake build system."""
        if (self._root / "CMakeLists.txt").exists() and self._has_java_files():
            return BuildSystem(
                name="Java/CMake",
                command="cmake",
                args=["-B", "build", "-S", "."],
                lock_file="CMakeLists.txt",
                output_dir="build",
            )
        return None

    def _check_java_maven(self) -> Optional[BuildSystem]:
        """Check for Java/Maven build system."""
        if (self._root / "pom.xml").exists():
            return BuildSystem(
                name="Maven",
                command="mvn",
                args=["compile"],
                lock_file="pom.xml",
                output_dir="target",
            )
        return None

    def _check_java_gradle(self) -> Optional[BuildSystem]:
        """Check for Java/Gradle build system."""
        if (self._root / "build.gradle").exists() or (self._root / "build.gradle.kts").exists():
            return BuildSystem(
                name="Gradle",
                command="gradle",
                args=["build"],
                lock_file="build.gradle",
                output_dir="build",
            )
        return None

    def _has_java_files(self) -> bool:
        """Check if project has Java source files."""
        return bool(list(self._root.rglob("*.java")))

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _classify_diagnostics(self, output: str) -> List[Dict]:
        """Parse build output for diagnostics."""
        diagnostics = []
        lines = output.splitlines()

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "error" in line_lower or "failed" in line_lower:
                diagnostics.append({
                    "severity": "error",
                    "message": line.strip(),
                    "line": i + 1,
                    "source": "build",
                })
            elif "warning" in line_lower:
                diagnostics.append({
                    "severity": "warning",
                    "message": line.strip(),
                    "line": i + 1,
                    "source": "build",
                })

        return diagnostics

    def _count_build_artifacts(self, output_dir: str) -> int:
        """Count files in build output directory."""
        if not output_dir:
            return 0

        dir_path = self._root / output_dir
        if not dir_path.exists():
            return 0

        try:
            return sum(1 for _ in dir_path.rglob("*") if _.is_file())
        except OSError:
            return 0