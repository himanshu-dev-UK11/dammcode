"""
context_builder.py — Raw context material collector.

The ContextBuilder is the first stage of the Context Engine pipeline.
It does not rank or filter — it simply gathers every raw piece of
information that the engine might want to include:

  • All project files (paths only)
  • Currently open editor tabs
  • Git-modified files in the working tree
  • Config files and entry points from ProjectContext
  • Known documentation / knowledge files
  • File modification times (for cache fingerprinting)

All I/O is lazy: file contents are NOT read here. They are read only
for the files that survive ranking, inside ContextEngine.build().
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from core.logger import setup_logger

if TYPE_CHECKING:
    from ai.memory.project_context import ProjectContext

logger = setup_logger(__name__)

# Directories whose files are never collected as raw candidates
_SKIP_DIRS: Set[str] = {
    "__pycache__", ".git", ".svn", "node_modules", "vendor",
    "build", "dist", "out", "target", "bin", "obj",
    ".venv", "venv", "env", ".mypy_cache", ".pytest_cache",
    ".terraform", "docker",
}

# Extensions that are worth collecting as candidate source files
_SOURCE_EXTS: Set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".cs", ".cpp", ".cc", ".c", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php", ".swift", ".dart", ".scala",
    ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg", ".env",
    ".md", ".txt",
}


@dataclass
class BuilderResult:
    """
    Raw context materials returned by ContextBuilder.

    Attributes:
        all_files:    Paths of all scannable files in the project.
        open_tabs:    Paths of files currently open in the editor.
        git_modified: Paths of files changed in the git working tree.
        config_files: Config/entry-point files from ProjectContext.
        doc_files:    Documentation / knowledge markdown files.
        file_mtimes:  path → mtime (float) for cache fingerprinting.
    """
    all_files:    List[str]              = field(default_factory=list)
    open_tabs:    List[str]              = field(default_factory=list)
    git_modified: List[str]             = field(default_factory=list)
    config_files: List[str]             = field(default_factory=list)
    doc_files:    List[str]             = field(default_factory=list)
    file_mtimes:  Dict[str, float]      = field(default_factory=dict)


class ContextBuilder:
    """
    Collects raw context materials for a project.

    Args:
        project_root: Absolute path to the workspace root directory.
    """

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root)
        logger.debug(f"ContextBuilder initialised (root='{self._root.name}').")

    # ── Public API ─────────────────────────────────────────────────────────

    def collect(
        self,
        project_context: Optional["ProjectContext"] = None,
        open_tabs:       Optional[List[str]] = None,
    ) -> BuilderResult:
        """
        Gather all raw context materials from the project.

        Args:
            project_context: ProjectContext from the last scan (may be None).
            open_tabs:       Paths currently open in the editor tab bar.

        Returns:
            BuilderResult with all gathered paths and mtimes.
        """
        result = BuilderResult()

        # ── 1. All source files ────────────────────────────────────────
        result.all_files = self._scan_files()
        logger.debug(f"ContextBuilder: {len(result.all_files)} source files collected.")

        # ── 2. File modification times ─────────────────────────────────
        result.file_mtimes = self._collect_mtimes(result.all_files)

        # ── 3. Open editor tabs ────────────────────────────────────────
        result.open_tabs = [str(Path(t)) for t in (open_tabs or [])]

        # ── 4. Git-modified files ──────────────────────────────────────
        result.git_modified = self._git_modified_files()

        # ── 5. Config + entry points from ProjectContext ───────────────
        if project_context:
            result.config_files = list(
                project_context.config_files + project_context.entry_points
            )
        else:
            result.config_files = self._find_config_files()

        # ── 6. Documentation files ─────────────────────────────────────
        result.doc_files = self._find_doc_files()

        return result

    # ── File scanning ──────────────────────────────────────────────────────

    def _scan_files(self) -> List[str]:
        """Walk the project tree and return paths of all source files."""
        found: List[str] = []

        for p in self._root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() in _SOURCE_EXTS or not p.suffix:
                found.append(str(p))

        return sorted(found)

    @staticmethod
    def _collect_mtimes(paths: List[str]) -> Dict[str, float]:
        """Return a mapping of path → last-modified timestamp (st_mtime)."""
        mtimes: Dict[str, float] = {}
        for raw in paths:
            try:
                mtimes[raw] = Path(raw).stat().st_mtime
            except OSError:
                mtimes[raw] = 0.0
        return mtimes

    def _find_config_files(self) -> List[str]:
        """Fallback config detection when no ProjectContext is available."""
        _CONFIG_NAMES = {
            "pyproject.toml", "setup.cfg", "setup.py",
            "package.json", "tsconfig.json", "webpack.config.js",
            "Cargo.toml", "pom.xml", "build.gradle",
            ".env", "config.yaml", "config.yml", "config.toml",
            "settings.py", "settings.yaml",
        }
        found: List[str] = []
        for name in _CONFIG_NAMES:
            candidate = self._root / name
            if candidate.is_file():
                found.append(str(candidate))
        return found

    def _find_doc_files(self) -> List[str]:
        """Locate markdown / text documentation files at the project root."""
        _DOC_NAMES = {
            "README.md", "ARCHITECTURE.md", "CONTRIBUTING.md",
            "PROJECT_BLUEPRINT.md", "PROGRESS_TRACKER.md",
            "API.md", "DESIGN.md", "NOTES.md",
        }
        found: List[str] = []
        for name in _DOC_NAMES:
            candidate = self._root / name
            if candidate.is_file():
                found.append(str(candidate))
        return found

    # ── Git integration ────────────────────────────────────────────────────

    def _git_modified_files(self) -> List[str]:
        """
        Return absolute paths of files changed in the git working tree.

        Runs 'git status --porcelain' which is always fast.
        Returns an empty list if git is unavailable or the project is
        not a git repository.
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True,
                cwd=str(self._root), timeout=5,
            )
            if result.returncode != 0:
                return []

            modified: List[str] = []
            for line in result.stdout.splitlines():
                if len(line) < 4:
                    continue
                relative = line[3:].strip()
                # Handle rename notation "old -> new"
                if " -> " in relative:
                    relative = relative.split(" -> ")[-1]
                abs_path = str(self._root / relative)
                if Path(abs_path).is_file():
                    modified.append(abs_path)

            logger.debug(
                f"ContextBuilder: {len(modified)} git-modified files detected."
            )
            return modified

        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            logger.debug(f"ContextBuilder: git status unavailable ({exc}).")
            return []
