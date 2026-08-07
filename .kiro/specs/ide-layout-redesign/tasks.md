# Implementation Plan: IDE Layout Redesign

## Overview

This plan transforms MyCodingMaster from a fragmented multi-panel interface into a professional, unified IDE layout comparable to VS Code, Cursor, and JetBrains IDEs. The redesign creates a modern, cohesive interface with six primary components: Activity Bar, Sidebar, Editor Area, AI Workspace, Bottom Dock, and Status Bar.

The implementation follows a structured approach:
- **Phase 1**: Core infrastructure and layout architecture
- **Phase 2**: Workspace system for panel state management
- **Phase 3**: Editor system for file management
- **Phase 4**: Explorer system with activity switching
- **Phase 5**: Docking system for bottom panels
- **Phase 6**: AI workspace organization
- **Phase 7**: Performance optimization
- **Phase 8**: Visual polish and animations
- **Phase 9**: Final QA and integration

---

## Tasks

### Phase 1 — Core Infrastructure

**After Phase 1, the project will have a robust layout architecture with all foundational components in place.**

#### Layout Architecture and State Management

- [ ] 1.1 Create layout data models (LayoutState, PanelConstraints, ActivityType, DockTab, AISection, SplitConfig)
  - Define LayoutState dataclass with all panel configuration fields
  - Define PanelConstraints dataclass with min/max/default values
  - Implement ActivityType enum (8 activities)
  - Implement DockTab enum (7 tabs)
  - Implement AISection enum (8 sections)
  - Implement SplitConfig dataclass for editor splits
  - _Requirements: 1.1-1.10, 2.1-2.10, 3.1-3.10, 7.1-7.12, 8.1-8.13, 10.1-10.11, 13.1-13.10, 14.1-14.12_

- [ ]* 1.2 Write property test for LayoutState serialization round-trip
  - **Property 3: LayoutState Serialization Round-Trip**
  - **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9**
  - Generate random LayoutState objects and verify serialization/deserialization preserves all fields
  - _Requirements: 15.1-15.9_

- [ ]* 1.3 Write property test for panel constraint enforcement
  - **Property 1: Panel Constraint Enforcement**
  - **Validates: Requirements 4.2, 4.3, 7.7, 8.7, 8.8, 9.2, 21.6**
  - Generate random resize values and verify all panel sizes stay within constraints
  - _Requirements: 4.2, 4.3, 7.7, 8.7, 8.8, 9.2_

- [ ]* 1.4 Write property test for EditorArea minimum size invariant
  - **Property 4: EditorArea Minimum Size Invariant**
  - **Validates: Requirements 23.5, 23.6**
  - Generate random layouts and verify EditorArea always meets 400x300 minimum
  - _Requirements: 23.5, 23.6_

#### Layout Components

- [ ] 1.5 Create SplitterHandle component
  - Implement SplitterHandle class with resize events
  - Implement visual hover effect (1px → 3px on hover)
  - Implement double-click reset functionality
  - Add constraint enforcement during drag
  - _Requirements: 9.1-9.10, 10.3, 10.4, 10.12_

- [ ] 1.6 Create CollapsibleSection component
  - Implement CollapsibleSection class with expand/collapse
  - Add 200ms animation with CSS transforms
  - Support non-collapsible mode (Conversation section)
  - Add chevron icon rotation on toggle
  - _Requirements: 7.4-7.5, 7.11_

#### Theme System Integration

- [ ] 1.7 Update theme system for layout components
  - Add bg_sidebar theme variable
  - Add bg_editor theme variable
  - Add bg_dock theme variable
  - Add bg_statusbar theme variable
  - Add accent_color and border_subtle theme variables
  - _Requirements: 11.1-11.2, 11.4, 11.9, 11.10, 11.11_

- [ ] 1.8 Create theme extension for layout colors
  - Add section_header background to theme
  - Add hover state colors
  - Add active indicator colors
  - Implement high contrast mode support
  - _Requirements: 11.3, 11.5, 11.6, 11.7, 11.8_

---

### Phase 2 — Workspace System

**After Phase 2, the IDE will persist and restore layout configurations across sessions.**

