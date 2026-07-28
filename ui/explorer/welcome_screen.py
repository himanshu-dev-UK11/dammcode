"""
Explorer Welcome Screen — v1.0

Displays when no workspace is open, showing:
- Open Folder button
- Recent Projects list
- Pinned Projects list
- Recent Files list

VS Code style welcome experience.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ui.design_system import get_design_system, Spacing, FontSize, Radius
from pathlib import Path


class WelcomeScreen(QWidget):
    """Welcome screen shown in Explorer when no workspace is open."""
    
    open_folder_requested = Signal()
    recent_project_selected = Signal(str)  # path
    pinned_project_selected = Signal(str)  # path
    recent_file_selected = Signal(str)  # path
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.setup_ui()
        
    def setup_ui(self):
        p = get_design_system().palette
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.XL)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignTop)
        
        # Header
        header_label = QLabel("EXPLORER")
        header_label.setStyleSheet(f"""
            font-size: {FontSize.XS}px;
            font-weight: 600;
            color: {p.text_tertiary};
            letter-spacing: 0.05em;
            padding: {Spacing.SM}px 0px;
        """)
        layout.addWidget(header_label)
        
        # Open Folder button - prominent
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setFixedHeight(40)
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self.open_folder_requested.emit)
        self.open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.accent};
                color: {p.primary_text};
                border: none;
                border-radius: {Radius.MD}px;
                font-size: {FontSize.MD}px;
                font-weight: 600;
                padding: {Spacing.SM}px {Spacing.MD}px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {p.primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {p.primary_active};
            }}
        """)
        layout.addWidget(self.open_folder_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {p.border_subtle}; max-height: 1px;")
        layout.addWidget(separator)
        
        # Recent Projects section
        recent_label = QLabel("Recent Projects")
        recent_label.setStyleSheet(f"""
            font-size: {FontSize.SM}px;
            font-weight: 600;
            color: {p.text_secondary};
            padding: {Spacing.XS}px 0px;
        """)
        layout.addWidget(recent_label)
        
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(150)
        self.recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
                font-size: {FontSize.SM}px;
                color: {p.text};
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.SM}px;
                min-height: 28px;
            }}
            QListWidget::item:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
            QListWidget::item:selected {{
                background-color: {p.selection};
                color: {p.text};
            }}
        """)
        self.recent_list.itemClicked.connect(self._on_recent_clicked)
        layout.addWidget(self.recent_list)
        
        # No recent projects message
        self.no_recent_label = QLabel("No recent projects")
        self.no_recent_label.setStyleSheet(f"""
            font-size: {FontSize.SM}px;
            color: {p.text_tertiary};
            padding: {Spacing.MD}px 0px;
            font-style: italic;
        """)
        self.no_recent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_recent_label)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Apply background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p.sidebar};
            }}
        """)
        
        # Load recent projects
        self.load_recent_projects()
    
    def load_recent_projects(self):
        """Load recent projects from settings or event bus."""
        # TODO: Integrate with actual recent projects manager
        # For now, show empty state
        self.recent_list.hide()
        self.no_recent_label.show()
        
        # Example: If we had recent projects
        # recent_projects = self.get_recent_projects()
        # if recent_projects:
        #     self.recent_list.show()
        #     self.no_recent_label.hide()
        #     for project_path in recent_projects:
        #         self.add_recent_project(project_path)
        # else:
        #     self.recent_list.hide()
        #     self.no_recent_label.show()
    
    def add_recent_project(self, path: str):
        """Add a project to the recent list."""
        project_name = Path(path).name
        item = QListWidgetItem(project_name)
        item.setData(Qt.UserRole, path)
        self.recent_list.addItem(item)
        
        # Show list, hide empty message
        self.recent_list.show()
        self.no_recent_label.hide()
    
    def _on_recent_clicked(self, item: QListWidgetItem):
        """Handle clicking a recent project."""
        path = item.data(Qt.UserRole)
        if path:
            self.recent_project_selected.emit(path)
