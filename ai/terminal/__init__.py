"""
AI Terminal Module — v1.0

Provides deep AI terminal integration for the MyCodingMaster IDE.
"""

from .ai_terminal_manager import AITerminalManager
from .terminal_approval_panel import TerminalApprovalPanel
from .ai_terminal_execution import AITerminalExecution
from .terminal_history_storage import TerminalHistoryStorage
from .terminal_output_analyzer import TerminalOutputAnalyzer

__all__ = [
    "AITerminalManager",
    "TerminalApprovalPanel",
    "AITerminalExecution",
    "TerminalHistoryStorage",
    "TerminalOutputAnalyzer"
]
