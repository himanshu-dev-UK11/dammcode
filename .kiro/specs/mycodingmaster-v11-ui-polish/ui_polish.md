# MyCodingMaster v1.1 — UI Polish & Professional UX

## Version 1.1 — Professional UI & UX Polish

Current Version: v1.0 (Bugfix Sprint Complete)
Target Version: v1.1 (UI Polish Sprint)

**This sprint is NOT for bug fixing.**
**This sprint is NOT for backend work.**
**This sprint is ONLY for making the application look and feel like premium desktop software.**

---

## 🎯 Goals

1. **Professional** — Looks like commercial IDEs, not a prototype
2. **Minimal** — Clean, uncluttered interface with intentional whitespace
3. **Fast** — Instant visual feedback, no loading states for normal operations
4. **Modern** — Current design trends, no dated visual elements
5. **Engineering-focused** — Serves developers' needs first
6. **Original** — Unique design language, not VS Code/Cursor/Windsurf/Zed clones

**DO NOT imitate VS Code, Cursor, Windsurf or Zed. Use them only as usability references.**

---

## 🎨 Design Principles

### Spacing & Layout
- Consistent 8px baseline grid
- Generous padding on interactive elements (min 12px)
- Logical grouping with visual separators
- Intentional whitespace to reduce cognitive load

### Typography
- Primary: Inter, Segoe UI, SF Pro Display (system fallback)
- Code: JetBrains Mono, Cascadia Code, Consolas (system fallback)
- UI text: 12px normal weight
- Labels: 10px uppercase with 0.8px letter spacing
- Code: 11px in dock, 12px in editor

### Colors (Professional Palette)

**Dark Theme** (default):
- Surface 0: `#0D0D0F` — Window background
- Surface 1: `#111113` — Sidebar/background panels
- Surface 2: `#161618` — Editor background
- Surface 3: `#1C1C1F` — Toolbars, tabs, status bar
- Surface 4: `#222226` — Hover states, input backgrounds
- Border: `#252528` — Structural borders
- Border Hi: `#303036` — High contrast borders
- Accent: `#3B82F6` — Blue-600 for focus, selection, active
- Text Primary: `#E2E2E6` — Main text
- Text Secondary: `#8E8E98` — Labels, secondary info
- Text Muted: `#52525C` — Placeholders, disabled text
- Success: `#22C55E`
- Warning: `#F59E0B`
- Error: `#EF4444`
- Info: `#60A5FA`

**Light Theme**:
- Surface 0: `#F5F5F7` — Window background
- Surface 1: `#FFFFFF` — Sidebar/background panels
- Surface 2: `#FAFAFA` — Editor background
- Surface 3: `#EBEBEF` — Toolbars, tabs, status bar
- Surface 4: `#E0E0E5` — Hover states, input backgrounds
- Border: `#D4D4DA` — Structural borders
- Accent: `#2563EB` — Blue-600
- Text Primary: `#111113`
- Text Secondary: `#52525C`
- Text Muted: `#8E8E98`

### Icons
- Consistent line weight (2px)
- Uniform 16x16px size for toolbar/status icons
- Uniform 24x24px for panel icons
- Nerd Fonts for specialized icons (file types, version control)
- Unicode fallbacks for environments without icon fonts
- Consistent stroke width across all icons
- Hover: 20% lighter
- Active: Accent color (`#3B82F6` dark, `#2563EB` light)

### Interactions
- Hover: Background change, slight scale (1.05x for buttons)
- Active/Pressed: Background darken, no scale
- Focus: Accent border, no outline (prevent outline in CSS)
- Selection: Accent background, text primary color
- Loading: Skeleton screens, not spinners (spinners only for >2s operations)
- Transitions: 200ms cubic-bezier(0.4, 0, 0.2, 1) for smooth but fast
- Animations: Subtle, purposeful, never distracting

### Empty States
- Illustrative placeholder (simple line art or icon)
- Helpful text explaining what's missing
- Actionable button or prompt
- No "404" or error colors
- Friendly, not discouraging

