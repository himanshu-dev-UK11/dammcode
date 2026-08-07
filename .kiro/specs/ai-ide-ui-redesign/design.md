# Design Document — AI IDE UI Redesign

## Overview

This document describes the architecture and implementation plan for the premium UI redesign of MyCodingMaster IDE. The redesign is strictly visual: no functional logic, signals, slots, or event-bus pathways change. All visual tokens are centralised in `ui/design_system.py`; the global QSS stylesheet is generated and applied through `ui/theme.py`. Every inline hardcoded hex colour in individual widget files is replaced with a live reference to `DesignSystem.palette`.

Design language: Material 3 · Fluent · Linear · Arc Browser — dark-first, rounded corners (8–12 px), thin 1 px separators, soft shadows, premium typography, maximum editor space.

---

## Components and Interfaces

See detailed component breakdowns in the sections below. Each affected widget is treated as a self-contained component whose visual interface (QSS, dimensions) changes while its programmatic interface (methods, signals, slots) stays frozen.

---

## Architecture

### Token-First Styling Pipeline

```
DesignSystem (design_system.py)
  ├─ Radius         — border-radius tokens
  ├─ Shadow         — elevation shadow strings
  ├─ Spacing        — layout spacing scale
  ├─ FontSize/Weight — typography scale
  └─ ColorPalette   — per-theme semantic colour tokens
          │
          ▼
ThemeManager (theme.py)
  └─ apply_theme(name) → regenerates full QSS → app.setStyleSheet()
          │
          ▼
  Each widget reads ds.palette.<token> for any
  per-widget inline style (activity bar, sidebar header, etc.)
```

All five themes (dark, light, one_dark, github_dark, nord) flow through the same pipeline. Changing the theme at runtime calls `apply_theme`, which replaces the global stylesheet and triggers a repaint on all top-level widgets. Widgets that set per-widget stylesheets inline must re-read `DesignSystem.palette` after a theme change.

### Affected Files

| File | Change |
|---|---|
| `ui/design_system.py` | Upgrade Radius, Shadow, Spacing token values; add `ROUND=20` to Radius |
| `ui/theme.py` | Expand `_generate_stylesheet` with premium QSS rules for all surfaces |
| `ui/main_window.py` | Replace inline hex in ActivityBar and Sidebar setStyleSheet calls |
| `ui/top_toolbar.py` | Replace hardcoded hex in `_sep()`, `ModelBadge`, `WorkspaceStatus` |
| `ui/editor/editor_tabs.py` | Replace hardcoded hex in `QTabWidget` setStyleSheet; theme-aware tab indicator |
| `ui/status_bar.py` | Replace hardcoded hex in `_separator_label()` and `StatusChip` |
| `ui/ai_workspace/ai_engineering_workspace.py` | Replace hardcoded hex in scroll area and container setStyleSheet |
| `ui/ai_workspace/ai_workspace_panel.py` | Restyle `Section` header with palette tokens |

---

## Component Design

### 1. Design Token Upgrade (`ui/design_system.py`)

Only the **token values** change. All attribute **names** are preserved for backward compatibility.

#### Radius (upgraded values)

```python
class Radius:
    NONE  = 0
    SM    = 4    # unchanged
    MD    = 6    # was 3
    LG    = 8    # was 4
    XL    = 10   # was 6
    ROUND = 20   # was 12
```

#### Shadow (richer shadows)

```python
class Shadow:
    NONE = "none"
    SM   = "0 1px 3px rgba(0,0,0,0.12)"   # was lighter
    MD   = "0 2px 8px rgba(0,0,0,0.18)"   # was lighter
    LG   = "0 4px 16px rgba(0,0,0,0.24)"  # was lighter
    XL   = "0 8px 24px rgba(0,0,0,0.32)"  # was lighter
```

#### Spacing (tighter premium scale)

```python
class Spacing:
    # Existing tokens preserved, values for LG/XL/XXL updated:
    LG  = 14   # was 12
    XL  = 20   # was 16
    XXL = 28   # was 24
```

No attribute is removed. `SM`, `MD`, `XXS`, `XS`, `XXXL` values are unchanged.

---

### 2. ThemeManager Global QSS (`ui/theme.py`)

`_generate_stylesheet` is expanded with explicit rules for each surface. Key additions to the existing stylesheet:

