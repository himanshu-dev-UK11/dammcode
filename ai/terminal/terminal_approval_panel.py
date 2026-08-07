"""
Terminal Approval Panel — v1.0

Shows an approval dialog before executing AI-requested terminal commands.
Displays command details, working directory, reason, and impact.
User must approve or cancel before execution proceeds.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame, QSplitter, QScrollArea, QStyleOptionButton,
    QStyle, QStylePainter
)
from PySide6.QtCore import Qt, Signal, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont
from pathlib import Path
from typing import Dict, Any

from core.logger import setup_logger
from core.event_bus import EventBus


logger = setup_logger(__name__)


class TerminalApprovalPanel(QWidget):
    """
    Approval panel for terminal command execution.
    
    Shows:
    - Command to execute
    - Working directory
    - Reason for execution
    - Estimated impact
    - Run, Edit Command, Cancel buttons
    
    Signals:
    approved(str) — Emitted when user approves
    cancelled(str) — Emitted when user cancels
    """
    
    approved = Signal(str)  # command
    cancelled = Signal(str)  # command
    
    def __init__(self, event_bus: EventBus = None, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self._command = ""
        self._working_directory = ""
        self._reason = ""
        self._impact = ""
        self._setup_ui()
    
    def set_request(
        self,
        command: str,
        working_directory: str,
        reason: str = "",
        impact: str = ""
    ):
        """Set the request details for approval."""
        self._command = command
        self._working_directory = working_directory
        self._reason = reason
        self._impact = impact
        
        # Update UI
        self._cmd_text.setPlainText(command)
        self._dir_label.setText(f"<b>Working Directory:</b> {working_directory}")
        
        if reason:
            self._reason_text.setPlainText(reason)
        else:
            self._reason_text.setPlainText("No reason provided")
        
        if impact:
            self._impact_text.setPlainText(impact)
        else:
            self._impact_text.setPlainText("Standard terminal execution")
    
    def _setup_ui(self):
        """Setup the approval panel UI."""
        self.setWindowTitle("Terminal Command Approval")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #0D0D0F;
                color: #E2E2E6;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main content
        main = self._create_main()
        layout.addWidget(main)
        
        # Footer
        footer = self._create_footer()
        layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Create the header with icon and title."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border-bottom: 1px solid #252528;
            }
        """)
        widget.setFixedHeight(60)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel(".Terminal")
        icon.setStyleSheet("""
            QLabel {
                background-color: #3B82F6;
                color: white;
                font-size: 20px;
                padding: 8px 12px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(icon)
        
        # Title
        title = QLabel("Terminal Command Execution")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #E2E2E6;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        return widget
    
    def _create_main(self) -> QWidget:
        """Create the main content with command details."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #0D0D0F;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Command section
        cmd_section = self._create_section("Command", self._create_command_widget())
        layout.addWidget(cmd_section)
        
        # Working directory
        dir_section = self._create_section("Working Directory", self._create_dir_widget())
        layout.addWidget(dir_section)
        
        # Reason
        reason_section = self._create_section("Reason", self._create_reason_widget())
        layout.addWidget(reason_section)
        
        # Impact
        impact_section = self._create_section("Estimated Impact", self._create_impact_widget())
        layout.addWidget(impact_section)
        
        return widget
    
    def _create_section(self, title: str, content: QWidget) -> QWidget:
        """Create a section with title and content."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border: 1px solid #252528;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #52525C;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(title_label)
        
        # Content
        layout.addWidget(content)
        
        return widget
    
    def _create_command_widget(self) -> QWidget:
        """Create the command display widget."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #0D0D0F;
                border: 1px solid #252528;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        self._cmd_text = QTextEdit()
        self._cmd_text.setReadOnly(True)
        self._cmd_text.setFixedHeight(80)
        self._cmd_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #E2E2E6;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 11px;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(self._cmd_text)
        
        return widget
    
    def _create_dir_widget(self) -> QWidget:
        """Create the directory display widget."""
        self._dir_label = QLabel("")
        self._dir_label.setStyleSheet("""
            QLabel {
                color: #8E8E98;
                font-size: 11px;
                padding: 8px;
                background-color: #1C1C1F;
                border: 1px solid #252528;
                border-radius: 3px;
            }
        """)
        return self._dir_label
    
    def _create_reason_widget(self) -> QWidget:
        """Create the reason display widget."""
        self._reason_text = QTextEdit()
        self._reason_text.setReadOnly(True)
        self._reason_text.setMaximumHeight(60)
        self._reason_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #8E8E98;
                font-size: 11px;
                border: none;
                padding: 8px;
            }
        """)
        return self._reason_text
    
    def _create_impact_widget(self) -> QWidget:
        """Create the impact display widget."""
        self._impact_text = QTextEdit()
        self._impact_text.setReadOnly(True)
        self._impact_text.setMaximumHeight(60)
        self._impact_text.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1F;
                color: #F59E0B;
                font-size: 11px;
                border: none;
                padding: 8px;
            }
        """)
        return self._impact_text
    
    def _create_footer(self) -> QWidget:
        """Create the footer with action buttons."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #111113;
                border-top: 1px solid #252528;
            }
        """)
        widget.setFixedHeight(50)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)
        
        # Run button
        self._btn_run = QPushButton("Run")
        self._btn_run.setFixedHeight(30)
        self._btn_run.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: #064E3B;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
            QPushButton:pressed {
                background-color: #15803D;
            }
        """)
        self._btn_run.clicked.connect(self._on_run)
        layout.addWidget(self._btn_run)
        
        # Edit Command button (disabled by default)
        self._btn_edit = QPushButton("Edit Command")
        self._btn_edit.setFixedHeight(30)
        self._btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 12px;
                font-weight: 500;
                border: none;
                border-radius: 4px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
            QPushButton:disabled {
                background-color: #252528;
                color: #52525C;
            }
        """)
        self._btn_edit.setEnabled(False)  # Not implemented yet
        layout.addWidget(self._btn_edit)
        
        # Cancel button
        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setFixedHeight(30)
        self._btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #7F1D1D;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        self._btn_cancel.clicked.connect(self._on_cancel)
        layout.addWidget(self._btn_cancel)
        
        layout.addStretch()
        
        return widget
    
    def _on_run(self):
        """User clicked Run button."""
        self.approved.emit(self._command)
        self.close()
    
    def _on_cancel(self):
        """User clicked Cancel button."""
        self.cancelled.emit(self._command)
        self.close()
    
    def show_approval(
        self,
        command: str,
        working_directory: str,
        reason: str = "",
        impact: str = ""
    ) -> str:
        """
        Show the approval panel and wait for user response.
        
        Returns:
            "approved" or "cancelled"
        """
        self.set_request(command, working_directory, reason, impact)
        self.show()
        
        # Return appropriate status
        # Note: In a real implementation, this would use a modal dialog
        # For now, we return "pending" and emit signals
        return "pending"


# For testing
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    panel = TerminalApprovalPanel()
    
    def on_approved(cmd):
        print(f"Approved: {cmd}")
    
    def on_cancelled(cmd):
        print(f"Cancelled: {cmd}")
    
    panel.approved.connect(on_approved)
    panel.cancelled.connect(on_cancelled)
    
    panel.show_approval(
        command="python myscript.py --arg1 value1",
        working_directory="C:\\Projects\\myproject",
        reason="AI detected this script needs to be run",
        impact="Will execute the Python script in the project directory"
    )
    
    sys.exit(app.exec())