### Feedback & Notifications
- Toast-style popups (bottom-right)
- Auto-hide with 5-second timer
- Queue multiple notifications
- Icons: Success (✓), Warning (△), Error (✕), Info (ℹ)
- Click to view details
- Clear all button

---

## 📋 Requirements by Component

### 1. Workspace Explorer

**Current State**: Basic QTreeWidget with placeholder icons
**Target**: Professional file explorer with rich interactions

#### Requirements:
- **Recursive folder loading** — Lazy load children on expand
- **Expand/Collapse** — Single click on arrow or double-click on folder
- **Folder icons** — Distinct icon for folders, different for open/closed
- **File icons** — Extension-based icons (Python, JS, JSON, Markdown, etc.)
- **Refresh** — Manual refresh button or F5 shortcut
- **Auto refresh on changes** — Watch file system events
- **Drag and drop** — Reorder files, move between folders (visual feedback)
- **Indentation** — Consistent 16px per level
- **Selection** — Clear visual selection state
- **Context menu** — Professional right-click menu

#### Context Menu Options:
- **New File** — Create new file in current folder
- **New Folder** — Create new subfolder
- **Rename** — Rename file/folder (F2 shortcut)
- **Duplicate** — Copy with "_copy" suffix
- **Delete** — Move to trash or permanent delete
- **Reveal** — Open folder in system file explorer
- **Copy Path** — Copy absolute path to clipboard
- **Open Externally** — Open with default system application
- **Refresh** — Refresh current folder
- **Collapse All** — Collapse all nodes
- **Expand All** — Expand all nodes

#### Icons to Implement:
```
Folder (closed):  📁  (or 📂)
Folder (open):    📂  (or 📁 with open indicator)
File (code):      󰌠  or  󰌓
File (text):      󰈚
File (image):     󰉏
File (video):     󰄀
File (audio):     󰅐
File (archive):   󰁦
File (config):    󰒓
File (document):  󰈦
```

### 2. Editor

**Current State**: Basic QTabWidget with code editor
**Target**: Professional code editor with all modern features

#### Requirements:
- **Multiple Tabs** — QTabWidget with close buttons
- **Tab Close** — Click X button or Ctrl+W
- **Tab Reorder** — Drag and drop tabs
- **Tab Pin** — Pinned tabs stay in position (not movable)
- **Unsaved \*** — Asterisk on tab for unsaved changes
- **Syntax Highlighting** — Already implemented in `syntax_highlighter.py`
- **Breadcrumbs** — Already implemented in `breadcrumb_bar.py`
- **Current Line Highlight** — Already in `CodeEditor`
- **Line Numbers** — Already in `CodeEditor`
- **Mini Map** — Toggleable (sidebar preview of file)
- **Word Wrap** — Toggle (Alt+Z or view menu)
- **Go To Line** — Ctrl+G (dialog or inline)
- **Find** — Ctrl+F (already in `search_replace.py`)
- **Replace** — Ctrl+H (already in `search_replace.py`)
- **Session Restore** — Open previous files on startup
- **Recent Files** — Quick switch from menu or sidebar

#### Editor Tab Improvements:
- Pinned tabs shown first, not movable
- Hover: Full path tooltip
- Active tab: Accent top border (2px `#3B82F6`)
- Unsaved: ` *` after filename
- Close button: Show on hover or always visible (style choice)
- Tab width: Flexible, min 80px, max 200px (ellipsis for long names)

#### Mini Map:
- Toggle: Ctrl+Shift+M or breadcrumbs icon
- Shows file preview (reduced scale)
- Shows cursor position as highlight
- Scroll sync with main editor
- Hide when editor is small (< 600px width)

#### Split Editor:
- Split: Horizontal or vertical
- Close split: X button or Ctrl+W on inactive split
- Sync scroll when enabled
- Independent cursor positions

### 3. AI Workspace

**Current State**: Crowded 11-section panel
**Target**: Clean, professional layout with essential info always visible

#### Requirements:
**Essential (always visible)**:
- Current Task
- Progress
- Conversation
- Prompt Input
- Current Context

