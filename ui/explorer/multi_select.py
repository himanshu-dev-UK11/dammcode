"""
Multi-Selection Manager — v2.2

Manages multi-selection in the Explorer tree.
Supports: Ctrl, Shift, Drag selection
"""
from pathlib import Path
from typing import List, Optional, Set
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, QItemSelection, QItemSelectionModel
from PySide6.QtGui import QMouseEvent
from core.logger import setup_logger

logger = setup_logger(__name__)


class MultiSelectManager:
    """
    Manages multi-selection in the Explorer tree.
    Supports Ctrl (add/remove), Shift (range), and drag selection.
    """
    
    def __init__(self, tree_widget: QTreeWidget):
        self.tree_widget = tree_widget
        self._selection_model = tree_widget.selectionModel()
        self._last_selected_item: Optional[QTreeWidgetItem] = None
        self._selection_modified = False
        
        # Track selection behavior
        self._is_selecting_range = False
        self._range_start_item: Optional[QTreeWidgetItem] = None
    
    def get_selected_paths(self) -> List[Path]:
        """Get list of selected file/folder paths."""
        items = self.tree_widget.selectedItems()
        paths = []
        
        for item in items:
            path_str = item.data(0, Qt.UserRole)
            if path_str:
                paths.append(Path(path_str))
        
        return paths
    
    def select_path(self, path: Path):
        """Select a specific path."""
        items = self.tree_widget.findItems(str(path), Qt.MatchRecursive | Qt.MatchExactly, 0)
        if items:
            self.tree_widget.setCurrentItem(items[0])
            self.tree_widget.scrollToItem(items[0])
    
    def select_paths(self, paths: List[Path]):
        """Select multiple paths."""
        self._selection_modified = True
        
        # Clear existing selection (if not adding)
        if not self.tree_widget.selectionMode() == QTreeWidget.ExtendedSelection:
            self.tree_widget.clearSelection()
        
        for path in paths:
            items = self.tree_widget.findItems(str(path), Qt.MatchRecursive | Qt.MatchExactly, 0)
            if items:
                self.tree_widget.setCurrentItem(items[0])
    
    def handle_mouse_press(self, event: QMouseEvent, item: QTreeWidgetItem):
        """Handle mouse press for selection."""
        if not item:
            return
        
        modifiers = event.modifiers()
        
        if modifiers & Qt.ControlModifier:
            # Toggle selection
            self._toggle_item_selection(item)
        elif modifiers & Qt.ShiftModifier and self._last_selected_item:
            # Range selection
            self._select_range(self._last_selected_item, item)
        else:
            # Single selection
            self.tree_widget.clearSelection()
            self.tree_widget.setCurrentItem(item)
        
        self._last_selected_item = item
        self._selection_modified = True
    
    def _toggle_item_selection(self, item: QTreeWidgetItem):
        """Toggle selection of a single item."""
        if item.isSelected():
            self.tree_widget.setItemSelected(item, False)
        else:
            self.tree_widget.setItemSelected(item, True)
            self.tree_widget.setCurrentItem(item)
    
    def _select_range(self, start_item: QTreeWidgetItem, end_item: QTreeWidgetItem):
        """Select a range of items between start and end."""
        if start_item.treeWidget() != self.tree_widget or end_item.treeWidget() != self.tree_widget:
            return
        
        # Get all top-level items
        root_items = []
        for i in range(self.tree_widget.topLevelItemCount()):
            root_items.append(self.tree_widget.topLevelItem(i))
            self._collect_children(self.tree_widget.topLevelItem(i), root_items)
        
        # Find indices of start and end items
        try:
            start_idx = root_items.index(start_item)
            end_idx = root_items.index(end_item)
        except ValueError:
            return
        
        # Select range
        min_idx = min(start_idx, end_idx)
        max_idx = max(start_idx, end_idx)
        
        for i in range(min_idx, max_idx + 1):
            item = root_items[i]
            self.tree_widget.setItemSelected(item, True)
    
    def _collect_children(self, item: QTreeWidgetItem, items_list: List[QTreeWidgetItem]):
        """Recursively collect all children of an item."""
        for i in range(item.childCount()):
            child = item.child(i)
            items_list.append(child)
            self._collect_children(child, items_list)
    
    def clear_selection(self):
        """Clear all selection."""
        self.tree_widget.clearSelection()
        self._last_selected_item = None
    
    def select_all(self):
        """Select all items."""
        items = []
        for i in range(self.tree_widget.topLevelItemCount()):
            self._collect_children(self.tree_widget.topLevelItem(i), items)
        
        for item in items:
            self.tree_widget.setItemSelected(item, True)
    
    def invert_selection(self):
        """Invert current selection."""
        items = []
        for i in range(self.tree_widget.topLevelItemCount()):
            self._collect_children(self.tree_widget.topLevelItem(i), items)
        
        for item in items:
            self.tree_widget.setItemSelected(item, not item.isSelected())
    
    def is_selecting(self) -> bool:
        """Check if selection was modified."""
        return self._selection_modified
    
    def reset_selection_state(self):
        """Reset selection state."""
        self._selection_modified = False
        self._last_selected_item = None
