"""
Tasks Package — Task System Integration

Provides a professional task system for the integrated terminal.
"""
from ui.tasks.task import Task, TaskStatus, TaskType, TaskExecutionRecord
from ui.tasks.task_manager import TaskManager
from ui.tasks.task_panel import TaskPanel
from ui.tasks.project_detector import ProjectDetector, create_default_tasks_for_project
from ui.tasks.quick_run_bar import QuickRunBar
from ui.tasks.task_events import *

__all__ = [
    # Models
    "Task",
    "TaskStatus",
    "TaskType",
    "TaskExecutionRecord",
    
    # Managers
    "TaskManager",
    "ProjectDetector",
    
    # UI Components
    "TaskPanel",
    "QuickRunBar",
    
    # Events
    "TASK_CREATED",
    "TASK_UPDATED",
    "TASK_DELETED",
    "TASK_STATUS_CHANGED",
    "TASK_PINNED",
    "TASK_FAVORITED",
    "TASK_EXECUTE_REQUESTED",
    "TASK_CANCEL_REQUESTED",
    "TASK_EXECUTING",
    "TASK_STARTED",
    "TASK_FINISHED",
    "TASK_FAILED",
    "TASK_CANCELLED",
    "TASK_HISTORY_UPDATED",
    "TASK_HISTORY_CLEARED",
    "TASK_PANEL_TASK_SELECTED",
    "TASK_PANEL_TASK_EXECUTED",
    "TASK_PANEL_TASK_CANCELLED",
    "QUICK_RUN_EXECUTE",
    
    # Utils
    "create_default_tasks_for_project",
]
