# MyCodingMaster v1.0 Bugfix Design

## Overview

This bugfix sprint addresses seven critical phases preventing MyCodingMaster from functioning as a professional IDE:

1. **Workspace Phase**: Fix "Open Project" - Explorer remains empty, folders not populated
2. **Explorer Phase**: Fix folder tree browsing (expand/collapse, icons, file counts)
3. **Editor Phase**: Fix double-click file opening workflow
4. **Terminal Phase**: Fix terminal initialization and functionality
5. **Toolbar Phase**: Fix all dead buttons (every button must work or show "Coming Soon")
6. **Status Bar Phase**: Fix live data updates (workspace, file, cursor, language, encoding, etc.)
7. **Performance Phase**: Fix UI freezing (heavy operations must run in background threads with progress indicators)

**Key Fix Strategy**: All fixes focus on existing broken functionality. No new features or backend systems. All heavy operations use EventBus for background threading.

## Glossary

- **Bug_Condition (C)**: Condition that triggers the bug - workspace loading/explorer population failures
- **Property (P)**: Expected correct behavior - Explorer should show tree with expand/collapse, icons, file counts
- **Preservation**: Existing working behaviors that must not be broken
- **ProjectScanner**: The single entry point for workspace analysis (v0.3 milestone)
- **EventBus**: Asynchronous event distribution system (core/event_bus.py) - prevents UI freezing
- **TreeBuilder**: Builds in-memory TreeNode folder tree (ai/tools/tree_builder.py)
- **TreeNode**: Dataclass representing file/folder with path, name, is_dir, children, files
- **ExplorerPanel**: 240px sliding panel with Explorer/Search/Git/Debug/Memory sub-panels
- **ProjectPanel**: QTreeWidget wrapper for displaying folder tree in Explorer
- **EditorTabs**: Multi-tab editor interface (ui/editor/editor_tabs.py)

## Bug Details

### Bug Condition

**Bug 1 - Explorer Empty**: When "Open Project" is selected, the workspace opens but the Explorer panel remains empty without any files or folders displayed.

**Bug 2 - Explorer Browsing**: When folders are displayed in Explorer, they cannot be expanded or collapsed properly, icons are missing, file/folder counts are not shown.

**Bug 3 - Editor File Opening**: When a file is double-clicked in the project tree, the editor tab does not open and the file content is not displayed.

**Bug 4 - Terminal Functionality**: When Terminal panel is opened, the terminal fails to initialize or run commands.

**Bug 5 - Dead Toolbar Buttons**: When toolbar buttons are clicked (Open, Save, Scan, Run, Stop, Refresh, Settings, Theme), most buttons are non-functional or show no response.

**Bug 6 - Status Bar Not Updating**: When status bar is displayed, it does not update live with workspace, file, cursor position, language, encoding, or background task information.

**Bug 7 - UI Freezing**: When heavy AI processing or scanning operations run, the UI freezes and becomes unresponsive without any progress indicators.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type WorkspaceEvent | MouseEvent | KeyEvent | SystemEvent
  OUTPUT: boolean
  
  CASE input.event_type:
    WHEN "workspace_loaded":
      RETURN tree_root IS NULL OR tree_root.children IS EMPTY
             OR explorer_tree_widget.itemCount = 0
    
    WHEN "folder_expanded" OR "folder_collapsed":
      RETURN target_folder IS NULL OR target_folder.children IS EMPTY
    
    WHEN "file_double_clicked":
      RETURN editor_tab NOT CREATED OR file_content NOT LOADED
    
    WHEN "terminal_opened":
      RETURN terminal_process NOT STARTED OR PTY NOT INITIALIZED
    
    WHEN "toolbar_button_clicked":
      RETURN button_action NOT IMPLEMENTED OR NO_RESPONSE
    
    WHEN "status_update_required":
      RETURN status_labels NOT UPDATED OR DATA STALE
    
    WHEN "heavy_operation_started":
      RETURN UI_BLOCKED OR NO_PROGRESS_INDICATOR
  END CASE
  
  RETURN FALSE
