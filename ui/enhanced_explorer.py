"""
Enhanced Explorer Panel — v3.2 (Professional IDE-style)

Redesigned Explorer with:
- Premium activity bar (46px width)
- Compact sidebar (220px default)
- Modern tree view
- Smooth animations
- Professional context menu
- Workspace sections
- Performance optimizations
- Resizable sidebar with drag handle
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QLineEdit, QToolButton, QSplitter, QFrame, QPushButton,
    QTreeView, QFileSystemModel, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QDir, QMimeData, QPropertyAnimation, QPoint, QEvent
from PySide6.QtGui import QAction, QCursor, QMouseEvent
from pathlib import Path
from ui.design_system import get_design_system, ActivityBar, Sidebar, Spacing, Radius, Easing, FontSize
from ui.explorer.context_menu import ContextMenuManager
from core.file_operations import FileOperations
from ui.explorer.copy_path import CopyPathManager


class ActivityButton(QPushButton):
    """
    Custom button for activity bar that handles both single and double clicks.
    Single click: toggle activity
    Double click: collapse/restore sidebar
    """
    double_clicked = Signal(str)  # activity_id
    
    def __init__(self, icon: str, activity_id: str, tooltip: str, shortcut: str, parent=None):
        super().__init__(icon, parent)
        self._activity_id = activity_id
        self.setFixedSize(32, 32)
        self.setToolTip(f"{tooltip} ({shortcut})")
        self.setCheckable(True)
        self.setObjectName(f"ActivityBtn_{activity_id}")
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to collapse/restore sidebar."""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self._activity_id)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class ResizeHandle(QWidget):
    """Draggable resize handle for sidebar."""
    
    resize_started = Signal()
    resize_moved = Signal(int)  # delta x
    resize_finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(3)
        self.setCursor(QCursor(Qt.SplitHCursor))
        self._dragging = False
        self._drag_start_pos = QPoint()
        
        p = get_design_system().palette
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
            QWidget:hover {{
                background-color: {p.accent};
            }}
        """)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPos()
            self.resize_started.emit()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.globalPos().x() - self._drag_start_pos.x()
            self._drag_start_pos = event.globalPos()
            self.resize_moved.emit(delta)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self.resize_finished.emit()
            event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click resets to default width."""
        if event.button() == Qt.LeftButton:
            self.resize_moved.emit(-(self.parent().width() - Sidebar.DEFAULT_WIDTH))
            event.accept()


