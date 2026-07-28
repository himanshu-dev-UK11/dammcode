"""
ComplexityAnalyzer module.

Estimates the project's overall difficulty level.
"""

from ai.memory.project_context import ProjectContext
from ai.engine.task import Task

class ComplexityAnalyzer:
    """
    Assigns an estimated complexity rating to a task.
    """
    def estimate_complexity(self, task: Task, context: ProjectContext) -> str:
        """
        Return Easy, Medium, Hard, or Very Hard based on context size and task type.
        """
        if not context:
            return "Easy"
            
        if context.total_files < 10:
            return "Easy"
        elif context.total_files < 50:
            return "Medium"
        elif context.total_files < 200:
            return "Hard"
        else:
            return "Very Hard"
