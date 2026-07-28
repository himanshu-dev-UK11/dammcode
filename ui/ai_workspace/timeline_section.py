"""Workspace Timeline Section"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt

class TimelineSection(QWidget):
    """Visual timeline of task execution events."""
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._events = []
        self.setup_ui()
        self._subscribe_events()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(8)
        
        # Scroll area for timeline
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent; border: none;")
        self.scroll.setFixedHeight(150)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.timeline_layout = QVBoxLayout(self.container)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(6)
        self.timeline_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
    def _subscribe_events(self):
        self.event_bus.subscribe("execution_task_started", self._on_task_started)
        self.event_bus.subscribe("execution_task_completed", self._on_task_completed)
        self.event_bus.subscribe("execution_task_failed", self._on_task_failed)
        self.event_bus.subscribe("execution_task_cancelled", self._on_task_cancelled)
        self.event_bus.subscribe("execution_task_paused", self._on_task_paused)
        self.event_bus.subscribe("execution_task_resumed", self._on_task_resumed)
        self.event_bus.subscribe("execution_task_dispatched", self._on_task_dispatched)
        self.event_bus.subscribe("workflow_verification_started", lambda _: self._add_event("Verification", "Running code verification..."))
        self.event_bus.subscribe("workflow_patch_ready", lambda _: self._add_event("Patch Generated", "Code changes ready for review."))
        
    def _on_task_started(self, data):
        task_id = data.get('task_id', '')[:8]
        self._add_event("Task Started", f"ID: {task_id}")
        
    def _on_task_completed(self, data):
        task_id = data.get('task_id', '')[:8]
        self._add_event("Task Completed ✓", f"ID: {task_id}", color="#22C55E")
        
    def _on_task_failed(self, data):
        task_id = data.get('task_id', '')[:8]
        error = data.get('error', 'Unknown error')[:40]
        self._add_event("Task Failed ✗", f"ID: {task_id} - {error}", color="#EF4444")
        
    def _on_task_cancelled(self, data):
        task_id = data.get('task_id', '')[:8]
        self._add_event("Task Cancelled", f"ID: {task_id}", color="#F59E0B")
        
    def _on_task_paused(self, data):
        task_id = data.get('task_id', '')[:8]
        self._add_event("Task Paused", f"ID: {task_id}", color="#8E8E98")
        
    def _on_task_resumed(self, data):
        task_id = data.get('task_id', '')[:8]
        self._add_event("Task Resumed", f"ID: {task_id}", color="#3B82F6")
        
    def _on_task_dispatched(self, data):
        task_id = data.get('task_id', '')[:8]
        title = data.get('title', 'Unknown')[:30]
        self._add_event("Task Dispatched", f"{title} (ID: {task_id})", color="#A78BFA")
        
    def _add_event(self, title: str, description: str, color: str = "#E2E2E6"):
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        
        item = QWidget()
        row = QHBoxLayout(item)
        row.setContentsMargins(0, 0, 0, 0)
        
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("color: #52525C; font-size: 10px; min-width: 50px;")
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #8E8E98; font-size: 11px;")
        desc_lbl.setWordWrap(True)
        
        row.addWidget(time_lbl)
        
        text_col = QVBoxLayout()
        text_col.addWidget(title_lbl)
        text_col.addWidget(desc_lbl)
        
        row.addLayout(text_col)
        row.addStretch()
        
        self.timeline_layout.addWidget(item)
        
        # Auto-scroll
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

