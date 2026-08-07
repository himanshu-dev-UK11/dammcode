# Implementation Plan: AI IDE UI Redesign

## Overview

Upgrade the visual design of MyCodingMaster IDE without changing any functional behaviour. All colour and dimension values are migrated from hardcoded hex literals to `DesignSystem` palette token references. The global QSS stylesheet in `ThemeManager` is expanded with premium rules for every surface. The implementation is purely cosmetic: signals, slots, event-bus subscriptions, and public APIs remain untouched throughout.

## Tasks

- [ ] 1. Upgrade design token values in `ui/design_system.py`
  - [ ] 1.1 Update `Radius`, `Shadow`, and `Spacing` constant values to the new premium spec
    - Set `Radius.MD = 6`, `Radius.LG = 8`, `Radius.XL = 10`, `Radius.ROUND = 20`
    - Set `Shadow.SM`, `MD`, `LG`, `XL` to the richer rgba strings defined in design Section 1
    - Set `Spacing.LG = 14`, `Spacing.XL = 20`, `Spacing.XXL = 28`
    - Do NOT rename or remove any existing attribute; preserve all other values unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [ ]* 1.2 Write property test for DesignSystem backward compatibility (Property 2)
    - **Property 2: DesignSystem backward compatibility — all existing token attributes preserved**
    - **Validates: Requirements 1.5, 6.6**
    - Generate all known pre-redesign attribute names for `ColorPalette`, `Spacing`, `Radius`, `Shadow`, `FontFamily`, `FontSize`, `FontWeight`, `Duration` and assert each still exists with the same type
    - Use `hypothesis` strategies to drive attribute name selection from the known set

- [ ] 2. Expand `ThemeManager` global QSS in `ui/theme.py`
  - [ ] 2.1 Add premium QSS rules for ActivityBar, Sidebar, TopToolbar, EditorTabBar, BottomStatusBar, QMainWindow separator, and QDockWidget
    - Insert all QSS blocks from design Section 2 into `_generate_stylesheet`
    - Use `p = self.ds.palette` and token class references (no hardcoded hex)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8, 2.9, 3.1, 3.2, 3.3, 3.4, 3.7, 4.1, 4.2, 2.13_

  - [ ] 2.2 Update `apply_theme` to force-repaint all top-level widgets after stylesheet change
    - After `app.setStyleSheet(stylesheet)`, iterate `app.topLevelWidgets()` and call `w.update()` on each
    - _Requirements: 1.4, 5.8_

  - [ ]* 2.3 Write property test for ThemeManager stylesheet regeneration (Property 1)
    - **Property 1: ThemeManager regenerates stylesheet for every supported theme**
    - **Validates: Requirements 1.4, 5.8**
    - Use `hypothesis` to iterate all five supported theme names; assert `apply_theme` produces a non-empty stylesheet containing at least one colour token value from that theme's `ColorPalette`

  - [ ]* 2.4 Write property test for distinct themes producing different stylesheets (Property 6)
    - **Property 6: Two distinct supported themes produce different QSS stylesheets**
    - **Validates: Requirements 1.4, 5.8**
    - Use `hypothesis` to draw two distinct theme names from the supported set; assert `_generate_stylesheet()` output after each `apply_theme` call differs between the two

- [ ] 3. Checkpoint — Ensure design token and ThemeManager tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Migrate `ui/main_window.py` — ActivityBar and Sidebar inline QSS
  - [ ] 4.1 Replace hardcoded hex strings in `setup_ui` ActivityBar and Sidebar `setStyleSheet` calls
    - Obtain `ds = get_design_system(); p = ds.palette` at the top of `setup_ui`
    - Set `objectName("ActivityBar")` on the activity bar widget
    - Replace hex literals with `p.bg_secondary`, `p.border_subtle`, `p.surface_hover`, `p.text_tertiary`, `p.text`, `p.accent`, and `Radius.LG` references as specified in design Section 3
    - Replace Sidebar header QSS hex with `p.bg_secondary`, `p.border`, `p.text_secondary`, and token references
    - Do NOT modify any `connect()` calls, `QShortcut` bindings, or signal declarations
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1_

  - [ ]* 4.2 Write property test: no hardcoded hex in MainWindow source (Property 5, main_window part)
    - **Property 5: No hardcoded hex colours in MainWindow source**
    - **Validates: Requirements 5.1**
    - Read the source of `ui/main_window.py` as text and assert none of the known hex literals (`#25262D`, `#8E939C`, `#D7D9DE`, etc.) appear as plain strings

