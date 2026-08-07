# AI Engineering Workspace Redesign — Technical Design

## Overview

This document provides the technical implementation plan for the AI Engineering Workspace redesign based on the requirements in `requirements.md`.

## Architecture

### Component Breakdown

```
ai_workspace/
├── workspace_panel.py          # Main container with layout structure
├── always_visible/
│   ├── current_task.py        # Current task display with status
│   ├── progress.py            # Progress bar and steps
│   ├── conversation.py        # Chat-style conversation panel
│   ├── prompt_input.py        # User input field with quick actions
│   └── context.py             # Context Inspector & token usage
├── collapsible/
│   ├── execution_plan.py      # Step-by-step execution plan
│   ├── pending_changes.py     # File changes preview & approval
│   ├── verification.py        # Verification results dashboard
│   ├── running_tools.py       # Active tool indicators
│   ├── models.py              # Model dashboard & selector
│   ├── memory.py              # Workspace memory & preferences
│   ├── logs.py                # AI activity timeline
│   └── statistics.py          # Project intelligence panel
├── quick_actions/
│   └── actions_panel.py       # One-click task generators
└── event_handlers.py          # EventBus subscriptions
```

### State Management

```python
# ai_workspace/state.py
class WorkspaceState:
    """Tracks workspace state for persistence."""
    
    def __init__(self):
        self.section_expansion = {}  # section_id -> is_expanded
        self.last_session = {}
    
    def save(self):
        """Persist state to config."""
        pass
    
    def restore(self):
        """Restore state from config."""
        pass
```

### EventBus Messages

| Event | Payload | Description |
|-------|---------|-------------|
| `ai_task_started` | `{task_id, title, status}` | AI begins new task |
| `ai_task_progress` | `{task_id, progress, total_steps, current_step}` | Task progress update |
| `ai_task_completed` | `{task_id, success, error}` | Task completion result |
| `ai_context_updated` | `{files, token_count, budget}` | Context change |
| `ai_model_selected` | `{model_id, provider, reason}` | Model change |
| `ai_tool_started` | `{tool_name, task_id}` | Tool execution begins |
| `ai_tool_completed` | `{tool_name, status}` | Tool execution ends |
| `ai_verification_status` | `{category, status, details}` | Verification result |
| `ai_pending_changes` | `{modified, added, deleted}` | Files pending approval |

## Component Design

### 1. Main Workspace Panel

```python
# ai_workspace/workspace_panel.py
class AIEngineeringWorkspace(QWidget):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.state = WorkspaceState()
        
        self.setup_ui()
        self.connect_events()
        self.state.restore()
    
    def setup_ui(self):
        """Build layout with always-visible and collapsible sections."""
        main_layout = QVBoxLayout(self)
        
        # Always visible sections
        self.current_task = CurrentTaskSection()
        self.progress = ProgressSection()
        self.conversation = ConversationSection()
        self.prompt_input = PromptInputSection()
        self.context = ContextSection()
        
        main_layout.addWidget(self.current_task)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.conversation)
        main_layout.addWidget(self.prompt_input)
        main_layout.addWidget(self.context)
        
        # Collapsible sections
        self.advanced_section = CollapsibleSection("Advanced")
        self.advanced_section.add_section(ExecutionPlanSection())
        self.advanced_section.add_section(PendingChangesSection())
        self.advanced_section.add_section(VerificationSection())
        self.advanced_section.add_section(RunningToolsSection())
        self.advanced_section.add_section(ModelDashboard())
        self.advanced_section.add_section(WorkspaceMemorySection())
        self.advanced_section.add_section(AITimeline())
        self.advanced_section.add_section(ProjectIntelligencePanel())
        
        main_layout.addWidget(self.advanced_section)
```

### 2. Current Task Section