```python
# Inside _generate_stylesheet, using p = self.ds.palette:

# ── Activity Bar ──────────────────────────────────────────────────────
"""
#ActivityBar {{
    background-color: {p.bg_secondary};
    border-right: 1px solid {p.border_subtle};
}}

#ActivityBar QPushButton {{
    background-color: transparent;
    color: {p.text_tertiary};
    border: none;
    border-radius: {Radius.LG}px;
    font-size: 18px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
}}

#ActivityBar QPushButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

#ActivityBar QPushButton[active="true"] {{
    color: {p.text};
    border-left: 2px solid {p.accent};
}}
"""

# ── Sidebar ────────────────────────────────────────────────────────────
"""
#SidebarHeader {{
    background-color: {p.bg_secondary};
    border-bottom: 1px solid {p.border};
}}

#SidebarTitle {{
    font-size: {FontSize.XS}px;
    font-weight: {FontWeight.SEMIBOLD};
    color: {p.text_secondary};
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
"""

# ── TopToolbar ─────────────────────────────────────────────────────────
"""
QToolBar#TopToolbar {{
    background-color: {p.toolbar};
    border: none;
    border-bottom: 1px solid {p.border};
    min-height: 38px;
    max-height: 38px;
    padding: 0 {Spacing.MD}px;
    spacing: {Spacing.SM}px;
}}

QToolBar#TopToolbar QToolButton {{
    background-color: transparent;
    color: {p.text_secondary};
    border: none;
    border-radius: {Radius.MD}px;
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.MEDIUM};
    padding: {Spacing.SM}px {Spacing.MD}px;
    min-height: 28px;
}}

QToolBar#TopToolbar QToolButton:hover {{
    background-color: {p.surface_hover};
    color: {p.text};
}}
"""

# ── Editor Tab Bar ─────────────────────────────────────────────────────
"""
QTabBar::tab {{
    background-color: {p.bg_secondary};
    color: {p.text_secondary};
    border: none;
    border-right: 1px solid {p.border_subtle};
    padding: 8px 16px;
    min-height: 34px;
    max-height: 34px;
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.MEDIUM};
}}

QTabBar::tab:hover:!selected {{
    background-color: {p.surface_hover};
    color: {p.text};
}}

QTabBar::tab:selected {{
    background-color: {p.editor_bg};
    color: {p.text};
    border-top: 2px solid {p.accent};
    padding-top: 6px;
}}

QTabWidget::pane {{
    border: none;
    background-color: {p.editor_bg};
}}
"""

# ── Status Bar ─────────────────────────────────────────────────────────
"""
QStatusBar#BottomStatusBar {{
    background-color: {p.statusbar};
    border-top: 1px solid {p.border};
    min-height: 24px;
    max-height: 24px;
    font-size: {FontSize.XS}px;
    padding: 0;
}}
"""

# ── QMainWindow Separator ──────────────────────────────────────────────
"""
QMainWindow::separator {{
    background-color: {p.border_subtle};
    width: 1px;
    height: 1px;
}}
"""

# ── QDockWidget (AI Workspace) ─────────────────────────────────────────
"""
QDockWidget::title {{
    background-color: {p.bg_secondary};
    color: {p.text_secondary};
    padding: {Spacing.MD}px;
    border-bottom: 1px solid {p.border};
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.SEMIBOLD};
}}

QDockWidget::close-button,
QDockWidget::float-button {{
    background-color: transparent;
    border: none;
    border-radius: {Radius.SM}px;
}}

QDockWidget::close-button:hover,
QDockWidget::float-button:hover {{
    background-color: {p.surface_hover};
}}
"""
```

Additionally, `apply_theme` must call `QApplication.instance().topLevelWidgets()` and trigger `update()` on each widget after setting the stylesheet to force repaints on widgets that inline-set stylesheets.

```python
def apply_theme(self, theme_name: str):
    set_design_system_theme(theme_name)
    self.ds = get_design_system()
    self.current_theme = theme_name
    stylesheet = self._generate_stylesheet()
    self.app.setStyleSheet(stylesheet)
    # Force repaint so inline-QSS widgets re-read palette
    for w in self.app.topLevelWidgets():
        w.update()
```

---

### 3. Main Window — ActivityBar & Sidebar (`ui/main_window.py`)

The inline `setStyleSheet` calls in `setup_ui` replace hardcoded hex with live `ds.palette` references. No layout or signal changes.

```python
# Before (hardcoded):
self._activity_bar.setStyleSheet(f"""
    background-color: {ds.palette.bg_secondary};
    border-right: 1px solid {ds.palette.border};
""")

# After — same call, but ds is obtained from get_design_system()
# which now reads the current theme, so toggling the theme works:
from ui.design_system import get_design_system
ds = get_design_system()
p = ds.palette

self._activity_bar.setObjectName("ActivityBar")
self._activity_bar.setStyleSheet(f"""
    QWidget#ActivityBar {{
        background-color: {p.bg_secondary};
        border-right: 1px solid {p.border_subtle};
    }}
""")
```

