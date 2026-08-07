"""
Enhanced Highlighting — v1.0

Current line highlight, line number highlight, and matching bracket highlighting
for the IDE editor.
"""

from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
from PySide6.QtCore import Qt, QRect, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QTextFormat, QTextCursor, QBrush


class HighlightManager(QObject):
    """Manages all highlighting features for the editor."""
    
    def __init__(self, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self.editor = editor
        self._highlight_current_line = True
        self._highlight_line_number = True
        self._highlight_matching_brackets = True
        self._highlight_indent_guides = True
        
        self.bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>'
        }
        
        # Brackets by direction
        self.open_brackets = set(self.bracket_pairs.keys())
        self.close_brackets = set(self.bracket_pairs.values())
        
    def set_highlight_current_line(self, enabled: bool):
        """Enable/disable current line highlight."""
        self._highlight_current_line = enabled
        self.editor.update()
        
    def set_highlight_line_number(self, enabled: bool):
        """Enable/disable line number highlight."""
        self._highlight_line_number = enabled
        self.editor.update()
        
    def set_highlight_matching_brackets(self, enabled: bool):
        """Enable/disable matching bracket highlighting."""
        self._highlight_matching_brackets = enabled
        self.editor.update()
        
    def set_highlight_indent_guides(self, enabled: bool):
        """Enable/disable indent guide highlighting."""
        self._highlight_indent_guides = enabled
        self.editor.update()
        
    def update_highlights(self):
        """Update all highlights."""
        self.editor.update()
        
    def get_extra_selections(self):
        """Get all extra selections for highlighting."""
        selections = []
        
        # Current line highlight
        if self._highlight_current_line:
            current_line_selection = self._highlight_current_line_selection()
            if current_line_selection:
                selections.append(current_line_selection)
                
        return selections
        
    def _highlight_current_line_selection(self):
        """Create selection for current line highlight."""
        if self.editor.isReadOnly():
            return None
            
        cursor = self.editor.textCursor()
        selection = QTextEdit.ExtraSelection()
        line_color = QColor("#313244")
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = cursor
        selection.cursor.clearSelection()
        return selection
        
    def find_matching_bracket(self, cursor: QTextCursor):
        """Find matching bracket position."""
        char = cursor.document().characterAt(cursor.position())
        
        if char in self.open_brackets:
            return self._find_matching_close(cursor, char)
        elif char in self.close_brackets:
            return self._find_matching_open(cursor, char)
            
        return -1
        
    def _find_matching_close(self, cursor, open_char):
        """Find matching closing bracket."""
        close_char = self.bracket_pairs[open_char]
        depth = 1
        pos = cursor.position()
        
        while pos < cursor.document().characterCount() - 1:
            pos += 1
            ch = cursor.document().characterAt(pos)
            
            if ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    return pos
                    
        return -1
        
    def _find_matching_open(self, cursor, close_char):
        """Find matching opening bracket."""
        open_char = None
        for k, v in self.bracket_pairs.items():
            if v == close_char:
                open_char = k
                break
                
        if not open_char:
            return -1
            
        depth = 1
        pos = cursor.position()
        
        while pos > 0:
            pos -= 1
            ch = cursor.document().characterAt(pos)
            
            if ch == close_char:
                depth += 1
            elif ch == open_char:
                depth -= 1
                if depth == 0:
                    return pos
                    
        return -1
        
    def highlight_brackets(self, cursor: QTextCursor):
        """Highlight matching brackets around cursor."""
        if not self._highlight_matching_brackets:
            return []
            
        selections = []
        
        # Get current character
        pos = cursor.position()
        char = cursor.document().characterAt(pos)
        
        # Check if at bracket
        if char in self.open_brackets or char in self.close_brackets:
            # Highlight current bracket
            selection1 = QTextEdit.ExtraSelection()
            selection1.cursor = QTextCursor(cursor)
            selection1.cursor.setPosition(pos)
            selection1.cursor.setPosition(pos + 1, QTextCursor.KeepAnchor)
            selection1.format.setBackground(QColor("rgba(59, 130, 246, 0.3)"))
            selections.append(selection1)
            
            # Find matching bracket
            match_pos = self.find_matching_bracket(cursor)
            if match_pos >= 0:
                selection2 = QTextEdit.ExtraSelection()
                selection2.cursor = QTextCursor(cursor)
                selection2.cursor.setPosition(match_pos)
                selection2.cursor.setPosition(match_pos + 1, QTextCursor.KeepAnchor)
                selection2.format.setBackground(QColor("rgba(59, 130, 246, 0.3)"))
                selections.append(selection2)
                
        return selections
        
    def get_indent_guide_positions(self, cursor: QTextCursor):
        """Get indent guide positions for current line."""
        if not self._highlight_indent_guides:
            return []
            
        positions = []
        text = cursor.block().text()
        
        # Count leading spaces
        indent_level = 0
        for char in text:
            if char == ' ':
                indent_level += 1
            elif char == '\t':
                indent_level += 4  # Assume 4 spaces per tab
            else:
                break
                
        # Calculate positions (in pixels)
        font_metrics = self.editor.fontMetrics()
        space_width = font_metrics.horizontalAdvance(' ')
        
        for i in range(4, indent_level + 1, 4):
            x_pos = i * space_width
            positions.append(x_pos)
            
        return positions


class LineNumberHighlighter(QObject):
    """Highlights the current line number in the line number area."""
    
    def __init__(self, line_number_area, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self.line_number_area = line_number_area
        self.editor = editor
        
    def paint_event(self, event):
        """Paint line numbers with current line highlighted."""
        from PySide6.QtGui import QPainter
        
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#181825"))
        
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        current_line = self.editor.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # Highlight current line number
                if block_number == current_line:
                    painter.setPen(QColor("#89B4FA"))
                    painter.setFont(self.editor.font())
                    painter.drawText(0, top, self.line_number_area.width() - 5,
                                     self.fontMetrics().height(),
                                     Qt.AlignRight | Qt.AlignVCenter, number)
                else:
                    painter.setPen(QColor("#6C7086"))
                    painter.drawText(0, top, self.line_number_area.width() - 5,
                                     self.fontMetrics().height(),
                                     Qt.AlignRight | Qt.AlignVCenter, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1
