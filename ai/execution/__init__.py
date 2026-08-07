"""
AI Execution Engine package.

The execution engine coordinates every AI action in MyCodingMaster.
It does NOT contain any LLM-specific code. It only manages execution.

Core components:
- execution_engine.py: Main orchestrator creating, scheduling, tracking tasks
- execution_task.py: Extended task dataclass with execution metadata
- execution_queue.py: Priority queue with persistence support
- task_scheduler.py: Sequential/parallel scheduling with dependencies
- task_executor.py: Thread pool executor with retry logic
- task_state.py: Task lifecycle state machine
- execution_monitor.py: Real-time monitoring of execution metrics
- execution_report.py: Human-readable execution reports
- execution_events.py: Event definitions for UI integration
- execution_metrics.py: Performance metrics tracking

All components use EventBus for non-blocking UI updates.
"""

from .execution_engine import ExecutionEngine
from .execution_task import ExecutionTask
from .execution_queue import ExecutionQueue
from .task_scheduler import TaskScheduler
from .task_executor import TaskExecutor
from .task_state import TaskState
from .execution_monitor import ExecutionMonitor
from .execution_report import ExecutionReportGenerator
from .execution_events import ExecutionEvents
from .execution_metrics import ExecutionMetrics

__all__ = [
    'ExecutionEngine',
    'ExecutionTask',
    'ExecutionQueue',
    'TaskScheduler',
    'TaskExecutor',
    'TaskState',
    'ExecutionMonitor',
    'ExecutionReportGenerator',
    'ExecutionEvents',
    'ExecutionMetrics',
]
