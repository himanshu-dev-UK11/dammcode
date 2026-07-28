"""
TaskState — task lifecycle state machine.

Defines the complete lifecycle states for ExecutionTasks and
provides state transition rules to prevent invalid state changes.

This is a state machine pattern implementation to ensure
tasks can only transition between valid states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Set


class TaskState(Enum):
    """
    Lifecycle states for ExecutionTask.
    
    States follow a directed acyclic graph:
    
    PENDING → SCHEDULED → RUNNING → [SUCCESS/FAILED/CANCELLED]
                 ↘→ PAUSED → RUNNING (loop)
    
    Terminal states: SUCCESS, FAILED, CANCELLED, EXPIRED
    """
    # ── Non-started states ─────────────────────────────────────────────────
    PENDING     = "pending"      # Just created, not yet scheduled
    SCHEDULED   = "scheduled"    # Queued, waiting for executor availability
    
    # ── Active execution states ──────────────────────────────────────────
    RUNNING     = "running"      # Currently executing
    PAUSED      = "paused"       # Execution temporarily suspended
    
    # ── Terminal states ──────────────────────────────────────────────────
    SUCCESS     = "success"      # Completed successfully
    FAILED      = "failed"       # Execution failed (after all retries)
    CANCELLED   = "cancelled"    # Stopped by user
    EXPIRED     = "expired"      # Timeout reached


@dataclass
class StateTransition:
    """
    Records a single state transition with timing.
    
    Used for audit trail and debugging execution flow.
    
    Attributes:
        from_state: Previous state (None for initial state)
        to_state:   New state
        timestamp:  When transition occurred
        reason:     Human-readable reason for transition
        metadata:   Arbitrary data associated with transition
    """
    from_state: Optional[TaskState]
    to_state:   TaskState
    timestamp:  datetime
    reason:     str = ""
    metadata:   dict = field(default_factory=dict)
    
    def __repr__(self) -> str:
        from_str = f"→ {self.from_state.value}" if self.from_state else "START"
        return f"{from_str} → {self.to_state.value} ({self.timestamp:%H:%M:%S.%f})"


@dataclass
class TaskStateHistory:
    """
    Complete history of state transitions for a task.
    
    Provides methods to query the state machine:
    - Get current state
    - Get all transitions
    - Check if state is terminal
    - Calculate time in each state
    """
    transitions: list[StateTransition] = field(default_factory=list)
    
    @property
    def current_state(self) -> TaskState:
        """Return the current (most recent) state."""
        if not self.transitions:
            return TaskState.PENDING
        return self.transitions[-1].to_state
    
    @property
    def is_terminal(self) -> bool:
        """Return True if the task has reached a terminal state."""
        return self.current_state in {
            TaskState.SUCCESS, TaskState.FAILED, 
            TaskState.CANCELLED, TaskState.EXPIRED
        }
    
    def get_transitions(self) -> list[StateTransition]:
        """Return all state transitions in order."""
        return list(self.transitions)
    
    def get_transitions_by_state(self, state: TaskState) -> list[StateTransition]:
        """Return all transitions TO a specific state."""
        return [t for t in self.transitions if t.to_state == state]
    
    def get_time_in_state(self, state: TaskState) -> Optional[float]:
        """
        Calculate total time spent in a state (in seconds).
        Returns None if task never entered that state.
        """
        state_transitions = self.get_transitions_by_state(state)
        if not state_transitions:
            return None
        
        total = 0.0
        for i, trans in enumerate(state_transitions):
            # Find next transition
            next_trans = None
            for t in self.transitions:
                if t.timestamp > trans.timestamp:
                    next_trans = t
                    break
            
            # Calculate duration
            if next_trans:
                total += (next_trans.timestamp - trans.timestamp).total_seconds()
            else:
                # Still in this state (if not terminal) or ended here
                if not self.is_terminal or trans.to_state == self.current_state:
                    total += (datetime.utcnow() - trans.timestamp).total_seconds()
        
        return total
    
    def add_transition(self, transition: StateTransition) -> None:
        """Add a new state transition to history."""
        self.transitions.append(transition)


# ── Valid state transitions ───────────────────────────────────────────────────

VALID_TRANSITIONS: dict[TaskState, Set[TaskState]] = {
    TaskState.PENDING:   {TaskState.SCHEDULED, TaskState.CANCELLED},
    TaskState.SCHEDULED: {TaskState.RUNNING, TaskState.PAUSED, TaskState.CANCELLED},
    TaskState.RUNNING:   {TaskState.SUCCESS, TaskState.FAILED, TaskState.PAUSED, 
                          TaskState.CANCELLED, TaskState.EXPIRED},
    TaskState.PAUSED:    {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.SUCCESS:   set(),  # Terminal - no outgoing
    TaskState.FAILED:    set(),  # Terminal - no outgoing
    TaskState.CANCELLED: set(),  # Terminal - no outgoing
    TaskState.EXPIRED:   set(),  # Terminal - no outgoing
}


def can_transition(from_state: TaskState, to_state: TaskState) -> bool:
    """
    Check if a state transition is valid.
    
    Args:
        from_state: Current state
        to_state:   Target state
        
    Returns:
        True if the transition is allowed
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def validate_transition(from_state: TaskState, to_state: TaskState) -> None:
    """
    Validate a state transition, raising ValueError if invalid.
    
    Args:
        from_state: Current state
        to_state:   Target state
        
    Raises:
        ValueError: If the transition is not allowed
    """
    if not can_transition(from_state, to_state):
        raise ValueError(
            f"Invalid transition: {from_state.value} → {to_state.value}. "
            f"Valid transitions from {from_state.value}: "
            f"{[s.value for s in VALID_TRANSITIONS.get(from_state, set())]}"
        )
