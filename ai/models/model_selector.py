"""
Intelligent Model Selector.

Determines the best model for a given task and context.
"""

from typing import Tuple, Dict, Any
from core.logger import setup_logger
from ai.models.model_registry import ModelRegistry
from ai.models.model_context import ModelContextManager
from ai.models.model_profile import ModelProfile
from ai.memory.project_context import ProjectContext
from ai.engine.task import Task

logger = setup_logger(__name__)

class ModelSelector:
    """
    Scores and selects the best model for a task.
    """
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.context_manager = ModelContextManager()

    def select_best_model(self, task: Task, plan: Any, context: ProjectContext, require_local: bool = False) -> Tuple[str, str]:
        """
        Evaluate all available models and select the best one based on weighted scores.
        Returns: (selected_model_name, reason_for_selection)
        """
        available = self.registry.get_available_models()
        if not available:
            return "none", "No available models in registry."
            
        best_model = None
        best_score = -1.0
        reason = ""

        for model_name in available:
            profile = self.registry.get_profile(model_name)
            health = self.registry.get_health(model_name)
            
            if not profile or not health:
                continue
                
            if require_local and not profile.is_local:
                continue

            if not self.context_manager.fits_in_context(task, context, profile):
                continue

            score = self._calculate_score(task, profile, health)
            
            if score > best_score:
                best_score = score
                best_model = model_name
                reason = self._generate_reason(task, profile)

        if not best_model:
            # Fallback to the first available if all else fails
            fallback = available[0]
            logger.warning(f"No optimal model found. Falling back to {fallback}.")
            return fallback, "Fallback selected due to constraints."

        logger.info(f"Selected model: {best_model} (Score: {best_score})")
        return best_model, reason

    def _calculate_score(self, task: Task, profile: ModelProfile, health: Any) -> float:
        """
        Compute a weighted score based on task complexity, model ability, and health.
        """
        score = 0.0
        
        # Coding vs Reasoning weighting
        if task and task.estimated_complexity.value in ("complex", "expert"):
            score += profile.reasoning_ability * 2.0
        else:
            score += profile.coding_ability * 1.5

        # Health penalty
        score *= health.current_availability
        
        return score

    def _generate_reason(self, task: Task, profile: ModelProfile) -> str:
        return f"Selected {profile.name} for its {profile.coding_ability}/10 coding ability and health status."