```python
# ai_workspace/always_visible/current_task.py
class CurrentTaskSection(QWidget):
    """Shows current active task with status."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._connect_events()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.task_title = QLabel("No active task")
        self.task_title.setObjectName("taskTitle")
        
        self.task_status = QLabel()
        self.task_status.setObjectName("taskStatus")
        
        layout.addWidget(self.task_title)
        layout.addWidget(self.task_status)
    
    def _connect_events(self):
        self.event_bus.subscribe("ai_task_started", self._on_task_started)
        self.event_bus.subscribe("ai_task_progress", self._on_task_progress)
        self.event_bus.subscribe("ai_task_completed", self._on_task_completed)
    
    def _on_task_started(self, data):
        self.task_title.setText(data.get("title", "Unknown task"))
        self.task_status.setText("Starting...")
```

### 3. Progress Section

```python
# ai_workspace/always_visible/progress.py
class ProgressSection(QWidget):
    """Shows task progress with visual bar."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.step_label = QLabel("Step 0 of 0")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.step_label)
    
    def update_progress(self, current: int, total: int, step: str = ""):
        """Update progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)
        
        self.progress_bar.setValue(percentage)
        self.step_label.setText(f"Step {current}/{total} — {step}")
```

### 4. Conversation Section

```python
# ai_workspace/always_visible/conversation.py
class ConversationSection(QWidget):
    """Chat-style conversation panel."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.messages_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        layout.addWidget(self.scroll_area)
```

### 5. Prompt Input Section

```python
# ai_workspace/always_visible/prompt_input.py
class PromptInputSection(QWidget):
    """User input field with quick actions."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Quick actions toolbar
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(4)
        
        for action in ["Explain", "Refactor", "Optimize", "Tests"]:
            btn = QPushButton(action)
            btn.setObjectName("quickAction")
            btn.clicked.connect(lambda _, a=action: self._quick_action(a))
            quick_actions.addWidget(btn)
        
        # Input field
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Enter your request...")
        self.input_field.setMaximumHeight(100)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_prompt)
        
        layout.addLayout(quick_actions)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_button)
```

### 6. Context Section

```python
# ai_workspace/always_visible/context.py
class ContextSection(QWidget):
    """Shows context files and token usage."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Token budget bar
        budget_layout = QHBoxLayout()
        self.token_label = QLabel("Tokens: 0/100000")
        
        self.budget_bar = QProgressBar()
        self.budget_bar.setRange(0, 100000)
        self.budget_bar.setValue(0)
        self.budget_bar.setTextVisible(False)
        
        budget_layout.addWidget(self.token_label)
        budget_layout.addWidget(self.budget_bar)
        layout.addLayout(budget_layout)
        
        # Context files list
        self.files_list = QListWidget()
        self.files_list.itemClicked.connect(self._on_file_selected)
        layout.addWidget(self.files_list)
        
        # Reason display
        self.reason_label = QLabel()
        self.reason_label.setWordWrap(True)
        layout.addWidget(self.reason_label)
```

### 7. Execution Plan Section

```python
# ai_workspace/collapsible/execution_plan.py
class ExecutionPlanSection(QWidget):
    """Shows step-by-step execution plan."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.steps_list = QListWidget()
        layout.addWidget(self.steps_list)
    
    def update_plan(self, steps: list):
        """Update execution plan."""
        self.steps_list.clear()
        for i, step in enumerate(steps, 1):
            item = QListWidgetItem(f"{i}. {step}")
            self.steps_list.addItem(item)
```

### 8. Pending Changes Section

```python
# ai_workspace/collapsible/pending_changes.py
class PendingChangesSection(QWidget):
    """Shows files pending approval."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Risk indicator
        risk_layout = QHBoxLayout()
        self.risk_label = QLabel("Risk: Low")
        risk_layout.addWidget(self.risk_label)
        layout.addLayout(risk_layout)
        
        # File lists
        self.modified_list = QListWidget()
        self.added_list = QListWidget()
        self.deleted_list = QListWidget()
        
        layout.addWidget(QLabel("Modified:"))
        layout.addWidget(self.modified_list)
        layout.addWidget(QLabel("Added:"))
        layout.addWidget(self.added_list)
        layout.addWidget(QLabel("Deleted:"))
        layout.addWidget(self.deleted_list)
        
        # Approval buttons
        buttons = QHBoxLayout()
        self.approve_button = QPushButton("Approve")
        self.approve_button.clicked.connect(self._approve_changes)
        self.reject_button = QPushButton("Reject")
        self.reject_button.clicked.connect(self._reject_changes)
        buttons.addWidget(self.approve_button)
        buttons.addWidget(self.reject_button)
        layout.addLayout(buttons)
```

