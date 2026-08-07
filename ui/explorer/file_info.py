"""
File Info Panel — v2.3

Displays file/folder information in the Explorer.
Shows: File Size, Modified Date, Created Date, Extension, Encoding, Hidden Files
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from core.logger import setup_logger
import os
from datetime import datetime

logger = setup_logger(__name__)


class FileInfo:
    """Represents file information."""
    
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.size = 0
        self.created = None
        self.modified = None
        self.extension = path.suffix
        self.mime_type = self._get_mime_type()
        self.is_hidden = path.name.startswith(".")
        self.is_file = path.is_file()
        self.is_dir = path.is_dir()
    
    def _get_mime_type(self) -> str:
        """Determine MIME type from extension."""
        extensions = {
            # Images
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".bmp": "image/bmp", ".svg": "image/svg+xml",
            # Text/Code
            ".py": "text/x-python", ".js": "text/javascript", ".ts": "text/typescript",
            ".json": "application/json", ".xml": "application/xml",
            ".html": "text/html", ".css": "text/css", ".md": "text/markdown",
            ".txt": "text/plain", ".csv": "text/csv", ".log": "text/plain",
            # Archives
            ".zip": "application/zip", ".tar": "application/x-tar",
            ".gz": "application/gzip", ".rar": "application/vnd.rar",
        }
        return extensions.get(self.extension.lower(), "application/octet-stream")
    
    def load_size(self):
        """Load file/folder size."""
        try:
            if self.is_file:
                self.size = self.path.stat().st_size
            else:
                # Calculate folder size
                self.size = sum(f.stat().st_size for f in self.path.rglob("*") if f.is_file())
        except Exception as e:
            logger.error(f"Failed to get size for {self.path}: {e}")
            self.size = 0
    
    def load_timestamps(self):
        """Load file timestamps."""
        try:
            stat = self.path.stat()
            self.created = datetime.fromtimestamp(stat.st_ctime)
            self.modified = datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            logger.error(f"Failed to get timestamps for {self.path}: {e}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "size_human": self._format_size(self.size),
            "created": str(self.created) if self.created else None,
            "modified": str(self.modified) if self.modified else None,
            "extension": self.extension,
            "mime_type": self.mime_type,
            "is_hidden": self.is_hidden,
            "is_file": self.is_file,
            "is_dir": self.is_dir,
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


class FileInfoWidget(QWidget):
    """Widget for displaying file information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_info: Optional[FileInfo] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Group box
        group = QGroupBox("File Information")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subline-offset: -4px;
                padding: 0 4px;
                color: #E2E2E6;
            }
        """)
        
        group_layout = QVBoxLayout(group)
        
        # File name
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        group_layout.addWidget(self.name_label)
        
        # File type
        self.type_label = QLabel()
        group_layout.addWidget(self.type_label)
        
        # Size
        self.size_label = QLabel()
        group_layout.addWidget(self.size_label)
        
        # Created
        self.created_label = QLabel()
        group_layout.addWidget(self.created_label)
        
        # Modified
        self.modified_label = QLabel()
        group_layout.addWidget(self.modified_label)
        
        # Extension
        self.extension_label = QLabel()
        group_layout.addWidget(self.extension_label)
        
        # Encoding
        self.encoding_label = QLabel()
        group_layout.addWidget(self.encoding_label)
        
        # Hidden indicator
        self.hidden_label = QLabel("👁️ Hidden file")
        self.hidden_label.setStyleSheet("color: #8E8E98;")
        self.hidden_label.hide()
        group_layout.addWidget(self.hidden_label)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def set_file(self, path: Path):
        """Set the file to display information for."""
        self.file_info = FileInfo(path)
        self.file_info.load_size()
        self.file_info.load_timestamps()
        
        # Update UI
        data = self.file_info.to_dict()
        
        self.name_label.setText(f"📄 {data['name']}")
        
        file_type = "Folder" if data['is_dir'] else "File"
        self.type_label.setText(f"Type: {file_type} ({data['mime_type']})")
        
        self.size_label.setText(f"Size: {data['size_human']}")
        
        if data['created']:
            self.created_label.setText(f"Created: {data['created']}")
        
        if data['modified']:
            self.modified_label.setText(f"Modified: {data['modified']}")
        
        self.extension_label.setText(f"Extension: {data['extension'] or '(none)'}")
        
        if data['is_hidden']:
            self.hidden_label.show()
        else:
            self.hidden_label.hide()
    
    def clear(self):
        """Clear the file information."""
        self.file_info = None
        self.name_label.setText("")
        self.type_label.setText("")
        self.size_label.setText("")
        self.created_label.setText("")
        self.modified_label.setText("")
        self.extension_label.setText("")
        self.hidden_label.hide()


class FileInfoManager:
    """Manages file info display in the Explorer."""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._current_path: Optional[Path] = None
        self._timer: Optional[QTimer] = None
    
    def start_auto_refresh(self):
        """Start auto-refresh timer for file info."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_info)
        self._timer.setInterval(1000)  # Refresh every second
        self._timer.start()
    
    def stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self._timer:
            self._timer.stop()
            self._timer = None
    
    def update_file_info(self, path: Path):
        """Update file info for a path."""
        self._current_path = path
    
    def _refresh_info(self):
        """Refresh current file info."""
        if self._current_path and self._current_path.exists():
            try:
                stat = self._current_path.stat()
                self.event_bus.publish("file_info_updated", {
                    "path": str(self._current_path),
                    "modified": stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Failed to refresh file info: {e}")