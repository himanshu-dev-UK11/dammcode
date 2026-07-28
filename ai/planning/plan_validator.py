"""
PlanValidator module.

Verifies the generated plan to prevent invalid execution sequences.
"""

from ai.planning.plan import Plan
from ai.planning.dependency_graph import DependencyGraph

class PlanValidator:
    """
    Runs safety and structural checks on the proposed Plan.
    """
    def validate(self, plan: Plan) -> bool:
        """
        Check for missing steps, duplicate work, invalid order, missing dependencies.
        """
        if not plan.steps:
            return False
            
        step_ids = [step.step_id for step in plan.steps]
        
        # Check for duplicate step IDs
        if len(step_ids) != len(set(step_ids)):
            return False
            
        # Check for missing dependencies
        graph = DependencyGraph()
        graph.build_step_graph(plan.steps)
        
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    return False
                    
        # Check for cyclic dependencies
        if graph.has_cycles():
            return False
            
        return True