#### State Persistence

- [ ] 2.1 Create SessionStateManager class
  - Implement save_state() and restore_state() methods
  - Handle missing/corrupted session file gracefully
  - Log errors with structured format
  - _Requirements: 15.1-15.9_

- [ ] 2.2 Create layout persistence service
  - Write .kiro/session.json workspace-specific file
  - Implement version compatibility checks
  - Handle validation failures with fallback to defaults
  - _Requirements: 15.1-15.9, 17.1-17.12, 20.1-20.10_

#### Layout Coordinator

- [ ] 2.3 Create WindowLayout class as root container
  - Implement coordinate layout calculation algorithm
  - Handle window resize events
  - Coordinate panel positioning
  - Manage global keyboard shortcuts
  - _Requirements: 1.1-1.10, 9.1-9.10, 17.1-17.12, 20.1-20.10_

- [ ] 2.4 Implement layout constraint validation
  - Create LayoutConstraintsValidator class
  - Enforce minimum window size 1024x680
  - Validate panel size ranges
  - Auto-collapse panels when constraints violated
  - _Requirements: 1.8, 23.1-23.10_

#### Event System

- [ ] 2.5 Create layout event types (ResizeEvent, VisibilityEvent)
  - Implement ResizeEvent dataclass
  - Implement VisibilityEvent dataclass
  - Add timestamp and metadata fields
  - _Requirements: 15.1-15.9_

- [ ] 2.6 Create event bus for panel communication
  - Implement observer pattern for panel events
  - Add panel_resized, panel_toggled, activity_selected events
  - _Requirements: 2.3-2.5, 3.1-3.10_

---

### Phase 3 — Editor System

**After Phase 3, the IDE will have a professional editor area with tab management and file operations.**

#### Editor Area Core

- [ ] 3.1 Create EditorArea class
  - Implement as main center panel container
  - Add event signals for file operations
  - Integrate with workspace system
  - _Requirements: 5.1-5.10, 6.1-6.11, 17.1-17.12_

#### Tab Management

- [ ] 3.2 Create EditorTabs component
  - Implement tab bar with close buttons
  - Support pinned tabs
  - Add tab switching events
  - Implement tab styling with rounded corners
  - _Requirements: 5.5, 5.7, 5.9_

- [ ] 3.3 Create BreadcrumbBar component
  - Display current file path
  - Show breadcrumbs for nested paths
  - Add clickable navigation segments
  - _Requirements: 5.8_

#### Welcome Screen

- [ ] 3.4 Create WelcomeScreen component
  - Display project logo at center
  - Add Open Folder, New Project, Clone Repository buttons
  - Show recent projects list (max 8)
  - Show recent files list (max 8)
  - _Requirements: 6.1-6.11_

#### Split Editor Support

- [ ] 3.5 Create SplitManager class
  - Implement horizontal/vertical split layouts
  - Manage split ratios and sizes
  - Add split divider interaction
  - _Requirements: 5.6_

---

### Phase 4 — Explorer System

**After Phase 4, the IDE will have a unified sidebar with activity-based content switching.**

#### Activity Bar

- [ ] 4.1 Create ActivityBar component
  - Implement fixed 44px width vertical bar
  - Add icon-only buttons (8 activities)
  - Implement active state indicator (2px accent bar)
  - Add hover effects
  - _Requirements: 2.1-2.10_

- [ ] 4.2 Add keyboard shortcuts for activity switching
  - Ctrl+Shift+E → Explorer
  - Ctrl+Shift+F → Search
  - Ctrl+Shift+G → Source Control
  - Ctrl+Shift+D → Debug
  - _Requirements: 12.4-12.7_

#### Sidebar Core

- [ ] 4.3 Create Sidebar class
  - Implement resizable panel (180-420px)
  - Add header with activity name display
  - Implement collapse/expand toggle
  - Add splitter handle on right edge
  - _Requirements: 3.1-3.10, 4.1-4.12_

- [ ] 4.4 Implement sidebar width constraints
  - Enforce minimum 180px and maximum 420px
  - Default width 220px
  - Collapsed width 0px
  - _Requirements: 4.2-4.4, 4.6-4.7_