END FUNCTION
```

### Examples

**Bug 1 - Explorer Empty (from workspace_manager.py:60-67):**
- **Expected**: WorkspaceManager.scan() calls ProjectScanner → creates context → EventBus.publish("workspace_loaded", {"context": context})
- **Actual**: workspace_loaded event fires but Explorer panel doesn't populate tree
- **Root cause**: ProjectPanel.handle_workspace_loaded() at ui/project_panel.py:99-108 builds tree, but context.tree may be None or empty

**Bug 2 - Explorer Browsing (from project_panel.py:14-66):**
- **Expected**: QTreeWidget with expand/collapse, icons, lazy loading
- **Actual**: Tree shows but children don't load on expand, icons may be missing
- **Root cause**: build_tree_item() may not handle lazy loading or icon setup correctly

**Bug 3 - Editor File Opening (from center_panel.py:140-147):**
- **Expected**: file_selected event → EditorTabs.open_file() → new tab with content
- **Actual**: double-click on file item doesn't trigger file_selected event or EditorTabs doesn't open
- **Root cause**: ProjectPanel.handle_item_double_clicked() at line 59-62 may not publish correct event

**Bug 4 - Terminal (from bottom_dock.py:17-29):**
- **Expected**: TerminalTab with PTY integration for running commands
- **Actual**: TerminalTab is stub QPlainTextEdit placeholder, no real terminal
- **Root cause**: v0.4 terminal is explicitly stubbed for v0.5 PTY integration

**Bug 5 - Dead Toolbar Buttons (from top_toolbar.py:109-125):**
- **Expected**: Every button either works or shows "Coming Soon"
- **Actual**: Most buttons have no connected slots or empty lambdas
- **Root cause**: Buttons have slots connected but implementations are stubs or missing

**Bug 6 - Status Bar (from status_bar.py:96-128):**
- **Expected**: Live updates for workspace, cursor, language, encoding, AI status
- **Actual**: Status bar shows "No Workspace" or stale data
- **Root cause**: EventBus events may not be published or handlers may not update correctly

**Bug 7 - UI Freezing (from event_bus.py:33-39):**
- **Expected**: Heavy operations run in background threads, UI remains responsive
- **Actual**: UI freezes during scanning, AI processing, or file I/O
- **Root cause**: EventBus uses threading but operations may still block main thread

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- EventBus-based async communication must continue to work (no synchronous calls)
- ThemeManager dark/light mode must continue to function
- QTreeWidget folder tree navigation must work as before
- EditorTabs multi-tab system must continue to support close, switch, save
- NavigationRail panel switching must continue to work
- Dashboard welcome screen must continue to show recent projects

**Scope:**
All inputs that do NOT involve the seven bug conditions should be completely unaffected by this fix. This includes:
- Mouse clicks on working buttons (already functional)
- Keyboard shortcuts (already implemented)
- Theme switching (already implemented)
- Dashboard navigation (already implemented)

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **ProjectScanner Context Not Populating Tree**
   - TreeBuilder.build() may return None or empty tree
   - ProjectScanner may fail silently during scan
   - ProjectPanel may not properly handle empty/None tree

2. **Explorer Panel Event Handling**
   - ProjectPanel may not subscribe to workspace_loaded event
   - handle_workspace_loaded() may not clear existing tree before rebuilding
   - QTreeWidget may not expand root item after population

3. **Editor File Opening Workflow**
   - ProjectPanel.handle_item_double_clicked() may not publish file_selected event
   - CenterPanel may not subscribe to file_selected event
   - EditorTabs.open_file() may not handle path properly

4. **Terminal Implementation**
   - TerminalTab is explicitly stubbed for v0.5 PTY integration
   - No real terminal process execution exists in v0.4
   - Requires PTY integration (deferred to v0.5 per requirements)

5. **Toolbar Button Connections**
   - TopToolbar has slots but many are empty lambdas or None
   - scan_project_requested has no subscriber in main_window.py
   - save_requested has no implementation in editor tabs

6. **Status Bar Event Subscriptions**
   - BottomStatusBar subscribes to many events but handlers may not update UI
   - workspace_loaded handler at line 118 may not update workspace path
   - tab_switched handler at line 142 may not detect language correctly

7. **Heavy Operation Threading**
   - EventBus uses threading but main thread may still block
   - ProjectScanner.scan() runs synchronously before EventBus publish
   - Tree building may take time and block UI during scan

## Correctness Properties

Property 1: Bug Condition - Workspace Loading and Explorer Population

_For any_ workspace opening event, the fixed code SHALL:
1. Scan the project folder recursively using TreeBuilder
2. Build an in-memory folder tree with all files and subfolders
3. Populate the Explorer QTreeWidget with the complete tree structure
4. Set root item as expanded by default
5. Display proper folder/file icons for each tree node

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Existing Editor and UI Functionality

_For any_ input that is NOT a bug condition (files already opened in editor tabs, existing explorer navigation, working toolbar buttons, status updates), the fixed code SHALL produce the same result as the original code, preserving all existing functionality.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

Property 3: Error Handling - Graceful Degradation

_For any_ workspace that fails to scan (empty directory, permission denied, invalid path), the fixed code SHALL:
1. Display appropriate error message in logs
2. Show user-friendly error notification via EventBus
3. Keep existing UI state unchanged (don't clear workspace)
4. Allow retry without application restart

**Validates: Requirements 1.1 error handling requirement**

Property 4: Performance - Background Thread Execution

_For any_ heavy operation (project scanning, tree building, file I/O), the fixed code SHALL:
1. Execute operations in background thread via EventBus
2. Display progress indicators during operation
3. Keep UI responsive throughout operation
4. Publish completion events on main thread

**Validates: Requirements 1.6, 7.1**

## Fix Implementation

### Changes Required

**File 1**: `ui/project_panel.py` (Explorer tree population)

**Current Issue**: ProjectPanel.handle_workspace_loaded() at lines 99-108 may not properly handle tree population

**Specific Changes**:
1. **Add error handling**: Wrap tree building in try-except to handle None/empty trees
2. **Clear before rebuild**: Add `self.tree.clear()` before adding new items
3. **Expand root**: Ensure root item is expanded by default
4. **Lazy loading support**: Add expand/collapse handlers for child nodes
5. **Count display**: Add file/folder count to tree root or status

**Implementation Details**:
```python
def handle_workspace_loaded(self, event_data):
    context = event_data.get("context")
    if not context or not context.tree:
        # Show error message or placeholder
        self.tree.clear()
        item = QTreeWidgetItem(["No files found"])
        self.tree.addTopLevelItem(item)
        return
        
    self.tree.clear()  # FIX: Clear before rebuild
    root_node = context.tree
    root_item = self.build_tree_item(root_node)
    self.tree.addTopLevelItem(root_item)
    root_item.setExpanded(True)  # FIX: Expand root by default
