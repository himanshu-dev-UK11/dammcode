"""
AI Chat Panel — v2.0

Complete AI chat interface with:
- Provider and model selection
- Message sending and receiving
- Conversation history
- Chat management (New, Clear)
- Placeholder responses until AI configured
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QFrame, QComboBox, QTextEdit, QMessageBox, QSizePolicy, QGridLayout, QToolButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ai.connection import get_connection_manager, ConnectionStatus
from ui.ai_workspace.intelligent_error_handler import ConnectionStatusWidget


class MessageWidget(QWidget):
    """A single premium message bubble — avatar + card layout matching reference."""
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        self.setup_ui(text, is_user)

    def setup_ui(self, text: str, is_user: bool):
        from ui.design_system import get_design_system, Radius, Spacing, FontSize
        p = get_design_system().palette

        outer = QHBoxLayout(self)
        outer.setContentsMargins(Spacing.MD, 4, Spacing.MD, 4)
        outer.setSpacing(Spacing.SM)
        outer.setAlignment(Qt.AlignTop)

        # ── Avatar ───────────────────────────────────────────────────────
        avatar = QLabel("👤" if is_user else "🤖")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {p.surface if is_user else p.accent + '33'};
                color: {'#FFFFFF' if not is_user else p.text};
                border: 1px solid {p.border};
                border-radius: 14px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        outer.addWidget(avatar, 0, Qt.AlignTop)

        # ── Message Column (role + card) ─────────────────────────────────
        col_wrap = QWidget()
        col_layout = QVBoxLayout(col_wrap)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(3)

        role = "You" if is_user else "AI Assistant"
        role_color = p.accent if is_user else p.text

        role_lbl = QLabel(role)
        role_lbl.setStyleSheet(f"""
            color: {role_color};
            font-size: {FontSize.XXS}px;
            font-weight: 700;
            background-color: transparent;
            letter-spacing: 0.2px;
        """)
        col_layout.addWidget(role_lbl)

        # ── Message Card ─────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("MessageCard")
        card_bg = p.bg_secondary if is_user else p.surface
        card_border = p.border

        card.setStyleSheet(f"""
            QFrame#MessageCard {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: {Radius.LG}px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        card_layout.setSpacing(0)

        text_lbl = QLabel(text)
        text_lbl.setObjectName("msg_body")
        text_lbl.setWordWrap(True)
        text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setStyleSheet(f"""
            color: {p.text};
            font-size: {FontSize.SM}px;
            background-color: transparent;
            line-height: 1.5;
        """)
        card_layout.addWidget(text_lbl)
        col_layout.addWidget(card)

        outer.addWidget(col_wrap, 1)