#### Activity Content Switching

- [ ] 4.5 Create ActivityContentManager class
  - Implement pluggable content provider interface
  - Lazy load activity content on first selection
  - Cache last 3 activity contents
  - _Requirements: 3.1-3.10, 13.3-13.4_

- [ ] 4.6 Implement Explorer activity content
  - Display project file tree
  - Add file/folder icons
  - Implement collapse/expand for folders
  - _Requirements: 3.1_

- [ ] 4.7 Implement Search activity content
  - Display workspace search panel
  - Add search input field
  - Implement search results list
  - _Requirements: 3.2_

- [ ] 4.8 Implement Source Control activity content
  - Display git changes and staging panel
  - Add change list with icons
  - Implement staged/unstaged filtering
  - _Requirements: 3.3_

- [ ] 4.9 Implement Debug activity content
  - Display debugging controls and variables
  - Add call stack view
  - Implement variable watchlist
  - _Requirements: 3.4_

- [ ] 4.10 Implement Extensions activity content
  - Display extension management interface
  - Add search and filter functionality
  - Implement install/uninstall actions
  - _Requirements: 3.5_

- [ ] 4.11 Implement AI Memory activity content
  - Display AI memory and context viewer
  - Show conversation history summary
  - Add context list
  - _Requirements: 3.6_

- [ ] 4.12 Implement Tasks activity content
  - Display task list and management interface
  - Add task creation and editing
  - Implement task status tracking
  - _Requirements: 3.7_

- [ ] 4.13 Implement Settings activity content
  - Display settings configuration panel
  - Add category navigation
  - Implement settings persistence
  - _Requirements: 3.8_

#### Sidebar Behavior

- [ ] 4.14 Implement keyboard toggle for sidebar
  - Ctrl+B → toggle visibility
  - Smooth 200ms animation
  - Update toggle button icon (‹/›)
  - _Requirements: 4.5, 4.6, 4.10_

- [ ] 4.15 Implement activity switching animation
  - Smooth content transition within 150ms
  - Fade out old content, fade in new content
  - _Requirements: 3.10_

---

### Phase 5 — Docking System

**After Phase 5, the IDE will have a unified bottom dock with tabbed interface for terminal and diagnostics.**

#### Bottom Dock Core

- [ ] 5.1 Create BottomDock class
  - Implement unified tabbed interface
  - Add tab switching functionality
  - Implement resizable panel (120px-50% window height)
  - _Requirements: 8.1-8.13, 10.10_

