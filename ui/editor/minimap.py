"""
Minimap — v1.0

Optional code minimap for IDE editor.
Displays a scaled-down view of the entire document with visible region highlight.
Supports click-to-navigate and smooth scrolling.
"""

from PySide6.QtWidgets import QWidget, QScrollArea, QFrame
from PySide6.QtCore import Qt, QRect, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QFontMetrics
from ui.editor.code_editor import CodeEditor


class MinimapWidget(QWidget):
    """The minimap widget that displays scaled-down code."""
    
    region_changed = Signal(QRect)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self.visible_region = QRect()
        self._hover_pos = None
        self._dragging = False
        self._drag_start_pos = None
        self._scroll_value_at_drag_start = None
        self._minimap_width = 120
        self._scale = 0.15  # Scaled down view
        
    def set_editor(self, editor: CodeEditor):
        """Set the editor to mirror."""
        self.editor = editor
        editor.blockCountChanged.connect(self.update_minimap)
        editor.updateRequest.connect(self._on_update_request)
        self.update_minimap()
        
    def minimumSizeHint(self):
        return self.sizeHint()
        
    def sizeHint(self):
        return super().sizeHint().expandedTo(self.minimumSizeHint())
        
    def update_minimap(self):
        """Update minimap content."""
        self.update()
        
    def _on_update_request(self, rect, dy):
        """Handle editor update requests."""
        if dy:
            self.scroll(0, dy)
        else:
            self.update()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.pos()
            self._scroll_value_at_drag_start = self.editor.verticalScrollBar().value()
            self._handle_click(event.pos())
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self._dragging:
            # Calculate scroll delta
            scroll_bar = self.editor.verticalScrollBar()
            max_scroll = scroll_bar.maximum()
            
            # Map minimap position to scroll value
            minimap_height = self.height()
            content_height = self._get_content_height()
            
            if content_height > minimap_height:
                delta = event.pos().y() - self._drag_start_pos.y()
                scroll_delta = int(delta * (max_scroll / minimap_height))
                new_value = max(0, min(max_scroll, self._scroll_value_at_drag_start + scroll_delta))
                scroll_bar.setValue(new_value)
                
        self._hover_pos = event.pos()
        self.update()
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)
        
    def leaveEvent(self, event):
        self._hover_pos = None
        self.update()
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        if not self.editor:
            return
            
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#181825"))
        
        # Get document dimensions
        document = self.editor.document()
        block_count = document.blockCount()
        
        # Calculate scale
        viewport_height = self.editor.viewport().height()
        content_height = self.editor.document().size().height()
        
        if content_height <= 0:
            return
            
        self._scale = self.height() / content_height
        if self._scale > 0.2:
            self._scale = 0.2
            
        # Calculate visible region in minimap coordinates
        first_visible_block = self.editor.firstVisibleBlock()
        top_offset = self.editor.blockBoundingGeometry(first_visible_block).translated(self.editor.contentOffset()).top()
        viewport_bottom = top_offset + viewport_height
        
        minimap_top = top_offset * self._scale
        minimap_height = viewport_height * self._scale
        
        self.visible_region = QRect(0, int(minimap_top), self.width(), int(minimap_height))
        
        # Draw visible region
        painter.fillRect(self.visible_region, QColor("rgba(59, 130, 246, 0.3)"))
        
        # Draw hover effect
        if self._hover_pos and self._dragging:
            hover_rect = QRect(0, self._hover_pos.y() - 10, self.width(), 20)
            painter.fillRect(hover_rect, QColor("rgba(59, 130, 246, 0.5)"))
            
        # Draw document lines (sampled)
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        
        # Calculate visible range
        top_y = self.editor.contentOffset().y()
        bottom_y = top_y + viewport_height
        
        y = top_y
        while block.isValid() and y < bottom_y:
            if block.isVisible():
                block_top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
                block_height = self.editor.blockBoundingRect(block).height()
                
                # Draw line in minimap
                minimap_y = block_top * self._scale
                minimap_height = block_height * self._scale
                
                if minimap_height >= 1:
                    painter.fillRect(4, int(minimap_y), self.width() - 8, int(minimap_height), QColor("#313244"))
                else:
                    painter.fillRect(4, int(minimap_y), self.width() - 8, 1, QColor("#313244"))
                    
                # Highlight current line
                if block_number == self.editor.textCursor().blockNumber():
                    painter.fillRect(4, int(minimap_y), self.width() - 8, int(minimap_height), QColor("rgba(59, 130, 246, 0.5)"))
                    
            block = block.next()
            y += self.editor.blockBoundingRect(block).height()
            block_number += 1
            
        # Draw scroll thumb indicator
        scroll_bar = self.editor.verticalScrollBar()
        if scroll_bar.maximum() > 0:
            page_step = scroll_bar.pageStep()
            total_size = scroll_bar.maximum() + page_step
            
            if total_size > 0:
                thumb_ratio = page_step / total_size
                thumb_height = max(30, int(self.height() * thumb_ratio))
                
                scroll_value = scroll_bar.value()
                thumb_pos = int((scroll_value / scroll_bar.maximum()) * (self.height() - thumb_height))
                
                # Draw thumb
                painter.fillRect(4, thumb_pos, self.width() - 8, thumb_height, QColor("#4B4B54"))
                
    def _get_content_height(self):
        """Get total content height."""
        if not self.editor:
            return 0
        return int(self.editor.document().size().height())
        
    def _handle_click(self, pos):
        """Handle click on minimap."""
        if not self.editor:
            return
            
        # Calculate scroll position from click
        scroll_bar = self.editor.verticalScrollBar()
        content_height = self._get_content_height()
        
        if content_height <= 0:
            return
            
        # Map minimap position to scroll value
        scroll_value = int((pos.y() / self.height()) * scroll_bar.maximum())
        scroll_value = max(0, min(scroll_bar.maximum(), scroll_value))
        
        scroll_bar.setValue(scroll_value)
        self.region_changed.emit(self.visible_region)


class MinimapPanel(QFrame):
    """Panel that contains the minimap with toggle functionality."""
    
    visibility_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible = False
        self._minimap = None
        self._toggle_button = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout."""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self.setStyleSheet(f"""
            MinimapPanel {{
                background-color: {p.editor_bg};
                border-left: 1px solid {p.border};
            }}
        """)
        
        self._layout = None
        self._minimap = MinimapWidget()
        
        # Initially hidden
        self.setVisible(False)
        self.setFixedWidth(0)
        
    def set_editor(self, editor: CodeEditor):
        """Set the editor to mirror in minimap."""
        if self._minimap:
            self._minimap.set_editor(editor)
            
    def toggle_visibility(self):
        """Toggle minimap visibility."""
        self._visible = not self._visible
        self.setVisible(self._visible)
        
        if self._visible:
            self.setFixedWidth(self._minimap._minimap_width)
        else:
            self.setFixedWidth(0)
            
        self.visibility_changed.emit(self._visible)
        
    def is_visible(self) -> bool:
        """Check if minimap is visible."""
        return self._visible
        
    def paintEvent(self, event):
        """Paint event."""
        if not self._visible:
            return
        super().paintEvent(event)
