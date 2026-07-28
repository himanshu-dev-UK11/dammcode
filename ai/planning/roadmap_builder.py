"""
RoadmapBuilder module.

Groups PlanSteps into sequential execution phases.
"""

from typing import List, Dict
from ai.planning.plan_step import PlanStep

class RoadmapBuilder:
    """
    Generates execution phases from a list of steps.
    """
    def build_roadmap(self, steps: List[PlanStep]) -> Dict[str, List[str]]:
        """
        Groups step IDs into logical phases.
        """
        phases = {
            "Phase 1: Preparation": [],
            "Phase 2: Implementation": [],
            "Phase 3: Testing and Verification": []
        }
        
        for i, step in enumerate(steps):
            if i == 0:
                phases["Phase 1: Preparation"].append(step.step_id)
            elif i == len(steps) - 1:
                phases["Phase 3: Testing and Verification"].append(step.step_id)
            else:
                phases["Phase 2: Implementation"].append(step.step_id)
                
        return phases
