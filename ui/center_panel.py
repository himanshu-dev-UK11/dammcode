
"""
Center Panel - Simple editor container.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from ui.editor.editor_tabs import EditorTabs
from ui.dashboard import Dashboard


class CenterPanel(QWidget):
    """
    Simple container for Welcome Screen and Editor Tabs.
    Always expands to fill available space.
    """
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.bottom_dock = None  # Backward compatibility only

        self.setup_ui()
        self.setup_shortcuts()
        
        # Set proper size policies to expand fully!
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.event_bus.subscribe("file_opened", self._on_file_opened)
        self.event_bus.subscribe("file_closed", self._on_file_closed)
        self.event_bus.subscribe("editor_save_current_requested", self._on_save_current_requested)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Editor area (stacked: dashboard or editor tabs)
        self._editor_area = QStackedWidget()
        self._editor_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.dashboard = Dashboard(self.event_bus)
        self.editor_tabs = EditorTabs(self.event_bus)

        self._editor_area.addWidget(self.dashboard)
        self._editor_area.addWidget(self.editor_tabs)
        self._editor_area.setCurrentWidget(self.dashboard)

        layout.addWidget(self._editor_area)

    def setup_shortcuts(self):
        """Register keyboard shortcuts (forward to main window if needed)."""
        pass

    def _on_file_opened(self, data):
        """Show editor tabs when a file is opened."""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info(f"[CenterPanel] File opened: {data}")

        path = data.get("path")
        content = data.get("content", "")
        read_only = data.get("read_only", False)

        if path:
            self._editor_area.setCurrentWidget(self.editor_tabs)
            self.editor_tabs.open_file(path, content, read_only=read_only)

    def _on_save_current_requested(self, data):
        editor = self.editor_tabs.get_current_editor()
        if editor and hasattr(editor, "file_path") and editor.file_path:
            self.event_bus.publish("request_save_file", {
                "editor": editor,
                "path": editor.file_path
            })

    def _on_file_closed(self, data):
        if not self.editor_tabs.editors:
            self._editor_area.setCurrentWidget(self.dashboard)

    def set_bottom_dock(self, dock):
        """Backward compatibility method; unused now."""
        self.bottom_dock = dock

    def set_lsp_manager(self, lsp_manager):
        if hasattr(self, "editor_tabs"):
            self.editor_tabs.set_lsp_manager(lsp_manager)

    def switch_view(self, view_name: str):
        """Backward compatibility stub."""
        pass
