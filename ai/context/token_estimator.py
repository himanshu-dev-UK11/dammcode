"""
token_estimator.py — Token budget management.

Estimates how many LLM tokens a given piece of text or an entire
ContextPackage will require, enforces model limits, and suggests
which files to drop when the budget is exceeded.

The estimator uses a characters-per-token heuristic (default 4) which
is accurate enough for budget planning without requiring a real tokenizer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple

from core.logger import setup_logger

if TYPE_CHECKING:
    from ai.context.context_engine import ContextPackage

logger = setup_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────
DEFAULT_CHARS_PER_TOKEN: int = 4
DEFAULT_MODEL_LIMIT:     int = 128_000   # Conservative default (128 K tokens)
PROMPT_OVERHEAD_TOKENS:  int = 512       # System prompt + formatting overhead


@dataclass
class BudgetReport:
    """Result of a budget check against a specific model limit."""
    total_tokens:   int
    model_limit:    int
    fits:           bool
    excess_tokens:  int          # 0 when fits=True
    utilisation_pct: float       # 0-100


class TokenEstimator:
    """
    Lightweight token estimator using character count heuristics.

    Args:
        chars_per_token: Average characters per token for the target
                         tokenizer family (GPT/Gemini ≈ 4, LLaMA ≈ 3.5).
    """

    def __init__(self, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> None:
        self._cpt = chars_per_token
        logger.debug(f"TokenEstimator initialised (chars_per_token={chars_per_token}).")

    # ── Core estimates ─────────────────────────────────────────────────────

    def estimate(self, text: str) -> int:
        """Return estimated token count for an arbitrary string."""
        if not text:
            return 0
        return math.ceil(len(text) / self._cpt)

    def estimate_file(self, path: str, content: str) -> int:
        """Estimate tokens for a single file (path header + content)."""
        header = f"# File: {path}\n"
        return self.estimate(header + content)

    def estimate_package(self, package: "ContextPackage") -> int:
        """
        Estimate total tokens for an entire ContextPackage.

        Accounts for:
          - The user prompt
          - All selected file contents
          - Symbol summaries
          - Formatting overhead
        """
        total = PROMPT_OVERHEAD_TOKENS
        total += self.estimate(package.prompt)

        for sf in package.selected_files:
            total += self.estimate_file(sf.path, sf.content)

        # Symbol summaries are terse; count only their names
        if package.symbols:
            symbol_text = "\n".join(
                f"{s.kind} {s.name} @ {s.file}:{s.line}"
                for s in package.symbols
            )
            total += self.estimate(symbol_text)

        return total

    # ── Budget enforcement ─────────────────────────────────────────────────

    def check_budget(
        self,
        package: "ContextPackage",
        model_limit: int = DEFAULT_MODEL_LIMIT,
    ) -> BudgetReport:
        """
        Check whether a ContextPackage fits within the model's token limit.

        Returns a BudgetReport describing utilisation and any excess.
        """
        total = self.estimate_package(package)
        fits  = total <= model_limit
        excess = max(0, total - model_limit)
        utilisation = round(total / model_limit * 100, 1) if model_limit else 0.0

        logger.debug(
            f"Budget check: {total} / {model_limit} tokens "
            f"({utilisation}%) — {'OK' if fits else 'EXCEEDS'}"
        )
        return BudgetReport(
            total_tokens=total,
            model_limit=model_limit,
            fits=fits,
            excess_tokens=excess,
            utilisation_pct=utilisation,
        )

    def suggest_reduction(
        self,
        package: "ContextPackage",
        model_limit: int = DEFAULT_MODEL_LIMIT,
    ) -> List[str]:
        """
        Suggest which files to remove when the package exceeds the budget.

        Strategy: drop lowest-scored files first until budget is satisfied.
        Returns a list of file paths that should be excluded.
        """
        report = self.check_budget(package, model_limit)
        if report.fits:
            return []

        # Sort by score ascending (drop cheapest-value files first)
        sorted_files = sorted(package.selected_files, key=lambda f: f.score)
        to_drop: List[str] = []
        saved_tokens = 0
        needed = report.excess_tokens

        for sf in sorted_files:
            if saved_tokens >= needed:
                break
            file_tokens = self.estimate_file(sf.path, sf.content)
            to_drop.append(sf.path)
            saved_tokens += file_tokens
            logger.debug(f"Suggest dropping '{sf.path}' (−{file_tokens} tokens).")

        return to_drop
