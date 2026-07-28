"""User Controls Section"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

class UserControlsSection(QWidget):
    """User controls for workflow execution."""
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(8)
        
        # Style for buttons
        btn_style = """
            QPushButton {
                background-color: #252528;
                color: #E2E2E6;
                border: 1px solid #333336;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2D2D30;
                border-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #1C1C1F;
            }
        """
        
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setStyleSheet(btn_style)
        self.btn_pause.clicked.connect(lambda: self.event_bus.publish("workflow_action_pause", {}))
        
        self.btn_resume = QPushButton("Resume")
        self.btn_resume.setStyleSheet(btn_style)
        self.btn_resume.clicked.connect(lambda: self.event_bus.publish("workflow_action_resume", {}))
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(btn_style + "QPushButton:hover { border-color: #EF4444; }")
        self.btn_cancel.clicked.connect(lambda: self.event_bus.publish("workflow_action_cancel", {}))
        
        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_resume)
        layout.addWidget(self.btn_cancel)
        layout.addStretch()