Each activity button's inline QSS references `p.surface_hover`, `p.text_tertiary`, `p.text`, `p.accent`, `Radius.LG` instead of hardcoded hex.

The sidebar header uses `p.bg_secondary`, `p.border`, `p.text_secondary`, `FontWeight.SEMIBOLD`, `FontSize.XS`. The sidebar toggle button uses `p.text_tertiary` text and `p.surface_hover` hover background.

---

### 4. Top Toolbar (`ui/top_toolbar.py`)

#### `_sep()` helper

```python
def _sep() -> QFrame:
    from ui.design_system import get_design_system
    p = get_design_system().palette
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFixedWidth(1)
    f.setStyleSheet(f"color: {p.border}; background-color: {p.border}; margin: 5px 3px;")
    return f
```

#### `WorkspaceStatus`

```python
class WorkspaceStatus(QLabel):
    def __init__(self):
        super().__init__("No Workspace")
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: {FontSize.SM}px;
            background-color: transparent;
            padding: 0 6px;
        """)
        self.setMaximumWidth(220)

    def set_workspace(self, name: str):
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self.setText(name)
        self.setStyleSheet(f"""
            color: {p.text_secondary};
            font-size: {FontSize.SM}px;
            background-color: transparent;
            padding: 0 6px;
        """)
```

#### `ModelBadge`

```python
# In ModelBadge.__init__:
from ui.design_system import get_design_system
p = get_design_system().palette
self.setStyleSheet(f"""
    #ModelBadge {{
        background-color: {p.surface};
        border: 1px solid {p.border};
        border-radius: {Radius.MD}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
    }}
    #ModelBadge:hover {{
        border-color: {p.border_hover};
        background-color: {p.surface_hover};
    }}
""")
```

The `QToolBar` is given `objectName("TopToolbar")` to allow targeted QSS rules. The toolbar fixed height is controlled by the global QSS rule `min-height: 38px; max-height: 38px`.

---

### 5. Editor Tabs (`ui/editor/editor_tabs.py`)

The hardcoded stylesheet in `setup_ui` for `self.tabs` is replaced:

```python
# Before (hardcoded hex):
self.tabs.setStyleSheet("""
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: #181825;
        color: #A6ADC8;
        ...
    }
    QTabBar::tab:selected {
        background: #1E1E2E;
        color: #CDD6F4;
        border-top: 2px solid #89B4FA;
    }
""")

# After (palette tokens):
from ui.design_system import get_design_system, Spacing, Radius, FontSize, FontWeight
p = get_design_system().palette
self.tabs.setStyleSheet(f"""
    QTabWidget::pane {{
        border: none;
        background-color: {p.editor_bg};
    }}
    QTabBar::tab {{
        background-color: {p.bg_secondary};
        color: {p.text_secondary};
        padding: 8px 16px;
        border: none;
        border-right: 1px solid {p.border_subtle};
        font-size: {FontSize.SM}px;
        font-weight: {FontWeight.MEDIUM};
        min-height: 34px;
        max-height: 34px;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {p.surface_hover};
        color: {p.text};
    }}
    QTabBar::tab:selected {{
        background-color: {p.editor_bg};
        color: {p.text};
        border-top: 2px solid {p.accent};
        padding-top: 6px;
    }}
    QTabBar::tab:pinned {{
        font-weight: bold;
    }}
""")
```

The `content_splitter` handle colour also uses `p.border_subtle` instead of the hardcoded `#313244`.

The unsaved indicator in `on_editor_modified` appends `" ●"` to the tab text. The requirement specifies the dot should be visually distinct. The implementation already uses a `●` character suffix; the QSS styling of the tab label colour (`p.warning` for the dot) is applied via a custom `QTabBar::tab[modified="true"]` rule that the `on_editor_modified` method sets as a property:

```python
# In on_editor_modified — after setting tab text:
tab_bar = self.tabs.tabBar()
tab_bar.setTabData(idx, {"modified": modified})
# QSS rule in global stylesheet handles coloring
```

The BreadcrumbBar already applies its own styling; `BreadcrumbNavigation` setStyleSheet references are updated to use `p.bg_secondary`, `p.border_subtle`, `p.text_secondary`, `FontSize.SM`.

---

### 6. Status Bar (`ui/status_bar.py`)

