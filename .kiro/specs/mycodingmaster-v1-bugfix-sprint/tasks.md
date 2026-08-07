# Implementation Plan - MyCodingMaster v1.0 Bugfix Sprint

## Phase 1: Workspace & Explorer Fix

- [ ] 1.1 Write bug condition exploration test - Explorer Empty Bug
  - **Property 1: Bug Condition** - Explorer Empty on Project Open
  - **IMPORTANT**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Test Approach**: Simulate workspace opening event, verify Explorer tree is populated
    - Open a project with known files (e.g., current mycodingmaster project with ~46 files)
    - Assert Explorer QTreeWidget.itemCount > 0 after workspace_loaded event
    - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - **Expected Counterexamples**: Explorer shows 0 items even though ProjectScanner found files
  - **Document counterexamples found** to understand root cause
  - **Mark task complete** when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [ ] 1.2 Write preservation property tests - Explorer Preservation (BEFORE implementing fix)
  - **Property 2: Preservation** - Explorer Tree Navigation
  - **IMPORTANT**: Follow observation-first methodology
  - **Observe behavior on UNFIXED code** for working scenarios:
    - Theme toggling still works (dark/light mode)
    - Existing editor tabs can be closed, switched, saved
    - NavigationRail panel switching works
    - Keyboard shortcuts still function
  - **Write property-based tests** capturing observed behavior patterns
  - **Property-based testing** generates many test cases for stronger guarantees
  - **Run tests on UNFIXED code** - expect PASS (this confirms baseline behavior to preserve)
  - **Mark task complete** when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 1.3 Fix Explorer Population
  - _Bug_Condition: isBugCondition(input) where input.event_type = "workspace_loaded" and tree is empty_
  - _Expected_Behavior: Explorer shows tree with files/folders, expand/collapse works_
  - _Preservation: Theme, tabs, rail navigation, shortcuts remain unchanged_
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 1.3.1 Update ProjectPanel.handle_workspace_loaded() in ui/project_panel.py
    - Add `self.tree.clear()` before rebuilding (prevents duplicate entries)
    - Add error handling for None/empty context.tree
    - Set root_item.setExpanded(True) by default
    - Add logger.debug for troubleshooting
    - _Bug_Condition: context.tree may be None or empty_
    - _Expected_Behavior: tree shows files/folders with expand/collapse_

  - [ ] 1.3.2 Update ProjectPanel.handle_item_double_clicked() in ui/project_panel.py
    - Add validation for path exists before publishing
    - Add logger.debug for debugging
    - Ensure path data is stored correctly in tree items
    - _Bug_Condition: double-click may not publish file_selected event_
    - _Expected_Behavior: file_selected event with correct path_

  - [ ] 1.3.3 Update CenterPanel to subscribe to file_selected in ui/center_panel.py
    - Add event bus subscription in __init__
    - Implement _on_file_selected() handler
    - Extract path from event data, read file, open editor tab
    - Add error handling for file read errors
    - _Bug_Condition: no handler for file_selected event_
    - _Expected_Behavior: file opens in editor tab with content_

  - [ ] 1.3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Explorer Population Fixed
    - **IMPORTANT**: Re-run the SAME test from task 1.1 - do NOT write a new test
    - The test from task 1.1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 1.3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Explorer Tree Navigation
    - **IMPORTANT**: Re-run the SAME tests from task 1.2 - do NOT write new tests
    - Run preservation property tests from step 1.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

## Phase 2: Editor File Opening Fix

- [ ] 2.1 Write editor opening bug condition test
  - **Property 1: Bug Condition** - Editor File Opening
  - **IMPORTANT**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **GOAL**: Surface counterexamples that demonstrate double-click doesn't open editor
  - **Test Approach**: Simulate double-click on file tree item, verify EditorTabs opens
    - Open a project and navigate to file in tree
    - Simulate double-click on file item
    - Assert EditorTabs count >= 1 after double-click
    - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - **Expected Counterexamples**: Double-click on file doesn't create editor tab
  - **Document counterexamples found** to understand root cause
  - **Mark task complete** when test is written, run, and failure is documented
  - _Requirements: 1.3, 2.4_

- [ ] 2.2 Write editor preservation tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Editor Tabs
  - **IMPORTANT**: Follow observation-first methodology
  - **Observe behavior on UNFIXED code** for working scenarios:
    - Existing editor tabs can be closed, switched, saved
    - Multiple tabs work correctly
    - Unsaved indicator (*) works
    - Tab switching works
  - **Write property-based tests** capturing observed behavior patterns
  - **Run tests on UNFIXED code** - expect PASS (this confirms baseline behavior to preserve)
  - **Mark task complete** when tests are written, run, and passing on unfixed code
  - _Requirements: 3.2_

