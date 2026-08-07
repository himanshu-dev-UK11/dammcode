"""
Terminal Events — v2.1

Event definitions for terminal functionality.
"""
from typing import Dict, Any


# Terminal Events
TERMINAL_CREATED = "terminal_created"
TERMINAL_CLOSED = "terminal_closed"
TERMINAL_OUTPUT = "terminal_output"
TERMINAL_INPUT = "terminal_input"
TERMINAL_PROCESS_STARTED = "terminal_process_started"
TERMINAL_PROCESS_FINISHED = "terminal_process_finished"
TERMINAL_DIRECTORY_CHANGED = "terminal_directory_changed"
TERMINAL_SPLIT_CREATED = "terminal_split_created"
TERMINAL_TAB_CHANGED = "terminal_tab_changed"
TERMINAL_ERROR = "terminal_error"

# Session Management Events
TERMINAL_SESSION_SAVED = "terminal_session_saved"
TERMINAL_SESSION_RESTORED = "terminal_session_restored"
TERMINAL_SESSIONS_SAVED = "terminal_sessions_saved"
TERMINAL_SESSIONS_CLEARED = "terminal_sessions_cleared"

# Split Events
TERMINAL_SPLIT_RESIZED = "terminal_split_resized"
TERMINAL_SPLIT_COLLAPSED = "terminal_split_collapsed"
TERMINAL_SPLIT_EXPANDED = "terminal_split_expanded"
TERMINAL_SPLIT_ACTIVATED = "terminal_split_activated"
TERMINAL_SPLIT_CLEARED = "terminal_splits_cleared"

# Tab Events
TERMINAL_TAB_REORDERED = "terminal_tab_reordered"
TERMINAL_TAB_MOVED_TO_GROUP = "terminal_tab_moved_to_group"
TERMINAL_TAB_CLEARED = "terminal_tabs_cleared"

# Auto-scroll Events
TERMINAL_AUTO_SCROLL_CHANGED = "terminal_autoscroll_changed"
TERMINAL_JUMP_AVAILABLE = "terminal_jump_available"
TERMINAL_JUMP_HIDDEN = "terminal_jump_hidden"

# Bookmark Events
TERMINAL_BOOKMARK_CREATED = "terminal_bookmark_created"
TERMINAL_BOOKMARK_DELETED = "terminal_bookmark_deleted"
TERMINAL_BOOKMARK_RENAMED = "terminal_bookmark_renamed"
TERMINAL_BOOKMARK_MOVED = "terminal_bookmark_moved"
TERMINAL_BOOKMARK_EXECUTED = "terminal_bookmark_executed"
TERMINAL_FOLDER_CLEARED = "terminal_folder_cleared"

# Snapshot Events
TERMINAL_SNAPSHOT_SAVED = "terminal_snapshot_saved"
TERMINAL_SNAPSHOT_LOADED = "terminal_snapshot_loaded"
TERMINAL_SNAPSHOT_DELETED = "terminal_snapshot_deleted"
TERMINAL_SNAPSHOT_EXPORTED = "terminal_snapshot_exported"
TERMINAL_ALL_SNAPSHOTS_EXPORTED = "terminal_all_snapshots_exported"
TERMINAL_SNAPSHOTS_CLEARED = "terminal_snapshots_cleared"

# Quick Action Events
TERMINAL_QUICK_ACTION_TRIGGERED = "terminal_quick_action_triggered"

# Profile Events
TERMINAL_PROFILE_CHANGED = "terminal_profile_changed"

# History Events
TERMINAL_HISTORY_UPDATED = "terminal_history_updated"
TERMINAL_HISTORY_LOADED = "terminal_history_loaded"
TERMINAL_HISTORY_CLEARED = "terminal_history_cleared"
TERMINAL_HISTORY_EXPORTED = "terminal_history_exported"

# Search Events
TERMINAL_SEARCH_STARTED = "terminal_search_started"
TERMINAL_SEARCH_FINISHED = "terminal_search_finished"
TERMINAL_SEARCH_ERROR = "terminal_search_error"

# Export Events
TERMINAL_EXPORTED = "terminal_exported"

# Badge Events
TERMINAL_BADGE_UPDATED = "terminal_badge_updated"

# Process Events
TERMINAL_PROCESS_CREATED = "terminal_process_created"
TERMINAL_PROCESS_UPDATED = "terminal_process_updated"
TERMINAL_PROCESS_KILLED = "terminal_process_killed"
