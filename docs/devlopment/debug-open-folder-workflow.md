# Debug Session: open-folder-workflow
- **Status**: [OPEN]
- **Issue**: Open Folder should load the workspace, populate the explorer, open files in the editor, hide the welcome screen, and support saving, but the current IDE stops somewhere in that workflow.
- **Debug Server**: pending
- **Log File**: .dbg/trae-debug-log-open-folder-workflow.ndjson

## Reproduction Steps
1. Launch MyCodingMaster.
2. Click `Open Folder`.
3. Select a project directory.
4. Observe workspace loading, explorer population, file open behavior, welcome screen visibility, and save behavior.

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | The Open Folder action is not connected to the correct workspace-loading slot or command path. | High | Low | Pending |
| B | `WorkspaceManager` loads state, but downstream EventBus publication or signal propagation never reaches explorer/dashboard/status consumers. | High | Medium | Pending |
| C | The project scanner builds data, but the explorer model is never refreshed with the real filesystem tree. | High | Medium | Pending |
| D | The editor/open-file path works independently, but explorer interaction is broken by missing callbacks, selection handling, or double-click wiring. | Medium | Medium | Pending |
| E | The welcome/dashboard visibility logic does not react to workspace/file-open state transitions, so the IDE remains in an unusable shell state. | Medium | Low | Pending |

## Log Evidence
[Awaiting instrumentation and runtime evidence]

## Verification Conclusion
[Pending]
