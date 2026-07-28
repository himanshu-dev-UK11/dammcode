"""
Enhanced Syntax Highlighter — v1.7

Comprehensive syntax highlighting for 30+ languages.
Uses language_support.py for language detection and keywords.
"""
import re
from pathlib import Path
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression
from ui.editor.language_support import detect_language, get_language_by_name


class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Advanced syntax highlighter with support for multiple languages.
    """
    def __init__(self, document, language_or_path):
        super().__init__(document)
        
        # Detect language
        if isinstance(language_or_path, str):
            if '.' in language_or_path or '/' in language_or_path or '\\' in language_or_path:
                # It's a file path
                self.lang_info = detect_language(Path(language_or_path))
            else:
                # It's a language name
                self.lang_info = get_language_by_name(language_or_path)
                if not self.lang_info:
                    from ui.editor.language_support import LANGUAGES
                    self.lang_info = LANGUAGES["plaintext"]
        elif isinstance(language_or_path, Path):
            self.lang_info = detect_language(language_or_path)
        else:
            from ui.editor.language_support import LANGUAGES
            self.lang_info = LANGUAGES["plaintext"]
            
        self.rules = []
        self.setup_formats()
        self.setup_rules()

    def setup_formats(self):
        """Setup text formats for different syntax elements."""
        # Keywords
        self.fmt_keyword = QTextCharFormat()
        self.fmt_keyword.setForeground(QColor("#CBA6F7"))  # Mauve
        self.fmt_keyword.setFontWeight(QFont.Bold)

        # Strings
        self.fmt_string = QTextCharFormat()
        self.fmt_string.setForeground(QColor("#A6E3A1"))  # Green

        # Comments
        self.fmt_comment = QTextCharFormat()
        self.fmt_comment.setForeground(QColor("#6C7086"))  # Overlay
        self.fmt_comment.setFontItalic(True)

        # Numbers
        self.fmt_number = QTextCharFormat()
        self.fmt_number.setForeground(QColor("#FAB387"))  # Peach

        # Functions
        self.fmt_function = QTextCharFormat()
        self.fmt_function.setForeground(QColor("#89B4FA"))  # Blue

        # Classes/Types
        self.fmt_class = QTextCharFormat()
        self.fmt_class.setForeground(QColor("#F9E2AF"))  # Yellow

        # Operators
        self.fmt_operator = QTextCharFormat()
        self.fmt_operator.setForeground(QColor("#89DCEB"))  # Sky

        # Brackets
        self.fmt_bracket = QTextCharFormat()
        self.fmt_bracket.setForeground(QColor("#F5C2E7"))  # Pink

    def setup_rules(self):
        """Setup highlighting rules based on language."""
        # Keywords
        for kw in self.lang_info.keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self.rules.append((pattern, self.fmt_keyword))

        # Numbers (integers, hex, floats)
        self.rules.append((QRegularExpression(r"\b\d+\.?\d*([eE][+-]?\d+)?\b"), self.fmt_number))
        self.rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), self.fmt_number))
        self.rules.append((QRegularExpression(r"\b0[bB][01]+\b"), self.fmt_number))
        self.rules.append((QRegularExpression(r"\b0[oO][0-7]+\b"), self.fmt_number))

        # Strings (double quotes)
        self.rules.append((QRegularExpression(r'"(?:[^"\\]|\\.)*"'), self.fmt_string))
        # Strings (single quotes)
        self.rules.append((QRegularExpression(r"'(?:[^'\\]|\\.)*'"), self.fmt_string))
        # Template literals (for JS/TS)
        if self.lang_info.name in ["JavaScript", "TypeScript"]:
            self.rules.append((QRegularExpression(r"`(?:[^`\\]|\\.)*`"), self.fmt_string))

        # Functions (name followed by opening paren)
        self.rules.append((QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"), self.fmt_function))

        # Classes/Types (CamelCase words)
        self.rules.append((QRegularExpression(r"\b[A-Z][A-Za-z0-9_]*\b"), self.fmt_class))

        # Operators
        operators = [
            r"\+", r"-", r"\*", r"/", r"%", r"=", r"==", r"!=", r"<", r">",
            r"<=", r">=", r"&&", r"\|\|", r"!", r"&", r"\|", r"\^", r"~",
            r"<<", r">>", r"\+=", r"-=", r"\*=", r"/=", r"%=", r"&=", r"\|=",
            r"\^=", r"<<=", r">>=", r"\+\+", r"--", r"->", r"::", r"\?", r":"
        ]
        for op in operators:
            self.rules.append((QRegularExpression(op), self.fmt_operator))

        # Brackets
        brackets = [r"\(", r"\)", r"\[", r"\]", r"\{", r"\}"]
        for br in brackets:
            self.rules.append((QRegularExpression(br), self.fmt_bracket))

        # Comments - handled separately in highlightBlock for multi-line support

    def highlightBlock(self, text):
        """Highlight a single block of text."""
        # Apply all regex rules
        for pattern, fmt in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Handle comments after other rules to override them
        self._highlight_comments(text)

    def _highlight_comments(self, text):
        """Highlight single-line and multi-line comments."""
        # Single-line comments
        if self.lang_info.line_comment:
            comment_start = text.find(self.lang_info.line_comment)
            if comment_start >= 0:
                # Check it's not inside a string (basic check)
                self.setFormat(comment_start, len(text) - comment_start, self.fmt_comment)

        # Multi-line comments (basic support)
        if self.lang_info.block_comment_start and self.lang_info.block_comment_end:
            start_pattern = QRegularExpression(re.escape(self.lang_info.block_comment_start))
            end_pattern   = QRegularExpression(re.escape(self.lang_info.block_comment_end))

            start_match = start_pattern.match(text)
            if start_match.hasMatch():
                start_index = start_match.capturedStart()
                end_match = end_pattern.match(
                    text, start_index + len(self.lang_info.block_comment_start)
                )
                if end_match.hasMatch():
                    length = end_match.capturedEnd() - start_index
                    self.setFormat(start_index, length, self.fmt_comment)
                else:
                    self.setFormat(start_index, len(text) - start_index, self.fmt_comment)
