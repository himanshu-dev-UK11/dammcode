# MyCodingMaster v1.1 — UI Polish Design

## Technical Approach

### Phase 1: Theme & Color System

**Centralize Colors**:
```python
# ui/colors.py
DARK = {...}
LIGHT = {...}
SYSTEM = {...}  # Detect system theme

def get_color(token: str) -> str:
    """Get color for token based on current theme."""
    pass

def set_theme(theme: str):
    """Set theme (dark/light/system)."""
    pass
```

**Theme Manager**:
```python
# ui/theme.py
class ThemeManager:
    def __init__(self, app):
        self._app = app
        self._theme = "dark"
    
    def apply_theme(self, theme: str):
        """Apply theme and update stylesheet."""
        self._theme = theme
        stylesheet = build_stylesheet(self._colors)
        self._app.setStyleSheet(stylesheet)
    
    def toggle(self):
        """Toggle between dark/light/system."""
        pass
```

### Phase 2: Explorer Improvements

**File Type Icons**:
```python
def get_file_icon(path: Path) -> QIcon:
    """Get icon based on file extension."""
    ext = path.suffix.lower()
    icons = {
        '.py': QIcon(':/icons/python.png'),
        '.js': QIcon(':/icons/javascript.png'),
        # ... more extensions
    }
    return icons.get(ext, QIcon(':/icons/file.png'))
```

**Context Menu**:
```python
class ExplorerPanel:
    def show_context_menu(self, position):
        menu = QMenu()
        
        # File operations
        menu.addAction("New File", self._new_file)
        menu.addAction("New Folder", self._new_folder)
        menu.addAction("Rename", self._rename)
        menu.addAction("Duplicate", self._duplicate)
        menu.addAction("Delete", self._delete)
        
        menu.addSeparator()
        
        # Navigation
        menu.addAction("Reveal in Explorer", self._reveal)
        menu.addAction("Copy Path", self._copy_path)
        menu.addAction("Open Externally", self._open_externally)
        
        menu.addSeparator()
        
        # View
        menu.addAction("Refresh", self._refresh)
        menu.addSeparator()
        menu.addAction("Collapse All", self.tree.collapseAll)
        menu.addAction("Expand All", self.tree.expandAll)
        
        menu.exec_(self.tree.viewport().mapToGlobal(position))
```

### Phase 3: Editor Polish

**Tab Improvements**:
```python
class EditorTabs(QTabWidget):
    def __init__(self):
        # Pinned tabs always first
        self.pinned_tabs = []
        self.movable_tabs = []
        
        # Unsaved indicator
        self.tabBar().tabCloseRequested.connect(self._close_tab)
        self.tabBar().tabBarDoubleClicked.connect(self._rename_tab)
        
        # Mini map
        self.minimap = MiniMapWidget()
        self.minimap.hide()
        
        # Split editor
        self.split_view = None
```

**Session Restore**:
```python
def load_session(self):
    """Load previous editor session from config."""
    session_file = Path("config/editor_session.json")
    if session_file.exists():
        with open(session_file) as f:
            session = json.load(f)
        
        for filepath in session.get("files", []):
            if Path(filepath).exists():
                with open(filepath) as f:
                    content = f.read()
                self.open_file(Path(filepath), content)
```

### Phase 4: AI Workspace Redesign

**Simplified Layout**:
```python
class AIEngineeringWorkspace:
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Essential (always visible)
        self.current_task = CurrentTaskSection()
        self.progress = ExecutionProgressSection()
        self.conversation = ConversationSection()
        self.prompt_input = PromptInputSection()
        self.context = ContextSection()
        
        layout.addWidget(self.current_task)
        layout.addWidget(self.progress)
        layout.addWidget(self.conversation)
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.context)
        
        # Advanced (collapsible)
        self.advanced = AdvancedSection()
        layout.addWidget(self.advanced)
```

**Advanced Section**:
```python
class AdvancedSection(QCollapsible):
    def __init__(self):
        self.expanded = False
        
        self.plan = ExecutionPlanSection()
        self.verification = VerificationSection()
        self.tools = RunningToolsSection()
        self.memory = MemorySection()
        self.models = ModelsSection()
        self.logs = LogsSection()
        self.stats = StatisticsSection()
        
        self.layout.addWidget(self.plan)
        self.layout.addWidget(self.verification)
        # ... more sections
```

### Phase 5: Toolbar Rebuild

**Grouped Toolbar**:
```python
class TopToolbar:
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Workspace group
        workspace_group = self._create_group()
        workspace_group.addWidget(self._btn_open)
        workspace_group.addWidget(self._btn_save)
        layout.addWidget(workspace_group)
        
        # Project group
        project_group = self._create_group()
        project_group.addWidget(self._btn_scan)
        project_group.addWidget(self._btn_analyze)
        layout.addWidget(project_group)
        
        # ... more groups
```

