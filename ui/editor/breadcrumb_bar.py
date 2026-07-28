"""
Breadcrumb Navigation Bar — v1.0

Professional breadcrumb navigation for IDE editor.
Displays: WorkspaceFolder → Subfolder → Current File → Current Symbol
Supports clickable navigation to any level.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QMenu
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QAction
from pathlib import Path


class BreadcrumbPath(QLabel):
    """A clickable path segment in the breadcrumb."""
    
    clicked = Signal(str, str)  # (path, segment_type)
    
    def __init__(self, text: str, path: str = None, segment_type: str = "file"):
        super().__init__(text)
        self.path = path
        self.segment_type = segment_type
        self._hover = False
        self._active = False
        
    def enterEvent(self, event):
        self._hover = True
        self._update_style()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hover = False
        self._update_style()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.path, self.segment_type)
        elif event.button() == Qt.RightButton:
            # Show context menu
            self._show_context_menu(event.globalPos())
        super().mousePressEvent(event)
        
    def _update_style(self):
        from ui.design_system import get_design_system
        p = get_design_system().palette
        if self._active:
            self.setStyleSheet(f"""
                QLabel {{
                    color: {p.accent};
                    font-weight: 600;
                    padding: 2px 8px;
                    border-radius: 4px;
                    background-color: rgba(79, 142, 247, 0.14);
                }}
            """)
        elif self._hover:
            self.setStyleSheet(f"""
                QLabel {{
                    color: {p.accent};
                    padding: 2px 8px;
                    border-radius: 4px;
                    background-color: {p.surface_hover};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLabel {{
                    color: {p.text_secondary};
                    padding: 2px 8px;
                }}
            """)
            
    def _show_context_menu(self, pos):
        """Show context menu for path segment."""
        menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.clicked.emit(self.path, self.segment_type))
        menu.addAction(open_action)
        
        if self.path:
            menu.addSeparator()
            
            open_folder_action = QAction("Open Folder", self)
            open_folder_action.triggered.connect(lambda: self.clicked.emit(str(Path(self.path).parent), "folder"))
            menu.addAction(open_folder_action)
            
            copy_path_action = QAction("Copy Path", self)
            copy_path_action.triggered.connect(lambda: self._copy_path())
            menu.addAction(copy_path_action)
            
            menu.addSeparator()
            
            reveal_action = QAction("Reveal in Explorer", self)
            reveal_action.triggered.connect(lambda: self._reveal_in_explorer())
            menu.addAction(reveal_action)
            
        menu.exec_(pos)
        
    def _copy_path(self):
        """Copy path to clipboard."""
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWidgets import QApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.path)
        
    def _reveal_in_explorer(self):
        """Reveal file in system file explorer."""
        import subprocess
        import os
        import platform
        
        if platform.system() == "Windows":
            subprocess.run(['explorer', '/select,', self.path])
        elif platform.system() == "Darwin":
            subprocess.run(['open', '-R', self.path])
        else:
            subprocess.run(['xdg-open', os.path.dirname(self.path)])
            
    def set_active(self, active: bool):
        """Set active state."""
        self._active = active
        self._update_style()


class BreadcrumbNavigation(QWidget):
    """Professional breadcrumb navigation bar."""
    
    path_navigated = Signal(str, str)  # (path, segment_type)
    symbol_selected = Signal(str)  # symbol_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._current_symbol = None
        self._layout = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout."""
        from ui.design_system import get_design_system
        p = get_design_system().palette

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 4, 12, 4)
        self._layout.setSpacing(2)
        self._layout.setAlignment(Qt.AlignLeft)
        
        self.setStyleSheet(f"""
            BreadcrumbNavigation {{
                background-color: {p.editor_bg};
                border-bottom: 1px solid {p.border};
            }}
        """)
        
    def update_breadcrumbs(self, file_path: str = None, symbol_name: str = None):
        """Update breadcrumb display."""
        if not file_path:
            self.clear()
            return
            
        self.clear()
        
        path = Path(file_path)
        workspace_root = None
        
        # Get workspace root (from environment or default)
        import os
        workspace_root = os.environ.get('WORKSPACE_ROOT', None)
        if workspace_root:
            workspace_root = Path(workspace_root)
        else:
            # Use parent directory as workspace root for now
            workspace_root = path.parent
        
        # Parse path into segments
        segments = []
        try:
            relative_path = path.relative_to(workspace_root)
            segments.append(("Workspace", str(workspace_root), "workspace"))
            segments.extend([
                (str(seg), str(Path(*path.parts[1:i+1])), "folder")
                for i, seg in enumerate(relative_path.parts[:-1])
            ])
            segments.append((path.name, str(path), "file"))
        except ValueError:
            # Path is not relative to workspace root
            segments.append((path.name, str(path), "file"))
        
        # Add breadcrumb segments
        for i, (name, full_path, seg_type) in enumerate(segments):
            if i > 0:
                # Add separator
                from ui.design_system import get_design_system
                p = get_design_system().palette
                separator = QLabel("›")
                separator.setStyleSheet(f"color: {p.text_tertiary}; padding: 0 4px; font-weight: 600;")
                self._layout.addWidget(separator)
            
            breadcrumb = BreadcrumbPath(name, full_path, seg_type)
            breadcrumb.clicked.connect(self._on_breadcrumb_clicked)
            self._layout.addWidget(breadcrumb)
        
        # Add current symbol if available
        if symbol_name:
            if segments:
                from ui.design_system import get_design_system
                p = get_design_system().palette
                separator = QLabel("›")
                separator.setStyleSheet(f"color: {p.text_tertiary}; padding: 0 4px; font-weight: 600;")
                self._layout.addWidget(separator)
            
            symbol_label = BreadcrumbPath(symbol_name, symbol_name, "symbol")
            symbol_label.set_active(True)
            symbol_label.clicked.connect(self._on_symbol_clicked)
            self._layout.addWidget(symbol_label)
        
        self._current_path = file_path
        self._current_symbol = symbol_name
        
    def clear(self):
        """Clear all breadcrumb segments."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
    def _on_breadcrumb_clicked(self, path: str, segment_type: str):
        """Handle breadcrumb click."""
        self.path_navigated.emit(path, segment_type)
        
    def _on_symbol_clicked(self, symbol_name: str, segment_type: str):
        """Handle symbol click."""
        self.symbol_selected.emit(symbol_name)
        
    def set_workspace(self, workspace_path: str):
        """Set workspace root path."""
        import os
        os.environ['WORKSPACE_ROOT'] = workspace_path
