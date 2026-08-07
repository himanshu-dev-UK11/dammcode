"""
Editor Package — v1.0

Professional IDE editor components with:
- Breadcrumb navigation
- Minimap
- Line highlighting
- Indent guides
- Bracket matching
- Sticky tabs
- Tab operations
- Split editor
"""

from ui.editor.code_editor import CodeEditor
from ui.editor.editor_tabs import EditorTabs
from ui.editor.breadcrumb_bar import BreadcrumbNavigation
from ui.editor.minimap import MinimapWidget, MinimapPanel
from ui.editor.highlighter import HighlightManager, LineNumberHighlighter
from ui.editor.indent_guides import IndentGuideOverlay, IndentGuideManager
from ui.editor.bracket_matcher import BracketMatcher
from ui.editor.sticky_tabs import StickyTabManager
from ui.editor.tab_operations import TabOperationsManager
from ui.editor.splitted_editor import SplitEditorManager
from ui.editor.editor_events import get_editor_events, EDITOR_EVENTS

__all__ = [
    # Core editor
    "CodeEditor",
    "EditorTabs",
    
    # Breadcrumb
    "BreadcrumbNavigation",
    
    # Minimap
    "MinimapWidget",
    "MinimapPanel",
    
    # Highlighting
    "HighlightManager",
    "LineNumberHighlighter",
    
    # Indent guides
    "IndentGuideOverlay",
    "IndentGuideManager",
    
    # Bracket matching
    "BracketMatcher",
    
    # Sticky tabs
    "StickyTabManager",
    
    # Tab operations
    "TabOperationsManager",
    
    # Split editor
    "SplitEditorManager",
    
    # Events
    "get_editor_events",
    "EDITOR_EVENTS",
]
