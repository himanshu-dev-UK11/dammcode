"""
Intelligent Error Handler UI.

Shows user-friendly error messages with actionable suggestions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ai.connection import ConnectionStatus


class ErrorActionWidget(QWidget):
    """Widget showing an error with suggested actions."""
    
    action_clicked = Signal(str)  # action_type
    retry_clicked = Signal()
    
    def __init__(self, status: ConnectionStatus, parent=None):
        super().__init__(parent)
        self.status = status
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Error icon and title
        header_layout = QHBoxLayout()
        
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon)
        
        title = QLabel(self.status.status_message)
        title.setStyleSheet("""
            color: #EF4444;
            font-size: 14px;
            font-weight: 600;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Error message
        if self.status.error_message:
            error_label = QLabel(self.status.error_message)
            error_label.setWordWrap(True)
            error_label.setStyleSheet("""
                color: #E2E2E6;
                font-size: 11px;
                padding: 8px;
                background-color: #1C1C1F;
                border-radius: 4px;
                border-left: 3px solid #EF4444;
            """)
            layout.addWidget(error_label)
        
        # Suggested action
        if self.status.suggested_action:
            action_frame = QFrame()
            action_frame.setStyleSheet("""
                QFrame {
                    background-color: #1C1C1F;
                    border-radius: 6px;
                    border: 1px solid #252528;
                }
            """)
            
            action_layout = QVBoxLayout(action_frame)
            action_layout.setContentsMargins(12, 12, 12, 12)
            action_layout.setSpacing(8)
            
            suggestion_label = QLabel("💡 Suggested Action:")
            suggestion_label.setStyleSheet("""
                color: #3B82F6;
                font-size: 10px;
                font-weight: 600;
            """)
            action_layout.addWidget(suggestion_label)
            
            action_text = QLabel(self.status.suggested_action)
            action_text.setWordWrap(True)
            action_text.setStyleSheet("""
                color: #E2E2E6;
                font-size: 11px;
            """)
            action_layout.addWidget(action_text)
            
            layout.addWidget(action_frame)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Retry button
        if self.status.can_retry:
            retry_btn = QPushButton("🔄 Retry Connection")
            retry_btn.setFixedHeight(32)
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            retry_btn.clicked.connect(self.retry_clicked.emit)
            button_layout.addWidget(retry_btn)
        
        # Fix settings button
        fix_btn = QPushButton("⚙️ Fix Settings")
        fix_btn.setFixedHeight(32)
        fix_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        fix_btn.clicked.connect(lambda: self.action_clicked.emit("fix_settings"))
        button_layout.addWidget(fix_btn)
        
        # Help button
        if self.status.help_url:
            help_btn = QPushButton("📖 View Documentation")
            help_btn.setFixedHeight(32)
            help_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1C1C1F;
                    color: #E2E2E6;
                    border: 1px solid #252528;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #252528;
                }
            """)
            help_btn.clicked.connect(lambda: self.action_clicked.emit("view_help"))
            button_layout.addWidget(help_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)


class ConnectionStatusWidget(QWidget):
    """Widget showing connection status with smart error handling."""
    
    fix_requested = Signal(str)  # provider_name
    retry_requested = Signal(str)  # provider_name
    help_requested = Signal(str, str)  # provider_name, url
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_status = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.content_widget)
    
    def show_status(self, status: ConnectionStatus):
        """Show connection status."""
        self.current_status = status
        
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if status.is_connected:
            # Show success message
            self._show_success(status)
        else:
            # Show error with actions
            self._show_error(status)
    
    def _show_success(self, status: ConnectionStatus):
        """Show success message."""
        success_widget = QWidget()
        success_layout = QVBoxLayout(success_widget)
        success_layout.setContentsMargins(12, 12, 12, 12)
        
        # Success icon and message
        header = QHBoxLayout()
        
        icon = QLabel("✅")
        icon.setStyleSheet("font-size: 20px;")
        header.addWidget(icon)
        
        message = QLabel(status.status_message)
        message.setStyleSheet("""
            color: #10B981;
            font-size: 12px;
            font-weight: 600;
        """)
        header.addWidget(message)
        header.addStretch()
        
        success_layout.addLayout(header)
        
        if status.suggested_action:
            action_label = QLabel(status.suggested_action)
            action_label.setWordWrap(True)
            action_label.setStyleSheet("""
                color: #8E8E98;
                font-size: 10px;
                padding-top: 4px;
            """)
            success_layout.addWidget(action_label)
        
        self.content_layout.addWidget(success_widget)
    
    def _show_error(self, status: ConnectionStatus):
        """Show error with actions."""
        error_widget = ErrorActionWidget(status)
        error_widget.action_clicked.connect(self._on_action_clicked)
        error_widget.retry_clicked.connect(
            lambda: self.retry_requested.emit(status.provider_name)
        )
        self.content_layout.addWidget(error_widget)
    
    def _on_action_clicked(self, action_type: str):
        """Handle action button clicks."""
        if not self.current_status:
            return
        
        if action_type == "fix_settings":
            self.fix_requested.emit(self.current_status.provider_name)
        elif action_type == "view_help":
            self.help_requested.emit(
                self.current_status.provider_name,
                self.current_status.help_url
            )