**Advanced (collapsible)**:
- Execution Plan
- Verification
- Running Tools
- Memory
- Models
- Logs
- Statistics

#### Layout:
```
━━━━━━━━━━━━━━��━━━━━━━━━━━━━━━━━━━━━━━━
Current Task        [status badge]
Progress            [bar]
Conversation        [messages]
Prompt Input        [input field + send]
Current Context     [token usage, files]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Advanced ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[All collapsible sections hidden]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Advanced Panel Contents:
```
Advanced ▼
├── Execution Plan
├── Verification
├── Running Tools
├── Memory
├── Models
├── Logs
└── Statistics
```

#### Context Section Improvements:
- Token budget bar: 100% max, color changes (green < 60%, yellow 60-85%, red > 85%)
- Selected files: List with icons, reasons (current, dependency, keyword)
- Token estimate: Exact or approximate
- Cache status: HIT/MISS badge

### 4. Explorer Panel

**Current State**: Basic QTreeWidget with context menu (limited)
**Target**: Professional file explorer with full feature set

#### Improvements:
- **Icons** — Extension-based icons (code, text, config, docs, media)
- **Indentation** — 16px per level, consistent alignment
- **Selection** — Clear visual selection (accent background)
- **Context Menu** — Full professional menu (see section 1)
- **Drag and Drop** — Visual feedback during drag
- **Loading** — Skeleton or spinner for large directories
- **Filter** — Quick filter box at top
- **Search** — Find in folder

#### Context Menu Implementation:
```python
# Right-click on tree item
- New File (F4)
- New Folder
- Rename (F2)
- Duplicate
- Delete
- —
- Reveal in Explorer
- Copy Path
- Open Externally
- —
- Refresh
- —
- Collapse All
- Expand All
```

### 5. Toolbar

**Current State**: 30px compact toolbar with basic groups
**Target**: Professional toolbar with logical groups and consistent spacing

#### Groups:
```
Workspace         [Open] [Save] [Save All] [Close]
────────────────────────────────────────────────────────
Project           [Scan] [Analyze] [Search]
────────────────────────────────────────────────────────
Execution         [▶ Run] [■ Stop] [▶ Debug] [▶ Test]
────────────────────────────────────────────────────────
AI                [New Chat] [Analyze] [Explain] [Refactor]
────────────────────────────────────────────────────────
View              [Theme] [Layout] [Panels] [Zoom]
────────────────────────────────────────────────────────
Settings          [⚙]
```

#### Button Improvements:
- Consistent size: 24x24px for icon-only, 80px for text buttons
- Consistent spacing: 8px between buttons, 16px between groups
- Icon-only buttons: 16x16px icons, centered
- Text buttons: Icon + text, 6px spacing
- Disabled buttons: Show tooltip explaining why
- Hover: 10% brighter background
- Active: 15% darker

#### Groups Implementation:
- Group separators: 1px border (`#252528` dark, `#D4D4DA` light)
- Group spacing: 16px vertical
- Icons: Nerd Fonts or unicode fallbacks
- Tooltips: Always show on hover

### 6. Dashboard

**Current State**: Basic welcome screen
**Target**: Professional home dashboard

#### Requirements:
**Display**:
- Recent Projects
- Pinned Projects
- Recent Files
- Recent Conversations
- Project Statistics
- Quick Actions
- Recent Activity

#### Layout:
```
MyCodingMaster
AI-Assisted Software Engineering

Recent Projects
────────────────────────────────────────────────────────
[Project List]

Quick Actions
────────────────────────────────────────────────────────
[New File] [Open Folder] [Scan Workspace]

Recent Files
────────────────────────────────────────────────────────
[File List]

System Status
────────────────────────────────────────────────────────
CPU: 0%  │  RAM: 0MB  │  AI: Idle

Recent Activity
────────────────────────────────────────────────────────
[Timeline]
```

#### Recent Projects:
- Show last 10 projects
- Click to open
- Hover shows full path
- Star to pin (keep at top)
- Show folder icon