- [ ] 2.3 Fix Editor File Opening
  - _Bug_Condition: isBugCondition where double-click on file doesn't publish file_selected_
  - _Expected_Behavior: double-click opens editor tab with file content_
  - _Preservation: Existing editor tabs, close, switch, save remain unchanged_
  - _Requirements: 1.3, 2.4, 3.2_

  - [ ] 2.3.1 Verify ProjectPanel handles double-click correctly
    - Already fixed in task 1.3.2 (handle_item_double_clicked)
    - Ensure file_selected event is published with correct path
    - _Bug_Condition: double-click may not publish file_selected event_
    - _Expected_Behavior: file_selected event with correct path_

  - [ ] 2.3.2 Verify CenterPanel handles file_selected correctly
    - Already fixed in task 1.3.3 (_on_file_selected handler)
    - Ensure file content is read and editor tab is opened
    - _Bug_Condition: no handler for file_selected event_
    - _Expected_Behavior: file opens in editor tab with content_

  - [ ] 2.3.3 Verify editor tab opens correctly
    - Open file in EditorTabs
    - Verify content is displayed
    - Verify syntax highlighting is applied
    - Verify editor is editable
    - _Bug_Condition: editor tab may not open or content may not load_
    - _Expected_Behavior: editor tab with editable content_

  - [ ] 2.3.4 Verify bug condition test now passes
    - **Property 1: Expected Behavior** - Editor File Opening Fixed
    - **IMPORTANT**: Re-run the SAME test from task 2.1
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 2.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.4_

  - [ ] 2.3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Editor Tabs
    - **IMPORTANT**: Re-run the SAME tests from task 2.2
    - Run preservation property tests from step 2.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.2_

## Phase 3: Toolbar Button Fix

- [ ] 3.1 Write toolbar button bug condition test
  - **Property 1: Bug Condition** - Dead Toolbar Buttons
  - **IMPORTANT**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **GOAL**: Surface counterexamples that toolbar buttons don't work
  - **Test Approach**: Simulate clicks on each toolbar button, verify event is published
    - For each button (Open, Save, Scan, Run, Stop, Refresh, Settings, Theme):
      - Click the button
      - Assert corresponding event is published
      - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - **Expected Counterexamples**: Toolbar buttons show no response when clicked
  - **Document counterexamples found** to understand root cause
  - **Mark task complete** when test is written, run, and failure is documented
  - _Requirements: 1.5, 2.6_

- [ ] 3.2 Write toolbar preservation tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Toolbar Functionality
  - **IMPORTANT**: Follow observation-first methodology
  - **Observe behavior on UNFIXED code** for working scenarios:
    - Theme toggle still works (if currently working)
    - Run/Stop buttons work (if currently working)
    - UI state remains consistent after button clicks
  - **Write property-based tests** capturing observed behavior patterns
  - **Run tests on UNFIXED code** - expect PASS (this confirms baseline behavior to preserve)
  - **Mark task complete** when tests are written, run, and passing on unfixed code
  - _Requirements: 3.3_

- [ ] 3.3 Fix Toolbar Buttons
  - _Bug_Condition: isBugCondition where toolbar buttons have no connected slots or empty lambdas_
  - _Expected_Behavior: every button either works or shows "Coming Soon"_
  - _Preservation: existing working functionality remains unchanged_
  - _Requirements: 1.5, 2.6, 3.3, 3.4_

  - [ ] 3.3.1 Update TopToolbar to connect save button in ui/top_toolbar.py
    - Connect btn_save.clicked to self._on_save_clicked
    - Implement _on_save_clicked() to publish request_save_current event
    - _Bug_Condition: save button has no connected slot_
    - _Expected_Behavior: save event published when button clicked_

  - [ ] 3.3.2 Update TopToolbar to implement scan button in ui/top_toolbar.py
    - Connect btn_scan.clicked to self._on_scan_clicked
    - Implement _on_scan_clicked() to publish request_scan_workspace event
    - _Bug_Condition: scan button has no connected slot_
    - _Expected_Behavior: scan event published when button clicked_

  - [ ] 3.3.3 Update TopToolbar to add refresh button in ui/top_toolbar.py
    - Add btn_refresh button with text "↻ Refresh"
    - Connect btn_refresh.clicked to self._on_refresh_clicked
    - Implement _on_refresh_clicked() to publish request_scan_workspace event
    - _Bug_Condition: refresh button doesn't exist_
    - _Expected_Behavior: refresh event published when button clicked_

  - [ ] 3.3.4 Update TopToolbar to add settings button in ui/top_toolbar.py
    - Add btn_settings button with icon "⚙"
    - Connect btn_settings.clicked to self._on_settings_clicked
    - Implement _on_settings_clicked() to publish settings_open_requested event
    - _Bug_Condition: settings button doesn't exist_
    - _Expected_Behavior: settings event published when button clicked_

  - [ ] 3.3.5 Update MainWindow to handle toolbar events in ui/main_window.py
    - Connect toolbar.open_project_requested to handle_open_project
    - Connect toolbar.scan_project_requested to _scan_workspace
    - _Bug_Condition: toolbar events may not be subscribed_
    - _Expected_Behavior: events trigger appropriate handlers_

  - [ ] 3.3.6 Verify toolbar bug condition test now passes
    - **Property 1: Expected Behavior** - Toolbar Buttons Fixed
    - **IMPORTANT**: Re-run the SAME test from task 3.1
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 3.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.6_

  - [ ] 3.3.7 Verify toolbar preservation tests still pass
    - **Property 2: Preservation** - Existing Toolbar Functionality
    - **IMPORTANT**: Re-run the SAME tests from task 3.2
    - Run preservation property tests from step 3.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.3, 3.4_

