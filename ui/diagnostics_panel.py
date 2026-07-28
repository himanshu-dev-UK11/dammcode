"""
Diagnostics Panel — v1.8.5

Displays:
  - Performance metrics (memory, CPU, threads)
  - Error history
  - Resource usage
  - System information
  - LSP Diagnostics (errors, warnings, hints from language servers)
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QFrame, QSplitter,
    QTextEdit, QGridLayout, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

from core.logger import setup_logger
from core.error_manager import get_error_manager, ErrorSeverity
from core.resource_manager import get_resource_manager
from core.performance_watchdog import get_performance_watchdog

logger = setup_logger(__name__)


class LSPDiagnosticsWidget(QWidget):
    """Widget that displays LSP diagnostics (errors, warnings, hints)."""
    
    def __init__(self):
        super().__init__()
        self._diagnostics = {}  # {file_path: [diagnostic]}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        self._count_label = QLabel("Diagnostics: 0")
        self._count_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        header_layout.addWidget(self._count_label)
        
        # File filter
        self._file_filter = QComboBox()
        self._file_filter.setPlaceholderText("Filter by file...")
        self._file_filter.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1F;
                color: #E2E2E6;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        self._file_filter.currentTextChanged.connect(self._refresh_diagnostics)
        header_layout.addWidget(self._file_filter)
        
        header_layout.addStretch()
        
        # Severity filter checkboxes
        self._cb_error = QCheckBox("Errors")
        self._cb_warning = QCheckBox("Warnings")
        self._cb_info = QCheckBox("Info")
        self._cb_hint = QCheckBox("Hints")
        
        for cb in [self._cb_error, self._cb_warning, self._cb_info, self._cb_hint]:
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 11px; color: #8E8E98;")
            cb.stateChanged.connect(self._refresh_diagnostics)
            header_layout.addWidget(cb)
        
        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #252528;
                color: #E2E2E6;
            }
        """)
        self._clear_btn.clicked.connect(self._clear_diagnostics)
        header_layout.addWidget(self._clear_btn)
        
        layout.addLayout(header_layout)
        
        # Diagnostics list
        self._diag_list = QListWidget()
        self._diag_list.setStyleSheet("""
            QListWidget {
                background-color: #0D0D0F;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                font-family: "JetBrains Mono", monospace;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #1C1C1F;
            }
            QListWidget::item:selected {
                background-color: #1E3A5F;
            }
        """)
        self._diag_list.itemClicked.connect(self._show_diag_details)
        layout.addWidget(self._diag_list)
        
        # Details
        self._details_label = QLabel("Select a diagnostic to see details")
        self._details_label.setStyleSheet("font-size: 11px; color: #52525C; margin-top: 8px;")
        layout.addWidget(self._details_label)
        
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(150)
        self._details_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D0D0F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-family: "JetBrains Mono", monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self._details_text)
    
    def update_diagnostics(self, file_path: str, diagnostics: list):
        """Update diagnostics for a specific file."""
        self._diagnostics[file_path] = diagnostics
        self._update_file_filter()
        self._refresh_diagnostics()
    
    def _update_file_filter(self):
        """Update the file filter dropdown."""
        current = self._file_filter.currentText()
        self._file_filter.blockSignals(True)
        self._file_filter.clear()
        self._file_filter.addItem("All Files")
        for path in self._diagnostics.keys():
            self._file_filter.addItem(Path(path).name)
        if current and self._file_filter.findText(current) != -1:
            self._file_filter.setCurrentText(current)
        self._file_filter.blockSignals(False)
    
    def _refresh_diagnostics(self):
        """Refresh the diagnostics list based on filters."""
        self._diag_list.clear()
        selected_file = self._file_filter.currentText()
        
        # Severity map from LSP
        severity_map = {
            1: ("Error", "#EF4444"),
            2: ("Warning", "#F59E0B"),
            3: ("Info", "#10B981"),
            4: ("Hint", "#60A5FA")
        }
        
        filter_severities = []
        if self._cb_error.isChecked():
            filter_severities.append(1)
        if self._cb_warning.isChecked():
            filter_severities.append(2)
        if self._cb_info.isChecked():
            filter_severities.append(3)
        if self._cb_hint.isChecked():
            filter_severities.append(4)
        
        total = 0
        for file_path, diags in self._diagnostics.items():
            if selected_file != "All Files" and selected_file != Path(file_path).name:
                continue
            
            for diag in diags:
                if diag.get("severity") not in filter_severities:
                    continue
                
                severity_name, color = severity_map.get(diag.get("severity", 1), ("Unknown", "#8E8E98"))
                line = diag.get("range", {}).get("start", {}).get("line", 0) + 1
                char = diag.get("range", {}).get("start", {}).get("character", 0) + 1
                message = diag.get("message", "")
                text = f"[{Path(file_path).name}:{line}:{char}] [{severity_name}] {message}"
                
                item = QListWidgetItem(text)
                item.setForeground(QColor(color))
                item.setData(Qt.UserRole, (file_path, diag))
                self._diag_list.addItem(item)
                total += 1
        
        self._count_label.setText(f"Diagnostics: {total}")
    
    def _show_diag_details(self, item):
        """Show details for a selected diagnostic."""
        file_path, diag = item.data(Qt.UserRole)
        if diag:
            details = (
                f"File: {file_path}\n"
                f"Severity: {diag.get('severity', 'Unknown')}\n"
                f"Line: {diag.get('range', {}).get('start', {}).get('line', 0) + 1}\n"
                f"Character: {diag.get('range', {}).get('start', {}).get('character', 0) + 1}\n"
                f"Message:\n{diag.get('message', '')}\n"
            )
            if "code" in diag:
                details += f"\nCode: {diag['code']}"
            if "source" in diag:
                details += f"\nSource: {diag['source']}"
            
            self._details_text.setText(details)
    
    def _clear_diagnostics(self):
        """Clear all diagnostics."""
        self._diagnostics.clear()
        self._diag_list.clear()
        self._details_text.clear()
        self._count_label.setText("Diagnostics: 0")
        self._update_file_filter()