class PremiumActivityBar(QWidget):
    """Premium 48px activity bar with IDE-style buttons."""
    
    activity_selected = Signal(str)
    activity_double_clicked = Signal(str)  # New signal for double-click
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(48)  # Updated to match new ActivityBar.WIDTH
        self._collapsed = False
        self._active_activity = None  # Track active activity
        self._last_clicked_activity = None  # Track last clicked for toggle detection
        self.setup_ui()
        
    def setup_ui(self):
        p = get_design_system().palette
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Activity buttons configuration - premium IDE style with proper icons
        activities = [
            ("📁", "explorer", "Explorer", "Ctrl+Shift+E"),
            ("🔍", "search", "Search", "Ctrl+Shift+F"),
            ("🔀", "git", "Source Control", "Ctrl+Shift+G"),
            ("▶", "debug", "Debug & Run", "Ctrl+Shift+D"),
            ("🧩", "extensions", "Extensions", "Ctrl+Shift+X"),
            ("🧠", "memory", "AI Memory", "Ctrl+Shift+M"),
            ("📋", "tasks", "Tasks", "Ctrl+Shift+T"),
            ("⚙", "settings", "Settings", "Ctrl+,"),
        ]
        
        self._buttons = {}
        
        for icon, activity_id, tooltip, shortcut in activities:
            # Use custom ActivityButton that supports double-click
            btn = ActivityButton(icon, activity_id, tooltip, shortcut)
            btn.clicked.connect(lambda checked, aid=activity_id: self._on_button_clicked(aid))
            btn.double_clicked.connect(self._on_button_double_clicked)
            self._buttons[activity_id] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Apply premium styling with smooth animations
        self.setObjectName("PremiumActivityBar")
        self.setStyleSheet(f"""
            QWidget#PremiumActivityBar {{
                background-color: {p.bg_secondary};
                border-right: 1px solid {p.border_subtle};
            }}
            
            QPushButton#ActivityBtn_explorer,
            QPushButton#ActivityBtn_search,
            QPushButton#ActivityBtn_git,
            QPushButton#ActivityBtn_debug,
            QPushButton#ActivityBtn_extensions,
            QPushButton#ActivityBtn_memory,
            QPushButton#ActivityBtn_tasks,
            QPushButton#ActivityBtn_settings {{
                background-color: transparent;
                color: {p.text_tertiary};
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 0px;
                min-width: 36px;
                max-width: 36px;
                min-height: 36px;
                max-height: 36px;
                margin: 0;
            }}
            
            QPushButton#ActivityBtn_explorer:hover,
            QPushButton#ActivityBtn_search:hover,
            QPushButton#ActivityBtn_git:hover,
            QPushButton#ActivityBtn_debug:hover,
            QPushButton#ActivityBtn_extensions:hover,
            QPushButton#ActivityBtn_memory:hover,
            QPushButton#ActivityBtn_tasks:hover,
            QPushButton#ActivityBtn_settings:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
            
            QPushButton#ActivityBtn_explorer:checked,
            QPushButton#ActivityBtn_search:checked,
            QPushButton#ActivityBtn_git:checked,
            QPushButton#ActivityBtn_debug:checked,
            QPushButton#ActivityBtn_extensions:checked,
            QPushButton#ActivityBtn_memory:checked,
            QPushButton#ActivityBtn_tasks:checked,
            QPushButton#ActivityBtn_settings:checked {{
                background-color: {p.surface_active};
                color: {p.text};
                border-radius: 6px;
                border-left: 2px solid {p.accent};
            }}
        """)
        
    def _on_button_clicked(self, activity_id: str):
        """Handle button click - VS Code style toggle behavior."""
        # Check if clicking the same activity that's already active
        if activity_id == self._active_activity:
            # Toggle off - hide sidebar and deselect button
            self._buttons[activity_id].setChecked(False)
            self._active_activity = None
            # Signal parent to toggle sidebar (hide it)
            self.activity_selected.emit("")  # Empty string signals toggle
        else:
            # Switch to different activity - show sidebar if hidden, switch content
            # Deselect all other buttons
            for aid, btn in self._buttons.items():
                if aid != activity_id:
                    btn.setChecked(False)
            
            # Select clicked button
            self._buttons[activity_id].setChecked(True)
            self._active_activity = activity_id
            
            # Signal parent to show this activity (will auto-show sidebar if hidden)
            self.activity_selected.emit(activity_id)
    
    def _on_button_double_clicked(self, activity_id: str):
        """
        Handle button double-click - collapse/restore sidebar.
        VS Code behavior: double-click collapses sidebar while keeping activity selected.
        """
        self.activity_double_clicked.emit(activity_id)
    
    def activate_activity(self, activity_id: str):
        """
        Activate an activity programmatically (e.g., from keyboard shortcut).
        This simulates clicking the button with VS Code toggle behavior.
        """
        if activity_id not in self._buttons:
            return
        
        # Check if this activity is already active
        if activity_id == self._active_activity:
            # Toggle off - hide sidebar and deselect button
            self._buttons[activity_id].setChecked(False)
            self._active_activity = None
            self.activity_selected.emit("")  # Empty string signals toggle
        else:
            # Switch to different activity - show sidebar if hidden, switch content
            # Deselect all other buttons
            for aid, btn in self._buttons.items():
                if aid != activity_id:
                    btn.setChecked(False)
            
            # Select target button
            self._buttons[activity_id].setChecked(True)
            self._active_activity = activity_id
            
            # Signal parent to show this activity (will auto-show sidebar if hidden)
            self.activity_selected.emit(activity_id)
    
    def set_active_activity(self, activity_id: str):
        """Programmatically set active activity."""
        self._active_activity = activity_id
        
        # Deselect all
        for btn in self._buttons.values():
            btn.setChecked(False)
        
        # Select requested activity
        if activity_id and activity_id in self._buttons:
            self._buttons[activity_id].setChecked(True)
    
    def set_collapsed(self, collapsed: bool):
        """Update collapse state - deselect all buttons when collapsed."""
        self._collapsed = collapsed
        if collapsed:
            self._active_activity = None
            for btn in self._buttons.values():
                btn.setChecked(False)


