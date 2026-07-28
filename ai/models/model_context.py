"""
Model Context Manager.

Determines if a task's context fits within a model's limits.
"""

from ai.models.model_profile import ModelProfile
from ai.memory.project_context import ProjectContext
from ai.engine.task import Task

class ModelContextManager:
    """
    Estimates token usage and validates context constraints.
    """
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation: 1 token ~= 4 characters."""
        if not text:
            return 0
        return len(text) // 4

    def fits_in_context(self, task: Task, context: ProjectContext, profile: ModelProfile) -> bool:
        """
        Check if the required context fits within the model's window.
        """
        prompt_tokens = self.estimate_tokens(task.original_prompt) if task else 0
        
        # Estimate context overhead based on project stats
        files_to_retrieve = min(10, context.total_files) if context else 0
        estimated_file_tokens = files_to_retrieve * 500  # Assume 500 tokens per file retrieved
        
        total_estimated = prompt_tokens + estimated_file_tokens
        
        # Keep 20% margin for generation and safety
        return total_estimated < (profile.context_window * 0.8)