class PerformanceMetricsWidget(QWidget):
    """Widget that displays real-time performance metrics."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_metrics)
        self._timer.start(1000)  # Update every second
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Metrics grid
        grid = QGridLayout()
        grid.setSpacing(12)
        
        # Memory
        self._mem_label = QLabel("Memory: --")
        self._mem_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        grid.addWidget(self._mem_label, 0, 0)
        
        self._mem_value = QLabel("-- MB")
        self._mem_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #E2E2E6;")
        grid.addWidget(self._mem_value, 1, 0)
        
        # CPU
        self._cpu_label = QLabel("CPU: --")
        self._cpu_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        grid.addWidget(self._cpu_label, 0, 1)
        
        self._cpu_value = QLabel("--%")
        self._cpu_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #E2E2E6;")
        grid.addWidget(self._cpu_value, 1, 1)
        
        # Threads
        self._thread_label = QLabel("Threads: --")
        self._thread_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        grid.addWidget(self._thread_label, 0, 2)
        
        self._thread_value = QLabel("--")
        self._thread_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #E2E2E6;")
        grid.addWidget(self._thread_value, 1, 2)
        
        # Objects
        self._obj_label = QLabel("Objects: --")
        self._obj_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        grid.addWidget(self._obj_label, 0, 3)
        
        self._obj_value = QLabel("--")
        self._obj_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #E2E2E6;")
        grid.addWidget(self._obj_value, 1, 3)
        
        layout.addLayout(grid)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #252528;")
        layout.addWidget(divider)
        
        # Stats label
        self._stats_label = QLabel("System Statistics")
        self._stats_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #52525C; letter-spacing: 0.5px;")
        layout.addWidget(self._stats_label)
        
        # Stats text
        self._stats_text = QTextEdit()
        self._stats_text.setReadOnly(True)
        self._stats_text.setMaximumHeight(150)
        self._stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D0D0F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-family: "JetBrains Mono", monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self._stats_text)
    
    def _update_metrics(self):
        """Update metrics from PerformanceWatchdog."""
        try:
            watchdog = get_performance_watchdog()
            metrics = watchdog.get_current_metrics()
            
            if metrics:
                self._mem_value.setText(f"{metrics.memory_used_mb:.1f} MB")
                self._mem_label.setText(f"Memory: {metrics.memory_percent:.1f}%")
                
                self._cpu_value.setText(f"{metrics.cpu_percent:.1f}%")
                self._thread_value.setText(str(metrics.thread_count))
                self._obj_value.setText(f"{metrics.object_count:,}")
                
                # Update color based on usage
                if metrics.memory_percent > 80:
                    self._mem_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;")
                elif metrics.memory_percent > 60:
                    self._mem_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #F59E0B;")
                else:
                    self._mem_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
                
                if metrics.cpu_percent > 80:
                    self._cpu_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;")
                elif metrics.cpu_percent > 60:
                    self._cpu_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #F59E0B;")
                else:
                    self._cpu_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
                
                # Update stats
                stats = watchdog.get_statistics()
                if stats:
                    stats_text = (
                        f"Total samples: {stats.get('samples', 0)}\n"
                        f"Memory - Min: {stats.get('memory', {}).get('min', 0):.1f}%, "
                        f"Max: {stats.get('memory', {}).get('max', 0):.1f}%, "
                        f"Avg: {stats.get('memory', {}).get('avg', 0):.1f}%\n"
                        f"CPU - Min: {stats.get('cpu', {}).get('min', 0):.1f}%, "
                        f"Max: {stats.get('cpu', {}).get('max', 0):.1f}%, "
                        f"Avg: {stats.get('cpu', {}).get('avg', 0):.1f}%"
                    )
                    self._stats_text.setText(stats_text)
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")


class ErrorHistoryWidget(QWidget):
    """Widget that displays error history."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_errors)
        self._refresh_timer.start(2000)  # Refresh every 2 seconds
        self._refresh_errors()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        self._count_label = QLabel("Errors: 0")
        self._count_label.setStyleSheet("font-size: 12px; color: #8E8E98;")
        header_layout.addWidget(self._count_label)
        
        header_layout.addStretch()
        
        self._clear_btn = QPushButton("Clear History")
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #252528;
                color: #E2E2E6;
            }
        """)
        self._clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(self._clear_btn)
        
        layout.addLayout(header_layout)
        
        # Error list
        self._error_list = QListWidget()
        self._error_list.setStyleSheet("""
            QListWidget {
                background-color: #0D0D0F;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                font-family: "JetBrains Mono", monospace;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #1C1C1F;
            }
            QListWidget::item:selected {
                background-color: #1E3A5F;
            }
        """)
        self._error_list.itemClicked.connect(self._show_error_details)
        layout.addWidget(self._error_list)
        
        # Error details
        self._details_label = QLabel("Select an error to see details")
        self._details_label.setStyleSheet("font-size: 11px; color: #52525C; margin-top: 8px;")
        layout.addWidget(self._details_label)
        
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(120)
        self._details_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D0D0F;
                color: #8E8E98;
                border: 1px solid #252528;
                border-radius: 4px;
                padding: 8px;
                font-family: "JetBrains Mono", monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self._details_text)
    
    def _refresh_errors(self):
        """Refresh error list from ErrorManager."""
        try:
            error_manager = get_error_manager()
            errors = error_manager.get_error_history(limit=100)
            
            self._error_list.clear()
            self._count_label.setText(f"Errors: {len(errors)}")
            
            for error in reversed(errors):  # Show newest first
                severity_colors = {
                    ErrorSeverity.CRITICAL: "#EF4444",
                    ErrorSeverity.ERROR: "#F59E0B",
                    ErrorSeverity.WARNING: "#60A5FA",
                    ErrorSeverity.INFO: "#10B981"
                }
                color = severity_colors.get(error.severity, "#8E8E98")
                
                time_str = error.timestamp.strftime("%H:%M:%S")
                text = f"[{time_str}] [{error.component}] {error.message}"
                
                item = QListWidgetItem(text)
                item.setForeground(QColor(color))
                item.setData(Qt.UserRole, error)
                self._error_list.addItem(item)
        except Exception as e:
            logger.error(f"Error refreshing error history: {e}")
    
    def _show_error_details(self, item):
        """Show details for a selected error."""
        error = item.data(Qt.UserRole)
        if error:
            details = (
                f"Time: {error.timestamp.isoformat()}\n"
                f"Severity: {error.severity.name}\n"
                f"Component: {error.component}\n"
                f"Message: {error.message}\n"
            )
            if error.exception_type:
                details += f"Exception: {error.exception_type}\n"
            if error.traceback:
                details += f"\nTraceback:\n{error.traceback}"
            if error.context:
                details += f"\nContext:\n{error.context}"
            
            self._details_text.setText(details)
    
    def _clear_history(self):
        """Clear error history."""
        try:
            error_manager = get_error_manager()
            error_manager.clear_history()
            self._refresh_errors()
            self._details_text.clear()
            self._details_label.setText("Select an error to see details")
        except Exception as e:
            logger.error(f"Error clearing history: {e}")


class ResourceUsageWidget(QWidget):
    """Widget that displays resource usage."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_resources)
        self._refresh_timer.start(2000)
        self._refresh_resources()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Resource list
        self._resource_list = QListWidget()
        self._resource_list.setStyleSheet("""
            QListWidget {
                background-color: #0D0D0F;
                border: 1px solid #252528;
                border-radius: 4px;
                font-size: 11px;
                font-family: "JetBrains Mono", monospace;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #1C1C1F;
            }
        """)
        layout.addWidget(self._resource_list)
    
    def _refresh_resources(self):
        """Refresh resource list from ResourceManager."""
        try:
            resource_manager = get_resource_manager()
            counts = resource_manager.get_resource_count()
            active = resource_manager.get_active_resources()
            
            self._resource_list.clear()
            
            # Summary
            self._resource_list.addItem(f"Total active resources: {len(active)}")
            self._resource_list.addItem("")
            
            # By type
            for resource_type, count in counts.items():
                self._resource_list.addItem(f"{resource_type.name}: {count}")
            
            self._resource_list.addItem("")
            
            # Active resources
            for resource in active:
                desc = resource.description or "Unnamed"
                text = f"[{resource.resource_type.name}] {desc} (ID: {resource.resource_id})"
                item = QListWidgetItem(text)
                item.setForeground(QColor("#60A5FA"))
                self._resource_list.addItem(item)
        except Exception as e:
            logger.error(f"Error refreshing resources: {e}")


class DiagnosticsTab(QWidget):
    """Diagnostics tab for BottomDock."""
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #0D0D0F;
            }
            QTabBar {
                background-color: #1C1C1F;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #52525C;
                padding: 3px 12px;
                border: none;
                border-right: 1px solid #252528;
                font-size: 11px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                color: #E2E2E6;
                border-bottom: 1px solid #3B82F6;
                background-color: #0D0D0F;
            }
            QTabBar::tab:hover:!selected {
                color: #8E8E98;
                background-color: #161618;
            }
        """)
        
        # Add tabs
        self._lsp_diag_widget = LSPDiagnosticsWidget()
        self._tabs.addTab(self._lsp_diag_widget, "LSP Diagnostics")
        self._tabs.addTab(PerformanceMetricsWidget(), "Performance")
        self._tabs.addTab(ErrorHistoryWidget(), "Errors")
        self._tabs.addTab(ResourceUsageWidget(), "Resources")
        
        layout.addWidget(self._tabs)
    
    def update_lsp_diagnostics(self, file_path: str, diagnostics: list):
        """Update LSP diagnostics."""
        self._lsp_diag_widget.update_diagnostics(file_path, diagnostics)