class AIChatPanel(QWidget):
    """
    Complete AI chat interface.
    
    Top: Provider/Model selection + Status
    Middle: Scrollable conversation area
    Bottom: Input box + Send/Stop/New/Clear buttons
    """
    
    message_sent = Signal(str)
    chunk_received = Signal(str)  # For thread-safe chunk updates
    generation_complete = Signal(str, float)  # For thread-safe completion
    provider_refresh_started = Signal()
    provider_refresh_complete = Signal(dict)  # key: provider_name, models
    models_updated = Signal()
    
    def __init__(self, event_bus, chat_engine=None):
        super().__init__()
        self.event_bus = event_bus
        self.chat_engine = chat_engine
        self._messages = []
        self._streaming_text = ""
        self._streaming_widget = None
        self._refresh_worker_thread = None
        self._refresh_stop_flag = False  # Add stop flag for cleanup
        
        # Connect signals to slots for thread safety
        self.chunk_received.connect(self._on_chunk_received_safe)
        self.generation_complete.connect(self._on_generation_complete_safe)
        self.provider_refresh_started.connect(self._on_provider_refresh_started)
        self.provider_refresh_complete.connect(self._on_provider_refresh_complete)
        self.models_updated.connect(self._on_models_updated)
        
        # Subscribe to events
        self.event_bus.subscribe("provider_connected", self._on_provider_connected_event)
        self.event_bus.subscribe("ai_action_requested", self._on_ai_action_requested_event)
        self.event_bus.subscribe("ai_chat_failover", self._on_chat_failover)
        self.event_bus.subscribe("workflow_generation_chunk", self._on_workflow_chunk)
        self.event_bus.subscribe("workflow_generation_finished", self._on_workflow_finished)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        from ui.design_system import get_design_system, Spacing, Radius, FontSize
        p = get_design_system().palette

        self.setStyleSheet(f"""
            AIChatPanel {{
                background-color: {p.bg};
            }}
        """)

        # ── Subtle Conversation Header ────────────────────────────────────
        header = QWidget()
        header.setObjectName("AIChatHeader")
        header.setStyleSheet(f"""
            background-color: {p.bg_secondary};
            border-bottom: 1px solid {p.border_subtle};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.SM, Spacing.SM)
        header_layout.setSpacing(Spacing.XS)

        # Avatar / greeting
        greeting_wrap = QHBoxLayout()
        greeting_wrap.setSpacing(Spacing.SM)
        avatar = QLabel("👩‍💻")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: 18px;
            font-size: 16px;
        """)
        greeting_wrap.addWidget(avatar)

        greeting_col = QVBoxLayout()
        greeting_col.setSpacing(0)
        greeting_title = QLabel("AI Assistant")
        greeting_title.setStyleSheet(f"""
            color: {p.text};
            font-size: {FontSize.SM}px;
            font-weight: 600;
            background: transparent;
        """)
        greeting_sub = QLabel("How can I help you build today?")
        greeting_sub.setStyleSheet(f"""
            color: {p.text_tertiary};
            font-size: {FontSize.XS}px;
            background: transparent;
        """)
        greeting_col.addWidget(greeting_title)
        greeting_col.addWidget(greeting_sub)
        greeting_wrap.addLayout(greeting_col)
        greeting_wrap.addStretch(1)
        header_layout.addLayout(greeting_wrap, 1)

        # Right: subtle action buttons (New Chat, Clear, Settings)
        def header_btn(icon, tip):
            b = QToolButton()
            b.setText(icon)
            b.setToolTip(tip)
            b.setFixedSize(28, 28)
            b.setStyleSheet(f"""
                QToolButton {{
                    background-color: transparent;
                    color: {p.text_tertiary};
                    border: none;
                    border-radius: {Radius.SM}px;
                    font-size: 13px;
                    padding: 0;
                }}
                QToolButton:hover {{
                    background-color: {p.surface_hover};
                    color: {p.text};
                }}
                QToolButton:pressed {{
                    background-color: {p.surface_active};
                    color: {p.text};
                }}
            """)
            return b

        btn_new = header_btn("＋", "New Chat (Ctrl+N)")
        btn_new.clicked.connect(self._on_new_chat)
        btn_clear = header_btn("⟲", "Clear Chat")
        btn_clear.clicked.connect(self._on_clear_chat)
        btn_settings = header_btn("⚙", "AI Settings")
        header_layout.addWidget(btn_new)
        header_layout.addWidget(btn_clear)
        header_layout.addWidget(btn_settings)

        layout.addWidget(header)

        # ── Conversation Area ─────────────────────────────────────────────
        self._setup_conversation(layout)

        # ── Bottom Input ──────────────────────────────────────────────────
        self._setup_input(layout)

        # Show welcome message
        self._show_welcome()
        
    def _setup_controls(self, parent_layout):
        """Setup provider/model controls — compact, all text visible."""
        from ui.design_system import get_design_system
        p = get_design_system().palette

        controls = QWidget()
        controls.setStyleSheet(f"""
            background-color: {p.bg};
            border-bottom: 1px solid {p.border_subtle};
        """)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(6)
        
        # Provider row
        provider_row = QHBoxLayout()
        provider_row.setSpacing(8)
        
        provider_lbl = QLabel("Provider")
        provider_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 11px; font-weight: 600;")
        provider_lbl.setFixedWidth(52)
        provider_row.addWidget(provider_lbl)
        
        self._provider_combo = QComboBox()
        self._provider_combo.addItem("Automatic", "automatic")
        self._provider_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self._provider_combo.setMinimumContentsLength(8)
        self._provider_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                border: 1px solid {p.border_subtle};
                border-radius: 4px;
                padding: 4px 8px;
                color: {p.text};
                font-size: 11px;
            }}
            QComboBox:hover {{ border-color: {p.accent}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid {p.text_secondary};
                width: 0; height: 0;
            }}
        """)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self._provider_combo, 1)
        controls_layout.addLayout(provider_row)
        
        # Model row
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        
        model_lbl = QLabel("Model")
        model_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 11px; font-weight: 600;")
        model_lbl.setFixedWidth(52)
        model_row.addWidget(model_lbl)
        
        self._model_combo = QComboBox()
        self._model_combo.addItem("Select a provider first")
        self._model_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self._model_combo.setMinimumContentsLength(8)
        self._model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                border: 1px solid {p.border_subtle};
                border-radius: 4px;
                padding: 4px 8px;
                color: {p.text};
                font-size: 11px;
            }}
            QComboBox:hover {{ border-color: {p.accent}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid {p.text_secondary};
                width: 0; height: 0;
            }}
        """)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_row.addWidget(self._model_combo, 1)
        controls_layout.addLayout(model_row)
        
        # Status row — status + latency on same line
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        
        status_lbl = QLabel("Status")
        status_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 11px; font-weight: 600;")
        status_lbl.setFixedWidth(52)
        status_row.addWidget(status_lbl)
        
        self._status_indicator = QLabel("● Disconnected")
        self._status_indicator.setStyleSheet(f"color: {p.error}; font-size: 11px;")
        self._status_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_row.addWidget(self._status_indicator, 1)
        
        self._latency_lbl = QLabel("")
        self._latency_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: 10px;")
        status_row.addWidget(self._latency_lbl)
        
        controls_layout.addLayout(status_row)
        parent_layout.addWidget(controls)
        
        # Initialize provider change
        self._on_provider_changed("Automatic")
        
    def _setup_conversation(self, parent_layout):
        """Setup scrollable conversation area."""
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {p.bg};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {p.border};
                border-radius: 4px;
                min-height: 28px;
                margin: 2px 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {p.border_hover};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self._msg_widget = QWidget()
        self._msg_widget.setStyleSheet(f"background-color: {p.bg};")
        self._msg_layout = QVBoxLayout(self._msg_widget)
        self._msg_layout.setContentsMargins(0, 12, 0, 12)
        self._msg_layout.setSpacing(10)
        self._msg_layout.setAlignment(Qt.AlignTop)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_widget)
        parent_layout.addWidget(self._scroll)
        
    def _setup_input(self, parent_layout):
        """
        Setup clean professional input area (reference design):
        — Provider/Model, Context selector (row above input)
        — Large multiline editor + rounded send button
        — Subtle status indicator in corner (hidden unless active)
        """
        from ui.design_system import get_design_system, Radius, Spacing, FontSize
        p = get_design_system().palette

        # ── Container ────────────────────────────────────────────────────
        container = QWidget()
        container.setObjectName("AIChatInputContainer")
        container.setStyleSheet(f"""
            background-color: {p.bg_secondary};
            border-top: 1px solid {p.border_subtle};
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # ── Row 1: Provider + Model + Context + subtle status ────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.SM)

        # Provider selector (compact — keeps existing logic working)
        self._provider_combo = QComboBox()
        self._provider_combo.addItem("Automatic", "automatic")
        self._provider_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self._provider_combo.setMinimumContentsLength(6)
        self._provider_combo.setToolTip("AI Provider")
        self._provider_combo.setMinimumHeight(28)
        self._provider_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: 0 {Spacing.SM}px 0 {Spacing.SM}px;
                font-size: {FontSize.XS}px;
                font-weight: 500;
                min-height: 28px;
            }}
            QComboBox:hover {{
                border-color: {p.border_hover};
                background-color: {p.surface_hover};
            }}
            QComboBox::drop-down {{ border: none; width: 14px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid {p.text_tertiary};
                width: 0; height: 0;
                margin-right: 2px;
            }}
        """)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        top_row.addWidget(self._provider_combo, 0)

        # Model selector dropdown (beautiful, compact)
        self._model_combo = QComboBox()
        self._model_combo.setMinimumHeight(28)
        self._model_combo.addItem("Automatic")
        self._model_combo.setToolTip("AI Model — click to change")
        self._model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: 0 {Spacing.MD}px 0 {Spacing.MD}px;
                font-size: {FontSize.XS}px;
                font-weight: 600;
                min-height: 28px;
            }}
            QComboBox:hover {{
                border-color: {p.border_hover};
                background-color: {p.surface_hover};
            }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid {p.text_tertiary};
                width: 0; height: 0;
                margin-right: 4px;
            }}
        """)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        top_row.addWidget(self._model_combo, 0)

        # Context chip button
        self._btn_context = QToolButton()
        self._btn_context.setText("⊙  Context")
        self._btn_context.setToolTip("Attach workspace context / files")
        self._btn_context.setCursor(Qt.PointingHandCursor)
        self._btn_context.setMinimumHeight(28)
        self._btn_context.setStyleSheet(f"""
            QToolButton {{
                background-color: {p.surface};
                color: {p.text_secondary};
                border: 1px solid {p.border};
                border-radius: {Radius.MD}px;
                padding: 0 {Spacing.MD}px;
                font-size: {FontSize.XS}px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background-color: {p.surface_hover};
                border-color: {p.accent};
                color: {p.accent};
            }}
            QToolButton:pressed {{
                background-color: {p.surface_active};
            }}
        """)
        top_row.addWidget(self._btn_context, 0)

        top_row.addStretch(1)

        # Latency label (keeps existing logic happy)
        self._latency_lbl = QLabel("")
        self._latency_lbl.setStyleSheet(f"color: {p.text_tertiary}; font-size: {FontSize.XXS}px;")
        top_row.addWidget(self._latency_lbl, 0, Qt.AlignRight)

        # Status indicator
        self._status_indicator = QLabel("● Connected")
        self._status_indicator.setWordWrap(True)
        self._status_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._status_indicator.setStyleSheet(f"color: {p.success}; font-size: {FontSize.XXS}px;")
        top_row.addWidget(self._status_indicator, 0, Qt.AlignRight)

        layout.addLayout(top_row)

        # ── Row 2: Multiline Input + Send Button ─────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(Spacing.SM)

        self._input = QTextEdit()
        self._input.setPlaceholderText("Ask anything… (Enter to send, Shift+Enter for new line)")
        self._input.setMinimumHeight(64)
        self._input.setMaximumHeight(160)
        self._input.installEventFilter(self)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: {Radius.LG}px;
                padding: {Spacing.MD}px {Spacing.MD}px;
                font-size: {FontSize.MD}px;
                selection-background-color: {p.selection};
            }}
            QTextEdit:hover {{
                border-color: {p.border_hover};
            }}
            QTextEdit:focus {{
                border-color: {p.accent};
                background-color: {p.bg};
            }}
        """)
        input_row.addWidget(self._input, 1)

        # Rounded accent send button
        self._btn_send = QPushButton("➤")
        self._btn_send.setToolTip("Send Message (Enter)")
        self._btn_send.setCursor(Qt.PointingHandCursor)
        self._btn_send.setFixedSize(40, 40)
        self._btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.accent};
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 700;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {p.accent_hover};
            }}
            QPushButton:pressed {{
                background-color: {p.accent_active};
            }}
            QPushButton:disabled {{
                background-color: {p.surface};
                color: {p.text_disabled};
                border: 1px solid {p.border};
            }}
        """)
        self._btn_send.clicked.connect(self._send)

        # Stop button (hidden by default)
        self._btn_stop = QPushButton("■")
        self._btn_stop.setToolTip("Stop Generation")
        self._btn_stop.setCursor(Qt.PointingHandCursor)
        self._btn_stop.setFixedSize(40, 40)
        self._btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.error};
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: #D43F38;
            }}
            QPushButton:pressed {{
                background-color: #B8332D;
            }}
        """)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.hide()

        send_wrap = QVBoxLayout()
        send_wrap.setContentsMargins(0, 0, 0, 0)
        send_wrap.setSpacing(0)
        send_wrap.addStretch(1)
        send_wrap.addWidget(self._btn_send, 0, Qt.AlignBottom)
        send_wrap.addWidget(self._btn_stop, 0, Qt.AlignBottom)
        input_row.addLayout(send_wrap)

        layout.addLayout(input_row)

        # ── Subtle Quick Action pill row ──────────────────────────────────
        qa_row = QHBoxLayout()
        qa_row.setSpacing(6)

        action_names = [
            ("Explain",  "Explain selected code"),
            ("Fix",      "Fix issues in code"),
            ("Refactor", "Refactor code"),
            ("Test",     "Generate tests"),
        ]
        qa_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {p.text_tertiary};
                border: 1px solid {p.border_subtle};
                border-radius: 12px;
                padding: 3px {Spacing.SM}px;
                font-size: {FontSize.XXS}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {p.surface_hover};
                color: {p.text};
                border-color: {p.border};
            }}
            QPushButton:pressed {{
                background-color: {p.surface_active};
            }}
        """
        for name, tip in action_names:
            b = QPushButton(name)
            b.setStyleSheet(qa_style)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, n=name: self._on_quick_action(n))
            qa_row.addWidget(b)
        qa_row.addStretch(1)
        layout.addLayout(qa_row)

        parent_layout.addWidget(container)

        # Initialize model/provider
        self._on_provider_changed("Automatic")
        
    def eventFilter(self, obj, event):
        """Handle Enter key for sending."""
        if obj == self._input and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() in (Qt.ShiftModifier, Qt.ControlModifier):
                    return False  # Allow new line
                else:
                    self._send()
                    return True
        return super().eventFilter(obj, event)
        
    def _on_quick_action(self, action_name: str):
        """Handle quick action button clicks."""
        prompt = self._build_prompt(action_name)
        self._input.setPlainText(prompt)
        
    def _build_prompt(self, action_name: str) -> str:
        """Build a prompt that includes current context."""
        from core.workspace_manager import get_workspace_manager
        from pathlib import Path
        
        prompt_parts = []
        
        # Action-specific instructions
        action_instructions = {
            "Explain": "Please explain the following code in detail, highlighting its purpose and key functionality:",
            "Review": "Please review the following code for potential bugs, code smells, and improvements:",
            "Fix": "Please identify and fix any issues in the following code:",
            "Refactor": "Please refactor the following code for better readability and maintainability:",
            "Document": "Please generate comprehensive documentation/comments for the following code:",
            "Test": "Please generate unit tests for the following code:",
            "Optimize": "Please optimize the following code for better performance or efficiency:",
            "Commit": "Please generate a concise and descriptive Git commit message for the following code changes:"
        }
        
        prompt_parts.append(action_instructions.get(action_name, f"Please {action_name.lower()} the following:"))
        
        # Try to get current file and selected code from EditorManager (via main window/editor)
        # For now, let's use context from event bus or assume we'll collect more later
        prompt_parts.append("(Note: Add your code here or select code in the editor)")
        
        return "\n\n".join(prompt_parts)
        
    def _on_ai_action_requested_event(self, data: dict):
        """Handle AI action events from the editor."""
        action = data.get("action", "")
        selected_text = data.get("selected_text", "")
        file_path = data.get("file_path", "")
        
        # Map actions to prompt instructions
        action_prompts = {
            "ask": "Please help with the following code:",
            "explain": "Please explain the following code in detail:",
            "optimize": "Please optimize the following code:",
            "refactor": "Please refactor the following code:",
            "generate_function": "Please generate a function for the following:",
            "generate_docs": "Please generate documentation/comments for the following code:",
            "review": "Please review the following code and suggest improvements:",
            "find_bugs": "Please identify potential bugs in the following code:",
            "generate_tests": "Please generate unit tests for the following code:",
            "copy_to_chat": "Here's some code from the editor:"
        }
        
        prompt_parts = []
        prompt_parts.append(action_prompts.get(action, "Please help with the following:"))
        
        if file_path:
            prompt_parts.append(f"File: {file_path}")
        
        if selected_text:
            prompt_parts.append(f"\n```\n{selected_text}\n```")
        else:
            prompt_parts.append("\n(No text selected)")
        
        full_prompt = "\n".join(prompt_parts)
        self._input.setPlainText(full_prompt)
        
    def _on_provider_changed(self, provider_text: str):
        """Update models when provider changes (non-blocking)."""
        from core.logger import setup_logger
        
        logger = setup_logger(__name__)
        
        provider = self._provider_combo.currentData()
        logger.info(f"Provider changed to: {provider_text} (data: {provider})")
        
        # Immediately update UI to show loading
        self._model_combo.clear()
        self._model_combo.addItem("Loading...", "")
        self._update_status("Connecting...", "info")
        
        if self.chat_engine:
            # Always start background refresh first — it will call models_updated when done
            self._start_provider_refresh_background()
            
            # Also populate immediately from whatever model_center already has
            try:
                model_center = self.chat_engine.model_center
                all_models_info = model_center.get_all_models()
                if all_models_info:
                    self._populate_model_combo(provider, all_models_info)
            except Exception as e:
                logger.warning(f"Could not do initial model_combo populate: {e}")
        else:
            self._model_combo.clear()
            self._model_combo.addItem("Initializing...", "")
            self._update_status("Initializing...", "info")

    def _populate_model_combo(self, provider, all_models_info):
        from core.logger import setup_logger
        from ai.models.model_catalog import ModelState
        
        logger = setup_logger(__name__)
        self._model_combo.clear()
        
        # Get model states from catalog
        catalog = self.chat_engine.model_registry.catalog if self.chat_engine else None
        
        available_models = []
        
        if provider == "automatic":
            for model_id, model_info in all_models_info.items():
                # Skip deepseek - user doesn't want it as default
                if "deepseek" in model_id.lower() or "deepseek" in model_info.display_name.lower():
                    logger.info(f"Skipping deepseek model: {model_id}")
                    continue
                
                # Get model state from catalog
                state = ModelState.UNKNOWN
                if catalog:
                    entry = catalog.get_entry(model_id)
                    if entry:
                        state = entry.state
                
                # Only add models that are not clearly broken/offline
                EXCLUDED_STATES = {
                    ModelState.OFFLINE,
                    ModelState.DISCONNECTED,
                    ModelState.AUTH_FAILED,
                    ModelState.API_MISSING,
                    ModelState.DISABLED,
                    ModelState.UNSUPPORTED,
                }
                if state not in EXCLUDED_STATES or model_info.status == "connected":
                    icon = ModelState.get_icon(state)
                    display_text = f"{icon} {model_info.display_name}"
                    available_models.append((model_id, display_text, model_info))
            
            if available_models:
                # Sort: local models first, then by availability
                available_models.sort(key=lambda x: (
                    0 if x[2].model_type == "local" else 1,
                    -x[2].availability,
                    x[1]
                ))
                
                for model_id, display_text, _ in available_models:
                    self._model_combo.addItem(display_text, model_id)
                
                # Auto-select the first available model
                if self._model_combo.count() > 0:
                    self._model_combo.setCurrentIndex(0)
                    selected_model = self._model_combo.currentData()
                    logger.info(f"Auto-selected first available model: {selected_model}")
                
                self._update_status(f"Ready: {len(available_models)} models", "success")
            else:
                self._model_combo.addItem("No models available", "")
                self._update_status("No models available", "warning")
        else:
            provider_models = []
            for model_id, model_info in all_models_info.items():
                if model_info.provider.lower() == provider.lower():
                    # Skip deepseek
                    if "deepseek" in model_id.lower() or "deepseek" in model_info.display_name.lower():
                        logger.info(f"Skipping deepseek model: {model_id}")
                        continue
                    
                    state = ModelState.UNKNOWN
                    if catalog:
                        entry = catalog.get_entry(model_id)
                        if entry:
                            state = entry.state
                    
                    # Only add models that are not clearly broken/offline
                    EXCLUDED_STATES = {
                        ModelState.OFFLINE,
                        ModelState.DISCONNECTED,
                        ModelState.AUTH_FAILED,
                        ModelState.API_MISSING,
                        ModelState.DISABLED,
                        ModelState.UNSUPPORTED,
                    }
                    if state not in EXCLUDED_STATES or model_info.status == "connected":
                        icon = ModelState.get_icon(state)
                        display_text = f"{icon} {model_info.display_name}"
                        provider_models.append((model_id, display_text))
            
            if provider_models:
                for model_id, display_text in provider_models:
                    self._model_combo.addItem(display_text, model_id)
                
                # Auto-select first model
                if self._model_combo.count() > 0:
                    self._model_combo.setCurrentIndex(0)
                    selected_model = self._model_combo.currentData()
                    logger.info(f"Auto-selected first model for provider {provider}: {selected_model}")
                
                self._update_status(f"Ready: {provider}", "success")
            else:
                self._model_combo.addItem("No models for provider", "")
                self._update_status("No models for provider", "warning")

    def _start_provider_refresh_background(self):
        """Start background thread to refresh providers and models"""
        from core.logger import setup_logger
        import threading
        
        logger = setup_logger(__name__)
        
        if self._refresh_worker_thread and self._refresh_worker_thread.is_alive():
            logger.info("Previous refresh thread still running, stopping it first")
            self._refresh_stop_flag = True
            # Give it a moment to stop
            self._refresh_worker_thread.join(timeout=1.0)
            self._refresh_stop_flag = False
        
        self.provider_refresh_started.emit()
        
        def worker():
            try:
                # Check stop flag throughout
                if self._refresh_stop_flag:
                    return
                    
                model_center = self.chat_engine.model_center
                provider_registry = self.chat_engine.provider_registry
                
                logger.info("Starting background provider refresh")
                
                all_providers = provider_registry.get_all_providers()
                refreshed_data = {}
                
                for provider_name, provider_obj in all_providers.items():
                    if self._refresh_stop_flag:
                        logger.info("Refresh stopped by flag")
                        return
                        
                    if provider_obj:
                        try:
                            if not provider_obj.is_connected():
                                try:
                                    if provider_obj.connect():
                                        logger.info(f"Connected to {provider_name} in background")
                                except Exception as e:
                                    logger.warning(f"Could not connect to {provider_name} in background: {e}")
                            models = provider_obj.refresh_models()
                            provider_obj._set_models(models)
                            refreshed_data[provider_name] = models
                            logger.info(f"Refreshed {len(models)} models from {provider_name} in background")
                        except Exception as e:
                            logger.error(f"Failed to refresh models for {provider_name} in background: {e}")
                
                if self._refresh_stop_flag:
                    logger.info("Refresh stopped before model center update")
                    return
                
                # Update model center
                for provider_name, provider_obj in all_providers.items():
                    models = provider_obj.get_models()
                    for model_id, model_info in models.items():
                        full_model_id = f"{provider_name}:{model_id}"
                        if full_model_id not in model_center._models:
                            from ai.models.model_center import ModelInfo, ModelCapabilities
                            model_center_info = ModelInfo(
                                model_id=full_model_id,
                                provider=provider_name,
                                display_name=model_info.get("name", model_id),
                                context_window=model_info.get("context_window", 4096),
                                max_output_tokens=model_info.get("max_output_tokens", 4096),
                                model_type=model_info.get("type", "local"),
                                capabilities=ModelCapabilities.from_config({
                                    "provider": provider_name,
                                    "type": model_info.get("type", "local"),
                                    "context_window": model_info.get("context_window", 4096),
                                    "supports_streaming": model_info.get("supports_streaming", True),
                                    "supports_vision": model_info.get("supports_vision", False),
                                    "supports_tool_calling": model_info.get("supports_tool_calling", False),
                                    "supports_function_calling": model_info.get("supports_function_calling", False),
                                }),
                                status="connected" if provider_obj.is_connected() else "disconnected",
                                availability=1.0 if provider_obj.is_connected() else 0.0,
                                tags=model_info.get("strengths", []),
                            )
                            model_center._models[full_model_id] = model_center_info
                            logger.info(f"Added {full_model_id} to Model Center in background")
                
                logger.info("Background provider refresh complete")
                self.provider_refresh_complete.emit(refreshed_data)
                self.models_updated.emit()
                
            except Exception as e:
                logger.error(f"Background refresh failed: {e}", exc_info=True)
        
        self._refresh_worker_thread = threading.Thread(target=worker, daemon=True, name="ProviderRefresh")
        self._refresh_worker_thread.start()
    
    def cleanup(self):
        """Cleanup resources - call this before panel destruction."""
        # Stop any running refresh thread
        if self._refresh_worker_thread and self._refresh_worker_thread.is_alive():
            self._refresh_stop_flag = True
            self._refresh_worker_thread.join(timeout=2.0)
            self._refresh_worker_thread = None

    def _on_provider_refresh_started(self):
        """Slot called when provider refresh starts in background"""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Provider refresh started in background")

    def _on_provider_refresh_complete(self, refreshed_data):
        """Slot called when provider refresh completes in background"""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info(f"Provider refresh complete: {len(refreshed_data)} providers refreshed")
        
    def _on_chat_failover(self, data: dict):
        """Handle AI failover event - switched models/providers automatically"""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        
        old_model = data.get("old_model", "unknown")
        new_model = data.get("new_model", "unknown")
        reason = data.get("reason", "unknown reason")
        
        logger.info(f"Failover: {old_model} -> {new_model} (reason: {reason})")
        
        self._update_status(f"Switched to {new_model} because {reason}", "warning")
        
        # Add failover message to chat
        failover_msg = f"**Switched Models**\nFrom: {old_model}\nTo: {new_model}\nReason: {reason}"
        self._add_message(failover_msg, is_user=False)

    def _on_models_updated(self):
        """Slot called when model center is updated in background thread"""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        
        try:
            if self.chat_engine:
                provider = self._provider_combo.currentData()
                model_center = self.chat_engine.model_center
                all_models_info = model_center.get_all_models()
                self._populate_model_combo(provider, all_models_info)
                logger.info("Model combo updated with refreshed data")
        except Exception as e:
            logger.error(f"Failed to update model combo: {e}", exc_info=True)
            
    def _on_model_changed(self, model: str):
        """Handle model selection."""
        if model and model not in ["Select a provider first", "No models available", "Configure in settings"]:
            self._update_status(f"Ready: {model}", "warning")
            self.event_bus.publish("ai_model_changed", {"model": model})
            
    def _update_status(self, message: str, status: str = "info"):
        """Update status indicator."""
        colors = {
            "error": "#EF4444",
            "warning": "#F59E0B",
            "success": "#22C55E",
            "info": "#3B82F6"
        }
        color = colors.get(status, "#52525C")
        self._status_indicator.setText(f"● {message}")
        self._status_indicator.setToolTip(message)
        self._status_indicator.setStyleSheet(f"color: {color}; font-size: 11px;")
        
    def _send(self):
        """Send message."""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        
        text = self._input.toPlainText().strip()
        if not text:
            return
        
        logger.info(f"Send message: '{text}' (chat_engine={self.chat_engine is not None})")
        
        # Add user message
        self._add_message(text, is_user=True)
        self._messages.append({"role": "user", "content": text})
        self._input.clear()
        
        # Toggle buttons
        self._btn_send.hide()
        self._btn_stop.show()
        
        # Update status
        self._update_status("Generating...", "info")
        
        # Emit signal
        self.message_sent.emit(text)
        self.event_bus.publish("user_message", {"message": text})
        
        # Check if chat engine is available
        if self.chat_engine is None:
            logger.warning("Chat engine is None! Showing placeholder response")
            # Placeholder response
            QTimer.singleShot(800, self._show_placeholder_response)
            return
        
        logger.info("Chat engine available, proceeding with real message")
        
        # Get selected model
        provider = self._provider_combo.currentText()
        model_display = self._model_combo.currentText()
        model_id = self._model_combo.currentData()  # Get actual model ID
        
        logger.info(f"Provider: {provider}, Model Display: {model_display}, Model ID: {model_id}")
        
        # Use display name as fallback if no data
        if not model_id:
            model_id = model_display
            logger.info(f"Using display name as model_id: {model_id}")
        
        # Check if provider and model are valid
        if not model_id or model_id in ["Select a provider first", "No models available", "Configure in settings", "Best available model", "No providers connected - connect one below", "No models for this provider", "Error loading models", "AI engine initializing..."]:
            logger.error(f"Invalid model_id: {model_id}")
            self._update_status("Please select a valid model", "error")
            self._btn_stop.hide()
            self._btn_send.show()
            self._add_message("**Error:** Please select a valid provider and model.", is_user=False)
            return
        
        logger.info(f"Sending message with model_id: {model_id}")
        
        # Create streaming response widget placeholder
        self._streaming_text = ""
        self._streaming_widget = MessageWidget("▌", is_user=False)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, self._streaming_widget)
        QTimer.singleShot(10, self._scroll_to_bottom)
        
        # ── Direct chat engine call (bypasses the stub EngineeringWorkflowCoordinator) ──
        import time
        _start_time = time.time()
        
        def on_chunk(chunk: str):
            self._on_chunk_received(chunk)   # thread-safe via Qt signal
        
        def on_complete(response: str):
            self._on_generation_complete(response, _start_time)  # thread-safe via Qt signal
        
        try:
            self.chat_engine.send_message(
                message=text,
                model_id=model_id,
                on_chunk=on_chunk,
                on_complete=on_complete,
            )
            logger.info(f"chat_engine.send_message() dispatched for model: {model_id}")
        except Exception as e:
            logger.error(f"Error dispatching to chat engine: {e}", exc_info=True)
            self._update_status(f"Error: {str(e)}", "error")
            self._btn_stop.hide()
            self._btn_send.show()
            if self._streaming_widget:
                self._streaming_widget.deleteLater()
                self._streaming_widget = None
            self._add_message(f"**Error:** {str(e)}", is_user=False)
        
    def _on_stop(self):
        """Stop generation."""
        self._btn_stop.hide()
        self._btn_send.show()
        
        # Cancel streaming in chat engine
        if self.chat_engine:
            self.event_bus.publish("ai_chat_cancel", {})
        
        self.event_bus.publish("ai_generation_stop", {})
        
        # Reset streaming state
        self._streaming_text = ""
        if self._streaming_widget:
            self._streaming_widget = None
        
        self._update_status("Generation stopped", "warning")
        
    def _on_new_chat(self):
        """Start new chat."""
        if self._messages:
            reply = QMessageBox.question(
                self, "New Chat",
                "Start a new chat? Current conversation will be cleared.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.clear_conversation()
        self._show_welcome()
        self.event_bus.publish("ai_chat_new", {})
        
    def _on_clear_chat(self):
        """Clear conversation."""
        if not self._messages:
            return
            
        reply = QMessageBox.question(
            self, "Clear Chat",
            "Clear all messages? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.clear_conversation()
            self._show_welcome()
            
    def _add_message(self, text: str, is_user: bool):
        """Add message to conversation."""
        msg = MessageWidget(text, is_user)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, msg)
        
        # Auto-scroll
        QTimer.singleShot(50, self._scroll_to_bottom)
        
    def _scroll_to_bottom(self):
        """Scroll to bottom of conversation."""
        scrollbar = self._scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _on_workflow_chunk(self, data: dict):
        """Handle workflow streaming chunk."""
        self._on_chunk_received(data.get("chunk", ""))
        
    def _on_workflow_finished(self, data: dict):
        """Handle workflow generation completion."""
        import time
        self._on_generation_complete(data.get("response", ""), time.time() - 0.5)

    def _on_chunk_received(self, chunk: str):
        """Handle a streaming chunk from AI (called from background thread)."""
        # Emit signal for thread-safe UI update
        self.chunk_received.emit(chunk)
    
    def _on_chunk_received_safe(self, chunk: str):
        """Handle chunk update in main thread (thread-safe)."""
        self._streaming_text += chunk
        
        # Update the streaming widget text in-place instead of recreating it
        if self._streaming_widget:
            # Find the label inside MessageWidget and update it directly
            labels = self._streaming_widget.findChildren(QLabel)
            for lbl in labels:
                if lbl.objectName() == "msg_body":
                    lbl.setText(self._streaming_text + "▌")
                    break
            else:
                # Fallback: recreate widget
                idx = self._msg_layout.indexOf(self._streaming_widget)
                if idx >= 0:
                    self._streaming_widget.deleteLater()
                    self._streaming_widget = MessageWidget(self._streaming_text + "▌", is_user=False)
                    self._msg_layout.insertWidget(idx, self._streaming_widget)
            
            # Auto-scroll
            QTimer.singleShot(10, self._scroll_to_bottom)
    
    def _on_generation_complete(self, response: str, start_time: float):
        """Handle completion of AI generation (called from background thread)."""
        # Emit signal for thread-safe UI update
        self.generation_complete.emit(response, start_time)
    
    def _on_generation_complete_safe(self, response: str, start_time: float):
        """Handle generation complete in main thread (thread-safe)."""
        import time
        elapsed = time.time() - start_time
        
        # Finalise the streaming widget with full clean text (no cursor)
        if self._streaming_widget:
            labels = self._streaming_widget.findChildren(QLabel)
            for lbl in labels:
                if lbl.objectName() == "msg_body":
                    lbl.setText(response if response else self._streaming_text)
                    break
        elif response:
            # No streaming widget existed — create a final message bubble
            self._add_message(response, is_user=False)
        
        # Store final message
        self._messages.append({"role": "assistant", "content": response or self._streaming_text})
        
        # Reset streaming state
        self._streaming_text = ""
        self._streaming_widget = None
        
        # Toggle buttons
        self._btn_stop.hide()
        self._btn_send.show()
        
        # Update status
        model = self._model_combo.currentText()
        self._update_status(f"Ready: {model}", "success")
        self._latency_lbl.setText(f"{elapsed:.2f}s")
        
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _show_placeholder_response(self):
        """Show placeholder AI response."""
        provider = self._provider_combo.currentText()
        model = self._model_combo.currentText()
        
        response = f"""**No AI Provider Connected**

