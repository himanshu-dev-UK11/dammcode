"""
AI Engineering Workspace — v4.0 PREMIUM TAB INTERFACE

Redesigned with tabbed interface matching the IDE reference design:
  Tab 1: Chat       — Conversation + prompt input
  Tab 2: Tasks      — Current task, execution progress, plans
  Tab 3: Memory     — Project context, memory, files
  Tab 4: Execution  — Models, tools, runtime controls

Visual philosophy:
- Conversation dominates (Chat tab, default)
- Related controls grouped into tabs (not long collapsible lists)
- ~60% less visual noise than v3
- Every panel belongs to ONE unified app
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton,
    QStackedWidget, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSettings, Signal
from core.logger import setup_logger

from ui.ai_workspace.ai_chat_panel import AIChatPanel
from ui.ai_workspace.execution_plan_section import ExecutionPlanSection
from ui.ai_workspace.context_section import ContextSection
from ui.ai_workspace.current_task_section import CurrentTaskSection
from ui.ai_workspace.execution_progress_section import ExecutionProgressSection
from ui.ai_workspace.models_section import ModelsSection
from ui.ai_workspace.user_controls_section import UserControlsSection

logger = setup_logger(__name__)


class AITabButton(QToolButton):
    """Custom tab button for AI Workspace — flat underline style."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self._setup_styles()

    def _setup_styles(self):
        from ui.design_system import get_design_system, Radius, Spacing, FontSize, FontWeight
        p = get_design_system().palette
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {p.text_tertiary};
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: {Spacing.SM}px {Spacing.MD}px {Spacing.SM - 2}px {Spacing.MD}px;
                font-size: {FontSize.SM}px;
                font-weight: {FontWeight.MEDIUM};
                min-height: 28px;
            }}
            QToolButton:hover {{
                color: {p.text_secondary};
                background-color: transparent;
            }}
            QToolButton:checked {{
                color: {p.text};
                font-weight: {FontWeight.SEMIBOLD};
                border-bottom: 2px solid {p.accent};
            }}
        """)


class AIEngineeringWorkspaceV3(QWidget):
    """
    Premium AI Workspace with tabbed interface.

    Layout:
      [AI Workspace Header (title + controls)]
      [Tab Bar: Chat | Tasks | Memory | Execution]
      [Stacked Tab Content:
        Chat:       AIChatPanel + welcome context
        Tasks:      CurrentTaskSection, ExecutionProgressSection, ExecutionPlanSection
        Memory:     ContextSection
        Execution:  UserControlsSection, ModelsSection
      ]
    """

    # Panel size constraints
    MIN_WIDTH = 450  # Keep the dock readable by default
    DEFAULT_WIDTH = 500  # Better default experience for the AI workspace
    MAX_WIDTH = 720  # Allow a wider readable dock when space is available

    def __init__(self, event_bus, chat_engine=None):
        super().__init__()
        self.event_bus = event_bus
        self.chat_engine = chat_engine
        self.provider_registry = None
        self.provider_manager = None
        self.project_analyzer = None

        self._settings = QSettings("MyCodingMaster", "AIWorkspace")
        self._active_tab = self._settings.value("active_tab", "chat", type=str)

        # Keep references to existing section instances (for API compatibility)
        self._section_chat = None  # type: Section | None
        self._section_prompt = None
        self._section_current_task = None
        self._section_exec_progress = None
        self._section_memory = None
        self._section_models = None

        self.setup_ui()
        self._subscribe_to_events()
        self._restore_panel_width()

    # ──────────────────────────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────────────────────────
    def setup_ui(self):
        from ui.design_system import get_design_system, Radius, Spacing, FontSize, FontWeight
        p = get_design_system().palette

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setObjectName("AIWorkspace")

        # ── 1) Workspace Header ─────────────────────────────────────────
        header = QWidget()
        header.setObjectName("AIWorkspaceHeader")
        header.setFixedHeight(44)
        header.setStyleSheet(f"""
            QWidget#AIWorkspaceHeader {{
                background-color: {p.bg_secondary};
                border-bottom: 1px solid {p.border_subtle};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(Spacing.MD, 0, Spacing.SM, 0)
        header_layout.setSpacing(Spacing.SM)

        # Icon badge (matches reference: purple circle with robot face)
        icon_lbl = QLabel("🧠")
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {p.accent};
                color: #FFFFFF;
                border-radius: {Radius.SM}px;
                font-size: 14px;
            }}
        """)
        header_layout.addWidget(icon_lbl)

        # Title / greeting column
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(0)

        title_lbl = QLabel("AI WORKSPACE")
        title_lbl.setStyleSheet(f"""
            QLabel {{
                color: {p.text};
                font-size: {FontSize.XS}px;
                font-weight: {FontWeight.SEMIBOLD};
                letter-spacing: 0.06em;
                background-color: transparent;
            }}
        """)
        subtitle_lbl = QLabel("How can I help you build today?")
        subtitle_lbl.setStyleSheet(f"""
            QLabel {{
                color: {p.text_tertiary};
                font-size: {FontSize.XS}px;
                background-color: transparent;
            }}
        """)
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)
        header_layout.addLayout(title_col, 1)

        # Right-side action buttons (subtle)
        for icon_text, action in [("⟳", "refresh"), ("⛶", "fullscreen"), ("×", "close")]:
            btn = QToolButton()
            btn.setText(icon_text)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: transparent;
                    color: {p.text_tertiary};
                    border: none;
                    border-radius: {Radius.SM}px;
                    font-size: 11px;
                }}
                QToolButton:hover {{
                    background-color: {p.surface_hover};
                    color: {p.text};
                }}
            """)
            if icon_text == "×":
                btn.setToolTip("Hide AI Workspace (Ctrl+\\)")
                btn.clicked.connect(self._request_hide)
            elif icon_text == "⛶":
                btn.setToolTip("Toggle Fullscreen")
                btn.clicked.connect(self._request_fullscreen)
            else:
                btn.setToolTip("Refresh AI Context")
            header_layout.addWidget(btn)

        root.addWidget(header)

        # ── 2) Tab Bar ──────────────────────────────────────────────────
        tab_bar = QWidget()
        tab_bar.setFixedHeight(34)
        tab_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {p.bg_secondary};
                border-bottom: 1px solid {p.border_subtle};
            }}
        """)
        tab_bar_layout = QHBoxLayout(tab_bar)
        tab_bar_layout.setContentsMargins(Spacing.SM, 0, 0, 0)
        tab_bar_layout.setSpacing(0)

        self._tab_buttons = {}
        tabs = [
            ("chat",      "Chat"),
            ("tasks",     "Tasks"),
            ("memory",    "Memory"),
            ("execution", "Execution"),
        ]
        for tab_id, label in tabs:
            btn = AITabButton(label)
            btn.clicked.connect(lambda _=False, tid=tab_id: self.switch_tab(tid))
            tab_bar_layout.addWidget(btn)
            self._tab_buttons[tab_id] = btn
        tab_bar_layout.addStretch(1)

        root.addWidget(tab_bar)

        # ── 3) Stacked Tab Content ──────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"QStackedWidget {{ background-color: {p.bg}; border: none; }}")
        root.addWidget(self._stack, 1)

        # --- Build each tab's page (scrollable) ---
        self._page_chat      = self._build_chat_tab()
        self._page_tasks     = self._build_tasks_tab()
        self._page_memory    = self._build_memory_tab()
        self._page_execution = self._build_execution_tab()

        self._stack.addWidget(self._page_chat)
        self._stack.addWidget(self._page_tasks)
        self._stack.addWidget(self._page_memory)
        self._stack.addWidget(self._page_execution)

        # Set initial tab
        self.switch_tab(self._active_tab, save=False)

        # ── Size constraints ────────────────────────────────────────────
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)

    # ── Tab Page Builders ───────────────────────────────────────────────
    def _make_scroll_page(self) -> tuple[QScrollArea, QVBoxLayout]:
        """Create a standard scrollable page with a container layout."""
        from ui.design_system import get_design_system
        p = get_design_system().palette

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
        """)
        inner = QWidget()
        inner.setStyleSheet(f"background-color: {p.bg};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignTop)
        scroll.setWidget(inner)
        return scroll, lay

    def _build_chat_tab(self) -> QWidget:
        page, _ = self._make_scroll_page()
        inner = page.widget()
        lay = inner.layout()

        self._chat = AIChatPanel(self.event_bus)
        lay.addWidget(self._chat)
        lay.addStretch(1)
        return page

    def _build_tasks_tab(self) -> QWidget:
        page, lay = self._make_scroll_page()
        inner = page.widget()

        self._current_task = CurrentTaskSection(self.event_bus)
        self._execution_progress = ExecutionProgressSection(self.event_bus)
        self._execution_plan = ExecutionPlanSection(self.event_bus)

        lay.addWidget(self._build_section_header("Current Task"))
        lay.addWidget(self._current_task)
        lay.addWidget(self._build_section_header("Progress"))
        lay.addWidget(self._execution_progress)
        lay.addWidget(self._build_section_header("Plan"))
        lay.addWidget(self._execution_plan)
        lay.addStretch(1)
        return page

    def _build_memory_tab(self) -> QWidget:
        page, lay = self._make_scroll_page()
        self._context = ContextSection(self.event_bus)
        lay.addWidget(self._build_section_header("Project Context & Memory"))
        lay.addWidget(self._context)
        lay.addStretch(1)
        return page

    def _build_execution_tab(self) -> QWidget:
        page, lay = self._make_scroll_page()
        self._prompt_composer = UserControlsSection(self.event_bus)
        self._models = ModelsSection(self.event_bus)

        lay.addWidget(self._build_section_header("Prompt Composer"))
        lay.addWidget(self._prompt_composer)
        lay.addWidget(self._build_section_header("Models & Providers"))
        lay.addWidget(self._models)
        lay.addStretch(1)
        return page

    def _build_section_header(self, title: str) -> QWidget:
        from ui.design_system import get_design_system, FontSize, FontWeight, Spacing
        p = get_design_system().palette
        w = QWidget()
        w.setFixedHeight(32)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        lay.setSpacing(0)
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {p.text_tertiary};
                font-size: 10px;
                font-weight: {FontWeight.SEMIBOLD};
                letter-spacing: 0.06em;
                background-color: transparent;
            }}
        """)
        lay.addWidget(lbl)
        return w

    # ──────────────────────────────────────────────────────────────────
    # TAB CONTROL
    # ──────────────────────────────────────────────────────────────────
    def switch_tab(self, tab_id: str, save: bool = True):
        index = {"chat": 0, "tasks": 1, "memory": 2, "execution": 3}.get(tab_id, 0)
        # Update buttons
        for tid, btn in self._tab_buttons.items():
            btn.setChecked(tid == tab_id)
        # Show page
        self._stack.setCurrentIndex(index)
        self._active_tab = tab_id
        if save:
            self._settings.setValue("active_tab", tab_id)

    def _request_hide(self):
        """Emit event to hide the AI panel."""
        self.event_bus.publish("ai_panel_hide_requested", {})
    
    def _request_fullscreen(self):
        """Emit event to toggle AI panel fullscreen mode."""
        self.event_bus.publish("ai_panel_fullscreen_requested", {})

    # ──────────────────────────────────────────────────────────────────
    # EVENTS (Preserving original auto-expand behavior)
    # ──────────────────────────────────────────────────────────────────
    def _subscribe_to_events(self):
        self.event_bus.subscribe("workflow_started",         self._on_workflow_started)
        self.event_bus.subscribe("workflow_stage_changed",   self._on_workflow_stage_changed)
        self.event_bus.subscribe("workflow_complete",        self._on_workflow_complete)
        self.event_bus.subscribe("workflow_failed",          self._on_workflow_failed)

    def _on_workflow_started(self, data: dict):
        """Switch to Tasks tab and ensure sections are visible."""
        self.switch_tab("tasks")
        for w in [self._current_task, self._execution_progress,
                  self._execution_plan]:
            try: w.setVisible(True)
            except Exception: pass

    def _on_workflow_stage_changed(self, data: dict): pass
    def _on_workflow_complete(self,      data: dict): pass
    def _on_workflow_failed(self,        data: dict): pass

    # ──────────────────────────────────────────────────────────────────
    # PUBLIC API (backwards compatible with v3 callers)
    # ──────────────────────────────────────────────────────────────────
    def set_chat_engine(self, chat_engine):
        self.chat_engine = chat_engine
        if hasattr(self, '_chat'):
            self._chat.set_chat_engine(chat_engine)

    def set_providers(self, provider_registry, provider_manager):
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        if hasattr(self, '_models'):
            self._models.set_providers(provider_registry, provider_manager)
        if self.chat_engine and hasattr(self.chat_engine, 'model_center'):
            try:
                self._models.set_model_center(
                    self.chat_engine.model_center,
                    provider_registry,
                    provider_manager,
                    self.chat_engine.model_registry,
                )
            except Exception as e:
                logger.warning(f"Failed to set model_center on ModelsSection: {e}")

    def set_project_analyzer(self, project_analyzer):
        self.project_analyzer = project_analyzer

    # Properties for old callers that reference `_section_*._content` or
    # `_section_*._header` via workflow events. We keep them as simple
    # wrappers so external code doesn't break on AttributeError.
    @property
    def section_chat(self): return self._chat
    @property
    def section_current_task(self): return self._current_task
    @property
    def section_exec_progress(self): return self._execution_progress
    @property
    def section_memory(self): return self._context
    @property
    def section_models(self): return self._models

    # ──────────────────────────────────────────────────────────────────
    # SIZING / LIFECYCLE
    # ──────────────────────────────────────────────────────────────────
    def _restore_panel_width(self):
        saved_width = self._settings.value("panel_width", self.DEFAULT_WIDTH, type=int)
        width = max(self.MIN_WIDTH, min(saved_width, self.MAX_WIDTH))
        self.setFixedWidth(width)

    def save_panel_width(self, width: int):
        self._settings.setValue("panel_width", width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.save_panel_width(event.size().width())
        except Exception:
            pass

    def cleanup(self):
        """Cleanup resources before destruction."""
        if hasattr(self, '_chat') and self._chat:
            try: self._chat.cleanup()
            except Exception: pass
