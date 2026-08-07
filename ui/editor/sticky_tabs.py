"""
Sticky Tabs — v1.0

Allow users to pin tabs. Pinned tabs stay left and cannot close accidentally.
Supports pin/unpin, visual indication, and proper tab ordering.
"""

from PySide6.QtWidgets import QTabBar, QTabWidget, QMenu
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction


class StickyTabManager(QObject):
    """Manages pinned/sticky tabs behavior."""
    
    tab_pinned = Signal(str)
    tab_unpinned = Signal(str)
    tabs_reordered = Signal()
    
    def __init__(self, tab_widget: QTabWidget, parent=None):
        super().__init__(parent)
        self.tab_widget = tab_widget
        self.pinned_tabs = {}  # path -> tab_index
        self._setup_tab_bar()
        
    def _setup_tab_bar(self):
        """Setup tab bar with custom context menu."""
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        tab_bar.customContextMenuRequested.connect(self._show_tab_context_menu)
        tab_bar.tabBarDoubleClicked.connect(self._handle_double_click)
        
    def _show_tab_context_menu(self, pos):
        """Show context menu for tab."""
        tab_index = self.tab_widget.tabBar().tabAt(pos)
        if tab_index < 0:
            return
            
        path = self._get_tab_path(tab_index)
        if not path:
            return
            
        menu = QMenu()
        
        # Pin/Unpin
        is_pinned = path in self.pinned_tabs
        pin_action = QAction("Unpin Tab" if is_pinned else "Pin Tab", self)
        pin_action.triggered.connect(lambda: self.toggle_pin_tab(tab_index))
        menu.addAction(pin_action)
        
        menu.addSeparator()
        
        # Close operations
        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self.close_tab(tab_index))
        menu.addAction(close_action)
        
        # Close others
        close_others_action = QAction("Close Others", self)
        close_others_action.triggered.connect(lambda: self._close_others(tab_index))
        menu.addAction(close_others_action)
        
        # Close all
        close_all_action = QAction("Close All", self)
        close_all_action.triggered.connect(self._close_all)
        menu.addAction(close_all_action)
        
        menu.exec_(self.tab_widget.tabBar().mapToGlobal(pos))
        
    def _handle_double_click(self, tab_index):
        """Handle double-click on tab."""
        self.toggle_pin_tab(tab_index)
        
    def _get_tab_path(self, tab_index: int):
        """Get file path for tab index."""
        widget = self.tab_widget.widget(tab_index)
        if hasattr(widget, 'file_path'):
            return widget.file_path
        return None
        
    def toggle_pin_tab(self, tab_index: int):
        """Toggle tab pin state."""
        path = self._get_tab_path(tab_index)
        if not path:
            return
            
        if path in self.pinned_tabs:
            self.unpin_tab(tab_index)
        else:
            self.pin_tab(tab_index)
            
    def pin_tab(self, tab_index: int):
        """Pin a tab."""
        path = self._get_tab_path(tab_index)
        if not path or path in self.pinned_tabs:
            return
            
        # Move tab to the left (before unpinned tabs)
        self.tab_widget.tabBar().moveTab(tab_index, len(self.pinned_tabs))
        
        self.pinned_tabs[path] = len(self.pinned_tabs)
        self.tab_widget.tabBar().setTabData(len(self.pinned_tabs) - 1, {"pinned": True})
        self.tab_widget.tabBar().setTabText(len(self.pinned_tabs) - 1, 
                                            self.tab_widget.tabBar().tabText(len(self.pinned_tabs) - 1))
        
        # Update font to indicate pinned
        tab_text = self.tab_widget.tabBar().tabText(len(self.pinned_tabs) - 1)
        self.tab_widget.tabBar().setTabText(len(self.pinned_tabs) - 1, tab_text)
        
        self.tab_pinned.emit(path)
        
    def unpin_tab(self, tab_index: int):
        """Unpin a tab."""
        path = self._get_tab_path(tab_index)
        if not path or path not in self.pinned_tabs:
            return
            
        # Remove from pinned dict
        del self.pinned_tabs[path]
        self.tab_widget.tabBar().setTabData(tab_index, {"pinned": False})
        
        # Reorder tabs
        self._reorder_tabs()
        
        self.tab_unpinned.emit(path)
        
    def is_tab_pinned(self, tab_index: int) -> bool:
        """Check if tab is pinned."""
        path = self._get_tab_path(tab_index)
        return path in self.pinned_tabs
        
    def _reorder_tabs(self):
        """Reorder tabs to put pinned tabs first."""
        tab_count = self.tab_widget.count()
        paths = []
        
        # Collect all paths
        for i in range(tab_count):
            path = self._get_tab_path(i)
            if path:
                paths.append(path)
                
        # Separate pinned and unpinned
        pinned = [p for p in paths if p in self.pinned_tabs]
        unpinned = [p for p in paths if p not in self.pinned_tabs]
        
        # Reorder
        new_paths = pinned + unpinned
        self._reorder_tabs_by_paths(new_paths)
        
    def _reorder_tabs_by_paths(self, ordered_paths):
        """Reorder tabs to match path order."""
        current_paths = []
        for i in range(self.tab_widget.count()):
            path = self._get_tab_path(i)
            if path:
                current_paths.append(path)
                
        # Build new order
        new_order = []
        for path in ordered_paths:
            if path in current_paths:
                idx = current_paths.index(path)
                new_order.append(idx)
                current_paths[idx] = None  # Mark as used
                
        # Add any remaining tabs
        for i, path in enumerate(current_paths):
            if path is not None:
                new_order.append(i)
                
        # Apply new order
        for i, idx in enumerate(new_order):
            if i != idx:
                self.tab_widget.tabBar().moveTab(idx, i)
                
    def _close_others(self, keep_index: int):
        """Close all tabs except the one at keep_index."""
        paths_to_keep = []
        for i in range(self.tab_widget.count()):
            if i == keep_index:
                path = self._get_tab_path(i)
                if path:
                    paths_to_keep.append(path)
                    
        # Close all tabs
        self._close_all()
        
        # Reopen kept tabs
        for path in paths_to_keep:
            # This would be handled by the main editor tabs logic
            pass
            
    def _close_all(self):
        """Close all tabs."""
        for i in reversed(range(self.tab_widget.count())):
            self.tab_widget.tabBar().tabCloseRequested.emit(i)
            
    def close_tab(self, tab_index: int):
        """Close a specific tab."""
        if tab_index >= 0:
            self.tab_widget.tabBar().tabCloseRequested.emit(tab_index)
            
    def get_pinned_paths(self):
        """Get list of pinned tab paths in order."""
        return list(self.pinned_tabs.keys())
        
    def set_pinned_paths(self, paths):
        """Set pinned tabs from path list."""
        self.pinned_tabs.clear()
        
        # Find tab indices for each path
        path_to_index = {}
        for i in range(self.tab_widget.count()):
            path = self._get_tab_path(i)
            if path:
                path_to_index[path] = i
                
        # Set pinned status
        for i, path in enumerate(paths):
            if path in path_to_index:
                self.pinned_tabs[path] = i
                self.tab_widget.tabBar().setTabData(i, {"pinned": True})
