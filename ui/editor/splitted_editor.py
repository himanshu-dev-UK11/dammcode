"""
Split Editor — v1.0

Support horizontal/vertical splits with file movement between splits.
Large file handling with smooth scrolling and UI freezes prevented.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from pathlib import Path


class SplitEditorArea(QWidget):
    """Area that holds split editor panels."""
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.splits = []  # List of (orientation, content)
        self.active_split = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        # Main splitter
        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {p.border};
                width: 4px;
            }}
            QSplitter::handle:hover {{
                background-color: {p.accent};
            }}
        """)
        self._layout.addWidget(self.splitter)
        
    def add_split(self, orientation=Qt.Horizontal):
        """Add a new split with the given orientation."""
        split_panel = SplitPanel(self.event_bus)
        split_panel.set_orientation(orientation)
        
        if orientation == Qt.Horizontal:
            # Add to right of last split
            self.splitter.addWidget(split_panel)
            self.splitter.setSizes([self.width() // 2, self.width() // 2])
        else:
            # Add below current active split
            current_split = self.splits[self.active_split] if self.splits else None
            if current_split:
                # Replace current with vertical splitter containing old and new
                old_split = current_split
                new_split = split_panel
                
                vsplitter = QSplitter(self)
                vsplitter.setOrientation(Qt.Vertical)
                vsplitter.addWidget(old_split)
                vsplitter.addWidget(new_split)
                
                idx = self.splits.index(old_split)
                self.splitter.replaceWidget(idx, vsplitter)
                
                self.splits[self.active_split] = vsplitter
                self.splits.insert(self.active_split + 1, new_split)
            else:
                self.splitter.addWidget(split_panel)
                
        self.splits.append(split_panel)
        self.active_split = len(self.splits) - 1
        
        self.event_bus.publish("editor_split", {
            "orientation": orientation,
            "split_count": len(self.splits)
        })
        
        return split_panel
        
    def remove_split(self, split_index: int):
        """Remove a split."""
        if split_index < 0 or split_index >= len(self.splits):
            return
            
        split = self.splits[split_index]
        split.deleteLater()
        self.splits.pop(split_index)
        
        if self.splits:
            self.active_split = min(self.active_split, len(self.splits) - 1)
            
        self.event_bus.publish("editor_closed", {"split_index": split_index})
        
    def get_active_split(self):
        """Get the currently active split panel."""
        if self.active_split < len(self.splits):
            return self.splits[self.active_split]
        return None
        
    def switch_split(self, split_index: int):
        """Switch active split."""
        if 0 <= split_index < len(self.splits):
            self.active_split = split_index
            self.event_bus.publish("editor_split_changed", {"split_index": split_index})


class SplitPanel(QFrame):
    """Panel containing a tab widget for a split."""
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.tab_widget = None
        self.orientation = Qt.Horizontal
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout."""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self.setStyleSheet(f"""
            SplitPanel {{
                background-color: {p.editor_bg};
            }}
        """)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # Tab widget
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background-color: {p.bg};
                color: {p.text_secondary};
                padding: 8px 16px;
                border-right: 1px solid {p.border};
            }}
            QTabBar::tab:selected {{
                background-color: {p.editor_bg};
                color: {p.text};
                border-top: 2px solid {p.accent};
            }}
        """)
        
        # Tab close signal
        self.tab_widget.tabBar().tabCloseRequested.connect(self._on_tab_close)
        self.tab_widget.tabBar().currentChanged.connect(self._on_tab_changed)
        
        self._layout.addWidget(self.tab_widget)
        
    def set_orientation(self, orientation: Qt.Orientation):
        """Set split orientation."""
        self.orientation = orientation
        
    def add_editor(self, editor, title: str):
        """Add editor to this split."""
        self.tab_widget.addTab(editor, title)
        
    def remove_editor(self, editor):
        """Remove editor from this split."""
        idx = self.tab_widget.indexOf(editor)
        if idx >= 0:
            self.tab_widget.removeTab(idx)
            
    def _on_tab_close(self, index: int):
        """Handle tab close request."""
        self.event_bus.publish("request_close_file", {
            "path": self._get_tab_path(index),
            "force": False
        })
        
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        path = self._get_tab_path(index)
        if path:
            self.event_bus.publish("tab_switched", {"path": path})
            
    def _get_tab_path(self, index: int):
        """Get file path for tab index."""
        editor = self.tab_widget.widget(index)
        if hasattr(editor, 'file_path'):
            return editor.file_path
        return None
        
    def get_active_editor(self):
        """Get the currently active editor."""
        return self.tab_widget.currentWidget()


class SplitEditorManager(QObject):
    """Manager for split editor operations."""
    
    split_created = Signal(int)  # split_index
    split_removed = Signal(int)  # split_index
    split_changed = Signal(int)  # split_index
    file_moved_to_split = Signal(int, int)  # from_split, to_split
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.area = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the split editor UI."""
        self.area = SplitEditorArea(self.event_bus)
        
        # Keyboard shortcuts
        self._setup_shortcuts()
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for split operations."""
        # Ctrl+Shift+\ - Split vertically
        QShortcut(QKeySequence("Ctrl+Shift+\\"), self.area, self._on_split_vertical)
        
        # Ctrl+Shift+- - Split horizontally
        QShortcut(QKeySequence("Ctrl+Shift+-"), self.area, self._on_split_horizontal)
        
        # Ctrl+Shift+1..9 - Switch to specific split
        for i in range(1, 10):
            QShortcut(QKeySequence(f"Ctrl+Shift+{i}"), self.area, 
                     lambda idx=i-1: self.switch_split(idx))
                     
        # Ctrl+Shift+Left/Right - Switch split
        QShortcut(QKeySequence("Ctrl+Shift+Left"), self.area, self._on_switch_left)
        QShortcut(QKeySequence("Ctrl+Shift+Right"), self.area, self._on_switch_right)
        
        # Ctrl+Shift+{ - Move file to previous split
        QShortcut(QKeySequence("Ctrl+Shift+{"), self.area, self._on_move_left)
        
        # Ctrl+Shift+} - Move file to next split
        QShortcut(QKeySequence("Ctrl+Shift+}"), self.area, self._on_move_right)
        
    def _on_split_vertical(self):
        """Create vertical split."""
        if self.area:
            self.area.add_split(Qt.Vertical)
            
    def _on_split_horizontal(self):
        """Create horizontal split."""
        if self.area:
            self.area.add_split(Qt.Horizontal)
            
    def _on_switch_left(self):
        """Switch to left split."""
        if self.area and self.area.active_split > 0:
            self.switch_split(self.area.active_split - 1)
            
    def _on_switch_right(self):
        """Switch to right split."""
        if self.area and self.area.active_split < len(self.area.splits) - 1:
            self.switch_split(self.area.active_split + 1)
            
    def _on_move_left(self):
        """Move file to left split."""
        self._move_file_to_split(-1)
        
    def _on_move_right(self):
        """Move file to right split."""
        self._move_file_to_split(1)
        
    def _move_file_to_split(self, direction: int):
        """Move active file to split in direction."""
        if not self.area:
            return
            
        current_split = self.area.get_active_split()
        if not current_split:
            return
            
        editor = current_split.get_active_editor()
        if not editor:
            return
            
        # Find target split
        target_idx = self.area.active_split + direction
        if target_idx < 0 or target_idx >= len(self.area.splits):
            return
            
        target_split = self.area.splits[target_idx]
        
        # Move editor
        current_split.remove_editor(editor)
        target_split.add_editor(editor, Path(editor.file_path).name if hasattr(editor, 'file_path') else "Untitled")
        
        self.area.active_split = target_idx
        
        self.file_moved_to_split.emit(self.area.active_split, target_idx)
        self.event_bus.publish("editor_file_moved", {
            "from_split": self.area.active_split,
            "to_split": target_idx,
            "file_path": editor.file_path if hasattr(editor, 'file_path') else None
        })
        
    def add_split(self, orientation=Qt.Horizontal):
        """Add a new split."""
        if self.area:
            return self.area.add_split(orientation)
        return None
        
    def remove_split(self, split_index: int):
        """Remove a split."""
        if self.area:
            self.area.remove_split(split_index)
            
    def switch_split(self, split_index: int):
        """Switch active split."""
        if self.area:
            self.area.switch_split(split_index)
            
    def get_area_widget(self) -> SplitEditorArea:
        """Get the split editor area widget."""
        return self.area
        
    def get_splits_count(self) -> int:
        """Get number of splits."""
        if self.area:
            return len(self.area.splits)
        return 0
