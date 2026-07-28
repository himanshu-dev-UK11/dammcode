"""
FrameworkDetector — automatically identify the project's framework.

Inspects well-known configuration and manifest files in the project
root to determine which framework (and language ecosystem) the user's
project belongs to. Returns a structured detection result with a
framework name, a confidence score, and the evidence that led to
the conclusion.

No files are written. This module is purely read-only analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from core.logger import setup_logger
from core.exceptions import MyCodingMasterError

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class FrameworkDetectionError(MyCodingMasterError):
    """Raised when framework detection cannot run due to an I/O or parse error."""


# ---------------------------------------------------------------------------
# Supported frameworks
# ---------------------------------------------------------------------------

class Framework(str, Enum):
    """All frameworks the detector can identify."""
    FLUTTER     = "Flutter"
    DJANGO      = "Django"
    FASTAPI     = "FastAPI"
    FLASK       = "Flask"
    PYTHON      = "Python"           # Generic Python (no web framework)
    REACT       = "React"
    NEXTJS      = "Next.js"
    NODEJS      = "Node.js"          # Generic Node (no specific framework)
    JAVA        = "Java"             # Generic Java / Maven / Gradle
    SPRING_BOOT = "Spring Boot"
    RUST        = "Rust"
    GO          = "Go"
    CSHARP      = "C#"
    CPP         = "C++"
    UNKNOWN     = "Unknown"


# ---------------------------------------------------------------------------
# Detection result
# ---------------------------------------------------------------------------

@dataclass
class FrameworkResult:
    """
    The outcome of a single framework detection pass.

    Attributes:
        framework:   The detected Framework enum value.
        confidence:  A float between 0.0 and 1.0 (higher = more certain).
        reason:      Human-readable explanation of why this framework was chosen.
        evidence_files: List of file paths that contributed to the detection.
    """
    framework:       Framework
    confidence:      float
    reason:          str
    evidence_files:  List[str]

    def __repr__(self) -> str:
        return (
            f"FrameworkResult(framework={self.framework.value!r}, "
            f"confidence={self.confidence:.0%}, reason={self.reason!r})"
        )


# ---------------------------------------------------------------------------
# Detection rules
# Each rule is: (file_to_check, content_substring_or_None, framework, confidence, reason)
# If content_substring is None, mere existence of the file is enough.
# ---------------------------------------------------------------------------

@dataclass
class _DetectionRule:
    filename:         str
    content_hint:     Optional[str]   # substring to search for inside the file
    framework:        Framework
    confidence:       float
    reason:           str


_RULES: List[_DetectionRule] = [
    # --- Flutter ---
    _DetectionRule("pubspec.yaml",    "flutter:",         Framework.FLUTTER,     0.98, "pubspec.yaml contains 'flutter:' dependency"),
    _DetectionRule("pubspec.yaml",    None,               Framework.FLUTTER,     0.80, "pubspec.yaml present (likely Flutter/Dart)"),

    # --- Python web frameworks (checked before generic Python) ---
    _DetectionRule("requirements.txt", "django",          Framework.DJANGO,      0.90, "requirements.txt contains 'django'"),
    _DetectionRule("requirements.txt", "fastapi",         Framework.FASTAPI,     0.90, "requirements.txt contains 'fastapi'"),
    _DetectionRule("requirements.txt", "flask",           Framework.FLASK,       0.90, "requirements.txt contains 'flask'"),
    _DetectionRule("pyproject.toml",   "django",          Framework.DJANGO,      0.90, "pyproject.toml contains 'django'"),
    _DetectionRule("pyproject.toml",   "fastapi",         Framework.FASTAPI,     0.90, "pyproject.toml contains 'fastapi'"),
    _DetectionRule("pyproject.toml",   "flask",           Framework.FLASK,       0.90, "pyproject.toml contains 'flask'"),
    _DetectionRule("manage.py",        "django",          Framework.DJANGO,      0.95, "manage.py present with 'django' content"),
    _DetectionRule("manage.py",        None,              Framework.DJANGO,      0.85, "manage.py present (Django management script)"),

    # --- Generic Python ---
    _DetectionRule("requirements.txt", None,              Framework.PYTHON,      0.70, "requirements.txt present (Python project)"),
    _DetectionRule("pyproject.toml",   None,              Framework.PYTHON,      0.70, "pyproject.toml present (Python project)"),
    _DetectionRule("setup.py",         None,              Framework.PYTHON,      0.65, "setup.py present (Python package)"),

    # --- JavaScript / Node ---
    _DetectionRule("package.json",     '"next"',          Framework.NEXTJS,      0.95, "package.json contains 'next' dependency"),
    _DetectionRule("next.config.js",   None,              Framework.NEXTJS,      0.97, "next.config.js present"),
    _DetectionRule("next.config.mjs",  None,              Framework.NEXTJS,      0.97, "next.config.mjs present"),
    _DetectionRule("package.json",     '"react"',         Framework.REACT,       0.90, "package.json contains 'react' dependency"),
    _DetectionRule("package.json",     None,              Framework.NODEJS,      0.65, "package.json present (Node.js project)"),

    # --- Rust ---
    _DetectionRule("Cargo.toml",       None,              Framework.RUST,        0.98, "Cargo.toml present (Rust project)"),

    # --- Java / Spring Boot ---
    _DetectionRule("pom.xml",          "spring-boot",     Framework.SPRING_BOOT, 0.95, "pom.xml contains 'spring-boot'"),
    _DetectionRule("build.gradle",     "spring-boot",     Framework.SPRING_BOOT, 0.95, "build.gradle contains 'spring-boot'"),
    _DetectionRule("pom.xml",          None,              Framework.JAVA,        0.80, "pom.xml present (Maven/Java project)"),
    _DetectionRule("build.gradle",     None,              Framework.JAVA,        0.80, "build.gradle present (Gradle/Java project)"),

    # --- C# ---
    _DetectionRule("*.sln",            None,              Framework.CSHARP,      0.95, ".sln solution file present (C# project)"),

    # --- C++ ---
    _DetectionRule("CMakeLists.txt",   None,              Framework.CPP,         0.90, "CMakeLists.txt present (C++ CMake project)"),

    # --- Go ---
    _DetectionRule("go.mod",           None,              Framework.GO,          0.97, "go.mod present (Go module)"),
]


class FrameworkDetector:
    """
    Detects the dominant framework of a software project.

    Evaluates a prioritized list of file-based detection rules
    against the project root, returning the highest-confidence
    match as a FrameworkResult.

    If no rule matches, returns UNKNOWN with 0.0 confidence.

    Usage:
        detector = FrameworkDetector("/path/to/project")
        result   = detector.detect()
        print(result.framework.value, result.confidence)
    """

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()
        logger.info(f"FrameworkDetector initialized for: {self.root_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self) -> FrameworkResult:
        """
        Run all detection rules and return the best match.

        Returns:
            FrameworkResult with the detected framework, confidence, reason,
            and list of evidence file paths.

        Raises:
            FrameworkDetectionError: If an unexpected I/O error occurs.
        """
        logger.info("Starting framework detection...")
        best: Optional[FrameworkResult] = None

        for rule in _RULES:
            result = self._evaluate_rule(rule)
            if result is None:
                continue
            if best is None or result.confidence > best.confidence:
                best = result
                logger.debug(f"New best match: {best}")

        if best is None:
            logger.info("No framework detected — returning UNKNOWN.")
            return FrameworkResult(
                framework=Framework.UNKNOWN,
                confidence=0.0,
                reason="No recognizable configuration file found.",
                evidence_files=[],
            )

        logger.info(f"Framework detected: {best.framework.value} ({best.confidence:.0%})")
        return best

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _evaluate_rule(self, rule: _DetectionRule) -> Optional[FrameworkResult]:
        """
        Test a single detection rule against the filesystem.

        Handles glob patterns (e.g. "*.sln") and optional content checks.

        Returns a FrameworkResult if the rule matches, otherwise None.
        """
        # Resolve the target file(s) — support simple glob patterns
        if "*" in rule.filename:
            matches = list(self.root_path.glob(rule.filename))
        else:
            candidate = self.root_path / rule.filename
            matches = [candidate] if candidate.exists() else []

        if not matches:
            return None

        evidence = [str(p) for p in matches]

        # If a content check is required, verify at least one matching file
        if rule.content_hint is not None:
            content_match = False
            for filepath in matches:
                try:
                    text = filepath.read_text(encoding="utf-8", errors="ignore").lower()
                    if rule.content_hint.lower() in text:
                        content_match = True
                        break
                except Exception as exc:
                    logger.warning(f"Could not read {filepath}: {exc}")
            if not content_match:
                return None

        return FrameworkResult(
            framework=rule.framework,
            confidence=rule.confidence,
            reason=rule.reason,
            evidence_files=evidence,
        )
