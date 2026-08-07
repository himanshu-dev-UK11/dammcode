"""
Debug Console — Debug Message Display

Console for displaying runtime messages, exceptions, warnings, and debugger output.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QLabel, QFrame, QToolBar, QToolButton,
                               QComboBox, QMenu, QAction)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

from ui.processes.process import DebugMessage, ProcessStatus
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontFamily
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class DebugConsole(QWidget):
    """
    Debug console for displaying runtime messages, exceptions, warnings,
    debugger output, and application logs.
    """
    
    clear_requested = Signal()
    copy_requested = Signal()
    
    def __init__(self, process_manager, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager
        self.ds = get_design_system()
        
        self._setup_ui()
        self._setup_connections()
        self._load_messages()
    
    def _setup_ui(self):
        """Setup console UI."""
        p = self.ds.palette
        font = QFont(FontFamily.TERMINAL, FontSize.SM)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Message display
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(font)
        self._output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {p.terminal_bg};
                border: none;
                padding: {Spacing.MD}px;
                color: {p.text};
            }}
        """)
        self._output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._output)
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Process manager signals
        self.process_manager.debug_console_updated.connect(self._on_debug_updated)
    
    def _create_toolbar(self) -> QWidget:
        """Create toolbar with controls."""
        p = self.ds.palette
        
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background-color: {p.surface};
                border-bottom: 1px solid {p.border};
            }}
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(Spacing.MD, Spacing.XS, Spacing.MD, Spacing.XS)
        layout.setSpacing(Spacing.MD)
        
        # Level filter
        level_label = QLabel("Level:")
        level_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(level_label)
        
        self._level_filter = QComboBox()
        self._level_filter.addItem("All", None)
        self._level_filter.addItem("DEBUG", "DEBUG")
        self._level_filter.addItem("INFO", "INFO")
        self._level_filter.addItem("WARNING", "WARNING")
        self._level_filter.addItem("ERROR", "ERROR")
        self._level_filter.addItem("CRITICAL", "CRITICAL")
        self._level_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.editor_bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                color: {p.text};
                font-size: {FontSize.XS}px;
            }}
        """)
        self._level_filter.currentIndexChanged.connect(self._on_level_filter_changed)
        layout.addWidget(self._level_filter)
        
        layout.addSpacing(Spacing.MD)
        
        # Source filter
        source_label = QLabel("Source:")
        source_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(source_label)
        
        self._source_filter = QComboBox()
        self._source_filter.addItem("All", None)
        self._source_filter.addItem("Runtime", "runtime")
        self._source_filter.addItem("Exception", "exception")
        self._source_filter.addItem("Warning", "warning")
        self._source_filter.addItem("Debugger", "debugger")
        self._source_filter.addItem("Application", "app")
        self._source_filter.addItem("System", "system")
        self._source_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.editor_bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                color: {p.text};
                font-size: {FontSize.XS}px;
            }}
        """)
        self._source_filter.currentIndexChanged.connect(self._on_source_filter_changed)
        layout.addWidget(self._source_filter)
        
        layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.error};
                color: {p.text_on_error};
                border: none;
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                font-size: {FontSize.XS}px;
            }}
            
            QPushButton:hover {{
                background-color: {p.error_hover};
            }}
        """)
        clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(clear_btn)
        
        # Copy button
        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.surface_hover};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                font-size: {FontSize.XS}px;
            }}
            
            QPushButton:hover {{
                background-color: {p.accent};
                color: {p.text_on_accent};
                border-color: {p.accent};
            }}
        """)
        copy_btn.clicked.connect(self._on_copy)
        layout.addWidget(copy_btn)
        
        return toolbar
    
    def _load_messages(self):
        """Load messages from process manager."""
        messages = self.process_manager.get_debug_messages(limit=500)
        self._update_display(messages)
    
    def _update_display(self, messages):
        """Update message display."""
        self._output.clear()
        
        for msg in messages:
            self._append_message(msg)
        
        # Scroll to bottom
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output.setTextCursor(cursor)
    
    def _append_message(self, msg: DebugMessage):
        """Append a message to the display."""
        cursor = self._output.textCursor()
        
        # Format timestamp
        timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Format level and source
        level_color = msg.level_color
        level_text = f"[{msg.level}]"
        
        # Format source
        source_text = f"[{msg.source}]"
        
        # Create text with formatting
        text = f"{timestamp} {level_text} {source_text} {msg.message}"
        
        if msg.file and msg.line:
            text += f"\n    at {msg.file}:{msg.line}"
        
        if msg.stack_trace:
            text += f"\n{msg.stack_trace}"
        
        # Append text
        self._output.append(text)
    
    def _on_debug_updated(self):
        """Handle debug console update."""
        self._load_messages()
    
    def _on_level_filter_changed(self, index):
        """Handle level filter change."""
        level = self._level_filter.currentData()
        messages = self.process_manager.get_debug_messages(level=level)
        self._update_display(messages)
    
    def _on_source_filter_changed(self, index):
        """Handle source filter change."""
        source = self._source_filter.currentData()
        messages = self.process_manager.get_debug_messages_by_source(source)
        self._update_display(messages)
    
    def _on_clear(self):
        """Clear all messages."""
        self.process_manager.clear_debug_messages()
        self._output.clear()
    
    def _on_copy(self):
        """Copy all messages to clipboard."""
        clipboard = self.style().standardIcon().createApplication().clipboard()
        clipboard.setText(self._output.toPlainText())
    
    def add_message(self, level: str, message: str, source: str = "runtime",
                   file: str = None, line: int = None, stack_trace: str = None):
        """Add a message to the console."""
        self.process_manager.add_debug_message(
            level=level,
            message=message,
            source=source,
            file=file,
            line=line,
            stack_trace=stack_trace
        )
    
    def log_runtime(self, message: str, file: str = None, line: int = None):
        """Log a runtime message."""
        self.add_message("INFO", message, "runtime", file, line)
    
    def log_exception(self, exception: Exception, message: str = None):
        """Log an exception."""
        import traceback
        tb = traceback.format_exc()
        self.add_message("ERROR", message or str(exception), "exception", stack_trace=tb)
    
    def log_warning(self, message: str, file: str = None, line: int = None):
        """Log a warning."""
        self.add_message("WARNING", message, "warning", file, line)
    
    def log_debug(self, message: str):
        """Log a debug message."""
        self.add_message("DEBUG", message, "debugger")
    
    def log_system(self, message: str):
        """Log a system message."""
        self.add_message("INFO", message, "system")
    
    def clear(self):
        """Clear all messages."""
        self.process_manager.clear_debug_messages()
        self._output.clear()
