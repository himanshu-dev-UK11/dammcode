"""
Editor Events — v1.0

EventBus event definitions for editor features.
"""

EDITOR_EVENTS = [
    # Breadcrumb navigation
    "breadcrumb_navigated",
    "symbol_selected",
    
    # Minimap
    "minimap_visible_changed",
    "minimap_region_changed",
    
    # Line highlighting
    "current_line_highlight_changed",
    "line_number_highlight_changed",
    
    # Bracket matching
    "brackets_matched",
    
    # Sticky tabs
    "editor_tab_pinned",
    "editor_tab_unpinned",
    "tabs_reordered",
    
    # Tab operations
    "editor_duplicate_tab",
    "editor_close_others",
    "editor_close_left",
    "editor_close_right",
    "editor_reopen_tab",
    "editor_tab_closed",
    
    # Split editor
    "editor_split",
    "editor_split_changed",
    "editor_closed",
    "editor_file_moved",
    
    # Performance events
    "large_file_loaded",
    "scroll_throttled",
]


def get_editor_events():
    """Get list of all editor event names."""
    return EDITOR_EVENTS.copy()
