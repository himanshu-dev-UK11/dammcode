"""
file_import_graph.py — Project-wide file import graph.

Builds a directed graph where every node is a source file and every
edge represents an import relationship:

    A → B  means file A imports from file B.

The graph answers two questions efficiently:
    1. "What does this file depend on?" (forward edges — imports)
    2. "What would break if I change this file?" (reverse edges — imported_by)

Currently supports Python (ast-based) with regex fallback for
JS/TS (import/require statements).

This graph is used by DependencyResolver to follow import chains
and by the Context Engine for future impact-analysis features.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from core.logger import setup_logger

logger = setup_logger(__name__)

# Directories to skip when building the graph
_SKIP_DIRS: Set[str] = {
    "__pycache__", ".git", "node_modules",
    "build", "dist", ".venv", "venv", "env",
    ".mypy_cache", ".pytest_cache", "migrations",
}

# JS/TS import patterns
_JS_IMPORT_RE = re.compile(
    r"""
    (?:import\s+.*?\s+from\s+['"](.+?)['"])   # ES6 import ... from '...'
    |
    (?:require\s*\(\s*['"](.+?)['"]\s*\))      # require('...')
    """,
    re.VERBOSE,
)


@dataclass
class GraphStats:
    """Summary statistics for the import graph."""
    total_files:    int
    total_edges:    int
    most_imported:  Optional[str]   # file imported by the most others
    most_importing: Optional[str]   # file that imports the most others


class FileImportGraph:
    """
    Directed import graph for an entire project.

    Attributes:
        imports:     file → set of files it imports (forward edges).
        imported_by: file → set of files that import it (reverse edges).
    """

    def __init__(self) -> None:
        self.imports:     Dict[str, Set[str]] = {}
        self.imported_by: Dict[str, Set[str]] = {}
        self._root: Optional[Path] = None

    # ── Builder ────────────────────────────────────────────────────────────

    @classmethod
    def build(cls, root_path: str) -> "FileImportGraph":
        """
        Walk *root_path* and build the full import graph.

        Returns a populated FileImportGraph. Errors in individual files
        are silently skipped so the overall graph is always returned.
        """
        graph = cls()
        root  = Path(root_path)
        graph._root = root

        # Collect all supported source files
        py_files  = list(_iter_files(root, {".py"}))
        js_files  = list(_iter_files(root, {".js", ".jsx", ".ts", ".tsx"}))

        logger.debug(
            f"FileImportGraph: scanning {len(py_files)} .py and "
            f"{len(js_files)} JS/TS files in '{root.name}'."
        )

        for p in py_files:
            graph._process_python(p, root)

        for p in js_files:
            graph._process_js(p, root)

        total_edges = sum(len(v) for v in graph.imports.values())
        logger.debug(
            f"FileImportGraph built: {len(graph.imports)} nodes, "
            f"{total_edges} edges."
        )
        return graph

    # ── Query API ──────────────────────────────────────────────────────────

    def get_imports(self, file_path: str) -> Set[str]:
        """Return the set of files that *file_path* imports."""
        return self.imports.get(str(Path(file_path)), set())

    def get_imported_by(self, file_path: str) -> Set[str]:
        """Return the set of files that import *file_path*."""
        return self.imported_by.get(str(Path(file_path)), set())

    def all_files(self) -> List[str]:
        """Return all files in the graph (nodes with at least one edge)."""
        return list(self.imports.keys())

    def stats(self) -> GraphStats:
        """Return summary statistics about the graph."""
        total_edges = sum(len(v) for v in self.imports.values())

        most_imported = None
        if self.imported_by:
            most_imported = max(
                self.imported_by, key=lambda k: len(self.imported_by[k])
            )

        most_importing = None
        if self.imports:
            most_importing = max(self.imports, key=lambda k: len(self.imports[k]))

        return GraphStats(
            total_files=len(self.imports),
            total_edges=total_edges,
            most_imported=most_imported,
            most_importing=most_importing,
        )

    # ── Python import resolver ─────────────────────────────────────────────

    def _process_python(self, path: Path, root: Path) -> None:
        """Parse Python imports and add edges to the graph."""
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            tree    = ast.parse(content, filename=str(path))
        except (OSError, SyntaxError) as exc:
            logger.debug(f"FileImportGraph: skipping {path.name}: {exc}")
            return

        file_key = str(path)
        if file_key not in self.imports:
            self.imports[file_key] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = self._resolve_python_module(alias.name, root)
                    if resolved:
                        self._add_edge(file_key, resolved)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    resolved = self._resolve_python_module(node.module, root)
                    if resolved:
                        self._add_edge(file_key, resolved)

    def _resolve_python_module(self, module_name: str, root: Path) -> Optional[str]:
        """
        Convert a Python module name to an absolute file path.

        Only resolves modules that exist *within* the project root.
        Third-party and stdlib modules are ignored (return None).
        """
        # Convert dotted module name to path components
        parts = module_name.replace("-", "_").split(".")

        # Try as a package file: a/b/c.py
        candidate = root.joinpath(*parts).with_suffix(".py")
        if candidate.is_file():
            return str(candidate)

        # Try as a package init: a/b/c/__init__.py
        init_candidate = root.joinpath(*parts, "__init__.py")
        if init_candidate.is_file():
            return str(init_candidate)

        return None  # external / stdlib module

    # ── JS/TS import resolver ──────────────────────────────────────────────

    def _process_js(self, path: Path, root: Path) -> None:
        """Parse JS/TS import statements and add edges to the graph."""
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug(f"FileImportGraph: skipping {path.name}: {exc}")
            return

        file_key = str(path)
        if file_key not in self.imports:
            self.imports[file_key] = set()

        for match in _JS_IMPORT_RE.finditer(content):
            specifier = match.group(1) or match.group(2)
            if not specifier or not specifier.startswith("."):
                continue  # skip third-party / absolute imports

            resolved = self._resolve_js_specifier(specifier, path, root)
            if resolved:
                self._add_edge(file_key, resolved)

    def _resolve_js_specifier(
        self, specifier: str, importer: Path, root: Path
    ) -> Optional[str]:
        """Resolve a relative JS/TS import specifier to an absolute path."""
        base  = importer.parent
        target = (base / specifier).resolve()

        # Try exact path, then with extensions
        for suffix in ("", ".js", ".jsx", ".ts", ".tsx"):
            candidate = target.with_suffix(suffix) if suffix else target
            if candidate.is_file() and str(candidate).startswith(str(root)):
                return str(candidate)

        # Try as index file
        for suffix in ("/index.js", "/index.ts", "/index.jsx", "/index.tsx"):
            candidate = Path(str(target) + suffix)
            if candidate.is_file() and str(candidate).startswith(str(root)):
                return str(candidate)

        return None

    # ── Graph edge management ──────────────────────────────────────────────

    def _add_edge(self, source: str, target: str) -> None:
        """Add a directed edge source → target and update the reverse index."""
        if source == target:
            return  # No self-loops

        self.imports.setdefault(source, set()).add(target)
        self.imported_by.setdefault(target, set()).add(source)


# ── Helper ─────────────────────────────────────────────────────────────────

def _iter_files(root: Path, extensions: Set[str]):
    """Yield all files under *root* with the given extensions, skipping ignored dirs."""
    for p in root.rglob("*"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in extensions and p.is_file():
            yield p
