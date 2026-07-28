"""
Process Panel — Process Manager UI

Professional process manager panel with tabs, search, filters, and resource monitoring.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QLabel, QFrame, QSplitter, QHeaderView, QLineEdit,
                               QComboBox, QCheckBox, QProgressBar)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from ui.processes.process import Process, ProcessStatus, ProcessType
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontFamily
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class ProcessPanel(QWidget):
    """
    Professional process manager panel integrated with the terminal.
    Displays running processes with detailed information.
    """
    
    kill_process_requested = Signal(str)  # process_id
    restart_process_requested = Signal(str)  # process_id
    open_terminal_requested = Signal(str)  # working_directory
    
    def __init__(self, process_manager, terminal_panel, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager
        self.terminal_panel = terminal_panel
        self.ds = get_design_system()
        
        self._setup_ui()
        self._setup_connections()
        self._load_processes()
    
    def _setup_ui(self):
        """Setup panel UI."""
        p = self.ds.palette
        font = QFont(FontFamily.UI, FontSize.SM)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Tab bar for different views
        self._tab_bar = QTabWidget()
        self._tab_bar.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {p.border};
                border-top-left-radius: {Radius.MD}px;
                border-top-right-radius: {Radius.MD}px;
                background-color: {p.surface};
            }}
            
            QTabBar::tab {{
                background-color: {p.surface};
                color: {p.text_secondary};
                border: 1px solid transparent;
                border-top-left-radius: {Radius.SM}px;
                border-top-right-radius: {Radius.SM}px;
                padding: {Spacing.MD}px {Spacing.LG}px;
                margin-right: 2px;
                font-size: {FontSize.SM}px;
            }}
            
            QTabBar::tab:hover {{
                color: {p.text};
            }}
            
            QTabBar::tab:selected {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-bottom: 2px solid {p.accent};
            }}
        """)
        
        # Create tabs
        self._create_running_tab()
        self._create_completed_tab()
        self._create_failed_tab()
        self._create_killed_tab()
        self._create_background_tab()
        
        layout.addWidget(self._tab_bar)
        
        # Resource monitor
        self._resource_monitor = self._create_resource_monitor()
        layout.addWidget(self._resource_monitor)
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Process manager signals
        self.process_manager.process_created.connect(self._on_process_created)
        self.process_manager.process_updated.connect(self._on_process_updated)
        self.process_manager.process_killed.connect(self._on_process_killed)
        self.process_manager.process_restarted.connect(self._on_process_restarted)
        self.process_manager.resource_usage_updated.connect(self._on_resource_updated)
    
    def _create_toolbar(self) -> QWidget:
        """Create toolbar with search and filters."""
        p = self.ds.palette
        
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background-color: {p.surface};
                border-bottom: 1px solid {p.border};
            }}
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.MD)
        
        # Search
        search_label = QLabel("🔍")
        search_label.setStyleSheet(f"color: {p.text_tertiary}")
        layout.addWidget(search_label)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by PID, name, command, directory...")
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {p.editor_bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                color: {p.text};
            }}
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)
        
        layout.addSpacing(Spacing.LG)
        
        # Filter by status
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {p.text_tertiary}")
        layout.addWidget(filter_label)
        
        self._status_filter = QComboBox()
        self._status_filter.addItem("All", None)
        self._status_filter.addItem("Running", ProcessStatus.RUNNING.value)
        self._status_filter.addItem("Completed", ProcessStatus.COMPLETED.value)
        self._status_filter.addItem("Failed", ProcessStatus.FAILED.value)
        self._status_filter.addItem("Killed", ProcessStatus.KILLED.value)
        self._status_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.editor_bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                color: {p.text};
                min-width: 100px;
            }}
        """)
        self._status_filter.currentIndexChanged.connect(self._on_status_filter_changed)
        layout.addWidget(self._status_filter)
        
        # Filter by type
        self._type_filter = QComboBox()
        self._type_filter.addItem("All", None)
        self._type_filter.addItem("Foreground", ProcessType.FOREGROUND.value)
        self._type_filter.addItem("Background", ProcessType.BACKGROUND.value)
        self._type_filter.addItem("Long Running", ProcessType.LONG_RUNNING.value)
        self._type_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.editor_bg};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                color: {p.text};
                min-width: 100px;
            }}
        """)
        self._type_filter.currentIndexChanged.connect(self._on_type_filter_changed)
        layout.addWidget(self._type_filter)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.accent};
                color: {p.text_on_accent};
                border: none;
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
            }}
            
            QPushButton:hover {{
                background-color: {p.accent_hover};
            }}
        """)
        refresh_btn.clicked.connect(self._load_processes)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_running_tab(self):
        """Create running processes tab."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Process", "PID", "Status", "CPU", "Memory", "Duration", "Working Directory", "Actions"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self._get_table_style())
        
        table.cellDoubleClicked.connect(self._on_process_double_clicked)
        table.customContextMenuRequested.connect(lambda: self._on_context_menu(table))
        
        self._tab_bar.addTab(table, "Running")
    
    def _create_completed_tab(self):
        """Create completed processes tab."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Process", "PID", "Exit Code", "Duration", "Start Time", "End Time", "Working Directory"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self._get_table_style())
        
        self._tab_bar.addTab(table, "Completed")
    
    def _create_failed_tab(self):
        """Create failed processes tab."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Process", "PID", "Exit Code", "Duration", "Start Time", "End Time", "Working Directory"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self._get_table_style())
        
        self._tab_bar.addTab(table, "Failed")
    
    def _create_killed_tab(self):
        """Create killed processes tab."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Process", "PID", "Exit Code", "Duration", "Start Time", "End Time", "Working Directory"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self._get_table_style())
        
        self._tab_bar.addTab(table, "Killed")
    
    def _create_background_tab(self):
        """Create background processes tab."""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Process", "PID", "Status", "CPU", "Memory", "Duration", "Working Directory", "Actions"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self._get_table_style())
        
        table.cellDoubleClicked.connect(self._on_process_double_clicked)
        table.customContextMenuRequested.connect(lambda: self._on_context_menu(table))
        
        self._tab_bar.addTab(table, "Background")
    
    def _get_table_style(self) -> str:
        """Get table styling."""
        p = self.ds.palette
        return f"""
            QTableWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
            }}
            
            QTableWidget::item {{
                padding: {Spacing.SM}px;
            }}
            
            QTableWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
            
            QTableWidget::item:selected {{
                background-color: {p.accent};
                color: {p.text_on_accent};
            }}
            
            QTableWidget::cornerButton {{
                background-color: {p.surface};
            }}
        """
    
    def _create_resource_monitor(self) -> QWidget:
        """Create resource monitor widget."""
        p = self.ds.palette
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {p.surface};
                border-top: 1px solid {p.border};
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(Spacing.MD, Spacing.XS, Spacing.MD, Spacing.XS)
        layout.setSpacing(Spacing.MD)
        
        # CPU Usage
        cpu_label = QLabel("CPU:")
        cpu_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(cpu_label)
        
        self._cpu_usage = QLabel("0%")
        self._cpu_usage.setStyleSheet(f"color: {p.accent}; font-weight: bold; font-size: {FontSize.XS}px;")
        layout.addWidget(self._cpu_usage)
        
        layout.addSpacing(Spacing.MD)
        
        # Memory Usage
        mem_label = QLabel("RAM:")
        mem_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(mem_label)
        
        self._memory_usage = QLabel("0 MB")
        self._memory_usage.setStyleSheet(f"color: {p.success}; font-weight: bold; font-size: {FontSize.XS}px;")
        layout.addWidget(self._memory_usage)
        
        layout.addSpacing(Spacing.MD)
        
        # Process Count
        proc_label = QLabel("Processes:")
        proc_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(proc_label)
        
        self._process_count = QLabel("0")
        self._process_count.setStyleSheet(f"color: {p.text}; font-weight: bold; font-size: {FontSize.XS}px;")
        layout.addWidget(self._process_count)
        
        layout.addSpacing(Spacing.MD)
        
        # Terminal Count
        term_label = QLabel("Terminals:")
        term_label.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px;")
        layout.addWidget(term_label)
        
        self._terminal_count = QLabel("0")
        self._terminal_count.setStyleSheet(f"color: {p.text}; font-weight: bold; font-size: {FontSize.XS}px;")
        layout.addWidget(self._terminal_count)
        
        return widget
    
    def _load_processes(self):
        """Load all processes into the panel."""
        # Load running processes
        running = self.process_manager.get_running_processes()
        self._update_process_table(self._tab_bar.widget(0), running, show_actions=True)
        
        # Load completed processes
        completed = self.process_manager.get_completed_processes()
        self._update_process_table(self._tab_bar.widget(1), completed, show_actions=False)
        
        # Load failed processes
        failed = self.process_manager.get_failed_processes()
        self._update_process_table(self._tab_bar.widget(2), failed, show_actions=False)
        
        # Load killed processes
        killed = self.process_manager.get_killed_processes()
        self._update_process_table(self._tab_bar.widget(3), killed, show_actions=False)
        
        # Load background processes
        background = self.process_manager.get_background_processes()
        self._update_process_table(self._tab_bar.widget(4), background, show_actions=True)
    
    def _update_process_table(self, table, processes, show_actions=False):
        """Update process table with processes."""
        table.setRowCount(len(processes))
        
        for row, process in enumerate(processes):
            # Process name
            name_item = QTableWidgetItem(process.name)
            name_item.setData(Qt.UserRole, process.process_id)
            table.setItem(row, 0, name_item)
            
            # PID
            pid_item = QTableWidgetItem(str(process.pid or "-"))
            table.setItem(row, 1, pid_item)
            
            # Status
            status_item = QTableWidgetItem(process.status.value.upper())
            status_color = self._get_status_color(process.status)
            status_item.setForeground(status_color)
            table.setItem(row, 2, status_item)
            
            # CPU Usage
            cpu_item = QTableWidgetItem(f"{process.cpu_usage:.1f}%")
            table.setItem(row, 3, cpu_item)
            
            # Memory Usage
            mem_item = QTableWidgetItem(f"{process.memory_usage_mb:.1f} MB")
            table.setItem(row, 4, mem_item)
            
            # Duration
            duration_item = QTableWidgetItem(process.duration_str)
            table.setItem(row, 5, duration_item)
            
            # Working Directory
            dir_item = QTableWidgetItem(process.working_directory)
            table.setItem(row, 6, dir_item)
            
            # Actions (if showing)
            if show_actions:
                action_item = QTableWidgetItem("More")
                action_item.setForeground(self.ds.palette.accent)
                table.setItem(row, 7, action_item)
        
        # Resize columns to fit
        table.resizeColumnsToContents()
    
    def _get_status_color(self, status):
        """Get color for process status."""
        p = self.ds.palette
        colors = {
            ProcessStatus.RUNNING: p.accent,
            ProcessStatus.COMPLETED: p.success,
            ProcessStatus.FAILED: p.error,
            ProcessStatus.STOPPED: p.text_tertiary,
            ProcessStatus.KILLED: p.error,
            ProcessStatus.PAUSED: p.warning
        }
        return colors.get(status, p.text)
    
    # Event Handlers
    
    def _on_process_created(self, process_id):
        """Handle process created."""
        self._load_processes()
    
    def _on_process_updated(self, process_id):
        """Handle process updated."""
        self._load_processes()
    
    def _on_process_killed(self, process_id):
        """Handle process killed."""
        self._load_processes()
    
    def _on_process_restarted(self, process_id):
        """Handle process restarted."""
        self._load_processes()
    
    def _on_resource_updated(self, usage):
        """Handle resource usage update."""
        self._cpu_usage.setText(f"{usage.cpu_usage:.1f}%")
        self._memory_usage.setText(f"{usage.memory_usage_mb:.1f} MB")
        self._process_count.setText(str(usage.process_count))
        self._terminal_count.setText(str(usage.terminal_count))
    
    def _on_search_changed(self, text):
        """Handle search text change."""
        # Would implement search filtering
        pass
    
    def _on_status_filter_changed(self, index):
        """Handle status filter change."""
        # Would implement status filtering
        pass
    
    def _on_type_filter_changed(self, index):
        """Handle type filter change."""
        # Would implement type filtering
        pass
    
    def _on_process_double_clicked(self, row, column):
        """Handle process double-click."""
        table = self.sender()
        if table:
            item = table.item(row, 0)
            if item:
                process_id = item.data(Qt.UserRole)
                self.open_terminal_requested.emit(process_id)
    
    def _on_context_menu(self, table):
        """Show context menu for process."""
        item = table.currentItem()
        if not item:
            return
        
        process_id = item.data(Qt.UserRole)
        
        menu = self.style().standardIcon().createMenu(self)
        
        kill_action = menu.addAction("Kill Process")
        kill_action.triggered.connect(lambda: self.kill_process_requested.emit(process_id))
        
        restart_action = menu.addAction("Restart Process")
        restart_action.triggered.connect(lambda: self.restart_process_requested.emit(process_id))
        
        open_terminal_action = menu.addAction("Open Terminal Here")
        open_terminal_action.triggered.connect(lambda: self.open_terminal_requested.emit(process_id))
        
        menu.exec(table.viewport().mapToGlobal(table.visualRect(item.index()).bottomLeft()))
