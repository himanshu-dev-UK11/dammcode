"""
TreeNode and TreeBuilder — in-memory folder tree generator.

Walks a workspace directory and builds a complete in-memory
representation of every file and folder. The resulting tree
is the structural backbone of ProjectContext; all other scanners
receive it to avoid redundant filesystem walks.

No files are modified. This module is read-only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from core.logger import setup_logger
from core.exceptions import MyCodingMasterError

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class TreeBuildError(MyCodingMasterError):
    """Raised when the tree cannot be built from the given root path."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TreeNode:
    """
    Represents a single file or directory in the project tree.

    Attributes:
        name:          Filename or directory name (not the full path).
        path:          Absolute path as a Path object.
        is_directory:  True if this node represents a directory.
        parent:        Reference to the parent TreeNode (None for root).
        children:      Ordered list of child TreeNodes (empty for files).
        extension:     Lowercased file extension including dot (e.g. ".py"),
                       or empty string for directories.
        size_bytes:    File size in bytes. 0 for directories.
        last_modified: UTC datetime of the last file modification.
    """

    name:          str
    path:          Path
    is_directory:  bool
    parent:        Optional[TreeNode]        = field(default=None,  repr=False)
    children:      List[TreeNode]            = field(default_factory=list, repr=False)
    extension:     str                       = ""
    size_bytes:    int                       = 0
    last_modified: Optional[datetime]        = None

    # Index populated by TreeBuilder for O(1) path lookups
    _path_index: Dict[str, TreeNode]         = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.is_directory:
            self.extension = self.path.suffix.lower()

    # ------------------------------------------------------------------
    # Tree traversal helpers
    # ------------------------------------------------------------------

    def walk(self) -> Iterator[TreeNode]:
        """Depth-first iterator over this node and all its descendants."""
        yield self
        for child in self.children:
            yield from child.walk()

    def files(self) -> Iterator[TreeNode]:
        """Iterator over all file nodes in the subtree (non-directories)."""
        return (n for n in self.walk() if not n.is_directory)

    def directories(self) -> Iterator[TreeNode]:
        """Iterator over all directory nodes in the subtree."""
        return (n for n in self.walk() if n.is_directory)

    def find_by_name(self, name: str) -> List[TreeNode]:
        """Return all nodes whose filename matches `name` (case-insensitive)."""
        return [n for n in self.walk() if n.name.lower() == name.lower()]

    def depth(self) -> int:
        """Return depth from this node to the root (root = 0)."""
        d = 0
        node = self
        while node.parent is not None:
            d += 1
            node = node.parent
        return d

    def relative_path(self, root: Path) -> Path:
        """Return this node's path relative to `root`."""
        return self.path.relative_to(root)

    def __repr__(self) -> str:
        kind = "Dir" if self.is_directory else "File"
        return f"TreeNode({kind}, {self.name!r})"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

# Directories to skip during scanning
_IGNORED_DIRS: frozenset = frozenset({
    ".git",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
    ".dart_tool",
    ".idea",
    ".vscode",
})


class TreeBuilder:
    """
    Builds a TreeNode tree from a workspace root directory.

    The tree is built once and cached in memory. The builder
    also maintains a path-keyed index for O(1) lookups by
    absolute path string.

    Usage:
        builder = TreeBuilder("/path/to/project")
        root    = builder.build()
        node    = builder.find("/path/to/project/main.py")

    Raises:
        TreeBuildError: If the root path does not exist or is not a directory.
    """

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()
        self._root_node: Optional[TreeNode] = None
        self._path_index: Dict[str, TreeNode] = {}
        logger.info(f"TreeBuilder initialized for: {self.root_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> TreeNode:
        """
        Walk the filesystem and build the complete in-memory tree.

        Returns:
            The root TreeNode of the built tree.

        Raises:
            TreeBuildError: If root_path does not exist or is not a directory.
        """
        if not self.root_path.exists():
            raise TreeBuildError(f"Root path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise TreeBuildError(f"Root path is not a directory: {self.root_path}")

        logger.info(f"Building tree for: {self.root_path}")
        self._path_index.clear()
        self._root_node = self._build_node(self.root_path, parent=None)
        logger.info(
            f"Tree built — {self.total_files()} files, "
            f"{self.total_dirs()} directories."
        )
        return self._root_node

    def find(self, path: str | Path) -> Optional[TreeNode]:
        """
        Look up a node by its absolute path string (O(1)).

        Returns None if the path was not indexed (e.g. it was ignored).
        """
        return self._path_index.get(str(Path(path).resolve()))

    def total_files(self) -> int:
        """Return the total number of file nodes in the tree."""
        if self._root_node is None:
            return 0
        return sum(1 for _ in self._root_node.files())

    def total_dirs(self) -> int:
        """Return the total number of directory nodes (excluding root)."""
        if self._root_node is None:
            return 0
        return sum(1 for _ in self._root_node.directories()) - 1  # exclude root

    def total_size_bytes(self) -> int:
        """Return the sum of all file sizes in the tree."""
        if self._root_node is None:
            return 0
        return sum(n.size_bytes for n in self._root_node.files())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_node(self, path: Path, parent: Optional[TreeNode]) -> TreeNode:
        """
        Recursively create a TreeNode for `path` and all its children.

        Directories in `_IGNORED_DIRS` are skipped entirely.
        """
        stat = path.stat()
        node = TreeNode(
            name          = path.name,
            path          = path,
            is_directory  = path.is_dir(),
            parent        = parent,
            size_bytes    = stat.st_size if path.is_file() else 0,
            last_modified = datetime.utcfromtimestamp(stat.st_mtime),
        )

        # Register in the path index
        self._path_index[str(path)] = node

        if path.is_dir():
            try:
                entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                logger.warning(f"Permission denied — skipping directory: {path}")
                return node

            for entry in entries:
                if entry.name in _IGNORED_DIRS:
                    logger.debug(f"Skipping ignored directory: {entry.name}")
                    continue
                try:
                    child = self._build_node(entry, parent=node)
                    node.children.append(child)
                except Exception as exc:
                    logger.warning(f"Could not index {entry}: {exc}")

        return node

    def render_ascii(self, node: Optional[TreeNode] = None, prefix: str = "") -> str:
        """
        Return an ASCII art representation of the tree (like the `tree` command).

        Args:
            node:   Starting node (defaults to root).
            prefix: Internal recursion prefix — do not set manually.
        """
        if node is None:
            node = self._root_node
        if node is None:
            return "(empty tree)"

        lines: List[str] = []
        if node.parent is None:
            lines.append(str(node.path))

        children = node.children
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{child.name}")
            if child.is_directory:
                extension = "    " if is_last else "│   "
                lines.append(self.render_ascii(child, prefix + extension))

        return "\n".join(filter(None, lines))
