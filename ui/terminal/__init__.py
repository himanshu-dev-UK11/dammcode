"""
Terminal module for MyCodingMaster IDE v2.1

Professional integrated terminal platform with multi-tab support, session persistence,
split management, drag & drop, and productivity features.
"""
from .terminal_manager import TerminalManager, TerminalSession
from .shell_manager import ShellManager, ShellConfig
from .session_manager import SessionManager
from .splits_manager import SplitsManager
from .drag_drop_manager import DragDropManager
from .breadcrumb import TerminalBreadcrumb
from .smart_scrolling import SmartScrollingManager
from .bookmarks_manager import BookmarksManager
from .snapshots_manager import SnapshotsManager
from .quick_actions import QuickActionsManager
from .indicators import TerminalIndicators

__all__ = [
    'TerminalManager', 'TerminalSession', 'ShellManager', 'ShellConfig',
    'SessionManager', 'SplitsManager', 'DragDropManager', 'TerminalBreadcrumb',
    'SmartScrollingManager', 'BookmarksManager', 'SnapshotsManager',
    'QuickActionsManager', 'TerminalIndicators'
]