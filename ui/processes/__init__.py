"""
Processes Package — Process Manager Integration

Provides process management and debug console for the integrated terminal.
"""
from ui.processes.process import Process, ProcessStatus, ProcessType, DebugMessage, ResourceUsage
from ui.processes.process_manager import ProcessManager
from ui.processes.process_panel import ProcessPanel
from ui.processes.debug_console import DebugConsole
from ui.processes.process_events import *

__all__ = [
    # Models
    "Process",
    "ProcessStatus",
    "ProcessType",
    "DebugMessage",
    "ResourceUsage",
    
    # Managers
    "ProcessManager",
    
    # UI Components
    "ProcessPanel",
    "DebugConsole",
    
    # Events
    "PROCESS_CREATED",
    "PROCESS_STARTED",
    "PROCESS_OUTPUT",
    "PROCESS_UPDATED",
    "PROCESS_FINISHED",
    "PROCESS_STOPPED",
    "PROCESS_KILLED",
    "PROCESS_RESTARTED",
    "DEBUG_MESSAGE",
    "DEBUG_CONSOLE_UPDATED",
    "RESOURCE_USAGE_UPDATED",
    "TERMINAL_BADGE_UPDATED",
    "BADGE_RUNNING",
    "BADGE_BUSY",
    "BADGE_IDLE",
    "BADGE_COMPLETED",
    "BADGE_FAILED",
]
