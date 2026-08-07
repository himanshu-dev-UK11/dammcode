"""
DecisionMemory — persists AI decisions across sessions.

Stores every significant decision made during task execution so the AI
can reference past choices, avoid repeating mistakes, and explain its
reasoning to the user.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import setup_logger

logger = setup_logger(__name__)

_STORAGE_FILE = Path("config/decision_memory.json")


@dataclass
class Decision:
    """A single recorded AI decision."""
    decision_id:  str
    task_id:      str
    prompt:       str
    choice:       str          # what the AI chose to do
    reasoning:    str          # why it made that choice
    outcome:      str = ""     # "success" | "failure" | "unknown"
    model_used:   str = ""
    timestamp:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata:     Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Decision":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class DecisionMemory:
    """
    In-memory + disk-backed store of AI decisions.

    Usage:
        memory = DecisionMemory()
        memory.record(task_id="abc", prompt="...", choice="...", reasoning="...")
        recent = memory.get_recent(limit=10)
    """

    def __init__(self, storage_file: Optional[str] = None) -> None:
        self._file = Path(storage_file) if storage_file else _STORAGE_FILE
        self._decisions: List[Decision] = []
        self._load()
        logger.info(f"DecisionMemory initialized ({len(self._decisions)} past decisions)")

    # ── Public API ─────────────────────────────────────────────────────────

    def record(
        self,
        task_id:   str,
        prompt:    str,
        choice:    str,
        reasoning: str,
        outcome:   str = "unknown",
        model_used: str = "",
        metadata:  Optional[Dict[str, Any]] = None,
    ) -> Decision:
        """Record a new decision and persist to disk."""
        import uuid
        decision = Decision(
            decision_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            prompt=prompt[:200],
            choice=choice[:500],
            reasoning=reasoning[:1000],
            outcome=outcome,
            model_used=model_used,
            metadata=metadata or {},
        )
        self._decisions.append(decision)
        self._save()
        logger.debug(f"Decision recorded: {decision.decision_id} (task={task_id[:8]})")
        return decision

    def update_outcome(self, decision_id: str, outcome: str) -> bool:
        """Update the outcome of a previously recorded decision."""
        for d in self._decisions:
            if d.decision_id == decision_id:
                d.outcome = outcome
                self._save()
                return True
        return False

    def get_recent(self, limit: int = 20) -> List[Decision]:
        """Return the most recent N decisions."""
        return list(reversed(self._decisions))[:limit]

    def get_for_task(self, task_id: str) -> List[Decision]:
        """Return all decisions for a specific task."""
        return [d for d in self._decisions if d.task_id == task_id]

    def get_failures(self) -> List[Decision]:
        """Return all decisions that resulted in failure."""
        return [d for d in self._decisions if d.outcome == "failure"]

    def summary_for_prompt(self, limit: int = 5) -> str:
        """Return a compact summary for injection into AI prompts."""
        recent = self.get_recent(limit)
        if not recent:
            return "No past decisions recorded."
        lines = ["Recent decisions:"]
        for d in recent:
            lines.append(
                f"  [{d.timestamp[:10]}] {d.choice[:80]} "
                f"(outcome={d.outcome})"
            )
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all decisions (e.g. on new project open)."""
        self._decisions.clear()
        self._save()
        logger.info("DecisionMemory cleared")

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._file.exists():
                data = json.loads(self._file.read_text(encoding="utf-8"))
                self._decisions = [Decision.from_dict(d) for d in data.get("decisions", [])]
        except Exception as e:
            logger.warning(f"DecisionMemory: could not load from disk: {e}")
            self._decisions = []

    def _save(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            payload = {"decisions": [d.to_dict() for d in self._decisions[-500:]]}
            self._file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"DecisionMemory: could not save to disk: {e}")
