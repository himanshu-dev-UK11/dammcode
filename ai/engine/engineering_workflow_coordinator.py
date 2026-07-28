"""
EngineeringWorkflowCoordinator — Version 1.8.7
Coordinates the end-to-end AI software engineering workflow, connecting:
Project Intelligence -> Context Engine -> Model Router -> AI Engine -> Editing/Verification.
Executes asynchronously on a worker thread to keep the UI unblocked.
"""

import threading
from typing import Dict, Any, Optional

from core.logger import setup_logger
from core.event_bus import EventBus
from ai.intelligence.project_analyzer import ProjectAnalyzer
from ai.context.context_engine import ContextEngine
from ai.models.router import ModelRouter, TaskType
from ai.chat.ai_chat_engine import AIChatEngine
from ai.editing.change_applier import ChangeApplier
from ai.verification.verification_engine import VerificationEngine
from ai.memory.project_memory import ProjectMemory
from ai.memory.decision_memory import DecisionMemory
from ai.engine.task_analyzer import TaskAnalyzer
from ai.planning.task_decomposer import TaskDecomposer
from ai.execution.execution_engine import ExecutionEngine

logger = setup_logger(__name__)


class EngineeringWorkflowCoordinator:
    """
    Orchestrates the entire AI engineering pipeline:
    1. Task Analysis
    2. Project Intelligence (architecture, health)
    3. Context Assembly
    4. Model Selection
    5. Execution Plan / Generation
    6. Verification & Patch Proposal
    7. Memory Update
    """

    def __init__(
        self,
        event_bus: EventBus,
        project_analyzer: Optional[ProjectAnalyzer] = None,
        context_engine: Optional[ContextEngine] = None,
        model_router: Optional[ModelRouter] = None,
        chat_engine: Optional[AIChatEngine] = None,
        patch_engine: Optional[ChangeApplier] = None,
        verification_engine: Optional[VerificationEngine] = None,
        project_memory: Optional[ProjectMemory] = None,
        decision_memory: Optional[DecisionMemory] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        self.event_bus = event_bus
        self.project_analyzer = project_analyzer
        self.context_engine = context_engine
        self.model_router = model_router
        self.chat_engine = chat_engine
        self.patch_engine = patch_engine
        self.verification_engine = verification_engine
        self.project_memory = project_memory or ProjectMemory()
        self.decision_memory = decision_memory or DecisionMemory()
        self.execution_engine = execution_engine
        
        self.task_analyzer = TaskAnalyzer()
        self.task_decomposer = TaskDecomposer()

        # Subscribe to AI requests
        self.event_bus.subscribe("user_ai_request", self._on_user_request)
        
        # Subscribe to user workflow controls (v1.8.8)
        self.event_bus.subscribe("workflow_action_pause", self._on_pause_request)
        self.event_bus.subscribe("workflow_action_resume", self._on_resume_request)
        self.event_bus.subscribe("workflow_action_cancel", self._on_cancel_request)
        
        logger.info("EngineeringWorkflowCoordinator initialized.")

    def _on_user_request(self, payload: Dict[str, Any]):
        """Triggered by the UI when a user submits a prompt."""
        prompt = payload.get("prompt", "")
        current_file = payload.get("current_file")
        open_tabs = payload.get("open_tabs", [])
        
        if not prompt:
            return

        # Start background workflow
        thread = threading.Thread(
            target=self._run_workflow,
            args=(prompt, current_file, open_tabs),
            daemon=True
        )
        thread.start()

    def _run_workflow(self, prompt: str, current_file: Optional[str], open_tabs: list):
        """Executes the pipeline sequentially in a background thread."""
        logger.info("Engineering Workflow Started.")
        self.event_bus.publish("workflow_started", {"prompt": prompt})

        # --- PHASE 1: Task Analysis ---
        self.event_bus.publish("workflow_stage_changed", {"stage": "Task Analysis"})
        task = self.task_analyzer.analyze(prompt)

        # --- PHASE 2: Project Intelligence ---
        self.event_bus.publish("workflow_stage_changed", {"stage": "Project Intelligence"})
        if self.project_analyzer and hasattr(self.project_analyzer, "analyze"):
            try:
                self.project_analyzer.analyze()
            except Exception as e:
                logger.warning(f"ProjectAnalyzer error: {e}")

        # --- PHASE 3: Context Assembly ---
        self.event_bus.publish("workflow_stage_changed", {"stage": "Context Assembly"})
        context_package = None
        if self.context_engine:
            try:
                context_package = self.context_engine.build(
                    prompt=prompt,
                    current_file=current_file,
                    open_tabs=open_tabs or [],
                )
                self.event_bus.publish("workflow_context_ready", {
                    "token_estimate": context_package.token_estimate,
                    "files_included": len(context_package.selected_files),
                })
                logger.info(
                    f"Context built: {len(context_package.selected_files)} files, "
                    f"~{context_package.token_estimate} tokens"
                )
            except Exception as e:
                logger.warning(f"Context Engine failed: {e}")
        else:
            logger.info("Context Engine not available — skipping context assembly")

        # --- PHASE 4: Model Selection ---
        self.event_bus.publish("workflow_stage_changed", {"stage": "Model Selection"})
        best_model = None
        if self.model_router:
            try:
                task_type = TaskType.CODING if task.requires_code_changes else TaskType.SIMPLE_CHAT
                best_model = self.model_router.select_best_model(task_type=task_type)
                if best_model:
                    # best_model is a string model ID
                    self.event_bus.publish("workflow_model_selected", {"model": best_model})
                    logger.info(f"Model selected: {best_model}")
                else:
                    self.event_bus.publish("workflow_model_selected", {"model": "automatic"})
            except Exception as e:
                logger.warning(f"Model selection failed: {e}")

        # --- PHASE 5: Decomposition & Execution ---
        self.event_bus.publish("workflow_stage_changed", {"stage": "Decomposition & Execution"})
        try:
            engineering_tasks = self.task_decomposer.decompose(task, context_package)
            logger.info(f"Decomposed into {len(engineering_tasks)} engineering tasks")
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            self.event_bus.publish("workflow_failed", {"error": f"Decomposition failed: {e}"})
            return

        if self.execution_engine:
            try:
                self.execution_engine.submit_engineering_tasks(engineering_tasks)
                self.event_bus.publish("workflow_generation_started", {
                    "task_count": len(engineering_tasks),
                })
                logger.info("Engineering tasks dispatched to ExecutionEngine")

                # --- PHASE 6: Record decision in memory ---
                try:
                    if self.decision_memory:
                        self.decision_memory.record(
                            task_id=task.id,
                            prompt=prompt,
                            choice=f"Decomposed into {len(engineering_tasks)} tasks",
                            reasoning=(
                                f"complexity={task.estimated_complexity.value}, "
                                f"model={best_model or 'automatic'}"
                            ),
                            model_used=str(best_model or ""),
                        )
                    if self.project_memory and best_model:
                        self.project_memory.remember(
                            category="general",
                            content=f"Executed: {prompt[:80]} using {best_model}",
                            source="workflow_coordinator",
                        )
                except Exception as me:
                    logger.debug(f"Memory update skipped: {me}")

            except Exception as e:
                logger.error(f"ExecutionEngine submission failed: {e}")
                self.event_bus.publish("workflow_failed", {"error": str(e)})
        else:
            self.event_bus.publish("workflow_failed", {"error": "No execution engine available"})
    
    def _on_pause_request(self, payload: Dict[str, Any]):
        """Handle workflow pause request from UI."""
        if self.execution_engine:
            # Pause all running tasks
            running = self.execution_engine.get_running_tasks()
            for task in running:
                self.execution_engine.pause_task(task.id)
            logger.info(f"Paused {len(running)} running tasks")
            self.event_bus.publish("workflow_paused", {"count": len(running)})
    
    def _on_resume_request(self, payload: Dict[str, Any]):
        """Handle workflow resume request from UI."""
        if self.execution_engine:
            # Resume all paused tasks
            paused = [t for t in self.execution_engine.get_all_tasks() if t.state.value == "paused"]
            for task in paused:
                self.execution_engine.resume_task(task.id)
            logger.info(f"Resumed {len(paused)} paused tasks")
            self.event_bus.publish("workflow_resumed", {"count": len(paused)})
    
    def _on_cancel_request(self, payload: Dict[str, Any]):
        """Handle workflow cancel request from UI."""
        if self.execution_engine:
            # Cancel all non-terminal tasks
            all_tasks = self.execution_engine.get_all_tasks()
            cancelled_count = 0
            for task in all_tasks:
                if not task.is_terminal:
                    self.execution_engine.cancel_task(task.id, by_user="UI")
                    cancelled_count += 1
            logger.info(f"Cancelled {cancelled_count} tasks")
            self.event_bus.publish("workflow_cancelled", {"count": cancelled_count})
