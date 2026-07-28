# MyCodingMaster v1.1 — UI Polish Implementation Tasks

## Phase 1: Theme & Color System

### Task 1.1: Centralize Colors
- [ ] Create `ui/colors.py` with centralized color tokens
- [ ] Implement `DARK`, `LIGHT`, `SYSTEM` color palettes
- [ ] Add color utility functions (contrast, opacity, hover)
- [ ] Document color usage guidelines

### Task 1.2: Theme Manager
- [ ] Update `ui/theme.py` with system theme detection
- [ ] Implement `ThemeManager.set_theme()` method
- [ ] Add theme switching UI (view menu, status bar button)
- [ ] Test theme transitions (no flicker)

### Task 1.3: Color Verification
- [ ] Verify all colors pass WCAG AA contrast (4.5:1 for text)
- [ ] Test on multiple monitors (different DPI)
- [ ] Verify color accessibility (colorblind-friendly)
- [ ] Document color usage guidelines

---

## Phase 2: Explorer Improvements

### Task 2.1: File Type Icons
- [ ] Create icon registry (20+ file types)
- [ ] Implement `get_file_icon()` function
- [ ] Update `project_panel.py` to use icons
- [ ] Add fallback icons for unknown types

### Task 2.2: Context Menu
- [ ] Implement `show_context_menu()` in `project_panel.py`
- [ ] Add all menu items (New File, New Folder, Rename, etc.)
- [ ] Implement all menu actions
- [ ] Test context menu on different items

### Task 2.3: Drag and Drop
- [ ] Enable drag and drop on QTreeWidget
- [ ] Implement visual feedback during drag
- [ ] Handle drop events (move, copy, reorder)
- [ ] Test drag and drop between folders

### Task 2.4: Lazy Loading
- [ ] Implement lazy loading for children
- [ ] Add loading indicator for large directories
- [ ] Optimize for 1000+ files
- [ ] Test with large projects

### Task 2.5: Filter/Search
- [ ] Add filter box at top of explorer
- [ ] Implement live filtering
- [ ] Add "Find in Folder" functionality
- [ ] Test with various file names

---

## Phase 3: Editor Polish

### Task 3.1: Tab Improvements
- [ ] Implement pinned tabs (not movable)
- [ ] Add hover tooltip (full path)
- [ ] Improve tab width calculation
- [ ] Test tab reordering

### Task 3.2: Mini Map
- [ ] Implement mini map widget
- [ ] Add toggle button in breadcrumbs
- [ ] Implement scroll sync
- [ ] Test with various file sizes

### Task 3.3: Split Editor
- [ ] Add split editor toggle
- [ ] Implement split view layout
- [ ] Add close split button
- [ ] Test split/unsplits

### Task 3.4: Session Restore
- [ ] Update `editor_manager.py` to save session
- [ ] Load session on startup
- [ ] Handle missing files gracefully
- [ ] Test session restore

### Task 3.5: Find/Replace UI
- [ ] Improve find/replace widget styling
- [ ] Add "Replace in Files" functionality
- [ ] Implement case sensitivity toggle
- [ ] Test regex search

---

## Phase 4: AI Workspace Redesign

### Task 4.1: Simplify Layout
- [ ] Move essential sections to top
- [ ] Create collapsible "Advanced" section
- [ ] Implement section toggling
- [ ] Test section visibility

### Task 4.2: Token Budget Bar
- [ ] Update `context_section.py` with color coding
- [ ] Add 60%/85% thresholds
- [ ] Implement gradient bar
- [ ] Test with various token counts

### Task 4.3: Conversation Improvements
- [ ] Update message bubbles
- [ ] Add copy button for AI messages
- [ ] Implement message timestamps
- [ ] Test message formatting

### Task 4.4: Progress Indicators
- [ ] Add visual progress to current task
- [ ] Implement step progress bar
- [ ] Add task timing display
- [ ] Test progress updates

### Task 4.5: Statistics Section
- [ ] Create statistics section in advanced
- [ ] Show token usage, file counts, dependencies
- [ ] Add project statistics
- [ ] Update with real data

---

## Phase 5: Toolbar Rebuild

### Task 5.1: Group Implementation
- [ ] Create grouped toolbar layout
- [ ] Implement group separators
- [ ] Add logical grouping (Workspace, Project, etc.)
- [ ] Test group spacing

### Task 5.2: Disabled Button Tooltips
- [ ] Add tooltips for disabled buttons
- [ ] Implement "Coming Soon" pattern
- [ ] Update all disabled buttons
- [ ] Test tooltip visibility

### Task 5.3: Button Styling
- [ ] Standardize button sizes (24x24 for icons, 80px for text)
- [ ] Implement consistent hover effects
- [ ] Add active/pressed states
- [ ] Test button states

### Task 5.4: Keyboard Shortcuts
- [ ] Add shortcuts to all tooltips
- [ ] Implement shortcut registry
- [ ] Test all shortcuts
- [ ] Document keyboard shortcuts

### Task 5.5: Placeholder Buttons
- [ ] Implement placeholder buttons for future features
- [ ] Add "Coming Soon" tooltips
- [ ] Test disabled states
- [ ] Update documentation

---

## Phase 6: Bottom Panel

