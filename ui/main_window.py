"""
Main Window — v4.0 (Professional IDE Navigation)

Professional IDE layout with VS Code/Cursor-style navigation:
  QMenuBar
  QToolBar
  ────────────────────────────────────────────────────
  Activity Bar (46px, always visible)
  Sidebar (collapsible, animated, resizable)
  Editor (CenterPanel — expands when sidebar hidden)
  Right dock:   AI Workspace (340px default)
  Bottom dock:  Terminal / Problems / Output

Navigation behavior (VS Code style):
  - Activity bar always visible (46px)
  - Sidebar toggles with smooth 220ms animation
  - Clicking activity icon shows sidebar
  - Clicking same activity icon again hides sidebar
  - Editor automatically expands to fill freed space
  - Sidebar width remembered across sessions
  - Draggable resize handle on sidebar edge
  - Double-click handle to reset to default width

Keyboard shortcuts:
  Ctrl+B         - Toggle Sidebar
  Ctrl+`         - Toggle Terminal
  Ctrl+Backslash - Toggle AI Workspace
  Ctrl+Shift+P   - Command Palette
  Ctrl+Shift+E   - Focus Explorer
  Ctrl+Shift+F   - Focus Search
  Ctrl+Shift+G   - Focus Git
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMenu, QMessageBox, 
    QFileDialog, QApplication, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QStyle
)
from PySide6.QtCore import Qt, QSize, QSettings, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QKeySequence, QShortcut, QAction

from core.logger import setup_logger
from core.startup_profiler import get_startup_profiler, ProfilePhase
from ui.top_toolbar import TopToolbar
from ui.status_bar import BottomStatusBar
from ui.center_panel import CenterPanel
from ui.ai_workspace.ai_engineering_workspace_v3 import AIEngineeringWorkspaceV3
from ui.enhanced_explorer import PremiumActivityBar, PremiumSidebarHeader, PremiumExplorer
from ui.command_palette import CommandPalette
from ui.notifications import create_notification_manager
from ui.bottom_dock import DOCK_DEFAULT_HEIGHT
from ui.design_system import Sidebar

logger = setup_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, event_bus):
        with ProfilePhase("mainwindow_init"):
            super().__init__()
            self.event_bus = event_bus
            self._theme_manager = None  # set by main.py after app creation

            self.setWindowTitle("MyCodingMaster")
            self.setMinimumSize(1024, 680)
            self.setDockOptions(
                QMainWindow.AnimatedDocks |
                QMainWindow.AllowNestedDocks |
                QMainWindow.AllowTabbedDocks |
                QMainWindow.GroupedDragging
            )

            # Initialize components
            with ProfilePhase("command_palette_init"):
                self._command_palette = CommandPalette(event_bus)
            
            with ProfilePhase("notification_manager_init"):
                self._notification_manager = create_notification_manager(event_bus)
            
            # Load saved sidebar state
            with ProfilePhase("load_sidebar_settings"):
                self._settings = QSettings("MyCodingMaster", "MainWindow")
                self._sidebar_width = self._settings.value("sidebar/width", Sidebar.DEFAULT_WIDTH, type=int)
                self._sidebar_visible = self._settings.value("sidebar/visible", True, type=bool)
                self._active_activity = self._settings.value("sidebar/activity", "explorer", type=str)
            
            self.setup_menu_bar()
            self.setup_ui()
            self.setup_shortcuts()
            self.setup_connections()
            
            # Subscribe to events
            with ProfilePhase("subscribe_events"):
                self.event_bus.subscribe("workspace_loaded",          self._on_workspace_loaded)
                self.event_bus.subscribe("workspace_scanning",        self._on_workspace_scanning)
                self.event_bus.subscribe("workspace_metadata_updated",self._on_workspace_metadata)
                self.event_bus.subscribe("workspace_error",           self._on_workspace_error)
                self.event_bus.subscribe("notification_show",         self._on_notification_show)
                self.event_bus.subscribe("show_open_folder",          self._show_open_folder)
                # Dashboard lives in center panel — wire after setup_ui() creates center
                self.center.dashboard.open_recent_requested.connect(self.handle_open_project)

    def setup_menu_bar(self):
        with ProfilePhase("setup_menu_bar"):
            mb = self.menuBar()
            self.menu_bar = mb  # Store reference for hide/unhide

            # File menu - Complete file operations
            file_menu = mb.addMenu("&File")
            self._add_action(file_menu, "New File", "Ctrl+N", lambda: self.event_bus.publish("file_new_requested", {}))
            self._add_action(file_menu, "New Window", "Ctrl+Shift+N", lambda: None)
            file_menu.addSeparator()
            self._add_action(file_menu, "Open File…", "Ctrl+O", self._open_file_dialog)
            self._add_action(file_menu, "Open Folder…", "Ctrl+K, Ctrl+O", self.handle_open_project)
            self._add_action(file_menu, "Open Recent", "Ctrl+R", lambda: None)
            file_menu.addSeparator()
            self._add_action(file_menu, "Save", "Ctrl+S", self._save_current)
            self._add_action(file_menu, "Save As…", "Ctrl+Shift+S", lambda: None)
            self._add_action(file_menu, "Save All", "", lambda: self.event_bus.publish("file_save_all_requested", {}))
            file_menu.addSeparator()
            self._add_action(file_menu, "Close File", "Ctrl+W", lambda: self.event_bus.publish("file_close_requested", {}))
            self._add_action(file_menu, "Close Folder", "Ctrl+K, F", lambda: None)
            file_menu.addSeparator()
            self._add_action(file_menu, "Preferences", "Ctrl+,", self._focus_settings)
            file_menu.addSeparator()
            self._add_action(file_menu, "Exit", "Ctrl+Q", self.close)

            # Edit menu - Complete editing operations
            edit_menu = mb.addMenu("&Edit")
            self._add_action(edit_menu, "Undo", "Ctrl+Z", lambda: self._editor_action("undo"))
            self._add_action(edit_menu, "Redo", "Ctrl+Y", lambda: self._editor_action("redo"))
            edit_menu.addSeparator()
            self._add_action(edit_menu, "Cut", "Ctrl+X", lambda: self._editor_action("cut"))
            self._add_action(edit_menu, "Copy", "Ctrl+C", lambda: self._editor_action("copy"))
            self._add_action(edit_menu, "Paste", "Ctrl+V", lambda: self._editor_action("paste"))
            edit_menu.addSeparator()
            self._add_action(edit_menu, "Find", "Ctrl+F", self._show_find)
            self._add_action(edit_menu, "Replace", "Ctrl+H", self._show_find)
            self._add_action(edit_menu, "Find in Files", "Ctrl+Shift+F", self._focus_search)
            edit_menu.addSeparator()
            self._add_action(edit_menu, "Select All", "Ctrl+A", lambda: self._editor_action("selectAll"))

            # View menu - Complete view controls
            view_menu = mb.addMenu("&View")
            self._add_action(view_menu, "Command Palette", "Ctrl+Shift+P", self._show_command_palette)
            view_menu.addSeparator()
            self._add_action(view_menu, "Explorer", "Ctrl+Shift+E", self._focus_explorer)
            self._add_action(view_menu, "Search", "Ctrl+Shift+F", self._focus_search)
            self._add_action(view_menu, "Source Control", "Ctrl+Shift+G", self._focus_git)
            self._add_action(view_menu, "Debug", "Ctrl+Shift+D", self._focus_debug)
            self._add_action(view_menu, "Extensions", "Ctrl+Shift+X", lambda: None)
            view_menu.addSeparator()
            self._add_action(view_menu, "Terminal", "Ctrl+`", self._toggle_dock)
            self._add_action(view_menu, "Problems", "Ctrl+Shift+M", lambda: self._bottom_widget.show_tab("problems") if self._bottom_widget else None)
            self._add_action(view_menu, "Output", "Ctrl+Shift+U", lambda: self._bottom_widget.show_tab("output") if self._bottom_widget else None)
            view_menu.addSeparator()
            self._add_action(view_menu, "AI Workspace", "Ctrl+\\", self.toggle_ai_panel)
            view_menu.addSeparator()
            
            # Appearance submenu
            appearance_menu = view_menu.addMenu("Appearance")
            self._add_action(appearance_menu, "Full Screen", "F11", self._toggle_maximize)
            self._add_action(appearance_menu, "Zen Mode", "Ctrl+K, Z", lambda: None)
            appearance_menu.addSeparator()
            self._add_action(appearance_menu, "Show Menu Bar", "Alt+M", self.toggle_menu_bar)
            self._add_action(appearance_menu, "Show Toolbar", "Alt+T", self.toggle_top_toolbar)
            self._add_action(appearance_menu, "Show Sidebar", "Ctrl+B", self.toggle_explorer)
            appearance_menu.addSeparator()
            
            # Theme submenu under Appearance
            theme_menu = appearance_menu.addMenu("Color Theme")
            for label, tid in [("Dark", "dark"), ("Light", "light"), ("One Dark", "one_dark"),
                              ("GitHub Dark", "github_dark"), ("Nord", "nord")]:
                self._add_action(theme_menu, label, "", lambda checked=False, t=tid: self._apply_theme(t))
            
            view_menu.addSeparator()
            self._add_action(view_menu, "Zoom In", "Ctrl+=", lambda: None)
            self._add_action(view_menu, "Zoom Out", "Ctrl+-", lambda: None)
            self._add_action(view_menu, "Reset Zoom", "Ctrl+0", lambda: None)

            # Navigate menu - Code navigation
            navigate_menu = mb.addMenu("&Navigate")
            self._add_action(navigate_menu, "Go to File", "Ctrl+P", self._show_command_palette)
            self._add_action(navigate_menu, "Go to Symbol", "Ctrl+Shift+O", lambda: None)
            self._add_action(navigate_menu, "Go to Line", "Ctrl+G", lambda: None)
            navigate_menu.addSeparator()
            self._add_action(navigate_menu, "Go Back", "Alt+Left", lambda: None)
            self._add_action(navigate_menu, "Go Forward", "Alt+Right", lambda: None)
            navigate_menu.addSeparator()
            self._add_action(navigate_menu, "Next Problem", "F8", lambda: None)
            self._add_action(navigate_menu, "Previous Problem", "Shift+F8", lambda: None)

            # Run menu - Execution and debugging
            run_menu = mb.addMenu("&Run")
            self._add_action(run_menu, "Start Debugging", "F5", lambda: self.event_bus.publish("debug_requested", {}))
            self._add_action(run_menu, "Run Without Debugging", "Ctrl+F5", lambda: self.event_bus.publish("run_requested", {}))
            self._add_action(run_menu, "Stop", "Shift+F5", lambda: self.event_bus.publish("stop_requested", {}))
            self._add_action(run_menu, "Restart", "Ctrl+Shift+F5", lambda: None)
            run_menu.addSeparator()
            self._add_action(run_menu, "Open Configurations", "", lambda: None)
            run_menu.addSeparator()
            self._add_action(run_menu, "Scan Workspace", "", self._scan_workspace)

            # AI menu - AI operations
            ai_menu = mb.addMenu("&AI")
            self._add_action(ai_menu, "New Task…", "Ctrl+Enter", lambda: self.event_bus.publish("ai_new_task_requested", {}))
            self._add_action(ai_menu, "Cancel Task", "Esc", lambda: self.event_bus.publish("ai_cancel_requested", {}))
            ai_menu.addSeparator()
            self._add_action(ai_menu, "Show AI Workspace", "Ctrl+\\", self.toggle_ai_panel)
            self._add_action(ai_menu, "Select Model…", "", lambda: None)
            ai_menu.addSeparator()
            
            # AI Code Actions submenu
            code_actions_menu = ai_menu.addMenu("Code Actions")
            self._add_action(code_actions_menu, "Explain Code", "", lambda: self.event_bus.publish("ai_explain_code", {}))
            self._add_action(code_actions_menu, "Review Code", "", lambda: self.event_bus.publish("ai_review_code", {}))
            self._add_action(code_actions_menu, "Fix Issues", "", lambda: self.event_bus.publish("ai_fix_issues", {}))
            self._add_action(code_actions_menu, "Refactor", "", lambda: self.event_bus.publish("ai_refactor", {}))
            self._add_action(code_actions_menu, "Optimize", "", lambda: self.event_bus.publish("ai_optimize", {}))
            code_actions_menu.addSeparator()
            self._add_action(code_actions_menu, "Generate Tests", "", lambda: self.event_bus.publish("ai_generate_tests", {}))
            self._add_action(code_actions_menu, "Generate Docs", "", lambda: self.event_bus.publish("ai_generate_docs", {}))
            
            ai_menu.addSeparator()
            self._add_action(ai_menu, "View Memory", "", self._focus_memory)

            # Git menu - Version control
            git_menu = mb.addMenu("&Git")
            self._add_action(git_menu, "Open Source Control", "Ctrl+Shift+G", self._focus_git)
            git_menu.addSeparator()
            self._add_action(git_menu, "Clone Repository…", "", lambda: None)
            self._add_action(git_menu, "Initialize Repository", "", lambda: None)
            git_menu.addSeparator()
            self._add_action(git_menu, "Commit", "Ctrl+K, Ctrl+C", lambda: None)
            self._add_action(git_menu, "Push", "", lambda: None)
            self._add_action(git_menu, "Pull", "", lambda: None)
            self._add_action(git_menu, "Fetch", "", lambda: None)
            self._add_action(git_menu, "Sync", "", lambda: None)
            git_menu.addSeparator()
            self._add_action(git_menu, "Checkout to…", "", lambda: None)
            self._add_action(git_menu, "Create Branch…", "", lambda: None)
            self._add_action(git_menu, "View Branches", "", lambda: None)
            git_menu.addSeparator()
            self._add_action(git_menu, "View Changes", "", lambda: None)
            self._add_action(git_menu, "View History", "", lambda: None)

            # Tools menu - Additional utilities
            tools_menu = mb.addMenu("&Tools")
            self._add_action(tools_menu, "Python: Select Interpreter", "", lambda: None)
            self._add_action(tools_menu, "Node: Select Version", "", lambda: None)
            tools_menu.addSeparator()
            self._add_action(tools_menu, "Format Document", "Shift+Alt+F", lambda: None)
            self._add_action(tools_menu, "Organize Imports", "Shift+Alt+O", lambda: None)
            tools_menu.addSeparator()
            self._add_action(tools_menu, "Build…", "Ctrl+Shift+B", lambda: None)
            self._add_action(tools_menu, "Run Task…", "", lambda: None)

            # Window menu - Window management
            window_menu = mb.addMenu("&Window")
            self._add_action(window_menu, "New Window", "Ctrl+Shift+N", lambda: None)
            self._add_action(window_menu, "Close Window", "Ctrl+Shift+W", self.close)
            window_menu.addSeparator()
            self._add_action(window_menu, "Minimize", "Ctrl+M", self.showMinimized)
            self._add_action(window_menu, "Maximize", "", self._toggle_maximize)
            window_menu.addSeparator()
            self._add_action(window_menu, "Split Editor", "Ctrl+\\", lambda: None)
            window_menu.addSeparator()
            self._add_action(window_menu, "Reset Layout", "", self._reset_layout)

            # Help menu - Documentation and support
            help_menu = mb.addMenu("&Help")
            self._add_action(help_menu, "Welcome", "", lambda: None)
            self._add_action(help_menu, "Documentation", "F1", lambda: None)
            self._add_action(help_menu, "Keyboard Shortcuts", "Ctrl+K, Ctrl+S", lambda: None)
            help_menu.addSeparator()
            self._add_action(help_menu, "View Logs", "", lambda: None)
            self._add_action(help_menu, "Toggle Developer Tools", "Ctrl+Shift+I", lambda: None)
            help_menu.addSeparator()
            self._add_action(help_menu, "Check for Updates", "", lambda: None)
            self._add_action(help_menu, "Report Issue", "", lambda: None)
            help_menu.addSeparator()
            self._add_action(help_menu, "About MyCodingMaster", "", self._show_about)

    def _add_action(self, menu: QMenu, text: str, shortcut: str, slot) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def setup_ui(self):
        with ProfilePhase("setup_ui"):
            # Toolbar
            with ProfilePhase("toolbar_init"):
                self.toolbar = TopToolbar()
                self.addToolBar(Qt.TopToolBarArea, self.toolbar)
            
            with ProfilePhase("design_system_load"):
                from ui.design_system import get_design_system, Radius, ActivityBar, Sidebar
                from PySide6.QtCore import QPropertyAnimation, QEasingCurve
                ds = get_design_system()
            
            # Note: _sidebar_width and _sidebar_visible loaded from QSettings in __init__
            
            # --- MAIN WORKSPACE LAYOUT ---
            with ProfilePhase("main_layout_setup"):
                central_widget = QWidget()
                self._main_layout = QHBoxLayout(central_widget)
                self._main_layout.setContentsMargins(0, 0, 0, 0)
                self._main_layout.setSpacing(0)
            
            # --- ACTIVITY BAR (Always Visible) ---
            with ProfilePhase("activity_bar_init"):
                self._activity_bar = PremiumActivityBar()
                self._activity_bar.setFixedWidth(48)  # Updated to match new ActivityBar.WIDTH
                self._activity_bar.activity_selected.connect(self._on_activity_selected)
                self._activity_bar.activity_double_clicked.connect(self._on_activity_double_clicked)
                self._main_layout.addWidget(self._activity_bar)
            
            # --- SPLITTER HIERARCHY ---
            with ProfilePhase("splitter_init"):
                self._workspace_splitter = QSplitter(Qt.Vertical)
                self._workspace_splitter.setObjectName("MainWorkspaceSplitter")
                self._workspace_splitter.setChildrenCollapsible(False)  # Don't allow collapsing to 0
                self._workspace_splitter.setOpaqueResize(True)
                self._workspace_splitter.setHandleWidth(6)  # Make handle visible

                self._top_splitter = QSplitter(Qt.Horizontal)
                self._top_splitter.setObjectName("TopWorkspaceSplitter")
                self._top_splitter.setChildrenCollapsible(False)  # Don't allow collapsing to 0
                self._top_splitter.setOpaqueResize(True)
                self._top_splitter.setHandleWidth(6)

                self._workspace_splitter.addWidget(self._top_splitter)
                self._main_layout.addWidget(self._workspace_splitter, 1)

            # --- SIDEBAR (Collapsible with Resizable Handle) ---
            with ProfilePhase("explorer_init"):
                self._explorer = PremiumExplorer(self.event_bus)
                self._explorer.setMinimumWidth(Sidebar.MIN_WIDTH)  # Use MIN_WIDTH instead of fixed width
                self._explorer.setMaximumWidth(Sidebar.MAX_WIDTH)  # Allow flexible resizing
                
                # Connect signals
                self._explorer.new_folder_requested.connect(lambda: self.event_bus.publish("new_folder_requested", {}))
                self._explorer.more_actions_requested.connect(lambda: self.event_bus.publish("more_actions_requested", {}))
                
                self._top_splitter.addWidget(self._explorer)
                self._top_splitter.setStretchFactor(0, 0)  # Sidebar doesn't stretch
            
            # --- EDITOR (Expandable) ---
            with ProfilePhase("center_panel_init"):
                self.center = CenterPanel(self.event_bus)
                self._top_splitter.addWidget(self.center)
                self._top_splitter.setStretchFactor(1, 1)  # Editor stretches to fill space
            
            # --- AI PANEL ---
            with ProfilePhase("ai_panel_init"):
                self.ai_workspace = AIEngineeringWorkspaceV3(self.event_bus)
                self.ai_workspace.setMinimumWidth(280)
                self.ai_workspace.setMaximumWidth(520)
                self._top_splitter.addWidget(self.ai_workspace)

            # --- TERMINAL (Bottom in same splitter hierarchy) ---
            with ProfilePhase("bottom_panel_init"):
                from ui.bottom_dock import BottomDock
                self._bottom_widget = BottomDock(self.event_bus)
                self._workspace_splitter.addWidget(self._bottom_widget)
                self._workspace_splitter.setStretchFactor(0, 1)
                self._workspace_splitter.setStretchFactor(1, 0)

            # Set central widget
            with ProfilePhase("set_central_widget"):
                self.setCentralWidget(central_widget)

            with ProfilePhase("splitter_state_handlers"):
                self._workspace_splitter.splitterMoved.connect(lambda *_: self._save_layout())
                self._top_splitter.splitterMoved.connect(lambda *_: self._save_layout())
                # Update BottomDock's expanded height when user drags the splitter
                self._workspace_splitter.splitterMoved.connect(self._on_main_splitter_moved)

            # Status Bar
            with ProfilePhase("status_bar_init"):
                self.status_bar = BottomStatusBar(self.event_bus)
                self.setStatusBar(self.status_bar)
            
            # Wire bottom dock to main window for splitter interaction
            with ProfilePhase("wire_components"):
                self._bottom_widget.set_main_splitter(self._workspace_splitter)

                # Command Palette
                self._command_palette.setParent(self)
                self._command_palette.setWindowFlags(
                    Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Popup
                )
                self._command_palette.set_parent_window(self)
                self._command_palette.hide()

                # Notification Manager
                self._notification_manager.setParent(self)

            with ProfilePhase("load_layout"):
                self._load_layout()
            
            # Apply saved sidebar state
            with ProfilePhase("apply_sidebar_state"):
                if not self._sidebar_visible:
                    # Hide sidebar without animation on startup
                    self._explorer.setMinimumWidth(0)
                    self._explorer.setMaximumWidth(0)
                    self._explorer.setVisible(False)
                    self._top_splitter.setHandleWidth(0)
                    self._activity_bar.set_collapsed(True)
                    # Set splitter sizes to give all space to editor
                    total_width = self._top_splitter.width()
                    if total_width > 0:
                        self._top_splitter.setSizes([0, total_width])
                else:
                    # Show with saved activity and allow resizing
                    self._explorer.setMinimumWidth(Sidebar.MIN_WIDTH)
                    self._explorer.setMaximumWidth(Sidebar.MAX_WIDTH)
                    self._explorer.setVisible(True)
                    self._top_splitter.setHandleWidth(6)
                    self._activity_bar.set_active_activity(self._active_activity)
                    # Set proper splitter sizes
                    total_width = self._top_splitter.width()
                    if total_width > 0:
                        self._top_splitter.setSizes([self._sidebar_width, total_width - self._sidebar_width])

    def toggle_explorer(self):
        """Toggle sidebar visibility via Ctrl+B."""
        self._toggle_sidebar()
    
    def _toggle_sidebar(self):
        """Toggle sidebar with smooth animation using QSplitter.setSizes() - VS Code style."""
        if hasattr(self, "_sidebar_anim") and self._sidebar_anim:
            try:
                self._sidebar_anim.stop()
            finally:
                self._sidebar_anim = None
                try:
                    self._explorer.setUpdatesEnabled(True)
                except Exception:
                    pass

        if self._sidebar_visible:
            self._sidebar_visible = False
            if self._explorer.width() > 0:
                self._sidebar_width = self._explorer.width()
            self._activity_bar.set_collapsed(True)

            # Use simpler approach with immediate size change for now
            current_sizes = self._top_splitter.sizes()
            if len(current_sizes) >= 2:
                total_width = sum(current_sizes)
                self._top_splitter.setSizes([0, total_width])
            
            self._explorer.setMinimumWidth(0)
            self._explorer.setMaximumWidth(0)
            self._explorer.setVisible(False)
            self._top_splitter.setHandleWidth(0)
        else:
            self._sidebar_visible = True
            if self._sidebar_width < Sidebar.MIN_WIDTH:
                self._sidebar_width = Sidebar.DEFAULT_WIDTH

            self._activity_bar.set_collapsed(False)
            # Restore the active activity button state
            if self._active_activity:
                self._activity_bar.set_active_activity(self._active_activity)
            else:
                self._active_activity = "explorer"
                self._activity_bar.set_active_activity("explorer")

            self._explorer.setVisible(True)
            self._top_splitter.setHandleWidth(6)
            self._explorer.setMinimumWidth(Sidebar.MIN_WIDTH)
            self._explorer.setMaximumWidth(Sidebar.MAX_WIDTH)

            # Use immediate size change for reliability
            current_sizes = self._top_splitter.sizes()
            if len(current_sizes) >= 2:
                total_width = sum(current_sizes)
                self._top_splitter.setSizes([self._sidebar_width, total_width - self._sidebar_width])
    
    def _on_activity_selected(self, activity_id: str):
        """Handle activity selection from activity bar - VS Code style."""
        # Empty string means toggle (same activity clicked twice)
        if not activity_id:
            self._toggle_sidebar()
            return
        
        # Store active activity first
        self._active_activity = activity_id
        
        # If sidebar is hidden, show it first with the new activity
        if not self._sidebar_visible:
            self._toggle_sidebar()  # This will set _sidebar_visible to True internally
            # After showing sidebar, ensure the activity button is properly checked
            self._activity_bar.set_active_activity(activity_id)
        
        # Update sidebar content based on activity
        # For now, we only have Explorer implemented
        # Future: implement Search, Git, Debug, etc.
        activity_titles = {
            "explorer": "EXPLORER",
            "search": "SEARCH",
            "git": "SOURCE CONTROL",
            "debug": "DEBUG",
            "extensions": "EXTENSIONS",
            "memory": "AI MEMORY",
            "tasks": "TASKS",
            "settings": "SETTINGS"
        }
        
        title = activity_titles.get(activity_id, "EXPLORER")
        self._explorer.set_header_title(title)
        
        # Switch to the appropriate content panel
        self._explorer.switch_activity(activity_id)
    
    def _on_activity_double_clicked(self, activity_id: str):
        """
        Handle activity button double-click - collapse/restore sidebar.
        Double-clicking an activity button collapses the sidebar but keeps the activity selected,
        so single-clicking it again will restore the sidebar to that activity.
        """
        # Simply toggle the sidebar
        self._toggle_sidebar()

    def _on_main_splitter_moved(self):
        """Update bottom dock's expanded height when user drags the splitter."""
        if not self._bottom_widget._collapsed:
            self._bottom_widget._expanded_height = max(DOCK_DEFAULT_HEIGHT, self._bottom_widget.height())
    
    def toggle_ai_panel(self):
        """Toggle AI panel visibility."""
        is_visible = self.ai_workspace.isVisible()
        if is_visible:
            self._ai_panel_width = max(240, self.ai_workspace.width())
            self.ai_workspace.setVisible(False)
        else:
            self.ai_workspace.setVisible(True)
            sizes = self._top_splitter.sizes()
            ai_w = getattr(self, "_ai_panel_width", max(240, min(380, int(self.width() * 0.25))))
            if len(sizes) == 3:
                available = max(0, sum(sizes) - ai_w)
                sizes[1] = max(240, available - max(180, sizes[0]))
                sizes[2] = ai_w
                self._top_splitter.setSizes(sizes)
        logger.info(f"AI panel {'hidden' if is_visible else 'shown'}")

    def _toggle_dock(self):
        """Toggle bottom dock visibility."""
        if self._bottom_widget:
            self._bottom_widget.toggle_collapse()
            logger.info(f"Bottom dock {'collapsed' if self._bottom_widget._collapsed else 'expanded'}")
    
    def toggle_menu_bar(self):
        """Toggle menu bar visibility with Alt+M"""
        if hasattr(self, 'menu_bar'):
            is_visible = self.menu_bar.isVisible()
            self.menu_bar.setVisible(not is_visible)
            self.event_bus.publish("menu_bar_toggled", {
                "visible": not is_visible
            })
            logger.info(f"Menu bar {'hidden' if is_visible else 'shown'}")
    
    def toggle_top_toolbar(self):
        """Toggle top toolbar visibility with Alt+T"""
        if hasattr(self, 'toolbar'):
            is_visible = self.toolbar.isVisible()
            self.toolbar.setVisible(not is_visible)
            self.event_bus.publish("top_toolbar_toggled", {
                "visible": not is_visible
            })
            logger.info(f"Top toolbar {'hidden' if is_visible else 'shown'}")
            self.event_bus.publish("top_toolbar_toggled", {
                "visible": self.toolbar.isVisible()
            })

    def _focus_explorer(self):
        """Show and focus the explorer activity."""
        self._activity_bar.activate_activity("explorer")

    def _focus_search(self):
        """Show and focus the search activity."""
        self._activity_bar.activate_activity("search")

    def _focus_git(self):
        """Show and focus the git activity."""
        self._activity_bar.activate_activity("git")

    def _focus_debug(self):
        """Show and focus the debug activity."""
        self._activity_bar.activate_activity("debug")

    def _focus_memory(self):
        """Show and focus the memory activity."""
        self._activity_bar.activate_activity("memory")

    def _focus_tasks(self):
        """Show and focus the tasks activity."""
        self._activity_bar.activate_activity("tasks")

    def _focus_settings(self):
        """Show and focus the settings activity."""
        self._activity_bar.activate_activity("settings")

    def _focus_model(self):
        pass

    def _show_settings(self):
        pass

    def _show_command_palette(self):
        palette_width = 600
        palette_height = 400
        x = (self.width() - palette_width) // 2
        y = 100
        self._command_palette.setFixedSize(palette_width, palette_height)
        self._command_palette.move(
            self.mapToGlobal(self.rect().topLeft()).x() + x, 
            self.mapToGlobal(self.rect().topLeft()).y() + y
        )
        self._command_palette.show_palette()

    def _on_command_executed(self, command_id: str):
        self.event_bus.publish("command_executed", {"command": command_id})
        
        handlers = {
            "file.new": lambda: self.event_bus.publish("file_new_requested", {}),
            "file.open": lambda: self._open_file_dialog(),
            "file.open_folder": lambda: self.handle_open_project(),
            "file.save": lambda: self._save_current(),
            "file.save_all": lambda: self.event_bus.publish("file_save_all_requested", {}),
            "file.close": lambda: self.event_bus.publish("file_close_requested", {}),
            "ai.new_task": lambda: self.event_bus.publish("ai_new_task_requested", {}),
            "ai.cancel": lambda: self.event_bus.publish("ai_cancel_requested", {}),
            "ai.conversation": lambda: self.event_bus.publish("ai_conversation_requested", {}),
            "run.run": lambda: self.toolbar.run_requested.emit(),
            "run.stop": lambda: self.toolbar.stop_requested.emit(),
            "run.debug": lambda: self.event_bus.publish("debug_requested", {}),
            "settings.open": lambda: self._show_settings(),
            "settings.theme": lambda: self._toggle_theme(),
            "view.explorer": lambda: self._focus_explorer(),
            "view.search": lambda: self._focus_search(),
            "view.git": lambda: self._focus_git(),
            "view.debug": lambda: self._focus_debug(),
            "view.extensions": lambda: self._focus_memory(),
            "view.memory": lambda: self._focus_memory(),
            "view.tasks": lambda: self._focus_tasks(),
            "view.settings": lambda: self._focus_settings(),
            "view.terminal": lambda: self._toggle_dock(),
            "view.ai": lambda: self.toggle_ai_panel(),
            "view.fullscreen": lambda: self._toggle_maximize(),
            "workspace.scan": lambda: self._scan_workspace(),
            "search.find": lambda: self.event_bus.publish("find_requested", {}),
            "search.replace": lambda: self.event_bus.publish("replace_requested", {}),
        }
        
        handler = handlers.get(command_id)
        if handler:
            handler()

    def _open_file_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*);;Python Files (*.py);;Text Files (*.txt)"
        )
        if filepath:
            self.event_bus.publish("file_open_requested", {"path": filepath})

    def handle_open_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if dir_path:
            logger.info(f"Opening workspace: {dir_path}")
            self.event_bus.publish("request_open_workspace", {"path": dir_path})
            
    def _show_open_folder(self, event_data=None):
        """Show open folder dialog when event is received."""
        self.handle_open_project()

    def _save_current(self):
        self.event_bus.publish("request_save_current", {})

    def _show_find(self):
        """Show the find/replace bar in the active editor."""
        editor_tabs = self.center.editor_tabs
        if editor_tabs:
            editor_tabs._show_search()

    def _editor_action(self, action: str):
        """Delegate a standard edit action to the active editor."""
        editor = self.center.editor_tabs.get_current_editor()
        if not editor:
            return
        actions = {
            "undo":      editor.undo,
            "redo":      editor.redo,
            "cut":       editor.cut,
            "copy":      editor.copy,
            "paste":     editor.paste,
            "selectAll": editor.selectAll,
        }
        fn = actions.get(action)
        if fn:
            fn()

    def _scan_workspace(self):
        self.event_bus.publish("request_scan_workspace", {})

    def set_theme_manager(self, tm):
        self._theme_manager = tm

    def set_chat_engine(self, chat_engine):
        self.ai_workspace.set_chat_engine(chat_engine)
        
    def set_lsp_manager(self, lsp_manager):
        """Set the LSP Manager and pass to relevant components."""
        self._lsp_manager = lsp_manager
        self.center.set_lsp_manager(lsp_manager)
        self._bottom_widget.set_lsp_manager(lsp_manager)
        
    def set_project_analyzer(self, project_analyzer):
        """Set the Project Analyzer and pass to relevant components."""
        self._project_analyzer = project_analyzer
        self.ai_workspace.set_project_analyzer(project_analyzer)
        self.center.dashboard.set_project_analyzer(project_analyzer)

    def set_workspace_manager(self, workspace_manager):
        """Pass WorkspaceManager to Dashboard for async stat loading."""
        self.center.dashboard.set_workspace_manager(workspace_manager)

    def set_provider_manager(self, provider_manager):
        """Pass ProviderManager to Dashboard for AI Center data."""
        self.center.dashboard.set_provider_manager(provider_manager)

    def _toggle_theme(self):
        if self._theme_manager:
            self._theme_manager.toggle()

    def _apply_theme(self, theme_name: str):
        if self._theme_manager:
            self._theme_manager.apply_theme(theme_name)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _show_about(self):
        QMessageBox.about(
            self, "About MyCodingMaster",
            "<b>MyCodingMaster v1.9.0</b><br>"
            "AI-Assisted Software Engineering<br><br>"
            "Built with PySide6 · Python 3.x"
        )

    def _on_workspace_loaded(self, data):
        logger.info("=" * 80)
        logger.info("[MainWindow._on_workspace_loaded] RECEIVED EVENT!")
        logger.info(f"[MainWindow._on_workspace_loaded] Event data: {data}")
        from pathlib import Path
        try:
            path_str = data.get("path", "")
            logger.debug(f"[MainWindow._on_workspace_loaded] path_str = {path_str}")

            if path_str:
                logger.info(f"[MainWindow._on_workspace_loaded] Step 1: Setting window title...")
                project_name = Path(path_str).name
                self.setWindowTitle(f"MyCodingMaster — {project_name}")
                logger.debug(f"[MainWindow._on_workspace_loaded] Window title set to: {self.windowTitle()}")

                logger.info(f"[MainWindow._on_workspace_loaded] Step 2: Updating toolbar...")
                self.toolbar.update_workspace(path_str)
                logger.debug(f"[MainWindow._on_workspace_loaded] Toolbar updated!")

                logger.info(f"[MainWindow._on_workspace_loaded] Step 3: Ensuring sidebar is visible...")
                if not self._sidebar_visible:
                    self.toggle_explorer()
                logger.debug(f"[MainWindow._on_workspace_loaded] Sidebar visible!")

            logger.info("[MainWindow._on_workspace_loaded] COMPLETE!")
            logger.info("=" * 80)
        except Exception as exc:
            logger.exception("[MainWindow._on_workspace_loaded] FAILED with exception!")
            self.status_bar.showMessage(f"⚠ Error loading workspace: {exc}", 8000)

    def _on_workspace_scanning(self, data):
        name = data.get("name", "project")
        self.setWindowTitle(f"MyCodingMaster — Loading {name}…")
        self.status_bar.showMessage(f"Scanning {name}…", 0)

    def _on_workspace_metadata(self, data):
        logger.info("=" * 80)
        logger.info(f"[MainWindow._on_workspace_metadata] RECEIVED EVENT: {data}")
        try:
            name     = data.get("project_name", "")
            path     = data.get("path", "")
            language = data.get("primary_language", "Unknown")
            fw       = data.get("framework", "Unknown")
            files    = data.get("total_files", 0)
            folders  = data.get("total_folders", 0)
            ms       = data.get("scan_duration_ms", 0)
            logger.debug(f"[MainWindow._on_workspace_metadata] Extracted values: name={name}, path={path}, language={language}, fw={fw}, files={files}, folders={folders}, ms={ms}")

            if name:
                logger.info(f"[MainWindow._on_workspace_metadata] Setting window title: {name}")
                self.setWindowTitle(f"MyCodingMaster — {name}")
            if path:
                logger.debug(f"[MainWindow._on_workspace_metadata] Updating toolbar with path: {path}")
                self.toolbar.update_workspace(path)

            logger.debug(f"[MainWindow._on_workspace_metadata] Updating status bar...")
            self.status_bar.update_workspace_status(path, name, language, fw, files, folders)
            self.status_bar.showMessage(
                f"✓ {name}  |  {files} files  |  {language}  |  scanned in {ms:.0f}ms", 5000
            )
            logger.info("[MainWindow._on_workspace_metadata] COMPLETE!")
            logger.info("=" * 80)
        except Exception as exc:
            logger.exception("[MainWindow._on_workspace_metadata] FAILED!")

    def _on_workspace_error(self, data):
        error = data.get("error", "Unknown error")
        self.setWindowTitle("MyCodingMaster")
        self.status_bar.showMessage(f"⚠ {error}", 8000)
            
    def _on_notification_show(self, data: dict):
        title = data.get("title", "Notification")
        message = data.get("message", "")
        notification_type = data.get("type", "info")
        auto_hide = data.get("auto_hide", True)
        self._notification_manager.show_notification(title, message, notification_type, auto_hide)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep notification overlay pinned to bottom-right
        x = self.width() - self._notification_manager.width() - 20
        y = self.height() - self._notification_manager.height() - 60
        self._notification_manager.move(max(0, x), max(0, y))
    
    def closeEvent(self, event):
        """Save sidebar state and cleanup resources before closing."""
        # Save sidebar state
        self._settings.setValue("sidebar/width", self._sidebar_width)
        self._settings.setValue("sidebar/visible", self._sidebar_visible)
        self._settings.setValue("sidebar/activity", self._active_activity or "explorer")
        
        # Cleanup AI workspace resources
        if hasattr(self, 'ai_workspace') and self.ai_workspace:
            self.ai_workspace.cleanup()
        
        # Cleanup bottom dock terminals
        if hasattr(self, '_bottom_widget') and self._bottom_widget:
            self._bottom_widget.terminal_manager.close_all_terminals()
        
        # Accept close event
        self._save_layout()
        super().closeEvent(event)

    def showEvent(self, event):
        """Apply correct proportional sizes once the real window size is known."""
        super().showEvent(event)
        # Only do this on the first show
        if not getattr(self, '_initial_sizes_applied', False):
            self._initial_sizes_applied = True
            if not getattr(self, "_layout_restored", False):
                self._apply_default_layout_sizes()

    def _apply_default_layout_sizes(self):
        """Set sidebar/editor/AI proportions based on actual window width."""
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return
        
        explorer_w = self._sidebar_width if self._sidebar_visible else 0
        ai_w = max(240, min(380, int(w * 0.25)))
        editor_w = max(320, w - self._activity_bar.width() - explorer_w - ai_w)

        if hasattr(self, "_top_splitter"):
            self._top_splitter.setSizes([max(0, explorer_w), editor_w, ai_w])

        terminal_h = 180
        top_h = max(240, h - terminal_h)
        if hasattr(self, "_workspace_splitter"):
            self._workspace_splitter.setSizes([top_h, terminal_h])
        
    def _save_layout(self):
        settings = QSettings("MyCodingMaster", "MainWindow")
        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("layout/main_splitter", self._workspace_splitter.saveState())
        settings.setValue("layout/top_splitter", self._top_splitter.saveState())
        settings.setValue("layout/ai_visible", self.ai_workspace.isVisible())
        settings.setValue("layout/terminal_collapsed", self._bottom_widget._collapsed)
        
    def _load_layout(self):
        settings = QSettings("MyCodingMaster", "MainWindow")
        # Clear old window/state that may have QDockWidget info
        settings.remove("window/state")
        geometry = settings.value("window/geometry")
        main_splitter_state = settings.value("layout/main_splitter")
        top_splitter_state = settings.value("layout/top_splitter")
        ai_visible = settings.value("layout/ai_visible", True, type=bool)
        terminal_collapsed = settings.value("layout/terminal_collapsed", False, type=bool)
        if geometry:
            self.restoreGeometry(geometry)
        
        # Only restore splitter states if sidebar is visible
        if self._sidebar_visible and top_splitter_state:
            self._top_splitter.restoreState(top_splitter_state)
        elif not self._sidebar_visible:
            # Set splitter to give all space to editor if sidebar is hidden
            QTimer.singleShot(100, self._apply_hidden_sidebar_layout)
        if main_splitter_state:
            self._workspace_splitter.restoreState(main_splitter_state)
        
        self.ai_workspace.setVisible(ai_visible)
        if terminal_collapsed:
            self._bottom_widget.collapse()
        self._layout_restored = bool(top_splitter_state or main_splitter_state)
    
    def _apply_hidden_sidebar_layout(self):
        """Apply layout when sidebar is hidden."""
        if not self._sidebar_visible:
            total_width = self._top_splitter.width()
            if total_width > 0:
                self._top_splitter.setSizes([0, total_width])
            
    def _reset_layout(self):
        """Restore default panel proportions."""
        self.ai_workspace.setVisible(True)
        self._bottom_widget.expand()
        if not self._sidebar_visible:
            self.toggle_explorer()

        # Re-apply proportional sizes
        self._initial_sizes_applied = False
        self._layout_restored = False
        self._apply_default_layout_sizes()

    def setup_shortcuts(self):
        with ProfilePhase("setup_shortcuts"):
            # Sidebar toggle
            QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.toggle_explorer)
            
            # Menu bar and toolbar toggles (using Alt combinations to avoid conflicts)
            QShortcut(QKeySequence("Alt+M"), self).activated.connect(self.toggle_menu_bar)
            QShortcut(QKeySequence("Alt+T"), self).activated.connect(self.toggle_top_toolbar)
            
            # Activity bar keyboard shortcuts - simulate clicking activity buttons
            QShortcut(QKeySequence("Ctrl+Shift+E"), self).activated.connect(lambda: self._activity_bar.activate_activity("explorer"))
            QShortcut(QKeySequence("Ctrl+Shift+F"), self).activated.connect(lambda: self._activity_bar.activate_activity("search"))
            QShortcut(QKeySequence("Ctrl+Shift+G"), self).activated.connect(lambda: self._activity_bar.activate_activity("git"))
            QShortcut(QKeySequence("Ctrl+Shift+D"), self).activated.connect(lambda: self._activity_bar.activate_activity("debug"))
            QShortcut(QKeySequence("Ctrl+Shift+X"), self).activated.connect(lambda: self._activity_bar.activate_activity("extensions"))
            QShortcut(QKeySequence("Ctrl+Shift+M"), self).activated.connect(lambda: self._activity_bar.activate_activity("memory"))
            QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(lambda: self._activity_bar.activate_activity("tasks"))
            QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(lambda: self._activity_bar.activate_activity("settings"))
            
            # AI workspace toggle
            QShortcut(QKeySequence("Ctrl+\\"), self).activated.connect(self.toggle_ai_panel)
            
            # Command palette
            QShortcut(QKeySequence("Ctrl+Shift+P"), self).activated.connect(self._show_command_palette)
            
            self._command_palette.command_executed.connect(self._on_command_executed)

    def setup_connections(self):
        with ProfilePhase("setup_connections"):
            # Toolbar signals - core actions
            self.toolbar.open_project_requested.connect(self.handle_open_project)
            self.toolbar.save_requested.connect(lambda: self._save_current())
            self.toolbar.save_all_requested.connect(lambda: None)
            self.toolbar.search_requested.connect(self._focus_search)
        self.toolbar.command_palette_requested.connect(self._show_command_palette)
        self.toolbar.run_requested.connect(lambda: self.event_bus.publish("run_requested", {}))
        self.toolbar.stop_requested.connect(lambda: self.event_bus.publish("stop_requested", {}))
        self.toolbar.model_selector_requested.connect(self._focus_model)
        self.toolbar.theme_change_requested.connect(self._apply_theme)
        
        # Toolbar signals - window operations
        self.toolbar.window_action_requested.connect(self._on_window_action)
        
        # Toolbar signals - view operations
        self.toolbar.view_action_requested.connect(self._on_view_action)
        
        # Toolbar signals - AI operations
        self.toolbar.ai_action_requested.connect(self._on_ai_action)
        
        # Toolbar signals - Git operations
        self.toolbar.git_action_requested.connect(self._on_git_action)
    
    def _on_window_action(self, action: str):
        """Handle window menu actions."""
        handlers = {
            "minimize": self.showMinimized,
            "maximize": self._toggle_maximize,
            "about": self._show_about,
            "blueprint": lambda: None,
            "shortcuts": lambda: None,
            "check_updates": lambda: None,
            "docs": lambda: None,
            "report_issue": lambda: None,
            "new_window": lambda: None,
            "split_editor": lambda: None,
        }
        handler = handlers.get(action)
        if handler:
            handler()
    
    def _on_view_action(self, action: str):
        """Handle view menu actions."""
        handlers = {
            "toggle_explorer": self.toggle_explorer,
            "toggle_terminal": self._toggle_dock,
            "toggle_ai_workspace": self.toggle_ai_panel,
            "reset_layout": self._reset_layout,
            "new_file": lambda: None,
            "close_file": lambda: None,
            "settings": lambda: None,
            "run_with_args": lambda: None,
            "debug_file": lambda: None,
            "run_config": lambda: None,
            "find_in_files": self._focus_search,
            "replace_in_files": lambda: None,
            "extensions": lambda: None,
        }
        handler = handlers.get(action)
        if handler:
            handler()
    
    def _on_ai_action(self, action: str):
        """Handle AI menu actions."""
        handlers = {
            "new_task": lambda: None,
            "cancel_task": lambda: None,
            "show_workspace": self.toggle_ai_panel,
            "select_model": lambda: None,
            "view_memory": lambda: None,
            "explain_code": lambda: None,
            "review_code": lambda: None,
            "fix_issues": lambda: None,
            "refactor": lambda: None,
            "optimize": lambda: None,
            "generate_tests": lambda: None,
            "generate_docs": lambda: None,
            "generate_commit_msg": lambda: None,
            "summarize": lambda: None,
        }
        handler = handlers.get(action)
        if handler:
            handler()
    
    def _on_git_action(self, action: str):
        """Handle Git menu actions."""
        handlers = {
            "source_control": self._focus_git,
            "commit": lambda: None,
            "push": lambda: None,
            "pull": lambda: None,
            "branches": lambda: None,
            "history": lambda: None,
        }
        handler = handlers.get(action)
        if handler:
            handler()

    def _on_activity_double_clicked(self, activity_id: str):
        """
        Handle activity button double-click - collapse/restore sidebar.
        Double-clicking an activity button collapses the sidebar but keeps the activity selected,
        so single-clicking it again will restore the sidebar to that activity.
        """
        # Simply toggle the sidebar
        self._toggle_sidebar()