class PremiumSidebarHeader(QWidget):
    """Premium sidebar header with professional IDE layout."""
    
    new_file_requested = Signal()
    new_folder_requested = Signal()
    more_actions_requested = Signal()
    
    def __init__(self, title: str = "EXPLORER", parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)  # Updated to match new Sidebar.HEADER_HEIGHT
        self._title = title
        self.setup_ui(title)
        
    def setup_ui(self, title: str):
        p = get_design_system().palette
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)
        
        # Folder icon
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 13px; color: {};".format(p.text_secondary))
        layout.addWidget(icon_label)
        
        # Title label - compact, professional
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 11px;
            color: {p.text_secondary};
            letter-spacing: 0.05em;
            background-color: transparent;
        """)
        layout.addWidget(self._title_label)
        
        layout.addStretch()
        
        # New Folder button - modern icon button
        self.new_folder_btn = QToolButton()
        self.new_folder_btn.setText("+")
        self.new_folder_btn.setFixedSize(26, 26)
        self.new_folder_btn.setToolTip("New Folder")
        self.new_folder_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: {Radius.SM}px;
                color: {p.text_tertiary};
                font-size: 16px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
        """)
        layout.addWidget(self.new_folder_btn)
        
        # More actions button - compact dots
        self.more_btn = QToolButton()
        self.more_btn.setText("⋯")
        self.more_btn.setFixedSize(26, 26)
        self.more_btn.setToolTip("More Actions")
        self.more_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: {Radius.SM}px;
                color: {p.text_tertiary};
                font-size: 16px;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
            }}
        """)
        layout.addWidget(self.more_btn)
        
        # Bottom border - 1px subtle separator
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p.bg_secondary};
                border-bottom: 1px solid {p.border_subtle};
            }}
        """)
        
    def update_title(self, title: str):
        """Update header title."""
        self._title = title
        self._title_label.setText(title)


