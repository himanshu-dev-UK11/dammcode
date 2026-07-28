"""
TaskAnalyzer — rule-based prompt intelligence.

Converts a raw user prompt into a fully populated Task object using
deterministic, keyword-based rules. No AI models are called here.

This is the first stage of the pipeline. By separating prompt
analysis from actual AI reasoning, we can cheaply pre-classify
tasks, assign priorities, and detect required tooling — making
the system faster and more predictable for simple tasks.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from core.logger import setup_logger
from ai.engine.task import Task, TaskComplexity, TaskPriority, TaskStatus

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Detection rule tables — extend these as the project grows.
# ---------------------------------------------------------------------------

_LANGUAGE_KEYWORDS: Dict[str, List[str]] = {
    "python":     ["python", ".py", "pip", "django", "flask", "fastapi"],
    "javascript": ["javascript", "js", "node", "npm", "react", "vue", "typescript", "ts"],
    "rust":       ["rust", "cargo", "crate"],
    "go":         ["golang", " go ", "goroutine"],
    "java":       ["java", "maven", "gradle", "spring"],
    "cpp":        ["c++", "cpp", "cmake"],
}

_FRAMEWORK_KEYWORDS: Dict[str, List[str]] = {
    "django":   ["django", "wsgi"],
    "flask":    ["flask", "blueprint"],
    "fastapi":  ["fastapi", "uvicorn", "pydantic"],
    "react":    ["react", "jsx", "tsx", "next.js", "nextjs"],
    "vue":      ["vue", "nuxt"],
    "express":  ["express", "middleware"],
    "pytorch":  ["pytorch", "torch", "tensor"],
    "sklearn":  ["sklearn", "scikit", "scikit-learn"],
}

_PROJECT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "web_app":    ["website", "web app", "frontend", "backend", "api", "rest"],
    "cli_tool":   ["cli", "command line", "terminal tool", "script"],
    "desktop_app":["desktop", "gui", "tkinter", "pyqt", "wxpython"],
    "ml_model":   ["machine learning", "train", "model", "dataset", "neural"],
    "data_pipeline": ["pipeline", "etl", "dataframe", "pandas", "spark"],
}

_TOOL_INDICATORS: Dict[str, List[str]] = {
    "terminal": ["run", "execute", "install", "compile", "build", "test", "command"],
    "file":     ["create file", "write file", "read file", "modify", "edit file", "delete file"],
    "git":      ["git", "commit", "branch", "push", "pull", "merge"],
    "browser":  ["search", "web", "internet", "google", "look up", "documentation"],
}

_COMPLEXITY_HIGH_INDICATORS: List[str] = [
    "architecture", "refactor", "entire", "whole project", "system",
    "multi", "complex", "integrate", "pipeline", "deploy", "migrate",
]

_PRIORITY_URGENT_INDICATORS: List[str] = [
    "urgent", "asap", "immediately", "critical", "broken", "crash", "error", "bug", "fix",
]

_PRIORITY_HIGH_INDICATORS: List[str] = [
    "important", "high priority", "must", "required", "blocker",
]


class TaskAnalyzer:
    """
    Rule-based prompt analyzer.

    Analyzes an incoming user prompt and produces a fully populated
    Task object with detected context and requirements.

    No AI models are invoked here. All decisions are deterministic
    and based on keyword matching.

    Usage:
        analyzer = TaskAnalyzer()
        task = analyzer.analyze("Build a Flask REST API with auth")
    """

    def __init__(self) -> None:
        logger.info("TaskAnalyzer initialized.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, prompt: str) -> Task:
        """
        Analyze a raw user prompt and return a Task object.

        Args:
            prompt: The exact text the user submitted.

        Returns:
            A Task instance populated with all detected context.
        """
        logger.info(f"Analyzing prompt: {prompt[:80]!r}...")

        task = Task(original_prompt=prompt)
        task.status = TaskStatus.ANALYZING

        normalized = prompt.lower()

        # Run all detectors in order
        task.detected_language    = self._detect_language(normalized)
        task.detected_framework   = self._detect_framework(normalized)
        task.detected_project_type = self._detect_project_type(normalized)
        task.required_tools       = self._detect_required_tools(normalized)
        task.needs_planning       = self._detect_needs_planning(normalized)
        task.needs_internet       = "browser" in task.required_tools
        task.needs_terminal       = "terminal" in task.required_tools
        task.needs_file_write     = "file" in task.required_tools
        task.estimated_complexity = self._estimate_complexity(normalized, task.required_tools)
        task.priority             = self._assign_priority(normalized)
        task.required_models      = self._select_required_models(task)
        task.title                = self._generate_title(prompt)
        task.objective            = prompt.strip()

        logger.info(
            f"Task analyzed — language={task.detected_language}, "
            f"complexity={task.estimated_complexity.value}, "
            f"priority={task.priority.value}, "
            f"tools={task.required_tools}"
        )
        return task

    # ------------------------------------------------------------------
    # Private detectors
    # ------------------------------------------------------------------

    def _detect_language(self, text: str) -> str | None:
        """Return the first matched programming language, or None."""
        for lang, keywords in _LANGUAGE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return lang
        return None

    def _detect_framework(self, text: str) -> str | None:
        """Return the first matched framework, or None."""
        for framework, keywords in _FRAMEWORK_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return framework
        return None

    def _detect_project_type(self, text: str) -> str | None:
        """Return the first matched project type, or None."""
        for ptype, keywords in _PROJECT_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return ptype
        return None

    def _detect_required_tools(self, text: str) -> List[str]:
        """Return a list of tool names that the prompt implies are needed."""
        needed: Set[str] = set()
        for tool, keywords in _TOOL_INDICATORS.items():
            if any(kw in text for kw in keywords):
                needed.add(tool)
        return sorted(needed)

    def _detect_needs_planning(self, text: str) -> bool:
        """
        Return True if the prompt implies multi-step planning is needed.

        Heuristics: multi-step words, large scope, or high complexity indicators.
        """
        planning_keywords = ["plan", "design", "architect", "step by step", "milestone"] + _COMPLEXITY_HIGH_INDICATORS
        return any(kw in text for kw in planning_keywords)

    def _estimate_complexity(self, text: str, required_tools: List[str]) -> TaskComplexity:
        """
        Estimate task complexity from keywords and tool count.

        Rules (evaluated top-down, first match wins):
        - EXPERT   → high-complexity keywords found
        - COMPLEX  → needs planning OR 3+ tools
        - MODERATE → 2 tools, or framework detected
        - SIMPLE   → default
        """
        if any(kw in text for kw in _COMPLEXITY_HIGH_INDICATORS):
            return TaskComplexity.EXPERT
        if self._detect_needs_planning(text) or len(required_tools) >= 3:
            return TaskComplexity.COMPLEX
        if len(required_tools) >= 2:
            return TaskComplexity.MODERATE
        return TaskComplexity.SIMPLE

    def _assign_priority(self, text: str) -> TaskPriority:
        """
        Assign priority based on urgency / importance keywords.

        Rules (evaluated top-down):
        - URGENT → crash / error / urgent words
        - HIGH   → importance words
        - MEDIUM → default
        """
        if any(kw in text for kw in _PRIORITY_URGENT_INDICATORS):
            return TaskPriority.URGENT
        if any(kw in text for kw in _PRIORITY_HIGH_INDICATORS):
            return TaskPriority.HIGH
        return TaskPriority.MEDIUM

    def _select_required_models(self, task: Task) -> List[str]:
        """
        Suggest model identifiers based on task complexity.

        TODO: Replace with intelligent model routing via ModelRouter.
        """
        if task.estimated_complexity in {TaskComplexity.EXPERT, TaskComplexity.COMPLEX}:
            return ["gemini"]
        return ["gemini"]  # Default for now; expand when more models are wired

    def _generate_title(self, prompt: str) -> str:
        """
        Create a short title from the first sentence of the prompt.
        Truncates at 60 characters.
        """
        first_sentence = re.split(r'[.\n]', prompt.strip())[0]
        title = first_sentence.strip()
        return title if len(title) <= 60 else title[:57] + "..."
