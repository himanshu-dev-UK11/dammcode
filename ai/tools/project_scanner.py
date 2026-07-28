"""
ProjectScanner — the entry point for workspace analysis.

Before any AI model receives a prompt, MyCodingMaster must completely
understand the user's project. ProjectScanner is the single component
responsible for that understanding.

It orchestrates all specialist analyzers, collects their output, and
assembles a single ProjectContext object that becomes the source of
truth for the entire AI pipeline session.

No files are modified. The scanner is entirely read-only.

Pipeline triggered by ProjectScanner.scan():

    TreeBuilder       — build in-memory folder tree
        ↓
    LanguageDetector  — calculate language percentages
        ↓
    FrameworkDetector — identify project framework
        ↓
    DependencyAnalyzer — parse manifest files
        ↓
    ProjectContext    — assembled and returned
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

from core.logger import setup_logger
from core.exceptions import MyCodingMasterError
from ai.tools.tree_builder import TreeBuilder, TreeNode
from ai.tools.framework_detector import FrameworkDetector
from ai.tools.dependency_analyzer import DependencyAnalyzer
from ai.tools.language_detector import LanguageDetector
from ai.memory.project_context import ProjectContext

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ProjectScanError(MyCodingMasterError):
    """Raised when the project scan fails critically and cannot complete."""


# ---------------------------------------------------------------------------
# Known entry-point file names (checked in order during important-file scan)
# ---------------------------------------------------------------------------

_ENTRY_POINT_NAMES: List[str] = [
    "main.py", "app.py", "run.py", "server.py", "index.js",
    "index.ts", "main.js", "main.ts", "main.dart", "main.go",
    "main.rs", "Main.java", "Program.cs", "main.cpp",
]

_CONFIG_FILE_NAMES: List[str] = [
    ".env", ".env.example", "config.py", "settings.py", "settings.json",
    "config.json", "pyproject.toml", "package.json", "Cargo.toml",
    "pubspec.yaml", "pom.xml", "build.gradle", "CMakeLists.txt",
    "docker-compose.yml", "Dockerfile", ".gitignore", "go.mod",
]

_IMPORTANT_FILE_NAMES: List[str] = [
    "README.md", "README.rst", "CHANGELOG.md", "LICENSE",
    "CONTRIBUTING.md", ".github",
]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class ProjectScanner:
    """
    Orchestrates all workspace analysis tools and produces a ProjectContext.

    The scanner is the first component called when a user opens a
    workspace in MyCodingMaster. The resulting ProjectContext is stored
    in memory and injected into every subsequent AI prompt so that
    agents always have complete structural awareness of the project.

    Args:
        workspace_root: Absolute path to the root of the project to analyze.

    Usage:
        scanner = ProjectScanner("/path/to/user/project")
        context = scanner.scan()
        print(context.summary())

    Raises:
        ProjectScanError: If the workspace_root does not exist or is not a directory.
    """

    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        logger.info(f"ProjectScanner created for: {self.workspace_root}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> ProjectContext:
        """
        Run a full analysis of the workspace and return a ProjectContext.

        Calls all sub-analyzers in sequence. Each failure is logged and
        handled gracefully — no single analyzer failure will abort the
        entire scan. The resulting context will simply have None in that
        field and continue.

        Returns:
            A fully populated ProjectContext object.

        Raises:
            ProjectScanError: If the workspace root does not exist.
        """
        if not self.workspace_root.exists():
            raise ProjectScanError(
                f"Workspace does not exist: {self.workspace_root}"
            )
        if not self.workspace_root.is_dir():
            raise ProjectScanError(
                f"Workspace path is not a directory: {self.workspace_root}"
            )

        logger.info(f"Beginning project scan: {self.workspace_root}")
        scan_start = time.perf_counter()

        # ── Stage 1: Build tree ─────────────────────────────────────────
        tree_root = self._run_tree_builder()

        # ── Stage 2: Language detection ─────────────────────────────────
        language_breakdown = self._run_language_detector(tree_root)

        # ── Stage 3: Framework detection ────────────────────────────────
        framework_result = self._run_framework_detector()

        # ── Stage 4: Dependency analysis ────────────────────────────────
        dependency_info = self._run_dependency_analyzer()

        # ── Stage 5: Identify important files ───────────────────────────
        entry_points, config_files, important_files = self._find_important_files(tree_root)

        # ── Assemble context ─────────────────────────────────────────────
        elapsed_ms = (time.perf_counter() - scan_start) * 1000

        # Count stats from tree builder
        builder_tmp = TreeBuilder(self.workspace_root)
        # Re-use already built tree_root for stats
        total_files   = sum(1 for _ in tree_root.files()) if tree_root else 0
        total_folders = sum(1 for _ in tree_root.directories()) - 1 if tree_root else 0
        total_size    = sum(n.size_bytes for n in tree_root.files()) if tree_root else 0

        from datetime import datetime
        context = ProjectContext(
            project_name          = self.workspace_root.name,
            root_path             = self.workspace_root,
            framework             = framework_result,
            languages             = language_breakdown,
            dependencies          = dependency_info,
            tree                  = tree_root,
            entry_points          = entry_points,
            config_files          = config_files,
            important_files       = important_files,
            total_files           = total_files,
            total_folders         = total_folders,
            total_size_bytes      = total_size,
            detected_pkg_manager  = dependency_info.package_manager if dependency_info else "",
            detected_build_system = self._detect_build_system(),
            last_scan_time        = datetime.utcnow(),
            scan_duration_ms      = round(elapsed_ms, 2),
        )

        logger.info(
            f"Scan complete in {elapsed_ms:.0f}ms — "
            f"{total_files} files, {total_folders} folders, "
            f"framework={context.framework_name!r}, "
            f"language={context.primary_language!r}."
        )
        return context

    # ------------------------------------------------------------------
    # Private — sub-analyzer wrappers
    # ------------------------------------------------------------------

    def _run_tree_builder(self) -> Optional[TreeNode]:
        """Build the in-memory folder tree. Returns None on failure."""
        try:
            builder = TreeBuilder(self.workspace_root)
            return builder.build()
        except Exception as exc:
            logger.error(f"TreeBuilder failed: {exc}", exc_info=True)
            return None

    def _run_language_detector(
        self, tree_root: Optional[TreeNode]
    ) -> Optional[object]:
        """Detect language composition from the tree. Returns None on failure."""
        if tree_root is None:
            logger.warning("Skipping language detection — tree not available.")
            return None
        try:
            detector = LanguageDetector()
            return detector.detect(tree_root)
        except Exception as exc:
            logger.error(f"LanguageDetector failed: {exc}", exc_info=True)
            return None

    def _run_framework_detector(self) -> Optional[object]:
        """Detect the project framework. Returns None on failure."""
        try:
            detector = FrameworkDetector(self.workspace_root)
            return detector.detect()
        except Exception as exc:
            logger.error(f"FrameworkDetector failed: {exc}", exc_info=True)
            return None

    def _run_dependency_analyzer(self) -> Optional[object]:
        """Parse dependency manifests. Returns None on failure."""
        try:
            analyzer = DependencyAnalyzer(self.workspace_root)
            return analyzer.analyze()
        except Exception as exc:
            logger.error(f"DependencyAnalyzer failed: {exc}", exc_info=True)
            return None

    def _find_important_files(
        self, tree_root: Optional[TreeNode]
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Walk the tree to locate entry points, config files, and important docs.

        Returns:
            Tuple of (entry_points, config_files, important_files).
        """
        entry_points:    List[str] = []
        config_files:    List[str] = []
        important_files: List[str] = []

        if tree_root is None:
            return entry_points, config_files, important_files

        # Check root-level files by name
        root = self.workspace_root
        for name in _ENTRY_POINT_NAMES:
            p = root / name
            if p.exists():
                entry_points.append(str(p))

        for name in _CONFIG_FILE_NAMES:
            p = root / name
            if p.exists():
                config_files.append(str(p))

        for name in _IMPORTANT_FILE_NAMES:
            p = root / name
            if p.exists():
                important_files.append(str(p))

        return entry_points, config_files, important_files

    def _detect_build_system(self) -> str:
        """
        Detect the build system from the presence of known build files.

        Returns:
            Build system name string, or empty string if not detected.
        """
        checks = {
            "cmake":  ["CMakeLists.txt"],
            "gradle": ["build.gradle", "gradlew"],
            "maven":  ["pom.xml"],
            "cargo":  ["Cargo.toml"],
            "make":   ["Makefile", "GNUmakefile"],
            "meson":  ["meson.build"],
            "bazel":  ["BUILD", "WORKSPACE"],
            "npm":    ["package.json"],
        }
        root = self.workspace_root
        for system, files in checks.items():
            if any((root / f).exists() for f in files):
                return system
        return ""
