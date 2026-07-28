"""
CoderAgent — generates and modifies code via the AI chat engine.

Routes coding requests through the active AIChatEngine using the best
available local model, streams the response, and returns the result.
"""

from __future__ import annotations

from typing import Callable, Optional

from ai.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """
    Agent responsible for code generation and modification.

    Relies on an injected AIChatEngine for actual LLM calls.
    Can be used standalone or wired into the EngineeringWorkflowCoordinator.
    """

    def __init__(self, event_bus, chat_engine=None) -> None:
        super().__init__("coder", event_bus)
        self._engine = chat_engine   # AIChatEngine, injected at runtime

    # ── Public API ─────────────────────────────────────────────────────────

    def set_engine(self, engine) -> None:
        """Inject / replace the chat engine at runtime."""
        self._engine = engine

    def implement_task(
        self,
        task_description: str,
        context: str = "",
        language: str = "",
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Generate code or a code modification for the given task description.

        Args:
            task_description: What the code should do.
            context:          Optional surrounding code / project context.
            language:         Target programming language hint (e.g. "python").
            on_chunk:         Optional streaming callback per token.
            on_complete:      Optional callback when generation finishes.

        Returns:
            The generated code as a string (may be empty if streaming only).
        """
        self.logger.info(f"CoderAgent.implement_task: {task_description[:80]}")

        if not self._engine:
            msg = (
                "CoderAgent: no chat engine available. "
                "Connect a provider in Settings → AI Providers."
            )
            self.logger.warning(msg)
            if on_complete:
                on_complete(msg)
            return msg

        prompt = self._build_prompt(task_description, context, language)

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

    def refactor(
        self,
        code: str,
        instruction: str,
        language: str = "",
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Refactor existing code per the instruction."""
        task = (
            f"Refactor the following code: {instruction}\n\n"
            f"```{language}\n{code}\n```"
        )
        return self.implement_task(
            task, language=language, on_chunk=on_chunk, on_complete=on_complete
        )

    def explain(self, code: str, language: str = "") -> str:
        """Explain what a piece of code does (blocking call)."""
        task = f"Explain the following code clearly and concisely:\n\n```{language}\n{code}\n```"
        result: list[str] = []
        self.implement_task(task, language=language, on_complete=lambda r: result.append(r))
        return result[0] if result else ""

    # ── Helpers ────────────────────────────────────────────────────────────

    def _build_prompt(self, task: str, context: str, language: str) -> str:
        parts = ["You are an expert software engineer. "]
        if language:
            parts.append(f"Write in {language}. ")
        parts.append("\n\nTask:\n" + task)
        if context:
            parts.append(f"\n\nContext / existing code:\n```\n{context}\n```")
        parts.append(
            "\n\nRespond with complete, working code only. "
            "Add brief inline comments where helpful."
        )
        return "".join(parts)