#### `_separator_label()`

```python
def _separator_label() -> QLabel:
    from ui.design_system import get_design_system
    p = get_design_system().palette
    lbl = QLabel("│")
    lbl.setStyleSheet(
        f"color: {p.border}; background-color: transparent; padding: 0 2px;"
    )
    return lbl
```

#### `StatusChip._update_style`

```python
def _update_style(self, accent: bool):
    from ui.design_system import get_design_system, FontSize
    p = get_design_system().palette
    if accent:
        self.setStyleSheet(f"""
            color: {p.accent};
            background-color: transparent;
            font-size: {FontSize.XS}px;
            padding: 0 8px;
            font-weight: 500;
        """)
    else:
        self.setStyleSheet(f"""
            color: {p.text_secondary};
            background-color: transparent;
            font-size: {FontSize.XS}px;
            padding: 0 8px;
        """)
```

The `_on_task_failed` handler similarly uses `p.error` instead of the hardcoded `#EF4444`. The `_on_provider_changed` / `_on_model_changed` handlers use `p.success`, `p.error`, `p.accent` instead of hardcoded colour strings.

The "Thinking" pulsing animation for the AI status chip is implemented via a `QPropertyAnimation` on the `windowOpacity` effect or via a custom `QGraphicsOpacityEffect`. The animation runs between opacity 1.0 and 0.5 with `Duration.SLOW` ms per half-cycle and loops while the AI is in the Thinking state.

---

### 7. AI Workspace Dock (`ui/ai_workspace/ai_engineering_workspace.py`)

The `setup_ui` method replaces all hardcoded hex strings:

```python
from ui.design_system import get_design_system
p = get_design_system().palette

scroll.setStyleSheet(f"""
    QScrollArea {{
        background-color: {p.bg};
        border: none;
    }}
    QScrollBar:vertical {{
        background-color: {p.bg};
        width: 6px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {p.border};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {p.accent};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
""")

container.setStyleSheet(f"background-color: {p.bg};")
```

The dock widget itself is styled via the global QSS rules in ThemeManager (see Section 2). No structural changes.

---

### 8. AI Workspace Panel — Section Header (`ui/ai_workspace/ai_workspace_panel.py`)

The `Section` component (which wraps collapsible content) is read to understand its header structure. The header widget's stylesheet is updated to use palette tokens:

```python
from ui.design_system import get_design_system, FontSize, FontWeight
p = get_design_system().palette

# Section header default style:
header_style = f"""
    QWidget#SectionHeader {{
        background-color: {p.bg_secondary};
        border-bottom: 1px solid {p.border_subtle};
    }}
    QWidget#SectionHeader:hover {{
        background-color: {p.surface_hover};
    }}
"""

# Section header label:
label_style = f"""
    font-size: {FontSize.SM}px;
    font-weight: {FontWeight.SEMIBOLD};
    color: {p.text};
"""

# Arrow label (collapse indicator):
arrow_style = f"""
    color: {p.text_tertiary};
    font-size: {FontSize.SM}px;
"""
```

---

## Data Models

No new data models are introduced. The existing `ColorPalette` dataclass, `Radius`, `Shadow`, `Spacing`, `FontSize`, `FontWeight` classes, and `DesignSystem` singleton are extended in-place with updated token values. The `ThemeManager` class is updated in-place.

All design tokens are pure class-level constants (integer or string). They carry no state and require no persistence.

---

## Error Handling

- If `get_design_system()` is called before the singleton is initialised (e.g., during early widget construction), it falls back to `Themes.DARK`. This behaviour is unchanged.
- If an unsupported theme name is passed to `apply_theme`, `_load_theme` already falls back to `Themes.DARK`. This behaviour is unchanged.
- Any `setStyleSheet` call that uses an f-string with palette tokens cannot produce a Python error (the tokens are plain strings/ints). Invalid QSS is silently ignored by Qt.

---

## Non-Regression Strategy

The constraint is explicit: no functional change. The following invariants are maintained throughout the implementation:

1. All signal declarations and `connect()` calls in every affected file are untouched.
2. All event-bus `subscribe()` and `publish()` calls are untouched.
3. All method signatures and public APIs are unchanged.
4. `QShortcut` bindings in `MainWindow.setup_shortcuts` are untouched.
5. Dock min/max widths (`setMinimumWidth(240)`, `setMaximumWidth(480)`) are unchanged.
6. Only `setStyleSheet`, `setFixedHeight`, `setFixedWidth`, colour string literals, and token class constant values are modified.

---

