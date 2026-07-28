"""
File System Watcher — v1.6

Monitors workspace for file changes and emits events.
Supports:
- File created
- File modified
- File deleted
- Directory created
- Directory deleted
"""
from pathlib import Path
from typing import Set, Optional
from PySide6.QtCore import QFileSystemWatcher, QObject, Signal
from core.logger import setup_logger

logger = setup_logger(__name__)


class FileWatcher(QObject):
    """
    Watches files and directories for changes.
    Emits events through EventBus.
    """
    file_created = Signal(str)  # path
    file_modified = Signal(str)  # path
    file_deleted = Signal(str)  # path
    directory_created = Signal(str)  # path
    directory_deleted = Signal(str)  # path

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.watcher = QFileSystemWatcher()
        self.watched_files: Set[str] = set()
        self.watched_dirs: Set[str] = set()
        
        # Connect signals
        self.watcher.fileChanged.connect(self._on_file_changed)
        self.watcher.directoryChanged.connect(self._on_directory_changed)
        
    def watch_directory(self, path: Path):
        """Add a directory to watch list."""
        path_str = str(path.resolve())
        if path_str not in self.watched_dirs:
            if self.watcher.addPath(path_str):
                self.watched_dirs.add(path_str)
                logger.debug(f"Watching directory: {path_str}")
            else:
                logger.warning(f"Failed to watch directory: {path_str}")
                
    def watch_file(self, path: Path):
        """Add a file to watch list."""
        path_str = str(path.resolve())
        if path_str not in self.watched_files:
            if self.watcher.addPath(path_str):
                self.watched_files.add(path_str)
                logger.debug(f"Watching file: {path_str}")
            else:
                logger.warning(f"Failed to watch file: {path_str}")
                
    def unwatch_file(self, path: Path):
        """Remove a file from watch list."""
        path_str = str(path.resolve())
        if path_str in self.watched_files:
            self.watcher.removePath(path_str)
            self.watched_files.remove(path_str)
            logger.debug(f"Stopped watching file: {path_str}")
            
    def unwatch_directory(self, path: Path):
        """Remove a directory from watch list."""
        path_str = str(path.resolve())
        if path_str in self.watched_dirs:
            self.watcher.removePath(path_str)
            self.watched_dirs.remove(path_str)
            logger.debug(f"Stopped watching directory: {path_str}")
            
    def clear_all(self):
        """Stop watching all files and directories."""
        for path in list(self.watched_files):
            self.watcher.removePath(path)
        for path in list(self.watched_dirs):
            self.watcher.removePath(path)
        self.watched_files.clear()
        self.watched_dirs.clear()
        
    def _on_file_changed(self, path: str):
        """Handle file change event."""
        p = Path(path)
        if p.exists():
            self.file_modified.emit(path)
            self.event_bus.publish("file_changed_externally", {"path": path})
        else:
            # File was deleted
            self.file_deleted.emit(path)
            self.event_bus.publish("file_deleted_externally", {"path": path})
            self.watched_files.discard(path)
            
    def _on_directory_changed(self, path: str):
        """Handle directory change event."""
        # Directory contents changed - could be file added, deleted, or modified
        self.event_bus.publish("directory_changed", {"path": path})