## Phase 4: Status Bar Live Updates Fix

- [ ] 4.1 Write status bar bug condition test
  - **Property 1: Bug Condition** - Status Bar Not Updating
  - **IMPORTANT**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **GOAL**: Surface counterexamples that status bar doesn't update live
  - **Test Approach**: Simulate workspace_loaded event, verify status bar updates
    - Open a project
    - Wait for workspace_loaded event
    - Assert status bar shows workspace path (not "No Workspace")
    - Assert status bar shows current file when editor tab opens
    - Assert status bar shows cursor position when cursor moves
    - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - **Expected Counterexamples**: Status bar shows "No Workspace" after project opens
  - **Document counterexamples found** to understand root cause
  - **Mark task complete** when test is written, run, and failure is documented
  - _Requirements: 1.6, 2.7_

- [ ] 4.2 Write status bar preservation tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Status Bar Functionality
  - **IMPORTANT**: Follow observation-first methodology
  - **Observe behavior on UNFIXED code** for working scenarios:
    - Existing status chips (cursor, language, etc.) work correctly
    - Event subscriptions still function
    - No errors occur during status updates
  - **Write property-based tests** capturing observed behavior patterns
  - **Run tests on UNFIXED code** - expect PASS (this confirms baseline behavior to preserve)
  - **Mark task complete** when tests are written, run, and passing on unfixed code
  - _Requirements: 3.6_

- [ ] 4.3 Fix Status Bar Updates
  - _Bug_Condition: isBugCondition where status bar handlers don't update UI correctly_
  - _Expected_Behavior: status bar updates live with workspace, file, cursor, language, encoding, AI status_
  - _Preservation: existing status chip functionality remains unchanged_
  - _Requirements: 1.6, 2.7, 3.6_

  - [ ] 4.3.1 Update BottomStatusBar._on_workspace() in ui/status_bar.py
    - Verify workspace path is extracted and displayed correctly
    - Add logging for debugging
    - _Bug_Condition: handler may not update workspace path_
    - _Expected_Behavior: workspace path displayed in status bar_

  - [ ] 4.3.2 Update BottomStatusBar._on_cursor() in ui/status_bar.py
    - Verify cursor position is displayed correctly (Ln X, Col Y)
    - Add total lines to display
    - _Bug_Condition: cursor position may not update correctly_
    - _Expected_Behavior: cursor position displayed in status bar_

  - [ ] 4.3.3 Update BottomStatusBar._on_tab_switched() in ui/status_bar.py
    - Verify language detection works correctly
    - Add encoding display (placeholder)
    - _Bug_Condition: language may not update correctly_
    - _Expected_Behavior: language displayed in status bar_

  - [ ] 4.3.4 Verify status bar bug condition test now passes
    - **Property 1: Expected Behavior** - Status Bar Updates Fixed
    - **IMPORTANT**: Re-run the SAME test from task 4.1
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 4.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.7_

  - [ ] 4.3.5 Verify status bar preservation tests still pass
    - **Property 2: Preservation** - Existing Status Bar Functionality
    - **IMPORTANT**: Re-run the SAME tests from task 4.2
    - Run preservation property tests from step 4.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.6_

## Phase 5: Performance & Background Thread Fix

- [ ] 5.1 Write performance bug condition test
  - **Property 1: Bug Condition** - UI Freezing During Operations
  - **IMPORTANT**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **GOAL**: Surface counterexamples that UI freezes during scanning/operations
  - **Test Approach**: Measure UI responsiveness during heavy operations
    - Open a large project (1000+ files)
    - Measure time to complete operation
    - Assert UI remains responsive (no freezes)
    - Assert progress indicators appear during operation
    - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - **Expected Counterexamples**: UI freezes for several seconds during scan
  - **Document counterexamples found** to understand root cause
  - **Mark task complete** when test is written, run, and failure is documented
  - _Requirements: 1.7, 2.8, 7.1_

