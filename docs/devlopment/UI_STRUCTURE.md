# MyCodingMaster UI Structure

## Current Clean Architecture (Post-Cleanup)

```
ui/
├── Main Components (13 files)
│   ├── main_window.py          ★ Main application window (QMainWindow)
│   ├── center_panel.py         ★ Central editor area with tabs
│   ├── top_toolbar.py          ★ Top toolbar with actions
│   ├── status_bar.py           ★ Bottom status bar
│   ├── bottom_dock.py          ★ Bottom panel (Terminal/Problems/Output)
│   ├── enhanced_explorer.py    ★ Explorer sidebar with activity bar
│   ├── dashboard.py            ★ Welcome/recent projects screen
│   ├── command_palette.py      → Command palette (Ctrl+Shift+P)
│   ├── notifications.py        → Toast notifications system
│   ├── diagnostics_panel.py    → Performance/error diagnostics
│   ├── design_system.py        → Design tokens & theming
│   ├── theme.py                → Theme manager
│   └── settings_manager.py     → Settings persistence
│
├── ai_workspace/ (17 files)
│   ├── ai_engineering_workspace_v3.py  ★ Main AI control center
│   ├── ai_chat_panel.py                → Chat interface
│   ├── ai_diagnostics.py               → AI diagnostics
│   ├── connect_provider_dialog.py      → Provider connection UI
│   ├── connected_providers_panel.py    → Active providers display
│   ├── context_section.py              → Context display
│   ├── conversation_section.py         → Conversation UI
│   ├── current_task_section.py         → Active task display
│   ├── embedded_connection_panel.py    → Embedded connection UI
│   ├── execution_plan_section.py       → Execution plan display
│   ├── execution_progress_section.py   → Progress tracking
│   ├── intelligent_error_handler.py    → Error handling UI
│   ├── models_section.py               → Model selection
│   ├── provider_selection_section.py   → Provider picker
│   ├── provider_setup_dialog.py        → Provider setup wizard
│   ├── qwen_coding_panel.py            → Qwen-specific panel
│   ├── runtime_tools_section.py        → Runtime tools display
│   ├── task_queue_section.py           → Task queue UI
│   ├── timeline_section.py             → Timeline visualization
│   └── user_controls_section.py        → User action controls
│
├── editor/ (14 files)
│   ├── code_editor.py          ★ Main code editor widget
│   ├── editor_tabs.py          ★ Tab management for editors
│   ├── breadcrumb_bar.py       → File path breadcrumb
│   ├── bracket_matcher.py      → Bracket matching
│   ├── highlighter.py          → Syntax highlighting
│   ├── indent_guides.py        → Indentation guides
│   ├── language_support.py     → Language-specific features
│   ├── line_number_area.py     → Line numbers display
│   ├── minimap.py              → Code minimap
│   ├── search_replace.py       → Find & replace
│   ├── splitted_editor.py      → Split editor support
│   ├── sticky_tabs.py          → Sticky tab behavior
│   ├── syntax_highlighter.py   → Advanced syntax highlighting
│   └── tab_operations.py       → Tab operations (close, reorder)
│
├── terminal/ (22 files)
│   ├── terminal_panel.py       ★ Main terminal panel
│   ├── terminal_manager.py     ★ Terminal session management
│   ├── terminal_toolbar.py     → Terminal toolbar
│   ├── shell_manager.py        → Shell detection & management
│   ├── process_manager.py      → Process lifecycle
│   ├── session_manager.py      → Session persistence
│   ├── terminal_executor.py    → Command execution
│   ├── profile_manager.py      → Terminal profiles
│   ├── search_manager.py       → Terminal search
│   ├── history_manager.py      → Command history
│   ├── splits_manager.py       → Terminal splitting
│   ├── drag_drop_manager.py    → Drag & drop support
│   ├── breadcrumb.py           → Terminal breadcrumb
│   ├── smart_scrolling.py      → Auto-scroll features
│   ├── bookmarks_manager.py    → Command bookmarks
│   ├── snapshots_manager.py    → Terminal snapshots
│   ├── quick_actions.py        → Quick action buttons
│   ├── indicators.py           → Status indicators
│   ├── clickable_link_manager.py → Link detection
│   ├── notification_manager.py  → Terminal notifications
│   └── terminal_events.py      → Event definitions
│
├── explorer/ (15 files)
│   ├── context_menu.py         → Right-click menu
│   ├── copy_path.py            → Copy path utilities
│   ├── drag_drop.py            → File drag & drop
│   ├── favorites.py            → Favorite files
│   ├── file_filters.py         → File filtering
│   ├── file_icons.py           → File type icons
│   ├── file_info.py            → File metadata
│   ├── file_preview.py         → File preview
│   ├── file_preview_widget.py  → Preview widget
│   ├── git_status.py           → Git status display
│   ├── inline_rename.py        → Inline rename
│   ├── multi_select.py         → Multi-selection
│   ├── open_editors.py         → Open editors list
│   ├── quick_access.py         → Quick access bar
│   ├── search.py               → File search
│   └── workspace_stats.py      → Workspace statistics
│
├── tasks/ (7 files)
│   ├── task_panel.py           ★ Task management panel
│   ├── task_manager.py         → Task lifecycle management
│   ├── task.py                 → Task data model
│   ├── task_events.py          → Task event definitions
│   ├── quick_run_bar.py        → Quick run actions
│   └── project_detector.py     → Project type detection
│
├── processes/ (6 files)
│   ├── process_panel.py        ★ Process management panel
│   ├── process_manager.py      → Process lifecycle
│   ├── process.py              → Process data model
│   ├── process_events.py       → Process event definitions
│   └── debug_console.py        → Debug console UI
│
├── models/ (3 files)
│   ├── models_page.py          ★ Models management page
│   ├── models_section.py       → Models section UI
│   └── marketplace_page.py     → Model marketplace
│
├── chat/ (2 files)
│   ├── chat_panel.py           ★ Chat interface panel
│   └── __init__.py
│
└── components/ (5 files)
    ├── badge.py                → Badge component
    ├── button.py               → Button component
    ├── card.py                 → Card component
    ├── separator.py            → Separator component
    └── __init__.py

★ = Primary/Entry Point Component
→ = Supporting/Utility Component
```

