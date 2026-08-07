# Sidebar Hide/Unhide Feature Implementation

## Summary
Added convenient hide/unhide functionality for the left sidebar (Explorer/File tree) and fixed shortcut conflicts.

## Changes Made

### 1. Explorer Header - Collapse Button (ui/enhanced_explorer.py)
- **Added collapse button** (‹ / ›) to the Explorer header next to the "+" button
- Button toggles between left chevron (‹) when expanded and right chevron (›) when collapsed
- Tooltip shows "Hide Sidebar (Ctrl+B)" or "Show Sidebar (Ctrl+B)" based on state
- Added `collapse_requested` Signal to PremiumSidebarHeader
- Added `update_collapse_state()` method to update button icon dynamically

### 2. Explorer Widget Updates (ui/enhanced_explorer.py)
- Connected collapse button click to emit `collapse_requested` signal
- Added `collapse_requested` Signal to PremiumExplorer class
- Added `update_collapse_state()` method to sync button state
- Properly forwards collapse request to main window

### 3. Main Window Integration (ui/main_window.py)
- Connected Explorer's `collapse_requested` signal to `_toggle_sidebar()` method
- Updated `_show_sidebar()` to call `explorer.update_collapse_state(False)`
- Updated `_hide_sidebar()` to call `explorer.update_collapse_state(True)`
- Menu bar reference stored for hide/unhide functionality
- Toolbar reference already existed

### 4. Fixed Shortcut Conflicts
**Problem:** `Ctrl+Shift+M` and `Ctrl+Shift+T` were already used by Activity Bar shortcuts

**Solution:**
- Changed Menu Bar toggle to **Alt+M**
- Changed Top Toolbar toggle to **Alt+T**
- Removed shortcuts from menu items to avoid QAction conflicts
- Added proper QShortcut handlers in `setup_shortcuts()`

## How to Use

### Hide/Unhide Left Sidebar (Explorer):
1. **Click the chevron button** in the Explorer header (left-most icon before "+" button)
2. **Press Ctrl+B** keyboard shortcut
3. **Use View menu** → Toggle Explorer

### Hide/Unhide Menu Bar:
1. **Press Alt+M** keyboard shortcut
2. **Use View menu** → Toggle Menu Bar (while menu is still visible)

### Hide/Unhide Top Toolbar:
1. **Press Alt+T** keyboard shortcut
2. **Use View menu** → Toggle Top Toolbar (while menu is still visible)

## Benefits
- ✅ Easy one-click access to hide sidebar after opening project
- ✅ Both keyboard shortcuts AND button clicks work
- ✅ Visual feedback with chevron direction (‹ expanded, › collapsed)
- ✅ No shortcut conflicts
- ✅ Proper state synchronization
- ✅ Event bus integration for logging/tracking

## Keyboard Shortcuts Summary
| Action | Shortcut | Location |
|--------|----------|----------|
| Toggle Explorer | Ctrl+B | View menu / Button / Shortcut |
| Toggle Menu Bar | Alt+M | View menu / Shortcut |
| Toggle Top Toolbar | Alt+T | View menu / Shortcut |
| Toggle Terminal | Ctrl+` | View menu / Shortcut |
| Toggle AI Workspace | Ctrl+\\ | View menu / Shortcut |

## Technical Details
- Collapse button positioned between title and action buttons
- Uses consistent design system styling (hover states, colors, border-radius)
- Maintains sidebar width when toggling
- Updates activity bar state when hiding/showing
- Publishes events to event bus for potential integrations