#### Recent Files:
- Show last 20 files
- Click to open
- Hover shows full path
- Show file type icon

### 7. Bottom Panel

**Current State**: Terminal stub, Problems, Output
**Target**: Full-featured dock with all panels

#### Tabs:
- **Terminal** — Stub now, full PTY in v0.5
- **Problems** — Errors and warnings
- **Output** — Log stream
- **Debug** — Debug information
- **Git** — Git status and history
- **Logs** — Application logs
- **Tasks** — Task progress

#### Requirements:
- **Resizable** — Drag top/bottom edge
- **Hide** — Collapse to header-only
- **Maximize** — Toggle full height
- **Tabs** — Switch between panels
- **Tab icons** — Consistent 16x16px icons
- **Tab hover** — Full name tooltip

#### Tab Icons:
```
Terminal:  󰄠  or  
Problems:  󰅚  or  ⚠
Output:    󰄉  or  
Debug:     󰄄  or  🐞
Git:       󰊢  or  ⚖
Logs:      󰅐  or  📝
Tasks:     󰓼  or  ✓
```

### 8. Status Bar

**Current State**: Basic status line
**Target**: Professional status bar with live data

#### Display:
```
[AI Status] [Workspace] [Branch]  │  [Ln:Col] [Lang] [Indent] [Version]
```

#### AI Status:
- Idle: `○ AI: Idle`
- Thinking: `● AI: Thinking`
- Error: `✕ AI: Error`
- Color: Success (`#22C55E`), Info (`#3B82F6`), Error (`#EF4444`)

#### Workspace:
- Show folder name (truncate long paths)
- Click to show full path tooltip
- Show git branch if in repo

#### Language:
- Detect from file extension
- Show full name (not just extension)
- Click to switch language manually

#### Encoding:
- UTF-8 (default)
- Show if different

#### Cursor:
- Line:Column format
- Click to go to line

#### Memory/CPU:
- Background tasks indicator
- Live update every 2 seconds

#### Background Tasks:
- Progress bars for long operations
- Click to show details
- Auto-hide when complete

### 9. UX — No Dead Buttons

**Requirement**: Every button must:
- Work, OR
- Show placeholder, OR
- Explain why disabled

#### Implementation:
- **Disabled state**: Show tooltip on hover
- **Placeholder**: Show "Coming Soon" tooltip
- **Loading**: Show spinner or progress
- **Error**: Show error icon and message

#### Button States:
- **Enabled**: Normal color, hover effect
- **Disabled**: Muted color (`#52525C`), no hover, tooltip explains
- **Loading**: Spinner or progress bar, disabled
- **Success**: Green checkmark, auto-hide after 2s
- **Error**: Red X, tooltip with error message

#### Placeholder Pattern:
```python
def _btn_disabled(self, text: str, reason: str) -> QToolButton:
    btn = QToolButton()
    btn.setText(text)
    btn.setEnabled(False)
    btn.setToolTip(f"{reason} — Coming Soon")
    return btn
```

### 10. Performance

**Requirement**: Never freeze UI

#### Background Threads:
- Heavy operations: Always in background
- UI updates: Always on main thread (QMetaObject.invokeMethod)
- Progress: Emit events every 100ms

#### Progress Indicators:
- **Loading spinners**: Only for >2s operations
- **Skeleton screens**: For lists, cards, tables
- **Progress bars**: For long operations (build, scan, analyze)
- **Toast notifications**: For completed operations

#### Lazy Loading:
- Explorer: Load children on expand
- Syntax highlighting: On first view
- Symbol indexing: Background, update on change

#### Optimizations:
- Avoid re-layout on every change
- Batch updates with QTimer.singleShot(0, ...)
- Use QScrollArea for large content
- Limit visible items in lists (virtual scrolling)

---

## 🎯 Implementation Tasks

### Phase 1: Theme & Color System

- [ ] Centralize all colors in `ui/colors.py`
- [ ] Create theme manager with system theme detection
- [ ] Implement dark/light/system theme modes
- [ ] Add theme switching UI
- [ ] Document color usage guidelines

