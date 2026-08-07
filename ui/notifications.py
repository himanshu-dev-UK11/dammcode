"""
Notification Manager — v0.8

Manages system notifications with:
- Auto hide with timer
- Queue multiple notifications
- Icons (success/warning/error)
- Smooth animations
- Click to view details

Notifications appear in a toast-style popup.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QIcon, QAction


class Notification(QWidget):
    """Single notification item."""
    close_requested = Signal(str)  # notification_id
    clicked = Signal(str)  # notification_id
    
    def __init__(self, id: str, title: str, message: str, 
                 notification_type: str = "info", auto_hide: bool = True):
        super().__init__()
        self.id = id
        self._notification_type = notification_type
        self._auto_hide = auto_hide
        self.setup_ui(title, message)
        
        # Auto-hide timer
        if auto_hide:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._on_timeout)
            self._timer.start(5000)  # 5 seconds
            
    def setup_ui(self, title: str, message: str):
        self.setObjectName("Notification")
        self.setFixedHeight(80)
        self._apply_style()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Icon
        self._icon = QLabel()
        self._icon.setFixedSize(24, 24)
        self._icon.setAlignment(Qt.AlignCenter)
        self._set_icon()
        layout.addWidget(self._icon)
        
        # Content
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        self._title = QLabel(title)
        self._title.setStyleSheet(f"""
            color: {p.text};
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
        """)
        content_layout.addWidget(self._title)
        
        self._message = QLabel(message)
        self._message.setWordWrap(True)
        self._message.setStyleSheet(f"""
            color: {p.text_secondary};
            font-size: 11px;
            background-color: transparent;
        """)
        content_layout.addWidget(self._message)
        
        layout.addWidget(content)
        
        # Close button
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(20, 20)
        from ui.design_system import get_design_system
        p_close = get_design_system().palette
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p_close.text_tertiary};
                border: none;
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {p_close.surface_hover};
                color: {p_close.text};
            }}
        """)
        self._close_btn.clicked.connect(self._on_close_clicked)
        layout.addWidget(self._close_btn)
        
        # Click to view
        self.setCursor(Qt.PointingHandCursor)
        self._message.setTextInteractionFlags(Qt.TextBrowserInteraction)
        
    def _apply_style(self):
        """Apply style based on notification type."""
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        types = {
            "success": {"bg": p.success_bg, "border": p.success, "icon": "✓"},
            "warning": {"bg": p.warning_bg, "border": p.warning, "icon": "△"},
            "error": {"bg": p.error_bg, "border": p.error, "icon": "✕"},
            "info": {"bg": p.info_bg, "border": p.info, "icon": "ℹ"},
        }
        
        style = types.get(self._notification_type, types["info"])
        self.setStyleSheet(f"""
            #Notification {{
                background-color: {style["bg"]};
                border: 1px solid {style["border"]};
                border-radius: 6px;
            }}
        """)
        
    def _set_icon(self):
        """Set icon based on notification type."""
        icons = {
            "success": "✓",
            "warning": "△",
            "error": "✕",
            "info": "ℹ",
        }
        self._icon.setText(icons.get(self._notification_type, "ℹ"))
        
    def _on_close_clicked(self):
        """Close button clicked."""
        self.close()
        self.close_requested.emit(self.id)
        
    def _on_timeout(self):
        """Auto-hide timeout."""
        self.close()
        
    def mousePressEvent(self, event):
        """Handle click to view."""
        super().mousePressEvent(event)
        self.clicked.emit(self.id)
        
    def mouseReleaseEvent(self, event):
        """Handle click release."""
        super().mouseReleaseEvent(event)
        self.clicked.emit(self.id)


