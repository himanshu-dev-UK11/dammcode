"""
WorkflowPipeline — the heart of MyCodingMaster.

This module wires every component of the system into a single,
linear processing pipeline. When a user submits a prompt, this
class is the entry point that orchestrates the entire journey
from raw text to final UI response.

Pipeline (v0.5):

    User Prompt
        ↓
    TaskAnalyzer       — rule-based: classify, detect, prioritize
        ↓
    PlannerAgent       — AI: break task into ordered steps
        ↓
    ContextEngine      — build optimized file + symbol context  [NEW v0.5]
        ↓
    ModelRouter        — select the best model for each step
        ↓
    ToolManager        — gatekeep all tool access
        ↓
    ExecutionManager   — run each step, retry failures
        ↓
    Memory Update      — persist context and decisions
        ↓
    UI Response        — publish final result to EventBus → UI

Note: AI calls inside PlannerAgent and ModelRouter are currently
stub implementations. The pipeline structure and all
inter-component contracts are fully in place.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from core.event_bus import EventBus
from ai.engine.task import Task, TaskStatus
from ai.engine.task_analyzer import TaskAnalyzer
from ai.engine.tool_manager import ToolManager
from ai.engine.execution_manager import ExecutionManager
from ai.agents.planner import PlannerAgent
from ai.models.router import ModelRouter
from ai.memory.decision_memory import DecisionMemory
from ai.memory.project_memory import ProjectMemory
from ai.context.context_engine import ContextEngine, ContextPackage
from ai.editing.change_applier import ChangeApplier
from ai.editing.diff_generator import DiffGenerator
from ai.editing.patch_validator import PatchValidator
from ai.editing.rollback_manager import RollbackManager
from ai.editing.file_lock_manager import FileLockManager
from ai.editing.edit_history import EditHistory
from ai.verification.verification_engine import VerificationEngine
from ai.verification.success_validator import SuccessValidator
from ai.verification.retry_manager import RetryManager

logger = setup_logger(__name__)


class WorkflowPipeline:
    """
    Central orchestrator for processing user prompts end-to-end.

    Holds references to every major system component and
    coordinates them in the correct sequence. No AI reasoning
    lives in this class — it only calls the right component
    at the right time and passes data between them.

    Args:
        event_bus:        The application-wide EventBus instance.
        tool_manager:     Pre-configured ToolManager with registered tools.
        decision_memory:  Shared decision context store.
        project_memory:   Shared project knowledge store.
        max_retries:      Step retry limit forwarded to ExecutionManager.

    Usage:
        pipeline = WorkflowPipeline(event_bus=bus, tool_manager=tm)
        result   = pipeline.process_prompt("Add logging to every agent")
    """

    def __init__(
        self,
        event_bus: EventBus,
        tool_manager: ToolManager,
        decision_memory: Optional[DecisionMemory] = None,
        project_memory: Optional[ProjectMemory] = None,
        max_retries: int = 2,
        project_root: Optional[str] = None,
    ) -> None:
        self.event_bus    = event_bus
        self.tool_manager = tool_manager

        # Core pipeline components
        self.task_analyzer     = TaskAnalyzer()
        self.planner           = PlannerAgent(event_bus)
        self.model_router      = ModelRouter()
        self.execution_manager = ExecutionManager(event_bus, tool_manager, max_retries)

        # Memory systems (use defaults if not provided)
        self.decision_memory = decision_memory or DecisionMemory()
        self.project_memory  = project_memory  or ProjectMemory()

        # Context Engine (v0.5) — sits between Planner and Model Manager
        self._project_root = project_root
        if project_root:
            self.context_engine: Optional[ContextEngine] = ContextEngine(
                event_bus=event_bus,
                project_root=project_root,
            )
            # Safe Code Editing System (v0.6)
            self.change_applier = ChangeApplier(event_bus, project_root)
            self.diff_generator = DiffGenerator()
            self.patch_validator = PatchValidator()
            self.rollback_manager = RollbackManager(project_root)
            self.file_lock_manager = FileLockManager()
            self.edit_history = EditHistory(project_root)
            # Verification Engine (v0.7)
            self.verification_engine = VerificationEngine(event_bus, project_root)
            self.success_validator = SuccessValidator()
            self.retry_manager = RetryManager()
        else:
            self.context_engine = None
            self.change_applier = None
            self.diff_generator = None
            self.patch_validator = None
            self.rollback_manager = None
            self.file_lock_manager = None
            self.edit_history = None
            self.verification_engine = None
            self.success_validator = None
            self.retry_manager = None

        logger.info("WorkflowPipeline initialized — all components ready (v0.5).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Run a raw user prompt through the full pipeline.

        This is the single public entry point for processing any
        user request. It runs each stage in sequence, gates on
        failures, and always returns a structured result dict.

        Args:
            prompt: The raw text submitted by the user.

        Returns:
            A result dict with the following keys:
              - "success"  (bool)
              - "task"     (Task)
              - "output"   (str | None)   — final response text
              - "error"    (str | None)   — error message if failed

        Pipeline stages:
            1. ANALYZE  → TaskAnalyzer.analyze()
            2. PLAN     → PlannerAgent.create_plan()
            3. ROUTE    → ModelRouter.select_model()
            4. EXECUTE  → ExecutionManager.execute_plan()
            5. MEMORIZE → memory systems update
            6. RESPOND  → publish to UI via EventBus
        """
        logger.info(f"WorkflowPipeline: processing new prompt ({len(prompt)} chars).")
        self._publish("pipeline_started", {"prompt_preview": prompt[:80]})

        # ── Stage 1: Analyze ──────────────────────────────────────────
        task = self._stage_analyze(prompt)
        if task is None:
            return self._failure_result(None, "Task analysis failed unexpectedly.")

        # ── Stage 2: Plan ─────────────────────────────────────────────
        plan = self._stage_plan(task)
        if plan is None:
            return self._failure_result(task, "Planning stage failed.")
        task.plan = plan

        # ── Stage 2.5: Context Engine (v0.5) ──────────────────────────
        context_package = self._stage_build_context(task, prompt)
        # Attach to task metadata for downstream stages
        task.metadata["context_package"] = context_package

        # ── Stage 3: Route model ──────────────────────────────────────
        selected_model = self._stage_route(task)
        # Model selection is advisory; pipeline continues even if routing is a stub

        # ── Stage 4: Execute ──────────────────────────────────────────
        step_results = self._stage_execute(task)
        if task.status == TaskStatus.FAILED:
            self._publish("pipeline_failed", {"task_id": task.id})
            return self._failure_result(task, f"Execution failed at a plan step.")

        # ── Stage 5: Memorize ─────────────────────────────────────────
        self._stage_memorize(task, step_results)

        # ── Stage 6: Respond ──────────────────────────────────────────
        output = self._stage_respond(task, step_results)

        logger.info(f"WorkflowPipeline: task {task.id[:8]} completed successfully.")
        return {"success": True, "task": task, "output": output, "error": None}

    # ------------------------------------------------------------------
    # Pipeline stages (private)
    # ------------------------------------------------------------------

    def _stage_analyze(self, prompt: str) -> Optional[Task]:
        """
        Stage 1 — TaskAnalyzer.

        Converts the raw prompt into a Task object with
        detected language, complexity, required tools, etc.
        """
        logger.info("Pipeline Stage 1: Analyzing prompt...")
        self._publish("stage_started", {"stage": "analyze"})
        try:
            task = self.task_analyzer.analyze(prompt)
            self._publish("stage_completed", {"stage": "analyze", "task_id": task.id})
            return task
        except Exception as exc:
            logger.error(f"Stage 1 (analyze) failed: {exc}", exc_info=True)
            return None

    def _stage_plan(self, task: Task) -> Optional[list]:
        """
        Stage 2 — PlannerAgent.

        Breaks the task objective into an ordered list of steps.

        TODO: PlannerAgent.create_plan() currently returns a stub list.
              Wire actual AI model calls once models are integrated.
        """
        logger.info("Pipeline Stage 2: Planning...")
        self._publish("stage_started", {"stage": "plan", "task_id": task.id})
        task.status = TaskStatus.PLANNING
        try:
            plan = self.planner.create_plan(task.objective)
            if not plan:
                # Fallback: single-step plan for simple tasks
                plan = [f"Complete task: {task.objective}"]
            self._publish("stage_completed", {"stage": "plan", "task_id": task.id, "steps": len(plan)})
            return plan
        except Exception as exc:
            logger.error(f"Stage 2 (plan) failed: {exc}", exc_info=True)
            task.mark_failed()
            return None

    def _stage_build_context(
        self,
        task: Task,
        prompt: str,
        current_file: Optional[str] = None,
        open_tabs: Optional[List[str]] = None,
    ) -> Optional[ContextPackage]:
        """
        Stage 2.5 — Context Engine (v0.5).

        Builds an optimized ContextPackage from the project files.
        This stage is non-blocking: if the engine is not available
        (e.g., no project root), the pipeline continues with None.
        """
        if self.context_engine is None:
            logger.debug("Pipeline Stage 2.5: Context Engine not configured — skipping.")
            return None

        logger.info("Pipeline Stage 2.5: Building context package...")
        self._publish("stage_started", {"stage": "context", "task_id": task.id})
        try:
            package = self.context_engine.build(
                prompt=prompt,
                current_file=current_file,
                open_tabs=open_tabs,
            )
            self._publish("stage_completed", {
                "stage":         "context",
                "task_id":       task.id,
                "files_selected": len(package.selected_files),
                "token_estimate": package.token_estimate,
                "cache_hit":      package.cache_hit,
            })
            logger.info(
                f"Pipeline Stage 2.5 complete: "
                f"{len(package.selected_files)} files, "
                f"~{package.token_estimate:,} tokens, "
                f"cache={'HIT' if package.cache_hit else 'MISS'}."
            )
            return package
        except Exception as exc:
            logger.warning(f"Stage 2.5 (context) failed non-critically: {exc}")
            return None  # Non-blocking — pipeline continues without context

    def _stage_route(self, task: Task) -> Optional[str]:
        """
        Stage 3 — ModelRouter.

        Selects the most appropriate model for this task type.

        TODO: ModelRouter.select_model() is currently a stub.
              Implement real routing logic based on task complexity and cost.
        """
        logger.info("Pipeline Stage 3: Routing to model...")
        self._publish("stage_started", {"stage": "route", "task_id": task.id})
        try:
            model = self.model_router.select_model(task.estimated_complexity.value)
            logger.info(f"Model routed: {model!r}")
            self._publish("stage_completed", {"stage": "route", "model": str(model)})
            return model
        except Exception as exc:
            logger.warning(f"Stage 3 (route) failed non-critically: {exc}")
            return None  # Non-blocking; execution proceeds with defaults

    def _stage_execute(self, task: Task) -> list:
        """
        Stage 4 — ExecutionManager.

        Runs each step of the plan through the ToolManager,
        with retry logic and progress events.
        """
        logger.info("Pipeline Stage 4: Executing plan...")
        self._publish("stage_started", {"stage": "execute", "task_id": task.id})
        step_results = self.execution_manager.execute_plan(task, task.plan)
        self._publish("stage_completed", {"stage": "execute", "task_id": task.id})
        return step_results

    def _stage_memorize(self, task: Task, step_results: list) -> None:
        """
        Stage 5 — Memory Update.

        Persists the task outcome to both memory systems so
        future tasks can benefit from the decision history.

        TODO: Implement actual serialization and retrieval in
              DecisionMemory and ProjectMemory.
        """
        logger.info("Pipeline Stage 5: Updating memory...")
        self._publish("stage_started", {"stage": "memorize", "task_id": task.id})
        try:
            # TODO: self.decision_memory.store(task)
            # TODO: self.project_memory.update_from_task(task)
            logger.debug("Memory update stubbed — no persistence yet.")
        except Exception as exc:
            logger.warning(f"Stage 5 (memorize) failed non-critically: {exc}")
        self._publish("stage_completed", {"stage": "memorize", "task_id": task.id})

    def _stage_respond(self, task: Task, step_results: list) -> str:
        """
        Stage 6 — UI Response.

        Assembles the final response string and publishes it to
        the EventBus so the ChatPanel can display it.

        TODO: Replace stub with actual model-generated response summary.
        """
        logger.info("Pipeline Stage 6: Publishing UI response...")
        self._publish("stage_started", {"stage": "respond", "task_id": task.id})

        # TODO: Generate a natural-language summary via model call.
        output = (
            f"Task '{task.title}' completed successfully.\n"
            f"Steps executed: {len(step_results)}."
        )

        self._publish(
            "pipeline_response",
            {"task_id": task.id, "response": output},
        )
        self._publish("stage_completed", {"stage": "respond", "task_id": task.id})
        return output

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Safely publish an event to the EventBus."""
        try:
            self.event_bus.publish(event_type, data)
        except Exception as exc:
            logger.error(f"Failed to publish event '{event_type}': {exc}")

    @staticmethod
    def _failure_result(task: Optional[Task], error: str) -> Dict[str, Any]:
        """Return a standardized failure result dict."""
        return {"success": False, "task": task, "output": None, "error": error}
