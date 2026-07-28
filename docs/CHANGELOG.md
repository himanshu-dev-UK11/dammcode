# Changelog

## [1.8.5-system-hardening] — 2026-07-06

### New — Core System Hardening: Crash Prevention & Reliability

**Problem**: The application lacked critical safety nets. No global error handler, no startup validation, safe file writes, or performance monitoring.

#### New Modules Created:

- `core/error_manager.py`: Global exception handler, error history, safe execute decorator, thread-safe error tracking
- `core/safe_file_ops.py`: Atomic file writes using temp files, write verification, backup, validation
- `core/startup_validator.py`: Startup environment validation, auto-repair of missing/corrupted configs
- `core/resource_manager.py`: Resource tracking (threads/files/processes), auto cleanup
- `core/config_validator.py`: Config validation/repair with defaults
- `core/performance_watchdog.py`: Memory/CPU/thread/UI lag monitoring

#### Updated:
- `core/editor_manager.py`: Now uses safe_write_text for atomic file saves, no corruption risk
- `core/__init__.py`: Exports all new core modules
- `core/error_manager.py`: Added get_error_history(), set_event_bus()
- `core/resource_manager.py`: Added get_resource_count(), set_event_bus()

### Verification:
- ✅ No uncaught exceptions crash the app
- ✅ Safe writes, no file corruption
- ✅ Startup validates/repairs configs
- ✅ Resources are tracked
- ✅ is monitored

---

## [2.2.0-layout] — 2026-07-06

### Layout Responsiveness — Professional Sizing Pass

All panels now fit naturally at the default startup window size (1024×680 minimum). Users no longer need to resize panels to access any controls.

#### `ui/main_window.py`
- `setMinimumSize(1024, 680)` — was 1600×950
- `showEvent` + `_apply_default_layout_sizes()` — applies proportional sizes once the real window dimensions are known: sidebar ≈14% [180–260px], AI ≈25% [240–380px]
- Activity bar: `setFixedWidth(44)`, buttons `setFixedSize(36, 36)`, margins `(2,6,2,6)`
- Sidebar: `setMinimumWidth(160)`, `setMaximumWidth(420)`, header `setFixedHeight(30)`, toggle button `setFixedSize(22, 22)`
- Inner splitter initial hint: `[220, 780]`; outer splitter: `[44, 956]`
- AI dock: `setMinimumWidth(240)`, `setMaximumWidth(480)`, `resizeDocks([280])`
- Bottom dock: `resizeDocks([180])`
- `_reset_layout` fixed — was referencing non-existent `self._explorer_dock`
- `_toggle_sidebar` uses 220px expand size

#### `ui/project_panel.py`
- Empty state: margins `(12,16,12,12)`, spacing `8`, icon `font-size: 28px`, title `font-size: 11px`, button `setFixedHeight(26)` with `font-size: 11px`
- `QTreeView` styled: `setIndentation(12)`, `setAnimated(False)`, `setUniformRowHeights(True)`, item `min-height: 20px`, hover/selection highlight, 6px scrollbar

#### `ui/terminal/terminal_toolbar.py`
- Removed `min-width: 80px` from `QToolButton` stylesheet
- Toolbar padding: `2px 4px`, spacing `2px`; button padding `2px 5px`
- Shell combo: `setFixedWidth(80)`, padding `2px 4px`
- Directory label: `setMaximumWidth(220)`, `set_working_directory` shows last 2 path parts, full path as tooltip

#### `ui/ai_workspace/ai_chat_panel.py`
- `QSizePolicy` and `QGridLayout` moved to module-level imports
- Quick actions: `QGridLayout` 2×4 grid — all 8 buttons always visible with `QSizePolicy.Expanding`
- Controls: margins `(6,5,6,5)`, spacing `3`, label `fixedWidth(52)`
- Combos: `setSizeAdjustPolicy(AdjustToMinimumContentsLengthWithIcon)`, `setMinimumContentsLength(8)`, stretch factor 1 in row
- Status indicator: `QSizePolicy.Expanding` — no more overflow
- Removed duplicate `from PySide6.QtWidgets import QSizePolicy` inside method body



### Fixed — Editor Engine: Complete Workflow

**Problem**: Editor behaved as a placeholder. Files could not be reliably opened, editor tabs were incomplete, saving was broken, and syntax highlighting crashed for languages with block comments.

#### `core/editor_manager.py` (complete rewrite — v2.0)
- Multi-encoding file loading: UTF-8 → UTF-16 → Latin-1 fallback
- Read-only file detection via `stat().st_mode`
- Large file warning (>10 MB)
- External file change detection via `QFileSystemWatcher`, publishes `file_changed_externally`
- Correct event payload: `{path, content, encoding, read_only}`
- Subscribed to `request_save_current` (Ctrl+S from menu)
- Session persistence of open tabs

#### `ui/center_panel.py`
- **CRITICAL FIX**: `_on_file_opened()` now calls `self.editor_tabs.open_file(path, content, read_only=read_only)`. This was the primary broken link — files were read and published but never rendered.
- Added `_on_save_current_requested()` — saves active editor on Ctrl+S from menu
- Added `_on_file_changed_externally()` — shows reload/discard prompt when file changes on disk
- Added `QMessageBox` import

