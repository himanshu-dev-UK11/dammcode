"""
Terminal Indicators — v2.1

Display terminal status indicators: active process, shell, background jobs,
notification count, encoding, read-only mode.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from typing import Optional
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalIndicators(QFrame):
    """
    Display terminal status indicators in a compact status bar.
    """
    
    # Signals
    encoding_changed = Signal(str)  # new encoding
    shell_changed = Signal(str)  # new shell
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = None  # Will be set by parent
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup indicators UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Active Process indicator
        self._lbl_process = QLabel()
        self._lbl_process.setObjectName("process_label")
        self._lbl_process.setToolTip("Active Process")
        layout.addWidget(self._lbl_process)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Shell indicator
        self._lbl_shell = QLabel()
        self._lbl_shell.setObjectName("shell_label")
        self._lbl_shell.setToolTip("Shell")
        layout.addWidget(self._lbl_shell)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Background Jobs indicator
        self._lbl_jobs = QLabel()
        self._lbl_jobs.setObjectName("jobs_label")
        self._lbl_jobs.setToolTip("Background Jobs")
        layout.addWidget(self._lbl_jobs)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Notification Count
        self._lbl_notifications = QLabel()
        self._lbl_notifications.setObjectName("notifications_label")
        self._lbl_notifications.setToolTip("Notification Count")
        layout.addWidget(self._lbl_notifications)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Terminal Encoding
        self._lbl_encoding = QLabel()
        self._lbl_encoding.setObjectName("encoding_label")
        self._lbl_encoding.setToolTip("Terminal Encoding")
        layout.addWidget(self._lbl_encoding)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Read Only Mode
        self._lbl_readonly = QLabel()
        self._lbl_readonly.setObjectName("readonly_label")
        self._lbl_readonly.setToolTip("Read Only Mode")
        layout.addWidget(self._lbl_readonly)
        
        self._apply_styles()
    
    def _create_separator(self) -> QLabel:
        """Create a separator label."""
        sep = QLabel("•")
        sep.setObjectName("separator")
        sep.setStyleSheet("""
            QLabel {
                color: #8E8E98;
                font-size: 12px;
            }
        """)
        return sep
    
    def _setup_connections(self):
        """Setup signal connections."""
        pass
    
    def _apply_styles(self):
        """Apply professional styling."""
        p = self.ds.palette if self.ds else None
        if not p:
            return
        
        self.setStyleSheet(f"""
            TerminalIndicators {{
                background-color: {p.surface};
                border-bottom: 1px solid {p.border};
            }}
            
            QLabel {{
                font-size: 11px;
                padding: 2px 4px;
                min-width: 40px;
            }}
            
            QLabel#process_label {{
                color: {p.success};
                font-family: "JetBrains Mono", monospace;
            }}
            
            QLabel#shell_label {{
                color: {p.accent};
                font-family: "JetBrains Mono", monospace;
            }}
            
            QLabel#jobs_label {{
                color: {p.warning};
            }}
            
            QLabel#notifications_label {{
                color: {p.accent};
                font-weight: bold;
                min-width: 16px;
            }}
            
            QLabel#encoding_label {{
                color: {p.text_tertiary};
                font-family: "JetBrains Mono", monospace;
            }}
            
            QLabel#readonly_label {{
                color: {p.error};
            }}
            
            QLabel#separator {{
                color: {p.border};
            }}
        """)
    
    def set_active_process(self, command: str):
        """Set the active process command."""
        if command:
            self._lbl_process.setText(f"▶ {command[:30]}")
            self._lbl_process.setToolTip(command)
        else:
            self._lbl_process.setText("⏸ Idle")
            self._lbl_process.setToolTip("No active process")
    
    def set_shell(self, shell: str):
        """Set the shell name."""
        self._lbl_shell.setText(f"▶ {shell}")
    
    def set_background_jobs(self, count: int):
        """Set the background job count."""
        if count > 0:
            self._lbl_jobs.setText(f"⚙ {count}")
            self._lbl_jobs.setToolTip(f"{count} background job(s) running")
        else:
            self._lbl_jobs.setText("⚙ 0")
            self._lbl_jobs.setToolTip("No background jobs")
    
    def set_notification_count(self, count: int):
        """Set the notification count."""
        if count > 0:
            self._lbl_notifications.setText(f"🔔 {count}")
            self._lbl_notifications.setToolTip(f"{count} notification(s)")
        else:
            self._lbl_notifications.setText("🔔 0")
            self._lbl_notifications.setToolTip("No notifications")
    
    def set_encoding(self, encoding: str):
        """Set the terminal encoding."""
        self._lbl_encoding.setText(encoding)
        self.encoding_changed.emit(encoding)
    
    def set_readonly(self, readonly: bool):
        """Set read-only mode."""
        if readonly:
            self._lbl_readonly.setText("🔒")
            self._lbl_readonly.setToolTip("Read Only Mode Enabled")
        else:
            self._lbl_readonly.setText("")
            self._lbl_readonly.setToolTip("Read Only Mode Disabled")
    
    def set_design_system(self, ds):
        """Set the design system."""
        self.ds = ds
        self._apply_styles()
    
    def update_from_session(self, command: str, shell: str,
                           jobs: int = 0, encoding: str = "UTF-8",
                           readonly: bool = False):
        """Update all indicators from a terminal session."""
        self.set_active_process(command)
        self.set_shell(shell)
        self.set_background_jobs(jobs)
        self.set_encoding(encoding)
        self.set_readonly(readonly)
