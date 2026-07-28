"""
dependency_resolver.py — Recursive import-chain follower.

Given a set of "seed" files (the files the Context Engine has
already decided are relevant), DependencyResolver walks the
FileImportGraph to collect every file those seeds depend on,
up to a configurable depth.

This prevents the common failure mode where the AI receives
"login.py" but not the "auth.py" and "user.py" it imports,
causing the model to hallucinate implementations for those symbols.

Depth semantics:
    depth 0 → seed files only (no resolution)
    depth 1 → direct imports of seeds
    depth 2 → imports of imports
    depth 3 → (default) three levels deep
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from core.logger import setup_logger
from ai.context.file_import_graph import FileImportGraph

logger = setup_logger(__name__)

DEFAULT_MAX_DEPTH = 3


@dataclass
class ResolvedChain:
    """
    The full dependency chain built from a set of seed files.

    Attributes:
        files:         All resolved file paths (seeds + dependencies),
                       ordered by discovery (BFS).
        depth_map:     file_path → depth at which it was discovered.
        seed_files:    The original input seeds.
        max_depth:     The depth cap that was applied.
    """
    files:      List[str]
    depth_map:  Dict[str, int]
    seed_files: List[str]
    max_depth:  int

    def at_depth(self, depth: int) -> List[str]:
        """Return files discovered at a specific depth."""
        return [f for f, d in self.depth_map.items() if d == depth]


class DependencyResolver:
    """
    Follows import chains from a set of seed files using a BFS strategy.

    Args:
        import_graph: A pre-built FileImportGraph for the project.
        max_depth:    Maximum number of hops from any seed file.
    """

    def __init__(
        self,
        import_graph: FileImportGraph,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> None:
        self._graph     = import_graph
        self._max_depth = max_depth
        logger.debug(
            f"DependencyResolver initialised (max_depth={max_depth})."
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def resolve(
        self,
        seed_files: List[str],
        max_depth: Optional[int] = None,
    ) -> ResolvedChain:
        """
        Resolve all dependencies reachable from *seed_files*.

        Uses a breadth-first search so shallower dependencies are
        discovered first and the depth_map is accurate.

        Args:
            seed_files: Files the Context Engine already selected.
            max_depth:  Override the instance default for this call.

        Returns:
            ResolvedChain with all discovered paths and their depths.
        """
        depth_limit = max_depth if max_depth is not None else self._max_depth

        visited:   Dict[str, int] = {}   # path → discovery depth
        queue:     List[tuple[str, int]] = []

        # Initialise BFS with seeds at depth 0
        for seed in seed_files:
            if seed not in visited:
                visited[seed] = 0
                queue.append((seed, 0))

        # BFS
        head = 0
        while head < len(queue):
            current, depth = queue[head]
            head += 1

            if depth >= depth_limit:
                continue  # Respect depth cap — don't enqueue children

            children = self._graph.get_imports(current)
            for child in children:
                if child not in visited:
                    visited[child] = depth + 1
                    queue.append((child, depth + 1))
                    logger.debug(
                        f"Dependency resolved: depth={depth+1} "
                        f"{self._short(current)} → {self._short(child)}"
                    )

        # Build ordered output list (BFS order = discovery order)
        ordered = [path for path, _ in queue]

        chain = ResolvedChain(
            files=ordered,
            depth_map=visited,
            seed_files=list(seed_files),
            max_depth=depth_limit,
        )

        dep_count = len(ordered) - len(seed_files)
        logger.info(
            f"DependencyResolver: {len(seed_files)} seeds → "
            f"{dep_count} dependencies found (depth ≤ {depth_limit})."
        )
        return chain

    def reverse_resolve(
        self,
        file_path: str,
        max_depth: int = 1,
    ) -> List[str]:
        """
        Find files that *import* the given file (impact analysis).

        Useful for answering "what would break if I change this file?"
        Returns the set of files that directly or transitively
        import *file_path*, up to *max_depth* hops.
        """
        visited: Set[str] = set()
        queue:   List[tuple[str, int]] = [(file_path, 0)]
        results: List[str] = []

        while queue:
            current, depth = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current != file_path:
                results.append(current)

            if depth < max_depth:
                for parent in self._graph.get_imported_by(current):
                    if parent not in visited:
                        queue.append((parent, depth + 1))

        return results

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _short(path: str) -> str:
        """Return a short display name (last 2 path components)."""
        from pathlib import Path
        p = Path(path)
        return str(p.parent.name + "/" + p.name)
