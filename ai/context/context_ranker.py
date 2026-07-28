"""
context_ranker.py — Multi-factor file relevance scorer.

Takes the candidate files from ContextSelector and assigns each one
a composite relevance score. The top-N files are forwarded to the
context builder for inclusion.

Scoring factors (weights sum to 1.0)
-------------------------------------
  current_file    0.30  — the file the user has open right now
  keyword_match   0.25  — how well the file name matched prompt keywords
  dependency      0.20  — is this file in the resolved dependency chain?
  git_modified    0.15  — was this file modified in the current git session?
  recently_opened 0.10  — does the user have it open in another tab?

The weights are designed so that the current file always wins, but
dependency files beat recently-opened files because they are structurally
necessary, not just convenient.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from core.logger import setup_logger
from ai.context.context_selector import CandidateFile

logger = setup_logger(__name__)

# ── Weight constants ───────────────────────────────────────────────────────
W_CURRENT_FILE    = 0.30
W_KEYWORD_MATCH   = 0.25
W_DEPENDENCY      = 0.20
W_GIT_MODIFIED    = 0.15
W_RECENTLY_OPENED = 0.10

# Number of ranked files to return by default
DEFAULT_TOP_N = 15


@dataclass
class RankedFile:
    """
    A file that has been scored for context inclusion.

    Attributes:
        path:          Absolute file path.
        score:         Composite relevance score in [0, 1].
        reasons:       Human-readable explanations for why this file was included.
        is_dependency: True if the file was pulled in by the dependency resolver.
        dep_depth:     Import chain depth from a seed file (0 = seed itself).
    """
    path:          str
    score:         float
    reasons:       List[str]
    is_dependency: bool = False
    dep_depth:     int  = 0


class ContextRanker:
    """
    Multi-factor ranker for context file candidates.

    Args:
        top_n: Maximum number of files to return after ranking.
    """

    def __init__(self, top_n: int = DEFAULT_TOP_N) -> None:
        self._top_n = top_n

    # ── Public API ─────────────────────────────────────────────────────────

    def rank(
        self,
        candidates:       List[CandidateFile],
        dependency_files: Optional[List[str]] = None,
        dep_depth_map:    Optional[Dict[str, int]] = None,
        git_modified:     Optional[Set[str]] = None,
        open_tabs:        Optional[List[str]] = None,
        current_file:     Optional[str] = None,
    ) -> List[RankedFile]:
        """
        Score and sort candidate files by composite relevance.

        Args:
            candidates:       Output of ContextSelector.select().
            dependency_files: Files discovered by DependencyResolver.
            dep_depth_map:    Map of file → discovery depth from seed.
            git_modified:     Paths of files changed in git working tree.
            open_tabs:        Paths of files open in the editor's tab bar.
            current_file:     Path of the file currently focused in editor.

        Returns:
            List of RankedFile, sorted by score descending, capped at top_n.
        """
        dep_set   = set(dependency_files or [])
        depth_map = dep_depth_map or {}
        git_set   = {str(Path(p)) for p in (git_modified or [])}
        tabs_set  = {str(Path(p)) for p in (open_tabs or [])}
        current   = str(Path(current_file)) if current_file else ""

        ranked: List[RankedFile] = []

        for candidate in candidates:
            norm = str(Path(candidate.path))
            score, reasons = self._compute_score(
                norm, candidate, dep_set, depth_map,
                git_set, tabs_set, current,
            )

            is_dep   = norm in dep_set
            dep_depth = depth_map.get(norm, 0)

            ranked.append(RankedFile(
                path=norm,
                score=round(score, 4),
                reasons=reasons,
                is_dependency=is_dep,
                dep_depth=dep_depth,
            ))

        # Also rank dependency files that weren't in the original candidates
        for dep_path in dep_set:
            norm = str(Path(dep_path))
            if not any(r.path == norm for r in ranked):
                dep_depth = depth_map.get(norm, 1)
                dep_score = self._dependency_score(dep_depth)
                reasons   = [f"dependency (depth {dep_depth})"]

                if norm in git_set:
                    dep_score += W_GIT_MODIFIED * 0.5
                    reasons.append("git modified")

                ranked.append(RankedFile(
                    path=norm,
                    score=round(dep_score, 4),
                    reasons=reasons,
                    is_dependency=True,
                    dep_depth=dep_depth,
                ))

        ranked.sort(key=lambda r: r.score, reverse=True)
        result = ranked[:self._top_n]

        logger.info(
            f"ContextRanker: {len(ranked)} files ranked → "
            f"top {len(result)} selected "
            f"(highest score: {result[0].score if result else 0:.3f})."
        )
        return result

    # ── Scoring internals ──────────────────────────────────────────────────

    def _compute_score(
        self,
        norm:       str,
        candidate:  CandidateFile,
        dep_set:    Set[str],
        depth_map:  Dict[str, int],
        git_set:    Set[str],
        tabs_set:   Set[str],
        current:    str,
    ) -> tuple[float, List[str]]:
        """Compute composite score and build reason list for one file."""
        score   = 0.0
        reasons: List[str] = []

        # ── Factor: current file ───────────────────────────────────────
        if norm == current:
            score += W_CURRENT_FILE
            reasons.append("current file")

        # ── Factor: keyword match ──────────────────────────────────────
        if candidate.keyword_score > 0.0:
            kw_contribution = W_KEYWORD_MATCH * candidate.keyword_score
            score += kw_contribution
            reasons.append(f"keyword match ({candidate.keyword_score:.2f})")

        # ── Factor: dependency chain ───────────────────────────────────
        if norm in dep_set:
            dep_depth = depth_map.get(norm, 1)
            dep_contribution = self._dependency_score(dep_depth)
            score += dep_contribution
            reasons.append(f"dependency (depth {dep_depth})")

        # ── Factor: git modified ───────────────────────────────────────
        if norm in git_set:
            score += W_GIT_MODIFIED
            reasons.append("git modified")

        # ── Factor: open in tab ────────────────────────────────────────
        if norm in tabs_set:
            score += W_RECENTLY_OPENED
            reasons.append("open in editor tab")

        return score, reasons

    @staticmethod
    def _dependency_score(depth: int) -> float:
        """
        Return a dependency weight that decays with import depth.

        depth 0 → W_DEPENDENCY (seed file itself)
        depth 1 → W_DEPENDENCY * 0.8
        depth 2 → W_DEPENDENCY * 0.6
        depth 3 → W_DEPENDENCY * 0.4
        """
        decay = max(0.4, 1.0 - (depth * 0.2))
        return W_DEPENDENCY * decay