### 9. Verification Section

```python
# ai_workspace/collapsible/verification.py
class VerificationSection(QWidget):
    """Shows verification results dashboard."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        
        categories = ["Formatting", "Lint", "Build", "Tests", "Security", "Performance"]
        self.status_indicators = {}
        
        for i, category in enumerate(categories):
            label = QLabel(category)
            indicator = QLabel()
            indicator.setObjectName("verificationIndicator")
            
            layout.addWidget(label, i, 0)
            layout.addWidget(indicator, i, 1)
            
            self.status_indicators[category] = indicator
    
    def update_status(self, category: str, status: str, details: str = ""):
        """Update verification status for a category."""
        indicator = self.status_indicators.get(category)
        if indicator:
            indicator.setText(status)
            indicator.setToolTip(details)
```

### 10. Running Tools Section

```python
# ai_workspace/collapsible/running_tools.py
class RunningToolsSection(QWidget):
    """Shows active tool indicators."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        self.tools_container = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_container)
        self.tools_layout.setAlignment(Qt.AlignTop)
        
        layout.addWidget(self.tools_container)
    
    def add_tool(self, tool_name: str, task_id: str):
        """Add running tool indicator."""
        tool_item = QLabel(f"Tool: {tool_name} (Task: {task_id})")
        tool_item.setProperty("status", "running")
        self.tools_layout.addWidget(tool_item)
    
    def update_tool_status(self, tool_name: str, status: str):
        """Update tool status."""
        for i in range(self.tools_layout.count()):
            item = self.tools_layout.itemAt(i).widget()
            if item and item.text().startswith(f"Tool: {tool_name}"):
                item.setProperty("status", status)
                item.style().polish(item)
```

### 11. Model Dashboard

```python
# ai_workspace/collapsible/models.py
class ModelDashboard(QWidget):
    """Shows current model and performance metrics."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Current model
        model_layout = QHBoxLayout()
        self.model_label = QLabel("Model: Qwen3 Coder Next")
        model_layout.addWidget(self.model_label)
        layout.addLayout(model_layout)
        
        # Reason
        reason_layout = QHBoxLayout()
        self.reason_label = QLabel("Reason: Best for current task")
        reason_layout.addWidget(self.reason_label)
        layout.addLayout(reason_layout)
        
        # Context size
        context_layout = QHBoxLayout()
        self.context_label = QLabel("Context: 45000/100000")
        context_layout.addWidget(self.context_label)
        layout.addLayout(context_layout)
        
        # Cost
        cost_layout = QHBoxLayout()
        self.cost_label = QLabel("Cost: $0.0023")
        cost_layout.addWidget(self.cost_label)
        layout.addLayout(cost_layout)
        
        # Response time
        time_layout = QHBoxLayout()
        self.time_label = QLabel("Avg Response: 2.3s")
        time_layout.addWidget(self.time_label)
        layout.addLayout(time_layout)
```

### 12. Workspace Memory Section

