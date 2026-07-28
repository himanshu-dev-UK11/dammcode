"""
ProjectMemory — persists project-level AI knowledge across sessions.

Stores high-level findings about the open workspace: architecture
decisions, known issues, key files, and summaries from past scans.
This lets the AI "remember" the project without re-scanning on every
request.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import setup_logger

logger = setup_logger(__name__)

_STORAGE_FILE = Path("config/project_memory.json")


@dataclass
class ProjectFact:
    """A single piece of remembered knowledge about the project."""
    fact_id:    str
    category:   str          # "architecture" | "issue" | "convention" | "file" | "general"
    content:    str
    confidence: float = 1.0  # 0-1
    source:     str = ""     # where this fact came from
    timestamp:  str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata:   Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectFact":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ProjectMemory:
    """
    In-memory + disk-backed store of project knowledge.

    Usage:
        memory = ProjectMemory()
        memory.remember(category="architecture", content="Uses MVC pattern")
        memory.remember(category="issue", content="main.py is too large (1200 lines)")
        ctx = memory.build_context_string()  # inject into AI prompt
    """

    def __init__(self, storage_file: Optional[str] = None) -> None:
        self._file = Path(storage_file) if storage_file else _STORAGE_FILE
        self._facts: List[ProjectFact] = []
        self._project_name: str = ""
        self._project_root: str = ""
        self._load()
        logger.info(f"ProjectMemory initialized ({len(self._facts)} facts)")

    # ── Public API ─────────────────────────────────────────────────────────

    def set_project(self, name: str, root: str) -> None:
        """Set the active project. Clears memory if the project changed."""
        if self._project_root and self._project_root != root:
            logger.info(f"ProjectMemory: project changed — clearing old facts")
            self._facts.clear()
        self._project_name = name
        self._project_root = root
        self._save()

    def remember(
        self,
        category: str,
        content:  str,
        confidence: float = 1.0,
        source:   str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProjectFact:
        """Store a new fact about the project."""
        import uuid
        fact = ProjectFact(
            fact_id=str(uuid.uuid4())[:8],
            category=category,
            content=content[:500],
            confidence=confidence,
            source=source,
            metadata=metadata or {},
        )
        # Avoid exact duplicates
        existing = [f for f in self._facts if f.content == content]
        if not existing:
            self._facts.append(fact)
            self._save()
            logger.debug(f"ProjectMemory: remembered [{category}] {content[:60]}")
        return fact

    def update_from_task(self, task_id: str, outcome: str, files_changed: List[str]) -> None:
        """Update memory after a task completes."""
        if files_changed:
            self.remember(
                category="file",
                content=f"Task {task_id[:8]} ({outcome}) modified: {', '.join(files_changed[:5])}",
                source="task_executor",
            )

    def get_by_category(self, category: str) -> List[ProjectFact]:
        """Return all facts in a category."""
        return [f for f in self._facts if f.category == category]

    def get_all(self) -> List[ProjectFact]:
        return list(self._facts)

    def build_context_string(self, max_facts: int = 15) -> str:
        """Build a compact string suitable for injection into AI prompts."""
        if not self._facts:
            return ""
        selected = sorted(
            self._facts, key=lambda f: f.confidence, reverse=True
        )[:max_facts]
        lines = [f"Project memory for '{self._project_name}':"]
        for f in selected:
            lines.append(f"  [{f.category}] {f.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all stored facts."""
        self._facts.clear()
        self._save()
        logger.info("ProjectMemory cleared")

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._file.exists():
                data = json.loads(self._file.read_text(encoding="utf-8"))
                self._project_name = data.get("project_name", "")
                self._project_root = data.get("project_root", "")
                self._facts = [ProjectFact.from_dict(f) for f in data.get("facts", [])]
        except Exception as e:
            logger.warning(f"ProjectMemory: could not load from disk: {e}")
            self._facts = []

    def _save(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "project_name": self._project_name,
                "project_root": self._project_root,
                "facts": [f.to_dict() for f in self._facts[-300:]],
            }
            self._file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"ProjectMemory: could not save to disk: {e}")