- [ ] 5. Migrate `ui/top_toolbar.py` — inline QSS token replacement
  - [ ] 5.1 Replace hardcoded hex in `_sep()`, `WorkspaceStatus`, and `ModelBadge`
    - `_sep()`: use `p.border` instead of `#252528`
    - `WorkspaceStatus`: use `p.text_tertiary` and `p.text_secondary` instead of `#52525C` / `#8E8E98`
    - `ModelBadge`: use `p.surface`, `p.border`, `p.border_hover`, `p.surface_hover`, `Radius.MD`, `Spacing.SM`, `Spacing.MD` instead of `#1C1C1F`, `#252528`, `#222226`
    - Assign `objectName("TopToolbar")` to the toolbar widget so global QSS rules target it
    - _Requirements: 2.9, 2.10, 5.2, 5.3, 5.4_

  - [ ]* 5.2 Write property test: no hardcoded hex in TopToolbar source (Property 5, top_toolbar part)
    - **Property 5: No hardcoded hex colours in TopToolbar source**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Read `ui/top_toolbar.py` source as text and assert none of `#252528`, `#1C1C1F`, `#222226`, `#52525C`, `#8E8E98` appear as plain strings

- [ ] 6. Migrate `ui/editor/editor_tabs.py` — tab bar QSS and unsaved indicator
  - [ ] 6.1 Replace hardcoded hex in `setup_ui` tab widget `setStyleSheet` call
    - Import `get_design_system`, `Spacing`, `Radius`, `FontSize`, `FontWeight` at top of file
    - Obtain `p = get_design_system().palette` inside `setup_ui`
    - Replace all hardcoded hex tab colours with palette tokens per design Section 5
    - Replace `content_splitter` handle colour `#313244` with `p.border_subtle`
    - Add `QTabBar::tab:pinned` rule preserving bold weight
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.7, 3.8_

  - [ ] 6.2 Update BreadcrumbBar stylesheet to use palette tokens
    - Replace any hardcoded hex in `BreadcrumbNavigation` `setStyleSheet` with `p.bg_secondary`, `p.border_subtle`, `p.text_secondary`, `FontSize.SM`
    - _Requirements: 3.6, 3.8_

  - [ ] 6.3 Implement theme-aware unsaved-changes dot indicator
    - In `on_editor_modified`, after setting tab text, call `tab_bar.setTabData(idx, {"modified": modified})`
    - Add a `QTabBar::tab[modified="true"]` QSS rule (in global stylesheet or local) using `p.warning` for the indicator colour
    - _Requirements: 3.5_

  - [ ]* 6.4 Write property test: no hardcoded hex in EditorTabs source (Property 3)
    - **Property 3: No hardcoded hex colours in EditorTabs source**
    - **Validates: Requirements 3.8**
    - Read `ui/editor/editor_tabs.py` source as text and assert none of `#181825`, `#1E1E2E`, `#89B4FA`, `#313244`, `#A6ADC8`, `#CDD6F4` appear as plain strings

