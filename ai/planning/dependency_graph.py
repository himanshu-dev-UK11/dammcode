"""
DependencyGraph module.

Builds a dependency graph to ensure correct step execution order
and to identify related files.
"""

from typing import List, Dict, Set
from ai.planning.plan_step import PlanStep

class DependencyGraph:
    """
    Manages relationships between execution steps and project files.
    """
    def __init__(self):
        self.step_dependencies: Dict[str, List[str]] = {}
        self.file_dependencies: Dict[str, List[str]] = {}
        
    def build_step_graph(self, steps: List[PlanStep]) -> None:
        """
        Build a directed graph of step dependencies.
        """
        for step in steps:
            self.step_dependencies[step.step_id] = step.dependencies
            
    def analyze_file_dependencies(self, files: List[str]) -> None:
        """
        Placeholder for file-level dependency analysis.
        e.g. login.dart -> auth_service.dart -> user_model.dart
        """
        pass
        
    def has_cycles(self) -> bool:
        """
        Check if the step dependency graph contains cyclic dependencies.
        """
        visited: Set[str] = set()
        path: Set[str] = set()
        
        def visit(node: str) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            path.add(node)
            
            for neighbor in self.step_dependencies.get(node, []):
                if visit(neighbor):
                    return True
                    
            path.remove(node)
            return False
            
        for node in self.step_dependencies:
            if visit(node):
                return True
                
        return False
