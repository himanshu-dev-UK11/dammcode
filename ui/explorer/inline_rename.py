"""
Inline Rename Manager — v2.2

Manages inline renaming of files and folders in the Explorer.
Press F2 to rename directly in the Explorer with validation.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QWidget, QLineEdit, QStyle, QStyleOptionButton
from PySide6.QtCore import Qt, Signal, QEvent, QRect
from PySide6.QtGui import QFont
from core.file_operations import FileOperations
from core.logger import setup_logger

logger = setup_logger(__name__)


class InlineRenameEditor(QLineEdit):
    """Inline editor for renaming files/folders."""
    
    finished = Signal(str, bool)  # new_name, success
    
    def __init__(self, initial_name: str, parent: QWidget = None):
        super().__init__(parent)
        self.initial_name = initial_name
        
        # Setup editor
        self.setText(initial_name)
        self.selectAll()
        self.setFont(QFont("JetBrains Mono", 11))
        
        # Style
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #3B82F6;
                border-radius: 2px;
                padding: 2px 8px;
                selection-background-color: #3B82F6;
                selection-color: #FFFFFF;
            }
        """)
        
        # Event filter for escape and enter
        self.installEventFilter(self)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Handle key events for the editor."""
        if event.type() == QEvent.KeyPress:
            key = event.key()
            
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                self._finish(True)
                return True
            
            elif key == Qt.Key_Escape:
                self._finish(False)
                return True
            
            elif key == Qt.Key_Tab:
                self._finish(True)
                return True
        
        return super().eventFilter(obj, event)
    
    def _finish(self, success: bool):
        """Finish the rename operation."""
        self.finished.emit(self.text().strip(), success)


class InlineRenameManager:
    """
    Manages inline file/folder renaming in the Explorer.
    Press F2 to rename directly, Cancel with Escape.
    """
    
    def __init__(self, event_bus, file_ops: FileOperations):
        self.event_bus = event_bus
        self.file_ops = file_ops
        self._current_rename_editor: Optional[InlineRenameEditor] = None
        self._current_rename_path: Optional[Path] = None
    
    def start_rename(self, path: Path, parent_widget: QWidget) -> InlineRenameEditor:
        """Start renaming a file/folder."""
        # Stop any existing rename
        if self._current_rename_editor:
            self.stop_rename()
        
        self._current_rename_path = path
        
        # Create editor
        editor = InlineRenameEditor(path.name, parent_widget)
        editor.finished.connect(self._on_rename_finished)
        
        # Store reference
        self._current_rename_editor = editor
        
        return editor
    
    def stop_rename(self):
        """Stop current rename operation."""
        if self._current_rename_editor:
            self._current_rename_editor.deleteLater()
            self._current_rename_editor = None
            self._current_rename_path = None
    
    def _on_rename_finished(self, new_name: str, success: bool):
        """Handle rename completion."""
        if not success or not self._current_rename_path:
            self.stop_rename()
            return
        
        # Validate new name
        if not new_name:
            self.stop_rename()
            return
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(c in new_name for c in invalid_chars):
            logger.warning(f"Invalid characters in filename: {new_name}")
            self.stop_rename()
            return
        
        # Check if name changed
        if new_name == self._current_rename_path.name:
            self.stop_rename()
            return
        
        # Check if target exists
        new_path = self._current_rename_path.parent / new_name
        if new_path.exists():
            logger.warning(f"File already exists: {new_path}")
            self.stop_rename()
            return
        
        # Perform rename
        try:
            result = self.file_ops.rename(self._current_rename_path, new_name)
            if result:
                logger.info(f"Renamed: {self._current_rename_path} -> {result}")
                self.event_bus.publish("file_renamed", {
                    "old_path": str(self._current_rename_path),
                    "new_path": str(result)
                })
        except Exception as e:
            logger.error(f"Failed to rename: {e}")
        
        self.stop_rename()
    
    def is_renaming(self) -> bool:
        """Check if a rename operation is in progress."""
        return self._current_rename_editor is not None
    
    def get_current_rename_path(self) -> Optional[Path]:
        """Get the currently renaming path."""
        return self._current_rename_path
