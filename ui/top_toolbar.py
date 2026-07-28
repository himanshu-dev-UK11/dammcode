"""
Top Toolbar — v2.0 (Professional Restore)

Professional IDE-style toolbar with frequently-used actions.
Comparable to VS Code, JetBrains, and Cursor.

Layout:
[File Actions] | [Edit Actions] | [Run/Debug] | [AI Actions] | [Spacer] [Model] [Workspace]

Features:
- Icon + text buttons for primary actions
- Separators between logical groups
- Model badge and workspace status on right
- Consistent spacing and professional styling
- No duplicate functionality with menus
"""

from PySide6.QtWidgets import (
    QToolBar, QToolButton, QWidget, QHBoxLayout, QLabel, QSizePolicy, QFrame, QMenu, QPushButton
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, Signal, QSize


def _create_separator() -> QFrame:
    """Vertical separator widget for toolbar groups."""
    from ui.design_system import get_design_system
    p = get_design_system().palette
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFixedWidth(1)
    f.setFixedHeight(18)
    f.setStyleSheet(f"color: {p.border_subtle}; background-color: {p.border_subtle}; margin: 0 4px;")
    return f


class ToolButton(QToolButton):
    """Custom tool button with consistent styling and animations."""
    
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setText(text)
        self._setup_styles()
    
    def _setup_styles(self):
        """Apply consistent button styling."""
        from ui.design_system import get_design_system, Radius, Spacing, FontSize, FontWeight
        p = get_design_system().palette
        
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {p.text_secondary};
                border: none;
                border-radius: {Radius.SM}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {FontSize.SM}px;
                font-weight: {FontWeight.MEDIUM};
                min-width: 26px;
                min-height: 26px;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
            QToolButton:pressed {{
                background-color: {p.surface_active};
            }}
            QToolButton:checked {{
                background-color: {p.surface_active};
                color: {p.text};
            }}
            QToolButton::menu-indicator {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                padding-right: 4px;
                image: none;
                width: 0;
                height: 0;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid {p.text_tertiary};
            }}
            QToolButton::menu-indicator:hover {{
                border-top-color: {p.text};
            }}
        """)


class ModelBadge(QWidget):
    """
    Compact model indicator shown in the toolbar right section.
    Shows: ● ModelName  [token budget]
    """
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("ModelBadge")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Active AI model — click to switch")

        from ui.design_system import get_design_system, Radius, Spacing, FontSize
        p = get_design_system().palette

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {p.success}; font-size: 8px; background-color: transparent;")

        self._model_name = QLabel("No Model")
        self._model_name.setStyleSheet(f"""
            color: {p.text_secondary};
            font-size: {FontSize.XS}px;
            font-weight: 500;
            background-color: transparent;
        """)

        self._token_lbl = QLabel("")
        self._token_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XS}px; background-color: transparent;")

        layout.addWidget(self._dot)
        layout.addWidget(self._model_name)
        layout.addWidget(self._token_lbl)

        self.setStyleSheet(f"""
            #ModelBadge {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: 0px;
            }}
            #ModelBadge:hover {{
                border-color: {p.border_hover};
                background-color: {p.surface_hover};
            }}
        """)

    def set_model(self, name: str, active: bool = True):
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self._model_name.setText(name)
        self._dot.setStyleSheet(
            f"color: {p.success if active else p.text_tertiary}; font-size: 8px; background-color: transparent;"
        )

    def set_tokens(self, used: int, limit: int):
        if limit > 0:
            pct = int(used / limit * 100)
            self._token_lbl.setText(f"{pct}%")

    def mousePressEvent(self, event):
        self.clicked.emit()


class WorkspaceStatus(QLabel):
    """Compact workspace path/name label in toolbar."""
    def __init__(self):
        super().__init__("No Workspace")
        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        self.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: {FontSize.XS}px;
            background-color: transparent;
            padding: 0 8px;
        """)
        self.setMaximumWidth(220)

    def set_workspace(self, name: str):
        from ui.design_system import get_design_system, FontSize
        p = get_design_system().palette
        self.setText(name)
        self.setStyleSheet(f"""
            color: {p.text_secondary};
            font-size: {FontSize.XS}px;
            background-color: transparent;
            padding: 0 8px;
        """)