- [ ] 7. Migrate `ui/status_bar.py` — StatusChip and separator inline QSS
  - [ ] 7.1 Replace hardcoded hex in `_separator_label()` and `StatusChip._update_style`
    - `_separator_label()`: use `p.border` instead of `#252528`
    - `StatusChip._update_style`: use `p.accent` for accent state and `p.text_secondary` for default state
    - `_on_task_failed`: replace `#EF4444` with `p.error`
    - `_on_provider_changed` / `_on_model_changed`: replace hardcoded colours with `p.success`, `p.error`, `p.accent`
    - Assign `objectName("BottomStatusBar")` so global QSS rules target it
    - _Requirements: 2.11, 2.12, 5.5, 5.6_

  - [ ] 7.2 Implement AI "Thinking" pulsing opacity animation
    - In the handler that sets AI status to "Thinking", create a `QGraphicsOpacityEffect` on the status `StatusChip`
    - Attach a `QPropertyAnimation` targeting `opacity`, running from 1.0 to 0.5 with `Duration.SLOW` ms per half-cycle, looping indefinitely
    - Stop and remove the animation when the task completes or fails
    - _Requirements: 2.12_

  - [ ]* 7.3 Write property test: no hardcoded hex in StatusBar source (Property 5, status_bar part)
    - **Property 5: No hardcoded hex colours in StatusBar source**
    - **Validates: Requirements 5.5, 5.6**
    - Read `ui/status_bar.py` source as text and assert none of `#252528`, `#3B82F6`, `#8E8E98`, `#EF4444` appear as plain strings

- [ ] 8. Checkpoint — Ensure all widget migration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Migrate `ui/ai_workspace/ai_engineering_workspace.py` — scroll area and container QSS
  - [ ] 9.1 Replace hardcoded hex in `setup_ui` scroll area and container `setStyleSheet` calls
    - Import `get_design_system` and replace `#111113` with `p.bg` and `#252528` scrollbar colour with `p.border`
    - Keep 6 px slim scrollbar width and all other layout values unchanged
    - _Requirements: 4.3, 4.4, 5.7_

  - [ ]* 9.2 Write property test: no hardcoded hex in AIEngineeringWorkspace source (Property 4)
    - **Property 4: No hardcoded hex colours in AIEngineeringWorkspace source**
    - **Validates: Requirements 4.3, 4.4, 5.7**
    - Read `ui/ai_workspace/ai_engineering_workspace.py` source as text and assert neither `#111113` nor `#252528` appear as plain strings

- [ ] 10. Migrate `ui/ai_workspace/ai_workspace_panel.py` — Section header QSS
  - [ ] 10.1 Update `Section` header widget stylesheet with palette tokens
    - Assign `objectName("SectionHeader")` to the header widget
    - Apply `p.bg_secondary` background, `p.border_subtle` bottom separator, `p.surface_hover` hover background
    - Apply `FontSize.SM`, `FontWeight.SEMIBOLD`, `p.text` to the section label
    - Apply `p.text_tertiary` and `FontSize.SM` to the collapse arrow label
    - _Requirements: 4.5, 4.6_

- [ ] 11. Verify non-regression of functional behaviour
  - [ ] 11.1 Write unit tests asserting all keyboard shortcuts, signals, and event-bus subscriptions are unchanged
    - Assert `MainWindow` shortcuts (`Ctrl+B`, `Ctrl+\`, `Ctrl+Shift+P`) are registered
    - Assert `TopToolbar` signals (`open_project_requested`, `run_requested`, `stop_requested`, `search_requested`, `command_palette_requested`, `model_selector_requested`) exist on the widget
    - Assert `AIWorkspaceDock` event-bus subscription handler methods are present and callable
    - Assert `BottomStatusBar` event-bus subscription handler methods are present and callable
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 11.2 Write unit tests asserting dock and toolbar fixed dimensions are unchanged
    - Assert `AIWorkspaceDock` minimum width is 240 px and maximum width is 480 px
    - Assert `TopToolbar` fixed height is 38 px (via global QSS min/max-height rules present in generated stylesheet)
    - Assert `BottomStatusBar` fixed height is 24 px
    - _Requirements: 4.7, 2.8, 2.11, 6.1_

- [ ] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The purely visual scope means no signal, slot, event-bus, or method signature is touched
- Property tests use `hypothesis`; unit tests use `pytest`
- The pulsing opacity animation (task 7.2) is the only runtime behaviour introduced; it is contained entirely within the status bar widget
- Token upgrade (task 1.1) is the foundation — complete it before any QSS migration tasks

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["4.1", "5.1", "6.1", "7.1", "9.1", "10.1"] },
    { "id": 4, "tasks": ["4.2", "5.2", "6.2", "6.3", "7.2", "9.2"] },
    { "id": 5, "tasks": ["6.4", "7.3", "11.1", "11.2"] }
  ]
}
```