```

**File 2**: `ui/project_panel.py` (Double-click file opening)

**Current Issue**: handle_item_double_clicked() at lines 59-62 may not publish correct event

**Specific Changes**:
1. **Publish file_selected event**: Ensure event includes absolute path
2. **Add validation**: Check path exists before publishing
3. **Log debug info**: Add logger.debug for troubleshooting

**Implementation Details**:
```python
def handle_item_double_clicked(self, item, column):
    path = item.data(0, Qt.UserRole)
    if not path:
        logger.warning("Double-clicked item has no path data")
        return
        
    if not Path(path).exists():
        logger.error(f"Path does not exist: {path}")
        return
        
    self.event_bus.publish("file_selected", {"path": path})
    logger.debug(f"File double-clicked: {path}")
```

**File 3**: `ui/center_panel.py` (Editor file opening)

**Current Issue**: No subscription to file_selected event

**Specific Changes**:
1. **Subscribe to file_selected**: Add event listener in __init__
2. **Handle file_selected**: Extract path, get content, open editor tab
3. **Add error handling**: Handle file read errors gracefully

**Implementation Details**:
```python
def __init__(self, event_bus):
    super().__init__()
    self.event_bus = event_bus
    # ... existing setup code ...
    self.event_bus.subscribe("file_selected", self._on_file_selected)  # FIX

def _on_file_selected(self, data):
    path = data.get("path", "")
    if not path:
        return
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.editor_tabs.open_file(Path(path), content)
        logger.debug(f"Opened file in editor: {path}")
    except Exception as e:
        logger.error(f"Failed to open file {path}: {e}")
        self.event_bus.publish("notification_show", {
            "title": "Error",
            "message": f"Could not open file: {path}",
            "type": "error"
        })
