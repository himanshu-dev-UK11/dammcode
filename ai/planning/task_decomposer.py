"""
TaskDecomposer — intelligent task decomposition.

Converts a Task into a list of actionable EngineeringTasks.
Adapts the number and type of steps to task complexity.
"""

from typing import List, Optional
import uuid
from core.logger import setup_logger
from ai.engine.task import Task, TaskComplexity
from ai.engine.engineering_task import EngineeringTask
from ai.engine.task import TaskPriority as EngineeringTaskPriority  # alias

logger = setup_logger(__name__)


class TaskDecomposer:
    """
    Breaks down a high-level Task into actionable EngineeringTasks.

    Decomposition strategy:
    - SIMPLE    → 1 step: direct execution
    - MODERATE  → 2 steps: analyse + implement
    - COMPLEX   → 3 steps: analyse + implement + verify
    - EXPERT    → 4 steps: analyse + plan + implement + verify
    """

    def decompose(self, task: Task, context=None) -> List[EngineeringTask]:
        """
        Convert task into an ordered list of EngineeringTasks.

        Args:
            task:    The analyzed Task object from TaskAnalyzer.
            context: Optional ContextPackage (may be None early in pipeline).

        Returns:
            Ordered list of EngineeringTasks with dependency chains set.
        """
        complexity = getattr(task, "estimated_complexity", TaskComplexity.SIMPLE)
        prompt     = getattr(task, "original_prompt", "Complete task")
        objective  = getattr(task, "objective", prompt) or prompt
        lang       = getattr(task, "detected_language", None)
        tools      = getattr(task, "required_tools", [])

        logger.info(
            f"TaskDecomposer: decomposing '{objective[:60]}' "
            f"(complexity={complexity.value})"
        )

        steps: List[EngineeringTask] = []

        # ── SIMPLE: one direct execution step ────────────────────────────
        if complexity == TaskComplexity.SIMPLE:
            step = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Execute task",
                description=objective,
                estimated_duration=30,
                priority=EngineeringTaskPriority.MEDIUM,
            )
            steps.append(step)

        # ── MODERATE: analyse + implement ───────────────────────────────
        elif complexity == TaskComplexity.MODERATE:
            s1 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Analyse context",
                description=(
                    f"Read relevant files{' (' + lang + ')' if lang else ''} "
                    "and understand the current state."
                ),
                estimated_duration=20,
                priority=EngineeringTaskPriority.HIGH,
            )
            s2 = EngineeringTask(
                id=str(uuid.uuid4()),
                title=f"Implement: {objective[:50]}",
                description=objective,
                dependencies=[s1.id],
                estimated_duration=90,
                priority=EngineeringTaskPriority.HIGH,
            )
            steps.extend([s1, s2])

        # ── COMPLEX: analyse + implement + verify ────────────────────────
        elif complexity == TaskComplexity.COMPLEX:
            s1 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Analyse project and gather context",
                description=(
                    "Locate entry points, config files, and relevant modules. "
                    f"Tools needed: {', '.join(tools) or 'none'}."
                ),
                estimated_duration=25,
                priority=EngineeringTaskPriority.HIGH,
            )
            s2 = EngineeringTask(
                id=str(uuid.uuid4()),
                title=f"Implement: {objective[:50]}",
                description=(
                    f"{objective}\n\nApply changes to the identified files, "
                    "following the project's existing patterns."
                ),
                dependencies=[s1.id],
                estimated_duration=120,
                priority=EngineeringTaskPriority.HIGH,
            )
            s3 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Verify and validate changes",
                description=(
                    "Run linters and tests on modified files. "
                    "Confirm changes are consistent and correct."
                ),
                dependencies=[s2.id],
                estimated_duration=40,
                priority=EngineeringTaskPriority.MEDIUM,
            )
            steps.extend([s1, s2, s3])

        # ── EXPERT: analyse + plan + implement + verify ──────────────────
        else:
            s1 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Deep project analysis",
                description=(
                    "Scan project architecture, dependencies, and identify all "
                    "affected components for this change."
                ),
                estimated_duration=30,
                priority=EngineeringTaskPriority.URGENT,
            )
            s2 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Plan implementation strategy",
                description=(
                    f"Design the approach for: {objective[:80]}. "
                    "Break down into safe, reversible sub-changes."
                ),
                dependencies=[s1.id],
                estimated_duration=30,
                priority=EngineeringTaskPriority.URGENT,
            )
            s3 = EngineeringTask(
                id=str(uuid.uuid4()),
                title=f"Implement: {objective[:50]}",
                description=(
                    f"{objective}\n\nFollow the plan from step 2. "
                    "Make atomic, focused changes per file."
                ),
                dependencies=[s2.id],
                estimated_duration=180,
                priority=EngineeringTaskPriority.HIGH,
            )
            s4 = EngineeringTask(
                id=str(uuid.uuid4()),
                title="Verify, test, and generate diff",
                description=(
                    "Run full verification suite. Generate a diff summary "
                    "of all changes for user review."
                ),
                dependencies=[s3.id],
                estimated_duration=60,
                priority=EngineeringTaskPriority.HIGH,
            )
            steps.extend([s1, s2, s3, s4])

        logger.info(
            f"TaskDecomposer: produced {len(steps)} steps "
            f"for complexity={complexity.value}"
        )
        return steps
