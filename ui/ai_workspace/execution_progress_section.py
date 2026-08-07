"""Execution Progress Section"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class ExecutionProgressSection(QWidget):
    """Display execution progress."""
    def __init__(self, event_bus=None):
        super().__init__()
        self.event_bus = event_bus
        self._total_tasks = 0
        self._completed_tasks = 0
        self._current_step_name = "—"
        self.setup_ui()
        
        # Subscribe to execution events
        if self.event_bus:
            self._subscribe_events()
    
    def _subscribe_events(self):
        """Subscribe to execution events."""
        self.event_bus.subscribe("execution_task_created", self._on_task_created)
        self.event_bus.subscribe("execution_task_completed", self._on_task_completed)
        self.event_bus.subscribe("execution_task_failed", self._on_task_failed)
        self.event_bus.subscribe("execution_task_update", self._on_task_update)
        self.event_bus.subscribe("execution_status_update", self._on_status_update)
        
    def _on_task_created(self, data):
        """Handle task created event."""
        self._total_tasks += 1
        self._update_display()
        
    def _on_task_completed(self, data):
        """Handle task completed event."""
        self._completed_tasks += 1
        self._update_display()
        
    def _on_task_failed(self, data):
        """Handle task failed event."""
        self._completed_tasks += 1  # Count failures as "done" for progress
        self._update_display()
        
    def _on_task_update(self, data):
        """Handle task update event."""
        title = data.get("title", "")
        if title:
            self._current_step_name = title
            self._update_display()
            
    def _on_status_update(self, data):
        """Handle status update event."""
        # Update totals from engine status
        completed = data.get("completed_tasks", 0) + data.get("failed_tasks", 0)
        if completed > self._completed_tasks:
            self._completed_tasks = completed
            self._update_display()
            
    def _update_display(self):
        """Update the progress display."""
        self.set_progress(self._completed_tasks, self._total_tasks, self._current_step_name)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(5)

        row = QHBoxLayout()
        self._step_lbl = QLabel("Step 0 of 0")
        self._step_lbl.setStyleSheet("color: #8E8E98; font-size: 11px; background-color: transparent;")
        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setStyleSheet("color: #52525C; font-size: 10px; background-color: transparent;")
        row.addWidget(self._step_lbl)
        row.addStretch()
        row.addWidget(self._pct_lbl)
        layout.addLayout(row)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(4)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        self._current_step = QLabel("—")
        self._current_step.setStyleSheet("color: #52525C; font-size: 10px; background-color: transparent;")
        self._current_step.setWordWrap(True)
        layout.addWidget(self._current_step)
        
    def set_progress(self, step: int, total: int, step_name: str = ""):
        """Update progress display."""
        pct = int(step / total * 100) if total > 0 else 0
        self._step_lbl.setText(f"Step {step} of {total}")
        self._pct_lbl.setText(f"{pct}%")
        self._bar.setValue(pct)
        self._current_step.setText(step_name or "—")