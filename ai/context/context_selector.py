"""
context_selector.py — Keyword-driven file relevance filter.

Chooses which files in the project are *candidates* for inclusion
in the context package, based on the user's prompt and the
currently open file.

Strategy
--------
1.  Extract intent keywords from the prompt (nouns, verbs, identifiers).
2.  Score every project file by how well its path/name matches those keywords.
3.  Always include the current file and its direct parents.
4.  Always exclude low-value directories (build artifacts, Docker, docs).
5.  Return the top N candidates for downstream ranking.

This is a purely heuristic, zero-AI filter — fast enough to run
synchronously on every keystroke if needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from core.logger import setup_logger

logger = setup_logger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────

# Directories whose contents are almost never relevant to AI coding tasks
_EXCLUDE_DIRS: Set[str] = {
    "__pycache__", ".git", ".svn", ".hg",
    "node_modules", "vendor", "third_party",
    "build", "dist", "out", "target", "bin", "obj",
    ".venv", "venv", "env", "site-packages",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "migrations", ".terraform", "docker",
}

# File patterns that are almost never code-relevant for a coding task
_EXCLUDE_PATTERNS: Set[str] = {
    "readme.md", "changelog.md", "license", "license.md",
    "license.txt", "authors", "contributing.md", "code_of_conduct.md",
    ".gitignore", ".dockerignore", ".editorconfig",
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", ".env.sample",
}

# Extensions treated as "always exclude" (binary / generated)
_EXCLUDE_EXTS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp3", ".mp4", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".bz2",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".lock",  # package lock files are rarely useful for coding tasks
}

# Extensions treated as "config — include only when needed"
_CONFIG_EXTS: Set[str] = {
    ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg",
    ".env", ".conf", ".config",
}

# Maximum number of candidates to return (before ranking)
DEFAULT_MAX_CANDIDATES = 30


@dataclass
class CandidateFile:
    """A file that passed the selection filter."""
    path:             str
    keyword_score:    float   # 0.0 → 1.0 — how well name matched prompt keywords
    is_current_file:  bool = False
    is_config_file:   bool = False
    reason:           str  = ""


class ContextSelector:
    """
    Selects a subset of project files as candidates for context inclusion.

    Args:
        max_candidates: Upper bound on the number of files returned.
    """

    def __init__(self, max_candidates: int = DEFAULT_MAX_CANDIDATES) -> None:
        self._max = max_candidates

    # ── Public API ─────────────────────────────────────────────────────────

    def select(
        self,
        prompt:        str,
        all_files:     List[str],
        current_file:  Optional[str] = None,
        config_files:  Optional[List[str]] = None,
    ) -> List[CandidateFile]:
        """
        Choose candidate files from *all_files* relevant to *prompt*.

        Args:
            prompt:       The raw user prompt.
            all_files:    Absolute paths of all project files.
            current_file: The file currently open in the editor (always included).
            config_files: Known config files (always included if budget allows).

        Returns:
            List of CandidateFile, sorted by keyword_score descending.
        """
        keywords = self._extract_keywords(prompt)
        logger.debug(
            f"ContextSelector: {len(all_files)} files, "
            f"keywords={keywords!r}"
        )

        current_norm = str(Path(current_file)) if current_file else ""
        config_norm  = {str(Path(c)) for c in (config_files or [])}
        candidates:  List[CandidateFile] = []

        for raw_path in all_files:
            p = Path(raw_path)
            norm = str(p)

            # ── Hard excludes ──────────────────────────────────────────
            if self._is_excluded(p):
                continue

            is_current = (norm == current_norm)
            is_config  = (norm in config_norm or p.suffix.lower() in _CONFIG_EXTS)

            # ── Keyword scoring ────────────────────────────────────────
            score = self._score_path(p, keywords)

            # Always include current file (score bump)
            if is_current:
                score = max(score, 1.0)
                reason = "current file"
            elif score == 0.0 and not is_config:
                continue  # No keyword match and not a config — skip
            elif is_config:
                reason = "config file"
                score  = max(score, 0.1)  # baseline so it passes threshold
            else:
                reason = f"keyword match ({score:.2f})"

            candidates.append(CandidateFile(
                path=norm,
                keyword_score=round(score, 3),
                is_current_file=is_current,
                is_config_file=is_config,
                reason=reason,
            ))

        # Sort by score descending, cap at max
        candidates.sort(key=lambda c: (c.is_current_file, c.keyword_score), reverse=True)
        result = candidates[:self._max]

        logger.info(
            f"ContextSelector: {len(all_files)} files → "
            f"{len(result)} candidates selected."
        )
        return result

    # ── Keyword extraction ─────────────────────────────────────────────────

    @staticmethod
    def _extract_keywords(prompt: str) -> List[str]:
        """
        Extract meaningful keywords from the user prompt.

        Splits on whitespace/punctuation, lower-cases everything, and
        removes very common English stop words that carry no file-name signal.
        """
        _STOP_WORDS = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "and",
            "or", "but", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "that", "this", "these", "those",
            "it", "its", "my", "your", "our", "their", "how", "what", "why",
            "when", "where", "which", "who",
            "fix", "add", "update", "change", "make", "create", "delete",
            "remove", "refactor", "improve", "implement", "write", "use",
        }

        tokens = re.findall(r"[a-zA-Z_]\w*", prompt.lower())
        return [t for t in tokens if t not in _STOP_WORDS and len(t) >= 3]

    # ── Scoring ────────────────────────────────────────────────────────────

    @staticmethod
    def _score_path(path: Path, keywords: List[str]) -> float:
        """
        Score a file path against a list of keywords.

        Checks the stem and parent directory names (case-insensitive).
        A full stem match scores higher than a partial substring match.
        """
        if not keywords:
            return 0.0

        # Parts to check: file stem and each parent dir name
        check_parts = [path.stem.lower()]
        check_parts += [p.lower() for p in path.parts[:-1]]

        total   = 0.0
        matched = 0

        for kw in keywords:
            kw_l = kw.lower()
            for part in check_parts:
                if part == kw_l:
                    total += 1.0   # Exact match
                    matched += 1
                    break
                elif kw_l in part or part in kw_l:
                    total += 0.5   # Partial match
                    matched += 1
                    break

        if matched == 0:
            return 0.0

        # Normalise to [0, 1]
        return min(1.0, total / len(keywords))

    # ── Exclusion logic ────────────────────────────────────────────────────

    @staticmethod
    def _is_excluded(path: Path) -> bool:
        """
        Return True if the file should be unconditionally excluded.

        Checks:
          - Any path component is a known exclude directory.
          - The file name (lower-cased) is in the exclude patterns set.
          - The file extension is a binary/generated type.
        """
        # Check each component (not just leaf)
        for part in path.parts:
            if part.lower() in _EXCLUDE_DIRS:
                return True

        # Check file name
        if path.name.lower() in _EXCLUDE_PATTERNS:
            return True

        # Check extension
        if path.suffix.lower() in _EXCLUDE_EXTS:
            return True

        return False