```python
# ai_workspace/collapsible/memory.py
class WorkspaceMemorySection(QWidget):
    """Shows workspace memory and preferences."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Coding style
        style_layout = QHBoxLayout()
        self.style_label = QLabel("Coding Style: PEP 8")
        style_layout.addWidget(self.style_label)
        layout.addLayout(style_layout)
        
        # Architecture summary
        arch_layout = QHBoxLayout()
        self.arch_label = QLabel("Architecture: MVC")
        arch_layout.addWidget(self.arch_label)
        layout.addLayout(arch_layout)
        
        # Naming conventions
        naming_layout = QHBoxLayout()
        self.naming_label = QLabel("Naming: snake_case")
        naming_layout.addWidget(self.naming_label)
        layout.addLayout(naming_layout)
        
        # Framework preferences
        framework_layout = QHBoxLayout()
        self.framework_label = QLabel("Frameworks: PySide6, FastAPI")
        framework_layout.addWidget(self.framework_label)
        layout.addLayout(framework_layout)
```

### 13. AI Activity Timeline

```python
# ai_workspace/collapsible/logs.py
class AITimeline(QWidget):
    """Shows AI activity log."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.timeline_list = QListWidget()
        layout.addWidget(self.timeline_list)
    
    def add_entry(self, timestamp: str, action: str, status: str):
        """Add timeline entry."""
        item = QListWidgetItem(f"{timestamp} — {action} ({status})")
        item.setProperty("status", status)
        self.timeline_list.addItem(item)
        self.timeline_list.scrollToBottom()
```

### 14. Project Intelligence Panel

```python
# ai_workspace/collapsible/statistics.py
class ProjectIntelligencePanel(QWidget):
    """Shows project characteristics and health."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        
        self.stats = {
            "Framework": QLabel("PySide6"),
            "Languages": QLabel("Python"),
            "Branch": QLabel("main"),
            "Open Files": QLabel("3"),
            "Module": QLabel("ai_workspace"),
            "Changed Files": QLabel("1"),
            "Dependencies": QLabel("12"),
            "Health Score": QLabel("87%"),
            "AI Confidence": QLabel("92%"),
        }
        
        row = 0
        for label_name, label_widget in self.stats.items():
            layout.addWidget(QLabel(label_name + ":"), row, 0)
            layout.addWidget(label_widget, row, 1)
            row += 1
    
    def update_stats(self, stats: dict):
        """Update project statistics."""
        for name, value in stats.items():
            if name in self.stats:
                self.stats[name].setText(str(value))
```

### 15. Quick Actions Panel

```python
# ai_workspace/quick_actions/actions_panel.py
class QuickActionsPanel(QWidget):
    """One-click task generators."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(4)
        
        actions = [
            ("Explain Code", "explain_code"),
            ("Refactor", "refactor"),
            ("Optimize", "optimize"),
            ("Generate Tests", "generate_tests"),
            ("Generate Docs", "generate_docs"),
            ("Review Arch", "review_arch"),
            ("Analyze Perf", "analyze_perf"),
            ("Find Dead Code", "find_dead_code"),
            ("Unused Imports", "find_unused"),
            ("Commit Msg", "commit_msg"),
            ("Changelog", "changelog"),
            ("TODO List", "todo_list"),
            ("Summarize", "summarize"),
            ("Estimate Risk", "estimate_risk"),
            ("Security Review", "security_review"),
            ("Accessibility", "accessibility"),
            ("Dependencies", "dependencies"),
            ("Health Check", "health_check"),
        ]
        
        row = 0
        col = 0
        for action_name, action_id in actions:
            btn = QPushButton(action_name)
            btn.setObjectName("quickAction")
            btn.clicked.connect(lambda _, a=action_id: self._trigger_action(a))
            
            layout.addWidget(btn, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
    
    def _trigger_action(self, action_id: str):
        """Trigger quick action task."""
        self.event_bus.publish("ai_quick_action", {"action_id": action_id})
```

## Event Handlers

