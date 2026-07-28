"""
Terminal Toolbar — v1.9

Professional terminal toolbar with actions and controls.
"""
from PySide6.QtWidgets import (
    QToolBar, QPushButton, QComboBox, QLabel, QToolButton, QLineEdit, QMenu
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from ui.design_system import get_design_system, Spacing


class TerminalToolbar(QToolBar):
    """
    Professional toolbar for terminal panel.
    Provides all terminal management actions in a compact layout.
    """
    
    # Signals
    new_terminal_requested = Signal()
    split_horizontal_requested = Signal()
    split_vertical_requested = Signal()
    run_file_requested = Signal()
    run_project_requested = Signal()
    build_project_requested = Signal()
    kill_terminal_requested = Signal()
    restart_terminal_requested = Signal()
    clear_output_requested = Signal()
    search_requested = Signal()
    shell_changed = Signal(str)
    directory_changed = Signal(str)
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ds = get_design_system()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup toolbar layout."""
        self.setMovable(False)
        self.setFloatable(False)
        self.setObjectName("TerminalToolbar")
        from PySide6.QtCore import QSize
        self.setIconSize(QSize(14, 14))

        # Apply compact toolbar styling — no min-width forcing
        p = self.ds.palette
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {p.surface};
                border-bottom: 1px solid {p.border};
                padding: 4px 8px;
                spacing: 4px;
            }}
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-height: 24px;
            }}
            QToolButton:hover {{
                background-color: {p.hover};
                border-color: {p.border};
            }}
            QToolButton:pressed {{
                background-color: {p.surface_active};
            }}
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {p.hover};
                border-color: {p.border};
            }}
            QPushButton:pressed {{
                background-color: {p.surface_active};
            }}
        """)
        
        # New Terminal button
        self._btn_new = self._create_button("New Terminal")
        self._btn_new.clicked.connect(self.new_terminal_requested)
        self.addWidget(self._btn_new)
        
        # Split buttons
        split_btn = QToolButton()
        split_btn.setText("Split")
        split_menu = self._create_split_menu()
        split_btn.setMenu(split_menu)
        split_btn.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(split_btn)
        
        # Separator
        self.addSeparator()
        
        # Run and Build buttons
        self._btn_run_file = self._create_button("Run File")
        self._btn_run_file.clicked.connect(self.run_file_requested)
        self.addWidget(self._btn_run_file)
        
        self._btn_run_project = self._create_button("Run Project")
        self._btn_run_project.clicked.connect(self.run_project_requested)
        self.addWidget(self._btn_run_project)
        
        self._btn_build_project = self._create_button("Build")
        self._btn_build_project.clicked.connect(self.build_project_requested)
        self.addWidget(self._btn_build_project)
        
        # Process control buttons
        self._btn_kill = self._create_button("Kill")
        self._btn_kill.clicked.connect(self.kill_terminal_requested)
        self.addWidget(self._btn_kill)
        
        self._btn_restart = self._create_button("Restart")
        self._btn_restart.clicked.connect(self.restart_terminal_requested)
        self.addWidget(self._btn_restart)
        
        self._btn_clear = self._create_button("Clear")
        self._btn_clear.clicked.connect(self.clear_output_requested)
        self.addWidget(self._btn_clear)
        
        # Search button
        self._btn_search = self._create_button("Search")
        self._btn_search.clicked.connect(self.search_requested)
        self.addWidget(self._btn_search)
        
        # Separator
        self.addSeparator()
        
        # Shell selector — compact width
        self._combo_shell = QComboBox()
        self._combo_shell.setFixedWidth(96)
        self._combo_shell.currentTextChanged.connect(self.shell_changed.emit)
        self._combo_shell.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
            }}
            QComboBox:hover {{ border-color: {p.accent}; }}
            QComboBox::drop-down {{ border: none; padding-right: 2px; }}
            QComboBox QAbstractItemView {{
                background-color: {p.surface};
                color: {p.text};
                selection-background-color: {p.accent};
            }}
        """)
        self.addWidget(self._combo_shell)
        
        # Current directory — elide long paths rather than pushing buttons off-screen
        self._lbl_directory = QLabel()
        self._lbl_directory.setMaximumWidth(240)
        self._lbl_directory.setStyleSheet(f"""
            QLabel {{
                color: {p.text_tertiary};
                font-size: 11px;
                font-family: "JetBrains Mono", monospace;
                padding: 0 8px;
            }}
        """)
        self.addWidget(self._lbl_directory)
        
        # Zoom controls
        self._btn_zoom_out = self._create_button("-")
        self._btn_zoom_out.clicked.connect(self.zoom_out_requested)
        self.addWidget(self._btn_zoom_out)
        
        self._btn_zoom_reset = self._create_button("100%")
        self._btn_zoom_reset.clicked.connect(self.zoom_reset_requested)
        self.addWidget(self._btn_zoom_reset)
        
        self._btn_zoom_in = self._create_button("+")
        self._btn_zoom_in.clicked.connect(self.zoom_in_requested)
        self.addWidget(self._btn_zoom_in)
    
    def _create_button(self, text: str, icon: str = "") -> QPushButton:
        """Create a toolbar button."""
        label = f"{icon} {text}".strip() if icon else text
        btn = QPushButton(label)
        return btn
    
    def _create_split_menu(self) -> QMenu:
        """Create split menu with horizontal/vertical options."""
        menu = QMenu()
        # Add actions for horizontal/vertical split
        return menu
    
    def set_shells(self, shells: list):
        """Update available shells in the selector."""
        self._combo_shell.clear()
        for shell in shells:
            self._combo_shell.addItem(shell)
    
    def set_current_shell(self, shell: str):
        """Set current shell in selector."""
        index = self._combo_shell.findText(shell)
        if index >= 0:
            self._combo_shell.setCurrentIndex(index)
    
    def set_working_directory(self, directory: str):
        """Update current directory display — elide long paths."""
        from pathlib import Path
        try:
            # Show only the last 2 path components to keep it short
            parts = Path(directory).parts
            short = str(Path(*parts[-2:])) if len(parts) >= 2 else directory
        except Exception:
            short = directory
        self._lbl_directory.setText(short)
        self._lbl_directory.setToolTip(directory)  # full path on hover
    
    def set_zoom_level(self, level: int):
        """Update zoom level display."""
        self._btn_zoom_reset.setText(f"{level}%")