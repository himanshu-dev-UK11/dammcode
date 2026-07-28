"""Context Section - v1.0"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QProgressBar, QGroupBox, QGridLayout
from PySide6.QtCore import Qt
from core.logger import setup_logger
from pathlib import Path

logger = setup_logger(__name__)


class ContextSection(QWidget):
    """Display context information including selected files, current file details, and token usage."""
    def __init__(self, event_bus=None):
        super().__init__()
        self.event_bus = event_bus
        self._current_file_data = {}  # Stores current file info
        self._open_files = []         # Stores list of open files
        self.setup_ui()
        self.setup_subscriptions()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(8)

        # ── Current File Info Group ─────────────────────────
        self._file_info_group = QGroupBox("Current File")
        self._file_info_group.setStyleSheet("""
            QGroupBox {
                color: #8E8E98;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        file_info_layout = QGridLayout(self._file_info_group)
        file_info_layout.setContentsMargins(8, 6, 8, 8)
        file_info_layout.setSpacing(4)
        
        self._file_name_label = QLabel("File: —")
        self._file_name_label.setStyleSheet("color: #E2E2E6; font-size: 10px;")
        
        self._file_lang_label = QLabel("Lang: —")
        self._file_lang_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        
        self._cursor_label = QLabel("Cursor: —")
        self._cursor_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        
        self._stats_label = QLabel("Stats: —")
        self._stats_label.setStyleSheet("color: #8E8E98; font-size: 10px;")
        
        self._modified_label = QLabel("Saved")
        self._modified_label.setStyleSheet("""
            color: #22C55E; font-size: 10px; font-weight: 600;
            background-color: #14532D; padding: 2px 6px; border-radius: 3px;
        """)
        
        file_info_layout.addWidget(self._file_name_label, 0, 0, 1, 2)
        file_info_layout.addWidget(self._file_lang_label, 1, 0)
        file_info_layout.addWidget(self._cursor_label, 1, 1)
        file_info_layout.addWidget(self._stats_label, 2, 0)
        file_info_layout.addWidget(self._modified_label, 2, 1)
        
        layout.addWidget(self._file_info_group)
        
        # ── Open Files Info Group ──────────────────────────
        self._open_files_group = QGroupBox("Open Files")
        self._open_files_group.setStyleSheet("""
            QGroupBox {
                color: #8E8E98;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #252528;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        open_files_layout = QVBoxLayout(self._open_files_group)
        open_files_layout.setContentsMargins(8, 6, 8, 8)
        
        self._open_files_list = QListWidget()
        self._open_files_list.setMaximumHeight(100)
        self._open_files_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 10px;
                font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            }
            QListWidget::item {
                color: #8E8E98;
                padding: 2px 0;
                min-height: 18px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #1E3A5F;
                color: #E2E2E6;
            }
            QListWidget::item:hover {
                background-color: #161618;
                color: #E2E2E6;
            }
        """)
        open_files_layout.addWidget(self._open_files_list)
        
        layout.addWidget(self._open_files_group)
        
        # ── Token budget row ─────────────────────────
        token_row = QHBoxLayout()
        token_row.setSpacing(6)

        self._token_label = QLabel("∼0 tokens")
        self._token_label.setStyleSheet(
            "color: #E2E2E6; font-size: 11px; font-weight: 500; "
            "background-color: transparent;"
        )
        self._limit_label = QLabel("/ 128K limit")
        self._limit_label.setStyleSheet(
            "color: #52525C; font-size: 10px; background-color: transparent;"
        )
        token_row.addWidget(self._token_label)
        token_row.addWidget(self._limit_label)
        token_row.addStretch()
        layout.addLayout(token_row)

        self._token_bar = QProgressBar()
        self._token_bar.setRange(0, 100)
        self._token_bar.setValue(0)
        self._token_bar.setFixedHeight(3)
        self._token_bar.setTextVisible(False)
        self._token_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1C1C1F;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 1px;
            }
        """)
        layout.addWidget(self._token_bar)
        
    def setup_subscriptions(self):
        """Subscribe to relevant events from Event Bus."""
        if self.event_bus:
            self.event_bus.subscribe("tab_switched", self._on_tab_switched)
            self.event_bus.subscribe("cursor_moved", self._on_cursor_moved)
            self.event_bus.subscribe("file_modified_state", self._on_file_modified)
            self.event_bus.subscribe("file_opened", self._on_file_opened)
            self.event_bus.subscribe("file_closed", self._on_file_closed)
        
    def _on_tab_switched(self, data: dict):
        """Handle tab switching event."""
        path = data.get("path")
        if path:
            self._update_current_file_info(path)
        
    def _on_cursor_moved(self, data: dict):
        """Handle cursor position change."""
        line = data.get("line", 0)
        col = data.get("col", 0)
        total = data.get("total", 0)
        self._cursor_label.setText(f"Cursor: {line}:{col}")
        self._stats_label.setText(f"Stats: {total} lines")
        
    def _on_file_modified(self, data: dict):
        """Handle file modification state change."""
        modified = data.get("modified", False)
        if modified:
            self._modified_label.setText("Modified")
            self._modified_label.setStyleSheet("""
                color: #F59E0B; font-size: 10px; font-weight: 600;
                background-color: #3E2D0F; padding: 2px 6px; border-radius: 3px;
            """)
        else:
            self._modified_label.setText("Saved")
            self._modified_label.setStyleSheet("""
                color: #22C55E; font-size: 10px; font-weight: 600;
                background-color: #14532D; padding: 2px 6px; border-radius: 3px;
            """)
        
    def _on_file_opened(self, data: dict):
        """Handle file opening event."""
        path = data.get("path")
        if path and str(path) not in self._open_files:
            self._open_files.append(str(path))
            self._update_open_files_list()
        self._update_current_file_info(str(path))
        
    def _on_file_closed(self, data: dict):
        """Handle file closing event."""
        path = data.get("path")
        if path and path in self._open_files:
            self._open_files.remove(path)
            self._update_open_files_list()
        
    def _update_current_file_info(self, path_str: str):
        """Update current file display based on file path."""
        path = Path(path_str)
        self._file_name_label.setText(f"File: {path.name}")
        
        # Determine language by extension
        ext = path.suffix.lower()
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".md": "Markdown",
            ".txt": "Plain Text"
        }
        lang = lang_map.get(ext, "Unknown")
        self._file_lang_label.setText(f"Lang: {lang}")
        
        # Try to get line count (we'll need editor reference for accurate count)
        self._stats_label.setText("Stats: —")
        
    def _update_open_files_list(self):
        """Update the list of open files."""
        self._open_files_list.clear()
        for file_path in self._open_files:
            name = Path(file_path).name
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, file_path)
            self._open_files_list.addItem(item)
        
    def update_context(self, data: dict):
        """Update context display (kept for compatibility)."""
        token_est = data.get("token_estimate", 0)
        model_limit_k = 128
        pct = min(100, int(token_est / (model_limit_k * 1000) * 100))

        if token_est >= 1_000:
            token_str = f"∼{token_est // 1000}K tokens"
        else:
            token_str = f"∼{token_est} tokens"
        self._token_label.setText(token_str)
        self._token_bar.setValue(pct)

        # Color bar based on utilization
        if pct >= 85:
            bar_color = "#EF4444"
        elif pct >= 60:
            bar_color = "#F59E0B"
        else:
            bar_color = "#3B82F6"
        self._token_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1C1C1F;
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 1px;
            }}
        """)