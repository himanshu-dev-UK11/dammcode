# How Sidebar Toggle Works (Phase 1)

## Visual Guide

### Scenario 1: First Click on Explorer
```
User clicks 📁
     ↓
Activity bar shows "📁 is selected"
     ↓
Explorer panel appears
     ↓
┌──────┬─────────┬──────────────┐
│ 📁✓  │         │              │
│ 🔍   │ Explorer│   Editor     │
│ 🔀   │ Files   │              │
└──────┴─────────┴──────────────┘
```

### Scenario 2: Second Click on Explorer (Toggle Off)
```
User clicks 📁 again
     ↓
Detects: "Already selected!"
     ↓
Deselects button + hides sidebar
     ↓
┌──────────────────────────────────┐
│                                  │
│         Editor (Full Width!)     │
│                                  │
└──────────────────────────────────┘
```

### Scenario 3: Click Different Activity
```
Sidebar hidden, user clicks 🔍
     ↓
Shows sidebar with Search
     ↓
┌──────┬─────────┬──────────────┐
│ 📁   │         │              │
│ 🔍✓  │ Search  │   Editor     │
│ 🔀   │ Panel   │              │
└──────┴─────────┴──────────────┘
```

### Scenario 4: Keyboard Shortcut (Ctrl+B)
```
User presses Ctrl+B
     ↓
If visible → Hide completely
If hidden  → Show with last activity
```

---

## Code Flow

### Double-Click Detection
```python
# In PremiumActivityBar._on_button_clicked()

if activity_id == self._active_activity and button.isChecked():
    # User clicked the SAME button again!
    button.setChecked(False)
    self.collapse_requested.emit()  # → MainWindow._toggle_sidebar()
else:
    # Normal selection
    self.activity_selected.emit(activity_id)  # → MainWindow._on_activity_selected()
```

### Hide Sidebar (Space Reclamation)
```python
# In MainWindow._hide_sidebar()

self._activity_bar.setVisible(False)  # ← Activity bar disappears!
self._explorer.setVisible(False)       # ← Explorer disappears!
self._sidebar_collapsed = True

# Result: Full width available for editor
```

### Show Sidebar
```python
# In MainWindow._show_sidebar()

self._activity_bar.setVisible(True)   # ← Activity bar appears
self._explorer.setVisible(True)       # ← Explorer appears
self._sidebar_collapsed = False

# Result: Sidebar visible, editor resizes
```

---

## User Actions & Results

| Action | Sidebar State Before | Result | Sidebar State After |
|--------|---------------------|--------|---------------------|
| Click 📁 | Hidden | Show with Explorer | Visible (📁) |
| Click 📁 | Visible (📁) | Hide completely | Hidden |
| Click 🔍 | Hidden | Show with Search | Visible (🔍) |
| Click 🔍 | Visible (🔍) | Hide completely | Hidden |
| Click 🔍 | Visible (📁) | Switch to Search | Visible (🔍) |
| Ctrl+B | Visible | Hide completely | Hidden |
| Ctrl+B | Hidden | Show last activity | Visible |
| Ctrl+Shift+E | Hidden | Show Explorer | Visible (📁) |
| Ctrl+Shift+F | Hidden | Show Search | Visible (🔍) |

---

## Space Usage

### Hidden State
```
Window Width: 1920px
├─ Activity Bar: 0px     (hidden!)
├─ Explorer: 0px         (hidden!)
└─ Editor: 1920px        (full width!)
```

### Visible State
```
Window Width: 1920px
├─ Activity Bar: 46px    (visible)
├─ Explorer: 220px       (visible)
└─ Editor: 1654px        (remaining)
```

---

## Benefits

✅ **Space Efficiency:** Editor uses full width when sidebar hidden
✅ **Intuitive:** Click same button to toggle (like VS Code)
✅ **Consistent:** Works same for all activities
✅ **Keyboard Friendly:** Ctrl+B still works
✅ **Visual Feedback:** Button highlights show state

---

## Testing It

1. **Launch:** `python main.py`
2. **Click 📁:** Sidebar appears
3. **Click 📁 again:** Sidebar disappears, editor expands
4. **Notice:** Activity bar is completely gone, not just hidden
5. **Click 🔍:** Sidebar reappears with Search
6. **Press Ctrl+B:** Sidebar disappears
7. **Press Ctrl+B:** Sidebar reappears

**Expected:** Smooth toggle, space reclaimed, no errors!

---

✅ Phase 1 Complete — Working as designed!