class PremiumFileTree(QTreeView):
    """Premium file tree with professional styling and performance."""
    
    file_opened = Signal(str)
    file_selected = Signal(str)
    directory_selected = Signal(str)
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.file_ops = FileOperations(event_bus, parent=self)
        self.copy_path_manager = CopyPathManager(event_bus)
        
        # Initialize model
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(
            QDir.Filter.AllDirs |
            QDir.Filter.Files |
            QDir.Filter.NoDotAndDotDot
        )
        self.model.setNameFilterDisables(False)
        
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.setIndentation(16)  # Professional indentation
        self.setAnimated(False)
        self.setUniformRowHeights(True)
        
        self._setup_styling()
        self._setup_connections()
        self._setup_context_menu()
        
    def _setup_styling(self):
        p = get_design_system().palette
        
        self.setStyleSheet(f"""
            QTreeView {{
                background-color: transparent;
                border: none;
                font-size: {FontSize.SM}px;
                outline: none;
                selection-background-color: {p.selection};
                selection-color: {p.text};
            }}
            
            QTreeView::item {{
                padding: 4px {Spacing.SM}px;
                min-height: 24px;
                border-radius: {Radius.SM}px;
                margin: 1px 8px;
            }}
            
            QTreeView::item:hover {{
                background-color: {p.surface_hover};
            }}
            
            QTreeView::item:selected {{
                background-color: {p.surface_active};
                color: {p.text};
            }}
            
            QTreeView::item:selected:!active {{
                background-color: {p.selection_inactive};
            }}
            
            QTreeView::branch {{
                background-color: transparent;
            }}
            
            QTreeView::branch:has-siblings:adjoining-sibling {{
                border-image: none;
            }}
            
            QTreeView::branch:has-siblings:!adjoining-sibling {{
                border-image: none;
            }}
            
            QTreeView::branch:closed:has-children:has-siblings {{
                border-image: none;
            }}
            
            QTreeView::branch:open:has-children:has-siblings {{
                border-image: none;
            }}
            
            /* Modern scrollbar */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {p.border};
                border-radius: 4px;
                min-height: 28px;
                margin: 2px 1px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {p.border_hover};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {p.border};
                border-radius: 4px;
                min-width: 28px;
                margin: 1px 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {p.border_hover};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)
        
        # Hide all columns except name
        for i in range(1, self.model.columnCount()):
            self.hideColumn(i)
            
    def _setup_connections(self):
        """Setup signal connections."""
        self.doubleClicked.connect(self._on_double_clicked)
        self.clicked.connect(self._on_clicked)
        
        # Custom context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _setup_context_menu(self):
        """Setup context menu."""
        self._context_menu = QMenu(self)
        
        # File operations
        self._action_open = QAction("📂 Open", self)
        self._action_open.triggered.connect(self._on_open_file)
        self._context_menu.addAction(self._action_open)
        
        self._action_open_with = QAction("📂 Open With...", self)
        self._action_open_with.triggered.connect(self._on_open_with)
        self._context_menu.addAction(self._action_open_with)
        
        self._context_menu.addSeparator()
        
        # File operations
        self._action_rename = QAction("✏️ Rename", self)
        self._action_rename.triggered.connect(self._on_rename)
        self._context_menu.addAction(self._action_rename)
        
        self._action_duplicate = QAction("📋 Duplicate", self)
        self._action_duplicate.triggered.connect(self._on_duplicate)
        self._context_menu.addAction(self._action_duplicate)
        
        self._context_menu.addSeparator()
        
        self._action_delete = QAction("🗑️ Delete", self)
        self._action_delete.triggered.connect(self._on_delete)
        self._context_menu.addAction(self._action_delete)
        
        self._context_menu.addSeparator()
        
        # Copy path
        copy_menu = self._context_menu.addMenu("📋 Copy Path")
        self.copy_path_manager.create_copy_menu(None, copy_menu)
        
        self._context_menu.addSeparator()
        
        # Reveal
        self._action_reveal = QAction("📂 Reveal in Explorer", self)
        self._action_reveal.triggered.connect(self._on_reveal)
        self._context_menu.addAction(self._action_reveal)
        
        self._context_menu.addSeparator()
        
        # New file/folder
        self._action_new_file = QAction("📄 New File", self)
        self._action_new_file.triggered.connect(self._on_new_file)
        self._context_menu.addAction(self._action_new_file)
        
        self._action_new_folder = QAction("📁 New Folder", self)
        self._action_new_folder.triggered.connect(self._on_new_folder)
        self._context_menu.addAction(self._action_new_folder)
        
        self._context_menu.addSeparator()
        
        self._action_properties = QAction("📋 Properties", self)
        self._action_properties.triggered.connect(self._on_properties)
        self._context_menu.addAction(self._action_properties)
        
    def set_root_path(self, path: str):
        """Set the root path of the tree."""
        self.root_path = path
        index = self.model.setRootPath(path)
        self.setRootIndex(index)
        
    def _get_current_path(self) -> str:
        """Get currently selected path."""
        index = self.currentIndex()
        if index.isValid():
            return self.model.filePath(index)
        return self.root_path or ""
        
    def _on_double_clicked(self, index):
        """Handle double-click."""
        path = self.model.filePath(index)
        if Path(path).exists():
            if Path(path).is_file():
                self.file_opened.emit(path)
            else:
                self.directory_selected.emit(path)
                
    def _on_clicked(self, index):
        """Handle single-click."""
        path = self.model.filePath(index)
        if Path(path).is_file():
            self.file_selected.emit(path)
            
    def _show_context_menu(self, pos):
        """Show context menu."""
        path = self._get_current_path()
        
        # Update menu actions based on path
        is_dir = Path(path).is_dir() if Path(path).exists() else True
        is_file = Path(path).is_file() if Path(path).exists() else False
        
        # Show menu
        self._context_menu.exec_(self.viewport().mapToGlobal(pos))
        
    def _on_open_file(self):
        """Open selected file."""
        path = self._get_current_path()
        if Path(path).exists() and Path(path).is_file():
            self.file_opened.emit(path)
            
    def _on_open_with(self):
        """Open file with specific application."""
        path = self._get_current_path()
        if Path(path).exists() and Path(path).is_file():
            self.event_bus.publish("file_open_with_requested", {"path": path})
            
    def _on_rename(self):
        """Rename file/folder."""
        path = self._get_current_path()
        if Path(path).exists():
            self.file_ops.rename(path)
            
    def _on_duplicate(self):
        """Duplicate file/folder."""
        path = self._get_current_path()
        if Path(path).exists():
            self.file_ops.duplicate(path)
            
    def _on_delete(self):
        """Delete file/folder."""
        path = self._get_current_path()
        if Path(path).exists():
            self.file_ops.delete(path)
            
    def _on_reveal(self):
        """Reveal in explorer."""
        path = self._get_current_path()
        if Path(path).exists():
            self.file_ops.reveal_in_explorer(path)
            
    def _on_new_file(self):
        """Create new file."""
        path = self._get_current_path()
        if Path(path).exists() and Path(path).is_dir():
            self.file_ops.create_file(Path(path))
            
    def _on_new_folder(self):
        """Create new folder."""
        path = self._get_current_path()
        if Path(path).exists() and Path(path).is_dir():
            self.file_ops.create_folder(Path(path))
            
    def _on_properties(self):
        """Show properties."""
        path = self._get_current_path()
        if Path(path).exists():
            self.event_bus.publish("properties_shown", {"path": path})


class PremiumExplorer(QWidget):
    """Main premium explorer panel with IDE-style design."""
    
    new_folder_requested = Signal()
    more_actions_requested = Signal()
    
    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self._current_width = Sidebar.DEFAULT_WIDTH
        self._is_resizing = False
        self._has_workspace = False
        self.setup_ui()
        
        # Subscribe to workspace events
        self.event_bus.subscribe("workspace_loaded", self._on_workspace_loaded)
        self.event_bus.subscribe("workspace_closed", self._on_workspace_closed)
        
    def setup_ui(self):
        p = get_design_system().palette
        
        self.setObjectName("PremiumExplorer")
        # Note: Width is managed by parent (MainWindow), not by this widget
        # setMinimumWidth and setMaximumWidth are set by parent during initialization
        
        # Main horizontal layout: content + resize handle
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content container (header + stacked content)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        self.header = PremiumSidebarHeader("EXPLORER")
        self.header.new_folder_btn.clicked.connect(self._on_new_folder)
        self.header.more_btn.clicked.connect(self._on_more_actions)
        content_layout.addWidget(self.header)
        
        # Stacked widget for different activity views
        self._content_stack = QStackedWidget()
        
        # Welcome screen (shown when no workspace)
        from ui.explorer.welcome_screen import WelcomeScreen
        self.welcome_screen = WelcomeScreen(self.event_bus)
        self.welcome_screen.open_folder_requested.connect(
            lambda: self.event_bus.publish("show_open_folder", {})
        )
        self.welcome_screen.recent_project_selected.connect(self._on_recent_project_selected)
        self._content_stack.addWidget(self.welcome_screen)
        
        # File tree (shown when workspace is open)
        self.tree = PremiumFileTree(self.event_bus)
        self.tree.file_opened.connect(self._on_file_opened)
        self.tree.file_selected.connect(self._on_file_selected)
        self._content_stack.addWidget(self.tree)
        
        # Search panel (placeholder for now)
        self.search_panel = QWidget()
        search_layout = QVBoxLayout(self.search_panel)
        search_layout.setContentsMargins(12, 12, 12, 12)
        search_label = QLabel("Search")
        search_label.setStyleSheet("color: #888; font-style: italic;")
        search_layout.addWidget(search_label)
        search_layout.addStretch()
        self._content_stack.addWidget(self.search_panel)
        
        # Git panel (placeholder for now)
        self.git_panel = QWidget()
        git_layout = QVBoxLayout(self.git_panel)
        git_layout.setContentsMargins(12, 12, 12, 12)
        git_label = QLabel("Source Control")
        git_label.setStyleSheet("color: #888; font-style: italic;")
        git_layout.addWidget(git_label)
        git_layout.addStretch()
        self._content_stack.addWidget(self.git_panel)
        
        # Debug panel (placeholder for now)
        self.debug_panel = QWidget()
        debug_layout = QVBoxLayout(self.debug_panel)
        debug_layout.setContentsMargins(12, 12, 12, 12)
        debug_label = QLabel("Debug & Run")
        debug_label.setStyleSheet("color: #888; font-style: italic;")
        debug_layout.addWidget(debug_label)
        debug_layout.addStretch()
        self._content_stack.addWidget(self.debug_panel)
        
        # Extensions panel (placeholder for now)
        self.extensions_panel = QWidget()
        ext_layout = QVBoxLayout(self.extensions_panel)
        ext_layout.setContentsMargins(12, 12, 12, 12)
        ext_label = QLabel("Extensions")
        ext_label.setStyleSheet("color: #888; font-style: italic;")
        ext_layout.addWidget(ext_label)
        ext_layout.addStretch()
        self._content_stack.addWidget(self.extensions_panel)
        
        # Memory panel (placeholder for now)
        self.memory_panel = QWidget()
        mem_layout = QVBoxLayout(self.memory_panel)
        mem_layout.setContentsMargins(12, 12, 12, 12)
        mem_label = QLabel("AI Memory")
        mem_label.setStyleSheet("color: #888; font-style: italic;")
        mem_layout.addWidget(mem_label)
        mem_layout.addStretch()
        self._content_stack.addWidget(self.memory_panel)
        
        # Tasks panel (placeholder for now)
        self.tasks_panel = QWidget()
        task_layout = QVBoxLayout(self.tasks_panel)
        task_layout.setContentsMargins(12, 12, 12, 12)
        task_label = QLabel("Tasks")
        task_label.setStyleSheet("color: #888; font-style: italic;")
        task_layout.addWidget(task_label)
        task_layout.addStretch()
        self._content_stack.addWidget(self.tasks_panel)
        
        # Settings panel (placeholder for now)
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("color: #888; font-style: italic;")
        settings_layout.addWidget(settings_label)
        settings_layout.addStretch()
        self._content_stack.addWidget(self.settings_panel)
        
        # Start with welcome screen
        self._content_stack.setCurrentWidget(self.welcome_screen)
        
        # Track current activity
        self._current_activity = "explorer"
        
        content_layout.addWidget(self._content_stack)
        
        main_layout.addWidget(content_widget)
        
        # Resize handle
        self._resize_handle = ResizeHandle(self)
        self._resize_handle.resize_moved.connect(self._on_resize)
        self._resize_handle.resize_started.connect(self._on_resize_started)
        self._resize_handle.resize_finished.connect(self._on_resize_finished)
        main_layout.addWidget(self._resize_handle)
        
        # Apply background styling
        self.setStyleSheet(f"""
            #PremiumExplorer {{
                background-color: {p.sidebar};
            }}
        """)
    
    def _on_resize_started(self):
        """Handle resize drag start."""
        self._is_resizing = True
    
    def _on_resize(self, delta: int):
        """Handle resize drag."""
        new_width = max(Sidebar.MIN_WIDTH, min(Sidebar.MAX_WIDTH, self.width() + delta))
        # Update both min and max to the same value to "fix" width during resize
        self.setMinimumWidth(new_width)
        self.setMaximumWidth(new_width)
        self._current_width = new_width
    
    def _on_resize_finished(self):
        """Handle resize drag end - unlock max width to allow future resizing."""
        self._is_resizing = False
        # After manual resize, keep min at current width but allow max to expand
        # This preserves the current width while allowing future animations and resizes
        self.setMinimumWidth(self._current_width)
        self.setMaximumWidth(Sidebar.MAX_WIDTH)
        
    def _on_new_folder(self):
        self.new_folder_requested.emit()
        
    def _on_more_actions(self):
        self.more_actions_requested.emit()
        
    def _on_file_opened(self, path: str):
        self.event_bus.publish("file_selected", {"path": path})
        
    def _on_file_selected(self, path: str):
        self.event_bus.publish("file_selected", {"path": path})
    
    def _on_workspace_loaded(self, data: dict):
        """Handle workspace loaded - switch to file tree."""
        self._has_workspace = True
        self._content_stack.setCurrentWidget(self.tree)
        
        # Set root path if provided
        path = data.get("path", "")
        if path:
            self.set_root_path(path)
    
    def _on_workspace_closed(self, data: dict):
        """Handle workspace closed - switch to welcome screen."""
        self._has_workspace = False
        self._content_stack.setCurrentWidget(self.welcome_screen)
    
    def _on_recent_project_selected(self, path: str):
        """Handle recent project selection - open it."""
        self.event_bus.publish("request_open_workspace", {"path": path})
        
    def set_root_path(self, path: str):
        """Set the root path."""
        self.tree.set_root_path(path)
        
    def set_header_title(self, title: str):
        """Update header title."""
        self.header.update_title(title)
    
    def switch_activity(self, activity_id: str):
        """Switch to a different activity panel."""
        self._current_activity = activity_id
        
        # If no workspace is loaded, show welcome screen for explorer
        if activity_id == "explorer" and not self._has_workspace:
            self._content_stack.setCurrentWidget(self.welcome_screen)
            return
        
        # Map activity IDs to widgets
        activity_widgets = {
            "explorer": self.tree,
            "search": self.search_panel,
            "git": self.git_panel,
            "debug": self.debug_panel,
            "extensions": self.extensions_panel,
            "memory": self.memory_panel,
            "tasks": self.tasks_panel,
            "settings": self.settings_panel,
        }
        
        widget = activity_widgets.get(activity_id, self.tree)
        if widget:
            self._content_stack.setCurrentWidget(widget)
    
    def resizeEvent(self, event):
        """Track width changes for state persistence."""
        super().resizeEvent(event)
        if self.width() > 0 and not self._is_resizing:  # Only track non-zero widths when not actively resizing
            self._current_width = self.width()
