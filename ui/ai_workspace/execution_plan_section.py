"""Execution Plan Section - v0.9"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtGui import QColor


class ExecutionPlanSection(QWidget):
    """Display the execution plan with phase tracking."""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 6)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setMaximumHeight(200)
        self._list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 11px;
                font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            }
            QListWidget::item {
                color: #8E8E98;
                padding: 4px 10px;
                min-height: 22px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #1C1C1F;
            }
            QListWidget::item:selected {
                background-color: #1E3A5F;
                color: #E2E2E6;
            }
        """)
        layout.addWidget(self._list)
        
    def set_plan(self, steps: list):
        """Update plan display.
        
        steps = [{'title': str, 'phase': str, 'status': 'pending'|'running'|'done'|'error'}]
        """
        self._list.clear()
        
        # Group by phase
        phases = {}
        for step in steps:
            phase = step.get('phase', 'General')
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(step)
            
        # Add phase headers and steps
        for phase, phase_steps in phases.items():
            # Phase header
            phase_item = QListWidgetItem(f"━━ {phase.upper()} ━━")
            phase_item.setForeground(QColor("#3B82F6"))
            phase_item.setFlags(phase_item.flags() & ~31)  # Not selectable
            self._list.addItem(phase_item)
            
            # Phase steps
            for step in phase_steps:
                icon = self._get_icon(step.get('status', 'pending'))
                text = f"{icon}  {step.get('title', '')}"
                item = QListWidgetItem(text)
                
                status = step.get('status', 'pending')
                if status == 'done':
                    item.setForeground(QColor("#22C55E"))
                elif status == 'running':
                    item.setForeground(QColor("#3B82F6"))
                elif status == 'error':
                    item.setForeground(QColor("#EF4444"))
                else:
                    item.setForeground(QColor("#8E8E98"))
                    
                self._list.addItem(item)
                
    def _get_icon(self, status: str) -> str:
        """Get status icon."""
        icons = {
            'done': '✓',
            'running': '⟳',
            'error': '✕',
            'pending': '○',
        }
        return icons.get(status, '○')