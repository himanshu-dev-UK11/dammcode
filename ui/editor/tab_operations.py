"""
Tab Operations — v1.0

Support tab operations: Duplicate, Close Others, Close Left, Close Right, Reopen Closed Tab.
"""

from PySide6.QtWidgets import QTabWidget, QMenu
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction
from pathlib import Path


class TabOperationsManager(QObject):
    """Manages tab operations."""
    
    tab_closed = Signal(str)
    tab_reopened = Signal(str)
    tabs_reordered = Signal()
    
    def __init__(self, tab_widget: QTabWidget, parent=None):
        super().__init__(parent)
        self.tab_widget = tab_widget
        self.closed_tabs = []  # Stack of closed tabs: (index, path, title)
        
    def _get_tab_path(self, tab_index: int):
        """Get file path for tab index."""
        widget = self.tab_widget.widget(tab_index)
        if hasattr(widget, 'file_path'):
            return widget.file_path
        return None
        
    def _get_tab_title(self, tab_index: int):
        """Get title for tab index."""
        return self.tab_widget.tabText(tab_index)
        
    def duplicate_tab(self, tab_index: int = None):
        """Duplicate a tab."""
        if tab_index is None:
            tab_index = self.tab_widget.currentIndex()
            
        if tab_index < 0:
            return
            
        path = self._get_tab_path(tab_index)
        if not path:
            return
            
        # Get content from the editor
        editor = self.tab_widget.widget(tab_index)
        content = editor.toPlainText() if hasattr(editor, 'toPlainText') else ""
        
        # Create new tab with same content
        new_editor = type(editor)(path)
        new_editor.setPlainText(content)
        new_editor.document().setModified(False)
        
        # Insert after current tab
        new_index = tab_index + 1
        self.tab_widget.insertTab(new_index, new_editor, Path(path).name)
        self.tab_widget.setCurrentIndex(new_index)
        
    def close_others(self, keep_index: int = None):
        """Close all tabs except the one at keep_index."""
        if keep_index is None:
            keep_index = self.tab_widget.currentIndex()
            
        tabs_to_close = []
        for i in range(self.tab_widget.count()):
            if i != keep_index:
                path = self._get_tab_path(i)
                if path:
                    tabs_to_close.append(i)
                    
        # Close in reverse order
        for i in reversed(tabs_to_close):
            self.close_tab(i)
            
    def close_all(self):
        """Close all tabs."""
        for i in reversed(range(self.tab_widget.count())):
            self.close_tab(i)
            
    def close_left(self, current_index: int = None):
        """Close all tabs to the left of current."""
        if current_index is None:
            current_index = self.tab_widget.currentIndex()
            
        tabs_to_close = list(range(current_index))
        for i in reversed(tabs_to_close):
            self.close_tab(i)
            
    def close_right(self, current_index: int = None):
        """Close all tabs to the right of current."""
        if current_index is None:
            current_index = self.tab_widget.currentIndex()
            
        tabs_to_close = list(range(current_index + 1, self.tab_widget.count()))
        for i in reversed(tabs_to_close):
            self.close_tab(i)
            
    def close_tab(self, tab_index: int):
        """Close a tab and save for potential reopening."""
        if tab_index < 0 or tab_index >= self.tab_widget.count():
            return
            
        path = self._get_tab_path(tab_index)
        title = self._get_tab_title(tab_index)
        
        # Save for potential reopen
        self.closed_tabs.append((tab_index, path, title))
        
        # Remove tab
        widget = self.tab_widget.widget(tab_index)
        self.tab_widget.removeTab(tab_index)
        if widget:
            widget.deleteLater()
            
        if path:
            self.tab_closed.emit(path)
            
    def reopen_closed_tab(self):
        """Reopen the most recently closed tab."""
        if not self.closed_tabs:
            return
            
        index, path, title = self.closed_tabs.pop()
        
        if path and Path(path).exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                content = ""
                
            # Create new editor
            from ui.editor.code_editor import CodeEditor
            editor = CodeEditor(path)
            editor.load_file(content)
            
            # Insert at the saved position (or at end)
            new_index = min(index, self.tab_widget.count())
            self.tab_widget.insertTab(new_index, editor, title)
            self.tab_widget.setCurrentIndex(new_index)
            
            self.tab_reopened.emit(path)
            
    def can_reopen_tab(self) -> bool:
        """Check if there's a closed tab to reopen."""
        return len(self.closed_tabs) > 0
        
    def get_closed_tabs_count(self) -> int:
        """Get number of closed tabs available for reopen."""
        return len(self.closed_tabs)
        
    def clear_closed_tabs(self):
        """Clear the closed tabs history."""
        self.closed_tabs.clear()
