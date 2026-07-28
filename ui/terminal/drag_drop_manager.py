"""
Terminal Drag & Drop Manager — v2.1

Supports dragging and dropping terminal tabs for reordering and moving between split groups.
"""
from PySide6.QtWidgets import QTabBar, QTableWidget, QAbstractItemView
from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal, QEvent
from PySide6.QtGui import QDrag, QPixmap
from typing import Dict, List, Optional
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalMimeData(QMimeData):
    """Custom MIME data for terminal drag operations."""
    
    MIME_TYPE = "application/x-terminal-session"
    
    def __init__(self, session_id: str, source_group: str = None):
        super().__init__()
        self.session_id = session_id
        self.source_group = source_group
        self.setData(self.MIME_TYPE, session_id.encode('utf-8'))


class DragDropManager:
    """
    Manages drag and drop operations for terminal tabs.
    Supports:
    - Drag terminal tabs to reorder
    - Move tabs between split groups
    """
    
    # Signals
    tab_dropped = Signal(str, str, int)  # session_id, target_group, target_index
    tab_reordered = Signal(str, int, int)  # session_id, old_index, new_index
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._dragged_session_id: str = None
        self._drag_source_group: str = None
        self._drag_start_index: int = -1
    
    def start_drag(self, session_id: str, source_group: str, index: int) -> QDrag:
        """Start a drag operation."""
        self._dragged_session_id = session_id
        self._drag_source_group = source_group
        self._drag_start_index = index
        
        drag = QDrag(source=None)
        mime_data = TerminalMimeData(session_id, source_group)
        drag.setMimeData(mime_data)
        
        # Create a simple visual representation
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        return drag
    
    def handle_drop(self, mime_data: QMimeData, target_group: str, target_index: int) -> bool:
        """Handle a drop operation."""
        if not mime_data.hasFormat(TerminalMimeData.MIME_TYPE):
            return False
        
        session_id = mime_data.data(TerminalMimeData.MIME_TYPE).data().decode('utf-8')
        
        if self._drag_source_group == target_group:
            # Reorder within same group
            if self._drag_start_index != target_index:
                self.tab_reordered.emit(session_id, self._drag_start_index, target_index)
                self.event_bus.publish("terminal_tab_reordered", {
                    "session_id": session_id,
                    "source_group": target_group,
                    "old_index": self._drag_start_index,
                    "new_index": target_index
                })
        else:
            # Move between groups
            self.tab_dropped.emit(session_id, target_group, target_index)
            self.event_bus.publish("terminal_tab_moved_to_group", {
                "session_id": session_id,
                "source_group": self._drag_source_group,
                "target_group": target_group,
                "target_index": target_index
            })
        
        return True
    
    def cancel_drag(self):
        """Cancel the current drag operation."""
        self._dragged_session_id = None
        self._drag_source_group = None
        self._drag_start_index = -1
    
    def is_dragging(self) -> bool:
        """Check if a drag operation is in progress."""
        return self._dragged_session_id is not None
    
    def get_dragged_session(self) -> Optional[str]:
        """Get the currently dragged session ID."""
        return self._dragged_session_id