```

**File 4**: `ui/top_toolbar.py` (Dead toolbar buttons)

**Current Issue**: Many buttons have empty implementations or missing slots

**Specific Changes**:
1. **Save button**: Connect to EditorTabs save functionality
2. **Scan button**: Implement project scanning with progress
3. **Refresh button**: Implement workspace refresh
4. **Settings button**: Open settings dialog or panel
5. **Add "Coming Soon" placeholder**: For buttons not yet implemented

**Implementation Details**:
```python
def setup_ui(self):
    # ... existing button setup ...
    
    # FIX: Connect save button to event
    self.btn_save.clicked.connect(self._on_save_clicked)
    
    # FIX: Implement scan button
    self.btn_scan.clicked.connect(self._on_scan_clicked)
    
    # FIX: Add refresh button
    self.btn_refresh = self._btn("↻ Refresh", "Refresh Workspace")
    self.btn_refresh.clicked.connect(self._on_refresh_clicked)
    self.addWidget(self.btn_refresh)
    
    # FIX: Add settings button
    self.btn_settings = self._btn("⚙", "Settings")
    self.btn_settings.clicked.connect(self._on_settings_clicked)
    self.addWidget(self.btn_settings)

def _on_save_clicked(self):
    self.event_bus.publish("request_save_current", {})

def _on_scan_clicked(self):
    self.event_bus.publish("request_scan_workspace", {})

def _on_refresh_clicked(self):
    self.event_bus.publish("request_scan_workspace", {})  # Re-scan

def _on_settings_clicked(self):
    self.event_bus.publish("settings_open_requested", {})
```

**File 5**: `ui/status_bar.py` (Status bar updates)

**Current Issue**: Some handlers may not update UI correctly

**Specific Changes**:
1. **Add cursor info**: Update _on_cursor to show encoding and line count
2. **Add AI status**: Show AI operation progress
3. **Add memory/CPU**: Show system resource usage
4. **Add background tasks**: Show count of active background operations

**Implementation Details**:
```python
def setup_ui(self):
    # ... existing status chip setup ...
    
    # FIX: Add memory and CPU chips
    self._lbl_memory = StatusChip("Mem: --")
    self._lbl_cpu = StatusChip("CPU: --")
    self._lbl_tasks = StatusChip("Tasks: 0")
    
    self.addPermanentWidget(_separator_label())
    self.addPermanentWidget(self._lbl_memory)
    self.addPermanentWidget(_separator_label())
    self.addPermanentWidget(self._lbl_cpu)
    self.addPermanentWidget(_separator_label())
    self.addPermanentWidget(self._lbl_tasks)

def _on_workspace(self, data):
    # ... existing implementation ...
    self._lbl_ws.setText(root)
    self._lbl_ws.set_accent(False)
    
    # FIX: Update memory/CPU after delay to allow scan to complete
    self._update_system_stats()

def _update_system_stats(self):
    """Update memory and CPU usage (placeholder implementation)"""
    try:
        import psutil
        self._lbl_memory.setText(f"Mem: {psutil.virtual_memory().percent:.0f}%")
        self._lbl_cpu.setText(f"CPU: {psutil.cpu_percent():.0f}%")
    except ImportError:
        self._lbl_memory.setText("Mem: N/A")
        self._lbl_cpu.setText("CPU: N/A")
```

**File 6**: `core/workspace_manager.py` (Background scanning)

**Current Issue**: ProjectScanner.scan() runs synchronously, blocking UI

**Specific Changes**:
1. **Move scanning to thread**: Run ProjectScanner in background thread
2. **Publish progress**: Emit progress events during scan
3. **Handle thread completion**: Publish workspace_loaded on main thread

**Implementation Details**:
```python
import threading
import time