### Task 6.1: All Tabs
- [ ] Implement Terminal tab (PTY in v0.5)
- [ ] Implement Problems tab (errors/warnings)
- [ ] Implement Output tab (logs)
- [ ] Implement Debug tab
- [ ] Implement Git tab
- [ ] Implement Logs tab
- [ ] Implement Tasks tab

### Task 6.2: Resize Handles
- [ ] Add resize handle to header
- [ ] Implement vertical resize
- [ ] Add minimum height constraint
- [ ] Test resize behavior

### Task 6.3: Maximize Toggle
- [ ] Add maximize button
- [ ] Implement toggle behavior
- [ ] Save/restore maximize state
- [ ] Test maximize/unmaximize

### Task 6.4: Tab Icons
- [ ] Create 16x16px tab icons
- [ ] Add hover effect
- [ ] Implement active indicator
- [ ] Test icon visibility

### Task 6.5: Tab Hover
- [ ] Add hover tooltip (full name)
- [ ] Implement tab switching with hover
- [ ] Test tooltip visibility
- [ ] Test tab switching

---

## Phase 7: Status Bar

### Task 7.1: Live Updates
- [ ] Update memory/CPU display
- [ ] Add background task indicators
- [ ] Implement progress bars
- [ ] Test live updates

### Task 7.2: AI Status
- [ ] Improve AI status display
- [ ] Add state indicators (idle/thinking/error)
- [ ] Implement error details
- [ ] Test status updates

### Task 7.3: Click-to-Action
- [ ] Make workspace clickable (show full path)
- [ ] Make cursor clickable (go to line)
- [ ] Make language clickable (switch manually)
- [ ] Test all click actions

### Task 7.4: Progress Indicators
- [ ] Add progress bar for long operations
- [ ] Implement cancel button
- [ ] Show progress percentage
- [ ] Test progress updates

### Task 7.5: Background Tasks
- [ ] Implement background task registry
- [ ] Add progress for each task
- [ ] Implement task queue
- [ ] Test task management

---

## Phase 8: Dashboard

### Task 8.1: Recent Projects
- [ ] Improve recent projects display
- [ ] Add folder icons
- [ ] Implement hover tooltips
- [ ] Test project opening

### Task 8.2: Pinned Projects
- [ ] Add pin/unpin functionality
- [ ] Show pinned projects first
- [ ] Save pinned list
- [ ] Test pin/unpin

### Task 8.3: Quick Actions
- [ ] Implement new file button
- [ ] Implement open folder button
- [ ] Implement scan workspace button
- [ ] Test all actions

### Task 8.4: Project Statistics
- [ ] Show file count
- [ ] Show folder count
- [ ] Show line count
- [ ] Update on workspace load

### Task 8.5: Activity Timeline
- [ ] Implement activity items
- [ ] Show timestamp
- [ ] Add icons
- [ ] Test timeline updates

---

## Phase 9: UX Polish

### Task 9.1: Hover Effects
- [ ] Add hover to all interactive elements
- [ ] Implement consistent hover styles
- [ ] Test hover states
- [ ] Verify accessibility

### Task 9.2: Loading States
- [ ] Implement loading indicator
- [ ] Add skeleton screens
- [ ] Implement progress bars
- [ ] Test loading states

### Task 9.3: Success/Error Notifications
- [ ] Update notification system
- [ ] Add success icon
- [ ] Add error details
- [ ] Test notifications

### Task 9.4: Button Validation
- [ ] Verify all buttons work or explain why disabled
- [ ] Fix all disabled buttons
- [ ] Update documentation
- [ ] Test all buttons

### Task 9.5: Keyboard Accessibility
- [ ] Test all functionality with keyboard
- [ ] Add keyboard shortcuts
- [ ] Document keyboard shortcuts
- [ ] Test tab navigation

---

## Phase 10: Performance

### Task 10.1: Background Threads
- [ ] Move heavy operations to background
- [ ] Implement progress events
- [ ] Test with large projects
- [ ] Verify no UI freezes

### Task 10.2: Lazy Loading
- [ ] Implement lazy loading for explorer
- [ ] Add loading indicators
- [ ] Optimize for 1000+ files
- [ ] Test with large projects

### Task 10.3: Layout Optimization
- [ ] Minimize re-layouts
- [ ] Batch updates
- [ ] Use QScrollArea appropriately
- [ ] Test with complex layouts

### Task 10.4: Skeleton Screens
- [ ] Implement skeleton for lists
- [ ] Implement skeleton for cards
- [ ] Implement skeleton for tables
- [ ] Test skeleton display

### Task 10.5: Debouncing
- [ ] Debounce rapid events
- [ ] Use QTimer for debouncing
- [ ] Test with rapid inputs
- [ ] Verify smooth behavior

---

## Testing

### Unit Tests:
- [ ] Theme color retrieval
- [ ] Icon selection by extension
- [ ] Context menu item visibility
- [ ] Tab close behavior
- [ ] Mini map sync
- [ ] Status bar updates

### Integration Tests:
- [ ] Explorer context menu commands
- [ ] Editor tab switching
- [ ] AI workspace section visibility
- [ ] Toolbar button states
- [ ] Bottom panel tab switching
- [ ] Dashboard recent projects

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

---

## Notes

- All improvements must pass accessibility checks
- All text must be localizable (use `QApplication.translate`)
- All icons must have fallbacks
- All colors must pass contrast checks (WCAG AA minimum)
- All animations must be opt-in (accessibility setting)
- All feedback must be keyboard accessible