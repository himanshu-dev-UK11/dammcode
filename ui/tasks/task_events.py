"""
Task Events — Event Definitions for Task System

Event types used by the Task System for EventBus communication.
"""


# Task Management Events

TASK_CREATED = "task_created"
"""Event: A new task was created.
Data: {"task_id": str, "task": dict}
"""


TASK_UPDATED = "task_updated"
"""Event: An existing task was updated.
Data: {"task_id": str, "task": dict}
"""


TASK_DELETED = "task_deleted"
"""Event: A task was deleted.
Data: {"task_id": str}
"""


TASK_STATUS_CHANGED = "task_status_changed"
"""Event: A task's status changed.
Data: {"task_id": str, "status": str}
"""


TASK_PINNED = "task_pinned"
"""Event: A task's pinned status changed.
Data: {"task_id": str, "is_pinned": bool}
"""


TASK_FAVORITED = "task_favorited"
"""Event: A task's favorite status changed.
Data: {"task_id": str, "is_favorite": bool}
"""


# Task Execution Events

TASK_EXECUTE_REQUESTED = "task_execute_requested"
"""Event: Request to execute a task.
Data: {"task_id": str}
"""


TASK_CANCEL_REQUESTED = "task_cancel_requested"
"""Event: Request to cancel a task.
Data: {"task_id": str}
"""


TASK_EXECUTING = "task_executing"
"""Event: A task is about to execute.
Data: {"task_id": str, "command": str, "working_directory": str}
"""


TASK_STARTED = "task_started"
"""Event: A task has started executing.
Data: {"task_id": str}
"""


TASK_FINISHED = "task_finished"
"""Event: A task has finished executing.
Data: {"task_id": str, "exit_code": int, "duration_ms": int}
"""


TASK_FAILED = "task_failed"
"""Event: A task has failed.
Data: {"task_id": str, "exit_code": int}
"""


TASK_CANCELLED = "task_cancelled"
"""Event: A task was cancelled.
Data: {"task_id": str}
"""


# Task History Events

TASK_HISTORY_UPDATED = "task_history_updated"
"""Event: Task history was updated (new record added).
Data: {}
"""


TASK_HISTORY_CLEARED = "task_history_cleared"
"""Event: Task history was cleared.
Data: {}
"""


# Terminal Panel Integration Events

TASK_PANEL_TASK_SELECTED = "task_panel_task_selected"
"""Event: A task was selected in the task panel.
Data: {"task_id": str}
"""


TASK_PANEL_TASK_EXECUTED = "task_panel_task_executed"
"""Event: A task was executed from the task panel.
Data: {"task_id": str}
"""


TASK_PANEL_TASK_CANCELLED = "task_panel_task_cancelled"
"""Event: A task was cancelled from the task panel.
Data: {"task_id": str}
"""


# Quick Run Bar Events

QUICK_RUN_EXECUTE = "quick_run_execute"
"""Event: Quick run button was pressed.
Data: {"task_type": str}
"""
