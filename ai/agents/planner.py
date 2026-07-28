"""
Project planning and roadmap generation agent.
"""

from typing import Optional
import uuid
from ai.agents.base_agent import BaseAgent
from ai.engine.task import Task
from ai.memory.project_context import ProjectContext
from ai.planning.plan import Plan
from ai.planning.task_decomposer import TaskDecomposer
from ai.planning.roadmap_builder import RoadmapBuilder
from ai.planning.complexity_analyzer import ComplexityAnalyzer
from ai.planning.risk_analyzer import RiskAnalyzer
from ai.planning.plan_validator import PlanValidator

class PlannerAgent(BaseAgent):
    def __init__(self, event_bus):
        super().__init__("planner", event_bus)
        self.decomposer = TaskDecomposer()
        self.roadmap_builder = RoadmapBuilder()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.validator = PlanValidator()
        
    def create_plan(self, goal: str, context: Optional[ProjectContext] = None, task: Optional[Task] = None) -> Plan:
        self.logger.info(f"Creating plan for goal: {goal}")
        
        if not task:
            task = Task(original_prompt=goal, objective=goal)
            
        # Decompose the task into executable steps
        steps = self.decomposer.decompose(task, context)
        
        # Group steps into execution phases
        phases = self.roadmap_builder.build_roadmap(steps)
        
        # Analyze project complexity and potential risks
        complexity = self.complexity_analyzer.estimate_complexity(task, context)
        risks = self.risk_analyzer.analyze_risks(task, context)
        
        # Build the final Plan object
        plan = Plan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            complexity=complexity,
            risks=risks,
            steps=steps,
            phases=phases
        )
        
        # Validate the generated plan
        is_valid = self.validator.validate(plan)
        if not is_valid:
            self.logger.warning("Generated plan failed validation!")
            plan.status = "failed_validation"
        else:
            plan.status = "validated"
            
        return plan
