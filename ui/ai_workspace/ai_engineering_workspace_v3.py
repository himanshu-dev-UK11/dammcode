"""
AI Engineering Workspace — v3.0 PREMIUM CONTROL CENTER

Complete redesign of the AI Workspace into a premium AI Engineering Control Center.
Modern, minimal, professional cockpit for AI-assisted software engineering.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QLabel, QToolButton
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QFont
from core.logger import setup_logger

from ui.ai_workspace.ai_chat_panel import AIChatPanel
from ui.ai_workspace.execution_plan_section import ExecutionPlanSection
from ui.ai_workspace.context_section import ContextSection
from ui.ai_workspace.current_task_section import CurrentTaskSection
from ui.ai_workspace.execution_progress_section import ExecutionProgressSection
from ui.ai_workspace.models_section import ModelsSection
from ui.ai_workspace.user_controls_section import UserControlsSection

logger = setup_logger(__name__)


class Section(QWidget):
    """
    Collapsible section container for AI Workspace panels.
    Simple wrapper that provides expand/collapse functionality.
    """
    toggled = Signal(bool)  # True when expanded, False when collapsed
    
    def __init__(self, title: str, content_widget: QWidget, expanded: bool = True, collapsible: bool = True, parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content_widget
        self._expanded = expanded
        self._collapsible = collapsible
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from ui.design_system import get_design_system, FontSize, Spacing
        p = get_design_system().palette
        
        # Header
        self.header = QWidget()
        self.header.setFixedHeight(26)
        self.header.setStyleSheet(f"""
            QWidget {{
                background-color: {p.bg_secondary};
                border-bottom: 1px solid {p.border_subtle};
            }}
        """)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(4)
        
        # Toggle button (only if collapsible)
        if self._collapsible:
            self.toggle_btn = QToolButton()
            self.toggle_btn.setText("▼" if self._expanded else "▶")
            self.toggle_btn.setFixedSize(14, 14)
            self.toggle_btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: transparent;
                    border: none;
                    color: {p.text_tertiary};
                    font-size: 8px;
                }}
                QToolButton:hover {{
                    color: {p.text};
                }}
            """)
            self.toggle_btn.clicked.connect(self.toggle)
            header_layout.addWidget(self.toggle_btn)
        else:
            # Add spacer for alignment when not collapsible
            spacer = QWidget()
            spacer.setFixedSize(14, 14)
            header_layout.addWidget(spacer)
        
        # Title
        title_label = QLabel(self.title.upper())
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {p.text_tertiary};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background-color: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(self.header)
        layout.addWidget(self.content)
        
        self.content.setVisible(self._expanded)
    
    def toggle(self):
        """Toggle section expansion."""
        if not self._collapsible:
            return
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        if hasattr(self, 'toggle_btn'):
            self.toggle_btn.setText("▼" if self._expanded else "▶")
        self.toggled.emit(self._expanded)
    
    def expand(self):
        """Expand the section."""
        if not self._expanded and self._collapsible:
            self.toggle()
    
    def collapse(self):
        """Collapse the section."""
        if self._expanded and self._collapsible:
            self.toggle()
    
    def is_expanded(self) -> bool:
        """Check if section is expanded."""
        return self._expanded


