"""
Line number area widget for CodeEditor.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            line_height = max(1, self.code_editor.fontMetrics().height())
            line_number = self.code_editor.firstVisibleBlock().blockNumber() + 1
            line_number += max(0, int(event.position().y() // line_height))
            if hasattr(self.code_editor, "toggle_fold_at_line"):
                self.code_editor.toggle_fold_at_line(line_number)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
