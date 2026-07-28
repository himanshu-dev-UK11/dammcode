"""
Indent Guides — v1.0

Display indentation guides in the editor with active indent highlighting.
Supports both space and tab indentation.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, Signal, QObject
from PySide6.QtGui import QPainter, QColor


class IndentGuideOverlay(QWidget):
    """Overlay widget that draws indent guides on top of the editor."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self._enabled = True
        self._active_indent = None
        self._indent_width = 4  # Spaces per indent level
        
    def set_editor(self, editor):
        """Set the editor to draw guides for."""
        self.editor = editor
        editor.blockCountChanged.connect(self.update)
        editor.updateRequest.connect(self._on_update_request)
        
    def _on_update_request(self, rect, dy):
        """Handle editor update requests."""
        if dy:
            self.scroll(0, dy)
        else:
            self.update()
            
    def set_enabled(self, enabled: bool):
        """Enable/disable indent guides."""
        self._enabled = enabled
        self.update()
        
    def set_indent_width(self, width: int):
        """Set spaces per indent level."""
        self._indent_width = width
        self.update()
        
    def paintEvent(self, event):
        """Draw indent guides."""
        if not self._enabled or not self.editor:
            return
            
        painter = QPainter(self)
        painter.setFont(self.editor.font())
        font_metrics = painter.fontMetrics()
        
        # Get editor viewport dimensions
        viewport = self.editor.viewport()
        viewport_rect = viewport.rect()
        
        # Calculate space width
        space_width = font_metrics.horizontalAdvance(' ')
        indent_pixel_width = self._indent_width * space_width
        
        # Get visible block range
        first_block = self.editor.firstVisibleBlock()
        last_block = first_block
        
        block = first_block
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()
        
        while block.isValid() and top < viewport_rect.bottom():
            if bottom >= viewport_rect.top():
                last_block = block
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            
        # Draw indent guides for visible blocks
        block = first_block
        while block.isValid() and block.blockNumber() <= last_block.blockNumber():
            if block.isVisible():
                text = block.text()
                indent_level = self._calculate_indent(text)
                
                # Draw vertical lines for each indent level
                for level in range(1, indent_level + 1):
                    x_pos = level * indent_pixel_width
                    if x_pos < viewport.width():
                        # Check if this indent level is "active" (contains code)
                        if self._is_active_indent(block, level, indent_pixel_width):
                            painter.setPen(QColor("rgba(59, 130, 246, 0.3)"))
                            painter.drawLine(x_pos, 0, x_pos, viewport.height())
                        else:
                            painter.setPen(QColor("#313244"))
                            painter.drawLine(x_pos, 0, x_pos, viewport.height())
                            
            block = block.next()
            
    def _calculate_indent(self, text: str) -> int:
        """Calculate indentation level from text."""
        indent_level = 0
        i = 0
        while i < len(text):
            if text[i] == ' ':
                indent_level += 1
            elif text[i] == '\t':
                indent_level += self._indent_width
            else:
                break
            i += 1
            
        return indent_level // self._indent_width
        
    def _is_active_indent(self, block, level: int, indent_width: int) -> bool:
        """Check if an indent level is active (contains non-whitespace)."""
        text = block.text()
        expected_indent = level * indent_width
        
        for i, char in enumerate(text):
            if char == ' ':
                if i >= expected_indent:
                    return True
                continue
            elif char == '\t':
                # Tab counts as multiple spaces
                if i >= expected_indent:
                    return True
                continue
            else:
                # Found non-whitespace character
                return True
                
        return False
        
    def get_active_indent(self, cursor):
        """Get the active indent level for the current line."""
        text = cursor.block().text()
        return self._calculate_indent(text)


class IndentGuideManager(QObject):
    """Manager for indent guide features."""
    
    def __init__(self, editor: QWidget, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.overlay = IndentGuideOverlay()
        self.overlay.set_editor(editor)
        
    def set_enabled(self, enabled: bool):
        """Enable/disable indent guides."""
        self.overlay.set_enabled(enabled)
        
    def set_indent_width(self, width: int):
        """Set spaces per indent level."""
        self.overlay.set_indent_width(width)
        
    def set_parent(self, parent):
        """Set parent widget for overlay."""
        self.overlay.setParent(parent)
        self.overlay.resize(parent.size())
        
    def resize_event(self, event):
        """Handle resize event for overlay."""
        if self.overlay:
            self.overlay.resize(self.editor.size())
