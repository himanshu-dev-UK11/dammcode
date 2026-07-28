"""
Plan dataclass.

Represents the complete, validated execution plan for a Task.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ai.planning.plan_step import PlanStep

@dataclass
class Plan:
    """
    Complete execution plan containing all steps, risks, and metadata.
    """
    plan_id: str
    goal: str
    status: str = "pending"
    estimated_time_minutes: float = 0.0
    estimated_tokens: int = 0
    complexity: str = "easy"
    risks: List[Dict[str, str]] = field(default_factory=list)
    required_models: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    phases: Dict[str, List[str]] = field(default_factory=dict)