```python
# ai_workspace/event_handlers.py
class WorkspaceEventHandlers:
    """Subscribes to EventBus messages and updates UI."""
    
    def __init__(self, workspace: AIEngineeringWorkspace):
        self.workspace = workspace
        self._subscriptions = []
        self._connect_events()
    
    def _connect_events(self):
        """Connect all EventBus events."""
        events = [
            ("ai_task_started", self._on_task_started),
            ("ai_task_progress", self._on_task_progress),
            ("ai_task_completed", self._on_task_completed),
            ("ai_context_updated", self._on_context_updated),
            ("ai_model_selected", self._on_model_selected),
            ("ai_tool_started", self._on_tool_started),
            ("ai_tool_completed", self._on_tool_completed),
            ("ai_verification_status", self._on_verification_status),
            ("ai_pending_changes", self._on_pending_changes),
        ]
        
        for event, handler in events:
            self._subscriptions.append(
                self.workspace.event_bus.subscribe(event, handler)
            )
    
    def _on_task_started(self, data):
        self.workspace.current_task._on_task_started(data)
        self.workspace.progress.update_progress(0, data.get("total_steps", 0))
    
    def _on_task_progress(self, data):
        self.workspace.progress.update_progress(
            data.get("current_step", 0),
            data.get("total_steps", 0),
            data.get("step_description", "")
        )
    
    def _on_task_completed(self, data):
        self.workspace.progress.update_progress(100, 100, "Completed")
    
    def _on_context_updated(self, data):
        self.workspace.context.update_context(
            data.get("files", []),
            data.get("token_count", 0),
            data.get("budget", 100000)
        )
    
    def _on_model_selected(self, data):
        self.workspace.models.update_model(
            data.get("model_id"),
            data.get("reason")
        )
    
    def _on_tool_started(self, data):
        self.workspace.running_tools.add_tool(
            data.get("tool_name"),
            data.get("task_id")
        )
    
    def _on_tool_completed(self, data):
        self.workspace.running_tools.update_tool_status(
            data.get("tool_name"),
            data.get("status")
        )
    
    def _on_verification_status(self, data):
        self.workspace.verification.update_status(
            data.get("category"),
            data.get("status"),
            data.get("details", "")
        )
    
    def _on_pending_changes(self, data):
        self.workspace.pending_changes.update_changes(
            data.get("modified", []),
            data.get("added", []),
            data.get("deleted", [])
        )
```

## Styling

```python
# ai_workspace/styles.py
DARK_STYLESHEET = """
/* Main Panel */
AIEngineeringWorkspace {
    background-color: #0D0D0F;
    color: #E2E2E6;
    font-family: Inter, sans-serif;
}

/* Section Headers */
QCollapsible::header {
    background-color: #1C1C1F;
    border: 1px solid #252528;
    border-radius: 3px;
    padding: 8px;
    font-weight: bold;
}

QCollapsible::header:hover {
    background-color: #252528;
}

QCollapsible::header::indicator {
    width: 16px;
    height: 16px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #252528;
    border-radius: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 2px;
}

/* Token Budget Bar */
#tokenBudgetBar::chunk {
    background-color: #22C55E;  /* Green for low usage */
}

#tokenBudgetBar::chunk[usage="60-85%"] {
    background-color: #F59E0B;  /* Yellow for medium usage */
}

#tokenBudgetBar::chunk[usage=">85%"] {
    background-color: #EF4444;  /* Red for high usage */
}

/* Quick Action Buttons */
#quickAction {
    background-color: #1C1C1F;
    border: 1px solid #252528;
    border-radius: 3px;
    padding: 4px 8px;
    color: #E2E2E6;
}

#quickAction:hover {
    background-color: #252528;
}

#quickAction:pressed {
    background-color: #303036;
}

/* Task Status Indicators */
#taskStatus {
    color: #60A5FA;  /* Blue for info */
}

#taskStatus[status="success"] {
    color: #22C55E;
}

#taskStatus[status="error"] {
    color: #EF4444;
}

/* Verification Indicators */
#verificationIndicator {
    padding: 2px 6px;
    border-radius: 2px;
}

#verificationIndicator[status="pass"] {
    background-color: #14532D;
    color: #4ADE80;
}

#verificationIndicator[status="fail"] {
    background-color: #7F1D1D;
    color: #F87171;
}

#verificationIndicator[status="pending"] {
    background-color: #4C1D95;
    color: #C084FC;
}

/* Scroll Areas */
QScrollArea {
    background-color: #111113;
    border: 1px solid #252528;
    border-radius: 3px;
}

/* Tool Tips */
QToolTip {
    background-color: #161618;
    color: #E2E2E6;
    border: 1px solid #252528;
    border-radius: 3px;
    padding: 4px 8px;
}
"""

LIGHT_STYLESHEET = """
/* Similar structure but with light theme colors */
AIEngineeringWorkspace {
    background-color: #F5F5F7;
    color: #111113;
}
/* ... rest of light theme styles ... */
"""
```

