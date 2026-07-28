"""
PlanStep dataclass.

Represents a single atomic step within a larger Plan.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PlanStep:
    """
    A single step in the execution plan.
    """
    step_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time_minutes: float = 0.0
    required_tool: Optional[str] = None
    required_model: Optional[str] = None
    expected_output: str = ""
    status: str = "pending"