- [ ] 5.2 Write performance preservation tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Event Bus Threading
  - **IMPORTANT**: Follow observation-first methodology
  - **Observe behavior on UNFIXED code** for working scenarios:
    - EventBus uses threading for background operations
    - UI remains responsive during background tasks
    - Completion events are published correctly
  - **Write property-based tests** capturing observed behavior patterns
  - **Run tests on UNFIXED code** - expect PASS (this confirms baseline behavior to preserve)
  - **Mark task complete** when tests are written, run, and passing on unfixed code
  - _Requirements: 3.4_

- [ ] 5.3 Fix Performance - Background Threading
  - _Bug_Condition: isBugCondition where heavy operations block UI thread_
  - _Expected_Behavior: heavy operations run in background threads, UI remains responsive with progress indicators_
  - _Preservation: existing EventBus threading functionality remains unchanged_
  - _Requirements: 1.7, 2.8, 3.4, 7.1_

  - [ ] 5.3.1 Update WorkspaceManager.open_workspace() in ui/core/workspace_manager.py
    - Move ProjectScanner.scan() to background thread
    - Publish progress events during scan
    - Use QTimer.singleShot to publish workspace_loaded on main thread
    - Add error handling for scan failures
    - _Bug_Condition: scan runs synchronously, blocking UI_
    - _Expected_Behavior: scan runs in background, UI stays responsive_

  - [ ] 5.3.2 Add background task tracking in EventBus
    - Track active background task count
    - Publish task_started and task_completed events
    - Add task_failed event for error handling
    - _Bug_Condition: no tracking of background tasks_
    - _Expected_Behavior: task count displayed in status bar_

  - [ ] 5.3.3 Update Status Bar to show background tasks
    - Add tasks label to status bar (Task 4.3.4 already does this)
    - Update task count when task_started/task_completed events fire
    - _Bug_Condition: task count not displayed_
    - _Expected_Behavior: task count displayed in status bar_

  - [ ] 5.3.4 Verify performance bug condition test now passes
    - **Property 1: Expected Behavior** - Performance Fixed
    - **IMPORTANT**: Re-run the SAME test from task 5.1
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 5.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.8, 7.1_

  - [ ] 5.3.5 Verify performance preservation tests still pass
    - **Property 2: Preservation** - Existing Event Bus Threading
    - **IMPORTANT**: Re-run the SAME tests from task 5.2
    - Run preservation property tests from step 5.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.4_

## Phase 6: Terminal Fix (Placeholder)

- [ ] 6.1 Document terminal requirements (v0.5 deferred)
  - **Property 1: Future Requirement** - Terminal PTY Integration
  - Terminal functionality requires PTY integration (deferred to v0.5 per requirements)
  - Current implementation is stub (QPlainTextEdit placeholder)
  - No PTY process execution exists in v0.4
  - **Requirements**: Open terminal, multiple terminals, stop process, clear, copy, auto scroll, background execution, no UI freezing
  - _Note_: Terminal PTY integration is deferred to v0.5 per Phase 4 requirements in V1.0 spec

## Phase 7: Checkpoint - Ensure All Tests Pass

- [ ] 7.1 Run all tests
  - Ensure all tests pass after all fixes are implemented
  - Verify no regressions in existing functionality
  - Run full test suite if available
  - Report any failing tests and fix them
  - **EXPECTED OUTCOME**: All tests PASS

## Summary

**Total Tasks**: 19 tasks
**Phase 1 (Workspace)**: 5 tasks
**Phase 2 (Editor)**: 5 tasks
**Phase 3 (Toolbar)**: 5 tasks
**Phase 4 (Status Bar)**: 5 tasks
**Phase 5 (Performance)**: 5 tasks
**Phase 6 (Terminal)**: 1 task (placeholder documentation)
**Phase 7 (Checkpoint)**: 1 task

**Key Principles Followed**:
1. Write exploration tests BEFORE implementing fix (Tasks 1.1, 2.1, 3.1, 4.1, 5.1)
2. Run tests on UNFIXED code to understand the bug
3. Write preservation tests BEFORE implementing fix (Tasks 1.2, 2.2, 3.2, 4.2, 5.2)
4. Run same tests after fix to verify (Tasks 1.3.4, 2.3.4, 3.3.6, 4.3.4, 5.3.4)
5. Use property-based testing for stronger guarantees
6. Follow observation-first methodology for preservation tests