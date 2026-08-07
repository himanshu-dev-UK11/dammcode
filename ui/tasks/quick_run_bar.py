"""
Quick Run Bar — Task System Quick Actions

A bar above the terminal with one-click task execution buttons.
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QFrame, QPushButton, 
                               QToolButton, QMenu, QAction, QSpacerItem, 
                               QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontFamily
from ui.tasks.task import TaskType
from core.logger import setup_logger
from core.event_bus import EventBus

logger = setup_logger(__name__)


class QuickRunBar(QWidget):
    """
    Quick action buttons above the terminal for common tasks.
    Automatically updates based on project type.
    """
    
    execute_task_requested = Signal(str)  # command
    execute_task_by_type = Signal(str)  # task_type
    
    def __init__(self, task_manager, terminal_panel, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.terminal_panel = terminal_panel
        self.ds = get_design_system()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup quick run bar UI."""
        p = self.ds.palette
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.SM)
        
        # Run button
        self._run_btn = self._create_task_button("Run", "▶", TaskType.RUN)
        layout.addWidget(self._run_btn)
        
        # Build button
        self._build_btn = self._create_task_button("Build", "🔨", TaskType.BUILD)
        layout.addWidget(self._build_btn)
        
        # Test button
        self._test_btn = self._create_task_button("Test", "🧪", TaskType.TEST)
        layout.addWidget(self._test_btn)
        
        # Format button
        self._format_btn = self._create_task_button("Format", "💄", TaskType.FORMAT)
        layout.addWidget(self._format_btn)
        
        # Lint button
        self._lint_btn = self._create_task_button("Lint", "⚠️", TaskType.LINT)
        layout.addWidget(self._lint_btn)
        
        # Clean button
        self._clean_btn = self._create_task_button("Clean", "🧹", TaskType.CLEAN)
        layout.addWidget(self._clean_btn)
        
        layout.addStretch()
    
    def _create_task_button(self, label: str, icon: str, task_type: TaskType) -> QToolButton:
        """Create a task button with context menu."""
        btn = QToolButton()
        btn.setText(f"{icon} {label}")
        btn.setPopupMode(QToolButton.InstantPopup)
        
        # Create menu
        menu = QMenu(btn)
        
        # Add "Run" action
        run_action = QAction(f"{icon} {label}", menu)
        run_action.triggered.connect(lambda: self.execute_task_by_type.emit(task_type.value))
        menu.addAction(run_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Configure" action
        configure_action = QAction("Configure Task...", menu)
        configure_action.triggered.connect(lambda: self._configure_task(task_type))
        menu.addAction(configure_action)
        
        btn.setMenu(menu)
        
        # Style the button
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {FontSize.SM}px;
                font-weight: 500;
            }}
            
            QToolButton:hover {{
                background-color: {p.surface_hover};
                border-color: {p.accent};
            }}
            
            QToolButton:pressed {{
                background-color: {p.accent};
                color: {p.text_on_accent};
                border-color: {p.accent};
            }}
            
            QToolButton::menu-indicator {{
                image: none;
            }}
        """)
        
        return btn
    
    def _configure_task(self, task_type: TaskType):
        """Open task configuration dialog."""
        # This would open a dialog to configure the task
        logger.info(f"Configure task: {task_type.value}")
    
    def update_project_tasks(self, project_type: str, tasks: list):
        """Update quick bar buttons based on project type."""
        # Update button text with project-specific commands
        for task in tasks:
            if task.task_type == TaskType.RUN:
                self._run_btn.setText(f"▶ {task.name}")
            elif task.task_type == TaskType.BUILD:
                self._build_btn.setText(f"🔨 {task.name}")
            elif task.task_type == TaskType.TEST:
                self._test_btn.setText(f"🧪 {task.name}")
            elif task.task_type == TaskType.FORMAT:
                self._format_btn.setText(f"💄 {task.name}")
            elif task.task_type == TaskType.LINT:
                self._lint_btn.setText(f"⚠️ {task.name}")
            elif task.task_type == TaskType.CLEAN:
                self._clean_btn.setText(f"🧹 {task.name}")
    
    def update_default_tasks(self):
        """Reset quick bar to default commands."""
        self._run_btn.setText("▶ Run")
        self._build_btn.setText("🔨 Build")
        self._test_btn.setText("🧪 Test")
        self._format_btn.setText("💄 Format")
        self._lint_btn.setText("⚠️ Lint")
        self._clean_btn.setText("🧹 Clean")
