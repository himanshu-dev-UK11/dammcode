"""
LanguageDetector — determine language composition of a project.

Walks the project tree, maps every file extension to a programming
language, and returns a breakdown of language usage as both raw file
counts and percentage of total code files.

No files are modified. This module is read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger
from ai.tools.tree_builder import TreeNode

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Extension → Language mapping
# ---------------------------------------------------------------------------

_EXT_MAP: Dict[str, str] = {
    # Python
    ".py":    "Python",
    ".pyi":   "Python",
    ".pyw":   "Python",
    # JavaScript / TypeScript
    ".js":    "JavaScript",
    ".mjs":   "JavaScript",
    ".cjs":   "JavaScript",
    ".jsx":   "JavaScript",
    ".ts":    "TypeScript",
    ".tsx":   "TypeScript",
    # Dart / Flutter
    ".dart":  "Dart",
    # Rust
    ".rs":    "Rust",
    # Go
    ".go":    "Go",
    # Java
    ".java":  "Java",
    # Kotlin
    ".kt":    "Kotlin",
    ".kts":   "Kotlin",
    # C / C++
    ".c":     "C",
    ".h":     "C",
    ".cpp":   "C++",
    ".cxx":   "C++",
    ".cc":    "C++",
    ".hpp":   "C++",
    # C#
    ".cs":    "C#",
    # Ruby
    ".rb":    "Ruby",
    # PHP
    ".php":   "PHP",
    # Swift
    ".swift": "Swift",
    # Shell
    ".sh":    "Shell",
    ".bash":  "Shell",
    ".zsh":   "Shell",
    ".ps1":   "PowerShell",
    # Web
    ".html":  "HTML",
    ".htm":   "HTML",
    ".css":   "CSS",
    ".scss":  "CSS",
    ".sass":  "CSS",
    ".less":  "CSS",
    # Data / Config
    ".json":  "JSON",
    ".yaml":  "YAML",
    ".yml":   "YAML",
    ".toml":  "TOML",
    ".xml":   "XML",
    ".sql":   "SQL",
    ".env":   "Config",
    ".ini":   "Config",
    ".cfg":   "Config",
    ".conf":  "Config",
    # Documentation
    ".md":    "Markdown",
    ".rst":   "reStructuredText",
    ".txt":   "Text",
    # Other
    ".r":     "R",
    ".scala": "Scala",
    ".lua":   "Lua",
    ".proto": "Protobuf",
    ".graphql": "GraphQL",
    ".gql":   "GraphQL",
}

# These extensions are counted but treated as non-code for percentage purposes
_NON_CODE_LANGUAGES: frozenset = frozenset({
    "JSON", "YAML", "TOML", "XML", "Markdown",
    "reStructuredText", "Text", "Config",
})


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class LanguageStats:
    """
    Statistics for a single programming language.

    Attributes:
        language:    Language name (e.g. "Python", "Dart").
        file_count:  Number of files written in this language.
        percentage:  Percentage of total detected files (0.0–100.0).
        is_code:     False for config/data/doc formats (JSON, YAML, etc.).
    """
    language:   str
    file_count: int
    percentage: float
    is_code:    bool = True

    def __repr__(self) -> str:
        return f"LanguageStats({self.language!r}, {self.file_count} files, {self.percentage:.1f}%)"


@dataclass
class LanguageBreakdown:
    """
    Full language composition of a project.

    Attributes:
        languages:        Ordered list (descending by file count).
        total_files:      Total number of files analyzed.
        primary_language: The language with the highest file count.
    """
    languages:        List[LanguageStats]
    total_files:      int
    primary_language: Optional[str] = None

    def get(self, language: str) -> Optional[LanguageStats]:
        """Return stats for a specific language, or None if not detected."""
        name_lower = language.lower()
        return next(
            (ls for ls in self.languages if ls.language.lower() == name_lower),
            None,
        )

    def code_languages(self) -> List[LanguageStats]:
        """Return only languages that are considered source code."""
        return [ls for ls in self.languages if ls.is_code]

    def __repr__(self) -> str:
        top = self.languages[:3] if self.languages else []
        return f"LanguageBreakdown(primary={self.primary_language!r}, top={top})"


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class LanguageDetector:
    """
    Determines the programming language composition of a project.

    Requires a pre-built TreeNode (from TreeBuilder) to avoid
    redundant filesystem walks.

    Usage:
        builder   = TreeBuilder(root)
        tree_root = builder.build()
        detector  = LanguageDetector()
        breakdown = detector.detect(tree_root)
        print(breakdown.primary_language)  # "Python"
    """

    def __init__(self) -> None:
        logger.info("LanguageDetector initialized.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, tree_root: TreeNode) -> LanguageBreakdown:
        """
        Walk the tree and calculate language percentages.

        Args:
            tree_root: Root TreeNode returned by TreeBuilder.build().

        Returns:
            LanguageBreakdown with per-language stats and a primary language.
        """
        logger.info("Detecting language composition...")
        counts: Dict[str, int] = {}

        for node in tree_root.files():
            lang = _EXT_MAP.get(node.extension)
            if lang:
                counts[lang] = counts.get(lang, 0) + 1

        total = sum(counts.values())
        if total == 0:
            logger.info("No recognized source files found.")
            return LanguageBreakdown(languages=[], total_files=0)

        stats: List[LanguageStats] = []
        for lang, count in sorted(counts.items(), key=lambda x: -x[1]):
            stats.append(LanguageStats(
                language   = lang,
                file_count = count,
                percentage = round(count / total * 100, 1),
                is_code    = lang not in _NON_CODE_LANGUAGES,
            ))

        primary = stats[0].language if stats else None
        logger.info(
            f"Language detection complete — {len(stats)} languages, "
            f"primary: {primary!r}, total files: {total}."
        )
        return LanguageBreakdown(
            languages        = stats,
            total_files      = total,
            primary_language = primary,
        )

    def detect_from_path(self, root_path: str | Path) -> LanguageBreakdown:
        """
        Convenience method: build a tree internally and detect languages.

        Use this when you do not already have a TreeNode available.
        """
        from ai.tools.tree_builder import TreeBuilder
        builder   = TreeBuilder(root_path)
        tree_root = builder.build()
        return self.detect(tree_root)