class AIEngineeringWorkspaceV3(QWidget):
    """
    Premium AI Engineering Control Center.
    
    Design Philosophy:
    - Conversation is primary — always visible
    - Everything else is collapsed by default
    - Clean, professional, minimal visual design
    - Smooth interactions and animations
    - Context-aware auto-expansion
    """
    
    # Panel size constraints
    MIN_WIDTH = 280
    DEFAULT_WIDTH = 320
    MAX_WIDTH = 520
    
    def __init__(self, event_bus, chat_engine=None):
        super().__init__()
        self.event_bus = event_bus
        self.chat_engine = chat_engine
        self.provider_registry = None
        self.provider_manager = None
        self.project_analyzer = None
        
        self._settings = QSettings("MyCodingMaster", "AIWorkspace")
        
        self.setup_ui()
        self._subscribe_to_events()
        self._restore_panel_width()
        
    def setup_ui(self):
        """Setup the premium control center UI."""
        from ui.design_system import get_design_system
        p = get_design_system().palette
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {p.bg};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {p.bg};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {p.border};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {p.accent};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        container = QWidget()
        container.setStyleSheet(f"background-color: {p.bg};")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setAlignment(Qt.AlignTop)
        
        # SECTION 1: CONVERSATION (Always visible, expanded by default)
        self._chat = AIChatPanel(self.event_bus)
        self._section_chat = Section("Conversation", self._chat, expanded=True, collapsible=False)
        container_layout.addWidget(self._section_chat)
        
        # SECTION 2: Prompt Composer (Collapsed by default)
        self._prompt_composer = UserControlsSection(self.event_bus)
        self._section_prompt = Section("Prompt Composer", self._prompt_composer, expanded=False)
        container_layout.addWidget(self._section_prompt)
        
        # SECTION 3: Current Task (Collapsed, auto-expands on task start)
        self._current_task = CurrentTaskSection(self.event_bus)
        self._section_current_task = Section("Current Task", self._current_task, expanded=False)
        container_layout.addWidget(self._section_current_task)
        
        # SECTION 4: Execution Progress (Collapsed, auto-expands on workflow start)
        self._execution_progress = ExecutionProgressSection(self.event_bus)
        self._section_exec_progress = Section("Execution Progress", self._execution_progress, expanded=False)
        container_layout.addWidget(self._section_exec_progress)
        
        # SECTION 5: Memory (Collapsed by default)
        self._context = ContextSection(self.event_bus)
        self._section_memory = Section("Memory", self._context, expanded=False)
        container_layout.addWidget(self._section_memory)
        
        # SECTION 6: Models (Collapsed by default)
        self._models = ModelsSection(self.event_bus)
        self._section_models = Section("Models", self._models, expanded=False)
        container_layout.addWidget(self._section_models)
        
        # Add stretch
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Set size constraints
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        
    def _subscribe_to_events(self):
        """Subscribe to relevant event bus events."""
        self.event_bus.subscribe("workflow_started", self._on_workflow_started)
        self.event_bus.subscribe("workflow_stage_changed", self._on_workflow_stage_changed)
        self.event_bus.subscribe("workflow_complete", self._on_workflow_complete)
        self.event_bus.subscribe("workflow_failed", self._on_workflow_failed)
        
    def _on_workflow_started(self, data: dict):
        """Auto-expand sections when workflow starts."""
        self._section_current_task._content.setVisible(True)
        self._section_exec_progress._content.setVisible(True)
        self._section_current_task._header._expanded = True
        self._section_exec_progress._header._expanded = True
        
    def _on_workflow_stage_changed(self, data: dict):
        """Update on stage change."""
        pass
        
    def _on_workflow_complete(self, data: dict):
        """Update on workflow complete."""
        pass
        
    def _on_workflow_failed(self, data: dict):
        """Update on workflow failed."""
        pass
        
    def set_chat_engine(self, chat_engine):
        """Set the AI Chat Engine."""
        self.chat_engine = chat_engine
        self._chat.set_chat_engine(chat_engine)
        
    def set_providers(self, provider_registry, provider_manager):
        """Set provider registry and manager."""
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self._models.set_providers(provider_registry, provider_manager)
        
        # Set model_center on ModelsSection if available
        if self.chat_engine and hasattr(self.chat_engine, 'model_center'):
            self._models.set_model_center(
                self.chat_engine.model_center,
                provider_registry,
                provider_manager,
                self.chat_engine.model_registry
            )
        
    def set_project_analyzer(self, project_analyzer):
        """Set the Project Analyzer."""
        self.project_analyzer = project_analyzer
        
    def _restore_panel_width(self):
        """Restore saved panel width."""
        saved_width = self._settings.value("panel_width", self.DEFAULT_WIDTH, type=int)
        width = max(self.MIN_WIDTH, min(saved_width, self.MAX_WIDTH))
        self.setFixedWidth(width)
        
    def save_panel_width(self, width: int):
        """Save panel width to settings."""
        self._settings.setValue("panel_width", width)
        
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.save_panel_width(event.size().width())
    
    def cleanup(self):
        """Cleanup resources before destruction."""
        # Cleanup chat panel (stops background threads)
        if hasattr(self, '_chat') and self._chat:
            self._chat.cleanup()
