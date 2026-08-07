"""
Open Editors Manager — v2.3

Manages the Open Editors section in the Explorer.
Displays: Open files, Unsaved indicator, Pinned tabs, Modified indicator
"""
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon
from core.logger import setup_logger

logger = setup_logger(__name__)


class OpenEditor:
    """Represents an open editor tab."""
    
    def __init__(self, path: Path, name: str = None):
        self.path = path
        self.name = name or path.name
        self.is_pinned = False
        self.is_modified = False
        self.is_active = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "name": self.name,
            "is_pinned": self.is_pinned,
            "is_modified": self.is_modified,
            "is_active": self.is_active,
        }


class OpenEditorsManager:
    """
    Manages open editor tabs in the Explorer.
    Tracks open files, unsaved changes, pinned tabs, and active editor.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._editors: List[OpenEditor] = []
        self._active_editor: Optional[OpenEditor] = None
    
    def add_editor(self, path: Path):
        """Add an open editor."""
        # Remove if already exists
        self.remove_editor(path)
        
        editor = OpenEditor(path)
        self._editors.append(editor)
        self._active_editor = editor
        
        self.event_bus.publish("open_editors_updated", {"editors": [e.to_dict() for e in self._editors]})
    
    def remove_editor(self, path: Path):
        """Remove an editor."""
        path_str = str(path.resolve())
        for i, editor in enumerate(self._editors):
            if str(editor.path.resolve()) == path_str:
                self._editors.pop(i)
                if self._active_editor and str(self._active_editor.path.resolve()) == path_str:
                    self._active_editor = None
                self.event_bus.publish("open_editors_updated", {"editors": [e.to_dict() for e in self._editors]})
                return
    
    def set_modified(self, path: Path, modified: bool = True):
        """Mark an editor as modified."""
        path_str = str(path.resolve())
        for editor in self._editors:
            if str(editor.path.resolve()) == path_str:
                editor.is_modified = modified
                self.event_bus.publish("open_editors_updated", {"editors": [e.to_dict() for e in self._editors]})
                return
    
    def set_pinned(self, path: Path, pinned: bool = True):
        """Pin or unpin an editor."""
        path_str = str(path.resolve())
        for editor in self._editors:
            if str(editor.path.resolve()) == path_str:
                editor.is_pinned = pinned
                # Reorder to keep pinned items at top
                self._editors.remove(editor)
                if pinned:
                    self._editors.insert(0, editor)
                else:
                    self._editors.append(editor)
                self.event_bus.publish("open_editors_updated", {"editors": [e.to_dict() for e in self._editors]})
                return
    
    def set_active(self, path: Path):
        """Set active editor."""
        path_str = str(path.resolve())
        for editor in self._editors:
            editor.is_active = str(editor.path.resolve()) == path_str
            if str(editor.path.resolve()) == path_str:
                self._active_editor = editor
        
        self.event_bus.publish("open_editors_updated", {"editors": [e.to_dict() for e in self._editors]})
    
    def get_editors(self) -> List[OpenEditor]:
        """Get all open editors."""
        return self._editors.copy()
    
    def get_active_editor(self) -> Optional[OpenEditor]:
        """Get active editor."""
        return self._active_editor
    
    def get_pinned_editors(self) -> List[OpenEditor]:
        """Get pinned editors."""
        return [e for e in self._editors if e.is_pinned]
    
    def has_unsaved_changes(self) -> bool:
        """Check if any editor has unsaved changes."""
        return any(e.is_modified for e in self._editors)


class OpenEditorsWidget(QWidget):
    """Widget for displaying open editors."""
    
    editor_clicked = Signal(str)  # path
    editor_close_requested = Signal(str)  # path
    editor_pin_requested = Signal(str, bool)  # path, pinned
    
    def __init__(self, editors_manager: OpenEditorsManager, parent=None):
        super().__init__(parent)
        self.editors_manager = editors_manager
        self._setup_ui()
        self._refresh_editors()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_label = QLabel("Open Editors")
        header_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: #8E8E98;
            letter-spacing: 0.8px;
        """)
        header_layout.addWidget(header_label)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d30;
                color: #8E8E98;
                border: none;
                padding: 2px 8px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #3d3d40;
                color: #E2E2E6;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Editor list
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)
    
    def _refresh_editors(self):
        """Refresh the open editors list."""
        self.tree.clear()
        
        editors = self.editors_manager.get_editors()
        
        for editor in editors:
            item = QTreeWidgetItem([editor.name])
            item.setData(0, Qt.UserRole, str(editor.path))
            
            # Add indicators
            indicators = []
            if editor.is_modified:
                indicators.append("●")
            if editor.is_pinned:
                indicators.append("📌")
            if editor.is_active:
                indicators.append("➤")
            
            if indicators:
                item.setText(0, f"{' '.join(indicators)} {editor.name}")
            else:
                item.setText(0, editor.name)
            
            # Set colors
            if editor.is_modified:
                item.setForeground(0, self.tree.palette().color(0).dark(150))
            
            self.tree.addTopLevelItem(item)
    
    def _on_item_clicked(self, item, column):
        """Handle item click."""
        path = item.data(0, Qt.UserRole)
        if path:
            self.editor_clicked.emit(path)
    
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on item."""
        path = item.data(0, Qt.UserRole)
        if path:
            # Toggle pin on double-click
            editors = self.editors_manager.get_editors()
            for editor in editors:
                if str(editor.path.resolve()) == path:
                    self.editors_manager.set_pinned(Path(path), not editor.is_pinned)
                    self._refresh_editors()
                    break
    
    def _on_clear_all(self):
        """Clear all editors."""
        editors = self.editors_manager.get_editors()
        for editor in editors:
            self.editor_close_requested.emit(str(editor.path))