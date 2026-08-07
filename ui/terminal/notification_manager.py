"""
Terminal Notification Manager — v2.0

Displays notifications for terminal events.
Supports:
- Long-running task completion
- Build completion
- Program exit
- Command failure
- Toast-style notifications
"""
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGraphicsOpacityEffect)
from PySide6.QtGui import QColor, QMovie
from typing import List, Optional
import time
from core.logger import setup_logger

logger = setup_logger(__name__)


class NotificationWidget(QWidget):
    """A single notification toast widget."""
    
    closed = Signal()  # Emitted when notification is closed
    
    def __init__(self, title: str, message: str, severity: str = "info", 
                 parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.severity = severity
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup notification UI."""
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set minimum width but allow it to grow
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        
        # Set padding and spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Severity styling
        p = self._get_severity_colors()
        
        # Background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p.bg};
                border: 1px solid {p.border};
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}
        """)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {p.title};
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {p.text};
                font-size: 11px;
            }}
        """)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.close_bg};
                color: {p.close_text};
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p.close_hover};
            }}
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def _get_severity_colors(self) -> dict:
        """Get colors based on severity."""
        return {
            "info": {
                "bg": "#161618",
                "border": "#252528",
                "title": "#61AFEF",
                "text": "#ABB2BF",
                "close_bg": "#3B3840",
                "close_hover": "#4B4850",
                "close_text": "#ABB2BF"
            },
            "success": {
                "bg": "#161618",
                "border": "#10B981",
                "title": "#10B981",
                "text": "#ABB2BF",
                "close_bg": "#152D23",
                "close_hover": "#1A382B",
                "close_text": "#10B981"
            },
            "warning": {
                "bg": "#161618",
                "border": "#F59E0B",
                "title": "#F59E0B",
                "text": "#ABB2BF",
                "close_bg": "#2D2415",
                "close_hover": "#3A2D1B",
                "close_text": "#F59E0B"
            },
            "error": {
                "bg": "#161618",
                "border": "#EF4444",
                "title": "#EF4444",
                "text": "#ABB2BF",
                "close_bg": "#2D1515",
                "close_hover": "#3A1B1B",
                "close_text": "#EF4444"
            }
        }.get(self.severity, {
            "bg": "#161618",
            "border": "#252528",
            "title": "#E2E2E6",
            "text": "#ABB2BF",
            "close_bg": "#3B3840",
            "close_hover": "#4B4850",
            "close_text": "#ABB2BF"
        })
    
    def _setup_connections(self):
        """Setup signal connections."""
        self._find_close_button().clicked.connect(self.close)
    
    def _find_close_button(self) -> QPushButton:
        """Find the close button widget."""
        for child in self.findChildren(QPushButton):
            if child.text() == "×":
                return child
        return QPushButton()
    
    def show_notification(self):
        """Show the notification with animation."""
        self.show()
        self._animate_in()
    
    def _animate_in(self):
        """Animate notification in."""
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        
        anim = self.property("animation")
        if anim:
            return
            
        # Simple fade in
        self._fade_in_effect = effect
    
    def mousePressEvent(self, event):
        """Handle mouse click to close."""
        self.close()
    
    def close(self):
        """Close the notification."""
        super().close()
        self.closed.emit()


class NotificationManager(QObject):
    """
    Manages terminal notifications.
    """
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._notifications: List[NotificationWidget] = []
        self._timer = QTimer()
        self._timer.timeout.connect(self._cleanup_notifications)
        self._timer.start(5000)  # Cleanup every 5 seconds
    
    def show_task_complete(self, command: str, duration_ms: int, 
                           exit_code: int = 0):
        """Show notification for task completion."""
        if exit_code == 0:
            severity = "success"
            title = "Task Completed"
            message = f"Command finished in {duration_ms / 1000:.1f}s"
        else:
            severity = "error"
            title = "Task Failed"
            message = f"Command failed with exit code {exit_code}"
        
        self._show_notification(title, message, severity)
        self.event_bus.publish("terminal_notification", {
            "type": "task_complete",
            "command": command,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "severity": severity
        })
    
    def show_build_complete(self, project: str, success: bool,
                           duration_ms: int = None):
        """Show notification for build completion."""
        if success:
            severity = "success"
            title = "Build Completed"
            message = f"Project '{project}' built successfully"
        else:
            severity = "error"
            title = "Build Failed"
            message = f"Project '{project}' build failed"
        
        if duration_ms:
            message += f" in {duration_ms / 1000:.1f}s"
        
        self._show_notification(title, message, severity)
        self.event_bus.publish("terminal_notification", {
            "type": "build_complete",
            "project": project,
            "success": success,
            "duration_ms": duration_ms
        })
    
    def show_program_exited(self, program: str, exit_code: int):
        """Show notification for program exit."""
        if exit_code == 0:
            severity = "info"
            title = "Program Exited"
            message = f"'{program}' exited with code 0"
        else:
            severity = "error"
            title = "Program Crashed"
            message = f"'{program}' crashed with exit code {exit_code}"
        
        self._show_notification(title, message, severity)
        self.event_bus.publish("terminal_notification", {
            "type": "program_exited",
            "program": program,
            "exit_code": exit_code
        })
    
    def show_command_failed(self, command: str, error: str):
        """Show notification for command failure."""
        self._show_notification(
            "Command Failed",
            f"'{command}': {error}",
            "error"
        )
        self.event_bus.publish("terminal_notification", {
            "type": "command_failed",
            "command": command,
            "error": error
        })
    
    def show_long_running_complete(self, task_name: str, duration_ms: int):
        """Show notification for long-running task completion."""
        self._show_notification(
            "Long-running Task Complete",
            f"'{task_name}' completed in {duration_ms / 1000:.1f}s",
            "success"
        )
        self.event_bus.publish("terminal_notification", {
            "type": "long_running_complete",
            "task_name": task_name,
            "duration_ms": duration_ms
        })
    
    def _show_notification(self, title: str, message: str, severity: str = "info"):
        """Show a notification."""
        notification = NotificationWidget(title, message, severity)
        notification.closed.connect(lambda: self._remove_notification(notification))
        
        self._notifications.append(notification)
        notification.show_notification()
        
        # Auto-close after 5 seconds
        QTimer.singleShot(5000, notification.close)
    
    def _remove_notification(self, notification: NotificationWidget):
        """Remove a notification."""
        if notification in self._notifications:
            self._notifications.remove(notification)
    
    def _cleanup_notifications(self):
        """Cleanup closed notifications."""
        self._notifications = [n for n in self._notifications if n.isVisible()]
    
    def show(self):
        """Show all notifications."""
        for notification in self._notifications:
            if not notification.isVisible():
                notification.show()
    
    def hide(self):
        """Hide all notifications."""
        for notification in self._notifications:
            notification.hide()
