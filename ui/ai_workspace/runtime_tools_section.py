"""Running Tools Section - v0.9"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel
from PySide6.QtGui import QColor


class RunningToolsSection(QWidget):
    """Display currently running tools."""
    def __init__(self, event_bus=None):
        super().__init__()
        self.event_bus = event_bus
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 6)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setMaximumHeight(120)
        self._list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 11px;
                font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            }
            QListWidget::item {
                color: #3B82F6;
                padding: 2px 10px;
                min-height: 22px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #1C1C1F;
            }
        """)
        self._idle = QLabel("No tools running")
        self._idle.setStyleSheet("color: #52525C; font-size: 11px; background-color: transparent;")
        layout.addWidget(self._list)
        layout.addWidget(self._idle)
        
    def set_tools(self, tools: list):
        """Update running tools display."""
        self._list.clear()
        for tool in tools:
            item_text = f"  ⟳  {tool}"
            item = QListWidgetItem(item_text)
            item.setForeground(QColor("#3B82F6"))
            self._list.addItem(item)
        self._idle.setVisible(len(tools) == 0)
        self._list.setVisible(len(tools) > 0)