- [ ] 5.2 Add keyboard toggle for bottom dock
  - Ctrl+` → toggle visibility
  - Implement collapsed strip mode (24px height)
  - Smooth 150ms animation
  - _Requirements: 8.10, 8.11, 8.12_

#### Tab Management

- [ ] 5.3 Implement standard dock tabs
  - Terminal tab
  - Problems tab
  - Output tab
  - Debug Console tab
  - Git tab
  - Tasks tab
  - Diagnostics tab
  - _Requirements: 8.2, 8.4_

- [ ] 5.4 Create tab content areas for each dock tab
  - Implement TerminalTab content
  - Implement ProblemsTab content
  - Implement OutputTab content
  - Implement DebugConsoleTab content
  - _Requirements: 8.1, 8.3, 8.4_

#### Dock Behavior

- [ ] 5.5 Implement splitter interaction
  - Add splitter handle on top edge
  - Double-click reset to default 180px height
  - Enforce min 120px and max 50% constraints
  - _Requirements: 8.6, 8.7, 8.8, 8.13_

- [ ] 5.6 Update default state for bottom dock
  - Hide bottom dock on initial startup (Requirement 10.6)
  - Show when user opens first terminal/debug session
  - Restore previous state on restart
  - _Requirements: 10.6_

---

### Phase 6 — AI Workspace

**After Phase 6, the IDE will have an organized right sidebar for AI features with collapsible sections.**

#### AI Workspace Core

- [ ] 6.1 Create AIWorkspace class
  - Implement resizable panel (240-480px)
  - Add splitter handle on left edge
  - Implement visibility toggle with Ctrl+\
  - _Requirements: 7.1-7.12_

#### Collapsible Sections

- [ ] 6.2 Implement Conversation section
  - Display always expanded (not collapsible)
  - Show chat interface
  - Add message list
  - _Requirements: 7.1, 7.3, 7.6_

- [ ] 6.3 Implement Prompt Input section
  - Display prompt input field
  - Add send button
  - Implement history dropdown
  - _Requirements: 7.2_

- [ ] 6.4 Implement Current Task Status section
  - Display task name and status
  - Add progress indicator
  - Show current step
  - _Requirements: 7.3_

- [ ] 6.5 Implement Execution Monitor section
  - Display execution statistics
  - Show token usage
  - Add execution time indicator
  - _Requirements: 7.4_

- [ ] 6.6 Implement Memory Viewer section
  - Display conversation memory
  - Show context summary
  - Add context tree view
  - _Requirements: 7.5_

- [ ] 6.7 Implement Verification Results section
  - Display property test results
  - Show verification status
  - Add details expansion
  - _Requirements: 7.6_

- [ ] 6.8 Implement Context Panel section
  - Display context file list
  - Add relevance scoring
  - Implement context filtering
  - _Requirements: 7.7_

- [ ] 6.9 Implement Model Selector section
  - Display model dropdown
  - Add model capabilities indicator
  - Implement model switching
  - _Requirements: 7.8_

#### AI Workspace Behavior

- [ ] 6.10 Implement section expand/collapse animations
  - 200ms smooth animation for each section
  - Chevron rotation on toggle
  - Save expanded state to session
  - _Requirements: 7.4, 7.5, 7.11_

- [ ] 6.11 Update AI workspace default state
  - Show Conversation section expanded (Requirement 7.3)
  - Hide all other sections by default
  - Set default width to 340px (Requirement 7.7)
  - _Requirements: 7.3, 10.4_

- [ ] 6.12 Implement keyboard toggle for AI workspace
  - Ctrl+\ → toggle visibility
  - Editor area expands to fill space when hidden
  - Smooth 200ms animation
  - _Requirements: 7.9, 7.10_

---

### Phase 7 — Performance

**After Phase 7, the IDE will render quickly and maintain 60fps animations.**

#### Rendering Optimization

- [ ] 7.1 Implement GPU-accelerated animations
  - Use CSS transforms for panel animations
  - Enable hardware-accelerated composition layers
  - Add will-change CSS property for animated panels
  - _Requirements: 18.2, 18.7_

- [ ] 7.2 Add debounced resize events
  - Implement 16ms debounce for resize operations
  - Prevent layout thrashing during rapid resizing
  - Maintain 60fps smoothness
  - _Requirements: 18.1-18.2, 18.7_

#### Lazy Loading

- [ ] 7.3 Implement lazy activity content loading
  - Load Explorer content only on first selection
  - Load Search content only on first selection
  - Load Source Control content only on first selection
  - _Requirements: 13.3_

- [ ] 7.4 Implement virtualization for large lists
  - Virtualize file tree (1000+ items)
  - Virtualize search results
  - Implement item recycling
  - _Requirements: 13.4_

#### Memory Management

- [ ] 7.5 Unload inactive panel content
  - Unload hidden panel content after 30 seconds of inactivity
  - Cache recently used activity contents
  - Limit layout memory footprint to <150MB
  - _Requirements: 13.3, 18.8_

- [ ] 7.6 Implement event subscription cleanup
  - Use weak references for event subscriptions
  - Clean up subscriptions on panel disposal
  - Prevent memory leaks
  - _Requirements: 18.8_

#### Initial Load Optimization

- [ ] 7.7 Optimize initial layout rendering
  - Render initial view in <100ms
  - Defer non-critical panel loading
  - Prioritize Activity Bar and EditorArea
  - _Requirements: 1.10, 10.11, 18.1_

- [ ] 7.8 Add loading states for content providers
  - Show loading spinner while content loads
  - Display error state if content fails
  - Add retry button for failed loads
  - _Requirements: 19.3_

---

### Phase 8 — Visual Polish

**After Phase 8, the IDE will have professional, cohesive visual design with smooth transitions.**

#### Layout Styling

- [ ] 8.1 Implement panel border styling
  - Add 1px borders with subtle colors
  - Add border to Activity Bar right edge
  - Add border to Sidebar right edge
  - Add border to AI Workspace left edge
  - Add border to Bottom Dock top edge
  - _Requirements: 11.3, 2.10, 4.12_

- [ ] 8.2 Add hover states for interactive elements
  - Activity Bar icons (200ms transition)
  - Splitter handles (150ms transition)
  - Section headers (150ms transition)
  - Close buttons on tabs
  - _Requirements: 11.5, 2.7, 4.9, 9.7_

#### Focus and Accessibility

- [ ] 8.3 Add focus indicators
  - Visual focus ring on keyboard navigation
  - High contrast focus indicators
  - Persistent focus visibility
  - _Requirements: 14.11, 14.12_

- [ ] 8.4 Implement proper tab order
  - Tab navigation through all interactive elements
  - Focus trapping in modal dialogs
  - Logical focus progression
  - _Requirements: 14.10, 14.12_

#### Theme Support

- [ ] 8.5 Implement theme switching
  - Support dark theme (default)
  - Support light theme
  - Support custom themes
  - Add theme selector in Settings
  - _Requirements: 11.8_

#### Animation Refinement

- [ ] 8.6 Refine panel transition animations
  - Sidebar expand/collapse: 200ms
  - AI Workspace expand/collapse: 200ms
  - Bottom Dock toggle: 150ms
  - Activity content switch: 150ms
  - _Requirements: 3.10, 4.12, 7.11, 8.12_

- [ ] 8.7 Add smooth splitter hover animation
  - Expand from 1px to 3px on hover (150ms)
  - Revert on hover out
  - Use CSS transitions
  - _Requirements: 9.7_

- [ ] 8.8 Implement resize feedback
  - Highlight splitter during drag
  - Show size preview during drag
  - Smooth resize animation
  - _Requirements: 9.1, 9.9_

---

### Phase 9 — Final QA and Integration

**After Phase 9, all components will be integrated and tested for a production-ready IDE.**

#### Integration Testing

- [ ] 9.1 Integration test layout calculation
  - Test window resize handling
  - Test panel resizing with constraints
  - Test auto-collapse behavior
  - _Requirements: 1.1-1.10, 9.1-9.10_

- [ ] 9.2 Integration test state persistence
  - Test save/restore workflow
  - Test corrupted file handling
  - Test version compatibility
  - _Requirements: 15.1-15.9, 17.1-17.12_

- [ ] 9.3 Integration test keyboard shortcuts
  - Test all 12 keyboard shortcuts
  - Verify shortcut documentation
  - Test shortcut conflicts
  - _Requirements: 12.1-12.12_

- [ ] 9.4 Integration test cross-panel events
  - Test ActivityBar ↔ Sidebar communication
  - Test ActivityBar ↔ EditorArea communication
  - Test AIWorkspace ↔ EditorArea communication
  - _Requirements: 2.3-2.5, 3.1-3.10_

#### Performance Validation

- [ ] 9.5 Validate rendering performance
  - Confirm <100ms initial render
  - Confirm 60fps animations
  - Confirm <150MB memory footprint
  - _Requirements: 18.1-18.10_

- [ ] 9.6 Validate animation performance
  - Measure animation frame times
  - Test with system under load
  - Test graceful degradation
  - _Requirements: 18.2-18.7_

#### Accessibility Validation

- [ ] 9.7 Validate screen reader compatibility
  - Test ARIA labels on all panels
  - Test keyboard navigation
  - Test focus management
  - _Requirements: 14.1-14.12_

#### Bug Fixes

- [ ] 9.8 Fix layout rendering issues
  - Address any visual glitches
  - Fix layout shifts during loading
  - Fix z-order issues
  - _Requirements: 18.7_

- [ ] 9.9 Fix constraint violations
  - Ensure all min/max constraints enforced
  - Ensure EditorArea never below minimum
  - Handle edge cases
  - _Requirements: 1.1-1.10, 9.1-9.10_

- [ ] 9.10 Fix animation issues
  - Fix jittery animations
  - Fix animation timing
  - Fix state inconsistencies
  - _Requirements: 11.4, 18.2_

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.7"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.8"] },
    { "id": 2, "tasks": ["1.6", "2.1", "2.7"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 4, "tasks": ["2.5", "2.6", "3.1", "3.2", "4.1"] },
    { "id": 5, "tasks": ["3.3", "3.4", "4.2", "4.3"] },
    { "id": 6, "tasks": ["3.5", "4.4", "4.5", "4.6"] },
    { "id": 7, "tasks": ["4.7", "4.8", "4.9", "4.10"] },
    { "id": 8, "tasks": ["4.11", "4.12", "4.13", "4.14", "4.15"] },
    { "id": 9, "tasks": ["5.1", "5.2", "5.3", "5.4"] },
    { "id": 10, "tasks": ["5.5", "5.6", "6.1", "6.2"] },
    { "id": 11, "tasks": ["6.3", "6.4", "6.5", "6.6"] },
    { "id": 12, "tasks": ["6.7", "6.8", "6.9", "6.10"] },
    { "id": 13, "tasks": ["6.11", "6.12", "7.1", "7.2"] },
    { "id": 14, "tasks": ["7.3", "7.4", "7.5", "7.6"] },
    { "id": 15, "tasks": ["7.7", "7.8", "8.1", "8.2"] },
    { "id": 16, "tasks": ["8.3", "8.4", "8.5", "8.6"] },
    { "id": 17, "tasks": ["8.7", "8.8", "9.1", "9.2"] },
    { "id": 18, "tasks": ["9.3", "9.4", "9.5", "9.6"] },
    { "id": 19, "tasks": ["9.7", "9.8", "9.9", "9.10"] }
  ]
}
```