You selected:
• Provider: {provider}
• Model: {model}

To enable AI features:
1. Configure a provider in Settings
2. Ensure the provider service is running (e.g., Ollama)
3. Test the connection

This placeholder confirms the chat interface is working correctly.
All UI components (provider selection, model selection, message sending) are functional.
"""
        
        self._add_message(response, is_user=False)
        self._messages.append({"role": "assistant", "content": response})
        
        self._btn_stop.hide()
        self._btn_send.show()
        
        self._latency_lbl.setText("~800ms")
        
    def _show_welcome(self):
        """Show welcome message."""
        welcome = """**Welcome to AI Chat**

This is the AI Chat interface. Select a provider and model above to get started.

Features:
• Multi-line input (Shift+Enter for new line)
• Message history with copy support
• Provider and model switching
• Chat management (New, Clear)

Configure your AI provider in Settings to enable real conversations."""
        
        self._add_message(welcome, is_user=False)
        
    def clear_conversation(self):
        """Clear all messages."""
        # Remove all message widgets except stretch
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.deleteLater()
        
        self._messages.clear()
        self._streaming_widget = None  # Clear streaming reference
        self._btn_stop.hide()
        self._btn_send.show()
    
    def cleanup(self):
        """Cleanup resources before destruction."""
        # Stop refresh thread
        if hasattr(self, '_refresh_worker_thread') and self._refresh_worker_thread and self._refresh_worker_thread.is_alive():
            self._refresh_stop_flag = True
            self._refresh_worker_thread.join(timeout=2.0)
            self._refresh_worker_thread = None
        
        # Clear all widgets
        self.clear_conversation()
    
    def set_chat_engine(self, chat_engine):
        """Set the AI Chat Engine reference."""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        
        logger.info("set_chat_engine called!")
        self.chat_engine = chat_engine
        logger.info(f"AI Chat Engine set: {chat_engine is not None}")
        
        # Update status to show connected
        if chat_engine:
            self._update_status("AI connected", "success")
            logger.info("AI Chat Engine connected successfully")
            
            # Populate the provider combo from provider registry
            logger.info("About to get provider_registry from chat_engine")
            provider_registry = chat_engine.provider_registry
            logger.info("About to get all providers")
            all_providers = provider_registry.get_all_providers()
            logger.info(f"Got {len(all_providers)} providers!")
            
            # Clear existing providers except "Automatic"
            self._provider_combo.blockSignals(True)
            self._provider_combo.clear()
            self._provider_combo.addItem("Automatic", "automatic")
            
            for provider_name, provider_obj in all_providers.items():
                # Add the provider with proper capitalization
                display_name = provider_name.capitalize()
                logger.info(f"Adding provider: {display_name}")
                self._provider_combo.addItem(display_name, provider_name.lower())
            
            self._provider_combo.blockSignals(False)
            
            # Refresh available models
            logger.info("About to call _refresh_providers_and_models")
            self._refresh_providers_and_models()
        else:
            logger.warning("AI Chat Engine is None!")
    
    def _refresh_providers_and_models(self):
        """Refresh providers and models from the chat engine."""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("_refresh_providers_and_models called!")
        if not self.chat_engine:
            logger.warning("No chat engine, can't refresh!")
            return
        
        try:
            # Just trigger a provider change to reload models with real data
            current_provider = self._provider_combo.currentText()
            logger.info(f"Current provider text: {current_provider}")
            if current_provider:
                logger.info("Calling _on_provider_changed")
                self._on_provider_changed(current_provider)
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}", exc_info=True)
            self._update_status(f"Error loading models: {str(e)}", "error")
    
    def _on_provider_connected_event(self, data: dict):
        """Handle provider connected event."""
        from core.logger import setup_logger
        logger = setup_logger(__name__)
        
        provider_name = data.get("provider_name", "")
        model = data.get("model", "")
        
        logger.info(f"Provider connected event: {provider_name}, model: {model}")
        
        # Refresh provider list
        self._refresh_providers_and_models()
        
        # Update status
        self._update_status(f"Connected: {provider_name}", "success")