**Disabled Button Pattern**:
```python
def _btn_disabled(self, text: str, tooltip: str = None) -> QToolButton:
    btn = QToolButton()
    btn.setText(text)
    btn.setEnabled(False)
    
    if tooltip:
        btn.setToolTip(f"{tooltip} — Coming Soon")
    else:
        btn.setToolTip("Coming Soon")
    
    return btn
```

### Phase 6: Bottom Panel

**All Tabs**:
```python
class BottomDock:
    def setup_ui(self):
        self.tabs = QTabWidget()
        
        self._terminal = TerminalTab()
        self._problems = ProblemsTab()
        self._output = OutputTab()
        self._debug = DebugTab()
        self._git = GitTab()
        self._logs = LogsTab()
        self._tasks = TasksTab()
        
        self.tabs.addTab(self._terminal, "Terminal")
        self.tabs.addTab(self._problems, "Problems")
        self.tabs.addTab(self._output, "Output")
        self.tabs.addTab(self._debug, "Debug")
        self.tabs.addTab(self._git, "Git")
        self.tabs.addTab(self._logs, "Logs")
        self.tabs.addTab(self._tasks, "Tasks")
```

### Phase 7: Status Bar

**Live Updates**:
```python
class BottomStatusBar:
    def __init__(self):
        # Background tasks timer
        self._tasks_timer = QTimer()
        self._tasks_timer.timeout.connect(self._update_tasks)
        self._tasks_timer.start(2000)  # Every 2 seconds
        
        # Memory/CPU timer
        self._system_timer = QTimer()
        self._system_timer.timeout.connect(self._update_system)
        self._system_timer.start(1000)  # Every 1 second
```

### Phase 8: Dashboard

**Recent Projects**:
```python
class Dashboard:
    def setup_ui(self):
        # Pinned projects
        self.pinned_list = QListWidget()
        self.pinned_list.itemClicked.connect(self._open_pinned)
        
        # Recent projects
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self._open_recent)
        
        # Quick actions
        self._btn_new_file = QPushButton("New File")
        self._btn_new_file.clicked.connect(self._new_file)
        
        self._btn_open_folder = QPushButton("Open Folder")
        self._btn_open_folder.clicked.connect(self._open_folder)
```

### Phase 9: UX Polish

**Loading States**:
```python
class LoadingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinner = QSpinner()
        self._message = QLabel()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self._spinner)
        layout.addWidget(self._message)
        layout.setAlignment(Qt.AlignCenter)
        
        self.hide()
    
    def show_loading(self, message: str = "Loading..."):
        self._message.setText(message)
        self.show()
    
    def hide_loading(self):
        self.hide()
```

### Phase 10: Performance

**Background Threads**:
```python
class BackgroundWorker(QThread):
    progress = Signal(int, int)  # current, total
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, task_fn):
        super().__init__()
        self._task_fn = task_fn
    
    def run(self):
        try:
            self._task_fn(self._progress_callback)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def _progress_callback(self, current: int, total: int):
        self.progress.emit(current, total)
```

**Skeleton Screens**:
```python
class SkeletonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(1000)
        self._animation.setLoopCount(-1)
        self._animation.setStartValue(0.3)
        self._animation.setEndValue(0.8)
        self._animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(0.3)
        painter.setBrush(QColor("#252528"))
        painter.drawRect(self.rect())
```

---

## Architecture Decisions

1. **Keep Existing Structure**: No architectural changes, only UI improvements
2. **EventBus for Updates**: All UI updates through EventBus, no direct calls
3. **QSplitter for Resizing**: Use QSplitter for all resizable areas
4. **QTabWidget for Tabs**: Standard tab behavior with custom styling
5. **QContextMenuEvent for Menus**: Standard context menu pattern
6. **QDrag for Drag and Drop**: Standard Qt drag and drop implementation
7. **QTimer for Debouncing**: Use QTimer for debouncing rapid events
8. **QScrollArea for Large Content**: Scroll area for lists, trees, etc.

---

## Testing Strategy

### Unit Tests:
- Theme color retrieval
- Icon selection by extension
- Context menu item visibility
- Tab close behavior
- Mini map sync
- Status bar updates

### Integration Tests:
- Explorer context menu commands
- Editor tab switching
- AI workspace section visibility
- Toolbar button states
- Bottom panel tab switching
- Dashboard recent projects

### Manual Testing Checklist:
- [ ] All buttons work or explain why disabled
- [ ] All icons render correctly
- [ ] All tooltips show on hover
- [ ] All animations are smooth
- [ ] All colors pass contrast checks
- [ ] All keyboard shortcuts work
- [ ] All drag and drop works
- [ ] All context menus work
- [ ] All tabs switch correctly
- [ ] All resizers work smoothly

---

## Git vs GitHub

- Git: Always available locally, used for snapshots, rollback, and history
- GitHub: Optional integration, disabled by default, manual enable required