### Phase 2: Explorer Improvements

- [ ] Add file type icons (code, text, config, docs, media)
- [ ] Implement context menu (New File, New Folder, Rename, etc.)
- [ ] Add drag and drop support with visual feedback
- [ ] Implement lazy loading for large directories
- [ ] Add filter/search functionality

### Phase 3: Editor Polish

- [ ] Improve tab styling and behavior
- [ ] Add mini map toggle
- [ ] Implement split editor placeholders
- [ ] Add session restore on startup
- [ ] Improve find/replace UI

### Phase 4: AI Workspace Redesign

- [ ] Simplify layout (essential always visible)
- [ ] Move advanced options to collapsible section
- [ ] Improve token budget bar
- [ ] Add conversation message bubbles
- [ ] Improve progress indicators

### Phase 5: Toolbar Rebuild

- [ ] Reorganize into logical groups
- [ ] Add disabled button tooltips
- [ ] Implement placeholder buttons for future features
- [ ] Improve button styling consistency
- [ ] Add keyboard shortcuts to tooltips

### Phase 6: Bottom Panel

- [ ] Implement all tabs (Terminal, Problems, Output, Debug, Git, Logs, Tasks)
- [ ] Add resize handles
- [ ] Implement maximize toggle
- [ ] Add tab icons
- [ ] Add hover tooltips

### Phase 7: Status Bar

- [ ] Add live updates for memory/CPU
- [ ] Add background task indicators
- [ ] Improve AI status display
- [ ] Add click-to-action (go to line, show full path)
- [ ] Implement progress indicators

### Phase 8: Dashboard

- [ ] Improve recent projects display
- [ ] Add pinned projects section
- [ ] Show project statistics
- [ ] Add quick actions
- [ ] Implement activity timeline

### Phase 9: UX Polish

- [ ] Add hover effects to all interactive elements
- [ ] Implement loading states for operations >500ms
- [ ] Add success/error notifications
- [ ] Ensure all buttons have purpose
- [ ] Test and fix all disabled buttons

### Phase 10: Performance

- [ ] Add background thread for heavy operations
- [ ] Implement skeleton screens for lists
- [ ] Add lazy loading for explorer
- [ ] Optimize layout reflows
- [ ] Add progress indicators for long operations

---

## 🚫 What NOT to Do

1. **Do NOT add new backend systems** — This is purely UI polish
2. **Do NOT redesign architecture** — Keep existing structure
3. **Do NOT add AI features** — Focus on visual and interaction polish
4. **Do NOT imitate existing IDEs** — Create unique design language
5. **Do NOT use gradients** — Flat design only
6. **Do NOT use border-radius > 3px** — Keep it minimal
7. **Do NOT add spinners for <2s operations** — Use skeleton or nothing

---

## 📦 Delivery

### Files to Update:
- `ui/colors.py` — New centralized color system
- `ui/theme.py` — Theme manager with system detection
- `ui/explorer_panel.py` — Context menu, icons, drag/drop
- `ui/project_panel.py` — Explorer improvements
- `ui/editor/editor_tabs.py` — Tab polish, session restore
- `ui/breadcrumb_bar.py` — Mini map toggle, split editor
- `ui/ai_workspace/` — Redesign layout
- `ui/top_toolbar.py` — Reorganize groups
- `ui/bottom_dock.py` — Add all tabs
- `ui/status_bar.py` — Live updates, progress
- `ui/dashboard.py` — Improve display

### Files to Keep:
- `ui/center_panel.py` — Keep existing structure
- `ui/left_sidebar.py` — Keep existing structure
- `ui/main_window.py` — Keep existing structure

### Git vs GitHub:
- Git: Always available locally, used for snapshots, rollback, and history
- GitHub: Optional integration, disabled by default, manual enable required

---

## 📝 Notes

- All improvements must pass accessibility checks
- All text must be localizable (use `QApplication.translate`)
- All icons must have fallbacks
- All colors must pass contrast checks (WCAG AA minimum)
- All animations must be opt-in (accessibility setting)
- All feedback must be keyboard accessible
