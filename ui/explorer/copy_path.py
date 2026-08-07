"""
Copy Path Manager — v2.2

Manages copying file/folder paths with different formats.
Supports: Relative Path, Absolute Path, File Name, Extension
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QMenu, QWidgetAction
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from core.logger import setup_logger

logger = setup_logger(__name__)


class CopyPathManager:
    """
    Manages copying file/folder paths with different formats.
    Provides: Relative Path, Absolute Path, File Name, Extension
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
    
    def copy_path(self, path: Path, format_type: str = "absolute"):
        """
        Copy a path to clipboard in the specified format.
        
        Args:
            path: The file or folder path
            format_type: One of: absolute, relative, name, extension
        """
        try:
            path = path.resolve()
            
            if format_type == "absolute":
                text = str(path)
            elif format_type == "relative":
                if hasattr(self, '_workspace_root'):
                    try:
                        text = str(path.relative_to(self._workspace_root))
                    except ValueError:
                        text = str(path)
                else:
                    text = str(path)
            elif format_type == "name":
                text = path.name
            elif format_type == "extension":
                text = path.suffix
            else:
                text = str(path)
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            logger.info(f"Copied path ({format_type}): {text}")
            self.event_bus.publish("path_copied", {
                "path": str(path),
                "format": format_type
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy path: {e}")
            return False
    
    def set_workspace_root(self, root: Path):
        """Set the workspace root for relative path calculations."""
        self._workspace_root = root
    
    def create_copy_menu(self, path: Path, parent: QWidget = None) -> QMenu:
        """Create a context menu with path copy options."""
        menu = QMenu("Copy Path", parent)
        
        # Absolute path
        action = QAction("Absolute Path", menu)
        action.triggered.connect(lambda: self.copy_path(path, "absolute"))
        menu.addAction(action)
        
        # Relative path
        action = QAction("Relative Path", menu)
        action.triggered.connect(lambda: self.copy_path(path, "relative"))
        menu.addAction(action)
        
        menu.addSeparator()
        
        # File name
        action = QAction("File Name", menu)
        action.triggered.connect(lambda: self.copy_path(path, "name"))
        menu.addAction(action)
        
        # Extension
        action = QAction("Extension", menu)
        action.triggered.connect(lambda: self.copy_path(path, "extension"))
        menu.addAction(action)
        
        return menu
    
    def copy_full_path(self, path: Path) -> bool:
        """Copy full (absolute) path."""
        return self.copy_path(path, "absolute")
    
    def copy_relative_path(self, path: Path) -> bool:
        """Copy relative path from workspace root."""
        return self.copy_path(path, "relative")
    
    def copy_file_name(self, path: Path) -> bool:
        """Copy just the file/folder name."""
        return self.copy_path(path, "name")
    
    def copy_extension(self, path: Path) -> bool:
        """Copy file extension."""
        return self.copy_path(path, "extension")