class NotificationManager(QWidget):
    """
    Manages notifications with queue and toast-style display.
    
    Notifications appear in the bottom-right corner and auto-hide.
    """
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._notifications = []
        self._notification_queue = []
        self._max_visible = 5
        self._spacing = 10
        self.setup_ui()
        
        # Subscribe to events
        event_bus.subscribe("notification_show", self._on_notification_show)
        event_bus.subscribe("notification_clear", self._on_notification_clear)
        
        # Layout timer
        self._layout_timer = QTimer(self)
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._update_layout)
        
    def setup_ui(self):
        self.setObjectName("NotificationManager")
        self.setStyleSheet("""
            #NotificationManager {
                background-color: transparent;
            }
        """)
        self.setFixedSize(400, 600)
        self.hide()  # Hidden by default
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(self._spacing)
        layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        
        # Header with Clear All (only shown when there are notifications)
        self._header = QWidget()
        self._header.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignRight)
        
        self._clear_btn = QPushButton("Clear All")
        from ui.design_system import get_design_system
        p_btn = get_design_system().palette
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p_btn.surface};
                color: {p_btn.text_secondary};
                border: 1px solid {p_btn.border_subtle};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {p_btn.surface_hover};
                color: {p_btn.text};
            }}
        """)
        self._clear_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(self._clear_btn)
        
        layout.addWidget(self._header)
        self._header.hide()  # Hidden by default
        
        # Notification container
        self._container = QWidget()
        self._container.setObjectName("NotificationContainer")
        self._container.setStyleSheet("""
            #NotificationContainer {
                background-color: transparent;
            }
        """)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(self._spacing)
        
        layout.addWidget(self._container)
        
        # System tray icon
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon())  # No icon for now
        
    def _on_notification_show(self, data: dict):
        """Show a new notification."""
        title = data.get("title", "Notification")
        message = data.get("message", "")
        notification_type = data.get("type", "info")  # success, warning, error, info
        auto_hide = data.get("auto_hide", True)
        
        from uuid import uuid4
        notification_id = str(uuid4())[:8]
        
        notification = Notification(
            notification_id, title, message, notification_type, auto_hide
        )
        
        notification.close_requested.connect(self._on_notification_close)
        notification.clicked.connect(self._on_notification_clicked)
        
        self._notifications.append(notification)
        self._container_layout.addWidget(notification)
        self._update_layout()
        
        # Show notification and header
        self.show()
        self._header.show()
        self.raise_()
        self._animate_in(notification)
        
        # Queue handling
        self._check_queue()
        
    def _on_notification_close(self, notification_id: str):
        """Notification close requested."""
        self._remove_notification(notification_id)
        
    def _on_notification_clicked(self, notification_id: str):
        """Notification clicked."""
        print(f"Notification clicked: {notification_id}")
        # In a real app, this would show notification details in a panel
        
    def _remove_notification(self, notification_id: str):
        """Remove a notification."""
        for i, notif in enumerate(self._notifications):
            if notif.id == notification_id:
                notif.deleteLater()
                self._notifications.pop(i)
                self._container_layout.removeWidget(notif)
                self._update_layout()
                
                # Show next from queue
                self._check_queue()
                
                # Hide if no more notifications
                if not self._notifications:
                    self._header.hide()
                    QTimer.singleShot(500, self.hide)
                    
                break
                
    def _check_queue(self):
        """Process notification queue."""
        if len(self._notifications) < self._max_visible and self._notification_queue:
            data = self._notification_queue.pop(0)
            self._on_notification_show(data)
            
    def _on_clear_all(self):
        """Clear all notifications."""
        for notif in self._notifications[:]:
            self._remove_notification(notif.id)
            
    def _update_layout(self):
        """Update notification layout."""
        # Ensure we don't exceed max visible
        if len(self._notifications) > self._max_visible:
            # Remove oldest
            for notif in self._notifications[:-self._max_visible]:
                self._remove_notification(notif.id)
                
    def _animate_in(self, notification: Notification):
        """Animate notification appearing."""
        # Simple opacity animation
        anim = QPropertyAnimation(notification, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: notification.setWindowOpacity(1.0))
        anim.start()
        
    def show_notification(self, title: str, message: str,
                          notification_type: str = "info",
                          auto_hide: bool = True):
        """Show a notification directly."""
        self.event_bus.publish("notification_show", {
            "title": title,
            "message": message,
            "type": notification_type,
            "auto_hide": auto_hide
        })
        
    def show_success(self, title: str, message: str, auto_hide: bool = True):
        """Show a success notification."""
        self.show_notification(title, message, "success", auto_hide)
        
    def show_warning(self, title: str, message: str, auto_hide: bool = True):
        """Show a warning notification."""
        self.show_notification(title, message, "warning", auto_hide)
        
    def show_error(self, title: str, message: str, auto_hide: bool = True):
        """Show an error notification."""
        self.show_notification(title, message, "error", auto_hide)
        
    def show_info(self, title: str, message: str, auto_hide: bool = True):
        """Show an info notification."""
        self.show_notification(title, message, "info", auto_hide)
        
    def _on_notification_clear(self, data: dict):
        """Clear all notifications from event."""
        self._on_clear_all()


def create_notification_manager(event_bus) -> NotificationManager:
    """Create and return a notification manager."""
    return NotificationManager(event_bus)