## Testing Strategy

### Unit Tests

```python
# tests/test_ai_workspace.py
def test_current_task_updates_on_start():
    """Test current task displays correctly on task start."""
    task_section = CurrentTaskSection()
    task_section._on_task_started({
        "task_id": "task-123",
        "title": "Refactor auth module",
        "status": "running"
    })
    
    assert task_section.task_title.text() == "Refactor auth module"
    assert task_section.task_status.text() == "Starting..."


def test_progress_bar_updates():
    """Test progress bar shows correct percentage."""
    progress = ProgressSection()
    progress.update_progress(5, 10, "Parsing files")
    
    assert progress.progress_bar.value() == 50
    assert "Parsing files" in progress.step_label.text()


def test_context_section_updates():
    """Test context section displays files and tokens."""
    context = ContextSection()
    context.update_context(
        files=["src/main.py", "src/utils.py"],
        token_count=45000,
        budget=100000
    )
    
    assert context.token_label.text() == "Tokens: 45000/100000"
    assert context.budget_bar.value() == 45


def test_verification_updates():
    """Test verification section updates correctly."""
    verification = VerificationSection()
    verification.update_status("Tests", "pass", "42 tests passed")
    
    assert verification.status_indicators["Tests"].text() == "pass"
    assert verification.status_indicators["Tests"].toolTip() == "42 tests passed"
```

### Integration Tests

```python
# tests/test_integration.py
def test_workspace_event_handlers():
    """Test event handlers update UI correctly."""
    event_bus = EventBus()
    workspace = AIEngineeringWorkspace(event_bus)
    handlers = WorkspaceEventHandlers(workspace)
    
    # Publish a task start event
    event_bus.publish("ai_task_started", {
        "task_id": "task-456",
        "title": "Add logging",
        "total_steps": 3
    })
    
    # Verify UI updates
    assert workspace.current_task.task_title.text() == "Add logging"
    assert workspace.progress.progress_bar.value() == 0


def test_collapsible_sections():
    """Test collapsible sections remember state."""
    workspace = AIEngineeringWorkspace(EventBus())
    
    # Expand a section
    workspace.advanced_section.expand("Verification")
    
    # Save state
    workspace.state.save()
    
    # Restore state
    new_workspace = AIEngineeringWorkspace(EventBus())
    new_workspace.state.restore()
    
    assert new_workspace.advanced_section.is_expanded("Verification")
```

## Performance Considerations

1. **Lazy Loading**: Load collapsible section content only when expanded
2. **Virtual Scrolling**: Use custom scroll areas for long lists
3. **Throttling**: Debounce rapid EventBus messages
4. **Background Threads**: Heavy operations in background threads
5. **Caching**: Cache rendered UI elements

## Implementation Priority

1. **Phase 1**: Core layout and always-visible sections (current task, progress, conversation)
2. **Phase 2**: Context Inspector and prompt input
3. **Phase 3**: Collapsible sections one at a time
4. **Phase 4**: Event handlers and data flow
5. **Phase 5**: Styling and polish
6. **Phase 6**: Testing and performance optimization

## Migration from v0.4

The current AI workspace has 11 sections crowded into one panel. This redesign:

- Keeps essential info always visible (5 sections)
- Moves advanced options to collapsible section
- Maintains EventBus communication pattern
- Preserves existing module architecture
- Adds no new backend systems