"""
Terminal Breadcrumb — v2.1

Displays workspace, current folder, shell, user, and host information.
Automatically updates when directory changes.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QStyle, QFrame
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from pathlib import Path
import platform
import getpass
from typing import Optional
from core.logger import setup_logger

logger = setup_logger(__name__)


class TerminalBreadcrumb(QFrame):
    """
    Display terminal context breadcrumb with workspace, folder, shell, user, and host.
    """
    
    # Signals
    directory_changed = Signal(str)  # new directory path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = None  # Will be set by parent
        self._setup_ui()
        self._setup_connections()
        
        # Timer for debouncing directory updates
        self._dir_update_timer = QTimer(self)
        self._dir_update_timer.setInterval(300)
        self._dir_update_timer.setSingleShot(True)
        self._dir_update_timer.timeout.connect(self._emit_directory_changed)
    
    def _setup_ui(self):
        """Setup breadcrumb UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Workspace icon and name
        self._lbl_workspace = QLabel()
        self._lbl_workspace.setObjectName("workspace_label")
        self._lbl_workspace.setToolTip("Workspace")
        layout.addWidget(self._lbl_workspace)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Current folder
        self._lbl_folder = QLabel()
        self._lbl_folder.setObjectName("folder_label")
        self._lbl_folder.setToolTip("Current Folder")
        layout.addWidget(self._lbl_folder)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Shell
        self._lbl_shell = QLabel()
        self._lbl_shell.setObjectName("shell_label")
        self._lbl_shell.setToolTip("Shell")
        layout.addWidget(self._lbl_shell)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # User
        self._lbl_user = QLabel()
        self._lbl_user.setObjectName("user_label")
        self._lbl_user.setToolTip("User")
        layout.addWidget(self._lbl_user)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Host
        self._lbl_host = QLabel()
        self._lbl_host.setObjectName("host_label")
        self._lbl_host.setToolTip("Host")
        layout.addWidget(self._lbl_host)
        
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
        pass  # No connections needed
    
    def _apply_styles(self):
        """Apply professional styling."""
        p = self.ds.palette if self.ds else None
        if not p:
            return
        
        self.setStyleSheet(f"""
            TerminalBreadcrumb {{
                background-color: {p.surface};
                border-bottom: 1px solid {p.border};
            }}
            
            QLabel {{
                font-size: 11px;
                padding: 2px 4px;
                min-width: 60px;
            }}
            
            QLabel#workspace_label {{
                color: {p.text_secondary};
                font-weight: bold;
            }}
            
            QLabel#folder_label {{
                color: {p.text};
                font-family: "JetBrains Mono", monospace;
                max-width: 200px;
                qProperty-translation: "text-overflow: ellipsis";
            }}
            
            QLabel#shell_label {{
                color: {p.accent};
                font-family: "JetBrains Mono", monospace;
            }}
            
            QLabel#user_label {{
                color: {p.text_tertiary};
            }}
            
            QLabel#host_label {{
                color: {p.text_tertiary};
                font-family: "JetBrains Mono", monospace;
            }}
            
            QLabel#separator {{
                color: {p.border};
            }}
        """)
    
    def set_workspace(self, path: str):
        """Set the workspace path."""
        try:
            workspace = Path(path)
            name = workspace.name if workspace.name else str(workspace)
            self._lbl_workspace.setText(f"🏠 {name}")
            self._lbl_workspace.setToolTip(str(path))
        except Exception as e:
            logger.warning(f"Failed to set workspace: {e}")
    
    def set_folder(self, path: str):
        """Set the current folder."""
        try:
            folder = Path(path)
            # Show relative path if possible
            rel_path = folder
            if hasattr(self, '_workspace_path'):
                try:
                    rel_path = folder.relative_to(self._workspace_path)
                except ValueError:
                    pass
            
            display_path = str(rel_path)
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]
            
            self._lbl_folder.setText(display_path)
            self._lbl_folder.setToolTip(str(folder))
        except Exception as e:
            logger.warning(f"Failed to set folder: {e}")
    
    def set_shell(self, shell: str):
        """Set the shell name."""
        self._lbl_shell.setText(f"▶ {shell}")
    
    def set_user(self, user: str = None):
        """Set the username."""
        if user is None:
            try:
                user = getpass.getuser()
            except:
                user = "unknown"
        self._lbl_user.setText(user)
    
    def set_host(self, host: str = None):
        """Set the hostname."""
        if host is None:
            try:
                host = platform.node()
            except:
                host = "unknown"
        self._lbl_host.setText(host)
    
    def set_directory(self, path: str):
        """Set the current working directory."""
        self.set_folder(path)
        self._workspace_path = path
    
    def set_design_system(self, ds):
        """Set the design system."""
        self.ds = ds
        self._apply_styles()
    
    def update_from_session(self, working_dir: str, shell: str):
        """Update all breadcrumb fields from a terminal session."""
        self.set_folder(working_dir)
        self.set_shell(shell)
        
        # Update workspace based on working directory
        try:
            # Go up 2 levels to find workspace
            dir_path = Path(working_dir)
            workspace = dir_path.parent.parent
            self.set_workspace(str(workspace))
        except Exception:
            self.set_workspace(working_dir)
        
        self.set_user()
        self.set_host()
    
    def _emit_directory_changed(self):
        """Emit directory changed signal."""
        if hasattr(self, '_current_directory'):
            self.directory_changed.emit(self._current_directory)