## Notes

- **Task Marking**: Tasks marked with `*` are optional (unit tests, property tests) and can be skipped for faster MVP
- **Implementation Order**: Tasks are ordered to ensure dependencies are met. Phase 1 must complete before Phase 2, etc.
- **Constraint Validation**: All panels enforce size constraints (sidebar: 180-420px, AI workspace: 240-480px, bottom dock: 120px-50%)
- **Default Layout**: Initial layout shows sidebar (220px), AI workspace (340px), hidden bottom dock, Activity Bar with Explorer selected
- **Keyboard Shortcuts**: All 12 shortcuts implemented (Ctrl+B, Ctrl+\, Ctrl+`, Ctrl+Shift+E/F/G/D, Ctrl+K Ctrl+O, F5)
- **State Persistence**: Session state saved to `.kiro/session.json` with fallback to defaults on corruption
- **Performance Targets**: <100ms initial render, 60fps animations, <150MB memory footprint
- **Accessibility**: Full keyboard navigation, focus indicators, screen reader compatibility

---

## Implementation Phases Summary

| Phase | Tasks | Objective | Result |
|-------|-------|-----------|--------|
| 1 | 1.1-1.8 | Core infrastructure | Layout components and state models ready |
| 2 | 2.1-2.6 | Workspace system | State persistence and event system ready |
| 3 | 3.1-3.5 | Editor system | Editor area and tab management ready |
| 4 | 4.1-4.15 | Explorer system | Unified sidebar with activity switching |
| 5 | 5.1-5.6 | Docking system | Unified bottom dock with 7 tabs |
| 6 | 6.1-6.12 | AI workspace | Organized AI features with collapsible sections |
| 7 | 7.1-7.8 | Performance | <100ms load, 60fps, <150MB memory |
| 8 | 8.1-8.8 | Visual polish | Professional design, smooth animations |
| 9 | 9.1-9.10 | QA and integration | Production-ready IDE |

---

## Next Steps

1. Review the task list and approve the implementation order
2. Begin Phase 1 (Core Infrastructure) to establish the foundation
3. Execute tasks in dependency order within each phase
4. Run integration tests after each phase completion
5. Continue through Phase 9 for final QA

**Note**: This implementation plan is a roadmap for a professional software team. Each task is designed to be self-contained and testable, with clear acceptance criteria derived from the requirements document.