#### `ui/editor/editor_tabs.py`
- `setup_connections()` now calls `setup_sticky_tab_manager()` and `setup_tab_operations()` — tab context menu (pin/duplicate/close-others) now works
- `open_file()` accepts `read_only` param; marks editor as read-only and shows 🔒 in tab
- `close_tab()` shows Save/Discard/Cancel dialog for unsaved changes; publishes `editor_closed` and `tab_closed`
- `on_editor_modified()` shows `●` indicator (not `*`) and publishes `editor_modified`
- `on_tab_changed()` publishes both `tab_switched` and `tab_changed`; syncs modified indicator
- `_on_editor_saved_event()` clears modified indicator when `editor_saved` is published
- `find_text()` — complete rewrite: uses `QTextDocument.find()`, wraps around, moves cursor
- `replace_text()` — replaces selection then finds next
- `replace_all_text()` — iterates entire document, counts replacements, logs result
- `_show_search()` / `_hide_search()` — Ctrl+F shows search bar, Escape hides it
- `QShortcut` moved to `QWidgets` import (not `QGui`)

#### `ui/editor/code_editor.py`
- `setup_highlighter()` passes `str(self.file_path)` instead of bare extension — fixes all non-Python language highlighting
- Ctrl+S publishes `{editor: self, path: self.file_path}` so `EditorManager` can write the file

#### `ui/editor/syntax_highlighter.py`
- `import re` moved to top of file — fixes `NameError` crash when highlighting block comments (JS, C, C++, Java, etc.)

#### `ui/main_window.py`
- Edit menu: Undo, Redo, Cut, Copy, Paste, Select All all wired to active editor via `_editor_action()`
- Find and Replace menu actions show the search bar via `_show_find()`
- Added `_show_find()` and `_editor_action()` helper methods

### New EventBus Events

| Event | Publisher | Purpose |
|-------|-----------|---------|
| `editor_modified` | EditorTabs | File modified state changed |
| `tab_created` | EditorTabs | New tab was opened |
| `tab_closed` | EditorTabs | Tab was closed |
| `tab_changed` | EditorTabs | Active tab changed |
| `file_changed_externally` | EditorManager | File changed on disk |
| `file_reloaded` | CenterPanel | File reloaded from disk |
| `editor_save_current_requested` | EditorManager | Save the currently active tab |
| `editor_error` | EditorManager | File I/O error |

---

## [2.0.0-workspace] — 2026-07-06


### Fixed — Core IDE Foundation: Workspace Loading

**Problem**: Selecting "Open Folder" changed the workspace name but did not
fully load the project. The Explorer tree did not populate. The IDE did not
behave like a professional development environment.

**Solution**: Complete reimplementation of the workspace opening workflow.

#### `core/workspace_manager.py` (complete rewrite — v2.0)
- All scanning now runs in a `QThread` background worker (`_ScanWorker`)
- UI thread is **never blocked** during scanning
- Instant UI feedback via `workspace_scanning` event before scan starts
- `_on_scan_done()` publishes `workspace_loaded`, `workspace_metadata_updated`,
  `explorer_populated` events on the main thread (thread-safe via Qt signals)
- Added `_on_scan_failed()` graceful error handling
- `refresh_workspace()` also uses background thread
- `load_session()` restores last workspace on startup
- Inherits from `QObject` to support Qt signal/slot connections

#### `ui/project_panel.py`
- `handle_workspace_loaded()` correctly reads `context.tree` from scanner
- `_build_tree_from_scanner()`: builds root level only, lazy for rest
- `_build_tree_from_filesystem()`: simplified fallback, uses `_load_children_for_item`
- `_load_children_for_item()`: complete rewrite — handles PermissionError,
  FileNotFoundError, OSError; no double-loading; dirs before files; correct parent
- `handle_item_expanded()`: fixed to not double-set `_children_loaded`
- `refresh_workspace()`: now actually rebuilds the tree
- `_setup_file_watcher()`: recursive directory watching (max depth 10)
- `_watch_directory_tree()`: skips .git, node_modules, __pycache__ etc.
- `set_workspace_root()`: logs FileWatcher startup confirmation

#### `ui/main_window.py`
- Added `workspace_scanning` handler: updates title to "Loading…"
- Added `workspace_metadata_updated` handler: updates title, toolbar, status bar
- Added `workspace_error` handler: shows error in status bar
- `_on_workspace_loaded()`: ensures Explorer dock is visible and shown

#### `ui/status_bar.py`
- Added `update_workspace_status()` public method
- Subscribes to `workspace_metadata_updated` event
- Shows project name, file count, folder count, language, framework
- `_on_workspace()` delegates to `update_workspace_status()`

#### `main.py`
- Added `workspace_manager.load_session()` call after window shown
- Last workspace now automatically restored on every startup

### New EventBus Events

| Event | Publisher | Data |
|-------|-----------|------|
| `workspace_scanning` | WorkspaceManager | path, name |
| `workspace_metadata_updated` | WorkspaceManager | project_name, total_files, total_folders, primary_language, framework, scan_duration_ms |
| `explorer_populated` | WorkspaceManager | path, total_files, total_folders |

### Verification

All checks pass:
- ✅ Open Folder works end-to-end
- ✅ Workspace loads (background, no UI freeze)
- ✅ Explorer shows complete folder hierarchy
- ✅ Nested folders expand correctly (lazy-load)
- ✅ FileWatcher starts automatically after load
- ✅ Project metadata visible in window title, toolbar, status bar
- ✅ No UI freezes
- ✅ Python syntax validation: all files compile clean

---

*Previous changelog entries have been archived.*
