"""
ProjectContext — single source of truth describing a scanned workspace.

This dataclass holds every piece of structural information that
MyCodingMaster needs to understand a user's project before any
planning, routing, or coding begins. It is populated exclusively
by ProjectScanner and consumed by the AI pipeline components.

Persisting this object in memory means the filesystem only needs
to be walked once per session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular imports at runtime; used only for type annotations.
    from ai.tools.tree_builder import TreeNode
    from ai.tools.framework_detector import FrameworkResult
    from ai.tools.dependency_analyzer import DependencyInfo
    from ai.tools.language_detector import LanguageBreakdown


@dataclass
class ProjectContext:
    """
    A complete structural snapshot of a user's workspace.

    This is the object the entire AI pipeline consumes.
    It is built once by ProjectScanner and stored in ProjectMemory
    so it can be injected into any agent prompt without re-scanning.

    Attributes:
        project_name:       Inferred from the root directory name.
        root_path:          Absolute path to the workspace root.
        framework:          Detected framework result (name + confidence).
        languages:          Language breakdown (percentages per language).
        dependencies:       Parsed dependency info (libraries + versions).
        tree:               Root TreeNode of the complete in-memory folder tree.
        important_files:    Absolute paths to high-value files
                            (main entry points, config files, etc.).
        entry_points:       Likely application entry-point file paths.
        config_files:       Configuration file paths found in the workspace.
        total_files:        Total number of non-ignored files in the workspace.
        total_folders:      Total number of non-ignored directories.
        total_size_bytes:   Sum of all file sizes in bytes.
        detected_pkg_manager: The package manager string (e.g. "pip", "npm").
        detected_build_system: Build system if detected (e.g. "gradle", "cmake").
        created_time:       UTC timestamp when this context object was created.
        last_scan_time:     UTC timestamp of the most recent scan that populated it.
        scan_duration_ms:   How long the last scan took in milliseconds.
        metadata:           Arbitrary extra key-value pairs for future use.
    """

    # ── Identity ─────────────────────────────────────────────────────────
    project_name: str
    root_path:    Path

    # ── Framework & Languages ─────────────────────────────────────────────
    framework:    Optional["FrameworkResult"]  = None
    languages:    Optional["LanguageBreakdown"] = None
    dependencies: Optional["DependencyInfo"]  = None

    # ── File System Structure ─────────────────────────────────────────────
    tree:          Optional["TreeNode"] = field(default=None, repr=False)
    important_files: List[str]          = field(default_factory=list)
    entry_points:    List[str]          = field(default_factory=list)
    config_files:    List[str]          = field(default_factory=list)

    # ── Statistics ────────────────────────────────────────────────────────
    total_files:           int   = 0
    total_folders:         int   = 0
    total_size_bytes:      int   = 0
    detected_pkg_manager:  str   = ""
    detected_build_system: str   = ""

    # ── Timing ───────────────────────────────────────────────────────────
    created_time:     datetime = field(default_factory=datetime.utcnow)
    last_scan_time:   Optional[datetime] = None
    scan_duration_ms: float              = 0.0

    # ── Extensibility ─────────────────────────────────────────────────────
    metadata: Dict[str, object] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def framework_name(self) -> str:
        """Return the detected framework name string, or 'Unknown'."""
        return self.framework.framework.value if self.framework else "Unknown"

    @property
    def primary_language(self) -> str:
        """Return the dominant language name, or 'Unknown'."""
        if self.languages and self.languages.primary_language:
            return self.languages.primary_language
        return "Unknown"

    @property
    def total_size_kb(self) -> float:
        """Project size in kilobytes (rounded to 2 dp)."""
        return round(self.total_size_bytes / 1024, 2)

    @property
    def total_size_mb(self) -> float:
        """Project size in megabytes (rounded to 2 dp)."""
        return round(self.total_size_bytes / (1024 * 1024), 2)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """
        Return a human-readable one-paragraph summary of the project context.

        This is the string that gets injected into AI model prompts so
        every agent immediately understands the project without re-scanning.
        """
        lang_lines = ""
        if self.languages:
            top = self.languages.languages[:5]
            lang_lines = ", ".join(f"{ls.language} ({ls.percentage}%)" for ls in top)

        dep_count = (
            len(self.dependencies.all_dependencies) if self.dependencies else 0
        )

        return (
            f"Project: {self.project_name}\n"
            f"Path: {self.root_path}\n"
            f"Framework: {self.framework_name}"
            + (f" (confidence: {self.framework.confidence:.0%})" if self.framework else "")
            + f"\nPrimary Language: {self.primary_language}\n"
            f"Languages: {lang_lines or 'N/A'}\n"
            f"Dependencies: {dep_count} packages "
            f"(manager: {self.detected_pkg_manager or 'unknown'})\n"
            f"Files: {self.total_files} | Folders: {self.total_folders} "
            f"| Size: {self.total_size_kb} KB\n"
            f"Entry Points: {', '.join(self.entry_points) or 'None detected'}\n"
            f"Last Scanned: {self.last_scan_time or 'Never'}"
        )

    def to_dict(self) -> Dict[str, object]:
        """
        Return a JSON-serializable dictionary of the context.

        The tree node is excluded as it is not serializable.
        """
        return {
            "project_name":          self.project_name,
            "root_path":             str(self.root_path),
            "framework":             self.framework_name,
            "framework_confidence":  self.framework.confidence if self.framework else 0,
            "primary_language":      self.primary_language,
            "languages":             [
                {"language": ls.language, "percentage": ls.percentage}
                for ls in (self.languages.languages if self.languages else [])
            ],
            "dependency_count":      len(self.dependencies.all_dependencies) if self.dependencies else 0,
            "package_manager":       self.detected_pkg_manager,
            "build_system":          self.detected_build_system,
            "total_files":           self.total_files,
            "total_folders":         self.total_folders,
            "total_size_bytes":      self.total_size_bytes,
            "entry_points":          self.entry_points,
            "config_files":          self.config_files,
            "important_files":       self.important_files,
            "last_scan_time":        str(self.last_scan_time),
            "scan_duration_ms":      self.scan_duration_ms,
        }

    def __repr__(self) -> str:
        return (
            f"ProjectContext(name={self.project_name!r}, "
            f"framework={self.framework_name!r}, "
            f"language={self.primary_language!r}, "
            f"files={self.total_files})"
        )