def open_workspace(self, path_str: str):
    path = Path(path_str).resolve()
    
    # Show progress
    self.event_bus.publish("log_message", {"message": f"Scanning workspace: {path}"})
    self.event_bus.publish("task_started", {"type": "workspace_scan"})
    
    # Run scan in background thread
    def scan_worker():
        try:
            scanner = ProjectScanner(path)
            context = scanner.scan()  # This is the slow part
            
            self.current_workspace = path
            self.current_context = context
            self.add_recent_project(str(path))
            
            # Publish on main thread (QTimer.singleShot for PySide6)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._on_scan_complete(context, path))
            
        except Exception as e:
            logger.error(f"Workspace scan failed: {e}")
            self.event_bus.publish("task_failed", {"type": "workspace_scan", "error": str(e)})
    
    threading.Thread(target=scan_worker, daemon=True).start()

def _on_scan_complete(self, context, path):
    """Called from main thread after scan completes"""
    self.event_bus.publish("workspace_loaded", {"context": context})
    self.event_bus.publish("task_completed", {"type": "workspace_scan"})
    self.event_bus.publish("log_message", {"message": f"Workspace loaded: {path}"})
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach:
1. **Explore** - Write tests BEFORE fix to understand the bug (Bug Condition)
2. **Preserve** - Write tests for non-buggy behavior (Preservation Requirements)
3. **Implement** - Apply the fix with understanding (Expected Behavior)
4. **Validate** - Verify fix works and doesn't break anything

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write tests that simulate user actions and assert Explorer/Editor behavior. Run these tests on UNFIXED code to observe failures.

**Test Cases**:
1. **Workspace Open Test**: Simulate opening a project with files, assert Explorer shows files
2. **Explorer Expand Test**: Simulate expanding a folder, assert children load correctly
3. **File Double-Click Test**: Simulate double-clicking a file, assert EditorTab opens
4. **Toolbar Click Test**: Click each toolbar button, assert action is triggered
5. **Status Update Test**: Simulate workspace load, assert status bar updates
6. **Scanning Performance Test**: Scan a large project, assert UI doesn't freeze

**Expected Counterexamples**:
- Explorer shows "No project loaded" even with files in directory
- Folder expansion doesn't load child items
- Double-click on file doesn't open editor tab
- Toolbar buttons show no response when clicked
- Status bar shows "No Workspace" after project opens
- UI freezes for several seconds during scan

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode**:
```
FOR ALL input WHERE isBugCondition(input) DO
  result := FixedCode(input)
  ASSERT expected_behavior(result)
END FOR
```

**Test Cases**:
1. **Workspace Open**: After opening project, Explorer tree contains at least 1 item
2. **Folder Expand**: After expanding folder, children count > 0
3. **File Open**: After double-click, EditorTabs count >= 1
4. **Toolbar Action**: After clicking button, corresponding event is published
5. **Status Update**: After workspace_loaded, status bar shows workspace path
6. **No Freeze**: Scan completes within threshold, UI remains responsive

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode**:
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT OriginalFunction(input) = FixedFunction(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged

**Test Cases**:
1. **Theme Toggle**: Dark/light mode switching still works
2. **Existing Tabs**: Existing editor tabs can still be closed, switched, saved
3. **Rail Navigation**: NavigationRail panel switching still works
4. **Keyboard Shortcuts**: All shortcuts still function correctly
5. **Dashboard**: Welcome screen still shows recent projects

### Unit Tests

- Test ProjectPanel.handle_workspace_loaded() with valid/invalid contexts
- Test ProjectPanel.handle_item_double_clicked() with valid/invalid paths
- Test CenterPanel._on_file_selected() with valid/invalid paths
- Test TopToolbar._on_save_clicked() publishes correct event
- Test TopToolbar._on_scan_clicked() publishes correct event
- Test BottomStatusBar._on_workspace() updates UI correctly
- Test WorkspaceManager.open_workspace() handles errors gracefully

### Property-Based Tests

- Generate random workspace paths and verify Explorer population
- Generate random file paths and verify double-click opens editors
- Generate random toolbar button sequences and verify event publishing
- Generate random status update events and verify UI updates
- Generate random scan scenarios and verify no UI freezing

### Integration Tests

- Full workflow: Open project → Explorer populates → Expand folder → Double-click file → Editor opens
- Toolbar workflow: Click buttons → Events published → Actions executed
- Status workflow: Open project → Status bar updates → Continues updating
- Performance workflow: Open large project → UI stays responsive → Progress shown