class TopToolbar(QToolBar):
    """
    Professional IDE-style toolbar with frequently-used actions.
    
    Layout:
    [Open][New][Save] | [Find][Replace] | [Run][Stop][Debug] | [AI Task][AI Menu] | [Spacer] [Model][Workspace]
    
    Signals:
        open_project_requested()
        save_requested()
        save_all_requested()
        run_requested()
        stop_requested()
        search_requested()
        command_palette_requested()
        model_selector_requested()
        theme_change_requested(str)
        git_action_requested(str)
        ai_action_requested(str)
        view_action_requested(str)
        window_action_requested(str)
    """
    
    # Signals for all toolbar actions
    open_project_requested  = Signal()
    save_requested          = Signal()
    save_all_requested      = Signal()
    run_requested           = Signal()
    stop_requested          = Signal()
    search_requested        = Signal()
    command_palette_requested = Signal()
    model_selector_requested = Signal()
    theme_change_requested  = Signal(str)
    git_action_requested    = Signal(str)
    ai_action_requested     = Signal(str)
    view_action_requested   = Signal(str)
    window_action_requested = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.setFloatable(False)
        self.setObjectName("TopToolbar")
        self.setIconSize(QSize(16, 16))
        self.setup_ui()
    
    def setup_ui(self):
        """Build professional toolbar with frequently-used actions."""
        from ui.design_system import get_design_system, Spacing
        p = get_design_system().palette
        
        # Set consistent toolbar styling
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {p.toolbar};
                border: none;
                border-bottom: 1px solid {p.border};
                spacing: {Spacing.SM}px;
                padding: {Spacing.XS}px {Spacing.MD}px;
                min-height: 36px;
            }}
            QToolButton {{
                min-width: 32px;
                min-height: 30px;
                padding: 4px 10px;
            }}
        """)
        
        # ── File Actions ────────────────────────────────────────────────
        self._add_file_actions()
        self.addWidget(_create_separator())
        
        # ── Edit Actions ────────────────────────────────────────────────
        self._add_edit_actions()
        self.addWidget(_create_separator())
        
        # ── Run/Debug Actions ───────────────────────────────────────────
        self._add_run_actions()
        self.addWidget(_create_separator())
        
        # ── AI Actions ──────────────────────────────────────────────────
        self._add_ai_actions()
        
        # ── Spacer for right-aligned elements ───────────────────────────
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(spacer)
        
        # ── Right Section: Status Indicators ────────────────────────────
        self._add_status_section()
    
    def _add_file_actions(self):
        """Add file operation buttons."""
        # Open Folder
        btn_open = ToolButton("Open")
        btn_open.setToolTip("Open Folder (Ctrl+K, Ctrl+O)")
        btn_open.clicked.connect(self.open_project_requested.emit)
        self.addWidget(btn_open)
        
        # New File
        btn_new = ToolButton("New")
        btn_new.setToolTip("New File (Ctrl+N)")
        btn_new.clicked.connect(lambda: self.view_action_requested.emit("new_file"))
        self.addWidget(btn_new)
        
        # Save
        btn_save = ToolButton("Save")
        btn_save.setToolTip("Save (Ctrl+S)")
        btn_save.clicked.connect(self.save_requested.emit)
        self.addWidget(btn_save)
        
        # Save All
        btn_save_all = ToolButton("Save All")
        btn_save_all.setToolTip("Save All Files")
        btn_save_all.clicked.connect(self.save_all_requested.emit)
        self.addWidget(btn_save_all)
    
    def _add_edit_actions(self):
        """Add editing action buttons."""
        # Find
        btn_find = ToolButton("Find")
        btn_find.setToolTip("Find (Ctrl+F)")
        btn_find.clicked.connect(self.search_requested.emit)
        self.addWidget(btn_find)
        
        # Find in Files
        btn_find_files = ToolButton("Find in Files")
        btn_find_files.setToolTip("Find in Files (Ctrl+Shift+F)")
        btn_find_files.clicked.connect(lambda: self.view_action_requested.emit("find_in_files"))
        self.addWidget(btn_find_files)
    
    def _add_run_actions(self):
        """Add run/debug action buttons."""
        # Run
        btn_run = ToolButton("Run")
        btn_run.setToolTip("Run (F5)")
        btn_run.clicked.connect(self.run_requested.emit)
        self.addWidget(btn_run)
        
        # Stop
        btn_stop = ToolButton("Stop")
        btn_stop.setToolTip("Stop (Shift+F5)")
        btn_stop.clicked.connect(self.stop_requested.emit)
        self.addWidget(btn_stop)
        
        # Debug
        btn_debug = ToolButton("Debug")
        btn_debug.setToolTip("Start Debugging (Ctrl+F5)")
        btn_debug.clicked.connect(lambda: self.view_action_requested.emit("debug_file"))
        self.addWidget(btn_debug)
    
    def _add_ai_actions(self):
        """Add AI-related action buttons."""
        # New AI Task
        btn_ai_task = ToolButton("AI Task")
        btn_ai_task.setToolTip("New AI Task (Ctrl+Enter)")
        btn_ai_task.clicked.connect(lambda: self.ai_action_requested.emit("new_task"))
        self.addWidget(btn_ai_task)
        
        # AI Actions Menu
        btn_ai_menu = ToolButton("AI ▼")
        btn_ai_menu.setToolTip("AI Actions")
        
        menu = QMenu(btn_ai_menu)
        menu.addAction("Explain Code").triggered.connect(
            lambda: self.ai_action_requested.emit("explain_code")
        )
        menu.addAction("Review Code").triggered.connect(
            lambda: self.ai_action_requested.emit("review_code")
        )
        menu.addAction("Fix Issues").triggered.connect(
            lambda: self.ai_action_requested.emit("fix_issues")
        )
        menu.addAction("Refactor").triggered.connect(
            lambda: self.ai_action_requested.emit("refactor")
        )
        menu.addAction("Optimize").triggered.connect(
            lambda: self.ai_action_requested.emit("optimize")
        )
        menu.addSeparator()
        menu.addAction("Generate Tests").triggered.connect(
            lambda: self.ai_action_requested.emit("generate_tests")
        )
        menu.addAction("Generate Docs").triggered.connect(
            lambda: self.ai_action_requested.emit("generate_docs")
        )
        
        btn_ai_menu.setMenu(menu)
        btn_ai_menu.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(btn_ai_menu)
    
    def _add_status_section(self):
        """Add right-aligned status indicators."""
        # Model badge
        self.model_badge = ModelBadge()
        self.model_badge.clicked.connect(self.model_selector_requested.emit)
        self.addWidget(self.model_badge)
        
        # Workspace status
        self.workspace_status = WorkspaceStatus()
        self.addWidget(self.workspace_status)
    
    def update_model(self, name: str, active: bool = True):
        """Update the model badge display."""
        self.model_badge.set_model(name, active)
    
    def update_workspace(self, path: str):
        """Show just the folder name for brevity."""
        from pathlib import Path
        try:
            name = Path(path).name or path
        except Exception:
            name = path
        self.workspace_status.set_workspace(name)
    
    def set_running(self, running: bool):
        """Update UI state when running/stopped."""
        # Update Run and Stop menu actions state
        pass  # Menus don't easily support enabling/disabling, could add indicators if needed