## Testing Strategy

**Unit tests** cover specific token values, individual QSS content assertions, and non-regression checks:
- Assert Radius, Shadow, Spacing token values match the specified upgrade targets.
- Assert all backward-compatible attribute names still exist on token classes.
- Assert QSS generated by `ThemeManager._generate_stylesheet` contains expected token references.
- Assert no hardcoded hex literals remain in `EditorTabs`, `AIEngineeringWorkspace`, `MainWindow`, `TopToolbar`, `StatusBar`.
- Assert dock min/max width constraints, toolbar height, and status bar height are unchanged.
- Assert keyboard shortcuts, signals, and event-bus subscriptions exist and are connected.

**Property-based tests** cover universal invariants across all five supported themes and all file paths:
- For every supported theme name, stylesheet regeneration produces non-empty, theme-specific output.
- For any two distinct themes, the produced stylesheets differ.
- All pre-existing token class attribute names survive the upgrade unchanged in name and type.

No property-based tests are written for UI rendering, infrastructure, or widget interaction — those are covered by unit/integration tests.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

#### Property Reflection

Before listing properties, I eliminate redundancy:

- Properties covering "no hardcoded hex in file X" (3.8, 4.3, 5.1) share the same pattern. They are kept as separate properties because they target different files with different known hex sets — combining them would lose specificity.
- Properties covering "DesignSystem attribute backward compatibility" (6.6) and "ThemeManager stylesheet regeneration for any theme" (1.4, 5.8) are distinct: 1.4 checks stylesheet content changes, 5.8 checks that regeneration produces distinct outputs for distinct themes; both are kept.
- 5.8 subsumes 1.4 in practice (if regeneration produces distinct stylesheets, it necessarily regenerated). 1.4 is kept as a simpler, more focused property.
- Properties 3.8, 4.3, 5.1 are kept distinct as they validate different source modules.

Final set: 6 non-redundant properties.

---

### Property 1: ThemeManager regenerates stylesheet for every supported theme

*For any* supported theme name (dark, light, one_dark, github_dark, nord), calling `ThemeManager.apply_theme(theme_name)` SHALL produce a non-empty global QSS stylesheet that contains at least one colour token value from that theme's `ColorPalette`.

**Validates: Requirements 1.4, 5.8**

---

### Property 2: DesignSystem backward compatibility — all existing token attributes preserved

*For any* attribute name that existed in `ColorPalette`, `Spacing`, `Radius`, `Shadow`, `FontFamily`, `FontSize`, `FontWeight`, or `Duration` before the redesign, that attribute SHALL still exist with the same type after the redesign is applied.

**Validates: Requirements 1.5, 6.6**

---

### Property 3: No hardcoded hex colours in EditorTabs source

*For any* known hardcoded hex colour literal previously embedded in `ui/editor/editor_tabs.py` (specifically `#181825`, `#1E1E2E`, `#89B4FA`, `#313244`, `#A6ADC8`, `#CDD6F4`), that literal SHALL NOT appear as a plain string in the module source after the redesign — all colour references SHALL use `DesignSystem.palette` token attributes.

**Validates: Requirements 3.8**

---

### Property 4: No hardcoded hex colours in AIEngineeringWorkspace source

*For any* known hardcoded hex colour literal previously embedded in `ui/ai_workspace/ai_engineering_workspace.py` (specifically `#111113`, `#252528`), that literal SHALL NOT appear as a plain string in the module source after the redesign — all colour references SHALL use `DesignSystem.palette` token attributes.

**Validates: Requirements 4.3, 4.4, 5.7**

---

### Property 5: No hardcoded hex colours in MainWindow/TopToolbar/StatusBar sources

*For any* known hardcoded hex colour literal previously embedded in `ui/main_window.py` (e.g., `#25262D`, `#8E939C`, `#D7D9DE`), `ui/top_toolbar.py` (e.g., `#252528`, `#1C1C1F`, `#222226`, `#52525C`, `#8E8E98`), or `ui/status_bar.py` (e.g., `#252528`, `#3B82F6`, `#8E8E98`), those literals SHALL NOT appear as plain strings in the respective module sources after the redesign.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

---

### Property 6: Two distinct supported themes produce different QSS stylesheets

*For any* two distinct supported theme names A and B, `ThemeManager._generate_stylesheet()` after `apply_theme(A)` SHALL produce a stylesheet string that differs from the stylesheet produced after `apply_theme(B)`, confirming that theme switching regenerates the stylesheet rather than caching a single output.

**Validates: Requirements 1.4, 5.8**
