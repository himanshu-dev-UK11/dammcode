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
    QToolBar, QToolButton, QWidget, QHBoxLayout, QLabel, QSizePolicy, QFrame, QMenu, QPushButton, QLineEdit
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
    f.setFixedHeight(16)
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
                padding: {Spacing.XS + 1}px {Spacing.MD}px;
                font-size: {FontSize.SM}px;
                font-weight: {FontWeight.MEDIUM};
                min-width: 32px;
                min-height: 28px;
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
                padding-right: 3px;
                image: none;
                width: 0;
                height: 0;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid {p.text_tertiary};
            }}
            QToolButton::menu-indicator:hover {{
                border-top-color: {p.text_secondary};
            }}
        """)


class ModelBadge(QWidget):
    """
    Elegant model indicator badge - matches reference design.
    Format: ● AI Model-Name
    """
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("ModelBadge")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Active AI model — click to configure")

        from ui.design_system import get_design_system, Radius, Spacing, FontSize, FontWeight
        p = get_design_system().palette

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)

        # Status indicator dot
        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {p.success}; font-size: 9px; background-color: transparent;")

        # Model name label - more prominent
        self._model_name = QLabel("No AI Model")
        self._model_name.setStyleSheet(f"""
            color: {p.text};
            font-size: {FontSize.SM}px;
            font-weight: {FontWeight.MEDIUM};
            background-color: transparent;
        """)

        layout.addWidget(self._dot)
        layout.addWidget(self._model_name)

        self.setStyleSheet(f"""
            #ModelBadge {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: 0px;
                min-height: 28px;
            }}
            #ModelBadge:hover {{
                border-color: {p.border_hover};
                background-color: {p.surface_hover};
            }}
        """)

    def set_model(self, name: str, active: bool = True):
        from ui.design_system import get_design_system
        p = get_design_system().palette
        # Format: show provider + model
        display_name = name if name else "No Model"
        self._model_name.setText(display_name)
        self._dot.setStyleSheet(
            f"color: {p.success if active else p.text_disabled}; font-size: 9px; background-color: transparent;"
        )

    def set_tokens(self, used: int, limit: int):
        # Remove token display from badge (too cluttered)
        pass

    def mousePressEvent(self, event):
        self.clicked.emit()


class WorkspaceStatus(QWidget):
    """Professional workspace badge with icon - matches reference design."""
    def __init__(self):
        super().__init__()
        from ui.design_system import get_design_system, Radius, Spacing, FontSize, FontWeight
        p = get_design_system().palette
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)
        
        # Folder icon
        self._icon = QLabel("📁")
        self._icon.setStyleSheet("font-size: 13px; background-color: transparent;")
        layout.addWidget(self._icon)
        
        # Workspace name
        self._label = QLabel("No Workspace")
        self._label.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: {FontSize.SM}px;
            font-weight: {FontWeight.MEDIUM};
            background-color: transparent;
        """)
        layout.addWidget(self._label)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                min-height: 28px;
            }}
            QWidget:hover {{
                border-color: {p.border_hover};
                background-color: {p.surface_hover};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Current workspace — click to open folder")
        self.setMaximumWidth(200)

    def set_workspace(self, name: str):
        from ui.design_system import get_design_system, FontSize, FontWeight
        p = get_design_system().palette
        
        # Truncate if too long
        display_name = name if len(name) <= 24 else name[:21] + "..."
        
        if name == "No Workspace":
            self._label.setText(name)
            self._label.setStyleSheet(f"""
                color: {p.text_tertiary};
                font-size: {FontSize.SM}px;
                font-weight: {FontWeight.MEDIUM};
                background-color: transparent;
            """)
        else:
            self._label.setText(display_name)
            self._label.setStyleSheet(f"""
                color: {p.text};
                font-size: {FontSize.SM}px;
                font-weight: {FontWeight.MEDIUM};
                background-color: transparent;
            """)
    
    def mousePressEvent(self, event):
        # Could emit signal to open folder dialog
        pass


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
        """Build professional toolbar matching IDE reference design."""
        from ui.design_system import get_design_system, Spacing, Radius, FontSize
        p = get_design_system().palette
        
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {p.bg_secondary};
                border: none;
                border-bottom: 1px solid {p.border_subtle};
                spacing: {Spacing.XS}px;
                padding: 0 {Spacing.MD}px;
                min-height: 40px;
                max-height: 40px;
            }}
            QToolButton {{
                min-width: 28px;
                min-height: 28px;
                padding: 3px 8px;
            }}
        """)
        
        # ── Window Controls Spacer (for traffic light buttons alignment) ──
        title_spacer = QWidget()
        title_spacer.setFixedWidth(72)
        title_spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(title_spacer)
        
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
        
        # ── Left spacer before search field ─────────────────────────────
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(left_spacer)
        
        # ── Centered Search in Project Field ────────────────────────────
        search_wrap = QWidget()
        search_wrap.setStyleSheet("background-color: transparent;")
        search_layout = QHBoxLayout(search_wrap)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_wrap.setFixedWidth(360)
        search_wrap.setMinimumWidth(240)
        search_wrap.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        search_icon = QLabel("🔍")
        search_icon.setAlignment(Qt.AlignCenter)
        search_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {p.surface};
                color: {p.text_tertiary};
                border: 1px solid {p.border};
                border-right: none;
                border-top-left-radius: {Radius.MD}px;
                border-bottom-left-radius: {Radius.MD}px;
                padding: 0 {Spacing.SM}px 0 {Spacing.MD}px;
                font-size: 12px;
            }}
        """)
        search_layout.addWidget(search_icon)
        
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search in project")
        self.search_field.returnPressed.connect(self.search_requested.emit)
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-left: none;
                border-right: none;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: {Spacing.XS + 2}px {Spacing.SM}px;
                font-size: {FontSize.SM}px;
                selection-background-color: {p.selection};
                min-height: 20px;
            }}
            QLineEdit:hover {{
                border-color: {p.border_hover};
            }}
            QLineEdit:focus {{
                border-color: {p.accent};
            }}
        """)
        search_layout.addWidget(self.search_field, 1)
        
        kbd_label = QLabel("⌘K")
        kbd_label.setAlignment(Qt.AlignCenter)
        kbd_label.setStyleSheet(f"""
            QLabel {{
                background-color: {p.surface};
                color: {p.text_tertiary};
                border: 1px solid {p.border};
                border-left: none;
                border-top-right-radius: {Radius.MD}px;
                border-bottom-right-radius: {Radius.MD}px;
                padding: 0 {Spacing.MD}px 0 {Spacing.XS}px;
                font-size: {FontSize.XXS}px;
                font-weight: 600;
            }}
        """)
        search_layout.addWidget(kbd_label)
        
        self.addWidget(search_wrap)
        
        # ── Right spacer after search ───────────────────────────────────
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(right_spacer)
        
        # ── Editor Actions (subtle toolbar) ─────────────────────────────
        self._add_editor_actions()
        self.addWidget(_create_separator())
        
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
    
    def _add_editor_actions(self):
        """Add editor layout/window actions matching reference design."""
        # Split Editor button
        btn_split = ToolButton("⊞")
        btn_split.setToolTip("Split Editor Right")
        btn_split.clicked.connect(lambda: self.view_action_requested.emit("split_editor"))
        self.addWidget(btn_split)
        
        # Editor Layout / View menu
        btn_layout = ToolButton("⋯")
        btn_layout.setToolTip("More Editor Actions")
        
        layout_menu = QMenu(btn_layout)
        layout_menu.addAction("Split Editor Right").triggered.connect(
            lambda: self.view_action_requested.emit("split_right")
        )
        layout_menu.addAction("Split Editor Down").triggered.connect(
            lambda: self.view_action_requested.emit("split_down")
        )
        layout_menu.addSeparator()
        layout_menu.addAction("Minimap").triggered.connect(
            lambda: self.view_action_requested.emit("toggle_minimap")
        )
        layout_menu.addAction("Breadcrumbs").triggered.connect(
            lambda: self.view_action_requested.emit("toggle_breadcrumbs")
        )
        layout_menu.addAction("Word Wrap").triggered.connect(
            lambda: self.view_action_requested.emit("toggle_wordwrap")
        )
        layout_menu.addSeparator()
        layout_menu.addAction("Command Palette… (Ctrl+Shift+P)").triggered.connect(
            self.command_palette_requested.emit
        )
        btn_layout.setMenu(layout_menu)
        btn_layout.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(btn_layout)
        
        # Settings button
        btn_settings = ToolButton("⚙")
        btn_settings.setToolTip("Settings and more")
        
        settings_menu = QMenu(btn_settings)
        settings_menu.addAction("Color Theme").triggered.connect(
            lambda: self.theme_change_requested.emit("menu")
        )
        settings_menu.addAction("Keyboard Shortcuts (Ctrl+K Ctrl+S)").triggered.connect(
            lambda: self.view_action_requested.emit("shortcuts")
        )
        settings_menu.addSeparator()
        settings_menu.addAction("Settings (Ctrl+,)").triggered.connect(
            lambda: self.view_action_requested.emit("settings")
        )
        btn_settings.setMenu(settings_menu)
        btn_settings.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(btn_settings)
    
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
