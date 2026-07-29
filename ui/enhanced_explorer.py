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
    QTreeView, QFileSystemModel, QMenu, QAbstractItemView, QInputDialog, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QDir, QMimeData, QPropertyAnimation, QPoint, QEvent, QTimer, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QAction, QCursor, QMouseEvent, QKeySequence
from pathlib import Path
from typing import Optional
from ui.design_system import get_design_system, ActivityBar, Sidebar, Spacing, Radius, Easing, FontSize
from ui.explorer.context_menu import ContextMenuManager
from core.file_operations import FileOperations
from ui.explorer.copy_path import CopyPathManager
from core.file_watcher import FileWatcher
from core.logger import setup_logger
from ui.explorer.file_icons import get_file_icon
from ui.explorer.search import SearchBox


logger = setup_logger(__name__)


class ExplorerFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._query = ""
        self.setRecursiveFilteringEnabled(True)

    def set_query(self, query: str):
        self._query = query.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._query:
            return True

        model = self.sourceModel()
        if model is None:
            return False

        index = model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        name = model.fileName(index).lower()
        path = model.filePath(index).lower()
        return self._query in name or self._query in path


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
    selection_changed = Signal(list)

    def __init__(self, event_bus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.file_ops = FileOperations(event_bus, parent=self)
        self.copy_path_manager = CopyPathManager(event_bus)
        self._root_path: Optional[Path] = None
        self._clipboard_paths: list[Path] = []
        self._clipboard_cut = False
        self._expanded_paths: set[str] = set()

        self._source_model = QFileSystemModel(self)
        self._source_model.setRootPath("")
        self._source_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self._source_model.setNameFilterDisables(False)

        self._proxy_model = ExplorerFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._source_model)

        self.setModel(self._proxy_model)
        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.setIndentation(18)
        self.setAnimated(False)
        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self._file_watcher = FileWatcher(event_bus)
        self._file_watcher.file_modified.connect(self._schedule_refresh)
        self._file_watcher.file_deleted.connect(self._schedule_refresh)
        self._file_watcher.directory_created.connect(self._schedule_refresh)
        self._file_watcher.directory_deleted.connect(self._schedule_refresh)
        self.event_bus.subscribe("directory_changed", self._schedule_refresh)
        self.event_bus.subscribe("file_changed_externally", self._schedule_refresh)
        self.event_bus.subscribe("file_deleted_externally", self._schedule_refresh)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(120)
        self._refresh_timer.timeout.connect(self._refresh_model)

        self._setup_styling()
        self._setup_connections()

    def _setup_styling(self):
        p = get_design_system().palette

        self.setStyleSheet(f"""
            QTreeView {{
                background-color: transparent;
                border: none;
                font-size: {FontSize.SM}px;
                outline: none;
                selection-background-color: transparent;
                selection-color: {p.text};
            }}

            QTreeView::item {{
                padding: 4px {Spacing.SM}px;
                min-height: 24px;
                border-radius: {Radius.SM}px;
                margin: 1px 6px;
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

        for i in range(1, self._source_model.columnCount()):
            self.hideColumn(i)

    def _setup_connections(self):
        self.doubleClicked.connect(self._on_double_clicked)
        self.clicked.connect(self._on_clicked)
        self.expanded.connect(self._on_expanded)
        self.collapsed.connect(self._on_collapsed)

        if self.selectionModel() is not None:
            self.selectionModel().selectionChanged.connect(self._on_selection_changed)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_root_path(self, path: str):
        self._root_path = Path(path)
        self.copy_path_manager.set_workspace_root(self._root_path)
        self._expanded_paths = {str(self._root_path.resolve())}
        self._source_model.setRootPath(path)
        self._refresh_model()

        source_index = self._source_model.index(path)
        proxy_index = self._proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.setRootIndex(proxy_index)
            self.expand(proxy_index)

    def set_search_query(self, query: str):
        self._proxy_model.set_query(query)

    def _map_to_source(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        return self._proxy_model.mapToSource(index)

    def _path_for_index(self, index: QModelIndex) -> Optional[Path]:
        source_index = self._map_to_source(index)
        if source_index.isValid():
            return Path(self._source_model.filePath(source_index))
        return None

    def _selected_paths(self) -> list[Path]:
        paths: list[Path] = []
        for proxy_index in self.selectedIndexes():
            if proxy_index.column() != 0:
                continue
            path = self._path_for_index(proxy_index)
            if path and path not in paths:
                paths.append(path)
        return paths

    def _single_current_path(self) -> Optional[Path]:
        selected = self._selected_paths()
        if selected:
            return selected[0]
        return self._path_for_index(self.currentIndex())

    def _current_target_directory(self) -> Optional[Path]:
        path = self._single_current_path()
        if path is None:
            return self._root_path
        return path if path.is_dir() else path.parent

    def _on_double_clicked(self, index):
        path = self._path_for_index(index)
        if not path or not path.exists():
            return
        if path.is_file():
            self.file_opened.emit(str(path))
        else:
            self.directory_selected.emit(str(path))

    def _on_clicked(self, index):
        path = self._path_for_index(index)
        if not path or not path.exists():
            return
        if path.is_file():
            self.file_selected.emit(str(path))
        else:
            self.directory_selected.emit(str(path))

    def _on_selection_changed(self, *_):
        self.selection_changed.emit([str(path) for path in self._selected_paths()])

    def _on_expanded(self, index):
        path = self._path_for_index(index)
        if path and path.is_dir():
            resolved = str(path.resolve())
            if resolved not in self._expanded_paths:
                self._expanded_paths.add(resolved)
                self._file_watcher.watch_directory(path)

    def _on_collapsed(self, index):
        path = self._path_for_index(index)
        if path and path.is_dir():
            self._expanded_paths.discard(str(path.resolve()))

    def _schedule_refresh(self, *_):
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def _refresh_model(self):
        if not self._root_path or not self._root_path.exists():
            return

        self._source_model.setRootPath(str(self._root_path))
        self._file_watcher.clear_all()
        self._file_watcher.watch_directory(self._root_path)

        for path_str in list(self._expanded_paths):
            path = Path(path_str)
            if path.exists() and path.is_dir():
                self._file_watcher.watch_directory(path)

    def _show_context_menu(self, pos):
        index = self.indexAt(pos)
        if index.isValid() and not any(sel == index for sel in self.selectedIndexes()):
            self.setCurrentIndex(index)
            self.selectionModel().select(index, self.selectionModel().ClearAndSelect | self.selectionModel().Rows)

        paths = self._selected_paths()
        if not paths:
            if self._root_path:
                paths = [self._root_path]
            else:
                return

        current_path = paths[0]
        menu = QMenu(self)
        single_selection = len(paths) == 1
        all_dirs = all(path.is_dir() for path in paths)

        if single_selection and current_path.exists():
            if current_path.is_file():
                open_action = QAction("Open", menu)
                open_action.triggered.connect(lambda: self._open_path(current_path))
                menu.addAction(open_action)

                open_containing = QAction("Open Containing Folder", menu)
                open_containing.triggered.connect(lambda: self.file_ops.reveal_in_explorer(current_path))
                menu.addAction(open_containing)

                menu.addSeparator()

            rename_action = QAction("Rename", menu)
            rename_action.triggered.connect(lambda: self._rename_path(current_path))
            menu.addAction(rename_action)

            duplicate_action = QAction("Duplicate", menu)
            duplicate_action.triggered.connect(lambda: self._duplicate_paths([current_path]))
            menu.addAction(duplicate_action)

            menu.addSeparator()

        if len(paths) > 1:
            duplicate_action = QAction("Duplicate Selection", menu)
            duplicate_action.triggered.connect(lambda: self._duplicate_paths(paths))
            menu.addAction(duplicate_action)
            menu.addSeparator()

        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(lambda: self._delete_paths(paths))
        menu.addAction(delete_action)

        menu.addSeparator()

        copy_menu = menu.addMenu("Copy Path")
        for label, fmt in (("Absolute Path", "absolute"), ("Relative Path", "relative"), ("File Name", "name"), ("Extension", "extension")):
            action = QAction(label, copy_menu)
            action.triggered.connect(lambda checked=False, f=fmt, p=current_path: self.copy_path_manager.copy_path(p, f))
            copy_menu.addAction(action)

        copy_action = QAction("Copy", menu)
        copy_action.triggered.connect(lambda: self._copy_paths(paths))
        menu.addAction(copy_action)

        paste_action = QAction("Paste", menu)
        paste_action.triggered.connect(lambda: self._paste_to(current_path if current_path.is_dir() else current_path.parent))
        paste_action.setEnabled(bool(self._clipboard_paths))
        menu.addAction(paste_action)

        menu.addSeparator()

        reveal_action = QAction("Reveal in Explorer", menu)
        reveal_action.triggered.connect(lambda: self.file_ops.reveal_in_explorer(current_path))
        menu.addAction(reveal_action)

        if all_dirs:
            new_file_action = QAction("New File", menu)
            new_file_action.triggered.connect(lambda: self._create_file(current_path))
            menu.addAction(new_file_action)

            new_folder_action = QAction("New Folder", menu)
            new_folder_action.triggered.connect(lambda: self._create_folder(current_path))
            menu.addAction(new_folder_action)

        menu.addSeparator()

        refresh_action = QAction("Refresh", menu)
        refresh_action.triggered.connect(self._refresh_model)
        menu.addAction(refresh_action)

        menu.exec(self.viewport().mapToGlobal(pos))

    def _open_path(self, path: Path):
        if path.is_file():
            self.file_opened.emit(str(path))
        elif path.is_dir():
            source_index = self._source_model.index(str(path))
            proxy_index = self._proxy_model.mapFromSource(source_index)
            if proxy_index.isValid():
                self.expand(proxy_index)
                self.setCurrentIndex(proxy_index)

    def _rename_path(self, path: Path):
        if not path.exists():
            return

        new_name, ok = QInputDialog.getText(self, "Rename", f"Rename '{path.name}' to:", text=path.name)
        if ok and new_name and new_name != path.name:
            self.file_ops.rename(path, new_name)
            self._schedule_refresh()

    def _duplicate_paths(self, paths: list[Path]):
        for path in paths:
            if path.exists():
                self.file_ops.duplicate(path)
        self._schedule_refresh()

    def _delete_paths(self, paths: list[Path]):
        for path in paths:
            if path.exists():
                self.file_ops.delete(path)
        self._schedule_refresh()

    def _copy_paths(self, paths: list[Path]):
        self._clipboard_paths = [path for path in paths if path.exists()]
        self._clipboard_cut = False
        QApplication.clipboard().setText("\n".join(str(path) for path in self._clipboard_paths))

    def _cut_paths(self, paths: list[Path]):
        self._clipboard_paths = [path for path in paths if path.exists()]
        self._clipboard_cut = True
        QApplication.clipboard().setText("\n".join(str(path) for path in self._clipboard_paths))

    def _paste_to(self, target_dir: Path):
        if not target_dir or not target_dir.exists() or not target_dir.is_dir():
            return

        for source in list(self._clipboard_paths):
            if not source.exists():
                continue
            destination = target_dir / source.name
            if self._clipboard_cut:
                self.file_ops.move(source, destination)
            else:
                self.file_ops.copy(source, destination)

        if self._clipboard_cut:
            self._clipboard_paths = []
            self._clipboard_cut = False

        self._schedule_refresh()

    def _create_file(self, parent_dir: Path):
        result = self.file_ops.create_file(parent_dir)
        if result:
            self._schedule_refresh()

    def _create_folder(self, parent_dir: Path):
        result = self.file_ops.create_folder(parent_dir)
        if result:
            self._schedule_refresh()

    def _open_selected(self):
        path = self._single_current_path()
        if path and path.exists():
            self._open_path(path)

    def _rename_selected(self):
        path = self._single_current_path()
        if path and path.exists():
            self._rename_path(path)

    def _delete_selected(self):
        self._delete_paths(self._selected_paths())

    def _duplicate_selected(self):
        self._duplicate_paths(self._selected_paths())

    def _copy_selected(self):
        self._copy_paths(self._selected_paths())

    def _cut_selected(self):
        self._cut_paths(self._selected_paths())

    def _paste_selected(self):
        target = self._current_target_directory()
        if target:
            self._paste_to(target)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self._copy_selected()
            event.accept()
            return
        if event.matches(QKeySequence.Cut):
            self._cut_selected()
            event.accept()
            return
        if event.matches(QKeySequence.Paste):
            self._paste_selected()
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self._delete_selected()
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._open_selected()
            event.accept()
            return
        if event.key() == Qt.Key_F2:
            self._rename_selected()
            event.accept()
            return
        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            self._duplicate_selected()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.source() is self and self._selected_paths():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() is self and self._selected_paths():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def startDrag(self, supportedActions):
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        target_index = self.indexAt(event.position().toPoint())
        target_path = self._path_for_index(target_index)
        if target_path and target_path.is_file():
            target_path = target_path.parent
        elif not target_path:
            target_path = self._root_path

        if not target_path or not target_path.exists():
            super().dropEvent(event)
            return

        source_paths = self._selected_paths()
        if not source_paths:
            super().dropEvent(event)
            return

        is_copy = bool(event.keyboardModifiers() & Qt.ControlModifier) or not self._clipboard_cut
        for source in source_paths:
            if source == target_path or target_path in source.parents:
                continue
            destination = target_path / source.name
            if is_copy:
                self.file_ops.copy(source, destination)
            else:
                self.file_ops.move(source, destination)

        self._clipboard_paths = []
        self._clipboard_cut = False
        self._schedule_refresh()
        event.acceptProposedAction()


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
        search_layout.setSpacing(8)
        search_title = QLabel("Search in Workspace")
        search_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #888;")
        search_layout.addWidget(search_title)

        self.search_box = SearchBox()
        self.search_box.search_changed.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box)

        search_hint = QLabel("Instantly filters the Explorer tree.")
        search_hint.setStyleSheet("color: #888; font-style: italic;")
        search_layout.addWidget(search_hint)
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
        
        # Update parent splitter to redistribute space
        if self.parent() and hasattr(self.parent(), 'parent'):
            parent_splitter = self.parent().parent()
            if hasattr(parent_splitter, 'setSizes'):
                current_sizes = parent_splitter.sizes()
                if len(current_sizes) >= 2:
                    total_width = sum(current_sizes)
                    # Maintain total width while adjusting sidebar
                    current_sizes[0] = new_width
                    current_sizes[1] = total_width - new_width
                    parent_splitter.setSizes(current_sizes)
    
    def _on_resize_finished(self):
        """Handle resize drag end - unlock max width to allow future resizing."""
        self._is_resizing = False
        # After manual resize, allow flexible resizing
        self.setMinimumWidth(Sidebar.MIN_WIDTH)
        self.setMaximumWidth(Sidebar.MAX_WIDTH)
        
        # Update parent splitter to ensure proper space distribution
        if self.parent() and hasattr(self.parent(), 'parent'):
            parent_splitter = self.parent().parent()
            if hasattr(parent_splitter, 'setSizes'):
                current_sizes = parent_splitter.sizes()
                if len(current_sizes) >= 2:
                    # Ensure sidebar gets proper space
                    current_sizes[0] = self._current_width
                    parent_splitter.setSizes(current_sizes)
        
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

    def _on_search_changed(self, query: str, options: dict):
        """Filter the live Explorer tree without affecting workspace indexing."""
        self.tree.set_search_query(query)
        
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
