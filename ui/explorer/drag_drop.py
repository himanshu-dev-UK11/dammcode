"""
Drag & Drop Manager — v2.2

Manages drag and drop operations for files and folders in the Explorer.
Supports: Move, Copy (with modifier), Auto expand folders
"""
from pathlib import Path
from typing import List, Optional, Set
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal
from PySide6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent
from core.file_operations import FileOperations
from core.logger import setup_logger

logger = setup_logger(__name__)


class ExplorerMimeData(QMimeData):
    """Custom MIME data for explorer drag operations."""
    
    MIME_TYPE = "application/x-explorer-file"
    
    def __init__(self, paths: List[Path]):
        super().__init__()
        self.paths = [str(p) for p in paths]
        self.setData(self.MIME_TYPE, "\n".join(self.paths).encode('utf-8'))


class DragDropManager:
    """
    Manages drag and drop operations for the file explorer.
    Supports moving files/folders, copying with modifier key, and auto-expanding.
    """
    
    # Signals
    files_dropped = Signal(list, Path)  # paths, destination
    files_moved = Signal(list, Path)  # paths, destination
    files_copied = Signal(list, Path)  # paths, destination
    
    def __init__(self, event_bus, file_ops: FileOperations, tree_widget: QTreeWidget):
        self.event_bus = event_bus
        self.file_ops = file_ops
        self.tree_widget = tree_widget
        
        # State
        self._dragged_paths: List[Path] = []
        self._drag_source_item: Optional[QTreeWidgetItem] = None
        self._is_copying = False
        
        # Configure tree widget
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(QTreeWidget.DragDrop)
        self.tree_widget.setDefaultDropAction(Qt.IgnoreAction)
    
    def start_drag(self, paths: List[Path], source_item: QTreeWidgetItem):
        """Start a drag operation."""
        self._dragged_paths = paths
        self._drag_source_item = source_item
        
        drag = QDrag(self.tree_widget)
        mime_data = ExplorerMimeData(paths)
        drag.setMimeData(mime_data)
        
        # Set pixmap
        drag.setPixmap(self.tree_widget.style().standardIcon(
            self.tree_widget.style().SP_FileIcon
        ).pixmap(32, 32))
        
        # Start drag with move action
        drop_action = drag.exec(Qt.MoveAction | Qt.CopyAction, Qt.CopyAction)
        
        # Check if copy was requested
        if drop_action == Qt.CopyAction:
            self._is_copying = True
        
        return drop_action
    
    def handle_drag_enter_event(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasFormat(ExplorerMimeData.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def handle_drag_move_event(self, event: QDragMoveEvent):
        """Handle drag move event."""
        if event.mimeData().hasFormat(ExplorerMimeData.MIME_TYPE):
            # Get drop target
            pos = event.position().toPoint()
            target_item = self.tree_widget.itemAt(pos)
            
            # Auto-expand folder if hovering over it
            if target_item and target_item.isDir():
                if not target_item.isExpanded():
                    target_item.setExpanded(True)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def handle_drop_event(self, event: QDropEvent):
        """Handle drop event."""
        if not event.mimeData().hasFormat(ExplorerMimeData.MIME_TYPE):
            event.ignore()
            return
        
        # Get drop position
        pos = event.position().toPoint()
        target_item = self.tree_widget.itemAt(pos)
        
        # Determine destination
        if target_item:
            # Get target path
            target_path_str = target_item.data(0, Qt.UserRole)
            if target_path_str:
                target_path = Path(target_path_str)
                
                # If item is a file, use parent directory
                if target_path.is_file():
                    target_path = target_path.parent
                
                # Ensure target is a directory
                if not target_path.is_dir():
                    event.ignore()
                    return
            else:
                event.ignore()
                return
        else:
            # Drop on empty space - use root
            if hasattr(self, '_root_path'):
                target_path = self._root_path
            else:
                event.ignore()
                return
        
        # Get source paths
        paths_data = event.mimeData().data(ExplorerMimeData.MIME_TYPE)
        paths_str = paths_data.data().decode('utf-8').split('\n')
        source_paths = [Path(p) for p in paths_str if p]
        
        # Filter out paths that are inside the target
        valid_paths = []
        for path in source_paths:
            try:
                path.relative_to(target_path)
                # Source is inside target - invalid
            except ValueError:
                # Source is outside target - valid
                valid_paths.append(path)
        
        if not valid_paths:
            event.ignore()
            return
        
        # Determine action (copy or move)
        is_copy = (event.dropAction() == Qt.CopyAction) or self._is_copying
        
        if is_copy:
            # Copy files
            self._copy_files(valid_paths, target_path)
            self.files_copied.emit(valid_paths, target_path)
        else:
            # Move files
            self._move_files(valid_paths, target_path)
            self.files_moved.emit(valid_paths, target_path)
        
        self._is_copying = False
        event.acceptProposedAction()
    
    def _copy_files(self, source_paths: List[Path], destination: Path):
        """Copy files to destination."""
        for source in source_paths:
            try:
                if source.is_dir():
                    # Copy directory with unique name
                    dest_dir = destination / source.name
                    counter = 1
                    while dest_dir.exists():
                        dest_dir = destination / f"{source.name}_{counter}"
                        counter += 1
                    self.file_ops.copy(source, dest_dir)
                else:
                    self.file_ops.copy(source, destination / source.name)
            except Exception as e:
                logger.error(f"Failed to copy {source}: {e}")
    
    def _move_files(self, source_paths: List[Path], destination: Path):
        """Move files to destination."""
        for source in source_paths:
            try:
                dest_path = destination / source.name
                counter = 1
                while dest_path.exists() and dest_path != source:
                    stem = source.stem
                    suffix = source.suffix
                    dest_path = destination / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                self.file_ops.move(source, dest_path)
            except Exception as e:
                logger.error(f"Failed to move {source}: {e}")
    
    def set_root_path(self, root: Path):
        """Set the root path for the tree."""
        self._root_path = root
