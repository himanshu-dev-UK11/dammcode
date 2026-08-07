"""
Task Panel — Task System UI

Professional tasks panel for the integrated terminal.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QListWidget, QListWidgetItem, QPushButton, 
                               QLabel, QFrame, QSplitter, QMenu, QAction,
                               QToolButton, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor

from ui.tasks.task import Task, TaskStatus
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontFamily
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class TaskPanel(QWidget):
    """
    Professional tasks panel integrated with the terminal.
    Displays recent, running, pinned, favorite, and completed tasks.
    """
    
    execute_task_requested = Signal(str)  # task_id
    cancel_task_requested = Signal(str)  # task_id
    edit_task_requested = Signal(str)  # task_id
    delete_task_requested = Signal(str)  # task_id
    
    def __init__(self, task_manager, terminal_panel, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.terminal_panel = terminal_panel
        self.ds = get_design_system()
        
        self._setup_ui()
        self._setup_connections()
        self._load_tasks()
    
    def _setup_ui(self):
        """Setup panel UI."""
        p = self.ds.palette
        font = QFont(FontFamily.UI, FontSize.SM)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
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
        self._create_recent_tab()
        self._create_running_tab()
        self._create_pinned_tab()
        self._create_favorite_tab()
        self._create_completed_tab()
        
        layout.addWidget(self._tab_bar)
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Task manager signals
        self.task_manager.task_created.connect(self._on_task_created)
        self.task_manager.task_deleted.connect(self._on_task_deleted)
        self.task_manager.task_started.connect(self._on_task_started)
        self.task_manager.task_finished.connect(self._on_task_finished)
        self.task_manager.task_failed.connect(self._on_task_failed)
        self.task_manager.task_cancelled.connect(self._on_task_cancelled)
    
    def _create_recent_tab(self):
        """Create recent tasks tab."""
        list_widget = QListWidget()
        list_widget.setFont(font)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
                padding: {Spacing.SM}px;
            }}
            
            QListWidget::item {{
                padding: {Spacing.MD}px;
                margin-bottom: {Spacing.XS}px;
                border-radius: {Radius.SM}px;
                border: 1px solid {p.border};
                background-color: {p.editor_bg};
            }}
            
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
                border-color: {p.accent};
            }}
            
            QListWidget::item:selected {{
                background-color: {p.accent};
                color: {p.text_on_accent};
                border-color: {p.accent};
            }}
        """)
        
        list_widget.itemDoubleClicked.connect(self._on_task_double_clicked)
        list_widget.customContextMenuRequested.connect(self._on_recent_context_menu)
        
        self._tab_bar.addTab(list_widget, "Recent")
    
    def _create_running_tab(self):
        """Create running tasks tab."""
        list_widget = QListWidget()
        list_widget.setFont(font)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
                padding: {Spacing.SM}px;
            }}
            
            QListWidget::item {{
                padding: {Spacing.MD}px;
                margin-bottom: {Spacing.XS}px;
                border-radius: {Radius.SM}px;
                border: 1px solid {p.border};
                background-color: {p.editor_bg};
            }}
            
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        
        stop_btn = QPushButton("Stop All")
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.error};
                color: {p.text_on_error};
                border: none;
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.SM}px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {p.error_hover};
            }}
        """)
        stop_btn.clicked.connect(self._on_stop_all_running)
        
        layout = QVBoxLayout()
        layout.addWidget(stop_btn)
        layout.addWidget(list_widget)
        
        container = QWidget()
        container.setLayout(layout)
        self._tab_bar.addTab(container, "Running")
    
    def _create_pinned_tab(self):
        """Create pinned tasks tab."""
        list_widget = QListWidget()
        list_widget.setFont(font)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
                padding: {Spacing.SM}px;
            }}
            
            QListWidget::item {{
                padding: {Spacing.MD}px;
                margin-bottom: {Spacing.XS}px;
                border-radius: {Radius.SM}px;
                border: 1px solid {p.border};
                background-color: {p.editor_bg};
            }}
            
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        
        list_widget.itemDoubleClicked.connect(self._on_task_double_clicked)
        list_widget.customContextMenuRequested.connect(self._on_pinned_context_menu)
        
        self._tab_bar.addTab(list_widget, "Pinned")
    
    def _create_favorite_tab(self):
        """Create favorite tasks tab."""
        list_widget = QListWidget()
        list_widget.setFont(font)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
                padding: {Spacing.SM}px;
            }}
            
            QListWidget::item {{
                padding: {Spacing.MD}px;
                margin-bottom: {Spacing.XS}px;
                border-radius: {Radius.SM}px;
                border: 1px solid {p.border};
                background-color: {p.editor_bg};
            }}
            
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        
        list_widget.itemDoubleClicked.connect(self._on_task_double_clicked)
        list_widget.customContextMenuRequested.connect(self._on_favorite_context_menu)
        
        self._tab_bar.addTab(list_widget, "Favorite")
    
    def _create_completed_tab(self):
        """Create completed tasks tab."""
        list_widget = QListWidget()
        list_widget.setFont(font)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.surface};
                border: none;
                outline: none;
                padding: {Spacing.SM}px;
            }}
            
            QListWidget::item {{
                padding: {Spacing.MD}px;
                margin-bottom: {Spacing.XS}px;
                border-radius: {Radius.SM}px;
                border: 1px solid {p.border};
                background-color: {p.editor_bg};
            }}
            
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.error};
                color: {p.text_on_error};
                border: none;
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.SM}px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {p.error_hover};
            }}
        """)
        clear_btn.clicked.connect(self._on_clear_history)
        
        layout = QVBoxLayout()
        layout.addWidget(clear_btn)
        layout.addWidget(list_widget)
        
        container = QWidget()
        container.setLayout(layout)
        self._tab_bar.addTab(container, "Completed")
    
    def _load_tasks(self):
        """Load all tasks into the panel."""
        # Load running tasks
        running_tasks = self.task_manager.get_running_tasks()
        self._update_task_list(self._tab_bar.widget(1), running_tasks, TaskStatus.RUNNING)
        
        # Load pinned tasks
        pinned_tasks = self.task_manager.get_pinned_tasks()
        self._update_task_list(self._tab_bar.widget(2), pinned_tasks, TaskStatus.QUEUED)
        
        # Load favorite tasks
        favorite_tasks = self.task_manager.get_favorite_tasks()
        self._update_task_list(self._tab_bar.widget(3), favorite_tasks, TaskStatus.QUEUED)
        
        # Load recent tasks
        history = self.task_manager.get_task_history(20)
        self._update_history_list(self._tab_bar.widget(0), history)
        
        # Load completed tasks
        all_history = self.task_manager.get_task_history(50)
        self._update_history_list(self._tab_bar.widget(4), all_history)
    
    def _update_task_list(self, list_widget, tasks, status):
        """Update task list widget."""
        list_widget.clear()
        
        for task in tasks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, task.id)
            
            status_color = self._get_status_color(status)
            status_text = status.value.upper()
            
            item.setText(f"  {task.name}  [{status_text}]")
            item.setForeground(status_color)
            
            list_widget.addItem(item)
    
    def _update_history_list(self, list_widget, history):
        """Update history list widget."""
        list_widget.clear()
        
        for record in reversed(history):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, record.task_id)
            
            if record.status == "completed":
                status_color = self.ds.palette.success
                status_text = "✓ COMPLETED"
            else:
                status_color = self.ds.palette.error
                status_text = "✗ FAILED"
            
            duration_str = f"{record.execution_time_ms / 1000:.1f}s" if record.execution_time_ms else "N/A"
            
            item.setText(f"  {record.task_name}  [{status_text}  {duration_str}]")
            item.setForeground(status_color)
            
            list_widget.addItem(item)
    
    def _get_status_color(self, status):
        """Get color for task status."""
        p = self.ds.palette
        colors = {
            TaskStatus.QUEUED: p.text_secondary,
            TaskStatus.RUNNING: p.accent,
            TaskStatus.COMPLETED: p.success,
            TaskStatus.FAILED: p.error,
            TaskStatus.CANCELLED: p.text_tertiary
        }
        return colors.get(status, p.text_secondary)
    
    # Event Handlers
    
    def _on_task_created(self, task_id):
        """Handle task created."""
        self._load_tasks()
    
    def _on_task_deleted(self, task_id):
        """Handle task deleted."""
        self._load_tasks()
    
    def _on_task_started(self, task_id):
        """Handle task started."""
        self._load_tasks()
    
    def _on_task_finished(self, task_id, exit_code, duration_ms):
        """Handle task finished."""
        self._load_tasks()
    
    def _on_task_failed(self, task_id, exit_code):
        """Handle task failed."""
        self._load_tasks()
    
    def _on_task_cancelled(self, task_id):
        """Handle task cancelled."""
        self._load_tasks()
    
    def _on_task_double_clicked(self, item):
        """Handle task double-click."""
        task_id = item.data(Qt.UserRole)
        self.execute_task_requested.emit(task_id)
    
    def _on_recent_context_menu(self, pos):
        """Show context menu for recent tab."""
        item = self._tab_bar.widget(0).itemAt(pos)
        if not item:
            return
        
        task_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        rerun_action = QAction("Rerun", menu)
        rerun_action.triggered.connect(lambda: self._rerun_from_history(task_id))
        menu.addAction(rerun_action)
        
        open_terminal_action = QAction("Open Terminal Here", menu)
        open_terminal_action.triggered.connect(lambda: self._open_terminal_at_task(task_id))
        menu.addAction(open_terminal_action)
        
        menu.exec(self._tab_bar.widget(0).mapToGlobal(pos))
    
    def _on_pinned_context_menu(self, pos):
        """Show context menu for pinned tab."""
        item = self._tab_bar.widget(2).itemAt(pos)
        if not item:
            return
        
        task_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        execute_action = QAction("Execute", menu)
        execute_action.triggered.connect(lambda: self.execute_task_requested.emit(task_id))
        menu.addAction(execute_action)
        
        unpin_action = QAction("Unpin", menu)
        unpin_action.triggered.connect(lambda: self.task_manager.toggle_pin(task_id))
        menu.addAction(unpin_action)
        
        favorite_action = QAction("Favorite", menu)
        favorite_action.triggered.connect(lambda: self.task_manager.toggle_favorite(task_id))
        menu.addAction(favorite_action)
        
        menu.exec(self._tab_bar.widget(2).mapToGlobal(pos))
    
    def _on_favorite_context_menu(self, pos):
        """Show context menu for favorite tab."""
        item = self._tab_bar.widget(3).itemAt(pos)
        if not item:
            return
        
        task_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        execute_action = QAction("Execute", menu)
        execute_action.triggered.connect(lambda: self.execute_task_requested.emit(task_id))
        menu.addAction(execute_action)
        
        unfavorite_action = QAction("Unfavorite", menu)
        unfavorite_action.triggered.connect(lambda: self.task_manager.toggle_favorite(task_id))
        menu.addAction(unfavorite_action)
        
        menu.exec(self._tab_bar.widget(3).mapToGlobal(pos))
    
    def _on_stop_all_running(self):
        """Stop all running tasks."""
        running_tasks = self.task_manager.get_running_tasks()
        for task in running_tasks:
            self.task_manager.cancel_task(task.id)
    
    def _on_clear_history(self):
        """Clear task history."""
        self.task_manager.clear_history()
        self._load_tasks()
    
    # Helper Methods
    
    def _rerun_from_history(self, task_id):
        """Rerun a task from history."""
        self.task_manager.rerun_task(task_id)
    
    def _open_terminal_at_task(self, task_id):
        """Open terminal at task's working directory."""
        record = next((r for r in self.task_manager.get_task_history() if r.task_id == task_id), None)
        if record:
            import os
            os.chdir(record.working_directory)
