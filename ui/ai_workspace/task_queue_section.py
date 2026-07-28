"""Task Queue Section - Displays all pending and active tasks"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QFrame)
from PySide6.QtCore import Qt


class TaskQueueSection(QWidget):
    """Display pending, running, and completed tasks."""
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._tasks = {}  # task_id -> task_data
        self.setup_ui()
        self._subscribe_events()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(8)
        
        # Header with counts
        header = QHBoxLayout()
        self._pending_lbl = QLabel("Pending: 0")
        self._pending_lbl.setStyleSheet("color: #F59E0B; font-size: 10px; font-weight: 600;")
        self._running_lbl = QLabel("Running: 0")
        self._running_lbl.setStyleSheet("color: #3B82F6; font-size: 10px; font-weight: 600;")
        self._done_lbl = QLabel("Done: 0")
        self._done_lbl.setStyleSheet("color: #22C55E; font-size: 10px; font-weight: 600;")
        header.addWidget(self._pending_lbl)
        header.addWidget(self._running_lbl)
        header.addWidget(self._done_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Scroll area for task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent; border: none;")
        self.scroll.setFixedHeight(200)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.task_list_layout = QVBoxLayout(self.container)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list_layout.setSpacing(4)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
    def _subscribe_events(self):
        """Subscribe to execution events."""
        self.event_bus.subscribe("execution_task_created", self._on_task_created)
        self.event_bus.subscribe("execution_task_started", self._on_task_started)
        self.event_bus.subscribe("execution_task_completed", self._on_task_completed)
        self.event_bus.subscribe("execution_task_failed", self._on_task_failed)
        self.event_bus.subscribe("execution_task_cancelled", self._on_task_cancelled)
        self.event_bus.subscribe("execution_status_update", self._on_status_update)
        
    def _on_task_created(self, data):
        """Handle task created event."""
        task_id = data.get("task_id", "")
        title = data.get("title", "Unknown Task")
        group = data.get("group", None)
        dependencies = data.get("dependencies", [])
        
        self._tasks[task_id] = {
            "title": title,
            "state": "pending",
            "group": group,
            "dependencies": dependencies,
            "widget": None
        }
        self._add_task_widget(task_id)
        self._update_counts()
        
    def _on_task_started(self, data):
        """Handle task started event."""
        task_id = data.get("task_id", "")
        if task_id in self._tasks:
            self._tasks[task_id]["state"] = "running"
            self._update_task_widget(task_id)
            self._update_counts()
        
    def _on_task_completed(self, data):
        """Handle task completed event."""
        task_id = data.get("task_id", "")
        if task_id in self._tasks:
            self._tasks[task_id]["state"] = "completed"
            self._update_task_widget(task_id)
            self._update_counts()
        
    def _on_task_failed(self, data):
        """Handle task failed event."""
        task_id = data.get("task_id", "")
        if task_id in self._tasks:
            self._tasks[task_id]["state"] = "failed"
            self._update_task_widget(task_id)
            self._update_counts()
        
    def _on_task_cancelled(self, data):
        """Handle task cancelled event."""
        task_id = data.get("task_id", "")
        if task_id in self._tasks:
            self._tasks[task_id]["state"] = "cancelled"
            self._update_task_widget(task_id)
            self._update_counts()
            
    def _on_status_update(self, data):
        """Handle execution status update."""
        # Refresh counts from engine status
        self._update_counts()
        
    def _add_task_widget(self, task_id: str):
        """Add a task widget to the list."""
        task_data = self._tasks[task_id]
        
        item = QWidget()
        item.setObjectName("TaskItem")
        row = QHBoxLayout(item)
        row.setContentsMargins(6, 4, 6, 4)
        
        # Status indicator
        status_dot = QLabel("●")
        status_dot.setFixedWidth(12)
        status_dot.setAlignment(Qt.AlignCenter)
        
        # Task title
        title_lbl = QLabel(task_data["title"][:40])
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("color: #E2E2E6; font-size: 11px;")
        
        # Task ID
        id_lbl = QLabel(task_id[:8])
        id_lbl.setStyleSheet("color: #52525C; font-size: 9px;")
        
        # Group badge (if any)
        group_badge = None
        if task_data["group"]:
            group_badge = QLabel(f"[{task_data['group'][:10]}]")
            group_badge.setStyleSheet("""
                color: #A78BFA;
                font-size: 9px;
                background-color: #2D1B4E;
                padding: 1px 4px;
                border-radius: 2px;
            """)
        
        # Dependencies indicator
        dep_badge = None
        if task_data["dependencies"]:
            dep_badge = QLabel(f"⇦ {len(task_data['dependencies'])}")
            dep_badge.setStyleSheet("color: #F59E0B; font-size: 9px;")
            dep_badge.setToolTip(f"Depends on {len(task_data['dependencies'])} task(s)")
        
        row.addWidget(status_dot)
        row.addWidget(title_lbl, stretch=1)
        if group_badge:
            row.addWidget(group_badge)
        if dep_badge:
            row.addWidget(dep_badge)
        row.addWidget(id_lbl)
        
        # Store widget reference
        task_data["widget"] = item
        task_data["status_dot"] = status_dot
        
        self.task_list_layout.addWidget(item)
        self._update_task_widget(task_id)
        
    def _update_task_widget(self, task_id: str):
        """Update task widget styling based on state."""
        if task_id not in self._tasks:
            return
            
        task_data = self._tasks[task_id]
        state = task_data["state"]
        status_dot = task_data.get("status_dot")
        widget = task_data.get("widget")
        
        if not status_dot or not widget:
            return
        
        # State-based styling
        colors = {
            "pending": ("#F59E0B", "#1C1C1F"),
            "running": ("#3B82F6", "#1E2533"),
            "completed": ("#22C55E", "#14532D"),
            "failed": ("#EF4444", "#450A0A"),
            "cancelled": ("#8E8E98", "#1C1C1F")
        }
        
        dot_color, bg_color = colors.get(state, ("#52525C", "#1C1C1F"))
        
        status_dot.setStyleSheet(f"color: {dot_color}; font-size: 14px;")
        widget.setStyleSheet(f"""
            #TaskItem {{
                background-color: {bg_color};
                border: 1px solid #252528;
                border-radius: 3px;
            }}
            #TaskItem:hover {{
                border-color: {dot_color};
            }}
        """)
        
    def _update_counts(self):
        """Update the header count labels."""
        pending = sum(1 for t in self._tasks.values() if t["state"] == "pending")
        running = sum(1 for t in self._tasks.values() if t["state"] == "running")
        done = sum(1 for t in self._tasks.values() if t["state"] in ["completed", "failed", "cancelled"])
        
        self._pending_lbl.setText(f"Pending: {pending}")
        self._running_lbl.setText(f"Running: {running}")
        self._done_lbl.setText(f"Done: {done}")
