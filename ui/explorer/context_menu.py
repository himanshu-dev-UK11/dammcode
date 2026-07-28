"""
Context Menu Manager — v2.2

Manages the professional context menu for the Explorer.
Supports: Open, Rename, Duplicate, Delete, Copy Path, Reveal, New File, New Folder, Properties
"""
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QAction
from core.file_operations import FileOperations
from ui.explorer.copy_path import CopyPathManager
from core.logger import setup_logger

logger = setup_logger(__name__)


class ContextMenuManager:
    """
    Manages the professional context menu for the Explorer.
    Provides: Open, Rename, Duplicate, Delete, Copy Path, Reveal, New File, New Folder, Properties
    """
    
    def __init__(self, event_bus, file_ops: FileOperations, copy_path_manager: CopyPathManager):
        self.event_bus = event_bus
        self.file_ops = file_ops
        self.copy_path_manager = copy_path_manager
        self._current_path: Optional[Path] = None
        self._is_directory = False
    
    def set_current_path(self, path: Path, is_dir: bool = False):
        """Set the current path for menu operations."""
        self._current_path = path
        self._is_directory = is_dir
    
    def create_context_menu(self, position) -> QMenu:
        """Create the context menu."""
        if not self._current_path:
            return self._create_empty_menu()
        
        menu = QMenu()
        
        # Open actions
        if self._current_path.exists():
            if self._current_path.is_file():
                open_action = QAction("📂 Open", menu)
                open_action.triggered.connect(lambda: self._open_file(self._current_path))
                menu.addAction(open_action)
                
                open_with_action = QAction("📂 Open With...", menu)
                open_with_action.triggered.connect(lambda: self._open_with(self._current_path))
                menu.addAction(open_with_action)
                
                menu.addSeparator()
            
            # Rename
            rename_action = QAction("✏️ Rename", menu)
            rename_action.triggered.connect(lambda: self._rename(self._current_path))
            menu.addAction(rename_action)
            
            # Duplicate
            duplicate_action = QAction("📋 Duplicate", menu)
            duplicate_action.triggered.connect(lambda: self._duplicate(self._current_path))
            menu.addAction(duplicate_action)
            
            menu.addSeparator()
            
            # Delete
            delete_action = QAction("🗑️ Delete", menu)
            delete_action.triggered.connect(lambda: self._delete(self._current_path))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # Copy Path
            copy_menu = menu.addMenu("📋 Copy Path")
            self.copy_path_manager.create_copy_menu(self._current_path, copy_menu)
            
            menu.addSeparator()
            
            # Reveal
            reveal_action = QAction("📂 Reveal in Explorer", menu)
            reveal_action.triggered.connect(lambda: self._reveal(self._current_path))
            menu.addAction(reveal_action)
            
            # Open Terminal
            if self._is_directory:
                menu.addSeparator()
                
                terminal_menu = menu.addMenu("💻 Open Terminal Here")
                
                terminal_cmd = QAction("Windows CMD", terminal_menu)
                terminal_cmd.triggered.connect(lambda: self._open_terminal(self._current_path, "cmd"))
                terminal_menu.addAction(terminal_cmd)
                
                terminal_ps = QAction("PowerShell", terminal_menu)
                terminal_ps.triggered.connect(lambda: self._open_terminal(self._current_path, "powershell"))
                terminal_menu.addAction(terminal_ps)
                
                terminal_bash = QAction("Git Bash", terminal_menu)
                terminal_bash.triggered.connect(lambda: self._open_terminal(self._current_path, "bash"))
                terminal_menu.addAction(terminal_bash)
                
                terminal_wsl = QAction("WSL", terminal_menu)
                terminal_wsl.triggered.connect(lambda: self._open_terminal(self._current_path, "wsl"))
                terminal_menu.addAction(terminal_wsl)
        
        menu.addSeparator()
        
        # New File / New Folder (if directory)
        if self._is_directory:
            new_file_action = QAction("📄 New File", menu)
            new_file_action.triggered.connect(lambda: self._new_file(self._current_path))
            menu.addAction(new_file_action)
            
            new_folder_action = QAction("📁 New Folder", menu)
            new_folder_action.triggered.connect(lambda: self._new_folder(self._current_path))
            menu.addAction(new_folder_action)
            
            menu.addSeparator()
        
        # Properties
        properties_action = QAction("📋 Properties", menu)
        properties_action.triggered.connect(lambda: self._properties(self._current_path))
        menu.addAction(properties_action)
        
        return menu
    
    def _create_empty_menu(self) -> QMenu:
        """Create empty context menu."""
        menu = QMenu()
        
        new_file_action = QAction("📄 New File", menu)
        menu.addAction(new_file_action)
        
        new_folder_action = QAction("📁 New Folder", menu)
        menu.addAction(new_folder_action)
        
        menu.addSeparator()
        
        properties_action = QAction("📋 Properties", menu)
        menu.addAction(properties_action)
        
        return menu
    
    def _open_file(self, path: Path):
        """Open a file."""
        self.event_bus.publish("file_open_requested", {"path": str(path)})
    
    def _open_with(self, path: Path):
        """Open file with specific application."""
        self.event_bus.publish("file_open_with_requested", {"path": str(path)})
    
    def _rename(self, path: Path):
        """Rename a file/folder."""
        result = self.file_ops.rename(path)
        if result:
            self.event_bus.publish("file_renamed", {
                "old_path": str(path),
                "new_path": str(result)
            })
    
    def _duplicate(self, path: Path):
        """Duplicate a file/folder."""
        result = self.file_ops.duplicate(path)
        if result:
            self.event_bus.publish("file_duplicated", {
                "source": str(path),
                "destination": str(result)
            })
    
    def _delete(self, path: Path):
        """Delete a file/folder."""
        if self.file_ops.delete(path):
            self.event_bus.publish("file_deleted", {"path": str(path)})
    
    def _copy_path(self, path: Path, format_type: str):
        """Copy path to clipboard."""
        self.copy_path_manager.copy_path(path, format_type)
    
    def _reveal(self, path: Path):
        """Reveal file in system explorer."""
        self.file_ops.reveal_in_explorer(path)
    
    def _open_terminal(self, path: Path, shell: str):
        """Open terminal in directory."""
        self.event_bus.publish("terminal_created", {
            "working_directory": str(path),
            "shell": shell
        })
    
    def _new_file(self, parent_dir: Path):
        """Create a new file."""
        result = self.file_ops.create_file(parent_dir)
        if result:
            self.event_bus.publish("file_created", {"path": str(result)})
    
    def _new_folder(self, parent_dir: Path):
        """Create a new folder."""
        result = self.file_ops.create_folder(parent_dir)
        if result:
            self.event_bus.publish("folder_created", {"path": str(result)})
    
    def _properties(self, path: Path):
        """Show file/folder properties."""
        try:
            import os
            stat = os.stat(str(path))
            
            props = {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_directory": path.is_dir(),
            }
            
            self.event_bus.publish("properties_shown", props)
            
        except Exception as e:
            logger.error(f"Failed to get properties: {e}")
