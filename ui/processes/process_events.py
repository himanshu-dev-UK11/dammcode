"""
Process Events — Event Definitions for Process Manager

Event types used by the Process Manager for EventBus communication.
"""


# Process Management Events

PROCESS_CREATED = "process_created"
"""Event: A new process was created.
Data: {"process_id": str, "process": dict}
"""


PROCESS_STARTED = "process_started"
"""Event: A process has started executing.
Data: {"process_id": str, "pid": int, "terminal_id": str, "session_id": str}
"""


PROCESS_OUTPUT = "process_output"
"""Event: Process output received.
Data: {"process_id": str, "output": str, "stream": str}
"""


PROCESS_UPDATED = "process_updated"
"""Event: A process was updated (status changed).
Data: {"process_id": str}
"""


PROCESS_FINISHED = "process_finished"
"""Event: A process has finished executing.
Data: {"process_id": str, "exit_code": int, "duration_ms": int}
"""


PROCESS_STOPPED = "process_stopped"
"""Event: A process was stopped.
Data: {"process_id": str}
"""


PROCESS_KILLED = "process_killed"
"""Event: A process was killed.
Data: {"process_id": str}
"""


PROCESS_RESTARTED = "process_restarted"
"""Event: A process was restarted.
Data: {"process_id": str, "new_process_id": str}
"""


# Debug Console Events

DEBUG_MESSAGE = "debug_message"
"""Event: A debug message was added.
Data: {"level": str, "message": str, "source": str, "file": str, "line": int, "stack_trace": str}
"""


DEBUG_CONSOLE_UPDATED = "debug_console_updated"
"""Event: Debug console was updated.
Data: {}
"""


# Resource Monitoring Events

RESOURCE_USAGE_UPDATED = "resource_usage_updated"
"""Event: Resource usage was updated.
Data: {"cpu_usage": float, "memory_usage_mb": float, "memory_usage_percent": float,
       "process_count": int, "running_tasks": int, "terminal_count": int}
"""


# Terminal Integration Events

TERMINAL_BADGE_UPDATED = "terminal_badge_updated"
"""Event: A terminal tab badge should be updated.
Data: {"terminal_id": str, "status": str, "badge": str}
"""

# Badge Status Values
BADGE_RUNNING = "running"
BADGE_BUSY = "busy"
BADGE_IDLE = "idle"
BADGE_COMPLETED = "completed"
BADGE_FAILED = "failed"
