"""
Bracket Matcher — v1.0

Highlight matching brackets: (), [], {}, <>
Supports all common bracket types with visual feedback.
"""

from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor


class BracketMatcher(QObject):
    """Matches and highlights bracket pairs."""
    
    brackets_changed = Signal()
    
    def __init__(self, editor: QPlainTextEdit, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>'
        }
        
        # Brackets by direction
        self.open_brackets = set(self.bracket_pairs.keys())
        self.close_brackets = set(self.bracket_pairs.values())
        
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("rgba(59, 130, 246, 0.3)"))
        
    def set_bracket_pairs(self, pairs: dict):
        """Set custom bracket pairs."""
        self.bracket_pairs = pairs
        self.open_brackets = set(pairs.keys())
        self.close_brackets = set(pairs.values())
        
    def find_matching_bracket(self, cursor: QTextCursor):
        """Find position of matching bracket."""
        pos = cursor.position()
        char = cursor.document().characterAt(pos)
        
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
        
    def highlight_matching_brackets(self):
        """Highlight matching brackets around cursor."""
        cursor = self.editor.textCursor()
        pos = cursor.position()
        
        # Get current character
        char = cursor.document().characterAt(pos)
        
        if char not in self.open_brackets and char not in self.close_brackets:
            # Try previous position
            if pos > 0:
                char = cursor.document().characterAt(pos - 1)
                if char not in self.open_brackets and char not in self.close_brackets:
                    self.editor.setExtraSelections([])
                    return
                    
        selections = []
        
        # Highlight current bracket
        if char in self.open_brackets or char in self.close_brackets:
            selection1 = QTextEdit.ExtraSelection()
            selection1.cursor = QTextCursor(cursor)
            selection1.cursor.setPosition(pos)
            selection1.cursor.setPosition(pos + 1, QTextCursor.KeepAnchor)
            selection1.format = self.highlight_format
            selections.append(selection1)
            
            # Find and highlight matching bracket
            match_pos = self.find_matching_bracket(cursor)
            if match_pos >= 0:
                selection2 = QTextEdit.ExtraSelection()
                selection2.cursor = QTextCursor(cursor)
                selection2.cursor.setPosition(match_pos)
                selection2.cursor.setPosition(match_pos + 1, QTextCursor.KeepAnchor)
                selection2.format = self.highlight_format
                selections.append(selection2)
                
        if hasattr(self.editor, "set_bracket_highlights"):
            self.editor.set_bracket_highlights(selections)
        else:
            self.editor.setExtraSelections(selections)
        
    def get_bracket_at_position(self, pos: int):
        """Get bracket character at position, if any."""
        cursor = self.editor.textCursor()
        cursor.setPosition(pos)
        char = cursor.document().characterAt(pos)
        
        if char in self.open_brackets or char in self.close_brackets:
            return char
        return None
        
    def is_bracket_at_cursor(self):
        """Check if cursor is at a bracket position."""
        cursor = self.editor.textCursor()
        pos = cursor.position()
        char = cursor.document().characterAt(pos)
        
        if char in self.open_brackets or char in self.close_brackets:
            return True
            
        # Check previous position
        if pos > 0:
            char = cursor.document().characterAt(pos - 1)
            return char in self.open_brackets or char in self.close_brackets
            
        return False
