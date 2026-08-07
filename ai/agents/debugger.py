"""
DebuggerAgent — analyses errors and suggests fixes via the AI chat engine.
"""

from __future__ import annotations

from typing import Callable, Optional

from ai.agents.base_agent import BaseAgent


class DebuggerAgent(BaseAgent):
    """
    Agent responsible for analysing errors and proposing fixes.

    Relies on an injected AIChatEngine for actual LLM calls.
    """

    def __init__(self, event_bus, chat_engine=None) -> None:
        super().__init__("debugger", event_bus)
        self._engine = chat_engine

    # ── Public API ─────────────────────────────────────────────────────────

    def set_engine(self, engine) -> None:
        """Inject / replace the chat engine at runtime."""
        self._engine = engine

    def analyze_error(
        self,
        error_message: str,
        context: str = "",
        file_path: str = "",
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Analyse an error and suggest a fix.

        Args:
            error_message: The full error / traceback text.
            context:       Surrounding source code where the error occurred.
            file_path:     Path of the file that triggered the error.
            on_chunk:      Optional streaming callback per token.
            on_complete:   Optional callback when analysis finishes.

        Returns:
            The analysis and fix suggestion as a string.
        """
        self.logger.info(f"DebuggerAgent.analyze_error: {error_message[:80]}")

        if not self._engine:
            msg = (
                "DebuggerAgent: no chat engine available. "
                "Connect a provider in Settings → AI Providers."
            )
            self.logger.warning(msg)
            if on_complete:
                on_complete(msg)
            return msg

        prompt = self._build_prompt(error_message, context, file_path)

        result: list[str] = []

        def _on_done(response: str) -> None:
            result.append(response)
            if on_complete:
                on_complete(response)

        try:
            self._engine.send_message(
                message=prompt,
                model_id=self._engine.get_current_model(),
                on_chunk=on_chunk,
                on_complete=_on_done,
            )
        except Exception as exc:
            self.handle_error(exc)
            if on_complete:
                on_complete(f"Error: {exc}")
            return ""

        return result[0] if result else ""

    def suggest_fix(
        self,
        code: str,
        error: str,
        language: str = "",
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Return a corrected version of the code that resolves the error."""
        prompt = (
            f"The following {language} code produces this error:\n"
            f"```\n{error}\n```\n\n"
            f"Code:\n```{language}\n{code}\n```\n\n"
            "Return the corrected code only, with a one-line comment explaining the fix."
        )
        result: list[str] = []
        self.analyze_error(
            error_message=prompt,
            on_chunk=on_chunk,
            on_complete=lambda r: result.append(r),
        )
        return result[0] if result else ""

    # ── Helpers ────────────────────────────────────────────────────────────

    def _build_prompt(self, error: str, context: str, file_path: str) -> str:
        parts = [
            "You are an expert debugger. Analyse the following error and explain:\n"
            "1. What caused it\n"
            "2. How to fix it\n"
            "3. The corrected code snippet (if applicable)\n\n"
        ]
        if file_path:
            parts.append(f"File: {file_path}\n\n")
        parts.append(f"Error:\n```\n{error}\n```")
        if context:
            parts.append(f"\n\nRelevant code:\n```\n{context}\n```")
        return "".join(parts)
