"""
Main Code Editor widget based on QPlainTextEdit.
"""
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QApplication, QMenu
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import (
    QPainter, QColor, QTextFormat, QFont, QKeySequence, QAction,
    QTextCursor, QTextOption
)

from ui.editor.line_number_area import LineNumberArea
from ui.editor.syntax_highlighter import SyntaxHighlighter
from core.logger import setup_logger

logger = setup_logger(__name__)

class CodeEditor(QPlainTextEdit):
    modified_state_changed = Signal(bool)
    cursor_position_changed = Signal()
    ai_action_requested = Signal(str, str)  # (action_name, selected_text)
    state_changed = Signal(object)

    def __init__(self, file_path=None, event_bus=None):
        super().__init__()
        self.file_path = file_path
        self.event_bus = event_bus
        self.line_number_area = LineNumberArea(self)
        self.lsp_manager = None
        self.diagnostics = []
        self.doc_version = 1
        self._selection_layers = {
            "current_line": [],
            "diagnostics": [],
            "brackets": [],
            "search": [],
        }
        self._folded_ranges = set()
        self._pending_restore_state = None
        self._capture_enabled = True
        
        self.setup_ui()
        self.setup_connections()
        self.setup_highlighter()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def setup_ui(self):
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.setCursorWidth(2)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {p.editor_bg};
                color: {p.text};
                border: none;
            }}
        """)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
    def setup_connections(self):
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.cursor_position_changed.emit)
        self.modificationChanged.connect(self.modified_state_changed.emit)
        self.textChanged.connect(self._on_text_changed)
        self.verticalScrollBar().valueChanged.connect(self._emit_state_changed)
        self.horizontalScrollBar().valueChanged.connect(self._emit_state_changed)
        self.cursorPositionChanged.connect(self._emit_state_changed)
        
    def setup_highlighter(self):
        """Setup syntax highlighter from full file path."""
        if self.file_path:
            # Pass the full path so SyntaxHighlighter can detect the language correctly
            self.highlighter = SyntaxHighlighter(self.document(), str(self.file_path))
        else:
            self.highlighter = SyntaxHighlighter(self.document(), "plaintext")
            
    def load_file(self, content):
        previous_cursor = self.textCursor()
        previous_scroll = self.verticalScrollBar().value()
        self._capture_enabled = False
        self.setUpdatesEnabled(False)
        try:
            self.setPlainText(content)
            self.document().setModified(False)
            if self._pending_restore_state:
                self.restore_state(self._pending_restore_state)
                self._pending_restore_state = None
            else:
                self.setTextCursor(previous_cursor)
                self.verticalScrollBar().setValue(previous_scroll)
        finally:
            self.setUpdatesEnabled(True)
            self._capture_enabled = True
            self._emit_state_changed()

    def set_pending_restore_state(self, state: dict):
        self._pending_restore_state = state or None

    def capture_state(self) -> dict:
        cursor = self.textCursor()
        return {
            "cursor": {
                "position": cursor.position(),
                "anchor": cursor.anchor(),
                "line": cursor.blockNumber() + 1,
                "column": cursor.columnNumber() + 1,
            },
            "scroll": {
                "vertical": self.verticalScrollBar().value(),
                "horizontal": self.horizontalScrollBar().value(),
            },
            "folded_ranges": [list(item) for item in sorted(self._folded_ranges)],
            "modified": self.document().isModified(),
            "read_only": self.isReadOnly(),
        }

    def restore_state(self, state: dict):
        if not state:
            return

        self._capture_enabled = False
        try:
            cursor_state = state.get("cursor", {})
            position = cursor_state.get("position")
            anchor = cursor_state.get("anchor")
            if position is not None:
                cursor = self.textCursor()
                if anchor is not None and anchor != position:
                    cursor.setPosition(anchor)
                    cursor.setPosition(position, QTextCursor.KeepAnchor)
                else:
                    cursor.setPosition(position)
                self.setTextCursor(cursor)

            scroll_state = state.get("scroll", {})
            if scroll_state:
                self.verticalScrollBar().setValue(scroll_state.get("vertical", self.verticalScrollBar().value()))
                self.horizontalScrollBar().setValue(scroll_state.get("horizontal", self.horizontalScrollBar().value()))

            self._folded_ranges = set()
            for range_item in state.get("folded_ranges", []):
                if isinstance(range_item, (list, tuple)) and len(range_item) == 2:
                    start, end = int(range_item[0]), int(range_item[1])
                    if start > 0 and end >= start:
                        self._folded_ranges.add((start, end))
                        self._apply_fold_range(start, end, folded=True)
        finally:
            self._capture_enabled = True
            self._emit_state_changed()

    def _emit_state_changed(self):
        if self._capture_enabled:
            self.state_changed.emit(self.capture_state())

    def set_search_highlights(self, selections):
        self._selection_layers["search"] = list(selections or [])
        self._refresh_extra_selections()

    def set_bracket_highlights(self, selections):
        self._selection_layers["brackets"] = list(selections or [])
        self._refresh_extra_selections()

    def set_diagnostics_highlights(self, selections):
        self._selection_layers["diagnostics"] = list(selections or [])
        self._refresh_extra_selections()

    def set_current_line_highlight(self, selections):
        self._selection_layers["current_line"] = list(selections or [])
        self._refresh_extra_selections()

    def _refresh_extra_selections(self):
        selections = []
        for layer_name in ("current_line", "diagnostics", "brackets", "search"):
            selections.extend(self._selection_layers[layer_name])
        super().setExtraSelections(selections)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#313244")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.set_current_line_highlight(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#181825"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#6C7086"))
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight | Qt.AlignVCenter, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_block = cursor.block().text()
            leading = len(current_block) - len(current_block.lstrip(" \t"))
            indent = current_block[:leading]
            extra_indent = ""
            stripped = current_block.rstrip()
            if stripped.endswith((":", "{", "[", "(")):
                extra_indent = "    "
            super().keyPressEvent(event)
            if indent or extra_indent:
                self.insertPlainText(indent + extra_indent)
            return

        if event.key() == Qt.Key_Backspace:
            if cursor.hasSelection():
                super().keyPressEvent(event)
                return
            block_text = cursor.block().text()
            block_start = cursor.block().position()
            relative_pos = cursor.position() - block_start
            before_cursor = block_text[:relative_pos]
            if before_cursor and before_cursor.isspace():
                spaces = min(4, len(before_cursor))
                cursor.beginEditBlock()
                cursor.setPosition(cursor.position() - spaces, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                cursor.endEditBlock()
                self.setTextCursor(cursor)
                return

        # Auto bracket/quote closing
        if event.key() in [Qt.Key_ParenLeft, Qt.Key_BracketLeft, Qt.Key_BraceLeft, Qt.Key_QuoteDbl, Qt.Key_Apostrophe]:
            pairs = {
                Qt.Key_ParenLeft: ')',
                Qt.Key_BracketLeft: ']',
                Qt.Key_BraceLeft: '}',
                Qt.Key_QuoteDbl: '"',
                Qt.Key_Apostrophe: "'"
            }
            open_char = event.text()
            close_char = pairs[event.key()]
            cursor = self.textCursor()
            cursor.insertText(open_char + close_char)
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            event.accept()
            return
        
        # Ctrl+D: Duplicate line
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
            cursor = self.textCursor()
            cursor.select(cursor.BlockUnderCursor)
            line_text = cursor.selectedText()
            cursor.movePosition(cursor.EndOfBlock)
            cursor.insertText('\n' + line_text)
            event.accept()
            return
        
        # Ctrl+Shift+Up/Down: Move line
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            if event.key() == Qt.Key_Up:
                self._move_line(-1)
                event.accept()
                return
            elif event.key() == Qt.Key_Down:
                self._move_line(1)
                event.accept()
                return
        
        # Ctrl+Y / Ctrl+Shift+K: Delete line
        if (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Y) or (event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_K):
            self._delete_line()
            event.accept()
            return
        
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            if self.event_bus:
                # Publish with self so EditorManager can write to disk
                self.event_bus.publish("request_save_file", {
                    "editor": self,
                    "path":   self.file_path,
                })
            event.accept()
            return
        super().keyPressEvent(event)

    def toggle_fold_at_line(self, line_number: int):
        if line_number <= 0:
            return

        block = self.document().findBlockByNumber(line_number - 1)
        if not block.isValid():
            return

        start, end = self._find_foldable_range(block)
        if start is None or end is None:
            return

        key = (start, end)
        if key in self._folded_ranges:
            self._folded_ranges.remove(key)
            self._apply_fold_range(start, end, folded=False)
        else:
            self._folded_ranges.add(key)
            self._apply_fold_range(start, end, folded=True)
        self._emit_state_changed()

    def _find_foldable_range(self, block):
        start = block.blockNumber() + 1
        base_indent = self._indent_width(block.text())
        if not block.next().isValid():
            return None, None

        end_block = block.next()
        if self._indent_width(end_block.text()) <= base_indent:
            return None, None

        last_folded = end_block.blockNumber() + 1
        while end_block.isValid():
            indent = self._indent_width(end_block.text())
            if indent <= base_indent and end_block.text().strip():
                break
            last_folded = end_block.blockNumber() + 1
            end_block = end_block.next()

        if last_folded > start:
            return start, last_folded
        return None, None

    def _apply_fold_range(self, start_line: int, end_line: int, folded: bool):
        start_block = self.document().findBlockByNumber(start_line - 1)
        end_block = self.document().findBlockByNumber(end_line - 1)
        if not start_block.isValid() or not end_block.isValid():
            return

        block = start_block.next()
        while block.isValid() and block.blockNumber() <= end_block.blockNumber():
            block.setVisible(not folded)
            block.setLineCount(0 if folded else 1)
            block = block.next()

        self.document().markContentsDirty(start_block.position(), end_block.position() - start_block.position())
        self.viewport().update()
        self.update_line_number_area_width(0)

    @staticmethod
    def _indent_width(text: str) -> int:
        width = 0
        for char in text:
            if char == " ":
                width += 1
            elif char == "\t":
                width += 4
            else:
                break
        return width
        
    def _move_line(self, delta):
        """Move current line up (-1) or down (+1)."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Get current block
        block = cursor.block()
        if not block.isValid():
            return
        
        # Get block contents
        text = block.text()
        next_block = block.next() if delta > 0 else block.previous()
        
        if not next_block.isValid():
            return
            
        # Remove current block
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        
        # Insert new block
        if delta < 0:
            cursor.movePosition(QTextCursor.PreviousBlock)
        cursor.insertText(text + '\n')
        
        cursor.endEditBlock()
        
    def _delete_line(self):
        """Delete current line."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        if cursor.block().isValid() and cursor.atBlockStart():
            cursor.deleteChar()
        cursor.endEditBlock()

    def toggle_word_wrap(self):
        if self.lineWrapMode() == QPlainTextEdit.NoWrap:
            self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.NoWrap)
            
    def _show_context_menu(self, pos):
        """Show custom context menu with AI actions."""
        menu = QMenu(self)
        
        # Add AI Actions
        ai_menu = menu.addMenu("AI Actions")
        
        actions = [
            ("Ask AI", "ask"),
            ("Explain", "explain"),
            ("Review", "review"),
            ("Fix Bug", "fix_bug"),
            ("Refactor", "refactor"),
            ("Optimize", "optimize"),
            ("Generate Documentation", "generate_docs"),
            ("Generate Unit Tests", "generate_tests"),
            ("Convert", "convert"),
            ("Improve", "improve"),
            ("Comment Code", "comment_code"),
            ("Extract Method", "extract_method"),
            ("Rename", "rename"),
            ("Improve Naming", "improve_naming"),
            ("Generate Class", "generate_class"),
            ("Generate API Client", "generate_api_client"),
            ("Generate UI", "generate_ui"),
            ("Generate Config", "generate_config"),
            ("Generate Dockerfile", "generate_dockerfile"),
            ("Generate CI/CD", "generate_ci"),
            ("Generate Regex", "generate_regex"),
            ("Generate SQL", "generate_sql"),
            ("Generate Commit Message", "generate_commit_msg"),
            ("Generate README", "generate_readme"),
            ("Copy to AI Chat", "copy_to_chat")
        ]
        
        selected_text = self.textCursor().selectedText()
        
        for label, action_name in actions:
            a = ai_menu.addAction(label)
            a.triggered.connect(lambda checked, n=action_name, t=selected_text: self._handle_ai_action(n, t))
        
        # Add default edit actions
        menu.addSeparator()
        
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self.cut)
        menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)
        
        # Show the menu
        menu.exec_(self.mapToGlobal(pos))
        
    def set_lsp_manager(self, lsp_manager):
        """Set LSP manager and connect signals."""
        self.lsp_manager = lsp_manager
        # Connect diagnostics signal from LSP manager
        self.lsp_manager.diagnostics_received.connect(self._on_diagnostics_received)
        
    def _on_diagnostics_received(self, file_path: str, diagnostics: list):
        """Update diagnostics for this file."""
        if file_path == self.file_path:
            self.diagnostics = diagnostics
            self._update_diagnostics_underline()
            
    def _update_diagnostics_underline(self):
        """Update underlines for errors/warnings in the editor."""
        extra_selections = []
        
        # First add the current line highlight
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#313244")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        # Add diagnostic underlines
        for diag in self.diagnostics:
            range_ = diag.get("range", {})
            start = range_.get("start", {})
            end = range_.get("end", {})
            
            # Convert LSP positions to QTextCursor
            cursor = self.textCursor()
            cursor.setPosition(0)
            
            # Move to start line
            for _ in range(start.get("line", 0)):
                cursor.movePosition(QTextCursor.NextBlock)
                
            # Move to start character
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, start.get("character", 0))
            
            # Select to end
            end_line = end.get("line", 0)
            if end_line > start.get("line", 0):
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                for _ in range(end_line - start.get("line", 0) - 1):
                    cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, end.get("character", 0))
            else:
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, end.get("character", 0) - start.get("character", 0))
                
            # Apply formatting based on severity
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            
            severity = diag.get("severity", 1)  # 1: Error, 2: Warning, 3: Info, 4: Hint
            if severity == 1:
                # Red wavy underline for errors
                selection.format.setUnderlineColor(QColor("#EF4444"))
                selection.format.setUnderlineStyle(QTextFormat.WaveUnderline)
            elif severity == 2:
                # Yellow wavy underline for warnings
                selection.format.setUnderlineColor(QColor("#F59E0B"))
                selection.format.setUnderlineStyle(QTextFormat.WaveUnderline)
            elif severity == 3:
                # Blue underline for info
                selection.format.setUnderlineColor(QColor("#60A5FA"))
                selection.format.setUnderlineStyle(QTextFormat.DotLine)
            elif severity == 4:
                # Purple underline for hints
                selection.format.setUnderlineColor(QColor("#8B5CF6"))
                selection.format.setUnderlineStyle(QTextFormat.DotLine)
                
            extra_selections.append(selection)
            
        self.set_diagnostics_highlights(extra_selections)
        
    def highlight_current_line(self):
        """Overridden to include diagnostic underlines."""
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#313244")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            self.set_current_line_highlight([selection])
        else:
            self.set_current_line_highlight([])

        self._update_diagnostics_underline()
        
    def _on_text_changed(self):
        """Notify LSP manager of document changes."""
        if self.lsp_manager and self.file_path:
            self.doc_version += 1
            from pathlib import Path
            self.lsp_manager.change_document(Path(self.file_path), self.toPlainText(), self.doc_version)
            
    def _handle_ai_action(self, action_name: str, selected_text: str):
        """Handle an AI action from the context menu."""
        logger.info(f"AI action requested: {action_name}")
        
        if self.event_bus:
            self.event_bus.publish("ai_action_requested", {
                "action": action_name,
                "selected_text": selected_text,
                "file_path": self.file_path
            })
        
        self.ai_action_requested.emit(action_name, selected_text)
