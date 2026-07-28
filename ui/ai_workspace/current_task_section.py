"""Current Task Section"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer


class CurrentTaskSection(QWidget):
    """Display the current active task."""
    def __init__(self, event_bus=None):
        super().__init__()
        self.event_bus = event_bus
        self.setup_ui()
        
        # Status update timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_elapsed)
        self._elapsed_seconds = 0
        self._last_update = None
        
        # Subscribe to execution events
        if self.event_bus:
            self._subscribe_events()
        
    def _subscribe_events(self):
        """Subscribe to execution task events."""
        self.event_bus.subscribe("execution_task_started", self._on_task_started)
        self.event_bus.subscribe("execution_task_completed", self._on_task_completed)
        self.event_bus.subscribe("execution_task_failed", self._on_task_failed)
        self.event_bus.subscribe("execution_task_update", self._on_task_update)
        self.event_bus.subscribe("workflow_stage_changed", self._on_stage_changed)
        
    def _on_task_started(self, data):
        """Handle task started event."""
        task_id = data.get("task_id", "")
        self.set_task(f"Task {task_id[:8]}...", "running")
        
    def _on_task_completed(self, data):
        """Handle task completed event."""
        task_id = data.get("task_id", "")
        self.set_task(f"Task {task_id[:8]}... completed", "success")
        
    def _on_task_failed(self, data):
        """Handle task failed event."""
        task_id = data.get("task_id", "")
        error = data.get("error", "Unknown error")
        self.set_task(f"Task {task_id[:8]}... failed: {error[:30]}", "error")
        
    def _on_task_update(self, data):
        """Handle task update event."""
        title = data.get("title", "Unknown Task")
        state = data.get("state", "idle")
        self.set_task(title, state)
        
    def _on_stage_changed(self, data):
        """Handle workflow stage change."""
        stage = data.get("stage", "Unknown")
        self.set_task(stage, "planning")
        
    def setup_ui(self):
        from ui.design_system import get_design_system
        p = get_design_system().palette

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(4)

        self._task_name = QLabel("Idle — no active task")
        self._task_name.setWordWrap(True)
        self._task_name.setStyleSheet(f"""
            color: {p.text};
            font-size: 12px;
            font-weight: 500;
            background-color: transparent;
        """)

        self._status_row = QHBoxLayout()
        self._status_row.setSpacing(6)

        self._status_badge = QLabel("IDLE")
        self._status_badge.setStyleSheet(f"""
            background-color: {p.bg_secondary};
            color: {p.text_tertiary};
            font-size: 9px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 2px;
            letter-spacing: 0.5px;
        """)

        self._elapsed = QLabel("—")
        self._elapsed.setStyleSheet(f"color: {p.text_tertiary}; font-size: 10px; background-color: transparent;")

        self._status_row.addWidget(self._status_badge)
        self._status_row.addWidget(self._elapsed)
        self._status_row.addStretch()

        layout.addWidget(self._task_name)
        layout.addLayout(self._status_row)
        
    def start_timer(self):
        """Start the elapsed time counter."""
        self._elapsed_seconds = 0
        self._last_update = None
        self._status_timer.start(1000)
        self._elapsed.setText("0s")
        
    def stop_timer(self):
        """Stop the elapsed time counter."""
        self._status_timer.stop()
        self._elapsed.setText("—")
        
    def _update_elapsed(self):
        """Update elapsed time display."""
        from datetime import datetime
        if self._last_update is None:
            self._last_update = datetime.now()
            return
            
        now = datetime.now()
        delta = now - self._last_update
        self._elapsed_seconds += int(delta.total_seconds())
        self._last_update = now
        
        # Format as Xh Ym Zs
        hours = self._elapsed_seconds // 3600
        minutes = (self._elapsed_seconds % 3600) // 60
        seconds = self._elapsed_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        self._elapsed.setText(" ".join(parts))
        
    def set_task(self, name: str, status: str = "idle"):
        """Update task display."""
        from ui.design_system import get_design_system
        p = get_design_system().palette

        self._task_name.setText(name)
        statuses = {
            "idle":     ("IDLE",     p.text_tertiary, p.bg_secondary),
            "running":  ("RUNNING",  p.accent,        p.selection),
            "success":  ("DONE",     p.success,       p.success_bg),
            "error":    ("ERROR",    p.error,         p.error_bg),
            "planning": ("PLANNING", p.warning,       p.warning_bg),
        }
        label, fg, bg = statuses.get(status, ("IDLE", p.text_tertiary, p.bg_secondary))
        self._status_badge.setText(label)
        self._status_badge.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            font-size: 9px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 2px;
            letter-spacing: 0.5px;
        """)
        
        if status == "running":
            self.start_timer()
        else:
            self.stop_timer()