## Component Hierarchy

```
MainWindow (main_window.py)
│
├── MenuBar
├── TopToolbar (top_toolbar.py)
│
├── Central Widget (QSplitter)
│   ├── ActivityBar (enhanced_explorer.py)
│   └── Inner Splitter
│       ├── Explorer Sidebar (enhanced_explorer.py)
│       │   └── File Tree
│       └── Center Panel (center_panel.py)
│           ├── Dashboard (dashboard.py) [when no files open]
│           └── Editor Tabs (editor/editor_tabs.py)
│               └── Code Editors (editor/code_editor.py)
│
├── Right Dock - AI Workspace
│   └── AIEngineeringWorkspaceV3 (ai_workspace/ai_engineering_workspace_v3.py)
│       ├── Models Section
│       ├── Current Task Section
│       ├── Context Section
│       ├── Execution Progress Section
│       └── Conversation Section
│
├── Bottom Dock (bottom_dock.py)
│   ├── Terminal Tabs (terminal output)
│   ├── Problems Tab
│   ├── Output Tab
│   └── Diagnostics Tab
│
├── Status Bar (status_bar.py)
│
└── Overlays
    ├── Command Palette (command_palette.py) [Ctrl+Shift+P]
    └── Notifications (notifications.py) [Toast overlays]
```

## Key Features by Component

### Main Window
- Professional IDE layout with VS Code-style sidebar
- Dockable panels (AI workspace, terminal)
- Keyboard shortcuts (Ctrl+B, Ctrl+`, Ctrl+\\)
- Menu bar with all actions
- Window state persistence

### Enhanced Explorer
- 46px activity bar with 8 activities
- 220px default sidebar width (resizable 180-600px)
- Premium file tree with icons
- Collapsible with smooth animations
- Workspace sections support

### Center Panel
- Multi-tab editor support
- Welcome dashboard when no files open
- Editor state persistence
- Split editor support

### Bottom Dock
- Unified tab bar for terminals + diagnostics
- Multiple terminal tabs
- Problems list (LSP integration)
- Output/log stream
- Diagnostics panel
- Collapsible with Ctrl+`

### AI Workspace (Right Dock)
- Model selection and switching
- Current task tracking
- Context visualization
- Execution progress
- AI conversation interface
- Provider management
- Runtime tools display

### Terminal
- Multiple shell support (cmd, PowerShell, bash, WSL)
- Tab management
- Terminal splitting
- Command history
- Bookmarks & snapshots
- Smart scrolling
- Working directory tracking

### Editor
- Syntax highlighting
- Line numbers & minimap
- Bracket matching
- Find & replace
- Indentation guides
- Language-specific features
- LSP integration

## Removed Components (Old/Duplicates)

These files were deleted during cleanup:
- ❌ `ui/terminal_widget.py` (replaced by terminal/)
- ❌ `ui/breadcrumb_bar.py` (moved to editor/)
- ❌ `ui/left_sidebar.py` (merged into enhanced_explorer.py)
- ❌ `ui/right_panel.py` (replaced by ai_workspace/)
- ❌ `ui/explorer_panel.py` (replaced by enhanced_explorer.py)
- ❌ `ui/memory_panel.py` (not used)
- ❌ `ui/project_panel.py` (not used)
- ❌ `ui/tasks_panel.py` (replaced by tasks/)
- ❌ `ui/test_enhanced_explorer.py` (test file)
- ❌ `ui/ai_workspace/ai_engineering_workspace.py` (replaced by v3)
- ❌ `ui/ai_workspace/ai_workspace_panel.py` (replaced by v3)

## Import Map (Quick Reference)

```python
# Main Window
from ui.main_window import MainWindow

# Core Panels
from ui.center_panel import CenterPanel
from ui.top_toolbar import TopToolbar
from ui.status_bar import BottomStatusBar
from ui.bottom_dock import BottomDock
from ui.enhanced_explorer import PremiumActivityBar, PremiumExplorer

# AI Workspace
from ui.ai_workspace.ai_engineering_workspace_v3 import AIEngineeringWorkspaceV3

# Editor
from ui.editor.code_editor import CodeEditor
from ui.editor.editor_tabs import EditorTabs

# Terminal
from ui.terminal.terminal_panel import TerminalTabBar
from ui.terminal.terminal_manager import TerminalManager

# Design System
from ui.design_system import get_design_system
from ui.theme import ThemeManager

# Utilities
from ui.command_palette import CommandPalette
from ui.notifications import create_notification_manager
```

---
**Last Updated:** 2026-07-11  
**Status:** Clean & Consolidated ✅
